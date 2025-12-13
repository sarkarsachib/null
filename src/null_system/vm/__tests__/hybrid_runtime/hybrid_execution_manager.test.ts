import { HybridExecutionManager } from '../../hybrid_runtime/hybrid_execution_manager';
import {
  BaseTransportAdapter,
  VMCapabilities,
  SuperBitMessage,
} from '../../hybrid_runtime/transport_adapter';

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

describe('HybridExecutionManager', () => {
  let adapter: MockTransportAdapter;
  let manager: HybridExecutionManager;

  beforeEach(async () => {
    adapter = new MockTransportAdapter();
    manager = new HybridExecutionManager(adapter, {
      loadBalancingStrategy: 'round-robin',
      maxTasksPerWorker: 5,
      enableAutoRestart: true,
    });
    await manager.initialize();
  });

  afterEach(async () => {
    await manager.shutdown();
  });

  describe('VM Registration', () => {
    it('should register a VM with capabilities', async () => {
      const capabilities: VMCapabilities = {
        vmId: 'test-vm-1',
        maxConcurrentTasks: 10,
        supportedMessageTypes: ['WORK', 'DATA'],
      };

      await manager.registerVM('test-vm-1', capabilities);
      const stats = manager.getStats();

      expect(stats.registeredVMs).toBe(1);
      expect(stats.healthyVMs).toBe(1);
    });

    it('should discover registered VMs', async () => {
      const cap1: VMCapabilities = {
        vmId: 'vm-1',
        maxConcurrentTasks: 10,
        supportedMessageTypes: ['WORK'],
      };
      const cap2: VMCapabilities = {
        vmId: 'vm-2',
        maxConcurrentTasks: 10,
        supportedMessageTypes: ['WORK'],
      };

      await manager.registerVM('vm-1', cap1);
      await manager.registerVM('vm-2', cap2);

      const discovered = await manager.discoverVMs();
      expect(discovered.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('Work Submission', () => {
    it('should submit work to a VM', async () => {
      const capabilities: VMCapabilities = {
        vmId: 'worker-1',
        maxConcurrentTasks: 10,
        supportedMessageTypes: ['WORK_ASSIGNMENT'],
      };

      await manager.registerVM('worker-1', capabilities);

      const workId = await manager.submitWork('worker-1', { task: 'compute' }, 1);
      expect(workId).toBeDefined();
      expect(typeof workId).toBe('string');
    });

    it('should distribute work across multiple VMs', async () => {
      await manager.registerVM('vm-1', {
        vmId: 'vm-1',
        maxConcurrentTasks: 5,
        supportedMessageTypes: ['WORK_ASSIGNMENT'],
      });

      await manager.registerVM('vm-2', {
        vmId: 'vm-2',
        maxConcurrentTasks: 5,
        supportedMessageTypes: ['WORK_ASSIGNMENT'],
      });

      const workIds = await Promise.all([
        manager.submitWork('', { task: 1 }),
        manager.submitWork('', { task: 2 }),
        manager.submitWork('', { task: 3 }),
      ]);

      expect(workIds.length).toBe(3);
      workIds.forEach((id) => expect(id).toBeDefined());
    });
  });

  describe('Message Passing', () => {
    it('should send messages between VMs', async () => {
      await manager.registerVM('vm-1', {
        vmId: 'vm-1',
        maxConcurrentTasks: 10,
        supportedMessageTypes: ['DATA', 'CONTROL'],
      });

      await manager.registerVM('vm-2', {
        vmId: 'vm-2',
        maxConcurrentTasks: 10,
        supportedMessageTypes: ['DATA', 'CONTROL'],
      });

      await expect(
        manager.sendMessage('vm-1', 'vm-2', 'DATA', { value: 42 })
      ).resolves.not.toThrow();
    });

    it('should reject messages to non-existent VMs', async () => {
      await manager.registerVM('vm-1', {
        vmId: 'vm-1',
        maxConcurrentTasks: 10,
        supportedMessageTypes: ['DATA'],
      });

      await expect(
        manager.sendMessage('vm-1', 'non-existent', 'DATA', { value: 42 })
      ).rejects.toThrow('Target VM not registered');
    });
  });

  describe('Barrier Synchronization', () => {
    it('should create and manage barriers', async () => {
      await manager.createBarrier('barrier-1', 2);

      const stats = manager.getStats();
      expect(stats.activeBarriers).toBe(1);
    });

    it('should synchronize VMs at barrier', async () => {
      await manager.registerVM('vm-1', {
        vmId: 'vm-1',
        maxConcurrentTasks: 10,
        supportedMessageTypes: [],
      });

      await manager.registerVM('vm-2', {
        vmId: 'vm-2',
        maxConcurrentTasks: 10,
        supportedMessageTypes: [],
      });

      await manager.createBarrier('sync-barrier', 2);

      const promises = [
        manager.arriveAtBarrier('sync-barrier', 'vm-1'),
        manager.arriveAtBarrier('sync-barrier', 'vm-2'),
      ];

      await expect(Promise.all(promises)).resolves.not.toThrow();

      const stats = manager.getStats();
      expect(stats.activeBarriers).toBe(0);
    });

    it('should timeout barrier if not all participants arrive', async () => {
      await manager.createBarrier('timeout-barrier', 2, 100);

      await expect(manager.arriveAtBarrier('timeout-barrier', 'vm-1')).rejects.toThrow(
        'Barrier timeout'
      );
    });
  });

  describe('Health Monitoring', () => {
    it('should track VM health status', async () => {
      const logMessages: string[] = [];
      manager.registerLogHook((message) => {
        logMessages.push(message);
      });

      await manager.registerVM('vm-1', {
        vmId: 'vm-1',
        maxConcurrentTasks: 10,
        supportedMessageTypes: [],
      });

      expect(logMessages.some((m) => m.includes('registered'))).toBe(true);
    });
  });

  describe('Statistics', () => {
    it('should provide comprehensive stats', async () => {
      await manager.registerVM('vm-1', {
        vmId: 'vm-1',
        maxConcurrentTasks: 10,
        supportedMessageTypes: ['WORK_ASSIGNMENT'],
      });

      const stats = manager.getStats();

      expect(stats).toHaveProperty('registeredVMs');
      expect(stats).toHaveProperty('healthyVMs');
      expect(stats).toHaveProperty('scheduler');
      expect(stats).toHaveProperty('pendingMessages');
      expect(stats).toHaveProperty('activeBarriers');
    });
  });
});
