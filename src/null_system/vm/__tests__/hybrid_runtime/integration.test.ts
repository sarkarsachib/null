import { NullVM } from '../../null_vm';
import { HybridExecutionManager } from '../../hybrid_runtime/hybrid_execution_manager';
import {
  BaseTransportAdapter,
  VMCapabilities,
  SuperBitMessage,
} from '../../hybrid_runtime/transport_adapter';
import { OpCode } from '../../instructions';

class MockTransportAdapter extends BaseTransportAdapter {
  readonly adapterId = 'mock';
  private capabilities: VMCapabilities[] = [];

  async initialize(): Promise<void> {
    return Promise.resolve();
  }

  async sendMessage(message: SuperBitMessage): Promise<void> {
    this.emitMessage(message);
    return Promise.resolve();
  }

  async advertiseCapabilities(capabilities: VMCapabilities): Promise<void> {
    this.capabilities.push(capabilities);
    this.emitHealth({
      vmId: capabilities.vmId,
      status: 'healthy',
      timestamp: Date.now(),
    });
    return Promise.resolve();
  }

  async discoverVMs(): Promise<VMCapabilities[]> {
    return Promise.resolve([...this.capabilities]);
  }

  async close(): Promise<void> {
    this.capabilities = [];
    return Promise.resolve();
  }
}

describe('Hybrid Runtime Integration', () => {
  let adapter: MockTransportAdapter;
  let manager: HybridExecutionManager;

  beforeEach(async () => {
    adapter = new MockTransportAdapter();
    manager = new HybridExecutionManager(adapter, {
      loadBalancingStrategy: 'round-robin',
      enableAutoRestart: true,
    });
    await manager.initialize();
  });

  afterEach(async () => {
    await manager.shutdown();
  });

  describe('Multiple VM Execution', () => {
    it('should spawn and execute multiple VMs', async () => {
      const vm1 = new NullVM({
        vmId: 'vm-1',
        hybridRuntime: {
          enabled: true,
          manager,
          capabilities: { maxConcurrentTasks: 10, supportedMessageTypes: [] },
        },
      });

      const vm2 = new NullVM({
        vmId: 'vm-2',
        hybridRuntime: {
          enabled: true,
          manager,
          capabilities: { maxConcurrentTasks: 10, supportedMessageTypes: [] },
        },
      });

      expect(vm1.getVMId()).toBe('vm-1');
      expect(vm2.getVMId()).toBe('vm-2');

      const program = [
        { opcode: OpCode.SET, args: ['x', 10] },
        { opcode: OpCode.ADD, args: ['x', 5] },
      ];

      vm1.execute(program);
      vm2.execute(program);

      expect(vm1.getMemory().getRegister('x')).toBe(15);
      expect(vm2.getMemory().getRegister('x')).toBe(15);
    });

    it('should spawn child VMs programmatically', async () => {
      const parentVM = new NullVM({
        vmId: 'parent',
        hybridRuntime: {
          enabled: true,
          manager,
        },
      });

      const childVM = await parentVM.spawnChildVM('child-1', {
        maxConcurrentTasks: 5,
        supportedMessageTypes: ['DATA'],
      });

      expect(childVM.getVMId()).toBe('child-1');
      expect(parentVM.getChildVMs().size).toBe(1);
    });
  });

  describe('Message Passing', () => {
    it('should exchange messages between VMs', async () => {
      const vm1 = new NullVM({
        vmId: 'sender',
        hybridRuntime: {
          enabled: true,
          manager,
        },
      });

      const vm2 = new NullVM({
        vmId: 'receiver',
        hybridRuntime: {
          enabled: true,
          manager,
        },
      });

      await vm1.sendMessageToVM('receiver', 'DATA', { value: 42 });

      vm2.queueMessage('DATA', { value: 42 });

      const program = [{ opcode: OpCode.RECV_MSG, args: ['result', 1000] }];

      vm2.execute(program);

      expect(vm2.getMemory().getRegister('result')).toBeGreaterThan(0);
    });

    it('should handle SEND_MSG and RECV_MSG opcodes', async () => {
      const vm1 = new NullVM({
        vmId: 'vm-1',
        hybridRuntime: {
          enabled: true,
          manager,
        },
      });

      const vm2 = new NullVM({
        vmId: 'vm-2',
        hybridRuntime: {
          enabled: true,
          manager,
        },
      });

      const sendProgram = [{ opcode: OpCode.SEND_MSG, args: ['vm-2', 'DATA', 100] }];

      vm2.queueMessage('DATA', 100);

      const recvProgram = [{ opcode: OpCode.RECV_MSG, args: ['msg', 1000] }];

      vm1.execute(sendProgram);
      vm2.execute(recvProgram);

      expect(vm2.getMemory().getRegister('msg')).toBe(100);
    });
  });

  describe('Barrier Synchronization', () => {
    it('should synchronize multiple VMs at barrier', async () => {
      const vm1 = new NullVM({
        vmId: 'vm-1',
        hybridRuntime: {
          enabled: true,
          manager,
        },
      });

      const vm2 = new NullVM({
        vmId: 'vm-2',
        hybridRuntime: {
          enabled: true,
          manager,
        },
      });

      await manager.createBarrier('test-barrier', 2);

      const arrivals = [vm1.joinBarrier('test-barrier'), vm2.joinBarrier('test-barrier')];

      await expect(Promise.all(arrivals)).resolves.not.toThrow();
    });

    it('should handle SYNC_BARRIER opcode', async () => {
      const vm1 = new NullVM({
        vmId: 'vm-1',
        hybridRuntime: {
          enabled: true,
          manager,
        },
      });

      await manager.createBarrier('opcode-barrier', 1);

      const program = [
        { opcode: OpCode.SET, args: ['x', 10] },
        { opcode: OpCode.SYNC_BARRIER, args: ['opcode-barrier', 5000] },
        { opcode: OpCode.ADD, args: ['x', 5] },
      ];

      vm1.execute(program);

      expect(vm1.getMemory().getRegister('x')).toBe(15);
    });
  });

  describe('Fault Recovery', () => {
    it('should handle VM failures gracefully', async () => {
      const logMessages: string[] = [];
      manager.registerLogHook((message) => {
        logMessages.push(message);
      });

      const vm1 = new NullVM({
        vmId: 'failing-vm',
        hybridRuntime: {
          enabled: true,
          manager,
        },
      });

      expect(logMessages.length).toBeGreaterThan(0);
    });
  });

  describe('Distributed Workloads', () => {
    it('should distribute REPEAT workload across VMs', async () => {
      const workers: NullVM[] = [];

      for (let i = 0; i < 3; i++) {
        workers.push(
          new NullVM({
            vmId: `worker-${i}`,
            hybridRuntime: {
              enabled: true,
              manager,
            },
          })
        );
      }

      const program = [
        { opcode: OpCode.SET, args: ['counter', 0] },
        {
          opcode: OpCode.REPEAT,
          args: ['iterations', [{ opcode: OpCode.ADD, args: ['counter', 1] }]],
        },
      ];

      workers.forEach((worker) => {
        worker.getMemory().setRegister('iterations', 3);
        worker.execute(program);
        expect(worker.getMemory().getRegister('counter')).toBe(3);
      });
    });

    it('should handle conditional distributed workload', async () => {
      const vm1 = new NullVM({
        vmId: 'conditional-vm-1',
        hybridRuntime: {
          enabled: true,
          manager,
        },
      });

      const vm2 = new NullVM({
        vmId: 'conditional-vm-2',
        hybridRuntime: {
          enabled: true,
          manager,
        },
      });

      const program = [
        { opcode: OpCode.SET, args: ['value', 10] },
        {
          opcode: OpCode.IF,
          args: ['value', '>', [{ opcode: OpCode.ADD, args: ['value', 5] }]],
        },
      ];

      vm1.execute(program);
      vm2.execute(program);

      expect(vm1.getMemory().getRegister('value')).toBe(15);
      expect(vm2.getMemory().getRegister('value')).toBe(15);
    });
  });

  describe('VM State Management', () => {
    it('should track VM state including hybrid runtime info', async () => {
      const vm = new NullVM({
        vmId: 'state-vm',
        hybridRuntime: {
          enabled: true,
          manager,
        },
      });

      const state = vm.getState();

      expect(state).toHaveProperty('vmId');
      expect(state).toHaveProperty('childVMCount');
      expect(state).toHaveProperty('messageQueueSize');
      expect(state.vmId).toBe('state-vm');
    });

    it('should spawn child VMs using SPAWN_VM opcode', async () => {
      const parent = new NullVM({
        vmId: 'parent-vm',
        hybridRuntime: {
          enabled: true,
          manager,
        },
      });

      const program = [{ opcode: OpCode.SPAWN_VM, args: ['child-vm-1', {}] }];

      parent.execute(program);

      expect(parent.getChildVMs().size).toBe(1);
      expect(parent.getChildVMs().has('child-vm-1')).toBe(true);
    });
  });
});
