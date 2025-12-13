/**
 * Super-bit tensor representations for probabilistic AI operations
 * Supports probabilistic vectors and matrices with uncertainty quantification
 */

export interface TensorShape {
  dims: number[];
}

export interface TensorMetadata {
  uncertainty: number;
  precision: number;
  superbitEncoded: boolean;
}

export class SuperBitTensor {
  private data: Float32Array;
  private shape: TensorShape;
  private metadata: TensorMetadata;

  constructor(shape: TensorShape, data?: Float32Array, metadata?: Partial<TensorMetadata>) {
    this.shape = shape;
    this.metadata = {
      uncertainty: metadata?.uncertainty ?? 0.0,
      precision: metadata?.precision ?? 1.0,
      superbitEncoded: metadata?.superbitEncoded ?? false,
    };

    const size = shape.dims.reduce((a, b) => a * b, 1);
    this.data = data || new Float32Array(size);

    if (data && data.length !== size) {
      throw new Error(`Data size mismatch: expected ${size}, got ${data.length}`);
    }
  }

  /**
   * Get tensor dimensions
   */
  getShape(): TensorShape {
    return { ...this.shape };
  }

  /**
   * Get total number of elements
   */
  getSize(): number {
    return this.data.length;
  }

  /**
   * Get raw data
   */
  getData(): Float32Array {
    return this.data;
  }

  /**
   * Get element at index
   */
  getAt(indices: number[]): number {
    const linearIndex = this.getLinearIndex(indices);
    return this.data[linearIndex];
  }

  /**
   * Set element at index
   */
  setAt(indices: number[], value: number): void {
    const linearIndex = this.getLinearIndex(indices);
    this.data[linearIndex] = value;
  }

  /**
   * Convert multi-dimensional indices to linear index
   */
  private getLinearIndex(indices: number[]): number {
    if (indices.length !== this.shape.dims.length) {
      throw new Error(
        `Index dimension mismatch: expected ${this.shape.dims.length}, got ${indices.length}`
      );
    }

    let index = 0;
    let stride = 1;

    for (let i = this.shape.dims.length - 1; i >= 0; i--) {
      if (indices[i] < 0 || indices[i] >= this.shape.dims[i]) {
        throw new Error(
          `Index out of bounds at dimension ${i}: ${indices[i]} not in [0, ${this.shape.dims[i]})`
        );
      }
      index += indices[i] * stride;
      stride *= this.shape.dims[i];
    }

    return index;
  }

  /**
   * Get metadata
   */
  getMetadata(): TensorMetadata {
    return { ...this.metadata };
  }

  /**
   * Update metadata
   */
  setMetadata(metadata: Partial<TensorMetadata>): void {
    this.metadata = { ...this.metadata, ...metadata };
  }

  /**
   * Reduce uncertainty through observed patterns
   */
  reduceUncertainty(reduction: number): void {
    this.metadata.uncertainty = Math.max(0, this.metadata.uncertainty - reduction);
  }

  /**
   * Clone tensor
   */
  clone(): SuperBitTensor {
    return new SuperBitTensor(this.shape, new Float32Array(this.data), this.metadata);
  }

  /**
   * Convert to Buffer for serialization
   */
  toBuffer(): Buffer {
    const shapeBuffer = Buffer.alloc(4 + this.shape.dims.length * 4);
    shapeBuffer.writeUInt32BE(this.shape.dims.length, 0);

    let offset = 4;
    for (let i = 0; i < this.shape.dims.length; i++) {
      shapeBuffer.writeUInt32BE(this.shape.dims[i], offset);
      offset += 4;
    }

    const dataBuffer = Buffer.from(this.data.buffer, this.data.byteOffset, this.data.byteLength);

    const metadataBuffer = Buffer.alloc(16);
    metadataBuffer.writeFloatBE(this.metadata.uncertainty, 0);
    metadataBuffer.writeFloatBE(this.metadata.precision, 4);
    metadataBuffer.writeUInt32BE(this.metadata.superbitEncoded ? 1 : 0, 8);

    return Buffer.concat([shapeBuffer, dataBuffer, metadataBuffer]);
  }

  /**
   * Create from Buffer
   */
  static fromBuffer(buffer: Buffer): SuperBitTensor {
    let offset = 0;

    const dimsLength = buffer.readUInt32BE(offset);
    offset += 4;

    const dims: number[] = [];
    for (let i = 0; i < dimsLength; i++) {
      dims.push(buffer.readUInt32BE(offset));
      offset += 4;
    }

    const shape: TensorShape = { dims };
    const size = dims.reduce((a, b) => a * b, 1);

    const dataBuffer = buffer.slice(offset, offset + size * 4);
    const data = new Float32Array(dataBuffer.buffer, dataBuffer.byteOffset, size);
    offset += size * 4;

    const uncertainty = buffer.readFloatBE(offset);
    offset += 4;
    const precision = buffer.readFloatBE(offset);
    offset += 4;
    const superbitEncoded = buffer.readUInt32BE(offset) !== 0;

    return new SuperBitTensor(shape, new Float32Array(data), {
      uncertainty,
      precision,
      superbitEncoded,
    });
  }
}
