import { createSampleProgram, createComprehensiveDemo } from '../sample_program';
import { NullVM } from '../../null_system/vm';

describe('Sample Programs', () => {
  describe('Sample Program', () => {
    it('should execute the sample factorial-like program', () => {
      const vm = new NullVM();
      const program = createSampleProgram();

      expect(() => vm.execute(program)).not.toThrow();
    });

    it('should produce expected state from sample program', () => {
      const vm = new NullVM();
      const program = createSampleProgram();

      vm.execute(program);

      const state = vm.getState();
      expect(state.memory.registers).toHaveProperty('n');
      expect(state.memory.registers).toHaveProperty('result');
    });

    it('should emit binary frames from sample program', () => {
      const vm = new NullVM();
      const program = createSampleProgram();

      vm.execute(program);

      const frames = vm.getBinaryBridge().getFrames();
      expect(frames.length).toBeGreaterThan(0);
    });
  });

  describe('Comprehensive Demo Program', () => {
    it('should execute comprehensive demo without errors', () => {
      const vm = new NullVM();
      const program = createComprehensiveDemo();

      expect(() => vm.execute(program)).not.toThrow();
    });

    it('should demonstrate arithmetic operations', () => {
      const vm = new NullVM();
      const program = createComprehensiveDemo();

      vm.execute(program);

      const registers = vm.getMemory().getAllRegisters();
      expect(registers.a).toBe(30); // 10 + 20
    });

    it('should demonstrate conditional logic', () => {
      const vm = new NullVM();
      const program = createComprehensiveDemo();

      vm.execute(program);

      const registers = vm.getMemory().getAllRegisters();
      expect(registers.condition_result).toBe(1);
    });

    it('should demonstrate function calls', () => {
      const vm = new NullVM();
      const program = createComprehensiveDemo();

      vm.execute(program);

      const registers = vm.getMemory().getAllRegisters();
      expect(registers.working_val).toBe(10); // 5 + 5
    });

    it('should demonstrate loops', () => {
      const vm = new NullVM();
      const program = createComprehensiveDemo();

      vm.execute(program);

      const registers = vm.getMemory().getAllRegisters();
      expect(registers.counter).toBe(3);
    });

    it('should demonstrate nested control structures', () => {
      const vm = new NullVM();
      const program = createComprehensiveDemo();

      vm.execute(program);

      const registers = vm.getMemory().getAllRegisters();
      expect(registers.nested_result).toBe(100);
    });

    it('should emit multiple frame types', () => {
      const vm = new NullVM();
      const program = createComprehensiveDemo();

      vm.execute(program);

      const frames = vm.getBinaryBridge().getFrames();
      const frameTypes = new Set(frames.map((f) => f.frameType));

      expect(frameTypes.has('OUTPUT')).toBe(true);
      expect(frameTypes.has('REGISTER')).toBe(true);
    });

    it('should execute efficiently', () => {
      const vm = new NullVM();
      const program = createComprehensiveDemo();

      vm.execute(program);

      const cycles = vm.getExecutionCycle();
      expect(cycles).toBeLessThan(1000); // Should complete in reasonable time
    });
  });

  describe('Program Structure', () => {
    it('sample program should have instructions', () => {
      const program = createSampleProgram();
      expect(Array.isArray(program)).toBe(true);
      expect(program.length).toBeGreaterThan(0);
    });

    it('comprehensive demo should have instructions', () => {
      const program = createComprehensiveDemo();
      expect(Array.isArray(program)).toBe(true);
      expect(program.length).toBeGreaterThan(0);
    });

    it('all programs should have valid opcodes', () => {
      const programs = [createSampleProgram(), createComprehensiveDemo()];

      const validOpcodes = [
        'SET',
        'ADD',
        'SHOW',
        'IF',
        'REPEAT',
        'DEFINE',
        'CALL',
        'RETURN',
        'JMP',
        'NOP',
      ];

      for (const program of programs) {
        for (const instruction of program) {
          expect(validOpcodes).toContain(instruction.opcode);
        }
      }
    });
  });

  describe('End-to-End Execution', () => {
    it('should maintain state across multiple operations', () => {
      const vm = new NullVM();
      const program: Record<string, unknown>[] = [
        { opcode: 'SET', args: ['x', 10] },
        { opcode: 'SET', args: ['y', 20] },
        { opcode: 'ADD', args: ['x', 'y'] },
        { opcode: 'SHOW', args: ['x'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(30);
      expect(vm.getBinaryBridge().getFrameCount()).toBeGreaterThan(0);
    });

    it('should reset properly between executions', () => {
      const vm = new NullVM();

      // First execution
      const prog1: Record<string, unknown>[] = [{ opcode: 'SET', args: ['x', 10] }];
      vm.execute(prog1);
      expect(vm.getMemory().getRegister('x')).toBe(10);

      // Reset
      vm.reset();
      expect(vm.getMemory().getRegister('x')).toBe(0);

      // Second execution
      const prog2: Record<string, unknown>[] = [{ opcode: 'SET', args: ['x', 20] }];
      vm.execute(prog2);
      expect(vm.getMemory().getRegister('x')).toBe(20);
    });
  });
});
