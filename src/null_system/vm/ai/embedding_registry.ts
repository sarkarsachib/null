/**
 * Embedding registry for managing reusable AI embeddings
 * Supports caching, serialization, and retrieval of dense embeddings
 */

import { SuperBitTensor } from './superbit_tensor';

export interface EmbeddingMetadata {
  id: string;
  dimension: number;
  type: 'dense' | 'sparse' | 'probabilistic';
  sourceModel?: string;
  createdAt: number;
  useCount: number;
}

export interface EmbeddingEntry {
  tensor: SuperBitTensor;
  metadata: EmbeddingMetadata;
}

export class EmbeddingRegistry {
  private embeddings: Map<string, EmbeddingEntry> = new Map();
  private embeddingsByType: Map<string, Set<string>> = new Map();

  constructor() {
    this.embeddingsByType.set('dense', new Set());
    this.embeddingsByType.set('sparse', new Set());
    this.embeddingsByType.set('probabilistic', new Set());
  }

  /**
   * Register an embedding
   */
  registerEmbedding(
    id: string,
    tensor: SuperBitTensor,
    type: 'dense' | 'sparse' | 'probabilistic' = 'dense',
    sourceModel?: string
  ): void {
    if (this.embeddings.has(id)) {
      throw new Error(`Embedding with id ${id} already exists`);
    }

    const shape = tensor.getShape();
    const dimension = shape.dims[shape.dims.length - 1] || 1;

    const metadata: EmbeddingMetadata = {
      id,
      dimension,
      type,
      sourceModel,
      createdAt: Date.now(),
      useCount: 0,
    };

    this.embeddings.set(id, { tensor, metadata });
    this.embeddingsByType.get(type)!.add(id);
  }

  /**
   * Retrieve an embedding by ID
   */
  getEmbedding(id: string): SuperBitTensor | null {
    const entry = this.embeddings.get(id);
    if (!entry) {
      return null;
    }

    entry.metadata.useCount++;
    return entry.tensor.clone();
  }

  /**
   * Get embedding metadata
   */
  getEmbeddingMetadata(id: string): EmbeddingMetadata | null {
    const entry = this.embeddings.get(id);
    return entry ? { ...entry.metadata } : null;
  }

  /**
   * Check if embedding exists
   */
  hasEmbedding(id: string): boolean {
    return this.embeddings.has(id);
  }

  /**
   * List all embeddings of a type
   */
  listByType(type: 'dense' | 'sparse' | 'probabilistic'): EmbeddingMetadata[] {
    const ids = this.embeddingsByType.get(type) || new Set();
    return Array.from(ids).map((id) => {
      const entry = this.embeddings.get(id)!;
      return { ...entry.metadata };
    });
  }

  /**
   * List all embeddings
   */
  listAll(): EmbeddingMetadata[] {
    return Array.from(this.embeddings.values()).map((entry) => ({ ...entry.metadata }));
  }

  /**
   * Delete an embedding
   */
  deleteEmbedding(id: string): boolean {
    const entry = this.embeddings.get(id);
    if (!entry) {
      return false;
    }

    this.embeddingsByType.get(entry.metadata.type)?.delete(id);
    this.embeddings.delete(id);
    return true;
  }

  /**
   * Clear all embeddings
   */
  clear(): void {
    this.embeddings.clear();
    for (const typeSet of this.embeddingsByType.values()) {
      typeSet.clear();
    }
  }

  /**
   * Get count of embeddings
   */
  getCount(): number {
    return this.embeddings.size;
  }

  /**
   * Create a dense embedding vector (uniform random initialization)
   */
  static createRandomDenseEmbedding(id: string, dimension: number): SuperBitTensor {
    const data = new Float32Array(dimension);
    for (let i = 0; i < dimension; i++) {
      data[i] = Math.random() * 2 - 1;
    }

    return new SuperBitTensor({ dims: [dimension] }, data, {
      uncertainty: 0.5,
      precision: 1.0,
      superbitEncoded: false,
    });
  }

  /**
   * Create a zero embedding vector
   */
  static createZeroEmbedding(dimension: number): SuperBitTensor {
    const data = new Float32Array(dimension);
    return new SuperBitTensor({ dims: [dimension] }, data, {
      uncertainty: 0,
      precision: 1.0,
      superbitEncoded: false,
    });
  }

  /**
   * Create a normalized embedding (unit length)
   */
  static createNormalizedEmbedding(data: number[]): SuperBitTensor {
    const length = Math.sqrt(data.reduce((sum, val) => sum + val * val, 0));
    const normalized = new Float32Array(data.map((val) => (length > 0 ? val / length : 0)));

    return new SuperBitTensor({ dims: [data.length] }, normalized, {
      uncertainty: 0.1,
      precision: 1.0,
      superbitEncoded: false,
    });
  }
}
