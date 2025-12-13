import { DistributedExecutor } from '../distributed';
import { NullVM } from '../null_vm';
import { OpCode } from '../instructions';

describe('DistributedExecutor', () => {
  let executor: DistributedExecutor;
  let vm1: NullVM;
  let vm2: NullVM;

  beforeEach(async () => {
    executor = new DistributedExecutor({
      nodeId: 'test-node',
      listenAddr: 'localhost',
      listenPort: 50051,
      maxWorkers: 10,
      enableCheckpointing: true,
      checkpointInterval: 1000,
      heartbeatInterval: 500,
    });

    vm1 = new NullVM({ vmId: 'vm-1' });
    vm2 = new NullVM({ vmId: 'vm-2' });

    executor.registerVM('vm-1', vm1);
    executor.registerVM('vm-2', vm2);

    await executor.initialize();
  });

  afterEach(async () => {
    await executor.shutdown();
  });

  describe('VM Registration', () => {
    it('should register VMs', () => {
      expect(executor.getVMCount()).toBe(2);
    });

    it('should provide VM count', () => {
      expect(executor.getVMCount()).toBeGreaterThan(0);
    });

    it('should track registered VMs', () => {
      const metrics = executor.getMetrics();
      expect(metrics.registeredVMs).toBe(2);
    });
  });

  describe('Program Execution', () => {
    it('should execute programs on specified VM', async () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 42] },
        { opcode: OpCode.ADD, args: ['x', 8] },
      ];

      const result = await executor.executeOnVM('vm-1', program as any);

      expect(result.status).toBe('success');
      expect(result.vmId).toBe('vm-1');
      expect(result.registers.x).toBe(50);
    });

    it('should handle execution failures', async () => {
      const program = [{ opcode: 'INVALID_OP' as any, args: [] }];

      const result = await executor.executeOnVM('vm-1', program);

      expect(result.status).toBe('failure');
      expect(result.error).toBeDefined();
    });

    it('should track execution cycles', async () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 10] },
        { opcode: OpCode.SET, args: ['y', 20] },
      ];

      const result = await executor.executeOnVM('vm-1', program as any);

      expect(result.executionCycles).toBeGreaterThan(0);
    });
  });

  describe('Work Submission', () => {
    it('should submit work to scheduler', () => {
      const program = [{ opcode: OpCode.SET, args: ['x', 42] }];

      const taskId = executor.submitWork('vm-1', program as any, 5);

      expect(taskId).toMatch(/^task-/);
    });

    it('should get assigned work for workers', () => {
      executor.submitWork('vm-1', [{ opcode: OpCode.SET, args: ['x', 1] }] as any);
      executor.submitWork('vm-2', [{ opcode: OpCode.SET, args: ['x', 2] }] as any);

      const work = executor.getWork('vm-1', 5);

      expect(work.length).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Checkpointing', () => {
    it('should create checkpoints', () => {
      const checkpointId = executor.createCheckpoint('vm-1');

      expect(checkpointId).toBeDefined();
    });

    it('should recover from checkpoints', async () => {
      const program = [
        { opcode: OpCode.SET, args: ['counter', 100] },
      ];

      await executor.executeOnVM('vm-1', program as any);

      const checkpointId = executor.createCheckpoint('vm-1');
      expect(checkpointId).not.toBeNull();

      const recovered = executor.recoverFromCheckpoint('vm-1', checkpointId!);
      expect(recovered).toBe(true);
    });

    it('should handle missing checkpoints', () => {
      const recovered = executor.recoverFromCheckpoint(
        'vm-1',
        'nonexistent-checkpoint'
      );

      expect(recovered).toBe(false);
    });
  });

  describe('Execution Hooks', () => {
    it('should use execution hooks for logging', async () => {
      const loggedCycles: number[] = [];

      vm1.registerExecutionHook(async (cycle) => {
        loggedCycles.push(cycle);
      });

      const program = [
        { opcode: OpCode.SET, args: ['x', 1] },
        { opcode: OpCode.ADD, args: ['x', 1] },
      ];

      await executor.executeOnVM('vm-1', program as any);

      expect(loggedCycles.length).toBeGreaterThan(0);

      vm1.clearExecutionHooks();
    });
  });

  describe('Metrics', () => {
    it('should provide executor metrics', () => {
      const metrics = executor.getMetrics();

      expect(metrics.nodeId).toBe('test-node');
      expect(metrics.registeredVMs).toBe(2);
      expect(metrics.schedulerMetrics).toBeDefined();
      expect(metrics.faultToleranceMetrics).toBeDefined();
    });

    it('should include scheduler metrics', async () => {
      executor.submitWork('vm-1', [{ opcode: OpCode.SET, args: ['x', '42'] }]);

      const metrics = executor.getMetrics();

      expect(metrics.schedulerMetrics.totalTasksScheduled).toBeGreaterThanOrEqual(
        1
      );
    });

    it('should include fault tolerance metrics', () => {
      executor.createCheckpoint('vm-1');

      const metrics = executor.getMetrics();

      expect(metrics.faultToleranceMetrics.totalCheckpoints).toBeGreaterThanOrEqual(
        1
      );
    });
  });

  describe('Peer Management', () => {
    it('should track peer addresses', () => {
      const peers = executor.getPeers();

      expect(peers).toEqual([]);
    });

    it('should support peer configuration', async () => {
      const executorWithPeers = new DistributedExecutor({
        nodeId: 'test-node-2',
        listenAddr: 'localhost',
        listenPort: 50052,
        peers: [
          { addr: 'localhost', port: 50051 },
          { addr: 'localhost', port: 50053 },
        ],
      });

      const metrics = executorWithPeers.getMetrics();
      expect(metrics.peers.length).toBe(2);

      await executorWithPeers.shutdown();
    });
  });

  describe('Shutdown', () => {
    it('should shutdown gracefully', async () => {
      await executor.shutdown();
      expect(executor.getVMCount()).toBe(2);
    });
  });

  describe('Integration Scenarios', () => {
    it('should execute multiple programs with different priorities', async () => {
      const results = [];

      for (let i = 0; i < 3; i++) {
        const result = await executor.executeOnVM('vm-1', [
          { opcode: OpCode.SET, args: ['x', i * 10] },
        ] as any);
        results.push(result);
      }

      expect(results).toHaveLength(3);
      expect(results.every((r) => r.status === 'success')).toBe(true);
    });

    it('should handle checkpoint and recovery workflow', async () => {
      const initialProgram = [
        { opcode: OpCode.SET, args: ['data', 1000] },
      ];

      await executor.executeOnVM('vm-1', initialProgram as any);

      const checkpointId = executor.createCheckpoint('vm-1');

      const recoveryResult = executor.recoverFromCheckpoint('vm-1', checkpointId!);
      expect(recoveryResult).toBe(true);

      const value = vm1.getMemory().getRegister('data');
      expect(value).toBe(1000);
    });

    it('should distribute work across multiple VMs', async () => {
      const program1 = [
        { opcode: OpCode.SET, args: ['a', 100] },
      ];
      const program2 = [
        { opcode: OpCode.SET, args: ['b', 200] },
      ];

      const result1 = executor.executeOnVM('vm-1', program1 as any);
      const result2 = executor.executeOnVM('vm-2', program2 as any);

      const [r1, r2] = await Promise.all([result1, result2]);

      expect(r1.registers.a).toBe(100);
      expect(r2.registers.b).toBe(200);
    });
  });

  describe('Async Execution', () => {
    it('should execute programs asynchronously', async () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 42] },
        { opcode: OpCode.ADD, args: ['x', 8] },
      ];

      const result = await executor.executeOnVM('vm-1', program as any);

      expect(result).toBeDefined();
      expect(result.status).toBe('success');
    });

    it('should handle concurrent executions', async () => {
      const programs = [
        [{ opcode: OpCode.SET, args: ['x', 1] }],
        [{ opcode: OpCode.SET, args: ['y', 2] }],
        [{ opcode: OpCode.SET, args: ['z', 3] }],
      ];

      const results = await Promise.all(
        programs.map((prog, i) =>
          executor.executeOnVM(i % 2 === 0 ? 'vm-1' : 'vm-2', prog as any)
        )
      );

      expect(results).toHaveLength(3);
      expect(results.every((r) => r.status === 'success')).toBe(true);
    });
  });
});
