import { NullVM } from '../null_vm';
import { OpCode } from '../instructions';
import {
  StateSnapshot,
  ReplayLog,
  FaultToleranceManager,
  VMSnapshot,
} from '../fault_tolerance';
import { Memory } from '../memory';
import { ExecutionContext } from '../execution_context';

describe('Fault Tolerance', () => {
  let vm: NullVM;
  let memory: Memory;
  let context: ExecutionContext;

  beforeEach(() => {
    vm = new NullVM({ vmId: 'test-vm' });
    memory = vm.getMemory();
    context = vm.getContext();
  });

  describe('StateSnapshot', () => {
    it('should create a snapshot of VM state', () => {
      memory.setRegister('x', 42);
      memory.setRegister('y', 100);
      memory.pushStack(10);

      const snapshot = StateSnapshot.createSnapshot(
        'test-vm',
        memory,
        context,
        5
      );

      expect(snapshot.vmId).toBe('test-vm');
      expect(snapshot.executionCycle).toBe(5);
      expect(snapshot.memory.registers).toEqual({ x: 42, y: 100 });
      expect(snapshot.memory.stackPointer).toBe(1);
    });

    it('should restore from a snapshot', () => {
      memory.setRegister('x', 42);
      memory.setRegister('y', 100);
      memory.pushStack(10);

      const snapshot = StateSnapshot.createSnapshot(
        'test-vm',
        memory,
        context,
        5
      );

      memory.reset();
      expect(memory.getRegister('x')).toBe(0);

      StateSnapshot.restoreSnapshot(snapshot, memory, context);

      expect(memory.getRegister('x')).toBe(42);
      expect(memory.getRegister('y')).toBe(100);
      expect(memory.getStackPointer()).toBe(1);
    });

    it('should preserve register state through snapshot cycle', () => {
      const program = [
        { opcode: OpCode.SET, args: ['x', 10] },
        { opcode: OpCode.ADD, args: ['x', 5] },
        { opcode: OpCode.SHOW, args: ['x'] },
      ];

      vm.execute(program as any);
      const initialValue = memory.getRegister('x');

      const snapshot = StateSnapshot.createSnapshot(
        'test-vm',
        memory,
        context,
        vm.getExecutionCycle()
      );

      vm.reset();
      expect(memory.getRegister('x')).toBe(0);

      StateSnapshot.restoreSnapshot(snapshot, memory, context);
      expect(memory.getRegister('x')).toBe(initialValue);
    });
  });

  describe('ReplayLog', () => {
    let replayLog: ReplayLog;

    beforeEach(() => {
      replayLog = new ReplayLog(100);
    });

    it('should log operations', () => {
      replayLog.logOperation(0, 'vm-1', 'SET', ['x', '42'], 42);
      replayLog.logOperation(1, 'vm-1', 'ADD', ['x', '5'], 47);

      const entries = replayLog.getEntries();
      expect(entries).toHaveLength(2);
      expect(entries[0].operation).toBe('SET');
      expect(entries[1].operation).toBe('ADD');
    });

    it('should enforce max entries limit', () => {
      const smallLog = new ReplayLog(5);

      for (let i = 0; i < 10; i++) {
        smallLog.logOperation(i, 'vm-1', 'SET', ['x', String(i)]);
      }

      expect(smallLog.size()).toBe(5);
    });

    it('should retrieve entries since a given cycle', () => {
      for (let i = 0; i < 5; i++) {
        replayLog.logOperation(i, 'vm-1', 'OPERATION', [String(i)]);
      }

      const recent = replayLog.getEntriesSince(2);
      expect(recent).toHaveLength(3);
      expect(recent[0].cycle).toBe(2);
    });

    it('should clear all entries', () => {
      replayLog.logOperation(0, 'vm-1', 'SET', ['x', '42']);
      expect(replayLog.size()).toBe(1);

      replayLog.clear();
      expect(replayLog.size()).toBe(0);
    });
  });

  describe('FaultToleranceManager', () => {
    let manager: FaultToleranceManager;

    beforeEach(() => {
      manager = new FaultToleranceManager();
    });

    it('should create checkpoints', () => {
      const snapshot = StateSnapshot.createSnapshot(
        'test-vm',
        memory,
        context,
        0
      );

      const checkpointId = manager.createCheckpoint('test-vm', snapshot, []);

      expect(checkpointId).toMatch(/^checkpoint-/);

      const retrieved = manager.getCheckpoint(checkpointId);
      expect(retrieved).toBeDefined();
      expect(retrieved!.vmSnapshot.vmId).toBe('test-vm');
    });

    it('should list checkpoints by VM', () => {
      const snapshot1 = StateSnapshot.createSnapshot(
        'vm-1',
        memory,
        context,
        0
      );
      const snapshot2 = StateSnapshot.createSnapshot(
        'vm-1',
        memory,
        context,
        10
      );

      manager.createCheckpoint('vm-1', snapshot1, []);
      manager.createCheckpoint('vm-1', snapshot2, []);

      const checkpoints = manager.listCheckpoints('vm-1');
      expect(checkpoints).toHaveLength(2);
      expect(checkpoints[0].vmSnapshot.executionCycle).toBe(10);
    });

    it('should delete checkpoints', () => {
      const snapshot = StateSnapshot.createSnapshot(
        'test-vm',
        memory,
        context,
        0
      );

      const checkpointId = manager.createCheckpoint('test-vm', snapshot, []);
      expect(manager.getCheckpoint(checkpointId)).toBeDefined();

      const deleted = manager.deleteCheckpoint(checkpointId);
      expect(deleted).toBe(true);
      expect(manager.getCheckpoint(checkpointId)).toBeUndefined();
    });

    it('should get or create replay logs for VMs', () => {
      const log1 = manager.getReplayLog('vm-1');
      const log2 = manager.getReplayLog('vm-1');

      expect(log1).toBe(log2);
    });

    it('should clear old checkpoints keeping recent ones', () => {
      const snapshot = StateSnapshot.createSnapshot(
        'test-vm',
        memory,
        context,
        0
      );

      const ids: string[] = [];
      for (let i = 0; i < 10; i++) {
        const id = manager.createCheckpoint('test-vm', snapshot, []);
        ids.push(id);
      }

      manager.clearOldCheckpoints('test-vm', 3);

      const remaining = manager.listCheckpoints('test-vm');
      expect(remaining.length).toBeLessThanOrEqual(3);
    });

    it('should provide statistics', () => {
      const snapshot = StateSnapshot.createSnapshot(
        'vm-1',
        memory,
        context,
        0
      );

      manager.createCheckpoint('vm-1', snapshot, []);
      manager.getReplayLog('vm-1').logOperation(0, 'vm-1', 'SET', ['x', '42']);

      const stats = manager.getStats();
      expect(stats.totalCheckpoints).toBe(1);
      expect(stats.checkpointsByVM).toBeDefined();
      expect(stats.replayLogSizes).toBeDefined();
    });
  });

  describe('Snapshot and Recovery Scenario', () => {
    it('should recover from crash at checkpoint', () => {
      const manager = new FaultToleranceManager();

      const program = [
        { opcode: OpCode.SET, args: ['counter', 0] },
        { opcode: OpCode.ADD, args: ['counter', 10] },
        { opcode: OpCode.ADD, args: ['counter', 5] },
      ];

      vm.execute(program as any);
      const finalValue = memory.getRegister('counter');
      expect(finalValue).toBe(15);

      const snapshot = StateSnapshot.createSnapshot(
        'test-vm',
        memory,
        context,
        vm.getExecutionCycle()
      );

      const checkpointId = manager.createCheckpoint('test-vm', snapshot, []);

      vm.reset();
      expect(memory.getRegister('counter')).toBe(0);

      const checkpoint = manager.getCheckpoint(checkpointId);
      expect(checkpoint).toBeDefined();

      StateSnapshot.restoreSnapshot(checkpoint!.vmSnapshot, memory, context);
      expect(memory.getRegister('counter')).toBe(15);
    });
  });
});
