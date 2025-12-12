import { WorkScheduler, WorkItem } from '../../hybrid_runtime/work_scheduler';
import { VMCapabilities } from '../../hybrid_runtime/transport_adapter';

describe('WorkScheduler', () => {
  let scheduler: WorkScheduler;

  beforeEach(() => {
    scheduler = new WorkScheduler({
      strategy: 'round-robin',
      maxTasksPerWorker: 10,
    });
  });

  describe('Work Queueing', () => {
    it('should enqueue work items', () => {
      const workItem: WorkItem = {
        id: 'work-1',
        payload: { task: 'compute' },
        priority: 1,
        createdAt: Date.now(),
      };

      scheduler.enqueueWork(workItem);
      expect(scheduler.getQueueLength()).toBe(1);
    });

    it('should sort work items by priority', () => {
      const work1: WorkItem = {
        id: 'work-1',
        payload: {},
        priority: 1,
        createdAt: Date.now(),
      };
      const work2: WorkItem = {
        id: 'work-2',
        payload: {},
        priority: 5,
        createdAt: Date.now(),
      };
      const work3: WorkItem = {
        id: 'work-3',
        payload: {},
        priority: 3,
        createdAt: Date.now(),
      };

      scheduler.enqueueWork(work1);
      scheduler.enqueueWork(work2);
      scheduler.enqueueWork(work3);

      const vms: VMCapabilities[] = [
        { vmId: 'vm-1', maxConcurrentTasks: 10, supportedMessageTypes: [] },
      ];
      scheduler.updateAvailableVMs(vms);

      const scheduled1 = scheduler.scheduleNext();
      const scheduled2 = scheduler.scheduleNext();
      const scheduled3 = scheduler.scheduleNext();

      expect(scheduled1?.id).toBe('work-2');
      expect(scheduled2?.id).toBe('work-3');
      expect(scheduled3?.id).toBe('work-1');
    });
  });

  describe('Round-Robin Scheduling', () => {
    it('should distribute work evenly across VMs', () => {
      const vms: VMCapabilities[] = [
        { vmId: 'vm-1', maxConcurrentTasks: 10, supportedMessageTypes: [] },
        { vmId: 'vm-2', maxConcurrentTasks: 10, supportedMessageTypes: [] },
        { vmId: 'vm-3', maxConcurrentTasks: 10, supportedMessageTypes: [] },
      ];
      scheduler.updateAvailableVMs(vms);

      for (let i = 0; i < 6; i++) {
        scheduler.enqueueWork({
          id: `work-${i}`,
          payload: {},
          priority: 0,
          createdAt: Date.now(),
        });
      }

      const assignments: string[] = [];
      for (let i = 0; i < 6; i++) {
        const work = scheduler.scheduleNext();
        if (work?.assignedTo) {
          assignments.push(work.assignedTo);
        }
      }

      expect(assignments.filter(a => a === 'vm-1').length).toBe(2);
      expect(assignments.filter(a => a === 'vm-2').length).toBe(2);
      expect(assignments.filter(a => a === 'vm-3').length).toBe(2);
    });
  });

  describe('Least-Loaded Scheduling', () => {
    beforeEach(() => {
      scheduler = new WorkScheduler({
        strategy: 'least-loaded',
        maxTasksPerWorker: 10,
      });
    });

    it('should assign work to least loaded VM', () => {
      const vms: VMCapabilities[] = [
        { vmId: 'vm-1', maxConcurrentTasks: 10, supportedMessageTypes: [] },
        { vmId: 'vm-2', maxConcurrentTasks: 10, supportedMessageTypes: [] },
      ];
      scheduler.updateAvailableVMs(vms);

      scheduler.enqueueWork({ id: 'w1', payload: {}, priority: 0, createdAt: Date.now() });
      scheduler.enqueueWork({ id: 'w2', payload: {}, priority: 0, createdAt: Date.now() });
      scheduler.enqueueWork({ id: 'w3', payload: {}, priority: 0, createdAt: Date.now() });

      const work1 = scheduler.scheduleNext();
      const work2 = scheduler.scheduleNext();

      scheduler.completeWork(work1!.assignedTo!);

      const work3 = scheduler.scheduleNext();

      expect(work3?.assignedTo).toBe(work1?.assignedTo);
    });
  });

  describe('Workload Management', () => {
    it('should track VM workloads', () => {
      const vms: VMCapabilities[] = [
        { vmId: 'vm-1', maxConcurrentTasks: 10, supportedMessageTypes: [] },
      ];
      scheduler.updateAvailableVMs(vms);

      scheduler.enqueueWork({ id: 'w1', payload: {}, priority: 0, createdAt: Date.now() });
      scheduler.scheduleNext();

      expect(scheduler.getWorkload('vm-1')).toBe(1);
    });

    it('should decrease workload on completion', () => {
      const vms: VMCapabilities[] = [
        { vmId: 'vm-1', maxConcurrentTasks: 10, supportedMessageTypes: [] },
      ];
      scheduler.updateAvailableVMs(vms);

      scheduler.enqueueWork({ id: 'w1', payload: {}, priority: 0, createdAt: Date.now() });
      scheduler.scheduleNext();

      expect(scheduler.getWorkload('vm-1')).toBe(1);

      scheduler.completeWork('vm-1');
      expect(scheduler.getWorkload('vm-1')).toBe(0);
    });
  });

  describe('Backpressure', () => {
    it('should detect when backpressure is needed', () => {
      const vms: VMCapabilities[] = [
        { vmId: 'vm-1', maxConcurrentTasks: 2, supportedMessageTypes: [] },
      ];
      
      scheduler = new WorkScheduler({
        strategy: 'round-robin',
        maxTasksPerWorker: 2,
      });
      scheduler.updateAvailableVMs(vms);

      for (let i = 0; i < 2; i++) {
        scheduler.enqueueWork({ id: `w${i}`, payload: {}, priority: 0, createdAt: Date.now() });
        scheduler.scheduleNext();
      }

      expect(scheduler.isBackpressureNeeded()).toBe(true);
    });
  });

  describe('Statistics', () => {
    it('should provide comprehensive stats', () => {
      const vms: VMCapabilities[] = [
        { vmId: 'vm-1', maxConcurrentTasks: 10, supportedMessageTypes: [] },
        { vmId: 'vm-2', maxConcurrentTasks: 10, supportedMessageTypes: [] },
      ];
      scheduler.updateAvailableVMs(vms);

      scheduler.enqueueWork({ id: 'w1', payload: {}, priority: 0, createdAt: Date.now() });
      scheduler.enqueueWork({ id: 'w2', payload: {}, priority: 0, createdAt: Date.now() });

      const stats = scheduler.getStats();

      expect(stats).toHaveProperty('queueLength');
      expect(stats).toHaveProperty('availableVMs');
      expect(stats).toHaveProperty('totalWorkload');
      expect(stats).toHaveProperty('vmWorkloads');
      expect(stats).toHaveProperty('backpressureActive');
    });
  });
});
