/**
 * Work-stealing scheduler for distributed execution
 * Manages worker threads with dynamic load balancing
 */

import { Instruction } from '../instructions';

export interface ScheduledTask {
  id: string;
  vmId: string;
  instructions: Instruction[];
  priority: number;
  createdAt: number;
  startedAt?: number;
  completedAt?: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: unknown;
  error?: Error;
}

export interface WorkerMetrics {
  workerId: string;
  tasksCompleted: number;
  totalExecutionTime: number;
  currentLoad: number;
  lastHeartbeat: number;
  healthy: boolean;
}

export interface SchedulerMetrics {
  totalTasksScheduled: number;
  totalTasksCompleted: number;
  totalTasksFailed: number;
  averageLatency: number;
  workerMetrics: WorkerMetrics[];
  queueSize: number;
  backpressureActive: boolean;
}

export class WorkStealingScheduler {
  private taskQueue: ScheduledTask[] = [];
  private workerQueues: Map<string, ScheduledTask[]> = new Map();
  private completedTasks: Map<string, ScheduledTask> = new Map();
  private workerMetrics: Map<string, WorkerMetrics> = new Map();
  private maxQueueSize: number;
  private maxTasksPerWorker: number;
  private enableBackpressure: boolean;

  constructor(config: {
    maxQueueSize?: number;
    maxTasksPerWorker?: number;
    enableBackpressure?: boolean;
  } = {}) {
    this.maxQueueSize = config.maxQueueSize || 1000;
    this.maxTasksPerWorker = config.maxTasksPerWorker || 50;
    this.enableBackpressure = config.enableBackpressure ?? true;
  }

  /**
   * Register a worker thread
   */
  registerWorker(workerId: string): void {
    if (!this.workerQueues.has(workerId)) {
      this.workerQueues.set(workerId, []);
      this.workerMetrics.set(workerId, {
        workerId,
        tasksCompleted: 0,
        totalExecutionTime: 0,
        currentLoad: 0,
        lastHeartbeat: Date.now(),
        healthy: true,
      });
    }
  }

  /**
   * Unregister a worker thread
   */
  unregisterWorker(workerId: string): void {
    const queue = this.workerQueues.get(workerId);
    if (queue) {
      this.taskQueue.push(...queue);
    }
    this.workerQueues.delete(workerId);
    this.workerMetrics.delete(workerId);
  }

  /**
   * Submit a task for execution
   */
  submitTask(
    vmId: string,
    instructions: Instruction[],
    priority: number = 0
  ): string {
    if (
      this.enableBackpressure &&
      this.taskQueue.length >= this.maxQueueSize
    ) {
      throw new Error(`Queue is full (size: ${this.taskQueue.length})`);
    }

    const taskId = `task-${Date.now()}-${Math.random().toString(36).substring(7)}`;
    const task: ScheduledTask = {
      id: taskId,
      vmId,
      instructions,
      priority,
      createdAt: Date.now(),
      status: 'pending',
    };

    this.taskQueue.push(task);
    this.taskQueue.sort((a, b) => b.priority - a.priority);

    return taskId;
  }

  /**
   * Schedule work to idle/available workers
   */
  scheduleWork(): Map<string, ScheduledTask[]> {
    const assignments = new Map<string, ScheduledTask[]>();

    while (this.taskQueue.length > 0) {
      const targetWorker = this.selectWorker();
      if (!targetWorker) {
        break;
      }

      const task = this.taskQueue.shift();
      if (!task) break;

      task.status = 'running';
      task.startedAt = Date.now();

      const queue = this.workerQueues.get(targetWorker) || [];
      queue.push(task);
      this.workerQueues.set(targetWorker, queue);

      const metrics = this.workerMetrics.get(targetWorker);
      if (metrics) {
        metrics.currentLoad = queue.length;
      }

      if (!assignments.has(targetWorker)) {
        assignments.set(targetWorker, []);
      }
      assignments.get(targetWorker)!.push(task);
    }

    return assignments;
  }

  /**
   * Mark a task as completed
   */
  completeTask(taskId: string, result?: unknown): void {
    for (const [workerId, queue] of this.workerQueues.entries()) {
      const index = queue.findIndex((t) => t.id === taskId);
      if (index !== -1) {
        const task = queue[index];
        task.status = 'completed';
        task.completedAt = Date.now();
        task.result = result;

        queue.splice(index, 1);

        const metrics = this.workerMetrics.get(workerId);
        if (metrics && task.startedAt) {
          metrics.tasksCompleted++;
          metrics.totalExecutionTime += task.completedAt - task.startedAt;
          metrics.currentLoad = queue.length;
        }

        this.completedTasks.set(taskId, task);
        return;
      }
    }
  }

  /**
   * Mark a task as failed
   */
  failTask(taskId: string, error: Error): void {
    for (const queue of this.workerQueues.values()) {
      const index = queue.findIndex((t) => t.id === taskId);
      if (index !== -1) {
        const task = queue[index];
        task.status = 'failed';
        task.error = error;
        queue.splice(index, 1);
        return;
      }
    }
  }

  /**
   * Steal work from overloaded workers
   */
  stealWork(maxTasks: number = 1): ScheduledTask[] {
    const stolen: ScheduledTask[] = [];

    const sortedWorkers = Array.from(this.workerQueues.entries())
      .sort(([, queueA], [, queueB]) => queueB.length - queueA.length);

    for (const [, queue] of sortedWorkers) {
      while (queue.length > this.maxTasksPerWorker && stolen.length < maxTasks) {
        const task = queue.pop();
        if (task) {
          stolen.push(task);
          task.status = 'pending';
        }
      }
      if (stolen.length >= maxTasks) break;
    }

    return stolen;
  }

  /**
   * Select the best worker for a task
   */
  private selectWorker(): string | null {
    let selectedWorker: string | null = null;
    let minLoad = Infinity;

    for (const [workerId, queue] of this.workerQueues.entries()) {
      const metrics = this.workerMetrics.get(workerId);
      if (!metrics || !metrics.healthy) {
        continue;
      }

      if (queue.length < this.maxTasksPerWorker && queue.length < minLoad) {
        minLoad = queue.length;
        selectedWorker = workerId;
      }
    }

    return selectedWorker;
  }

  /**
   * Update worker health status
   */
  updateWorkerHealth(workerId: string, healthy: boolean): void {
    const metrics = this.workerMetrics.get(workerId);
    if (metrics) {
      metrics.healthy = healthy;
      metrics.lastHeartbeat = Date.now();
    }
  }

  /**
   * Get scheduler metrics
   */
  getMetrics(): SchedulerMetrics {
    const completedTasks = Array.from(this.completedTasks.values());
    const failedCount = completedTasks.filter(
      (t) => t.status === 'failed'
    ).length;

    let totalLatency = 0;
    let completedCount = 0;
    for (const task of completedTasks) {
      if (task.completedAt && task.createdAt) {
        totalLatency += task.completedAt - task.createdAt;
        completedCount++;
      }
    }

    const totalLoad = Array.from(this.workerQueues.values()).reduce(
      (sum, queue) => sum + queue.length,
      0
    );
    const avgLoadPerWorker =
      totalLoad / Math.max(1, this.workerQueues.size);

    return {
      totalTasksScheduled: completedTasks.length + this.taskQueue.length,
      totalTasksCompleted: completedCount,
      totalTasksFailed: failedCount,
      averageLatency:
        completedCount > 0
          ? totalLatency / completedCount
          : 0,
      workerMetrics: Array.from(this.workerMetrics.values()),
      queueSize: this.taskQueue.length,
      backpressureActive:
        this.enableBackpressure &&
        avgLoadPerWorker > this.maxTasksPerWorker * 0.8,
    };
  }

  /**
   * Get pending tasks
   */
  getPendingTasks(): ScheduledTask[] {
    return this.taskQueue;
  }

  /**
   * Get task status
   */
  getTaskStatus(taskId: string): ScheduledTask | undefined {
    for (const queue of this.workerQueues.values()) {
      const task = queue.find((t) => t.id === taskId);
      if (task) return task;
    }
    return this.completedTasks.get(taskId);
  }

  /**
   * Clear completed tasks
   */
  clearCompletedTasks(): void {
    this.completedTasks.clear();
  }
}
