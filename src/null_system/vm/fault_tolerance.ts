/**
 * Fault tolerance module for hybrid executor
 * Provides checkpointing, snapshots, and replay capabilities
 */

import { Memory } from './memory';
import { ExecutionContext } from './execution_context';

export interface VMSnapshot {
  vmId: string;
  timestamp: number;
  memory: {
    registers: Record<string, number>;
    stackPointer: number;
    heapPointer: number;
  };
  context: {
    programCounter: number;
    callStackDepth: number;
    definedFunctions: string[];
    programLength: number;
  };
  executionCycle: number;
}

export interface ReplayLogEntry {
  cycle: number;
  operation: string;
  args: unknown[];
  result?: unknown;
  timestamp: number;
  vmId: string;
}

export interface CheckpointData {
  snapshotId: string;
  vmSnapshot: VMSnapshot;
  replayLog: ReplayLogEntry[];
  createdAt: number;
  checkpointIndex: number;
}

export class StateSnapshot {
  static createSnapshot(
    vmId: string,
    memory: Memory,
    context: ExecutionContext,
    executionCycle: number
  ): VMSnapshot {
    return {
      vmId,
      timestamp: Date.now(),
      memory: {
        registers: memory.getAllRegisters(),
        stackPointer: memory.getStackPointer(),
        heapPointer: 0,
      },
      context: context.getSnapshot() as unknown as { programCounter: number; callStackDepth: number; definedFunctions: string[]; programLength: number },
      executionCycle,
    };
  }

  static restoreSnapshot(
    snapshot: VMSnapshot,
    memory: Memory,
    _context: ExecutionContext
  ): void {
    memory.reset();

    for (const [register, value] of Object.entries(snapshot.memory.registers)) {
      memory.setRegister(register, value as number);
    }

    memory.setStackPointer(snapshot.memory.stackPointer);
  }
}

export class ReplayLog {
  private entries: ReplayLogEntry[] = [];
  private maxEntries: number;

  constructor(maxEntries: number = 10000) {
    this.maxEntries = maxEntries;
  }

  logOperation(
    cycle: number,
    vmId: string,
    operation: string,
    args: unknown[],
    result?: unknown
  ): void {
    const entry: ReplayLogEntry = {
      cycle,
      operation,
      args,
      result,
      timestamp: Date.now(),
      vmId,
    };

    this.entries.push(entry);

    if (this.entries.length > this.maxEntries) {
      this.entries.shift();
    }
  }

  getEntries(): ReplayLogEntry[] {
    return [...this.entries];
  }

  getEntriesSince(cycle: number): ReplayLogEntry[] {
    return this.entries.filter((e) => e.cycle >= cycle);
  }

  clear(): void {
    this.entries = [];
  }

  size(): number {
    return this.entries.length;
  }
}

export class FaultToleranceManager {
  private snapshots: Map<string, CheckpointData> = new Map();
  private replayLogs: Map<string, ReplayLog> = new Map();
  private checkpointIndex: number = 0;

  createCheckpoint(
    vmId: string,
    snapshot: VMSnapshot,
    replayLog: ReplayLogEntry[]
  ): string {
    const snapshotId = `checkpoint-${vmId}-${this.checkpointIndex++}`;

    const checkpoint: CheckpointData = {
      snapshotId,
      vmSnapshot: snapshot,
      replayLog,
      createdAt: Date.now(),
      checkpointIndex: this.checkpointIndex - 1,
    };

    this.snapshots.set(snapshotId, checkpoint);
    return snapshotId;
  }

  getCheckpoint(snapshotId: string): CheckpointData | undefined {
    return this.snapshots.get(snapshotId);
  }

  listCheckpoints(vmId: string): CheckpointData[] {
    return Array.from(this.snapshots.values())
      .filter((cp) => cp.vmSnapshot.vmId === vmId)
      .sort((a, b) => b.createdAt - a.createdAt);
  }

  deleteCheckpoint(snapshotId: string): boolean {
    return this.snapshots.delete(snapshotId);
  }

  getReplayLog(vmId: string): ReplayLog {
    if (!this.replayLogs.has(vmId)) {
      this.replayLogs.set(vmId, new ReplayLog());
    }
    return this.replayLogs.get(vmId)!;
  }

  clearOldCheckpoints(vmId: string, keepCount: number = 5): void {
    const checkpoints = this.listCheckpoints(vmId);
    if (checkpoints.length > keepCount) {
      const toDelete = checkpoints.slice(keepCount);
      for (const cp of toDelete) {
        this.snapshots.delete(cp.snapshotId);
      }
    }
  }

  getStats(): Record<string, unknown> {
    const checkpointsByVMMap = new Map<string, number>();
    for (const cp of this.snapshots.values()) {
      const vmId = cp.vmSnapshot.vmId;
      checkpointsByVMMap.set(vmId, (checkpointsByVMMap.get(vmId) || 0) + 1);
    }

    const checkpointsByVM: Record<string, number> = {};
    for (const [vmId, count] of checkpointsByVMMap.entries()) {
      checkpointsByVM[vmId] = count;
    }

    const replayLogSizes: Record<string, number> = {};
    for (const [vmId, log] of this.replayLogs.entries()) {
      replayLogSizes[vmId] = log.size();
    }

    return {
      totalCheckpoints: this.snapshots.size,
      checkpointsByVM,
      replayLogSizes,
    };
  }
}
