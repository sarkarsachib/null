import { NullVM, ExecutionHook } from '../null_vm';
import { OpCode, Instruction } from '../instructions';
import { WorkStealingScheduler } from '../scheduler';
import { StateSnapshot, FaultToleranceManager } from '../fault_tolerance';

describe('Hybrid Executor Integration', () => {
  describe('Async Execution with Hooks', () => {
    it('should execute programs asynchronously', async () => {
      const vm = new NullVM({ vmId: 'test-vm' });

      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', '10'] },
        { opcode: OpCode.ADD, args: ['x', '5'] },
      ];

      await vm.executeAsync(program);

      expect(vm.getMemory().getRegister('x')).toBe(15);
    });

    it('should invoke execution hooks during async execution', async () => {
      const vm = new NullVM({ vmId: 'test-vm' });
      const cycles: number[] = [];

      const hook: ExecutionHook = async (cycle) => {
        cycles.push(cycle);
      };

      vm.registerExecutionHook(hook);

      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', '10'] },
        { opcode: OpCode.ADD, args: ['x', '5'] },
        { opcode: OpCode.SHOW, args: ['x'] },
      ];

      await vm.executeAsync(program);

      expect(cycles.length).toBeGreaterThan(0);
      expect(cycles[0]).toBe(0);
    });

    it('should pass context to execution hooks', async () => {
      const vm = new NullVM({ vmId: 'test-vm' });
      const contexts: any[] = [];

      const hook: ExecutionHook = async (cycle, instruction, context) => {
        contexts.push({ cycle, instruction: instruction.opcode, context });
      };

      vm.registerExecutionHook(hook);

      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', '42'] },
      ];

      await vm.executeAsync(program);

      expect(contexts.length).toBeGreaterThan(0);
      expect(contexts[0].context.registers).toBeDefined();
    });
  });

  describe('Multi-VM Execution', () => {
    it('should create multiple VM instances', () => {
      const vm1 = new NullVM({ vmId: 'vm-1' });
      const vm2 = new NullVM({ vmId: 'vm-2' });
      const vm3 = new NullVM({ vmId: 'vm-3' });

      expect(vm1.getVMId()).toBe('vm-1');
      expect(vm2.getVMId()).toBe('vm-2');
      expect(vm3.getVMId()).toBe('vm-3');
    });

    it('should execute different programs on different VMs', async () => {
      const vm1 = new NullVM({ vmId: 'vm-1' });
      const vm2 = new NullVM({ vmId: 'vm-2' });

      const program1: Instruction[] = [
        { opcode: OpCode.SET, args: ['a', '100'] },
      ];

      const program2: Instruction[] = [
        { opcode: OpCode.SET, args: ['b', '200'] },
      ];

      await Promise.all([vm1.executeAsync(program1), vm2.executeAsync(program2)]);

      expect(vm1.getMemory().getRegister('a')).toBe(100);
      expect(vm2.getMemory().getRegister('b')).toBe(200);
    });

    it('should isolate state between VMs', async () => {
      const vm1 = new NullVM({ vmId: 'vm-1' });
      const vm2 = new NullVM({ vmId: 'vm-2' });

      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', '99'] },
      ];

      await vm1.executeAsync(program);
      await vm2.executeAsync([
        { opcode: OpCode.SET, args: ['x', '42'] },
      ]);

      expect(vm1.getMemory().getRegister('x')).toBe(99);
      expect(vm2.getMemory().getRegister('x')).toBe(42);
    });
  });

  describe('Scheduler Integration', () => {
    it('should schedule tasks to workers', () => {
      const scheduler = new WorkStealingScheduler();

      scheduler.registerWorker('worker-1');
      scheduler.registerWorker('worker-2');

      const taskId = scheduler.submitTask('vm-1', [
        { opcode: OpCode.SET, args: ['x', '42'] },
      ]);

      expect(taskId).toBeDefined();

      const assignments = scheduler.scheduleWork();
      expect(assignments.size).toBeGreaterThan(0);
    });

    it('should balance load across workers', () => {
      const scheduler = new WorkStealingScheduler({
        maxTasksPerWorker: 5,
      });

      for (let i = 0; i < 3; i++) {
        scheduler.registerWorker(`worker-${i}`);
      }

      for (let i = 0; i < 12; i++) {
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

    it('should report scheduler metrics', () => {
      const scheduler = new WorkStealingScheduler();

      scheduler.registerWorker('worker-1');

      scheduler.submitTask('vm-1', [
        { opcode: OpCode.SET, args: ['x', '42'] },
      ]);

      const metrics = scheduler.getMetrics();

      expect(metrics.totalTasksScheduled).toBeGreaterThanOrEqual(1);
      expect(metrics.workerMetrics.length).toBe(1);
      expect(metrics.queueSize).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Snapshot and Recovery', () => {
    it('should create snapshots', () => {
      const vm = new NullVM({ vmId: 'test-vm' });

      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', '42'] },
        { opcode: OpCode.ADD, args: ['x', '8'] },
      ];

      vm.execute(program);

      const snapshot = vm.createSnapshot();

      expect(snapshot.vmId).toBe('test-vm');
      expect(snapshot.memory.registers.x).toBe(50);
    });

    it('should restore from snapshots', () => {
      const vm = new NullVM({ vmId: 'test-vm' });

      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['counter', '100'] },
      ];

      vm.execute(program);
      const snapshot = vm.createSnapshot();

      vm.reset();
      expect(vm.getMemory().getRegister('counter')).toBe(0);

      vm.restoreSnapshot(snapshot);
      expect(vm.getMemory().getRegister('counter')).toBe(100);
    });

    it('should use fault tolerance manager', () => {
      const vm = new NullVM({ vmId: 'test-vm' });
      const manager = new FaultToleranceManager();

      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['data', '999'] },
      ];

      vm.execute(program);

      const snapshot = vm.createSnapshot();
      const checkpointId = manager.createCheckpoint('test-vm', snapshot, []);

      expect(checkpointId).toMatch(/^checkpoint-/);

      const retrieved = manager.getCheckpoint(checkpointId);
      expect(retrieved?.vmSnapshot.memory.registers.data).toBe(999);
    });
  });

  describe('Fairness and Throughput', () => {
    it('should maintain near-linear scaling with multiple workers', async () => {
      const workerCounts = [1, 2, 4];
      const throughputs: number[] = [];

      for (const workerCount of workerCounts) {
        const scheduler = new WorkStealingScheduler();

        for (let i = 0; i < workerCount; i++) {
          scheduler.registerWorker(`worker-${i}`);
        }

        const startTime = Date.now();

        for (let i = 0; i < 100; i++) {
          scheduler.submitTask(`vm-${i % workerCount}`, [
            { opcode: OpCode.SET, args: ['x', String(i)] },
          ]);
        }

        const assignments = scheduler.scheduleWork();

        for (const tasks of assignments.values()) {
          for (const task of tasks) {
            scheduler.completeTask(task.id);
          }
        }

        const duration = Date.now() - startTime;
        const throughput = (100 / duration) * 1000;
        throughputs.push(throughput);
      }

      expect(throughputs[1]).toBeGreaterThanOrEqual(throughputs[0]);
      expect(throughputs[2]).toBeGreaterThanOrEqual(throughputs[1] * 0.9);
    });

    it('should achieve low latency per task', () => {
      const scheduler = new WorkStealingScheduler();

      scheduler.registerWorker('worker-1');

      const startTime = Date.now();

      const taskId = scheduler.submitTask('vm-1', [
        { opcode: OpCode.SET, args: ['x', '42'] },
      ]);

      scheduler.scheduleWork();
      scheduler.completeTask(taskId);

      const duration = Date.now() - startTime;

      expect(duration).toBeLessThan(5000);
    });
  });

  describe('Stress Tests', () => {
    it('should handle high task volume', () => {
      const scheduler = new WorkStealingScheduler({
        maxQueueSize: 10000,
      });

      for (let i = 0; i < 10; i++) {
        scheduler.registerWorker(`worker-${i}`);
      }

      const taskCount = 1000;
      for (let i = 0; i < taskCount; i++) {
        scheduler.submitTask(`vm-${i % 10}`, [
          { opcode: OpCode.SET, args: ['x', String(i)] },
        ]);
      }

      const assignments = scheduler.scheduleWork();

      let totalAssigned = 0;
      for (const tasks of assignments.values()) {
        totalAssigned += tasks.length;
      }

      expect(totalAssigned).toBeGreaterThan(0);
    });

    it('should handle concurrent VM execution', async () => {
      const vms = Array.from({ length: 20 }, (_, i) =>
        new NullVM({ vmId: `vm-${i}` })
      );

      const programs = Array.from({ length: 20 }, (_, i) => [
        { opcode: OpCode.SET, args: [`x`, i * 10] },
        { opcode: OpCode.ADD, args: [`x`, i] },
      ] as Instruction[]);

      const results = await Promise.all(
        vms.map((vm, i) => vm.executeAsync(programs[i]))
      );

      expect(results).toHaveLength(20);

      for (let i = 0; i < 20; i++) {
        const expected = i * 10 + i;
        expect(vms[i].getMemory().getRegister('x')).toBe(expected);
      }
    });
  });

  describe('Message Loss Prevention', () => {
    it('should track execution with replay logs', async () => {
      const vm = new NullVM({ vmId: 'test-vm' });
      const manager = new FaultToleranceManager();
      const replayLog = manager.getReplayLog('test-vm');

      const hook: ExecutionHook = async (cycle, instruction) => {
        replayLog.logOperation(
          cycle,
          'test-vm',
          instruction.opcode,
          instruction.args || []
        );
      };

      vm.registerExecutionHook(hook);

      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 1] },
        { opcode: OpCode.ADD, args: ['x', 2] },
        { opcode: OpCode.ADD, args: ['x', 3] },
      ];

      await vm.executeAsync(program);

      const entries = replayLog.getEntries();
      expect(entries.length).toBeGreaterThan(0);
      expect(entries.every((e) => e.vmId === 'test-vm')).toBe(true);
    });
  });
});
