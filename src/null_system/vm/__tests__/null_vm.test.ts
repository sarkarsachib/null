import { NullVM } from '../null_vm';
import { OpCode, Instruction } from '../instructions';

describe('NullVM', () => {
  let vm: NullVM;

  beforeEach(() => {
    vm = new NullVM();
  });

  describe('Basic Operations', () => {
    it('should execute SET instruction', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 42] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(42);
    });

    it('should execute ADD instruction with immediate value', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 10] },
        { opcode: OpCode.ADD, args: ['x', 5] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(15);
    });

    it('should execute ADD instruction with register operand', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 10] },
        { opcode: OpCode.SET, args: ['y', 5] },
        { opcode: OpCode.ADD, args: ['x', 'y'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(15);
    });

    it('should execute SHOW instruction', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['result', 99] },
        { opcode: OpCode.SHOW, args: ['result'] },
      ];

      vm.execute(program);

      const frames = vm.getBinaryBridge().getFrames();
      expect(frames.length).toBeGreaterThan(0);
      expect(frames.some(f => f.frameType === 'OUTPUT')).toBe(true);
    });

    it('should handle multiple registers', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['a', 1] },
        { opcode: OpCode.SET, args: ['b', 2] },
        { opcode: OpCode.SET, args: ['c', 3] },
        { opcode: OpCode.ADD, args: ['a', 'b'] },
        { opcode: OpCode.ADD, args: ['a', 'c'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('a')).toBe(6);
      expect(vm.getMemory().getRegister('b')).toBe(2);
      expect(vm.getMemory().getRegister('c')).toBe(3);
    });
  });

  describe('Control Flow - IF', () => {
    it('should execute IF block when condition is true', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 5] },
        {
          opcode: OpCode.IF,
          args: [
            'x',
            '>',
            [
              { opcode: OpCode.SET, args: ['result', 100] },
            ],
          ],
        },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('result')).toBe(100);
    });

    it('should skip IF block when condition is false', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 5] },
        {
          opcode: OpCode.IF,
          args: [
            'x',
            '<',
            [
              { opcode: OpCode.SET, args: ['result', 100] },
            ],
          ],
        },
        { opcode: OpCode.SET, args: ['result', 0] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('result')).toBe(0);
    });

    it('should support equality comparison', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 0] },
        {
          opcode: OpCode.IF,
          args: [
            'x',
            '==',
            [
              { opcode: OpCode.SET, args: ['result', 50] },
            ],
          ],
        },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('result')).toBe(50);
    });

    it('should support != operator', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 5] },
        {
          opcode: OpCode.IF,
          args: [
            'x',
            '!=',
            [
              { opcode: OpCode.SET, args: ['result', 75] },
            ],
          ],
        },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('result')).toBe(75);
    });

    it('should support >= operator', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 5] },
        {
          opcode: OpCode.IF,
          args: [
            'x',
            '>=',
            [
              { opcode: OpCode.SET, args: ['result', 60] },
            ],
          ],
        },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('result')).toBe(60);
    });

    it('should support <= operator', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', -5] },
        {
          opcode: OpCode.IF,
          args: [
            'x',
            '<=',
            [
              { opcode: OpCode.SET, args: ['result', 40] },
            ],
          ],
        },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('result')).toBe(40);
    });
  });

  describe('Looping - REPEAT', () => {
    it('should execute REPEAT block correct number of times', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['counter', 0] },
        { opcode: OpCode.SET, args: ['count', 5] },
        {
          opcode: OpCode.REPEAT,
          args: [
            'count',
            [
              { opcode: OpCode.ADD, args: ['counter', 1] },
            ],
          ],
        },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('counter')).toBe(5);
    });

    it('should handle zero-count REPEAT', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 10] },
        { opcode: OpCode.SET, args: ['count', 0] },
        {
          opcode: OpCode.REPEAT,
          args: [
            'count',
            [
              { opcode: OpCode.ADD, args: ['x', 1] },
            ],
          ],
        },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(10);
    });

    it('should handle nested operations in REPEAT', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['result', 0] },
        { opcode: OpCode.SET, args: ['i', 3] },
        {
          opcode: OpCode.REPEAT,
          args: [
            'i',
            [
              { opcode: OpCode.SET, args: ['temp', 10] },
              { opcode: OpCode.ADD, args: ['result', 'temp'] },
            ],
          ],
        },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('result')).toBe(30);
    });
  });

  describe('Function Definitions and Calls', () => {
    it('should define and call a simple function', () => {
      const program: Instruction[] = [
        {
          opcode: OpCode.DEFINE,
          args: [
            'add_ten',
            [
              { opcode: OpCode.SET, args: ['x', 10] },
            ],
          ],
        },
        { opcode: OpCode.CALL, args: ['add_ten'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(10);
    });

    it('should allow function reuse', () => {
      const program: Instruction[] = [
        {
          opcode: OpCode.DEFINE,
          args: [
            'increment',
            [
              { opcode: OpCode.ADD, args: ['counter', 1] },
            ],
          ],
        },
        { opcode: OpCode.SET, args: ['counter', 0] },
        { opcode: OpCode.CALL, args: ['increment'] },
        { opcode: OpCode.CALL, args: ['increment'] },
        { opcode: OpCode.CALL, args: ['increment'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('counter')).toBe(3);
    });

    it('should handle function calls with local operations', () => {
      const program: Instruction[] = [
        {
          opcode: OpCode.DEFINE,
          args: [
            'square',
            [
              { opcode: OpCode.SET, args: ['temp', 5] },
              { opcode: OpCode.ADD, args: ['temp', 5] },
              { opcode: OpCode.ADD, args: ['result', 'temp'] },
            ],
          ],
        },
        { opcode: OpCode.SET, args: ['result', 0] },
        { opcode: OpCode.CALL, args: ['square'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('result')).toBe(10);
    });

    it('should fail when calling undefined function', () => {
      const program: Instruction[] = [
        { opcode: OpCode.CALL, args: ['undefined_function'] },
      ];

      expect(() => vm.execute(program)).toThrow();
    });

    it('should support multiple function definitions', () => {
      const program: Instruction[] = [
        {
          opcode: OpCode.DEFINE,
          args: [
            'func1',
            [
              { opcode: OpCode.SET, args: ['a', 100] },
            ],
          ],
        },
        {
          opcode: OpCode.DEFINE,
          args: [
            'func2',
            [
              { opcode: OpCode.SET, args: ['b', 200] },
            ],
          ],
        },
        { opcode: OpCode.CALL, args: ['func1'] },
        { opcode: OpCode.CALL, args: ['func2'] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('a')).toBe(100);
      expect(vm.getMemory().getRegister('b')).toBe(200);
    });
  });

  describe('Complex Scenarios', () => {
    it('should combine REPEAT and IF', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['sum', 0] },
        { opcode: OpCode.SET, args: ['i', 5] },
        {
          opcode: OpCode.REPEAT,
          args: [
            'i',
            [
              { opcode: OpCode.SET, args: ['val', 10] },
              {
                opcode: OpCode.IF,
                args: [
                  'val',
                  '>',
                  [
                    { opcode: OpCode.ADD, args: ['sum', 'val'] },
                  ],
                ],
              },
            ],
          ],
        },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('sum')).toBe(50);
    });

    it('should handle function calls within REPEAT', () => {
      const program: Instruction[] = [
        {
          opcode: OpCode.DEFINE,
          args: [
            'add_five',
            [
              { opcode: OpCode.ADD, args: ['total', 5] },
            ],
          ],
        },
        { opcode: OpCode.SET, args: ['total', 0] },
        { opcode: OpCode.SET, args: ['loops', 3] },
        {
          opcode: OpCode.REPEAT,
          args: [
            'loops',
            [
              { opcode: OpCode.CALL, args: ['add_five'] },
            ],
          ],
        },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('total')).toBe(15);
    });

    it('should handle nested IF blocks', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 10] },
        { opcode: OpCode.SET, args: ['y', 5] },
        {
          opcode: OpCode.IF,
          args: [
            'x',
            '>',
            [
              {
                opcode: OpCode.IF,
                args: [
                  'y',
                  '>',
                  [
                    { opcode: OpCode.SET, args: ['result', 100] },
                  ],
                ],
              },
            ],
          ],
        },
      ];

      vm.execute(program);

      // Should not crash
      expect(vm.getMemory().hasRegister('x')).toBe(true);
      expect(vm.getMemory().getRegister('result')).toBe(100);
    });
  });

  describe('Error Handling', () => {
    it('should handle invalid program format', () => {
      const invalidProgram = { invalid: 'structure' } as unknown as Record<string, unknown>[];

      expect(() => vm.execute(invalidProgram)).toThrow();
    });

    it('should handle invalid opcodes', () => {
      const program = [
        { opcode: 'INVALID', args: [] },
      ];

      expect(() => vm.execute(program)).toThrow();
    });

    it('should handle missing required arguments', () => {
      const program = [
        { opcode: OpCode.SET, args: [42] }, // Missing register name
      ];

      expect(() => vm.execute(program)).toThrow();
    });

    it('should throw on execution exceeding max cycles', () => {
      const smallVm = new NullVM({ maxCycles: 2 });
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 5] },
        { opcode: OpCode.SET, args: ['y', 10] },
        { opcode: OpCode.SET, args: ['z', 15] },
      ];

      expect(() => smallVm.execute(program)).toThrow();
    });
  });

  describe('VM State and Reset', () => {
    it('should track execution state', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 42] },
      ];

      vm.execute(program);

      const state = vm.getState();
      expect(state.executionCycle).toBeGreaterThan(0);
      expect(state.memory.registers).toHaveProperty('x');
    });

    it('should reset VM state', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 42] },
        { opcode: OpCode.SHOW, args: ['x'] },
      ];

      vm.execute(program);
      expect(vm.getMemory().getRegister('x')).toBe(42);
      expect(vm.getBinaryBridge().getFrameCount()).toBeGreaterThan(0);

      vm.reset();

      expect(vm.getMemory().getRegister('x')).toBe(0);
      expect(vm.getBinaryBridge().getFrameCount()).toBe(0);
      expect(vm.getExecutionCycle()).toBe(0);
    });

    it('should emit binary frames for SHOW operations', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 100] },
        { opcode: OpCode.SHOW, args: ['x'] },
      ];

      vm.execute(program);

      const frames = vm.getBinaryBridge().getFrames();
      expect(frames.some(f => f.frameType === 'OUTPUT')).toBe(true);
    });

    it('should emit register state frames for SET operations', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['myReg', 42] },
      ];

      vm.execute(program);

      const frames = vm.getBinaryBridge().getFrames();
      expect(frames.some(f => f.frameType === 'REGISTER')).toBe(true);
    });
  });

  describe('Fuzzy Bit Evaluation', () => {
    it('should support fuzzy bit evaluator', () => {
      const vmFuzzy = new NullVM();
      const evaluator = vmFuzzy.getFuzzyBitEvaluator();

      expect(evaluator.evaluateCondition('>', 5)).toBe(true);
      expect(evaluator.evaluateCondition('>', -5)).toBe(false);
      expect(evaluator.evaluateCondition('==', 0)).toBe(true);
    });

    it('should allow fuzzy bit configuration', () => {
      const vmFuzzy = new NullVM({
        fuzzyBitConfig: { probabilityThreshold: 0.7, noiseLevel: 0.1 },
      });

      const config = vmFuzzy.getFuzzyBitEvaluator().getConfig();
      expect(config.probabilityThreshold).toBe(0.7);
      expect(config.noiseLevel).toBe(0.1);
    });
  });

  describe('NOP Instruction', () => {
    it('should execute NOP without side effects', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 42] },
        { opcode: OpCode.NOP, args: [] },
        { opcode: OpCode.NOP, args: [] },
      ];

      vm.execute(program);

      expect(vm.getMemory().getRegister('x')).toBe(42);
    });
  });
});
