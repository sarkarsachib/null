import { Worker } from 'worker_threads';
import {
  BaseTransportAdapter,
  SuperBitMessage,
  VMCapabilities,
  HealthStatus,
} from './transport_adapter';

interface WorkerMessage {
  type: 'message' | 'health' | 'capabilities';
  data: SuperBitMessage | HealthStatus | VMCapabilities;
}

export class WorkerThreadAdapter extends BaseTransportAdapter {
  readonly adapterId = 'worker_threads';
  private workers: Map<string, Worker> = new Map();
  private capabilities: Map<string, VMCapabilities> = new Map();
  private messageQueue: SuperBitMessage[] = [];
  private maxQueueSize = 1000;

  async initialize(): Promise<void> {
    return Promise.resolve();
  }

  async sendMessage(message: SuperBitMessage): Promise<void> {
    const worker = this.workers.get(message.targetVmId);
    
    if (!worker) {
      throw new Error(`Worker not found for VM ID: ${message.targetVmId}`);
    }

    if (this.messageQueue.length >= this.maxQueueSize) {
      throw new Error('Message queue full - backpressure applied');
    }

    this.messageQueue.push(message);

    return new Promise((resolve, reject) => {
      try {
        const workerMessage: WorkerMessage = {
          type: 'message',
          data: message,
        };
        worker.postMessage(workerMessage);
        this.messageQueue = this.messageQueue.filter(m => m.id !== message.id);
        resolve();
      } catch (error) {
        reject(error);
        this.emitFault(message.targetVmId, error as Error);
      }
    });
  }

  async advertiseCapabilities(capabilities: VMCapabilities): Promise<void> {
    this.capabilities.set(capabilities.vmId, capabilities);
    return Promise.resolve();
  }

  async discoverVMs(): Promise<VMCapabilities[]> {
    return Array.from(this.capabilities.values());
  }

  async close(): Promise<void> {
    const terminationPromises = Array.from(this.workers.values()).map(
      (worker) =>
        new Promise<void>((resolve) => {
          worker.terminate().then(() => resolve());
        })
    );
    await Promise.all(terminationPromises);
    this.workers.clear();
    this.capabilities.clear();
  }

  registerWorker(vmId: string, worker: Worker): void {
    this.workers.set(vmId, worker);

    worker.on('message', (msg: WorkerMessage) => {
      switch (msg.type) {
        case 'message':
          this.emitMessage(msg.data as SuperBitMessage);
          break;
        case 'health':
          this.emitHealth(msg.data as HealthStatus);
          break;
        case 'capabilities':
          this.capabilities.set(vmId, msg.data as VMCapabilities);
          break;
      }
    });

    worker.on('error', (error) => {
      this.emitFault(vmId, error);
      this.emitHealth({
        vmId,
        status: 'failed',
        timestamp: Date.now(),
        errorMessage: error.message,
      });
    });

    worker.on('exit', (code) => {
      if (code !== 0) {
        this.emitFault(vmId, new Error(`Worker exited with code ${code}`));
        this.emitHealth({
          vmId,
          status: 'failed',
          timestamp: Date.now(),
          errorMessage: `Worker process exited with code ${code}`,
        });
      }
    });
  }

  getQueueSize(): number {
    return this.messageQueue.length;
  }

  getInFlightMessages(): SuperBitMessage[] {
    return [...this.messageQueue];
  }
}
