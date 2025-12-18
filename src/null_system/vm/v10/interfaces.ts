/**
 * V10 Runtime Interfaces - Core capability interfaces for advanced runtime features
 */

import { Instruction, OpCode } from '../instructions';

/**
 * Coroutine identifier
 */
export type CoroutineId = string;

/**
 * Channel identifier
 */
export type ChannelId = string;

/**
 * Task priority levels
 */
export enum TaskPriority {
  LOW = 0,
  NORMAL = 1,
  HIGH = 2,
  CRITICAL = 3,
}

/**
 * Task states
 */
export enum TaskState {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  SUSPENDED = 'SUSPENDED',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
}

/**
 * Structured concurrency supervisor interface
 */
export interface Supervisor {
  readonly supervisorId: string;
  readonly parentSupervisorId?: string;
  readonly childSupervisorIds: Set<string>;
  
  start(): Promise<void>;
  stop(): Promise<void>;
  supervise(task: CoroutineTask): Promise<TaskResult>;
  getMetrics(): SupervisorMetrics;
}

/**
 * Coroutine task interface
 */
export interface CoroutineTask {
  readonly taskId: CoroutineId;
  readonly supervisorId: string;
  readonly priority: TaskPriority;
  readonly state: TaskState;
  readonly startTime: number;
  readonly instructions: Instruction[];
  readonly instructionPointer: number;
  
  execute(context: TaskExecutionContext): Promise<TaskResult>;
  suspend(reason: string): void;
  resume(): void;
  cancel(): Promise<void>;
}

/**
 * Task execution context
 */
export interface TaskExecutionContext {
  readonly taskId: CoroutineId;
  readonly supervisorId: string;
  variables: Map<string, unknown>;
  readonly deadlines: Map<string, number>;
  readonly timeouts: Map<string, NodeJS.Timeout>;
  
  setVariable(name: string, value: unknown): void;
  getVariable(name: string): unknown | undefined;
  setDeadline(deadlineId: string, deadlineMs: number): void;
  clearDeadline(deadlineId: string): void;
}

/**
 * Task execution result
 */
export interface TaskResult {
  readonly taskId: CoroutineId;
  readonly state: TaskState;
  readonly startTime: number;
  readonly endTime: number;
  readonly executionTime: number;
  readonly result?: unknown;
  readonly error?: Error;
  readonly metadata: Record<string, unknown>;
}

/**
 * Channel interface for communication between coroutines
 */
export interface Channel<T = unknown> {
  readonly channelId: ChannelId;
  readonly capacity: number;
  readonly isClosed: boolean;
  
  send(value: T): Promise<void>;
  receive(): Promise<T>;
  tryReceive(): T | undefined;
  close(): Promise<void>;
  onClose(handler: () => void): void;
}

/**
 * Select operation interface for channel multiplexing
 */
export interface SelectOperation<T = unknown> {
  readonly operationId: string;
  readonly channel: Channel<T>;
  readonly operationType: 'send' | 'receive';
  readonly value?: T;
  readonly timeoutMs?: number;
  
  execute(): Promise<SelectResult<T>>;
}

/**
 * Select operation result
 */
export interface SelectResult<T = unknown> {
  readonly operationId: string;
  readonly succeeded: boolean;
  readonly value?: T;
  readonly channelId: ChannelId;
  readonly error?: Error;
}

/**
 * Coroutine scheduler interface
 */
export interface CoroutineScheduler {
  readonly schedulerId: string;
  
  schedule(task: CoroutineTask): Promise<void>;
  cancel(taskId: CoroutineId): Promise<void>;
  pause(taskId: CoroutineId): Promise<void>;
  resume(taskId: CoroutineId): Promise<void>;
  getStatus(taskId: CoroutineId): TaskState;
  getAllTasks(): Array<{ taskId: CoroutineId; state: TaskState; priority: TaskPriority }>;
  shutdown(): Promise<void>;
}

/**
 * V10 Runtime configuration
 */
export interface V10Config {
  maxConcurrentTasks?: number;
  defaultTaskTimeout?: number;
  enableProfiling?: boolean;
  enableJit?: boolean;
  gcConfig?: {
    incremental: boolean;
    maxPauseMs?: number;
    heapSizeLimit?: number;
  };
}

/**
 * Execution pipeline stages
 */
export interface ExecutionPipeline {
  interpreter: Interpreter;
  jitCompiler?: JITCompiler;
  profiler?: Profiler;
  gcManager?: GarbageCollector;
  
  execute(instruction: Instruction, context: TaskExecutionContext): Promise<ExecutionResult>;
  getHotPaths(): HotPath[];
}

/**
 * Interpreter interface
 */
export interface Interpreter {
  readonly interpreterId: string;
  
  execute(instruction: Instruction, context: TaskExecutionContext): Promise<ExecutionResult>;
  getInstructionCount(): number;
  resetCounters(): void;
}

/**
 * Execution result
 */
export interface ExecutionResult {
  readonly success: boolean;
  readonly value?: unknown;
  readonly nextInstruction: number;
  readonly executionTime: number;
  readonly profiling?: ProfilingData;
}

/**
 * JIT Compiler interface
 */
export interface JITCompiler {
  readonly compilerId: string;
  
  compile(functionId: string, instructions: Instruction[]): Promise<CompiledFunction>;
  getCompilationStats(): CompilationStats;
  clearCache(): void;
}

/**
 * Compiled function
 */
export interface CompiledFunction {
  readonly functionId: string;
  readonly originalInstructions: Instruction[];
  readonly compiledCode: unknown;
  readonly metadata: CompilationMetadata;
}

/**
 * Compilation statistics
 */
export interface CompilationStats {
  readonly totalFunctions: number;
  readonly totalCompilations: number;
  readonly cacheHitRate: number;
  readonly averageCompilationTime: number;
}

/**
 * Compilation metadata
 */
export interface CompilationMetadata {
  readonly compilationTime: number;
  readonly hotnessScore: number;
  readonly dependencies: string[];
  readonly optimizationLevel: number;
}

/**
 * Profiler interface
 */
export interface Profiler {
  readonly profilerId: string;
  
  startProfiling(taskId: CoroutineId): void;
  stopProfiling(taskId: CoroutineId): ProfilingData;
  recordExecution(instruction: Instruction, context: TaskExecutionContext, executionTime: number): void;
  getHotPaths(): HotPath[];
  getProfileSummary(): ProfileSummary;
}

/**
 * Hot path information
 */
export interface HotPath {
  readonly pathId: string;
  readonly instructionCount: number;
  readonly executionCount: number;
  readonly averageExecutionTime: number;
  readonly instructions: Instruction[];
}

/**
 * Profiling data
 */
export interface ProfilingData {
  readonly taskId: CoroutineId;
  readonly startTime: number;
  readonly endTime: number;
  readonly instructionCount: number;
  readonly totalExecutionTime: number;
  readonly instructionBreakdown: Map<Instruction, InstructionProfilingData>;
}

/**
 * Instruction-level profiling data
 */
export interface InstructionProfilingData {
  readonly executionCount: number;
  readonly totalTime: number;
  readonly averageTime: number;
  readonly lastExecuted: number;
}

/**
 * Profile summary
 */
export interface ProfileSummary {
  readonly totalInstructionsExecuted: number;
  readonly totalExecutionTime: number;
  readonly hotPaths: HotPath[];
  readonly instructionFrequency: Array<{ opcode: string; count: number }>;
}

/**
 * Garbage Collector interface
 */
export interface GarbageCollector {
  readonly gcId: string;
  
  collect(): Promise<GCResult>;
  getStats(): GCStats;
  configure(config: Partial<GCConfig>): void;
}

/**
 * GC configuration
 */
export interface GCConfig {
  readonly incremental: boolean;
  readonly maxPauseMs: number;
  readonly heapSizeLimit: number;
}

/**
 * GC statistics
 */
export interface GCStats {
  readonly totalCollections: number;
  readonly totalTime: number;
  readonly averageTime: number;
  readonly memoryFreed: number;
  readonly heapSize: number;
}

/**
 * GC result
 */
export interface GCResult {
  readonly success: boolean;
  readonly memoryFreed: number;
  readonly collectionTime: number;
  readonly heapSizeBefore: number;
  readonly heapSizeAfter: number;
}

/**
 * Supervisor metrics
 */
export interface SupervisorMetrics {
  readonly activeTasks: number;
  readonly completedTasks: number;
  readonly failedTasks: number;
  readonly averageExecutionTime: number;
  readonly totalExecutionTime: number;
  readonly memoryUsage: number;
}

/**
 * V10 Runtime capability interface
 */
export interface V10RuntimeCapability {
  readonly runtimeId: string;
  readonly version: string;
  
  createChannel<T>(capacity?: number): Promise<Channel<T>>;
  createSupervisor(parentId?: string): Promise<Supervisor>;
  spawnTask(task: CoroutineTask): Promise<void>;
  createScheduler(): Promise<CoroutineScheduler>;
  getExecutionPipeline(): ExecutionPipeline;
  configure(config: V10Config): void;
}

/**
 * Error classes for V10 runtime
 */
export class V10RuntimeError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'V10RuntimeError';
  }
}

export class SupervisorError extends V10RuntimeError {
  constructor(supervisorId: string, message: string, details?: Record<string, unknown>) {
    super(`Supervisor ${supervisorId}: ${message}`, 'SUPERVISOR_ERROR', details);
    this.name = 'SupervisorError';
  }
}

export class TaskError extends V10RuntimeError {
  constructor(taskId: CoroutineId, message: string, details?: Record<string, unknown>) {
    super(`Task ${taskId}: ${message}`, 'TASK_ERROR', details);
    this.name = 'TaskError';
  }
}

export class ChannelError extends V10RuntimeError {
  constructor(channelId: ChannelId, message: string, details?: Record<string, unknown>) {
    super(`Channel ${channelId}: ${message}`, 'CHANNEL_ERROR', details);
    this.name = 'ChannelError';
  }
}

export class SchedulerError extends V10RuntimeError {
  constructor(schedulerId: string, message: string, details?: Record<string, unknown>) {
    super(`Scheduler ${schedulerId}: ${message}`, 'SCHEDULER_ERROR', details);
    this.name = 'SchedulerError';
  }
}