# NullVM - Virtual Machine for Super-Bit Programs

A TypeScript implementation of a virtual machine that executes super-bit programs with support for instruction decoding, execution contexts, memory management, and binary frame emission.

## Features

- **Instruction Set Support**: SET, ADD, SHOW, IF, REPEAT, DEFINE, CALL, RETURN, JMP, NOP
- **Memory Model**: Registers, stack, and heap abstractions
- **Control Flow**: Conditional execution (IF) and loops (REPEAT)
- **Function Definitions**: Define and call custom functions with proper call stack management
- **Binary Bridge**: Emit binary frames for output and register state tracking
- **Error Handling**: Structured error propagation with detailed error types
- **Tracing Hooks**: Hook into execution events for debugging and monitoring
- **Fuzzy Bit Evaluation**: Stubs for probabilistic evaluation support

## Project Structure

```
src/
├── null_system/
│   └── vm/
│       ├── null_vm.ts              # Main NullVM class
│       ├── instructions.ts          # Instruction definitions and opcodes
│       ├── decoder.ts               # Super-bit program decoder
│       ├── memory.ts                # Memory model (registers, stack, heap)
│       ├── execution_context.ts     # Execution state and call stack management
│       ├── binary_bridge.ts         # Binary frame emission
│       ├── fuzzy_bits.ts            # Fuzzy/probabilistic evaluation stubs
│       ├── errors.ts                # Error types and handling
│       ├── index.ts                 # Module exports
│       └── __tests__/               # Unit tests for VM components
├── examples/
│   ├── sample_program.ts            # Sample super-bit programs
│   └── __tests__/                   # End-to-end tests
└── index.ts                         # Main package exports
```

## Installation

```bash
npm install
```

## Usage

### Running the Sample Program

```bash
npx ts-node src/examples/sample_program.ts
```

### Using the NullVM in Your Code

```typescript
import { NullVM, OpCode } from './null_system/vm';

// Create a VM instance
const vm = new NullVM();

// Define a program
const program = [
  { opcode: OpCode.SET, args: ['x', 10] },
  { opcode: OpCode.ADD, args: ['x', 5] },
  { opcode: OpCode.SHOW, args: ['x'] },
];

// Execute the program
vm.execute(program);

// Access results
const state = vm.getState();
console.log('Result:', state.memory.registers.x); // 15
```

## Instruction Reference

### SET - Set Register Value
```javascript
{ opcode: 'SET', args: ['register_name', value] }
```

### ADD - Add to Register
```javascript
{ opcode: 'ADD', args: ['register_name', value_or_register] }
```

### SHOW - Output Register Value
```javascript
{ opcode: 'SHOW', args: ['register_name'] }
```

### IF - Conditional Execution
```javascript
{
  opcode: 'IF',
  args: ['condition_register', operator, instructions_array]
}
// Operators: '>', '<', '==', '!=', '>=', '<='
```

### REPEAT - Loop Execution
```javascript
{
  opcode: 'REPEAT',
  args: ['count_register', instructions_array]
}
```

### DEFINE - Define Function
```javascript
{
  opcode: 'DEFINE',
  args: ['function_name', instructions_array]
}
```

### CALL - Call Function
```javascript
{ opcode: 'CALL', args: ['function_name'] }
```

### RETURN - Return from Function
```javascript
{ opcode: 'RETURN', args: [] }
```

### NOP - No Operation
```javascript
{ opcode: 'NOP', args: [] }
```

## API Documentation

### NullVM

Main virtual machine class for executing super-bit programs.

```typescript
class NullVM {
  constructor(config?: NullVMConfig)
  execute(program: SuperBitProgram | unknown[]): void
  getMemory(): Memory
  getContext(): ExecutionContext
  getBinaryBridge(): BinaryBridge
  getFuzzyBitEvaluator(): FuzzyBitEvaluator
  reset(): void
  getExecutionCycle(): number
  getState(): object
}
```

### Memory

Manages registers, stack, and heap.

```typescript
class Memory {
  setRegister(name: string, value: number): void
  getRegister(name: string): number
  pushStack(value: number): void
  popStack(): number
  peekStack(): number
  writeHeap(offset: number, value: number): void
  readHeap(offset: number): number
  allocateHeap(size: number): number
  reset(): void
  getSnapshot(): object
}
```

### ExecutionContext

Manages program execution state, call stack, and function definitions.

```typescript
class ExecutionContext {
  setProgram(instructions: Instruction[]): void
  getCurrentInstruction(): Instruction | null
  advanceProgramCounter(): void
  setProgramCounter(address: number): void
  pushCallFrame(functionName: string, returnAddress: number, stackPointer: number): void
  popCallFrame(): StackFrame
  defineFunction(name: string, instructions: Instruction[]): void
  getFunction(name: string): Instruction[] | null
  addTraceHook(hook: TraceHook): void
  emitTrace(event: string, data: object): void
  reset(): void
  getSnapshot(): object
}
```

### BinaryBridge

Emits binary frames for output and register state tracking.

```typescript
class BinaryBridge {
  emitFrame(frameType: string, data: Buffer): void
  emitOutput(label: string, value: number): void
  emitRegisterState(name: string, value: number): void
  emitControlFlow(event: string, data?: object): void
  getFrames(): BinaryFrame[]
  getFrameCount(): number
  clearFrames(): void
}
```

## Development

### Run Tests
```bash
npm test
```

### Build TypeScript
```bash
npm run build
```

### Run Linter
```bash
npm run lint
```

### Format Code
```bash
npm run format
```

## Test Coverage

The project includes comprehensive test suites:

- **NullVM Tests** (142 tests):
  - Basic operations (SET, ADD, SHOW)
  - Control flow (IF, REPEAT)
  - Function definitions and calls
  - Complex scenarios with nested control structures
  - Error handling
  - State management and reset
  - Fuzzy bit evaluation

- **Component Tests**:
  - Memory: Register, stack, and heap operations
  - ExecutionContext: Program counter, call stack, function definitions
  - Decoder: Program parsing and validation
  - BinaryBridge: Frame emission and management
  - Sample Programs: End-to-end execution tests

## Example Programs

### Simple Arithmetic
```typescript
const program = [
  { opcode: OpCode.SET, args: ['a', 10] },
  { opcode: OpCode.SET, args: ['b', 20] },
  { opcode: OpCode.ADD, args: ['a', 'b'] },
  { opcode: OpCode.SHOW, args: ['a'] },
];
```

### Conditional Logic
```typescript
const program = [
  { opcode: OpCode.SET, args: ['x', 5] },
  {
    opcode: OpCode.IF,
    args: ['x', '>', [
      { opcode: OpCode.SET, args: ['result', 100] },
    ]],
  },
  { opcode: OpCode.SHOW, args: ['result'] },
];
```

### Loops
```typescript
const program = [
  { opcode: OpCode.SET, args: ['counter', 0] },
  { opcode: OpCode.SET, args: ['iterations', 5] },
  {
    opcode: OpCode.REPEAT,
    args: ['iterations', [
      { opcode: OpCode.ADD, args: ['counter', 1] },
    ]],
  },
  { opcode: OpCode.SHOW, args: ['counter'] },
];
```

### Function Definition and Call
```typescript
const program = [
  {
    opcode: OpCode.DEFINE,
    args: ['increment', [
      { opcode: OpCode.ADD, args: ['x', 1] },
    ]],
  },
  { opcode: OpCode.SET, args: ['x', 0] },
  { opcode: OpCode.CALL, args: ['increment'] },
  { opcode: OpCode.CALL, args: ['increment'] },
  { opcode: OpCode.SHOW, args: ['x'] },
];
```

## Error Handling

The VM provides detailed error information with error types:

- `INVALID_INSTRUCTION`: Invalid opcode or instruction format
- `INVALID_REGISTER`: Invalid register name or value type
- `STACK_UNDERFLOW`: Attempting to pop from empty stack
- `STACK_OVERFLOW`: Stack limit exceeded
- `HEAP_OUT_OF_BOUNDS`: Heap memory access out of bounds
- `UNDEFINED_FUNCTION`: Attempting to call undefined function
- `INVALID_PROGRAM`: Program has invalid structure
- `EXECUTION_ERROR`: Runtime execution error

## Configuration

```typescript
interface NullVMConfig {
  maxCycles?: number;           // Max execution cycles (default: 10000)
  enableTracing?: boolean;       // Enable execution tracing (default: false)
  fuzzyBitConfig?: FuzzyBitConfig;
}

interface FuzzyBitConfig {
  probabilityThreshold?: number; // Probability threshold (default: 0.5)
  noiseLevel?: number;          // Noise level (default: 0)
}
```

## License

MIT
