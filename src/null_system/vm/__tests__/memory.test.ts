import { Memory } from '../memory';

describe('Memory', () => {
  let memory: Memory;

  beforeEach(() => {
    memory = new Memory();
  });

  describe('Registers', () => {
    it('should set and get register values', () => {
      memory.setRegister('x', 42);
      expect(memory.getRegister('x')).toBe(42);
    });

    it('should initialize uninitialized registers to 0', () => {
      expect(memory.getRegister('unset')).toBe(0);
    });

    it('should handle multiple registers independently', () => {
      memory.setRegister('a', 1);
      memory.setRegister('b', 2);
      memory.setRegister('c', 3);

      expect(memory.getRegister('a')).toBe(1);
      expect(memory.getRegister('b')).toBe(2);
      expect(memory.getRegister('c')).toBe(3);
    });

    it('should check register existence', () => {
      memory.setRegister('x', 10);
      expect(memory.hasRegister('x')).toBe(true);
      expect(memory.hasRegister('y')).toBe(false);
    });

    it('should return all registers', () => {
      memory.setRegister('a', 1);
      memory.setRegister('b', 2);

      const regs = memory.getAllRegisters();
      expect(regs.a).toBe(1);
      expect(regs.b).toBe(2);
    });

    it('should reject non-numeric values', () => {
      expect(() => memory.setRegister('x', 'not a number' as unknown as number)).toThrow();
    });
  });

  describe('Stack', () => {
    it('should push and pop values', () => {
      memory.pushStack(42);
      expect(memory.popStack()).toBe(42);
    });

    it('should handle multiple stack operations', () => {
      memory.pushStack(1);
      memory.pushStack(2);
      memory.pushStack(3);

      expect(memory.popStack()).toBe(3);
      expect(memory.popStack()).toBe(2);
      expect(memory.popStack()).toBe(1);
    });

    it('should peek without popping', () => {
      memory.pushStack(42);
      expect(memory.peekStack()).toBe(42);
      expect(memory.peekStack()).toBe(42);
      expect(memory.popStack()).toBe(42);
    });

    it('should throw on underflow when popping', () => {
      expect(() => memory.popStack()).toThrow();
    });

    it('should throw on underflow when peeking', () => {
      expect(() => memory.peekStack()).toThrow();
    });

    it('should track stack pointer', () => {
      expect(memory.getStackPointer()).toBe(0);
      memory.pushStack(1);
      expect(memory.getStackPointer()).toBe(1);
      memory.pushStack(2);
      expect(memory.getStackPointer()).toBe(2);
      memory.popStack();
      expect(memory.getStackPointer()).toBe(1);
    });

    it('should set stack pointer', () => {
      memory.pushStack(1);
      memory.pushStack(2);
      memory.setStackPointer(1);
      expect(memory.getStackPointer()).toBe(1);
    });

    it('should throw on invalid stack pointer', () => {
      expect(() => memory.setStackPointer(-1)).toThrow();
    });
  });

  describe('Heap', () => {
    it('should write and read heap values', () => {
      memory.writeHeap(0, 42);
      expect(memory.readHeap(0)).toBe(42);
    });

    it('should handle multiple heap locations', () => {
      memory.writeHeap(0, 100);
      memory.writeHeap(4, 200);
      memory.writeHeap(8, 300);

      expect(memory.readHeap(0)).toBe(100);
      expect(memory.readHeap(4)).toBe(200);
      expect(memory.readHeap(8)).toBe(300);
    });

    it('should allocate heap space', () => {
      const addr1 = memory.allocateHeap(100);
      const addr2 = memory.allocateHeap(100);

      expect(addr1).toBe(0);
      expect(addr2).toBeGreaterThan(addr1);
    });

    it('should throw on heap out of bounds read', () => {
      expect(() => memory.readHeap(99999)).toThrow();
    });

    it('should throw on heap out of bounds write', () => {
      expect(() => memory.writeHeap(99999, 42)).toThrow();
    });

    it('should throw on heap allocation overflow', () => {
      expect(() => memory.allocateHeap(99999)).toThrow();
    });
  });

  describe('Memory Reset', () => {
    it('should reset all memory', () => {
      memory.setRegister('x', 42);
      memory.pushStack(100);
      memory.writeHeap(0, 50);

      memory.reset();

      expect(memory.getRegister('x')).toBe(0);
      expect(memory.getStackPointer()).toBe(0);
      expect(memory.readHeap(0)).toBe(0);
    });
  });

  describe('Memory Snapshot', () => {
    it('should provide memory state snapshot', () => {
      memory.setRegister('a', 1);
      memory.setRegister('b', 2);
      memory.pushStack(10);
      memory.pushStack(20);

      const snapshot = memory.getSnapshot();

      expect(snapshot.registers).toEqual({ a: 1, b: 2 });
      expect(snapshot.stackPointer).toBe(2);
      expect(snapshot.heapPointer).toBe(0);
    });
  });
});
