export interface SuperBitMessage {
  id: string;
  sourceVmId: string;
  targetVmId: string;
  messageType: string;
  payload: Buffer;
  timestamp: number;
}

export interface VMCapabilities {
  vmId: string;
  maxConcurrentTasks: number;
  supportedMessageTypes: string[];
  customMetadata?: Record<string, unknown>;
}

export interface HealthStatus {
  vmId: string;
  status: 'healthy' | 'degraded' | 'failed';
  timestamp: number;
  errorMessage?: string;
}

export type MessageHandler = (message: SuperBitMessage) => void | Promise<void>;
export type HealthCallback = (status: HealthStatus) => void;
export type FaultCallback = (vmId: string, error: Error) => void;

export interface TransportAdapter {
  readonly adapterId: string;

  initialize(): Promise<void>;

  sendMessage(message: SuperBitMessage): Promise<void>;

  receiveMessage(handler: MessageHandler): void;

  registerHealthCallback(callback: HealthCallback): void;

  registerFaultCallback(callback: FaultCallback): void;

  advertiseCapabilities(capabilities: VMCapabilities): Promise<void>;

  discoverVMs(): Promise<VMCapabilities[]>;

  close(): Promise<void>;
}

export abstract class BaseTransportAdapter implements TransportAdapter {
  abstract readonly adapterId: string;

  protected messageHandlers: MessageHandler[] = [];
  protected healthCallbacks: HealthCallback[] = [];
  protected faultCallbacks: FaultCallback[] = [];

  abstract initialize(): Promise<void>;
  abstract sendMessage(message: SuperBitMessage): Promise<void>;
  abstract advertiseCapabilities(capabilities: VMCapabilities): Promise<void>;
  abstract discoverVMs(): Promise<VMCapabilities[]>;
  abstract close(): Promise<void>;

  receiveMessage(handler: MessageHandler): void {
    this.messageHandlers.push(handler);
  }

  registerHealthCallback(callback: HealthCallback): void {
    this.healthCallbacks.push(callback);
  }

  registerFaultCallback(callback: FaultCallback): void {
    this.faultCallbacks.push(callback);
  }

  protected emitMessage(message: SuperBitMessage): void {
    this.messageHandlers.forEach((handler) => {
      try {
        const result = handler(message);
        if (result instanceof Promise) {
          result.catch((err) => this.emitFault(message.sourceVmId, err));
        }
      } catch (err) {
        this.emitFault(message.sourceVmId, err as Error);
      }
    });
  }

  protected emitHealth(status: HealthStatus): void {
    this.healthCallbacks.forEach((callback) => callback(status));
  }

  protected emitFault(vmId: string, error: Error): void {
    this.faultCallbacks.forEach((callback) => callback(vmId, error));
  }
}
