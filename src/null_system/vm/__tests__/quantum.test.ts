import { NullVM } from '../null_vm';
import { OpCode } from '../instructions';

describe('Quantum Simulation', () => {
  let vm: NullVM;

  beforeEach(() => {
    vm = new NullVM({ enableTracing: false });
  });

  test('Bell pair creation and measurement', () => {
    // 1. Alloc q0, q1
    // 2. H q0
    // 3. CNOT q0, q1
    // 4. Measure q0 -> r0
    // 5. Measure q1 -> r1
    // 6. Assert r0 == r1
    
    const program = [
      { opcode: OpCode.Q_ALLOC, args: ['q0'] },
      { opcode: OpCode.Q_ALLOC, args: ['q1'] },
      { opcode: OpCode.Q_SUPERPOSE, args: ['q0'] },
      { opcode: OpCode.Q_ENTANGLE, args: ['q0', 'q1'] },
      { opcode: OpCode.Q_MEASURE, args: ['q0', 'r0'] },
      { opcode: OpCode.Q_MEASURE, args: ['q1', 'r1'] },
    ];
    
    vm.execute(program);
    
    const state = vm.getState();
    const r0 = state.memory.registers['r0'];
    const r1 = state.memory.registers['r1'];
    
    expect(r0).toBeDefined();
    expect(r1).toBeDefined();
    expect(r0).toBe(r1);
  });
  
  test('Superposition statistics', () => {
      // Run many times to check probability is roughly 50/50
      let zeros = 0;
      let ones = 0;
      const iterations = 100;
      
      for(let i=0; i<iterations; i++) {
          const v = new NullVM();
          const p = [
              { opcode: OpCode.Q_ALLOC, args: ['q0'] },
              { opcode: OpCode.Q_SUPERPOSE, args: ['q0'] },
              { opcode: OpCode.Q_MEASURE, args: ['q0', 'r0'] }
          ];
          v.execute(p);
          const val = v.getState().memory.registers['r0'];
          if (val === 0) zeros++; else ones++;
      }
      
      expect(zeros).toBeGreaterThan(0);
      expect(ones).toBeGreaterThan(0);
  });

  test('Illegal gate application', () => {
     // Apply gate to non-existent qubit (out of bounds)
     // q0 defaults to 0. But state has 0 qubits, so index 0 is invalid.
     const program = [
         { opcode: OpCode.Q_SUPERPOSE, args: ['q0'] } 
     ];
     
     expect(() => vm.execute(program)).toThrow();
  });
  
  test('Multiple qubits allocation and state size', () => {
      const program = [
          { opcode: OpCode.Q_ALLOC, args: ['q0'] },
          { opcode: OpCode.Q_ALLOC, args: ['q1'] },
          { opcode: OpCode.Q_ALLOC, args: ['q2'] },
      ];
      
      vm.execute(program);
      const state = vm.getState();
      const q0 = state.memory.registers['q0'];
      const q1 = state.memory.registers['q1'];
      const q2 = state.memory.registers['q2'];
      
      expect(q0).toBe(0);
      expect(q1).toBe(1);
      expect(q2).toBe(2);
  });
});
