import { Complex, C, addC, subC, mulC, GateLibrary, GateMatrix } from './gate_library';
import { FuzzyBitEvaluator } from '../fuzzy_bits';

export class QuantumState {
  private stateVector: Complex[];
  private numQubits: number;
  private fuzzyEvaluator: FuzzyBitEvaluator;

  constructor(fuzzyEvaluator: FuzzyBitEvaluator) {
    this.stateVector = [C(1, 0)]; // Initial state |0...0> (empty means magnitude 1)
    this.numQubits = 0;
    this.fuzzyEvaluator = fuzzyEvaluator;
  }

  get qubitCount(): number {
    return this.numQubits;
  }

  allocateQubit(): number {
    const newQubitIndex = this.numQubits;
    this.numQubits++;
    
    // Expand state vector: |psi> -> |psi> (x) |0>
    // Assuming new qubit is the least significant bit (or most? let's stick to LSB convention for indexing convenience usually)
    // Actually, if we append |0>, the state vector doubles.
    // |psi> = [a, b, ...]
    // |psi> (x) |0> = [a, b, ..., 0, 0, ...] if |0> is second in tensor product?
    // Let's verify: [1, 0] (x) [a, b] = [1*[a,b], 0*[a,b]] = [a, b, 0, 0].
    // So if the new qubit is the 'first' one in tensor product (MSB), the vector is just padded with zeros.
    // Let's treat the new qubit as the MSB (highest index).
    
    const oldSize = this.stateVector.length;
    const newSize = oldSize * 2;
    // We just extend with zeros because the new qubit is definitely 0.
    for (let i = oldSize; i < newSize; i++) {
      this.stateVector.push(C(0, 0));
    }
    
    return newQubitIndex;
  }

  applyGate(gateName: string, targetQubits: number[]) {
    const matrix = GateLibrary[gateName];
    if (!matrix) {
      throw new Error(`Unknown gate: ${gateName}`);
    }

    // Basic noise simulation:
    // With some probability, apply a random rotation or flip?
    // For now, let's keep it clean but check noise config.
    const config = this.fuzzyEvaluator.getConfig();
    if (config.noiseLevel && config.noiseLevel > 0) {
        // TODO: Implement noise
    }

    if (targetQubits.length === 1) {
      this.applySingleQubitGate(matrix, targetQubits[0]);
    } else if (targetQubits.length === 2) {
       this.applyTwoQubitGate(matrix, targetQubits[0], targetQubits[1]);
    } else {
      throw new Error("Only 1 and 2 qubit gates supported currently");
    }
  }

  private applySingleQubitGate(matrix: GateMatrix, target: number) {
    const size = this.stateVector.length;
    // Iterate over all pairs of states where only bit 'target' differs
    // bit 'target' is 0 or 1.
    const step = 1 << target;
    
    for (let i = 0; i < size; i += 2 * step) {
      for (let j = 0; j < step; j++) {
        const idx0 = i + j;
        const idx1 = i + j + step;
        
        const amp0 = this.stateVector[idx0];
        const amp1 = this.stateVector[idx1];
        
        // [ new0 ]   [ m00 m01 ] [ amp0 ]
        // [ new1 ] = [ m10 m11 ] [ amp1 ]
        
        const new0 = addC(mulC(matrix[0][0], amp0), mulC(matrix[0][1], amp1));
        const new1 = addC(mulC(matrix[1][0], amp0), mulC(matrix[1][1], amp1));
        
        this.stateVector[idx0] = new0;
        this.stateVector[idx1] = new1;
      }
    }
  }
  
  private applyTwoQubitGate(matrix: GateMatrix, control: number, target: number) {
      // General 2-qubit gate application is complex if we allow arbitrary qubits.
      // But usually we just implement CNOT.
      // CNOT matrix is 4x4.
      // We iterate over groups of 4 indices: 00, 01, 10, 11 for the two bits.
      // This is getting complicated to implement generically for any 2-qubit gate 
      // without swapping or clever indexing.
      
      // For specific case of CNOT where we control on 'control' and target 'target':
      // If control bit is 0, nothing happens.
      // If control bit is 1, apply X to target.
      
      // Let's assume the matrix provided is standard CNOT (control=0-th of pair, target=1-st of pair in standard basis)
      // But here `control` and `target` are arbitrary indices in the state vector.
      
      // If it is indeed CNOT, we can optimize.
      // If it's a general 4x4 matrix, we need to map the matrix indices (0,1,2,3) to the state vector indices.
      
      // Let's implement CNOT logic directly for now as it's the only 2-qubit gate we likely need.
      // If gate is NOT CNOT, throw error for now or implement generic later.
      
      // Actually, let's look at the matrix passed.
      // If we implement `Q_ENTANGLE` it usually implies CNOT.
      
      // Logic for CNOT(control, target):
      // For every state index `i`:
      //   if bit `control` is set:
      //      swap amplitudes of `i` (where target=0) and `i XOR (1<<target)` (where target=1)
      
      const size = this.stateVector.length;
      
      // We need to iterate such that we find pairs (i, j) where i has control=1, target=0
      // and j has control=1, target=1. And i, j differ only in target bit.
      
      // Iterate all `k` from 0 to size-1.
      // If k has control bit == 1:
      //    if k has target bit == 0:
      //       swap state[k] and state[k | (1<<target)]
      
      // To avoid double swapping, we only iterate k where target bit is 0.
      
      for (let k = 0; k < size; k++) {
          if (((k >> control) & 1) === 1) { // Control is 1
              if (((k >> target) & 1) === 0) { // Target is 0
                  const partner = k | (1 << target);
                  const temp = this.stateVector[k];
                  this.stateVector[k] = this.stateVector[partner];
                  this.stateVector[partner] = temp;
              }
          }
      }
  }

  getStateVector(): Complex[] {
      return [...this.stateVector];
  }
  
  getAmplitude(index: number): Complex {
      return this.stateVector[index];
  }

  // Used by measurement module
  setStateVector(newState: Complex[]) {
      if (newState.length !== this.stateVector.length) {
          throw new Error("State vector size mismatch");
      }
      this.stateVector = newState;
  }
}
