import { QuantumState } from './quantum_state';
import { Complex, absC, C, mulC } from './gate_library';

export interface MeasurementResult {
  value: number; // 0 or 1
  probability: number;
}

export function measureQubit(state: QuantumState, qubitIndex: number): MeasurementResult {
  const stateVector = state.getStateVector();
  const size = stateVector.length;
  
  // Calculate probability of 0
  let prob0 = 0;
  for (let i = 0; i < size; i++) {
    if (((i >> qubitIndex) & 1) === 0) {
      const mag = absC(stateVector[i]);
      prob0 += mag * mag;
    }
  }
  
  // Determine outcome
  const rand = Math.random(); // TODO: Use seeded RNG from VM if available? Or FuzzyBitEvaluator?
  const outcome = rand < prob0 ? 0 : 1;
  const probOutcome = outcome === 0 ? prob0 : (1 - prob0);
  
  // Collapse state
  const normFactor = 1 / Math.sqrt(probOutcome);
  const newState: Complex[] = new Array(size);
  
  for (let i = 0; i < size; i++) {
    const bitSet = ((i >> qubitIndex) & 1) === 1;
    if ((outcome === 0 && !bitSet) || (outcome === 1 && bitSet)) {
      newState[i] = mulC(stateVector[i], C(normFactor, 0));
    } else {
      newState[i] = C(0, 0);
    }
  }
  
  state.setStateVector(newState);
  
  return {
    value: outcome,
    probability: probOutcome
  };
}
