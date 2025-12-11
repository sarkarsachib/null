import { ExecutionContext, TraceHook } from '../execution_context';
import { OpCode, Instruction } from '../instructions';

describe('ExecutionContext', () => {
  let context: ExecutionContext;

  beforeEach(() => {
    context = new ExecutionContext();
  });

  describe('Program Management', () => {
    it('should set and retrieve current instruction', () => {
      const instructions: Instruction[] = [{ opcode: OpCode.SET, args: ['x', 1] }];
      context.setProgram(instructions);

      const current = context.getCurrentInstruction();
      expect(current?.opcode).toBe(OpCode.SET);
    });

    it('should return null when program counter exceeds program length', () => {
      const instructions: Instruction[] = [{ opcode: OpCode.SET, args: ['x', 1] }];
      context.setProgram(instructions);
      context.setProgramCounter(1);

      expect(context.getCurrentInstruction()).toBeNull();
    });

    it('should advance program counter', () => {
      const instructions: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 1] },
        { opcode: OpCode.SET, args: ['y', 2] },
      ];
      context.setProgram(instructions);

      expect(context.getProgramCounter()).toBe(0);
      context.advanceProgramCounter();
      expect(context.getProgramCounter()).toBe(1);
    });

    it('should set program counter to specific address', () => {
      const instructions: Instruction[] = [
        { opcode: OpCode.SET, args: ['x', 1] },
        { opcode: OpCode.SET, args: ['y', 2] },
        { opcode: OpCode.SET, args: ['z', 3] },
      ];
      context.setProgram(instructions);

      context.setProgramCounter(2);
      expect(context.getProgramCounter()).toBe(2);
      expect(context.getCurrentInstruction()?.args[0]).toBe('z');
    });

    it('should reject invalid program counter addresses', () => {
      const instructions: Instruction[] = [{ opcode: OpCode.SET, args: ['x', 1] }];
      context.setProgram(instructions);

      expect(() => context.setProgramCounter(-1)).toThrow();
      expect(() => context.setProgramCounter(999)).toThrow();
    });
  });

  describe('Call Stack Management', () => {
    it('should push and pop call frames', () => {
      context.pushCallFrame('func1', 5, 0);
      expect(context.getCallStackDepth()).toBe(1);

      const frame = context.popCallFrame();
      expect(frame.functionName).toBe('func1');
      expect(frame.returnAddress).toBe(5);
      expect(context.getCallStackDepth()).toBe(0);
    });

    it('should save stack pointer in call frame', () => {
      context.pushCallFrame('func', 0, 42);
      const frame = context.popCallFrame();

      expect(frame.savedStackPointer).toBe(42);
    });

    it('should get current call frame', () => {
      expect(context.getCurrentCallFrame()).toBeNull();

      context.pushCallFrame('func', 0, 0);
      const frame = context.getCurrentCallFrame();
      expect(frame?.functionName).toBe('func');
    });

    it('should handle nested function calls', () => {
      context.pushCallFrame('func1', 0, 0);
      context.pushCallFrame('func2', 10, 5);
      context.pushCallFrame('func3', 20, 10);

      expect(context.getCallStackDepth()).toBe(3);

      context.popCallFrame();
      expect(context.getCallStackDepth()).toBe(2);
      expect(context.getCurrentCallFrame()?.functionName).toBe('func2');
    });

    it('should throw on pop from empty call stack', () => {
      expect(() => context.popCallFrame()).toThrow();
    });

    it('should throw on call stack overflow', () => {
      // Push many frames to exceed max depth
      for (let i = 0; i < 256; i++) {
        context.pushCallFrame(`func${i}`, 0, 0);
      }

      expect(() => context.pushCallFrame('overflow', 0, 0)).toThrow();
    });
  });

  describe('Function Definitions', () => {
    it('should define and retrieve functions', () => {
      const instructions: Instruction[] = [{ opcode: OpCode.SET, args: ['x', 1] }];
      context.defineFunction('func1', instructions);

      const retrieved = context.getFunction('func1');
      expect(retrieved).toEqual(instructions);
    });

    it('should check if function is defined', () => {
      context.defineFunction('func1', []);
      expect(context.isFunctionDefined('func1')).toBe(true);
      expect(context.isFunctionDefined('func2')).toBe(false);
    });

    it('should handle multiple function definitions', () => {
      context.defineFunction('func1', [{ opcode: OpCode.NOP, args: [] }]);
      context.defineFunction('func2', [{ opcode: OpCode.NOP, args: [] }]);
      context.defineFunction('func3', [{ opcode: OpCode.NOP, args: [] }]);

      expect(context.isFunctionDefined('func1')).toBe(true);
      expect(context.isFunctionDefined('func2')).toBe(true);
      expect(context.isFunctionDefined('func3')).toBe(true);
    });

    it('should return null for undefined function', () => {
      expect(context.getFunction('undefined')).toBeNull();
    });

    it('should overwrite function definitions', () => {
      const instr1: Instruction[] = [{ opcode: OpCode.SET, args: ['x', 1] }];
      const instr2: Instruction[] = [{ opcode: OpCode.SET, args: ['x', 2] }];

      context.defineFunction('func', instr1);
      expect(context.getFunction('func')).toEqual(instr1);

      context.defineFunction('func', instr2);
      expect(context.getFunction('func')).toEqual(instr2);
    });
  });

  describe('Trace Hooks', () => {
    it('should add and emit trace events', () => {
      const events: string[] = [];
      context.addTraceHook((event, _data) => {
        events.push(event);
      });

      context.emitTrace('instruction', { opcode: 'SET' });
      context.emitTrace('error', { message: 'test' });

      expect(events).toContain('instruction');
      expect(events).toContain('error');
    });

    it('should handle multiple trace hooks', () => {
      const events1: string[] = [];
      const events2: string[] = [];

      context.addTraceHook((event) => {
        events1.push(event);
      });
      context.addTraceHook((event) => {
        events2.push(event);
      });

      context.emitTrace('instruction', {});

      expect(events1).toContain('instruction');
      expect(events2).toContain('instruction');
    });

    it('should remove trace hooks', () => {
      const events: string[] = [];
      const hook: TraceHook = (event) => {
        events.push(event);
      };

      context.addTraceHook(hook);
      context.emitTrace('instruction', {});
      expect(events).toHaveLength(1);

      context.removeTraceHook(hook);
      context.emitTrace('instruction', {});
      expect(events).toHaveLength(1);
    });

    it('should suppress errors in trace hooks', () => {
      context.addTraceHook(() => {
        throw new Error('Hook error');
      });

      // Should not throw
      expect(() => context.emitTrace('instruction', {})).not.toThrow();
    });

    it('should pass event data to trace hooks', () => {
      let capturedData: Record<string, unknown> = {};
      context.addTraceHook((_event, data) => {
        capturedData = data;
      });

      const testData = { test: 'value', num: 42 };
      context.emitTrace('instruction', testData);

      expect(capturedData).toEqual(testData);
    });
  });

  describe('Running State', () => {
    it('should track running state', () => {
      expect(context.isContextRunning()).toBe(false);

      context.setRunning(true);
      expect(context.isContextRunning()).toBe(true);

      context.setRunning(false);
      expect(context.isContextRunning()).toBe(false);
    });
  });

  describe('Context Reset', () => {
    it('should reset context state', () => {
      const instructions: Instruction[] = [{ opcode: OpCode.SET, args: ['x', 1] }];
      context.setProgram(instructions);
      context.setProgramCounter(1);
      context.setRunning(true);
      context.defineFunction('func', []);

      context.reset();

      expect(context.getProgramCounter()).toBe(0);
      expect(context.isContextRunning()).toBe(false);
      expect(context.getCurrentInstruction()).toBeNull();
    });
  });

  describe('Context Snapshot', () => {
    it('should provide context state snapshot', () => {
      const instructions: Instruction[] = [{ opcode: OpCode.SET, args: ['x', 1] }];
      context.setProgram(instructions);
      context.setRunning(true);
      context.defineFunction('func1', []);
      context.pushCallFrame('main', 0, 0);

      const snapshot = context.getSnapshot();

      expect(snapshot.programCounter).toBe(0);
      expect(snapshot.isRunning).toBe(true);
      expect(snapshot.callStackDepth).toBe(1);
      expect(snapshot.definedFunctions).toContain('func1');
      expect(snapshot.programLength).toBe(1);
    });
  });
});
