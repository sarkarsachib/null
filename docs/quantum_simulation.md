# Quantum Simulation Layer for NullVM

The NullVM Quantum Simulation Layer allows execution of quantum-like programs using super-bits as virtual qubits. It supports a full state vector simulation, entanglement, and measurement.

## Quantum Instructions

The following new opcodes are available:

- `Q_ALLOC <target_reg>`: Allocates a new qubit and stores its handle (ID) in the target register.
- `Q_SUPERPOSE <qubit_reg>`: Applies a Hadamard gate to the qubit referenced by the register.
- `Q_ENTANGLE <control_reg> <target_reg>`: Entangles two qubits using a CNOT operation.
- `Q_APPLY <gate_name> <qubit_regs>`: Applies a specified gate (e.g., "X", "Y", "Z") to the given qubits.
- `Q_MEASURE <qubit_reg> <dest_reg>`: Measures a qubit, collapsing its state, and stores the result (0 or 1) in a classical register.

## Simulation Model

The simulator maintains a global state vector for all allocated qubits.
- Initial state is `|0>`.
- `Q_ALLOC` expands the state vector.
- Gates update the complex amplitudes of the state vector.
- Measurement calculates probabilities based on amplitude magnitudes squared, probabilistically selects an outcome, and collapses the state vector.

## Noise and Fuzzy Evaluation

The system integrates with `FuzzyBitEvaluator` to introduce probabilistic noise. (Currently partially implemented).

## Example Program

```typescript
// Bell State Creation
[
  { opcode: 'Q_ALLOC', args: ['q0'] },
  { opcode: 'Q_ALLOC', args: ['q1'] },
  { opcode: 'Q_SUPERPOSE', args: ['q0'] },
  { opcode: 'Q_ENTANGLE', args: ['q0', 'q1'] },
  { opcode: 'Q_MEASURE', args: ['q0', 'r0'] },
  { opcode: 'Q_MEASURE', args: ['q1', 'r1'] }
]
// Expect r0 == r1 with ~50% probability for 0 and 1.
```

## Binary Bridge Events

Quantum events are emitted via the Binary Bridge:
- `Q_ALLOC`: `{ register, qubitIndex }`
- `Q_SUPERPOSE`: `{ register, qubitIndex }`
- `Q_ENTANGLE`: `{ controlReg, targetReg, controlIndex, targetIndex }`
- `Q_APPLY`: `{ gateName, qubitRegs, qubitIndices }`
- `Q_MEASURE`: `{ qubitReg, destReg, qubitIndex, value, probability }`

This allows external tooling to visualize the quantum circuit and execution flow.
