/**
 * Layer types and interfaces for layered execution
 */

import { Instruction } from '../instructions';

export enum LayerKind {
  ENGLISH = 'english',
  SUPERBIT = 'superbit',
  BINARY = 'binary',
  CPU = 'cpu',
  DISTRIBUTED = 'distributed',
}

export interface LayerSnapshot {
  layer: LayerKind;
  registers: Map<string, number>;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface LayerExecutionResult {
  success: boolean;
  error?: Error;
  snapshot?: LayerSnapshot;
  crossLayerTraces?: string[];
}

export interface PerformanceProfile {
  estimatedCycles?: number;
  memoryFootprint?: number;
  preferredLayer?: LayerKind;
  metadata?: Record<string, unknown>;
}

export interface LayerAdapter {
  /**
   * Execute an instruction on this layer
   */
  execute(instruction: Instruction, context: LayerExecutionContext): Promise<LayerExecutionResult>;

  /**
   * Get current layer state snapshot
   */
  snapshot(): LayerSnapshot;

  /**
   * Register a breakpoint at this layer
   */
  registerBreakpoint(address: number, condition?: (context: LayerExecutionContext) => boolean): void;

  /**
   * Check if a breakpoint is hit
   */
  checkBreakpoint(address: number, context: LayerExecutionContext): boolean;

  /**
   * Get layer identifier
   */
  getLayerId(): LayerKind;

  /**
   * Verify that required layers are available
   */
  verifyLayerAvailability(layers: LayerKind[]): boolean;
}

export interface LayerExecutionContext {
  instruction: Instruction;
  registers: Map<string, number>;
  memory?: Record<string, unknown>;
  layer?: LayerKind;
  requiredLayers?: LayerKind[];
  preferredLayers?: LayerKind[];
  performanceProfile?: PerformanceProfile;
}
