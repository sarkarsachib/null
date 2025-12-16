/**
 * Neural engine for lightweight dense layers and transformations on classical hardware
 * Implements matrix operations for AI inference
 */

import { SuperBitTensor } from './superbit_tensor';

export interface LayerConfig {
  inputDim: number;
  outputDim: number;
  activation?: 'relu' | 'sigmoid' | 'tanh' | 'linear';
  usesBias?: boolean;
}

export class DenseLayer {
  private weights: SuperBitTensor;
  private bias: SuperBitTensor | null;
  private activation: 'relu' | 'sigmoid' | 'tanh' | 'linear';
  private config: LayerConfig;

  constructor(config: LayerConfig, weights?: SuperBitTensor, bias?: SuperBitTensor) {
    this.config = config;
    this.activation = config.activation || 'linear';

    if (weights) {
      const shape = weights.getShape();
      if (shape.dims[0] !== config.inputDim || shape.dims[1] !== config.outputDim) {
        throw new Error(
          `Weight shape mismatch: expected [${config.inputDim}, ${config.outputDim}], got [${shape.dims[0]}, ${shape.dims[1]}]`
        );
      }
      this.weights = weights;
    } else {
      this.weights = DenseLayer.initializeRandomWeights(config.inputDim, config.outputDim);
    }

    if (config.usesBias !== false) {
      if (bias) {
        if (bias.getShape().dims[0] !== config.outputDim) {
          throw new Error(
            `Bias shape mismatch: expected [${config.outputDim}], got [${bias.getShape().dims[0]}]`
          );
        }
        this.bias = bias;
      } else {
        this.bias = new SuperBitTensor(
          { dims: [config.outputDim] },
          new Float32Array(config.outputDim)
        );
      }
    } else {
      this.bias = null;
    }
  }

  /**
   * Forward pass through layer
   */
  forward(input: SuperBitTensor): SuperBitTensor {
    const inputShape = input.getShape();
    if (inputShape.dims[inputShape.dims.length - 1] !== this.config.inputDim) {
      throw new Error(
        `Input dimension mismatch: expected ${this.config.inputDim}, got ${inputShape.dims[inputShape.dims.length - 1]}`
      );
    }

    const inputData = input.getData();
    const weightsData = this.weights.getData();
    const outputSize = this.config.outputDim;

    const outputData = new Float32Array(outputSize);

    for (let i = 0; i < outputSize; i++) {
      let sum = 0;
      for (let j = 0; j < this.config.inputDim; j++) {
        sum += inputData[j] * weightsData[j * outputSize + i];
      }

      if (this.bias) {
        sum += this.bias.getData()[i];
      }

      outputData[i] = this.applyActivation(sum);
    }

    const outputTensor = new SuperBitTensor({ dims: [outputSize] }, outputData, {
      uncertainty: Math.max(
        input.getMetadata().uncertainty,
        this.weights.getMetadata().uncertainty
      ),
      precision: input.getMetadata().precision * this.weights.getMetadata().precision,
      superbitEncoded: false,
    });

    return outputTensor;
  }

  /**
   * Apply activation function
   */
  private applyActivation(x: number): number {
    switch (this.activation) {
      case 'relu':
        return Math.max(0, x);
      case 'sigmoid':
        return 1 / (1 + Math.exp(-x));
      case 'tanh':
        return Math.tanh(x);
      case 'linear':
      default:
        return x;
    }
  }

  /**
   * Get weights
   */
  getWeights(): SuperBitTensor {
    return this.weights.clone();
  }

  /**
   * Get bias
   */
  getBias(): SuperBitTensor | null {
    return this.bias ? this.bias.clone() : null;
  }

  /**
   * Set weights
   */
  setWeights(weights: SuperBitTensor): void {
    const shape = weights.getShape();
    if (shape.dims[0] !== this.config.inputDim || shape.dims[1] !== this.config.outputDim) {
      throw new Error(
        `Weight shape mismatch: expected [${this.config.inputDim}, ${this.config.outputDim}], got [${shape.dims[0]}, ${shape.dims[1]}]`
      );
    }
    this.weights = weights;
  }

  /**
   * Initialize random weights using Xavier/Glorot initialization
   */
  private static initializeRandomWeights(inputDim: number, outputDim: number): SuperBitTensor {
    const limit = Math.sqrt(6 / (inputDim + outputDim));
    const size = inputDim * outputDim;
    const data = new Float32Array(size);

    for (let i = 0; i < size; i++) {
      data[i] = Math.random() * 2 * limit - limit;
    }

    return new SuperBitTensor({ dims: [inputDim, outputDim] }, data, {
      uncertainty: 0.5,
      precision: 1.0,
      superbitEncoded: false,
    });
  }
}

export type OptimizationProfile = 'balanced' | 'low-latency' | 'high-throughput';

export class NeuralEngine {
  private layers: DenseLayer[] = [];
  private optimizationProfile: OptimizationProfile = 'balanced';

  setOptimizationProfile(profile: OptimizationProfile): void {
    this.optimizationProfile = profile;
  }

  setIntent(intent: string | null): void {
    switch (intent) {
      case 'minimize_latency':
      case 'low_latency':
        this.optimizationProfile = 'low-latency';
        return;
      case 'maximize_throughput':
      case 'high_throughput':
        this.optimizationProfile = 'high-throughput';
        return;
      default:
        this.optimizationProfile = 'balanced';
    }
  }

  getOptimizationProfile(): OptimizationProfile {
    return this.optimizationProfile;
  }

  /**
   * Add a layer to the network
   */
  addLayer(config: LayerConfig, weights?: SuperBitTensor, bias?: SuperBitTensor): void {
    const layer = new DenseLayer(config, weights, bias);
    this.layers.push(layer);
  }

  /**
   * Forward pass through entire network
   */
  forward(input: SuperBitTensor): SuperBitTensor {
    let output = input;

    for (const layer of this.layers) {
      output = layer.forward(output);
    }

    return output;
  }

  /**
   * Get number of layers
   */
  getLayerCount(): number {
    return this.layers.length;
  }

  /**
   * Get specific layer
   */
  getLayer(index: number): DenseLayer | null {
    return this.layers[index] || null;
  }

  /**
   * Clear all layers
   */
  clear(): void {
    this.layers = [];
  }

  /**
   * Clone the engine
   */
  clone(): NeuralEngine {
    const cloned = new NeuralEngine();
    for (const layer of this.layers) {
      const weights = layer.getWeights();
      const bias = layer.getBias();
      const config = {
        inputDim: weights.getShape().dims[0],
        outputDim: weights.getShape().dims[1],
        activation: 'linear' as const,
        usesBias: bias !== null,
      };
      cloned.addLayer(config, weights, bias || undefined);
    }
    return cloned;
  }
}
