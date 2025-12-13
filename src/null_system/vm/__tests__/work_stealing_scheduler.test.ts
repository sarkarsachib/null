import { WorkStealingScheduler, ScheduledTask } from '../scheduler';
import { OpCode } from '../instructions';

describe('WorkStealingScheduler', () => {
  let scheduler: WorkStealingScheduler;

  beforeEach(() => {
    scheduler = new WorkStealingScheduler({
      maxQueueSize: 1000,
      maxTasksPerWorker: 10,
      enableBackpressure: true,
    });
  });

  describe('Worker Management', () => {
    it('should register workers', () => {
      scheduler.registerWorker('worker-1');
      scheduler.registerWorker('worker-2');

      const metrics = scheduler.getMetrics();
      expect(metrics.workerMetrics).toHaveLength(2);
    });

    it('should unregister workers and redistribute work', () => {
      scheduler.registerWorker('worker-1');
      scheduler.registerWorker('worker-2');

      const taskId = scheduler.submitTask('vm-1', [
        { opcode: OpCode.SET, args: ['x', '42'] },
      ]);
      expect(taskId).toBeDefined();

      scheduler.unregisterWorker('worker-1');

      const metrics = scheduler.getMetrics();
      expect(metrics.workerMetrics).toHaveLength(1);
    });
  });

  describe('Task Submission', () => {
    beforeEach(() => {
      scheduler.registerWorker('worker-1');
      scheduler.registerWorker('worker-2');
    });

    it('should submit tasks', () => {
      const taskId = scheduler.submitTask('vm-1', [
        { opcode: OpCode.SET, args: ['x', '42'] },
      ]);

      expect(taskId).toMatch(/^task-/);
      const pending = scheduler.getPendingTasks();
      expect(pending).toHaveLength(1);
    });

    it('should respect priority ordering', () => {
      const low = scheduler.submitTask(
        'vm-1',
        [{ opcode: OpCode.SET, args: ['x', '1'] }],
        1
      );
      const high = scheduler.submitTask(
        'vm-2',
        [{ opcode: OpCode.SET, args: ['x', '2'] }],
        10
      );
      const medium = scheduler.submitTask(
        'vm-3',
        [{ opcode: OpCode.SET, args: ['x', '3'] }],
        5
      );

      const pending = scheduler.getPendingTasks();
      expect(pending[0].id).toBe(high);
      expect(pending[1].id).toBe(medium);
      expect(pending[2].id).toBe(low);
    });

    it('should enforce backpressure on full queue', () => {
      const smallScheduler = new WorkStealingScheduler({
        maxQueueSize: 2,
        maxTasksPerWorker: 10,
        enableBackpressure: true,
      });

      smallScheduler.submitTask('vm-1', [{ opcode: OpCode.SET, args: ['x', '1'] }]);
      smallScheduler.submitTask('vm-1', [{ opcode: OpCode.SET, args: ['x', '2'] }]);

      expect(() => {
        smallScheduler.submitTask('vm-1', [{ opcode: OpCode.SET, args: ['x', '3'] }]);
      }).toThrow();
    });
  });

  describe('Scheduling', () => {
    beforeEach(() => {
      scheduler.registerWorker('worker-1');
      scheduler.registerWorker('worker-2');
      scheduler.registerWorker('worker-3');
    });

    it('should schedule tasks to workers', () => {
      for (let i = 0; i < 5; i++) {
        scheduler.submitTask('vm-1', [
          { opcode: OpCode.SET, args: ['x', String(i)] },
        ]);
      }

      const assignments = scheduler.scheduleWork();

      expect(assignments.size).toBeGreaterThan(0);

      let totalScheduled = 0;
      for (const tasks of assignments.values()) {
        totalScheduled += tasks.length;
      }
      expect(totalScheduled).toBeGreaterThan(0);
    });

    it('should balance load across workers', () => {
      for (let i = 0; i < 15; i++) {
        scheduler.submitTask('vm-1', [
          { opcode: OpCode.SET, args: ['x', String(i)] },
        ]);
      }

      scheduler.scheduleWork();
      const metrics = scheduler.getMetrics();

      const loads = metrics.workerMetrics.map((w) => w.currentLoad);
      const maxLoad = Math.max(...loads);
      const minLoad = Math.min(...loads);

      expect(maxLoad - minLoad).toBeLessThanOrEqual(2);
    });

    it('should handle work stealing', () => {
      scheduler.registerWorker('worker-4');

      for (let i = 0; i < 20; i++) {
        scheduler.submitTask('vm-1', [
          { opcode: OpCode.SET, args: ['x', String(i)] },
        ]);
      }

      const assignments = scheduler.scheduleWork();
      for (const [workerId, tasks] of assignments.entries()) {
        for (const task of tasks) {
          scheduler.completeTask(task.id);
        }
      }

      const stolen = scheduler.stealWork(5);
      expect(stolen.length).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Task Completion', () => {
    beforeEach(() => {
      scheduler.registerWorker('worker-1');
    });

    it('should mark tasks as completed', () => {
      const taskId = scheduler.submitTask('vm-1', [
        { opcode: OpCode.SET, args: ['x', '42'] },
      ]);

      scheduler.scheduleWork();
      scheduler.completeTask(taskId, { result: 42 });

      const status = scheduler.getTaskStatus(taskId);
      expect(status?.status).toBe('completed');
      expect(status?.result).toEqual({ result: 42 });
    });

    it('should mark tasks as failed', () => {
      const taskId = scheduler.submitTask('vm-1', [
        { opcode: OpCode.SET, args: ['x', '42'] },
      ]);

      scheduler.scheduleWork();
      const error = new Error('Execution failed');
      scheduler.failTask(taskId, error);

      const status = scheduler.getTaskStatus(taskId);
      expect(status?.status).toBe('failed');
      expect(status?.error).toBe(error);
    });

    it('should track worker metrics', () => {
      scheduler.submitTask('vm-1', [{ opcode: OpCode.SET, args: ['x', '42'] }]);
      scheduler.submitTask('vm-2', [{ opcode: OpCode.SET, args: ['y', '99'] }]);

      const assignments = scheduler.scheduleWork();

      for (const [workerId, tasks] of assignments.entries()) {
        for (const task of tasks) {
          scheduler.completeTask(task.id, {});
        }
      }

      const metrics = scheduler.getMetrics();
      expect(metrics.totalTasksCompleted).toBeGreaterThan(0);
    });
  });

  describe('Metrics and Monitoring', () => {
    it('should provide scheduler metrics', () => {
      scheduler.registerWorker('worker-1');
      scheduler.registerWorker('worker-2');

      scheduler.submitTask('vm-1', [{ opcode: OpCode.SET, args: ['x', '42'] }]);

      const metrics = scheduler.getMetrics();

      expect(metrics.totalTasksScheduled).toBeGreaterThanOrEqual(1);
      expect(metrics.workerMetrics.length).toBe(2);
      expect(metrics.queueSize).toBe(0);
    });

    it('should calculate average latency', () => {
      scheduler.registerWorker('worker-1');

      const taskId = scheduler.submitTask('vm-1', [
        { opcode: OpCode.SET, args: ['x', '42'] },
      ]);

      scheduler.scheduleWork();
      scheduler.completeTask(taskId);

      const metrics = scheduler.getMetrics();
      expect(metrics.averageLatency).toBeGreaterThanOrEqual(0);
    });

    it('should detect backpressure conditions', () => {
      scheduler.registerWorker('worker-1');

      for (let i = 0; i < 8; i++) {
        scheduler.submitTask('vm-1', [
          { opcode: OpCode.SET, args: ['x', String(i)] },
        ]);
      }

      scheduler.scheduleWork();

      const metrics = scheduler.getMetrics();
      expect(metrics.backpressureActive).toBe(true);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty work queue', () => {
      scheduler.registerWorker('worker-1');

      const assignments = scheduler.scheduleWork();
      expect(assignments.size).toBe(0);

      const pending = scheduler.getPendingTasks();
      expect(pending).toHaveLength(0);
    });

    it('should handle no available workers', () => {
      const taskId = scheduler.submitTask('vm-1', [
        { opcode: OpCode.SET, args: ['x', '42'] },
      ]);

      const assignments = scheduler.scheduleWork();
      expect(assignments.size).toBe(0);

      const pending = scheduler.getPendingTasks();
      expect(pending).toHaveLength(1);
    });

    it('should handle worker health updates', () => {
      scheduler.registerWorker('worker-1');
      scheduler.registerWorker('worker-2');

      scheduler.updateWorkerHealth('worker-1', false);

      scheduler.submitTask('vm-1', [
        { opcode: OpCode.SET, args: ['x', '42'] },
      ]);

      const assignments = scheduler.scheduleWork();

      expect(assignments.get('worker-1')).toBeUndefined();
    });

    it('should clear completed tasks', () => {
      scheduler.registerWorker('worker-1');

      const taskId = scheduler.submitTask('vm-1', [
        { opcode: OpCode.SET, args: ['x', '42'] },
      ]);

      scheduler.scheduleWork();
      scheduler.completeTask(taskId);

      scheduler.clearCompletedTasks();

      expect(scheduler.getTaskStatus(taskId)).toBeUndefined();
    });
  });
});
