/**
 * V10 Runtime main interface
 */

import { 
  V10RuntimeCapability,
  V10Config,
  Channel,
  ChannelId,
  Supervisor,
  CoroutineTask,
  TaskResult,
  CoroutineScheduler,
  ExecutionPipeline,
  CoroutineId,
  TaskPriority,
  TaskState
} from './interfaces';
import { createChannel } from './channel';
import { createSupervisor } from './supervisor';
import { createScheduler } from './scheduler';
import { createExecutionPipeline } from './execution_pipeline';
import { OpCode } from '../instructions';

/**
 * V10 Runtime capability implementation
 */
export class V10RuntimeImpl implements V10RuntimeCapability {
  readonly runtimeId: string;
  readonly version = '10.0.0';
  
  private config: V10Config;
  private channels: Map<ChannelId, Channel> = new Map();
  private supervisors: Map<string, Supervisor> = new Map();
  private schedulers: Map<string, CoroutineScheduler> = new Map();
  private tasks: Map<CoroutineId, CoroutineTask> = new Map();
  private executionPipeline: ExecutionPipeline;

  constructor(runtimeId: string, config: V10Config = {}) {
    this.runtimeId = runtimeId;
    this.config = {
      maxConcurrentTasks: config.maxConcurrentTasks || 10,
      defaultTaskTimeout: config.defaultTaskTimeout || 30000,
      enableProfiling: config.enableProfiling || false,
      enableJit: config.enableJit || false,
      gcConfig: config.gcConfig || {
        incremental: true,
        maxPauseMs: 10,
        heapSizeLimit: 1024 * 1024, // 1MB
      },
    };

    // Create execution pipeline
    this.executionPipeline = createExecutionPipeline();
    
    console.log(`[V10Runtime] Initialized with config:`, this.config);
  }

  async createChannel<T>(capacity?: number): Promise<Channel<T>> {
    const channelId = `channel-${Date.now()}-${Math.random().toString(36).substring(2)}`;
    const channel = createChannel<T>(channelId, capacity || 0);
    
    this.channels.set(channelId, channel);
    console.log(`[V10Runtime] Created channel ${channelId} with capacity ${capacity || 0}`);
    
    return channel;
  }

  async createSupervisor(parentId?: string): Promise<Supervisor> {
    const supervisorId = `supervisor-${Date.now()}-${Math.random().toString(36).substring(2)}`;
    const supervisor = createSupervisor(supervisorId, parentId);
    
    this.supervisors.set(supervisorId, supervisor);
    await supervisor.start();
    
    console.log(`[V10Runtime] Created supervisor ${supervisorId}${parentId ? ` (child of ${parentId})` : ''}`);
    
    return supervisor;
  }

  async spawnTask(task: CoroutineTask): Promise<void> {
    if (this.tasks.has(task.taskId)) {
      throw new Error(`Task ${task.taskId} already exists`);
    }

    this.tasks.set(task.taskId, task);
    
    // Find appropriate scheduler
    const scheduler = this.schedulers.get(task.supervisorId);
    if (!scheduler) {
      throw new Error(`No scheduler found for supervisor ${task.supervisorId}`);
    }

    await scheduler.schedule(task);
    console.log(`[V10Runtime] Spawned task ${task.taskId}`);
  }

  async createScheduler(): Promise<CoroutineScheduler> {
    const schedulerId = `scheduler-${Date.now()}-${Math.random().toString(36).substring(2)}`;
    const scheduler = createScheduler(schedulerId, this.config.maxConcurrentTasks);
    
    this.schedulers.set(schedulerId, scheduler);
    
    console.log(`[V10Runtime] Created scheduler ${schedulerId}`);
    
    return scheduler;
  }

  getExecutionPipeline(): ExecutionPipeline {
    return this.executionPipeline;
  }

  configure(config: V10Config): void {
    this.config = { ...this.config, ...config };
    console.log('[V10Runtime] Configuration updated:', this.config);
  }

  /**
   * Get channel by ID
   */
  getChannel(channelId: ChannelId): Channel | undefined {
    return this.channels.get(channelId);
  }

  /**
   * Get supervisor by ID
   */
  getSupervisor(supervisorId: string): Supervisor | undefined {
    return this.supervisors.get(supervisorId);
  }

  /**
   * Get scheduler by ID
   */
  getScheduler(schedulerId: string): CoroutineScheduler | undefined {
    return this.schedulers.get(schedulerId);
  }

  /**
   * Get task by ID
   */
  getTask(taskId: CoroutineId): CoroutineTask | undefined {
    return this.tasks.get(taskId);
  }

  /**
   * List all active channels
   */
  listChannels(): ChannelId[] {
    return Array.from(this.channels.keys());
  }

  /**
   * List all supervisors
   */
  listSupervisors(): string[] {
    return Array.from(this.supervisors.keys());
  }

  /**
   * List all schedulers
   */
  listSchedulers(): string[] {
    return Array.from(this.schedulers.keys());
  }

  /**
   * List all tasks
   */
  listTasks(): CoroutineId[] {
    return Array.from(this.tasks.keys());
  }

  /**
   * Clean up resources
   */
  async shutdown(): Promise<void> {
    console.log('[V10Runtime] Shutting down...');

    // Cancel all tasks
    const taskPromises = Array.from(this.tasks.keys()).map(async (taskId) => {
      try {
        const task = this.tasks.get(taskId);
        if (task) {
          await task.cancel();
        }
      } catch (error) {
        console.warn(`Error cancelling task ${taskId}:`, error);
      }
    });

    await Promise.allSettled(taskPromises);
    this.tasks.clear();

    // Stop all schedulers
    const schedulerPromises = Array.from(this.schedulers.values()).map(async (scheduler) => {
      try {
        await scheduler.shutdown();
      } catch (error) {
        console.warn('Error shutting down scheduler:', error);
      }
    });

    await Promise.allSettled(schedulerPromises);
    this.schedulers.clear();

    // Stop all supervisors
    const supervisorPromises = Array.from(this.supervisors.values()).map(async (supervisor) => {
      try {
        await supervisor.stop();
      } catch (error) {
        console.warn('Error stopping supervisor:', error);
      }
    });

    await Promise.allSettled(supervisorPromises);
    this.supervisors.clear();

    // Close all channels
    const channelPromises = Array.from(this.channels.values()).map(async (channel) => {
      try {
        await channel.close();
      } catch (error) {
        console.warn('Error closing channel:', error);
      }
    });

    await Promise.allSettled(channelPromises);
    this.channels.clear();

    console.log('[V10Runtime] Shutdown complete');
  }
}

/**
 * Factory function for creating V10 runtime
 */
export function createV10Runtime(runtimeId?: string, config?: V10Config): V10RuntimeCapability {
  const id = runtimeId || `v10-runtime-${Date.now()}-${Math.random().toString(36).substring(2)}`;
  return new V10RuntimeImpl(id, config);
}