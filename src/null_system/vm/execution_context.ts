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

export interface LayerBreakpoint {
  address: number;
  layer?: string;
  condition?: (context: ExecutionContext) => boolean;
}

export interface LayerRegisterSnapshot {
  layer: string;
  registers: Map<string, number>;
  timestamp: number;
}

export type TraceHook = (
  event: 'instruction' | 'error' | 'function_call' | 'function_return' | 'layer_switch' | 'breakpoint_hit' | string,
  data: Record<string, unknown>
) => void;

export class ExecutionContext {
  private callStack: StackFrame[] = [];
  program: Instruction[] = [];
  private programCounter: number = 0;
  private traceHooks: TraceHook[] = [];
  private definitions: Map<string, Instruction[]> = new Map();
  private isRunning: boolean = false;
  private maxStackDepth: number = 256;
  private layerStack: string[] = [];
  private currentLayer: string = 'english';
  private layerBreakpoints: LayerBreakpoint[] = [];
  private layerRegisterSnapshots: Map<string, LayerRegisterSnapshot> = new Map();

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
    event: 'instruction' | 'error' | 'function_call' | 'function_return' | 'layer_switch' | 'breakpoint_hit' | string,
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
    this.layerStack = [];
    this.layerRegisterSnapshots.clear();
  }

  /**
   * Push layer onto stack
   */
  pushLayer(layer: string): void {
    this.layerStack.push(layer);
    this.currentLayer = layer;
    this.emitTrace('layer_switch', { layer, layerStackDepth: this.layerStack.length });
  }

  /**
   * Pop layer from stack
   */
  popLayer(): string | null {
    if (this.layerStack.length === 0) {
      return null;
    }
    const popped = this.layerStack.pop();
    if (this.layerStack.length > 0) {
      this.currentLayer = this.layerStack[this.layerStack.length - 1];
    } else {
      this.currentLayer = 'english';
    }
    return popped || null;
  }

  /**
   * Get current layer
   */
  getCurrentLayer(): string {
    return this.currentLayer;
  }

  /**
   * Get layer stack
   */
  getLayerStack(): string[] {
    return [...this.layerStack];
  }

  /**
   * Register a layer-specific breakpoint
   */
  registerLayerBreakpoint(
    address: number,
    layer?: string,
    condition?: (context: ExecutionContext) => boolean
  ): void {
    this.layerBreakpoints.push({ address, layer, condition });
  }

  /**
   * Check if a breakpoint is hit at current address and layer
   */
  checkLayerBreakpoint(address: number): boolean {
    return this.layerBreakpoints.some((bp) => {
      const addressMatches = bp.address === address;
      const layerMatches = !bp.layer || bp.layer === this.currentLayer;
      const conditionMatches = !bp.condition || bp.condition(this);
      return addressMatches && layerMatches && conditionMatches;
    });
  }

  /**
   * Get pending breakpoints for a layer
   */
  getPendingBreakpoints(layer?: string): LayerBreakpoint[] {
    if (!layer) {
      return [...this.layerBreakpoints];
    }
    return this.layerBreakpoints.filter((bp) => !bp.layer || bp.layer === layer);
  }

  /**
   * Save register snapshot for a layer
   */
  saveLayerRegisterSnapshot(layer: string, registers: Map<string, number>): void {
    this.layerRegisterSnapshots.set(layer, {
      layer,
      registers: new Map(registers),
      timestamp: Date.now(),
    });
  }

  /**
   * Get layer register snapshot
   */
  getLayerRegisterSnapshot(layer: string): LayerRegisterSnapshot | null {
    return this.layerRegisterSnapshots.get(layer) || null;
  }

  /**
   * Get all layer register snapshots
   */
  getAllLayerRegisterSnapshots(): Map<string, LayerRegisterSnapshot> {
    return new Map(this.layerRegisterSnapshots);
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
      currentLayer: this.currentLayer,
      layerStackDepth: this.layerStack.length,
      pendingBreakpoints: this.layerBreakpoints.length,
    };
  }
}
