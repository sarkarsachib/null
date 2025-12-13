import { SuperBitMessage, TransportAdapter } from './transport_adapter';

function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export interface MessageBusConfig {
  maxRetries?: number;
  retryDelayMs?: number;
  messageTimeoutMs?: number;
}

interface PendingMessage {
  message: SuperBitMessage;
  retries: number;
  timestamp: number;
  resolve: (value: void) => void;
  reject: (error: Error) => void;
}

export class SuperBitMessageBus {
  private transport: TransportAdapter;
  private pendingMessages: Map<string, PendingMessage> = new Map();
  private messageHistory: SuperBitMessage[] = [];
  private maxHistorySize = 1000;
  private maxRetries: number;
  private retryDelayMs: number;
  private messageTimeoutMs: number;
  private timeoutCheckInterval?: NodeJS.Timeout;

  constructor(transport: TransportAdapter, config: MessageBusConfig = {}) {
    this.transport = transport;
    this.maxRetries = config.maxRetries ?? 3;
    this.retryDelayMs = config.retryDelayMs ?? 1000;
    this.messageTimeoutMs = config.messageTimeoutMs ?? 30000;

    this.transport.receiveMessage((message) => this.handleReceivedMessage(message));
    this.startTimeoutChecker();
  }

  async sendMessage(
    sourceVmId: string,
    targetVmId: string,
    messageType: string,
    payload: unknown
  ): Promise<void> {
    const message: SuperBitMessage = {
      id: generateUUID(),
      sourceVmId,
      targetVmId,
      messageType,
      payload: this.serializePayload(payload),
      timestamp: Date.now(),
    };

    return this.sendMessageWithRetry(message);
  }

  private async sendMessageWithRetry(message: SuperBitMessage): Promise<void> {
    return new Promise((resolve, reject) => {
      this.pendingMessages.set(message.id, {
        message,
        retries: 0,
        timestamp: Date.now(),
        resolve,
        reject,
      });

      this.attemptSend(message.id);
    });
  }

  private async attemptSend(messageId: string): Promise<void> {
    const pending = this.pendingMessages.get(messageId);
    if (!pending) return;

    try {
      await this.transport.sendMessage(pending.message);
      this.messageHistory.push(pending.message);
      if (this.messageHistory.length > this.maxHistorySize) {
        this.messageHistory.shift();
      }
      this.pendingMessages.delete(messageId);
      pending.resolve();
    } catch (error) {
      pending.retries++;
      if (pending.retries >= this.maxRetries) {
        this.pendingMessages.delete(messageId);
        pending.reject(
          new Error(
            `Failed to send message after ${this.maxRetries} retries: ${(error as Error).message}`
          )
        );
      } else {
        setTimeout(() => this.attemptSend(messageId), this.retryDelayMs);
      }
    }
  }

  private handleReceivedMessage(message: SuperBitMessage): void {
    this.messageHistory.push(message);
    if (this.messageHistory.length > this.maxHistorySize) {
      this.messageHistory.shift();
    }
  }

  private startTimeoutChecker(): void {
    this.timeoutCheckInterval = setInterval(() => {
      const now = Date.now();
      for (const [messageId, pending] of this.pendingMessages.entries()) {
        if (now - pending.timestamp > this.messageTimeoutMs) {
          this.pendingMessages.delete(messageId);
          pending.reject(new Error(`Message timeout after ${this.messageTimeoutMs}ms`));
        }
      }
    }, 5000);
    this.timeoutCheckInterval.unref();
  }

  destroy(): void {
    if (this.timeoutCheckInterval) {
      clearInterval(this.timeoutCheckInterval);
    }
  }

  private serializePayload(payload: unknown): Buffer {
    const jsonString = JSON.stringify(payload);
    return Buffer.from(jsonString, 'utf-8');
  }

  deserializePayload(buffer: Buffer): unknown {
    const jsonString = buffer.toString('utf-8');
    return JSON.parse(jsonString);
  }

  getMessageHistory(): SuperBitMessage[] {
    return [...this.messageHistory];
  }

  getPendingMessageCount(): number {
    return this.pendingMessages.size;
  }

  replayInFlightMessages(vmId: string): Promise<void[]> {
    const inFlightMessages = Array.from(this.pendingMessages.values())
      .filter((pending) => pending.message.targetVmId === vmId)
      .map((pending) => {
        const newMessage = { ...pending.message, id: generateUUID(), timestamp: Date.now() };
        return this.sendMessageWithRetry(newMessage);
      });

    return Promise.all(inFlightMessages);
  }
}
