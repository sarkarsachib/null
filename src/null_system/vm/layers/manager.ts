/**
 * Layer execution manager - coordinates execution across different abstraction layers
 */

import {
  LayerAdapter,
  LayerExecutionContext,
  LayerExecutionResult,
  LayerKind,
  LayerSnapshot,
} from './types';
import { Instruction } from '../instructions';
import {
  EnglishLayerAdapter,
  SuperBitLayerAdapter,
  BinaryLayerAdapter,
  CPULayerAdapter,
  DistributedLayerAdapter,
} from './adapters';
import { createError, ErrorType } from '../errors';

export interface LayerBreakpoint {
  address: number;
  layer?: LayerKind;
  condition?: (context: LayerExecutionContext) => boolean;
}

export interface LayerMetadata {
  layer?: LayerKind;
  requiredLayers?: LayerKind[];
  preferredLayers?: LayerKind[];
}

export class LayerExecutionManager {
  private adapters: Map<LayerKind, LayerAdapter> = new Map();
  private currentLayer: LayerKind = LayerKind.ENGLISH;
  private layerStack: LayerKind[] = [];
  private breakpoints: LayerBreakpoint[] = [];
  private crossLayerTraces: string[] = [];
  private layerSnapshots: Map<LayerKind, LayerSnapshot> = new Map();
  private availableLayers: Set<LayerKind>;

  constructor(availableLayers?: LayerKind[]) {
    this.availableLayers = new Set(availableLayers || Object.values(LayerKind));
    this.initializeAdapters();
  }

  private initializeAdapters(): void {
    if (this.availableLayers.has(LayerKind.ENGLISH)) {
      this.adapters.set(LayerKind.ENGLISH, new EnglishLayerAdapter());
    }
    if (this.availableLayers.has(LayerKind.SUPERBIT)) {
      this.adapters.set(LayerKind.SUPERBIT, new SuperBitLayerAdapter());
    }
    if (this.availableLayers.has(LayerKind.BINARY)) {
      this.adapters.set(LayerKind.BINARY, new BinaryLayerAdapter());
    }
    if (this.availableLayers.has(LayerKind.CPU)) {
      this.adapters.set(LayerKind.CPU, new CPULayerAdapter());
    }
    if (this.availableLayers.has(LayerKind.DISTRIBUTED)) {
      this.adapters.set(LayerKind.DISTRIBUTED, new DistributedLayerAdapter());
    }
  }

  /**
   * Execute instruction with layer routing
   */
  async executeWithLayering(
    instruction: Instruction,
    context: LayerExecutionContext,
    metadata?: LayerMetadata
  ): Promise<LayerExecutionResult> {
    const targetLayer = this.selectLayer(metadata);

    context.layer = targetLayer;
    context.requiredLayers = metadata?.requiredLayers;
    context.preferredLayers = metadata?.preferredLayers;

    if (metadata?.requiredLayers && !this.verifyRequiredLayers(metadata.requiredLayers)) {
      throw createError(
        ErrorType.IllegalState,
        `Required layers not available: ${metadata.requiredLayers.join(', ')}`,
        { required: metadata.requiredLayers, available: Array.from(this.availableLayers) }
      );
    }

    this.pushLayer(targetLayer);
    this.crossLayerTraces.push(`[${new Date().toISOString()}] Routing to layer: ${targetLayer}`);

    try {
      const adapter = this.adapters.get(targetLayer);
      if (!adapter) {
        throw createError(ErrorType.IllegalState, `Layer adapter not found: ${targetLayer}`, {
          targetLayer,
          availableAdapters: Array.from(this.adapters.keys()),
        });
      }

      const result = await adapter.execute(instruction, context);

      if (result.success) {
        const snapshot = adapter.snapshot();
        this.layerSnapshots.set(targetLayer, snapshot);

        if (this.checkBreakpointsForLayer(targetLayer, context)) {
          this.crossLayerTraces.push(
            `[${new Date().toISOString()}] Breakpoint hit at layer: ${targetLayer}`
          );
        }
      }

      return result;
    } finally {
      this.popLayer();
    }
  }

  /**
   * Select target layer based on metadata
   */
  private selectLayer(metadata?: LayerMetadata): LayerKind {
    if (metadata?.layer && this.availableLayers.has(metadata.layer)) {
      return metadata.layer;
    }

    if (metadata?.preferredLayers) {
      for (const layer of metadata.preferredLayers) {
        if (this.availableLayers.has(layer)) {
          return layer;
        }
      }
    }

    return this.currentLayer;
  }

  /**
   * Verify that all required layers are available
   */
  private verifyRequiredLayers(requiredLayers: LayerKind[]): boolean {
    return requiredLayers.every((layer) => this.availableLayers.has(layer));
  }

  /**
   * Register a layer-specific breakpoint
   */
  registerBreakpoint(
    address: number,
    layer?: LayerKind,
    condition?: (context: LayerExecutionContext) => boolean
  ): void {
    this.breakpoints.push({ address, layer, condition });

    const adapter = layer ? this.adapters.get(layer) : Array.from(this.adapters.values())[0];
    if (adapter) {
      adapter.registerBreakpoint(address, condition);
    }
  }

  /**
   * Check if a breakpoint is hit in the specified layer
   */
  private checkBreakpointsForLayer(layer: LayerKind, context: LayerExecutionContext): boolean {
    const adapter = this.adapters.get(layer);
    if (!adapter) return false;

    const instruction = context.instruction;
    const address = instruction.lineno || 0;

    return adapter.checkBreakpoint(address, context);
  }

  /**
   * Push layer onto stack
   */
  private pushLayer(layer: LayerKind): void {
    this.layerStack.push(layer);
  }

  /**
   * Pop layer from stack
   */
  private popLayer(): void {
    if (this.layerStack.length > 0) {
      this.layerStack.pop();
    }
  }

  /**
   * Get current layer
   */
  getCurrentLayer(): LayerKind {
    return this.currentLayer;
  }

  /**
   * Set current layer
   */
  setCurrentLayer(layer: LayerKind): void {
    if (this.availableLayers.has(layer)) {
      this.currentLayer = layer;
    }
  }

  /**
   * Get layer stack
   */
  getLayerStack(): LayerKind[] {
    return [...this.layerStack];
  }

  /**
   * Get cross-layer execution traces
   */
  getCrossLayerTraces(): string[] {
    return [...this.crossLayerTraces];
  }

  /**
   * Clear cross-layer traces
   */
  clearCrossLayerTraces(): void {
    this.crossLayerTraces = [];
  }

  /**
   * Get snapshot for layer
   */
  getLayerSnapshot(layer: LayerKind): LayerSnapshot | null {
    return this.layerSnapshots.get(layer) || null;
  }

  /**
   * Get all layer snapshots
   */
  getAllLayerSnapshots(): Map<LayerKind, LayerSnapshot> {
    return new Map(this.layerSnapshots);
  }

  /**
   * Check if layer is available
   */
  isLayerAvailable(layer: LayerKind): boolean {
    return this.availableLayers.has(layer);
  }

  /**
   * Get available layers
   */
  getAvailableLayers(): LayerKind[] {
    return Array.from(this.availableLayers);
  }

  /**
   * Register a new layer adapter
   */
  registerAdapter(adapter: LayerAdapter): void {
    const layerId = adapter.getLayerId();
    this.adapters.set(layerId, adapter);
    this.availableLayers.add(layerId);
  }

  /**
   * Remove a layer adapter
   */
  removeAdapter(layer: LayerKind): void {
    this.adapters.delete(layer);
    this.availableLayers.delete(layer);
  }
}
