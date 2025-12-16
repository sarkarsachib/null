/**
 * Execution context for NullVM - manages function calls, return addresses, and state
 */

import { Instruction } from './instructions';
import { createError, ErrorType } from './errors';

export interface StackFrame {
  functionName: string;
  returnAddress: number;
  savedStackPointer: number;
  locals: Map<string, number>;
}

export type TraceHook = (
  event: 'instruction' | 'error' | 'function_call' | 'function_return',
  data: Record<string, unknown>
) => void;

export interface ConstraintDirective {
  id: string;
  register: string;
  operator: string;
  value: number;
  createdAt: number;
  severity: 'error' | 'alert';
}

export class ExecutionContext {
  private callStack: StackFrame[] = [];
  program: Instruction[] = [];
  private programCounter: number = 0;
  private traceHooks: TraceHook[] = [];
  private definitions: Map<string, Instruction[]> = new Map();
  private isRunning: boolean = false;
  private maxStackDepth: number = 256;

  private activeIntent: string | null = null;
  private constraints: ConstraintDirective[] = [];
  private deadlineAt: number | null = null;
  private timeHintMs: number | null = null;

  /**
   * Initialize execution context with a program
   */
  setProgram(instructions: Instruction[]): void {
    this.program = instructions;
    this.programCounter = 0;
  }

  /**
   * Get current instruction
   */
  getCurrentInstruction(): Instruction | null {
    if (this.programCounter >= this.program.length) {
      return null;
    }
    return this.program[this.programCounter];
  }

  /**
   * Advance program counter
   */
  advanceProgramCounter(): void {
    this.programCounter++;
  }

  /**
   * Set program counter to specific address
   */
  setProgramCounter(address: number): void {
    if (address < 0 || address > this.program.length) {
      throw createError(ErrorType.IllegalState, 'Invalid program counter address', {
        address,
        programLength: this.program.length,
      });
    }
    this.programCounter = address;
  }

  /**
   * Get program counter
   */
  getProgramCounter(): number {
    return this.programCounter;
  }

  /**
   * Push a function call onto the call stack
   */
  pushCallFrame(functionName: string, returnAddress: number, stackPointer: number): void {
    if (this.callStack.length >= this.maxStackDepth) {
      throw createError(ErrorType.StackOverflow, 'Call stack overflow', {
        callStackDepth: this.callStack.length,
        maxDepth: this.maxStackDepth,
      });
    }

    this.callStack.push({
      functionName,
      returnAddress,
      savedStackPointer: stackPointer,
      locals: new Map(),
    });

    this.emitTrace('function_call', {
      functionName,
      returnAddress,
      callStackDepth: this.callStack.length,
    });
  }

  /**
   * Pop a function call from the call stack
   */
  popCallFrame(): StackFrame {
    if (this.callStack.length === 0) {
      throw createError(ErrorType.IllegalState, 'Cannot pop from empty call stack');
    }

    const frame = this.callStack.pop()!;
    this.emitTrace('function_return', {
      functionName: frame.functionName,
      callStackDepth: this.callStack.length,
    });

    return frame;
  }

  /**
   * Get current call frame
   */
  getCurrentCallFrame(): StackFrame | null {
    return this.callStack.length > 0 ? this.callStack[this.callStack.length - 1] : null;
  }

  /**
   * Get call stack depth
   */
  getCallStackDepth(): number {
    return this.callStack.length;
  }

  /**
   * Define a function
   */
  defineFunction(name: string, instructions: Instruction[]): void {
    this.definitions.set(name, instructions);
  }

  /**
   * Get function definition
   */
  getFunction(name: string): Instruction[] | null {
    return this.definitions.get(name) || null;
  }

  /**
   * Check if function is defined
   */
  isFunctionDefined(name: string): boolean {
    return this.definitions.has(name);
  }

  /**
   * Set active intent for downstream scheduling/optimization.
   */
  setIntent(intent: string | null): void {
    this.activeIntent = intent;
  }

  getIntent(): string | null {
    return this.activeIntent;
  }

  applyConstraint(
    register: string,
    operator: string,
    value: number,
    severity: 'error' | 'alert' = 'error'
  ): string {
    const id = `constraint-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    this.constraints.push({
      id,
      register,
      operator,
      value,
      createdAt: Date.now(),
      severity,
    });
    return id;
  }

  getConstraints(): ConstraintDirective[] {
    return [...this.constraints];
  }

  setDeadlineAt(deadlineAt: number | null): void {
    this.deadlineAt = deadlineAt;
  }

  getDeadlineAt(): number | null {
    return this.deadlineAt;
  }

  setTimeHintMs(timeHintMs: number | null): void {
    this.timeHintMs = timeHintMs;
  }

  getTimeHintMs(): number | null {
    return this.timeHintMs;
  }

  /**
   * Add trace hook
   */
  addTraceHook(hook: TraceHook): void {
    this.traceHooks.push(hook);
  }

  /**
   * Remove trace hook
   */
  removeTraceHook(hook: TraceHook): void {
    const index = this.traceHooks.indexOf(hook);
    if (index !== -1) {
      this.traceHooks.splice(index, 1);
    }
  }

  /**
   * Emit trace event
   */
  emitTrace(
    event: 'instruction' | 'error' | 'function_call' | 'function_return',
    data: Record<string, unknown>
  ): void {
    this.traceHooks.forEach((hook) => {
      try {
        hook(event, data);
      } catch (e) {
        // Suppress errors in trace hooks
      }
    });
  }

  /**
   * Set running state
   */
  setRunning(value: boolean): void {
    this.isRunning = value;
  }

  /**
   * Check if context is running
   */
  isContextRunning(): boolean {
    return this.isRunning;
  }

  /**
   * Reset context
   */
  reset(): void {
    this.callStack = [];
    this.program = [];
    this.programCounter = 0;
    this.isRunning = false;
    this.activeIntent = null;
    this.constraints = [];
    this.deadlineAt = null;
    this.timeHintMs = null;
  }

  /**
   * Get context state snapshot
   */
  getSnapshot() {
    return {
      programCounter: this.programCounter,
      callStackDepth: this.callStack.length,
      isRunning: this.isRunning,
      definedFunctions: Array.from(this.definitions.keys()),
      programLength: this.program.length,
      intent: this.activeIntent,
      constraints: this.constraints.map((c) => ({ ...c })),
      deadlineAt: this.deadlineAt,
      timeHintMs: this.timeHintMs,
    };
  }
}
