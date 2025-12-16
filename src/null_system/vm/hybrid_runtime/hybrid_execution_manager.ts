import { TransportAdapter, VMCapabilities, HealthStatus, SuperBitMessage } from './transport_adapter';
import { SuperBitMessageBus } from './superbit_message_bus';
import { WorkScheduler, WorkItem, LoadBalancingStrategy } from './work_scheduler';

function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export interface HybridExecutionConfig {
  loadBalancingStrategy?: LoadBalancingStrategy;
  maxTasksPerWorker?: number;
  enableAutoRestart?: boolean;
  healthCheckIntervalMs?: number;
  maxRetries?: number;
}

export interface SyncBarrier {
  id: string;
  participantCount: number;
  arrivedParticipants: Set<string>;
  timeoutMs?: number;
  createdAt: number;
  resolvers: Array<() => void>;
}

export class HybridExecutionManager {
  private transport: TransportAdapter;
  private messageBus: SuperBitMessageBus;
  private scheduler: WorkScheduler;
  private registeredVMs: Map<string, VMCapabilities> = new Map();
  private vmHealth: Map<string, HealthStatus> = new Map();
  private barriers: Map<string, SyncBarrier> = new Map();
  private enableAutoRestart: boolean;
  private healthCheckInterval?: NodeJS.Timeout;
  private logHooks: Array<(message: string, data?: unknown) => void> = [];
  private vmMessageHandlers: Map<
    string,
    Array<(messageType: string, payload: unknown, sourceVmId: string) => void | Promise<void>>
  > = new Map();

  constructor(transport: TransportAdapter, config: HybridExecutionConfig = {}) {
    this.transport = transport;
    this.messageBus = new SuperBitMessageBus(transport, {
      maxRetries: config.maxRetries,
    });
    this.scheduler = new WorkScheduler({
      strategy: config.loadBalancingStrategy,
      maxTasksPerWorker: config.maxTasksPerWorker,
    });
    this.enableAutoRestart = config.enableAutoRestart ?? true;

    this.setupTransportCallbacks();

    if (config.healthCheckIntervalMs) {
      this.startHealthChecks(config.healthCheckIntervalMs);
    }
  }

  private setupTransportCallbacks(): void {
    this.transport.registerHealthCallback((status) => {
      this.handleHealthUpdate(status);
    });

    this.transport.registerFaultCallback((vmId, error) => {
      this.handleFault(vmId, error);
    });

    this.transport.receiveMessage((message) => this.dispatchVMMessage(message));
  }

  async initialize(): Promise<void> {
    await this.transport.initialize();
    this.log('HybridExecutionManager initialized');
  }

  async registerVM(vmId: string, capabilities: VMCapabilities): Promise<void> {
    this.registeredVMs.set(vmId, capabilities);
    await this.transport.advertiseCapabilities(capabilities);

    this.vmHealth.set(vmId, {
      vmId,
      status: 'healthy',
      timestamp: Date.now(),
    });

    this.updateScheduler();
    this.log('VM registered', { vmId, capabilities });
  }

  async discoverVMs(): Promise<VMCapabilities[]> {
    const vms = await this.transport.discoverVMs();
    vms.forEach((vm) => {
      if (!this.registeredVMs.has(vm.vmId)) {
        this.registeredVMs.set(vm.vmId, vm);
      }
    });
    this.updateScheduler();
    return vms;
  }

  private updateScheduler(): void {
    const healthyVMs = Array.from(this.registeredVMs.values()).filter((vm) => {
      const health = this.vmHealth.get(vm.vmId);
      return health?.status === 'healthy';
    });
    this.scheduler.updateAvailableVMs(healthyVMs);
  }

  async submitWork(vmId: string, payload: unknown, priority = 0): Promise<string> {
    const workItem: WorkItem = {
      id: generateUUID(),
      payload,
      priority,
      createdAt: Date.now(),
    };

    this.scheduler.enqueueWork(workItem);

    if (!vmId) {
      const scheduled = this.scheduler.scheduleNext();
      if (scheduled) {
        vmId = scheduled.assignedTo!;
        await this.messageBus.sendMessage('manager', vmId, 'WORK_ASSIGNMENT', scheduled);
      }
    } else {
      await this.messageBus.sendMessage('manager', vmId, 'WORK_ASSIGNMENT', workItem);
    }

    this.log('Work submitted', { workId: workItem.id, vmId });
    return workItem.id;
  }

  async sendMessage(
    sourceVmId: string,
    targetVmId: string,
    messageType: string,
    payload: unknown
  ): Promise<void> {
    if (!this.registeredVMs.has(targetVmId)) {
      throw new Error(`Target VM not registered: ${targetVmId}`);
    }

    const health = this.vmHealth.get(targetVmId);
    if (health?.status !== 'healthy') {
      throw new Error(`Target VM is not healthy: ${targetVmId} (${health?.status})`);
    }

    await this.messageBus.sendMessage(sourceVmId, targetVmId, messageType, payload);
    this.log('Message sent', { sourceVmId, targetVmId, messageType });
  }

  setActiveIntent(intent: string | null): void {
    this.scheduler.setActiveIntent(intent);
    this.log('Intent updated', { intent });
  }

  getActiveIntent(): string | null {
    return this.scheduler.getActiveIntent();
  }

  registerVMMessageHandler(
    vmId: string,
    handler: (messageType: string, payload: unknown, sourceVmId: string) => void | Promise<void>
  ): void {
    const handlers = this.vmMessageHandlers.get(vmId) ?? [];
    handlers.push(handler);
    this.vmMessageHandlers.set(vmId, handlers);
  }

  getRegisteredVMIds(): string[] {
    return Array.from(this.registeredVMs.keys());
  }

  async broadcastMessage(
    sourceVmId: string,
    messageType: string,
    payload: unknown,
    options: { includeSelf?: boolean } = {}
  ): Promise<void> {
    const includeSelf = options.includeSelf ?? false;
    const targets = Array.from(this.registeredVMs.keys()).filter(
      (vmId) => includeSelf || vmId !== sourceVmId
    );
    await Promise.all(targets.map((vmId) => this.sendMessage(sourceVmId, vmId, messageType, payload)));
  }

  private async dispatchVMMessage(message: SuperBitMessage): Promise<void> {
    const handlers = this.vmMessageHandlers.get(message.targetVmId);
    if (!handlers || handlers.length === 0) {
      return;
    }

    let payload: unknown;
    try {
      payload = this.messageBus.deserializePayload(message.payload);
    } catch (err) {
      this.log('Failed to deserialize message payload', {
        messageType: message.messageType,
        error: err instanceof Error ? err.message : String(err),
      });
      return;
    }

    for (const handler of handlers) {
      await Promise.resolve(handler(message.messageType, payload, message.sourceVmId));
    }
  }

  async createBarrier(
    barrierId: string,
    participantCount: number,
    timeoutMs?: number
  ): Promise<void> {
    if (this.barriers.has(barrierId)) {
      throw new Error(`Barrier already exists: ${barrierId}`);
    }

    this.barriers.set(barrierId, {
      id: barrierId,
      participantCount,
      arrivedParticipants: new Set(),
      timeoutMs,
      createdAt: Date.now(),
      resolvers: [],
    });

    this.log('Barrier created', { barrierId, participantCount });
  }

  async arriveAtBarrier(barrierId: string, vmId: string): Promise<void> {
    const barrier = this.barriers.get(barrierId);
    if (!barrier) {
      throw new Error(`Barrier not found: ${barrierId}`);
    }

    barrier.arrivedParticipants.add(vmId);
    this.log('VM arrived at barrier', {
      barrierId,
      vmId,
      arrived: barrier.arrivedParticipants.size,
    });

    if (barrier.arrivedParticipants.size >= barrier.participantCount) {
      barrier.resolvers.forEach((resolve) => resolve());
      this.barriers.delete(barrierId);
      this.log('Barrier released', { barrierId });
      return;
    }

    return new Promise((resolve, reject) => {
      barrier.resolvers.push(resolve);

      if (barrier.timeoutMs) {
        setTimeout(() => {
          if (this.barriers.has(barrierId)) {
            reject(new Error(`Barrier timeout: ${barrierId}`));
          }
        }, barrier.timeoutMs);
      }
    });
  }

  private handleHealthUpdate(status: HealthStatus): void {
    this.vmHealth.set(status.vmId, status);
    this.log('Health update', status);

    if (status.status === 'healthy') {
      this.updateScheduler();
    } else if (status.status === 'failed' && this.enableAutoRestart) {
      this.restartVM(status.vmId);
    }
  }

  private handleFault(vmId: string, error: Error): void {
    this.log('VM fault detected', { vmId, error: error.message });

    this.vmHealth.set(vmId, {
      vmId,
      status: 'failed',
      timestamp: Date.now(),
      errorMessage: error.message,
    });

    if (this.enableAutoRestart) {
      this.restartVM(vmId);
    }
  }

  private async restartVM(vmId: string): Promise<void> {
    this.log('Attempting VM restart', { vmId });

    const capabilities = this.registeredVMs.get(vmId);
    if (!capabilities) {
      this.log('Cannot restart VM - no capabilities found', { vmId });
      return;
    }

    try {
      await this.messageBus.replayInFlightMessages(vmId);

      this.vmHealth.set(vmId, {
        vmId,
        status: 'healthy',
        timestamp: Date.now(),
      });

      this.updateScheduler();
      this.log('VM restarted successfully', { vmId });
    } catch (error) {
      this.log('VM restart failed', { vmId, error: (error as Error).message });
    }
  }

  private startHealthChecks(intervalMs: number): void {
    this.healthCheckInterval = setInterval(() => {
      for (const [vmId, health] of this.vmHealth.entries()) {
        if (Date.now() - health.timestamp > intervalMs * 3) {
          this.vmHealth.set(vmId, {
            vmId,
            status: 'degraded',
            timestamp: Date.now(),
            errorMessage: 'No health updates received',
          });
          this.updateScheduler();
        }
      }
    }, intervalMs);
  }

  registerLogHook(hook: (message: string, data?: unknown) => void): void {
    this.logHooks.push(hook);
  }

  private log(message: string, data?: unknown): void {
    this.logHooks.forEach((hook) => hook(message, data));
  }

  getStats() {
    return {
      registeredVMs: this.registeredVMs.size,
      healthyVMs: Array.from(this.vmHealth.values()).filter((h) => h.status === 'healthy').length,
      scheduler: this.scheduler.getStats(),
      pendingMessages: this.messageBus.getPendingMessageCount(),
      activeBarriers: this.barriers.size,
    };
  }

  async shutdown(): Promise<void> {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }
    this.messageBus.destroy();
    await this.transport.close();
    this.log('HybridExecutionManager shutdown');
  }
}
