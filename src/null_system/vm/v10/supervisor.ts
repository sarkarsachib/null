/**
 * Structured concurrency supervisor for hierarchical task management
 */

import {
  Supervisor,
  SupervisorMetrics,
  CoroutineTask,
  TaskResult,
  TaskState,
  V10RuntimeError,
  SupervisorError
} from './interfaces';

interface ChildSupervisor {
  supervisorId: string;
  supervisor: Supervisor;
  startedAt: number;
}

interface SupervisedTask {
  task: CoroutineTask;
  startedAt: number;
  promise: Promise<TaskResult>;
  status: TaskState;
}

/**
 * Structured concurrency supervisor implementation
 */
export class SupervisorImpl implements Supervisor {
  readonly supervisorId: string;
  readonly parentSupervisorId?: string;
  readonly childSupervisorIds: Set<string> = new Set();
  
  private childSupervisors: Map<string, ChildSupervisor> = new Map();
  private supervisedTasks: Map<string, SupervisedTask> = new Map();
  private metrics: SupervisorMetrics;
  private isRunning = false;
  private shutdownPromise?: Promise<void>;

  constructor(supervisorId: string, parentSupervisorId?: string) {
    this.supervisorId = supervisorId;
    this.parentSupervisorId = parentSupervisorId;
    this.metrics = {
      activeTasks: 0,
      completedTasks: 0,
      failedTasks: 0,
      averageExecutionTime: 0,
      totalExecutionTime: 0,
      memoryUsage: 0,
    };
  }

  async start(): Promise<void> {
    if (this.shutdownPromise) {
      throw new SupervisorError(this.supervisorId, 'Supervisor is already shutting down');
    }
    this.isRunning = true;
    console.log(`Supervisor ${this.supervisorId} started${this.parentSupervisorId ? ` (child of ${this.parentSupervisorId})` : ''}`);
  }

  async stop(): Promise<void> {
    if (this.shutdownPromise) {
      return this.shutdownPromise;
    }

    this.shutdownPromise = this.performStop();
    return this.shutdownPromise;
  }

  async supervise(task: CoroutineTask): Promise<TaskResult> {
    if (!this.isRunning) {
      throw new SupervisorError(this.supervisorId, 'Supervisor is not running');
    }

    if (task.supervisorId !== this.supervisorId) {
      throw new SupervisorError(this.supervisorId, `Task ${task.taskId} does not belong to this supervisor`);
    }

    if (this.supervisedTasks.has(task.taskId)) {
      throw new SupervisorError(this.supervisorId, `Task ${task.taskId} is already being supervised`);
    }

    const startedAt = Date.now();
    const executionPromise = this.executeTaskUnderSupervision(task);

    const supervisedTask: SupervisedTask = {
      task,
      startedAt,
      promise: executionPromise,
      status: TaskState.PENDING,
    };

    this.supervisedTasks.set(task.taskId, supervisedTask);
    this.updateMetrics();

    // Start monitoring the task
    executionPromise
      .then(result => {
        this.taskCompleted(task.taskId, result);
      })
      .catch(error => {
        this.taskFailed(task.taskId, error);
      });

    return executionPromise;
  }

  getMetrics(): SupervisorMetrics {
    return { ...this.metrics };
  }

  /**
   * Add a child supervisor to this supervisor
   */
  async addChildSupervisor(childSupervisor: Supervisor): Promise<void> {
    if (!this.isRunning) {
      throw new SupervisorError(this.supervisorId, 'Supervisor is not running');
    }

    if (this.childSupervisors.has(childSupervisor.supervisorId)) {
      throw new SupervisorError(this.supervisorId, `Child supervisor ${childSupervisor.supervisorId} already exists`);
    }

    if (childSupervisor.parentSupervisorId !== this.supervisorId) {
      throw new SupervisorError(this.supervisorId, `Child supervisor must have parent supervisor ID: ${this.supervisorId}`);
    }

    const child: ChildSupervisor = {
      supervisorId: childSupervisor.supervisorId,
      supervisor: childSupervisor,
      startedAt: Date.now(),
    };

    this.childSupervisors.set(childSupervisor.supervisorId, child);
    this.childSupervisorIds.add(childSupervisor.supervisorId);

    try {
      await childSupervisor.start();
    } catch (error) {
      // Remove from children if start fails
      this.childSupervisors.delete(childSupervisor.supervisorId);
      this.childSupervisorIds.delete(childSupervisor.supervisorId);
      throw error;
    }
  }

  /**
   * Remove a child supervisor from this supervisor
   */
  async removeChildSupervisor(childSupervisorId: string): Promise<void> {
    const child = this.childSupervisors.get(childSupervisorId);
    if (!child) {
      throw new SupervisorError(this.supervisorId, `Child supervisor ${childSupervisorId} not found`);
    }

    // Stop the child supervisor
    await child.supervisor.stop();

    // Remove from tracking
    this.childSupervisors.delete(childSupervisorId);
    this.childSupervisorIds.delete(childSupervisorId);
  }

  /**
   * Get all child supervisor IDs
   */
  getChildSupervisorIds(): string[] {
    return Array.from(this.childSupervisorIds);
  }

  /**
   * Get all supervised task IDs
   */
  getSupervisedTaskIds(): string[] {
    return Array.from(this.supervisedTasks.keys());
  }

  /**
   * Check if supervisor is running
   */
  get running(): boolean {
    return this.isRunning && !this.shutdownPromise;
  }

  private async executeTaskUnderSupervision(task: CoroutineTask): Promise<TaskResult> {
    try {
      // Create execution context for the task
      const executionContext = this.createTaskExecutionContext(task);
      
      // Execute the task
      const result = await task.execute(executionContext);
      
      return result;
    } catch (error) {
      // Wrap the error with supervisor context
      throw new V10RuntimeError(
        `Task execution failed in supervisor ${this.supervisorId}: ${error instanceof Error ? error.message : String(error)}`,
        'SUPERVISED_TASK_ERROR',
        {
          supervisorId: this.supervisorId,
          taskId: task.taskId,
          originalError: error,
        }
      );
    }
  }

  private createTaskExecutionContext(task: CoroutineTask): any {
    // This would integrate with the actual task execution context
    // For now, create a minimal context
    return {
      taskId: task.taskId,
      supervisorId: this.supervisorId,
      variables: new Map(),
      deadlines: new Map(),
      timeouts: new Map(),
      
      setVariable: (name: string, value: unknown) => {
        // Implementation would integrate with actual variable management
      },
      
      getVariable: (name: string) => {
        // Implementation would integrate with actual variable management
        return undefined;
      },
      
      setDeadline: (deadlineId: string, deadlineMs: number) => {
        // Implementation would integrate with deadline management
      },
      
      clearDeadline: (deadlineId: string) => {
        // Implementation would integrate with deadline management
      },
    };
  }

  private taskCompleted(taskId: string, result: TaskResult): void {
    const supervisedTask = this.supervisedTasks.get(taskId);
    if (!supervisedTask) {
      return; // Task was already cleaned up
    }

    supervisedTask.status = result.state;
    this.updateMetrics();
    
    console.log(`Supervisor ${this.supervisorId}: Task ${taskId} completed with state ${result.state}`);
  }

  private taskFailed(taskId: string, error: unknown): void {
    const supervisedTask = this.supervisedTasks.get(taskId);
    if (!supervisedTask) {
      return;
    }

    supervisedTask.status = TaskState.FAILED;
    this.updateMetrics();
    
    console.error(`Supervisor ${this.supervisorId}: Task ${taskId} failed:`, error);

    // In structured concurrency, we might want to propagate failure to parent supervisor
    // and cancel sibling tasks
    if (this.parentSupervisorId) {
      // This would be handled by parent supervisor notification
      console.log(`Propagating task failure to parent supervisor ${this.parentSupervisorId}`);
    }
  }

  private updateMetrics(): void {
    const now = Date.now();
    const activeTasks = Array.from(this.supervisedTasks.values())
      .filter(task => task.status === TaskState.PENDING || task.status === TaskState.RUNNING).length;
    
    const completedTasks = Array.from(this.supervisedTasks.values())
      .filter(task => task.status === TaskState.COMPLETED).length;
    
    const failedTasks = Array.from(this.supervisedTasks.values())
      .filter(task => task.status === TaskState.FAILED).length;

    // Calculate execution times
    const completedTaskTimes = Array.from(this.supervisedTasks.values())
      .filter(task => task.status === TaskState.COMPLETED)
      .map(task => now - task.startedAt);
    
    const averageExecutionTime = completedTaskTimes.length > 0 
      ? completedTaskTimes.reduce((sum, time) => sum + time, 0) / completedTaskTimes.length
      : 0;

    const totalExecutionTime = completedTaskTimes.reduce((sum, time) => sum + time, 0);

    this.metrics = {
      activeTasks,
      completedTasks,
      failedTasks,
      averageExecutionTime,
      totalExecutionTime,
      memoryUsage: this.estimateMemoryUsage(),
    };
  }

  private estimateMemoryUsage(): number {
    // Rough estimation of memory usage
    const taskMemory = this.supervisedTasks.size * 1024; // ~1KB per task
    const supervisorMemory = this.childSupervisors.size * 2048; // ~2KB per child supervisor
    return taskMemory + supervisorMemory;
  }

  private async performStop(): Promise<void> {
    console.log(`Stopping supervisor ${this.supervisorId}...`);

    // Stop accepting new tasks
    this.isRunning = false;

    // Cancel all supervised tasks
    const taskPromises = Array.from(this.supervisedTasks.values()).map(async (supervisedTask) => {
      try {
        // Try to cancel the task gracefully
        await supervisedTask.task.cancel();
      } catch (error) {
        console.warn(`Error cancelling task ${supervisedTask.task.taskId}:`, error);
      }
    });

    // Wait for all tasks to be cancelled (with timeout)
    await Promise.race([
      Promise.all(taskPromises),
      new Promise(resolve => setTimeout(resolve, 5000)), // 5 second timeout
    ]);

    // Stop all child supervisors
    const childPromises = Array.from(this.childSupervisors.values()).map(async (child) => {
      try {
        await child.supervisor.stop();
      } catch (error) {
        console.warn(`Error stopping child supervisor ${child.supervisorId}:`, error);
      }
    });

    await Promise.all(childPromises);

    // Clean up
    this.supervisedTasks.clear();
    this.childSupervisors.clear();
    this.childSupervisorIds.clear();

    console.log(`Supervisor ${this.supervisorId} stopped`);
  }
}

/**
 * Factory function for creating supervisors
 */
export function createSupervisor(supervisorId?: string, parentId?: string): Supervisor {
  const id = supervisorId || `supervisor-${Date.now()}-${Math.random().toString(36).substring(2)}`;
  return new SupervisorImpl(id, parentId);
}