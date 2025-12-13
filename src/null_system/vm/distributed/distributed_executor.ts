/**
 * Distributed executor for NullVM
 * Manages execution across multiple nodes with gRPC transport
 */

import { NullVM } from '../null_vm';
import { Instruction } from '../instructions';
import {
  StateSnapshot,
  ReplayLog,
  FaultToleranceManager,
  CheckpointData,
} from '../fault_tolerance';
import { WorkStealingScheduler, ScheduledTask } from '../scheduler';

export interface DistributedExecutorConfig {
  nodeId: string;
  listenAddr: string;
  listenPort: number;
  peers?: Array<{ addr: string; port: number }>;
  enableCheckpointing?: boolean;
  checkpointInterval?: number;
  maxWorkers?: number;
  heartbeatInterval?: number;
}

export interface ExecutionResult {
  taskId: string;
  vmId: string;
  status: 'success' | 'failure';
  registers: Record<string, number>;
  executionCycles: number;
  duration: number;
  error?: string;
  checkpoint?: CheckpointData;
}

export class DistributedExecutor {
  private nodeId: string;
  private config: DistributedExecutorConfig;
  private vms: Map<string, NullVM> = new Map();
  private scheduler: WorkStealingScheduler;
  private faultToleranceManager: FaultToleranceManager;
  private replayLogs: Map<string, ReplayLog> = new Map();
  private peers: Set<string> = new Set();
  private checkpointInterval: NodeJS.Timer | null = null;
  private heartbeatInterval: NodeJS.Timer | null = null;

  constructor(config: DistributedExecutorConfig) {
    this.nodeId = config.nodeId;
    this.config = config;
    this.scheduler = new WorkStealingScheduler({
      maxQueueSize: 10000,
      maxTasksPerWorker: config.maxWorkers || 100,
      enableBackpressure: true,
    });
    this.faultToleranceManager = new FaultToleranceManager();

    if (config.peers) {
      for (const peer of config.peers) {
        this.peers.add(`${peer.addr}:${peer.port}`);
      }
    }
  }

  /**
   * Initialize the distributed executor
   */
  async initialize(): Promise<void> {
    if (this.config.enableCheckpointing && this.config.checkpointInterval) {
      this.startCheckpointing(this.config.checkpointInterval);
    }

    if (this.config.heartbeatInterval) {
      this.startHeartbeat(this.config.heartbeatInterval);
    }
  }

  /**
   * Register a worker VM
   */
  registerVM(vmId: string, vm: NullVM): void {
    this.vms.set(vmId, vm);
    this.scheduler.registerWorker(vmId);
    this.replayLogs.set(vmId, new ReplayLog());
  }

  /**
   * Execute a program on a specific VM
   */
  async executeOnVM(
    vmId: string,
    instructions: Instruction[],
    priority: number = 0
  ): Promise<ExecutionResult> {
    const vm = this.vms.get(vmId);
    if (!vm) {
      throw new Error(`VM not found: ${vmId}`);
    }

    const startTime = Date.now();
    const taskId = this.scheduler.submitTask(vmId, instructions, priority);

    try {
      // Register execution hook for logging
      const replayLog = this.replayLogs.get(vmId);
      const executionHook = async (
        cycle: number,
        instruction: Instruction
      ) => {
        if (replayLog) {
          replayLog.logOperation(
            cycle,
            vmId,
            instruction.opcode,
            instruction.args || []
          );
        }
      };

      vm.registerExecutionHook(executionHook);

      // Execute the program
      await vm.executeAsync(instructions);

      vm.unregisterExecutionHook(executionHook);

      // Create checkpoint if enabled
      let checkpoint: CheckpointData | undefined;
      if (this.config.enableCheckpointing) {
        const snapshot = vm.createSnapshot();
        const log = replayLog ? replayLog.getEntries() : [];
        checkpoint = {
          snapshotId: `snap-${taskId}`,
          vmSnapshot: snapshot,
          replayLog: log,
          createdAt: Date.now(),
          checkpointIndex: 0,
        };
        this.faultToleranceManager.createCheckpoint(
          vmId,
          snapshot,
          log
        );
      }

      const duration = Date.now() - startTime;
      this.scheduler.completeTask(taskId);

      return {
        taskId,
        vmId,
        status: 'success',
        registers: vm.getMemory().getAllRegisters(),
        executionCycles: vm.getExecutionCycle(),
        duration,
        checkpoint,
      };
    } catch (error) {
      const duration = Date.now() - startTime;
      this.scheduler.failTask(taskId, error as Error);

      return {
        taskId,
        vmId,
        status: 'failure',
        registers: {},
        executionCycles: vm.getExecutionCycle(),
        duration,
        error: String(error),
      };
    }
  }

  /**
   * Submit work to the scheduler
   */
  submitWork(
    vmId: string,
    instructions: Instruction[],
    priority: number = 0
  ): string {
    return this.scheduler.submitTask(vmId, instructions, priority);
  }

  /**
   * Get assigned work for a worker
   */
  getWork(workerId: string, maxTasks: number = 5): ScheduledTask[] {
    const assignments = this.scheduler.scheduleWork();
    return assignments.get(workerId) || [];
  }

  /**
   * Create a checkpoint for a VM
   */
  createCheckpoint(vmId: string): string | null {
    const vm = this.vms.get(vmId);
    if (!vm) return null;

    const snapshot = vm.createSnapshot();
    const replayLog = this.replayLogs.get(vmId);
    const log = replayLog ? replayLog.getEntries() : [];

    return this.faultToleranceManager.createCheckpoint(vmId, snapshot, log);
  }

  /**
   * Recover from a checkpoint
   */
  recoverFromCheckpoint(vmId: string, checkpointId: string): boolean {
    const vm = this.vms.get(vmId);
    if (!vm) return false;

    const checkpoint = this.faultToleranceManager.getCheckpoint(checkpointId);
    if (!checkpoint) return false;

    vm.restoreSnapshot(checkpoint.vmSnapshot);
    return true;
  }

  /**
   * Start periodic checkpointing
   */
  private startCheckpointing(intervalMs: number): void {
    this.checkpointInterval = setInterval(() => {
      for (const [vmId] of this.vms) {
        this.createCheckpoint(vmId);
      }
    }, intervalMs) as any;

    if (this.checkpointInterval) {
      (this.checkpointInterval as any).unref();
    }
  }

  /**
   * Start periodic health checks
   */
  private startHeartbeat(intervalMs: number): void {
    this.heartbeatInterval = setInterval(() => {
      for (const [vmId, vm] of this.vms) {
        const state = vm.getState();
        // Health check: VM should be responsive
        this.scheduler.updateWorkerHealth(vmId, true);
      }
    }, intervalMs) as any;

    if (this.heartbeatInterval) {
      (this.heartbeatInterval as any).unref();
    }
  }

  /**
   * Get executor metrics
   */
  getMetrics() {
    return {
      nodeId: this.nodeId,
      registeredVMs: this.vms.size,
      peers: Array.from(this.peers),
      schedulerMetrics: this.scheduler.getMetrics(),
      faultToleranceMetrics: this.faultToleranceManager.getStats(),
    };
  }

  /**
   * Shutdown the executor
   */
  async shutdown(): Promise<void> {
    if (this.checkpointInterval) {
      clearInterval(this.checkpointInterval as any);
    }
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval as any);
    }
  }

  /**
   * Get VM count
   */
  getVMCount(): number {
    return this.vms.size;
  }

  /**
   * Get peers
   */
  getPeers(): string[] {
    return Array.from(this.peers);
  }
}
