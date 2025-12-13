/**
 * Memory model for NullVM - registers, stack, and heap
 */

import { createError, ErrorType } from './errors';

const STACK_SIZE = 1024;
const HEAP_SIZE = 4096;

export interface EncryptedData {
  ciphertext: Buffer;
  keyId: string;
  type: 'encrypted';
}

export interface StoredTensor {
  dimensions: number;
  bits: Uint8Array;
  metadata?: Record<string, unknown>;
}

export class Memory {
  private registers: Map<string, number> = new Map();
  private stack: number[] = [];
  private heap: Buffer;
  private stackPointer: number = 0;
  private heapPointer: number = 0;
  private encryptedValues: Map<string, EncryptedData> = new Map();
  private keys: Map<string, { publicKey: Buffer; privateKey?: Buffer }> = new Map();
  private tensors: Map<string, StoredTensor> = new Map();
  private graphs: Map<string, Record<string, unknown>> = new Map();

  constructor() {
    this.heap = Buffer.alloc(HEAP_SIZE, 0);
  }

  /**
   * Set a register value
   */
  setRegister(name: string, value: number): void {
    if (typeof value !== 'number') {
      throw createError(
        ErrorType.InvalidRegister,
        `Register value must be a number, got ${typeof value}`,
        { register: name, value }
      );
    }
    this.registers.set(name, value);
  }

  /**
   * Get a register value
   */
  getRegister(name: string): number {
    if (!this.registers.has(name)) {
      this.registers.set(name, 0);
    }
    return this.registers.get(name)!;
  }

  /**
   * Check if register exists
   */
  hasRegister(name: string): boolean {
    return this.registers.has(name);
  }

  /**
   * Get all registers
   */
  getAllRegisters(): Record<string, number> {
    return Object.fromEntries(this.registers);
  }

  /**
   * Push value onto stack
   */
  pushStack(value: number): void {
    if (this.stackPointer >= STACK_SIZE) {
      throw createError(ErrorType.StackOverflow, 'Stack overflow', {
        stackPointer: this.stackPointer,
        stackSize: STACK_SIZE,
      });
    }
    this.stack[this.stackPointer++] = value;
  }

  /**
   * Pop value from stack
   */
  popStack(): number {
    if (this.stackPointer <= 0) {
      throw createError(ErrorType.StackUnderflow, 'Stack underflow', {
        stackPointer: this.stackPointer,
      });
    }
    return this.stack[--this.stackPointer];
  }

  /**
   * Peek at top of stack without popping
   */
  peekStack(): number {
    if (this.stackPointer <= 0) {
      throw createError(ErrorType.StackUnderflow, 'Stack underflow', {
        stackPointer: this.stackPointer,
      });
    }
    return this.stack[this.stackPointer - 1];
  }

  /**
   * Get current stack pointer
   */
  getStackPointer(): number {
    return this.stackPointer;
  }

  /**
   * Set stack pointer (for function calls)
   */
  setStackPointer(value: number): void {
    if (value < 0 || value > STACK_SIZE) {
      throw createError(
        ErrorType.StackUnderflow,
        'Invalid stack pointer value',
        { value, stackSize: STACK_SIZE }
      );
    }
    this.stackPointer = value;
  }

  /**
   * Write to heap
   */
  writeHeap(offset: number, value: number): void {
    if (offset < 0 || offset >= HEAP_SIZE) {
      throw createError(ErrorType.HeapOutOfBounds, 'Heap write out of bounds', {
        offset,
        heapSize: HEAP_SIZE,
      });
    }
    this.heap.writeUInt32BE(value, offset);
  }

  /**
   * Read from heap
   */
  readHeap(offset: number): number {
    if (offset < 0 || offset >= HEAP_SIZE) {
      throw createError(ErrorType.HeapOutOfBounds, 'Heap read out of bounds', {
        offset,
        heapSize: HEAP_SIZE,
      });
    }
    return this.heap.readUInt32BE(offset);
  }

  /**
   * Allocate heap space
   */
  allocateHeap(size: number): number {
    const address = this.heapPointer;
    if (this.heapPointer + size > HEAP_SIZE) {
      throw createError(
        ErrorType.HeapOutOfBounds,
        'Heap allocation failed: out of memory',
        {
          requested: size,
          available: HEAP_SIZE - this.heapPointer,
        }
      );
    }
    this.heapPointer += size;
    return address;
  }

  /**
   * Store a key pair
   */
  storeKey(keyId: string, publicKey: Buffer, privateKey?: Buffer): void {
    this.keys.set(keyId, { publicKey, privateKey });
  }

  /**
   * Get a stored key
   */
  getKey(keyId: string): { publicKey: Buffer; privateKey?: Buffer } | undefined {
    return this.keys.get(keyId);
  }

  /**
   * Store an encrypted value
   */
  storeEncryptedValue(valueId: string, ciphertext: Buffer, keyId: string): void {
    this.encryptedValues.set(valueId, { ciphertext, keyId, type: 'encrypted' });
  }

  /**
   * Get an encrypted value
   */
  getEncryptedValue(valueId: string): EncryptedData | undefined {
    return this.encryptedValues.get(valueId);
  }

  /**
   * Check if a value is encrypted
   */
  isEncrypted(valueId: string): boolean {
    return this.encryptedValues.has(valueId);
  }

  /**
   * Get all encrypted values
   */
  getAllEncryptedValues(): Record<string, EncryptedData> {
    return Object.fromEntries(this.encryptedValues);
  }

  /**
   * Store a tensor
   */
  storeTensor(id: string, tensor: StoredTensor): void {
    this.tensors.set(id, tensor);
  }

  /**
   * Get a tensor
   */
  getTensor(id: string): StoredTensor | undefined {
    return this.tensors.get(id);
  }

  /**
   * Store a graph
   */
  storeGraph(id: string, graph: Record<string, unknown>): void {
    this.graphs.set(id, graph);
  }

  /**
   * Get a graph
   */
  getGraph(id: string): Record<string, unknown> | undefined {
    return this.graphs.get(id);
  }

  /**
   * Reset all memory
   */
  reset(): void {
    this.registers.clear();
    this.stack = [];
    this.stackPointer = 0;
    this.heap.fill(0);
    this.heapPointer = 0;
    this.encryptedValues.clear();
    this.keys.clear();
    this.tensors.clear();
    this.graphs.clear();
  }

  /**
   * Get memory state snapshot
   */
  getSnapshot() {
    return {
      registers: Object.fromEntries(this.registers),
      stackPointer: this.stackPointer,
      heapPointer: this.heapPointer,
      stackSize: STACK_SIZE,
      heapSize: HEAP_SIZE,
      encryptedValuesCount: this.encryptedValues.size,
      keysCount: this.keys.size,
      tensorCount: this.tensors.size,
      graphCount: this.graphs.size,
    };
  }
}

