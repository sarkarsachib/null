/**
 * Channel implementation for inter-coroutine communication
 */

import { Channel, ChannelId, ChannelError, SelectOperation, SelectResult } from './interfaces';
import { createError, ErrorType } from '../errors';

interface ChannelQueue<T> {
  queue: T[];
  closed: boolean;
  waitingReceivers: Array<(value: T | undefined) => void>;
  waitingSenders: Array<(sent: boolean) => void>;
}

/**
 * Implementation of bounded channel with optional buffering
 */
export class ChannelImpl<T = unknown> implements Channel<T> {
  public readonly channelId: ChannelId;
  public readonly capacity: number;
  private queue: ChannelQueue<T>;
  private closeHandlers: Array<() => void> = [];

  constructor(channelId: ChannelId, capacity: number = 0) {
    this.channelId = channelId;
    this.capacity = capacity;
    this.queue = {
      queue: [],
      closed: false,
      waitingReceivers: [],
      waitingSenders: [],
    };
  }

  get isClosed(): boolean {
    return this.queue.closed;
  }

  async send(value: T): Promise<void> {
    // Check if channel is closed
    if (this.queue.closed) {
      throw new ChannelError(this.channelId, 'Cannot send to closed channel');
    }

    // Handle synchronous send for unbuffered channels
    if (this.capacity === 0) {
      return this.sendUnbuffered(value);
    }

    // Handle buffered send
    if (this.queue.queue.length < this.capacity) {
      this.queue.queue.push(value);
      this.resolveNextReceiver();
      return;
    }

    // Channel is full, wait for space
    return new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => {
        // Remove from waiting senders
        const index = this.queue.waitingSenders.indexOf(resolver);
        if (index >= 0) {
          this.queue.waitingSenders.splice(index, 1);
        }
        reject(new ChannelError(this.channelId, 'Send timeout'));
      }, 30000); // 30 second timeout

      const resolver = (sent: boolean) => {
        clearTimeout(timeout);
        if (sent) {
          resolve();
        } else {
          reject(new ChannelError(this.channelId, 'Send cancelled'));
        }
      };

      this.queue.waitingSenders.push(resolver);
    });
  }

  private async sendUnbuffered(value: T): Promise<void> {
    // Check if there's a waiting receiver
    if (this.queue.waitingReceivers.length > 0) {
      const receiver = this.queue.waitingReceivers.shift()!;
      receiver(value);
      return;
    }

    // No receiver waiting, wait for one
    return new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => {
        const index = this.queue.waitingSenders.indexOf(resolver);
        if (index >= 0) {
          this.queue.waitingSenders.splice(index, 1);
        }
        reject(new ChannelError(this.channelId, 'Send timeout - no receiver'));
      }, 30000);

      const resolver = (sent: boolean) => {
        clearTimeout(timeout);
        if (sent) {
          resolve();
        } else {
          reject(new ChannelError(this.channelId, 'Send cancelled'));
        }
      };

      this.queue.waitingSenders.push(resolver);
    });
  }

  async receive(): Promise<T> {
    if (this.queue.closed) {
      throw new ChannelError(this.channelId, 'Cannot receive from closed channel');
    }

    // Try to get value from buffer
    if (this.queue.queue.length > 0) {
      const value = this.queue.queue.shift()!;
      this.resolveNextSender();
      return value;
    }

    // No buffered value, wait for sender
    return new Promise<T>((resolve, reject) => {
      const timeout = setTimeout(() => {
        const index = this.queue.waitingReceivers.indexOf(resolver);
        if (index >= 0) {
          this.queue.waitingReceivers.splice(index, 1);
        }
        reject(new ChannelError(this.channelId, 'Receive timeout'));
      }, 30000);

      const resolver = (value: T | undefined) => {
        clearTimeout(timeout);
        if (value !== undefined) {
          resolve(value);
        } else {
          reject(new ChannelError(this.channelId, 'Received undefined value'));
        }
      };

      this.queue.waitingReceivers.push(resolver);
    });
  }

  tryReceive(): T | undefined {
    if (this.queue.queue.length > 0) {
      const value = this.queue.queue.shift()!;
      this.resolveNextSender();
      return value;
    }
    return undefined;
  }

  async close(): Promise<void> {
    if (this.queue.closed) {
      return; // Already closed
    }

    this.queue.closed = true;

    // Resolve all waiting promises with appropriate values
    while (this.queue.waitingReceivers.length > 0) {
      const receiver = this.queue.waitingReceivers.shift()!;
      receiver(undefined);
    }

    while (this.queue.waitingSenders.length > 0) {
      const sender = this.queue.waitingSenders.shift()!;
      sender(false);
    }

    // Notify close handlers
    this.closeHandlers.forEach(handler => {
      try {
        handler();
      } catch (error) {
        console.error(`Error in channel close handler for ${this.channelId}:`, error);
      }
    });
  }

  onClose(handler: () => void): void {
    this.closeHandlers.push(handler);
  }

  private resolveNextReceiver(): void {
    if (this.queue.waitingReceivers.length > 0) {
      const receiver = this.queue.waitingReceivers.shift()!;
      if (this.queue.queue.length > 0) {
        const value = this.queue.queue.shift()!;
        receiver(value);
      }
    }
  }

  private resolveNextSender(): void {
    if (this.queue.waitingSenders.length > 0 && this.queue.queue.length < this.capacity) {
      const sender = this.queue.waitingSenders.shift()!;
      sender(true);
    }
  }
}

/**
 * Factory function for creating channels
 */
export function createChannel<T>(channelId: ChannelId, capacity: number = 0): Channel<T> {
  if (capacity < 0) {
    throw new ChannelError(channelId, 'Channel capacity must be non-negative');
  }
  
  return new ChannelImpl<T>(channelId, capacity);
}

/**
 * Select operation implementations
 */
export class SendSelectOperation<T> implements SelectOperation<T> {
  readonly operationId: string;
  readonly operationType: 'send' = 'send';
  
  constructor(
    readonly channel: Channel<T>,
    readonly value: T,
    readonly timeoutMs?: number
  ) {
    this.operationId = `send-${channel.channelId}-${Date.now()}-${Math.random().toString(36).substring(2)}`;
  }
  
  async execute(): Promise<SelectResult<T>> {
    const startTime = Date.now();
    
    try {
      if (this.timeoutMs !== undefined) {
        await Promise.race([
          this.channel.send(this.value),
          new Promise<void>((_, reject) => 
            setTimeout(() => reject(new Error('Select operation timeout')), this.timeoutMs!)
          )
        ]);
      } else {
        await this.channel.send(this.value);
      }
      
      return {
        operationId: this.operationId,
        succeeded: true,
        channelId: this.channel.channelId,
      };
    } catch (error) {
      return {
        operationId: this.operationId,
        succeeded: false,
        channelId: this.channel.channelId,
        error: error as Error,
      };
    }
  }
}

export class ReceiveSelectOperation<T> implements SelectOperation<T> {
  readonly operationId: string;
  readonly operationType: 'receive' = 'receive';
  
  constructor(
    readonly channel: Channel<T>,
    readonly timeoutMs?: number
  ) {
    this.operationId = `recv-${channel.channelId}-${Date.now()}-${Math.random().toString(36).substring(2)}`;
  }
  
  async execute(): Promise<SelectResult<T>> {
    try {
      let value: T;
      
      if (this.timeoutMs !== undefined) {
        value = await Promise.race([
          this.channel.receive(),
          new Promise<T>((_, reject) => 
            setTimeout(() => reject(new Error('Select operation timeout')), this.timeoutMs!)
          )
        ]);
      } else {
        value = await this.channel.receive();
      }
      
      return {
        operationId: this.operationId,
        succeeded: true,
        value,
        channelId: this.channel.channelId,
      };
    } catch (error) {
      return {
        operationId: this.operationId,
        succeeded: false,
        channelId: this.channel.channelId,
        error: error as Error,
      };
    }
  }
}