import { SuperBitTensor } from '../ai/superbit_tensor';
import { QuantumState } from '../quantum/quantum_state';
import { measureQubit, MeasurementResult } from '../quantum/measurement';
import { FuzzyBitEvaluator } from '../fuzzy_bits';

export enum EvolvedValueType {
  SuperBit = 'SuperBit',
  Prob = 'Prob',
  Quantum = 'Quantum',
  Binary = 'Binary',
  Knowledge = 'Knowledge',
}

export interface EvolvedValueMetadata {
  confidence?: number;
  encoding?: string;
  ontologyId?: string;
  precision?: number;
  uncertainty?: number;
  createdAt?: number;
  source?: string;
}

export abstract class EvolvedValue<T> {
  protected value: T;
  protected metadata: EvolvedValueMetadata;
  public readonly type: EvolvedValueType;

  constructor(value: T, type: EvolvedValueType, metadata: EvolvedValueMetadata = {}) {
    this.value = value;
    this.type = type;
    this.metadata = {
      ...metadata,
      createdAt: metadata.createdAt || Date.now(),
    };
  }

  abstract toNumeric(): number;
  abstract toString(): string;
  abstract clone(): EvolvedValue<T>;
  abstract serialize(): Record<string, unknown>;

  getValue(): T {
    return this.value;
  }

  getMetadata(): EvolvedValueMetadata {
    return { ...this.metadata };
  }

  setMetadata(metadata: Partial<EvolvedValueMetadata>): void {
    this.metadata = { ...this.metadata, ...metadata };
  }

  getType(): EvolvedValueType {
    return this.type;
  }
}

export class SuperBitValue extends EvolvedValue<SuperBitTensor> {
  constructor(tensor: SuperBitTensor, metadata: EvolvedValueMetadata = {}) {
    const tensorMetadata = tensor.getMetadata();
    super(tensor, EvolvedValueType.SuperBit, {
      ...metadata,
      uncertainty: metadata.uncertainty ?? tensorMetadata.uncertainty,
      precision: metadata.precision ?? tensorMetadata.precision,
      encoding: metadata.encoding ?? 'superbit',
    });
  }

  toNumeric(): number {
    const shape = this.value.getShape();
    const data = this.value.getData();
    if (shape.dims.length === 0 || (shape.dims.length === 1 && shape.dims[0] === 1)) {
      if (data.length === 0) return 0;
      return data[0];
    }
    return Array.from(data).reduce((acc, val) => acc + val, 0) / data.length;
  }

  toString(): string {
    return `SuperBit<${this.value.getShape().dims.join('x')}>(uncertainty=${this.metadata.uncertainty?.toFixed(3) || 0})`;
  }

  clone(): SuperBitValue {
    return new SuperBitValue(this.value.clone(), this.getMetadata());
  }

  serialize(): Record<string, unknown> {
    return {
      type: this.type,
      shape: this.value.getShape(),
      metadata: this.metadata,
      tensor: Array.from(this.value.getData()),
    };
  }

  getTensor(): SuperBitTensor {
    return this.value.clone();
  }

  static add(a: SuperBitValue, b: SuperBitValue): SuperBitValue {
    const aData = a.value.getData();
    const bData = b.value.getData();
    const aShape = a.value.getShape();
    const bShape = b.value.getShape();

    if (aData.length !== bData.length) {
      throw new Error('Cannot add SuperBitValues with different sizes');
    }

    const resultData = new Float32Array(aData.length);
    for (let i = 0; i < aData.length; i++) {
      resultData[i] = aData[i] + bData[i];
    }

    const resultTensor = new SuperBitTensor(aShape, resultData);
    const combinedUncertainty = Math.sqrt(
      (a.metadata.uncertainty || 0) ** 2 + (b.metadata.uncertainty || 0) ** 2
    );
    return new SuperBitValue(resultTensor, {
      uncertainty: combinedUncertainty,
      confidence: Math.min(a.metadata.confidence || 1.0, b.metadata.confidence || 1.0),
      encoding: a.metadata.encoding,
    });
  }
}

export class ProbValue extends EvolvedValue<number> {
  private probability: number;

  constructor(
    value: number,
    probability: number = 1.0,
    metadata: EvolvedValueMetadata = {}
  ) {
    super(value, EvolvedValueType.Prob, {
      ...metadata,
      uncertainty: metadata.uncertainty ?? (1 - probability),
      confidence: metadata.confidence ?? probability,
      encoding: 'probabilistic',
    });
    this.probability = Math.max(0, Math.min(1, probability));
  }

  toNumeric(): number {
    return this.value;
  }

  toString(): string {
    return `Prob<${this.value}>(p=${this.probability.toFixed(3)}, ±${(this.metadata.uncertainty || 0).toFixed(3)})`;
  }

  clone(): ProbValue {
    return new ProbValue(this.value, this.probability, this.getMetadata());
  }

  serialize(): Record<string, unknown> {
    return {
      type: this.type,
      value: this.value,
      probability: this.probability,
      metadata: this.metadata,
    };
  }

  getProbability(): number {
    return this.probability;
  }

  static add(a: ProbValue, b: ProbValue): ProbValue {
    const resultValue = a.value + b.value;
    const uncertaintyA = a.metadata.uncertainty || 0;
    const uncertaintyB = b.metadata.uncertainty || 0;
    const combinedUncertainty = Math.sqrt(uncertaintyA ** 2 + uncertaintyB ** 2);
    const combinedProbability = a.probability * b.probability;

    return new ProbValue(resultValue, combinedProbability, {
      uncertainty: combinedUncertainty,
      confidence: Math.min(a.metadata.confidence || 1.0, b.metadata.confidence || 1.0),
    });
  }

  static multiply(a: ProbValue, b: ProbValue): ProbValue {
    const resultValue = a.value * b.value;
    const uncertaintyA = a.metadata.uncertainty || 0;
    const uncertaintyB = b.metadata.uncertainty || 0;
    const relativeUncertainty = Math.sqrt(
      (uncertaintyA / (a.value || 1)) ** 2 + (uncertaintyB / (b.value || 1)) ** 2
    );
    const absoluteUncertainty = Math.abs(resultValue) * relativeUncertainty;
    const combinedProbability = a.probability * b.probability;

    return new ProbValue(resultValue, combinedProbability, {
      uncertainty: absoluteUncertainty,
      confidence: Math.min(a.metadata.confidence || 1.0, b.metadata.confidence || 1.0),
    });
  }
}

export class QuantumValue extends EvolvedValue<QuantumState> {
  private measured: boolean = false;
  private measurementResult?: MeasurementResult;

  constructor(
    quantumState: QuantumState,
    metadata: EvolvedValueMetadata = {}
  ) {
    super(quantumState, EvolvedValueType.Quantum, {
      ...metadata,
      encoding: 'quantum',
      confidence: metadata.confidence ?? 0.5,
      uncertainty: metadata.uncertainty ?? 1.0,
    });
  }

  toNumeric(): number {
    if (!this.measured) {
      this.measure(0);
    }
    return this.measurementResult?.value || 0;
  }

  toString(): string {
    if (this.measured) {
      return `Quantum<measured=${this.measurementResult?.value}>(p=${this.measurementResult?.probability.toFixed(3)})`;
    }
    return `Quantum<qubits=${this.value.qubitCount}>(superposition)`;
  }

  clone(): QuantumValue {
    const newQuantumState = new QuantumState(new FuzzyBitEvaluator());
    const stateVector = this.value.getStateVector();
    if (stateVector.length > 1) {
      for (let i = 0; i < this.value.qubitCount; i++) {
        newQuantumState.allocateQubit();
      }
      newQuantumState.setStateVector([...stateVector]);
    }
    const cloned = new QuantumValue(newQuantumState, this.getMetadata());
    if (this.measured) {
      cloned.measured = this.measured;
      cloned.measurementResult = { ...this.measurementResult! };
    }
    return cloned;
  }

  serialize(): Record<string, unknown> {
    return {
      type: this.type,
      qubits: this.value.qubitCount,
      measured: this.measured,
      measurementResult: this.measurementResult,
      metadata: this.metadata,
    };
  }

  measure(qubitIndex: number = 0): MeasurementResult {
    if (this.value.qubitCount === 0) {
      throw new Error('Cannot measure: no qubits allocated');
    }
    if (qubitIndex >= this.value.qubitCount) {
      throw new Error(`Cannot measure qubit ${qubitIndex}: only ${this.value.qubitCount} qubits allocated`);
    }
    this.measurementResult = measureQubit(this.value, qubitIndex);
    this.measured = true;
    this.metadata.confidence = this.measurementResult.probability;
    this.metadata.uncertainty = 1 - this.measurementResult.probability;
    return this.measurementResult;
  }

  isMeasured(): boolean {
    return this.measured;
  }

  getMeasurementResult(): MeasurementResult | undefined {
    return this.measurementResult;
  }

  getQuantumState(): QuantumState {
    return this.value;
  }
}

export class BinaryValue extends EvolvedValue<number> {
  constructor(value: number, metadata: EvolvedValueMetadata = {}) {
    super(Math.floor(value), EvolvedValueType.Binary, {
      encoding: 'binary',
      confidence: 1.0,
      uncertainty: 0,
      precision: Number.MAX_SAFE_INTEGER,
      ...metadata,
    });
  }

  toNumeric(): number {
    return this.value;
  }

  toString(): string {
    return `Binary<${this.value}>(0b${this.value.toString(2)})`;
  }

  clone(): BinaryValue {
    return new BinaryValue(this.value, this.getMetadata());
  }

  serialize(): Record<string, unknown> {
    return {
      type: this.type,
      value: this.value,
      binary: this.value.toString(2),
      metadata: this.metadata,
    };
  }

  static add(a: BinaryValue, b: BinaryValue): BinaryValue {
    return new BinaryValue(a.value + b.value, {
      confidence: Math.min(a.metadata.confidence || 1.0, b.metadata.confidence || 1.0),
      encoding: 'binary',
    });
  }

  static bitwiseAnd(a: BinaryValue, b: BinaryValue): BinaryValue {
    return new BinaryValue(a.value & b.value, {
      confidence: Math.min(a.metadata.confidence || 1.0, b.metadata.confidence || 1.0),
      encoding: 'binary',
    });
  }

  static bitwiseOr(a: BinaryValue, b: BinaryValue): BinaryValue {
    return new BinaryValue(a.value | b.value, {
      confidence: Math.min(a.metadata.confidence || 1.0, b.metadata.confidence || 1.0),
      encoding: 'binary',
    });
  }

  static bitwiseXor(a: BinaryValue, b: BinaryValue): BinaryValue {
    return new BinaryValue(a.value ^ b.value, {
      confidence: Math.min(a.metadata.confidence || 1.0, b.metadata.confidence || 1.0),
      encoding: 'binary',
    });
  }
}

export class KnowledgeValue extends EvolvedValue<unknown> {
  private entityId?: string;
  private relationships: Map<string, unknown> = new Map();

  constructor(
    value: unknown,
    entityId?: string,
    metadata: EvolvedValueMetadata = {}
  ) {
    super(value, EvolvedValueType.Knowledge, {
      ...metadata,
      encoding: 'knowledge',
      ontologyId: metadata.ontologyId || entityId,
      confidence: metadata.confidence ?? 0.8,
    });
    this.entityId = entityId;
  }

  toNumeric(): number {
    if (typeof this.value === 'number') {
      return this.value;
    }
    if (typeof this.value === 'string') {
      const parsed = parseFloat(this.value);
      return isNaN(parsed) ? 0 : parsed;
    }
    return 0;
  }

  toString(): string {
    const ontologyRef = this.metadata.ontologyId ? `@${this.metadata.ontologyId}` : '';
    return `Knowledge<${JSON.stringify(this.value)}>${ontologyRef}`;
  }

  clone(): KnowledgeValue {
    const cloned = new KnowledgeValue(this.value, this.entityId, this.getMetadata());
    this.relationships.forEach((value, key) => {
      cloned.relationships.set(key, value);
    });
    return cloned;
  }

  serialize(): Record<string, unknown> {
    return {
      type: this.type,
      value: this.value,
      entityId: this.entityId,
      relationships: Object.fromEntries(this.relationships),
      metadata: this.metadata,
    };
  }

  getEntityId(): string | undefined {
    return this.entityId;
  }

  addRelationship(relationshipType: string, target: unknown): void {
    this.relationships.set(relationshipType, target);
  }

  getRelationship(relationshipType: string): unknown {
    return this.relationships.get(relationshipType);
  }

  getRelationships(): Map<string, unknown> {
    return new Map(this.relationships);
  }
}

export type AnyEvolvedValue =
  | SuperBitValue
  | ProbValue
  | QuantumValue
  | BinaryValue
  | KnowledgeValue;

export function isEvolvedValue(value: unknown): value is AnyEvolvedValue {
  return value instanceof EvolvedValue;
}

export function coerceToNumeric(value: number | AnyEvolvedValue): number {
  if (typeof value === 'number') {
    return value;
  }
  if (isEvolvedValue(value)) {
    return value.toNumeric();
  }
  return 0;
}

export function coerceToString(value: number | AnyEvolvedValue): string {
  if (typeof value === 'number') {
    return value.toString();
  }
  if (isEvolvedValue(value)) {
    return value.toString();
  }
  return String(value);
}
