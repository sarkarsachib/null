/**
 * Coroutine scheduler for managing task execution
 */

import { 
  CoroutineScheduler, 
  CoroutineTask, 
  TaskState, 
  TaskResult, 
  TaskPriority,
  SchedulerError,
  TaskExecutionContext,
  CoroutineId
} from './interfaces';

interface ScheduledTask {
  task: CoroutineTask;
  priority: TaskPriority;
  scheduledAt: number;
  executionPromise?: Promise<void>;
}

interface TaskStatus {
  state: TaskState;
  startTime?: number;
  endTime?: number;
  priority?: TaskPriority;
}

/**
 * Coroutine scheduler implementation
 */
export class CoroutineSchedulerImpl implements CoroutineScheduler {
  readonly schedulerId: string;
  private tasks: Map<CoroutineId, ScheduledTask> = new Map();
  private taskStatus: Map<CoroutineId, TaskStatus> = new Map();
  private executionQueue: Array<CoroutineId> = [];
  private isRunning = false;
  private maxConcurrentTasks: number;
  private shutdownPromise?: Promise<void>;

  constructor(schedulerId: string, maxConcurrentTasks: number = 10) {
    this.schedulerId = schedulerId;
    this.maxConcurrentTasks = maxConcurrentTasks;
  }

  async schedule(task: CoroutineTask): Promise<void> {
    if (this.isShutdown) {
      throw new SchedulerError(this.schedulerId, 'Scheduler is shutdown');
    }

    if (this.tasks.has(task.taskId)) {
      throw new SchedulerError(this.schedulerId, `Task ${task.taskId} already scheduled`);
    }

    const scheduledTask: ScheduledTask = {
      task,
      priority: task.priority,
      scheduledAt: Date.now(),
    };

    this.tasks.set(task.taskId, scheduledTask);
    this.taskStatus.set(task.taskId, { state: TaskState.PENDING, priority: task.priority });
    this.executionQueue.push(task.taskId);
    
    // Sort execution queue by priority
    this.executionQueue.sort((a, b) => {
      const taskA = this.tasks.get(a)!;
      const taskB = this.tasks.get(b)!;
      return taskB.priority - taskA.priority;
    });

    // Start processing if not already running
    this.ensureProcessing();
  }

  async cancel(taskId: CoroutineId): Promise<void> {
    const scheduledTask = this.tasks.get(taskId);
    if (!scheduledTask) {
      throw new SchedulerError(this.schedulerId, `Task ${taskId} not found`);
    }

    const status = this.taskStatus.get(taskId)!;
    if (status.state === TaskState.COMPLETED || status.state === TaskState.FAILED) {
      return; // Already finished
    }

    // Update status
    this.taskStatus.set(taskId, { ...status, state: TaskState.CANCELLED });

    // Cancel the task if it's running
    if (status.state === TaskState.RUNNING) {
      await scheduledTask.task.cancel();
    }

    // Remove from execution queue
    const queueIndex = this.executionQueue.indexOf(taskId);
    if (queueIndex >= 0) {
      this.executionQueue.splice(queueIndex, 1);
    }

    // Clean up
    this.tasks.delete(taskId);
    this.taskStatus.delete(taskId);
  }

  async pause(taskId: CoroutineId): Promise<void> {
    const scheduledTask = this.tasks.get(taskId);
    if (!scheduledTask) {
      throw new SchedulerError(this.schedulerId, `Task ${taskId} not found`);
    }

    const status = this.taskStatus.get(taskId)!;
    if (status.state !== TaskState.RUNNING) {
      throw new SchedulerError(this.schedulerId, `Task ${taskId} is not running`);
    }

    scheduledTask.task.suspend('Manual pause');
    this.taskStatus.set(taskId, { ...status, state: TaskState.SUSPENDED });
  }

  async resume(taskId: CoroutineId): Promise<void> {
    const scheduledTask = this.tasks.get(taskId);
    if (!scheduledTask) {
      throw new SchedulerError(this.schedulerId, `Task ${taskId} not found`);
    }

    const status = this.taskStatus.get(taskId)!;
    if (status.state !== TaskState.SUSPENDED) {
      throw new SchedulerError(this.schedulerId, `Task ${taskId} is not suspended`);
    }

    scheduledTask.task.resume();
    this.taskStatus.set(taskId, { ...status, state: TaskState.PENDING });
    
    if (!this.executionQueue.includes(taskId)) {
      this.executionQueue.push(taskId);
      this.executionQueue.sort((a, b) => {
        const taskA = this.tasks.get(a)!;
        const taskB = this.tasks.get(b)!;
        return taskB.priority - taskA.priority;
      });
    }

    this.ensureProcessing();
  }

  getStatus(taskId: CoroutineId): TaskState {
    const status = this.taskStatus.get(taskId);
    if (!status) {
      throw new SchedulerError(this.schedulerId, `Task ${taskId} not found`);
    }
    return status.state;
  }

  getAllTasks(): Array<{ taskId: CoroutineId; state: TaskState; priority: TaskPriority }> {
    return Array.from(this.taskStatus.entries()).map(([taskId, status]) => ({
      taskId,
      state: status.state,
      priority: status.priority || TaskPriority.NORMAL,
    }));
  }

  async shutdown(): Promise<void> {
    if (this.shutdownPromise) {
      return this.shutdownPromise;
    }

    this.shutdownPromise = this.performShutdown();
    return this.shutdownPromise;
  }

  private get isShutdown(): boolean {
    return this.shutdownPromise !== undefined;
  }

  private ensureProcessing(): void {
    if (this.isRunning || this.isShutdown) {
      return;
    }

    this.isRunning = true;
    
    // Process tasks asynchronously
    Promise.resolve().then(() => this.processTasks());
  }

  private async processTasks(): Promise<void> {
    try {
      while (!this.isShutdown && this.executionQueue.length > 0) {
        // Check if we can start more tasks
        const runningCount = Array.from(this.taskStatus.values())
          .filter(status => status.state === TaskState.RUNNING).length;
        
        if (runningCount >= this.maxConcurrentTasks) {
          // Wait a bit before checking again
          await new Promise(resolve => setTimeout(resolve, 10));
          continue;
        }

        // Get next task to execute
        const taskId = this.executionQueue.shift();
        if (!taskId) {
          continue;
        }

        const scheduledTask = this.tasks.get(taskId);
        if (!scheduledTask) {
          continue; // Task was cancelled
        }

        const status = this.taskStatus.get(taskId)!;
        if (status.state !== TaskState.PENDING) {
          continue; // Task is no longer pending
        }

        // Update status to running
        const newStatus = { ...status, state: TaskState.RUNNING, startTime: Date.now() };
        this.taskStatus.set(taskId, newStatus);

        // Execute the task
        const context = this.createTaskExecutionContext(taskId);
        const executionPromise = this.executeTask(scheduledTask.task, context, taskId);
        scheduledTask.executionPromise = executionPromise;

        // Don't await here to allow parallel execution
        executionPromise.catch(error => {
          console.error(`Task ${taskId} execution failed:`, error);
        });
      }
    } finally {
      this.isRunning = false;
    }
  }

  private createTaskExecutionContext(taskId: CoroutineId): TaskExecutionContext {
    const variables = new Map<string, unknown>();
    const deadlines = new Map<string, number>();
    const timeouts = new Map<string, NodeJS.Timeout>();
    
    return {
      taskId,
      supervisorId: this.schedulerId,
      variables,
      deadlines,
      timeouts,
      
      setVariable: (name: string, value: unknown) => {
        variables.set(name, value);
      },
      
      getVariable: (name: string) => {
        return variables.get(name);
      },
      
      setDeadline: (deadlineId: string, deadlineMs: number) => {
        const deadline = Date.now() + deadlineMs;
        deadlines.set(deadlineId, deadline);
      },
      
      clearDeadline: (deadlineId: string) => {
        deadlines.delete(deadlineId);
      },
    };
  }

  private async executeTask(
    task: CoroutineTask, 
    context: TaskExecutionContext, 
    taskId: CoroutineId
  ): Promise<void> {
    try {
      const result = await task.execute(context);
      
      const status = this.taskStatus.get(taskId)!;
      const endTime = Date.now();
      
      // Update final status
      this.taskStatus.set(taskId, {
        ...status,
        state: result.state,
        endTime,
      });

      console.log(`Task ${taskId} completed with state: ${result.state}`);
      
    } catch (error) {
      const status = this.taskStatus.get(taskId)!;
      const endTime = Date.now();
      
      // Mark as failed
      this.taskStatus.set(taskId, {
        ...status,
        state: TaskState.FAILED,
        endTime,
      });

      console.error(`Task ${taskId} failed:`, error);
      
    } finally {
      // Clean up
      this.tasks.delete(taskId);
      
      // Continue processing other tasks
      this.ensureProcessing();
    }
  }

  private async performShutdown(): Promise<void> {
    // Cancel all pending tasks
    const taskIds = Array.from(this.tasks.keys());
    await Promise.all(taskIds.map(taskId => this.cancel(taskId).catch(error => {
      console.error(`Error cancelling task ${taskId} during shutdown:`, error);
    })));

    this.isRunning = false;
  }
}

/**
 * Factory function for creating schedulers
 */
export function createScheduler(
  schedulerId?: string, 
  maxConcurrentTasks: number = 10
): CoroutineScheduler {
  const id = schedulerId || `scheduler-${Date.now()}-${Math.random().toString(36).substring(2)}`;
  return new CoroutineSchedulerImpl(id, maxConcurrentTasks);
}