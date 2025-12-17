import {
  SuperBitValue,
  ProbValue,
  QuantumValue,
  BinaryValue,
  KnowledgeValue,
  EvolvedValueType,
  isEvolvedValue,
  coerceToNumeric,
  coerceToString,
} from '../types/evolved_values';
import { SuperBitTensor } from '../ai/superbit_tensor';
import { QuantumState } from '../quantum/quantum_state';
import { FuzzyBitEvaluator } from '../fuzzy_bits';
import { Memory } from '../memory';

describe('EvolvedValues', () => {
  describe('SuperBitValue', () => {
    it('should create a SuperBitValue from tensor', () => {
      const tensor = new SuperBitTensor({ dims: [3] }, new Float32Array([1, 0, 1]));
      const value = new SuperBitValue(tensor);

      expect(value.getType()).toBe(EvolvedValueType.SuperBit);
      expect(value.getTensor().getData()).toEqual(new Float32Array([1, 0, 1]));
    });

    it('should convert to numeric', () => {
      const tensor = new SuperBitTensor({ dims: [3] }, new Float32Array([1, 0, 1]));
      const value = new SuperBitValue(tensor);

      const numeric = value.toNumeric();
      expect(typeof numeric).toBe('number');
    });

    it('should serialize correctly', () => {
      const tensor = new SuperBitTensor({ dims: [3] }, new Float32Array([1, 0, 1]));
      const value = new SuperBitValue(tensor, { confidence: 0.9 });

      const serialized = value.serialize();
      expect(serialized.type).toBe(EvolvedValueType.SuperBit);
      expect(serialized.metadata).toBeDefined();
      expect(Array.from(serialized.tensor as Float32Array)).toEqual([1, 0, 1]);
    });

    it('should clone independently', () => {
      const tensor = new SuperBitTensor({ dims: [3] }, new Float32Array([1, 0, 1]));
      const value = new SuperBitValue(tensor);
      const cloned = value.clone();

      expect(cloned).not.toBe(value);
      expect(cloned.getTensor().getData()).toEqual(new Float32Array([1, 0, 1]));
    });

    it('should add two SuperBitValues', () => {
      const tensor1 = new SuperBitTensor({ dims: [3] }, new Float32Array([1, 0, 1]));
      const tensor2 = new SuperBitTensor({ dims: [3] }, new Float32Array([0, 1, 1]));
      const value1 = new SuperBitValue(tensor1, { uncertainty: 0.1 });
      const value2 = new SuperBitValue(tensor2, { uncertainty: 0.2 });

      const result = SuperBitValue.add(value1, value2);

      expect(result).toBeInstanceOf(SuperBitValue);
      const metadata = result.getMetadata();
      expect(metadata.uncertainty).toBeGreaterThan(0);
    });

    it('should propagate uncertainty in addition', () => {
      const tensor1 = new SuperBitTensor({ dims: [1] }, new Float32Array([1]));
      const tensor2 = new SuperBitTensor({ dims: [1] }, new Float32Array([1]));
      const value1 = new SuperBitValue(tensor1, { uncertainty: 0.3 });
      const value2 = new SuperBitValue(tensor2, { uncertainty: 0.4 });

      const result = SuperBitValue.add(value1, value2);
      const uncertainty = result.getMetadata().uncertainty;

      expect(uncertainty).toBeCloseTo(Math.sqrt(0.3 ** 2 + 0.4 ** 2), 5);
    });
  });

  describe('ProbValue', () => {
    it('should create a ProbValue with probability', () => {
      const value = new ProbValue(42, 0.8);

      expect(value.getType()).toBe(EvolvedValueType.Prob);
      expect(value.toNumeric()).toBe(42);
      expect(value.getProbability()).toBe(0.8);
    });

    it('should clamp probability to [0, 1]', () => {
      const value1 = new ProbValue(10, -0.5);
      const value2 = new ProbValue(10, 1.5);

      expect(value1.getProbability()).toBe(0);
      expect(value2.getProbability()).toBe(1);
    });

    it('should set uncertainty from probability', () => {
      const value = new ProbValue(100, 0.7);
      const metadata = value.getMetadata();

      expect(metadata.uncertainty).toBeCloseTo(0.3, 5);
    });

    it('should serialize correctly', () => {
      const value = new ProbValue(42, 0.9, { source: 'test' });
      const serialized = value.serialize();

      expect(serialized.type).toBe(EvolvedValueType.Prob);
      expect(serialized.value).toBe(42);
      expect(serialized.probability).toBe(0.9);
    });

    it('should add two ProbValues', () => {
      const value1 = new ProbValue(10, 0.9);
      const value2 = new ProbValue(5, 0.8);

      const result = ProbValue.add(value1, value2);

      expect(result.toNumeric()).toBe(15);
      expect(result.getProbability()).toBeCloseTo(0.72, 5);
    });

    it('should multiply two ProbValues', () => {
      const value1 = new ProbValue(3, 0.9);
      const value2 = new ProbValue(4, 0.8);

      const result = ProbValue.multiply(value1, value2);

      expect(result.toNumeric()).toBe(12);
      expect(result.getProbability()).toBeCloseTo(0.72, 5);
    });

    it('should propagate uncertainty in addition', () => {
      const value1 = new ProbValue(10, 0.9, { uncertainty: 0.1 });
      const value2 = new ProbValue(5, 0.8, { uncertainty: 0.2 });

      const result = ProbValue.add(value1, value2);
      const uncertainty = result.getMetadata().uncertainty;

      expect(uncertainty).toBeGreaterThan(0);
    });

    it('should format toString with probability and uncertainty', () => {
      const value = new ProbValue(42, 0.85);
      const str = value.toString();

      expect(str).toContain('Prob');
      expect(str).toContain('42');
      expect(str).toContain('0.850');
    });
  });

  describe('QuantumValue', () => {
    it('should create a QuantumValue from quantum state', () => {
      const fuzzy = new FuzzyBitEvaluator();
      const qstate = new QuantumState(fuzzy);
      qstate.allocateQubit();

      const value = new QuantumValue(qstate);

      expect(value.getType()).toBe(EvolvedValueType.Quantum);
      expect(value.getQuantumState()).toBe(qstate);
    });

    it('should measure and collapse quantum state', () => {
      const fuzzy = new FuzzyBitEvaluator();
      const qstate = new QuantumState(fuzzy);
      qstate.allocateQubit();

      const value = new QuantumValue(qstate);
      expect(value.isMeasured()).toBe(false);

      const result = value.measure(0);

      expect(value.isMeasured()).toBe(true);
      expect(result.value).toBeGreaterThanOrEqual(0);
      expect(result.value).toBeLessThanOrEqual(1);
      expect(result.probability).toBeGreaterThan(0);
      expect(result.probability).toBeLessThanOrEqual(1);
    });

    it('should update metadata after measurement', () => {
      const fuzzy = new FuzzyBitEvaluator();
      const qstate = new QuantumState(fuzzy);
      qstate.allocateQubit();

      const value = new QuantumValue(qstate);
      value.measure(0);

      const metadata = value.getMetadata();
      expect(metadata.confidence).toBeDefined();
      expect(metadata.uncertainty).toBeDefined();
    });

    it('should convert to numeric after measurement', () => {
      const fuzzy = new FuzzyBitEvaluator();
      const qstate = new QuantumState(fuzzy);
      qstate.allocateQubit();

      const value = new QuantumValue(qstate);
      const numeric = value.toNumeric();

      expect(typeof numeric).toBe('number');
      expect(value.isMeasured()).toBe(true);
    });

    it('should serialize with measurement state', () => {
      const fuzzy = new FuzzyBitEvaluator();
      const qstate = new QuantumState(fuzzy);
      qstate.allocateQubit();

      const value = new QuantumValue(qstate);
      value.measure(0);

      const serialized = value.serialize();
      expect(serialized.type).toBe(EvolvedValueType.Quantum);
      expect(serialized.measured).toBe(true);
      expect(serialized.measurementResult).toBeDefined();
    });

    it('should throw on invalid qubit measurement', () => {
      const fuzzy = new FuzzyBitEvaluator();
      const qstate = new QuantumState(fuzzy);
      qstate.allocateQubit();

      const value = new QuantumValue(qstate);

      expect(() => value.measure(5)).toThrow();
    });

    it('should clone with measurement state', () => {
      const fuzzy = new FuzzyBitEvaluator();
      const qstate = new QuantumState(fuzzy);
      qstate.allocateQubit();

      const value = new QuantumValue(qstate);
      value.measure(0);

      const cloned = value.clone();
      expect(cloned.isMeasured()).toBe(true);
      expect(cloned.getMeasurementResult()).toBeDefined();
    });
  });

  describe('BinaryValue', () => {
    it('should create a BinaryValue', () => {
      const value = new BinaryValue(42);

      expect(value.getType()).toBe(EvolvedValueType.Binary);
      expect(value.toNumeric()).toBe(42);
    });

    it('should floor decimal values', () => {
      const value = new BinaryValue(42.7);

      expect(value.toNumeric()).toBe(42);
    });

    it('should format toString with binary representation', () => {
      const value = new BinaryValue(5);
      const str = value.toString();

      expect(str).toContain('Binary');
      expect(str).toContain('5');
      expect(str).toContain('0b101');
    });

    it('should add two BinaryValues', () => {
      const value1 = new BinaryValue(10);
      const value2 = new BinaryValue(5);

      const result = BinaryValue.add(value1, value2);

      expect(result.toNumeric()).toBe(15);
    });

    it('should perform bitwise AND', () => {
      const value1 = new BinaryValue(0b1100);
      const value2 = new BinaryValue(0b1010);

      const result = BinaryValue.bitwiseAnd(value1, value2);

      expect(result.toNumeric()).toBe(0b1000);
    });

    it('should perform bitwise OR', () => {
      const value1 = new BinaryValue(0b1100);
      const value2 = new BinaryValue(0b1010);

      const result = BinaryValue.bitwiseOr(value1, value2);

      expect(result.toNumeric()).toBe(0b1110);
    });

    it('should perform bitwise XOR', () => {
      const value1 = new BinaryValue(0b1100);
      const value2 = new BinaryValue(0b1010);

      const result = BinaryValue.bitwiseXor(value1, value2);

      expect(result.toNumeric()).toBe(0b0110);
    });

    it('should serialize correctly', () => {
      const value = new BinaryValue(10);
      const serialized = value.serialize();

      expect(serialized.type).toBe(EvolvedValueType.Binary);
      expect(serialized.value).toBe(10);
      expect(serialized.binary).toBe('1010');
    });
  });

  describe('KnowledgeValue', () => {
    it('should create a KnowledgeValue', () => {
      const value = new KnowledgeValue({ name: 'test' }, 'entity-1');

      expect(value.getType()).toBe(EvolvedValueType.Knowledge);
      expect(value.getEntityId()).toBe('entity-1');
    });

    it('should convert numeric value', () => {
      const value = new KnowledgeValue(42);

      expect(value.toNumeric()).toBe(42);
    });

    it('should convert string to numeric', () => {
      const value = new KnowledgeValue('123.45');

      expect(value.toNumeric()).toBeCloseTo(123.45, 2);
    });

    it('should return 0 for non-numeric values', () => {
      const value = new KnowledgeValue({ complex: 'object' });

      expect(value.toNumeric()).toBe(0);
    });

    it('should add and retrieve relationships', () => {
      const value = new KnowledgeValue({ name: 'Alice' }, 'person-1');
      value.addRelationship('knows', 'person-2');
      value.addRelationship('worksAt', 'company-1');

      expect(value.getRelationship('knows')).toBe('person-2');
      expect(value.getRelationship('worksAt')).toBe('company-1');
    });

    it('should get all relationships', () => {
      const value = new KnowledgeValue({ name: 'Bob' });
      value.addRelationship('knows', 'Alice');
      value.addRelationship('likes', 'Coffee');

      const relationships = value.getRelationships();
      expect(relationships.size).toBe(2);
      expect(relationships.get('knows')).toBe('Alice');
      expect(relationships.get('likes')).toBe('Coffee');
    });

    it('should serialize with relationships', () => {
      const value = new KnowledgeValue({ name: 'Test' }, 'entity-1');
      value.addRelationship('type', 'Person');

      const serialized = value.serialize();
      expect(serialized.type).toBe(EvolvedValueType.Knowledge);
      expect(serialized.entityId).toBe('entity-1');
      expect(serialized.relationships).toBeDefined();
    });

    it('should format toString with ontology reference', () => {
      const value = new KnowledgeValue({ name: 'test' }, 'entity-1', {
        ontologyId: 'schema:Person',
      });
      const str = value.toString();

      expect(str).toContain('Knowledge');
      expect(str).toContain('@schema:Person');
    });
  });

  describe('Type Guards and Coercion', () => {
    it('should identify evolved values', () => {
      const binaryVal = new BinaryValue(42);
      const probVal = new ProbValue(10, 0.8);
      const numVal = 42;

      expect(isEvolvedValue(binaryVal)).toBe(true);
      expect(isEvolvedValue(probVal)).toBe(true);
      expect(isEvolvedValue(numVal)).toBe(false);
    });

    it('should coerce to numeric', () => {
      const binaryVal = new BinaryValue(42);
      const numVal = 100;

      expect(coerceToNumeric(binaryVal)).toBe(42);
      expect(coerceToNumeric(numVal)).toBe(100);
    });

    it('should coerce to string', () => {
      const probVal = new ProbValue(10, 0.9);
      const numVal = 42;

      const probStr = coerceToString(probVal);
      const numStr = coerceToString(numVal);

      expect(probStr).toContain('Prob');
      expect(numStr).toBe('42');
    });
  });

  describe('Memory Integration', () => {
    let memory: Memory;

    beforeEach(() => {
      memory = new Memory();
    });

    it('should store and retrieve evolved values', () => {
      const value = new BinaryValue(42);
      memory.setEvolvedRegister('x', value);

      const retrieved = memory.getEvolvedRegister('x');
      expect(retrieved).not.toBeNull();
      expect(retrieved!.toNumeric()).toBe(42);
    });

    it('should check evolved register existence', () => {
      const value = new ProbValue(10, 0.9);
      memory.setEvolvedRegister('x', value);

      expect(memory.hasEvolvedRegister('x')).toBe(true);
      expect(memory.hasEvolvedRegister('y')).toBe(false);
    });

    it('should get all evolved registers', () => {
      memory.setEvolvedRegister('x', new BinaryValue(1));
      memory.setEvolvedRegister('y', new ProbValue(2, 0.8));

      const allRegs = memory.getAllEvolvedRegisters();
      expect(Object.keys(allRegs)).toHaveLength(2);
    });

    it('should use setRegisterTyped for unified API', () => {
      memory.setRegisterTyped('x', new BinaryValue(42));
      memory.setRegisterTyped('y', 100);

      expect(memory.hasEvolvedRegister('x')).toBe(true);
      expect(memory.hasRegister('y')).toBe(true);
    });

    it('should coerce evolved values to numeric', () => {
      const value = new ProbValue(42, 0.9);
      memory.setEvolvedRegister('x', value);

      const numeric = memory.getRegisterAsNumeric('x');
      expect(numeric).toBe(42);
    });

    it('should get typed register values', () => {
      memory.setEvolvedRegister('x', new BinaryValue(42));
      memory.setRegister('y', 100);

      const xValue = memory.getRegisterTyped('x');
      const yValue = memory.getRegisterTyped('y');

      expect(isEvolvedValue(xValue)).toBe(true);
      expect(typeof yValue).toBe('number');
    });

    it('should clear evolved registers on reset', () => {
      memory.setEvolvedRegister('x', new BinaryValue(42));
      memory.reset();

      expect(memory.hasEvolvedRegister('x')).toBe(false);
    });

    it('should include evolved registers in snapshot', () => {
      memory.setEvolvedRegister('x', new BinaryValue(42));
      const snapshot = memory.getSnapshot();

      expect(snapshot.evolvedRegistersCount).toBe(1);
      expect(snapshot.evolvedRegisters).toBeDefined();
      expect(snapshot.evolvedRegisters.x).toBeDefined();
    });
  });

  describe('Metadata Management', () => {
    it('should store and retrieve metadata', () => {
      const value = new BinaryValue(42, {
        confidence: 0.95,
        encoding: 'custom',
        source: 'test',
      });

      const metadata = value.getMetadata();
      expect(metadata.confidence).toBe(0.95);
      expect(metadata.encoding).toBe('custom');
      expect(metadata.source).toBe('test');
    });

    it('should update metadata', () => {
      const value = new BinaryValue(42);
      value.setMetadata({ confidence: 0.8 });

      const metadata = value.getMetadata();
      expect(metadata.confidence).toBe(0.8);
    });

    it('should include creation timestamp', () => {
      const value = new BinaryValue(42);
      const metadata = value.getMetadata();

      expect(metadata.createdAt).toBeDefined();
      expect(metadata.createdAt).toBeGreaterThan(0);
    });
  });

  describe('Error Handling', () => {
    it('should reject non-evolved values in setEvolvedRegister', () => {
      const memory = new Memory();

      expect(() => memory.setEvolvedRegister('x', 42 as any)).toThrow();
    });

    it('should reject invalid types in setRegisterTyped', () => {
      const memory = new Memory();

      expect(() => memory.setRegisterTyped('x', 'string' as any)).toThrow();
    });

    it('should handle measurement on empty quantum state', () => {
      const fuzzy = new FuzzyBitEvaluator();
      const qstate = new QuantumState(fuzzy);
      const value = new QuantumValue(qstate);

      expect(() => value.measure(0)).toThrow();
    });
  });
});
