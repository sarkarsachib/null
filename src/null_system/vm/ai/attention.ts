/**
 * Attention mechanisms for reducing uncertainty in super-bit tensors
 * Implements scaled dot-product attention and uncertainty reduction strategies
 */

import { SuperBitTensor } from './superbit_tensor';

export interface AttentionConfig {
  headCount?: number;
  temperatureScale?: number;
  uncertaintyReductionFactor?: number;
}

export class AttentionModule {
  private headCount: number;
  private temperatureScale: number;
  private uncertaintyReductionFactor: number;

  constructor(config: AttentionConfig = {}) {
    this.headCount = config.headCount || 1;
    this.temperatureScale = config.temperatureScale || 1.0;
    this.uncertaintyReductionFactor = config.uncertaintyReductionFactor || 0.3;
  }

  /**
   * Apply scaled dot-product attention
   * Computes attention weights and applies them to values
   */
  scaledDotProductAttention(
    query: SuperBitTensor,
    key: SuperBitTensor,
    value: SuperBitTensor
  ): SuperBitTensor {
    const queryData = query.getData();
    const keyData = key.getData();
    const valueData = value.getData();

    const dim = queryData.length;

    if (keyData.length !== dim || valueData.length !== dim) {
      throw new Error('Query, key, and value must have same dimension');
    }

    // Compute scaled dot product: Q * K^T / sqrt(d_k)
    let dotProduct = 0;
    for (let i = 0; i < dim; i++) {
      dotProduct += queryData[i] * keyData[i];
    }

    const scale = Math.sqrt(dim) * this.temperatureScale;
    const scaledScore = dotProduct / scale;

    // Apply softmax-like attention (normalized exponential)
    const attentionWeight = this.softmax(scaledScore);

    // Apply attention to values
    const outputData = new Float32Array(dim);
    for (let i = 0; i < dim; i++) {
      outputData[i] = valueData[i] * attentionWeight;
    }

    // Create output tensor with reduced uncertainty
    const inputUncertainty = Math.max(
      query.getMetadata().uncertainty,
      Math.max(key.getMetadata().uncertainty, value.getMetadata().uncertainty)
    );

    const outputTensor = new SuperBitTensor({ dims: [dim] }, outputData, {
      uncertainty: Math.max(0, inputUncertainty - this.uncertaintyReductionFactor),
      precision: Math.min(
        1.0,
        Math.max(
          query.getMetadata().precision,
          Math.max(key.getMetadata().precision, value.getMetadata().precision)
        )
      ),
      superbitEncoded: false,
    });

    return outputTensor;
  }

  /**
   * Multi-head attention
   * Splits input into multiple heads and combines results
   */
  multiHeadAttention(
    query: SuperBitTensor,
    key: SuperBitTensor,
    value: SuperBitTensor
  ): SuperBitTensor {
    const dim = query.getData().length;

    if (dim % this.headCount !== 0) {
      throw new Error(`Dimension ${dim} must be divisible by head count ${this.headCount}`);
    }

    const headDim = dim / this.headCount;
    const queryData = query.getData();
    const keyData = key.getData();
    const valueData = value.getData();

    const outputData = new Float32Array(dim);
    let totalUncertainty = 0;
    let totalPrecision = 1.0;

    for (let head = 0; head < this.headCount; head++) {
      const startIdx = head * headDim;
      const endIdx = startIdx + headDim;

      const queryHead = new SuperBitTensor({ dims: [headDim] }, queryData.slice(startIdx, endIdx));
      const keyHead = new SuperBitTensor({ dims: [headDim] }, keyData.slice(startIdx, endIdx));
      const valueHead = new SuperBitTensor({ dims: [headDim] }, valueData.slice(startIdx, endIdx));

      const headOutput = this.scaledDotProductAttention(queryHead, keyHead, valueHead);
      const headOutputData = headOutput.getData();

      for (let i = 0; i < headDim; i++) {
        outputData[startIdx + i] = headOutputData[i];
      }

      totalUncertainty += headOutput.getMetadata().uncertainty;
      totalPrecision *= headOutput.getMetadata().precision;
    }

    const avgUncertainty = totalUncertainty / this.headCount;

    const outputTensor = new SuperBitTensor({ dims: [dim] }, outputData, {
      uncertainty: avgUncertainty,
      precision: Math.pow(totalPrecision, 1 / this.headCount),
      superbitEncoded: false,
    });

    return outputTensor;
  }

  /**
   * Self-attention: uses same tensor for Q, K, V
   */
  selfAttention(input: SuperBitTensor): SuperBitTensor {
    return this.multiHeadAttention(input, input, input);
  }

  /**
   * Cross-attention between two tensors
   */
  crossAttention(target: SuperBitTensor, context: SuperBitTensor): SuperBitTensor {
    return this.multiHeadAttention(target, context, context);
  }

  /**
   * Softmax function normalized to [0, 1]
   */
  private softmax(x: number): number {
    // Use tanh-like squashing for simplicity and stability
    return (Math.tanh(x) + 1) / 2;
  }

  /**
   * Apply attention with uncertainty reduction
   * This reduces uncertainty by examining attention focus patterns
   */
  reduceUncertaintyWithAttention(tensor: SuperBitTensor): SuperBitTensor {
    const attention = this.selfAttention(tensor);

    // The attention mechanism should reduce uncertainty as it focuses on patterns
    attention.reduceUncertainty(this.uncertaintyReductionFactor);

    return attention;
  }

  /**
   * Get configuration
   */
  getConfig(): AttentionConfig {
    return {
      headCount: this.headCount,
      temperatureScale: this.temperatureScale,
      uncertaintyReductionFactor: this.uncertaintyReductionFactor,
    };
  }

  /**
   * Set configuration
   */
  setConfig(config: Partial<AttentionConfig>): void {
    if (config.headCount !== undefined) this.headCount = config.headCount;
    if (config.temperatureScale !== undefined) this.temperatureScale = config.temperatureScale;
    if (config.uncertaintyReductionFactor !== undefined) {
      this.uncertaintyReductionFactor = config.uncertaintyReductionFactor;
    }
  }
}
