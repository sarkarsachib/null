# NullVM - Virtual Machine for Super-Bit Programs

A TypeScript implementation of a virtual machine that executes super-bit programs with support for instruction decoding, execution contexts, memory management, and binary frame emission.

## Features

- **Instruction Set Support**: SET, ADD, SHOW, IF, REPEAT, DEFINE, CALL, RETURN, JMP, NOP, and security opcodes
- **Memory Model**: Registers, stack, and heap abstractions with encrypted value storage
- **Control Flow**: Conditional execution (IF) and loops (REPEAT)
- **Function Definitions**: Define and call custom functions with proper call stack management
- **Binary Bridge**: Emit binary frames for output, register state, and security metadata
- **Error Handling**: Structured error propagation with detailed error types
- **Tracing Hooks**: Hook into execution events for debugging and monitoring
- **Fuzzy Bit Evaluation**: Stubs for probabilistic evaluation support
- **Cryptographic Primitives**: Homomorphic encryption, secure channels, zero-knowledge proofs, and secure multi-party computation (SMPC)
- **Hybrid Executor**: Distributed execution with work-stealing load balancing, async execution hooks, and fault tolerance
- **Fault Tolerance**: State snapshots, replay logs, and automatic recovery
- **Work-Stealing Scheduler**: Fair task distribution across multiple workers with backpressure handling

## Project Structure

```
src/
├── null_system/
│   ├── vm/
│   │   ├── null_vm.ts                      # Main NullVM class
│   │   ├── instructions.ts                 # Instruction definitions and opcodes
│   │   ├── decoder.ts                      # Super-bit program decoder
│   │   ├── memory.ts                       # Memory model (registers, stack, heap)
│   │   ├── execution_context.ts            # Execution state and call stack management
│   │   ├── binary_bridge.ts                # Binary frame emission
│   │   ├── fuzzy_bits.ts                   # Fuzzy/probabilistic evaluation stubs
│   │   ├── errors.ts                       # Error types and handling
│   │   ├── fault_tolerance.ts              # Checkpointing and replay logs
│   │   ├── scheduler/
│   │   │   ├── work_stealing_scheduler.ts  # Work-stealing load balancer
│   │   │   └── index.ts
│   │   ├── distributed/
│   │   │   ├── distributed_executor.ts     # Distributed execution orchestrator
│   │   │   ├── nullvm.proto                # gRPC service definitions
│   │   │   └── index.ts
│   │   ├── hybrid_runtime/                 # Hybrid execution runtime
│   │   │   ├── hybrid_execution_manager.ts # Multi-VM orchestration
│   │   │   ├── work_scheduler.ts           # Work queue management
│   │   │   ├── superbit_message_bus.ts     # Message passing with super-bit encoding
│   │   │   ├── transport_adapter.ts        # Transport layer abstraction
│   │   │   ├── worker_adapter.ts           # Worker thread management
│   │   │   └── index.ts
│   │   ├── __tests__/                      # Unit tests for VM components
│   │   │   ├── fault_tolerance.test.ts
│   │   │   ├── work_stealing_scheduler.test.ts
│   │   │   ├── distributed_executor.test.ts
│   │   │   ├── hybrid_executor.test.ts
│   │   │   └── ...
│   │   └── index.ts                        # Module exports
│   ├── security/
│   │   ├── homomorphic_engine.ts           # Homomorphic encryption
│   │   ├── secure_channel.ts               # Key exchange & authenticated transport
│   │   ├── zkp.ts                          # Zero-knowledge proofs
│   │   ├── smpc_orchestrator.ts            # Secret sharing & SMPC
│   │   ├── index.ts
│   │   └── __tests__/                      # Security module tests
│   ├── compiler/
│   │   ├── hybrid_runner.py                # Python bridge for distributed execution
│   │   └── ...
│   └── ...
├── bin/
│   └── cli.ts                              # CLI entry point (nullvm command)
├── examples/
│   ├── sample_program.ts                   # Sample super-bit programs
│   ├── distributed_execution.ts            # Distributed workload example
│   └── ...
├── docs/
│   ├── hybrid_execution.md                 # Hybrid executor guide
│   └── ...
└── index.ts                                # Main package exports
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

### Using the Hybrid Executor for Distributed Execution

```typescript
import { DistributedExecutor } from './null_system/vm/distributed';
import { OpCode } from './null_system/vm';

// Create distributed executor
const executor = new DistributedExecutor({
  nodeId: 'node-1',
  listenAddr: 'localhost',
  listenPort: 50051,
  maxWorkers: 100,
  enableCheckpointing: true,
  checkpointInterval: 5000,
});

await executor.initialize();

// Register VMs as workers
const vm = new NullVM({ vmId: 'vm-1' });
executor.registerVM('vm-1', vm);

// Execute program on distributed executor
const program = [
  { opcode: OpCode.SET, args: ['x', '42'] },
  { opcode: OpCode.ADD, args: ['x', '8'] },
];

const result = await executor.executeOnVM('vm-1', program);
console.log('Execution result:', result);
// { status: 'success', registers: { x: 50 }, executionCycles: 2, duration: 1 }
```

### Using Async Execution with Hooks

```typescript
// Register execution hook for monitoring
vm.registerExecutionHook(async (cycle, instruction, context) => {
  console.log(`Cycle ${cycle}: ${instruction.opcode}`);
  console.log(`Registers:`, context.registers);
});

// Execute asynchronously with hooks invoked
await vm.executeAsync(program);
```

### Using Fault Tolerance

```typescript
import { StateSnapshot, FaultToleranceManager } from './null_system/vm';

const manager = new FaultToleranceManager();

// Execute and create checkpoint
vm.execute(program);
const snapshot = vm.createSnapshot();
const checkpointId = manager.createCheckpoint('vm-1', snapshot, []);

// Later: recover from checkpoint
const checkpoint = manager.getCheckpoint(checkpointId);
vm.restoreSnapshot(checkpoint.vmSnapshot);
```

### Using the CLI

```bash
# Run a program with tracing
npm run build
node dist/bin/cli.js run --program "SET x 10; ADD x 5; SHOW x" --tracing

# Run a benchmark
node dist/bin/cli.js benchmark --workers 100 --taskCount 10000

# Start a distributed executor server
node dist/bin/cli.js server --port 50051 --workers 100 --nodeId node-1
```

## Hybrid Executor Guide

See [docs/hybrid_execution.md](docs/hybrid_execution.md) for comprehensive hybrid executor documentation including:

- Architecture and components
- Work-stealing scheduler details
- Fault tolerance and recovery
- Performance characteristics
- Configuration options
- Monitoring and metrics
- Deployment guide

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

### SECURE_ENC - Encrypt Register Value
```javascript
{ opcode: 'SECURE_ENC', args: ['register_name', 'key_id'] }
// Encrypts a register value using homomorphic encryption
```

### SECURE_DEC - Decrypt Encrypted Value
```javascript
{ opcode: 'SECURE_DEC', args: ['register_name', 'key_id'] }
// Decrypts a previously encrypted register value
```

### SECURE_EVAL - Evaluate on Encrypted Values
```javascript
{ opcode: 'SECURE_EVAL', args: ['operation', 'source_register', 'dest_register'] }
// Supported operations: 'add', 'mul_scalar'
// Performs homomorphic operations on encrypted data
```

### ZK_PROVE - Generate Zero-Knowledge Proof
```javascript
{ opcode: 'ZK_PROVE', args: ['trace_id'] }
// Records execution trace and generates ZK proof without revealing secrets
```

### ZK_VERIFY - Verify Zero-Knowledge Proof
```javascript
{ opcode: 'ZK_VERIFY', args: ['proof_id', 'digest_id'] }
// Verifies a previously generated ZK proof
```

### SMPC_SHARE - Share Secret for Multi-Party Computation
```javascript
{ opcode: 'SMPC_SHARE', args: ['secret_id', threshold] }
// Splits a secret into shares for secure multi-party computation
```

### SMPC_COMBINE - Combine Shares to Reconstruct Secret
```javascript
{ opcode: 'SMPC_COMBINE', args: ['secret_id', ['share_id_1', 'share_id_2', ...]] }
// Reconstructs secret from sufficient shares (must meet or exceed threshold)
```

### Q_ALLOC - Allocate Qubit
```javascript
{ opcode: 'Q_ALLOC', args: ['target_reg'] }
// Allocates a new qubit and stores its index in the target register
```

### Q_SUPERPOSE - Superpose Qubit
```javascript
{ opcode: 'Q_SUPERPOSE', args: ['qubit_reg'] }
// Applies a Hadamard gate to the qubit
```

### Q_ENTANGLE - Entangle Qubits
```javascript
{ opcode: 'Q_ENTANGLE', args: ['control_reg', 'target_reg'] }
// Entangles two qubits using a CNOT operation
```

### Q_APPLY - Apply Quantum Gate
```javascript
{ opcode: 'Q_APPLY', args: ['gate_name', ['qubit_reg']] }
// Applies a specified gate (e.g. 'X', 'Y', 'Z') to the qubit(s)
```

### Q_MEASURE - Measure Qubit
```javascript
{ opcode: 'Q_MEASURE', args: ['qubit_reg', 'dest_reg'] }
// Measures a qubit and stores the result (0 or 1) in the destination register
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
  getHomomorphicEngine(): HomomorphicEngine
  getSecureChannel(): SecureChannel
  getZKProofSystem(): ZKProofSystem
  getSMPCOrchestrator(): SMPCOrchestrator
  reset(): void
  getExecutionCycle(): number
  getState(): object
}
```

### Memory

Manages registers, stack, heap, encrypted values, and cryptographic keys.

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
  storeKey(keyId: string, publicKey: Buffer, privateKey?: Buffer): void
  getKey(keyId: string): { publicKey: Buffer; privateKey?: Buffer } | undefined
  storeEncryptedValue(valueId: string, ciphertext: Buffer, keyId: string): void
  getEncryptedValue(valueId: string): EncryptedData | undefined
  isEncrypted(valueId: string): boolean
  getAllEncryptedValues(): Record<string, EncryptedData>
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

Emits binary frames for output, register state tracking, and security metadata.

```typescript
class BinaryBridge {
  emitFrame(frameType: string, data: Buffer): void
  emitOutput(label: string, value: number): void
  emitRegisterState(name: string, value: number): void
  emitControlFlow(event: string, data?: object): void
  emitProofTranscript(proofId: string, transcript: string): void
  emitChannelMetadata(channelId: string, metadata: Record<string, unknown>): void
  emitKeyExchange(party1: string, party2: string, success: boolean): void
  getFrames(): BinaryFrame[]
  getFrameCount(): number
  clearFrames(): void
}
```

## Security Modules

The `src/null_system/security/` directory contains cryptographic primitives for privacy-preserving computation:

### HomomorphicEngine

Supports encrypted operations on tensor data using Paillier-style encryption.

```typescript
class HomomorphicEngine {
  generateKeyPair(): EncryptionKeyPair
  encrypt(value: number, publicKey: Buffer): EncryptedValue
  decrypt(encrypted: EncryptedValue, privateKey: Buffer): number
  encryptedAdd(encrypted1: EncryptedValue, encrypted2: EncryptedValue): EncryptedValue
  encryptedScalarMultiply(encrypted: EncryptedValue, scalar: number): EncryptedValue
  encryptTensor(tensor: TensorData, publicKey: Buffer): EncryptedValue
  decryptTensor(encrypted: EncryptedValue, privateKey: Buffer): TensorData
  verifyCiphertext(encrypted: EncryptedValue): boolean
}
```

### SecureChannel

Implements key exchange and authenticated message transport using NaCl (libsodium).

```typescript
class SecureChannel {
  constructor(config: ChannelConfig)
  initiateKeyExchange(): KeyExchangeMessage
  completeKeyExchange(remotePublicKey: Uint8Array): void
  sendMessage(plaintext: Buffer): AuthenticatedMessage
  receiveMessage(message: AuthenticatedMessage): Buffer
  getPublicKey(): Buffer
  getState(): object
  reset(): void
}
```

### ZKProofSystem

Provides zero-knowledge proof generation and verification using Fiat-Shamir heuristic.

```typescript
class ZKProofSystem {
  recordTrace(traceId: string, statements: string[]): ExecutionTrace
  proveExecution(traceId: string): ZKProof
  verifyProof(proof: ZKProof): boolean
  verifyAgainstDigest(proof: ZKProof, expectedDigest: Buffer): boolean
  getProofTranscript(proofId: string): string
  clear(): void
}
```

### SMPCOrchestrator

Implements secret sharing and multi-party computation coordination (Shamir secret sharing).

```typescript
class SMPCOrchestrator {
  constructor(config: SMPCConfig)
  shareSecret(secretId: string, secret: Buffer): Map<string, Buffer>
  submitShare(secretId: string, share: Buffer): void
  combineShares(secretId: string, shareIds: string[]): Buffer
  computeSum(shareIds: string[]): number
  computeProduct(shareIds: string[]): number
  getShareInfo(shareId: string): SecretShare | undefined
  getSecretShares(secretId: string): Map<string, Buffer> | undefined
  isReconstructed(secretId: string): boolean
  getConfig(): SMPCConfig
  getState(): object
  reset(): void
}
```

## Security Threat Model & Configuration

### Supported Operations

- **Encryption**: Homomorphic encryption for secure computation on encrypted data
- **Key Exchange**: NaCl-based (Curve25519) key establishment
- **Zero-Knowledge Proofs**: Fiat-Shamir non-interactive proofs for execution verification
- **Secret Sharing**: Shamir secret sharing for threshold-based security

### Key Sizes

- **Homomorphic Encryption**: 1024-bit, 2048-bit, 4096-bit (default: 2048)
- **ECDH Key Exchange**: Curve25519 (256-bit equivalent security)
- **NaCl Box**: 32-byte public/private keys

### Dependencies

- **tweetnacl** (^1.0.3): For secure key exchange and authenticated message transport

### Development Mode

For development and testing, security features can be disabled or use reduced key sizes:

```typescript
const engine = new HomomorphicEngine(512); // Smaller keys for testing
const channel = new SecureChannel({ algorithm: 'nacl-box', enableLogging: true });
```

### Production Recommendations

1. Use 2048-bit or larger homomorphic keys in production
2. Implement proper key management and storage
3. Use secure random number generation
4. Validate all ciphertexts and proofs
5. Implement proper error handling for cryptographic failures
6. Monitor and log security-relevant events

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

### Secure Computation - Homomorphic Encryption
```typescript
const program = [
  { opcode: OpCode.SET, args: ['secret_a', 10] },
  { opcode: OpCode.SET, args: ['secret_b', 20] },
  // Encrypt sensitive values
  { opcode: OpCode.SECURE_ENC, args: ['secret_a', 'key1'] },
  { opcode: OpCode.SECURE_ENC, args: ['secret_b', 'key1'] },
  // Perform computation on encrypted values
  { opcode: OpCode.SECURE_EVAL, args: ['add', 'secret_a', 'secret_b'] },
  // Generate proof without revealing secrets
  { opcode: OpCode.ZK_PROVE, args: ['computation'] },
  // Decrypt result (only with private key)
  { opcode: OpCode.SECURE_DEC, args: ['secret_a', 'key1'] },
  { opcode: OpCode.SHOW, args: ['secret_a'] },
];
```

### Multi-Party Secret Sharing
```typescript
const program = [
  { opcode: OpCode.SET, args: ['secret', 42] },
  // Share secret among 3 parties (need 2 to reconstruct)
  { opcode: OpCode.SMPC_SHARE, args: ['secret_shares', 2] },
  // Later: reconstruct from shares
  {
    opcode: OpCode.SMPC_COMBINE,
    args: ['secret_shares', [
      'secret_shares_party_0',
      'secret_shares_party_1',
    ]],
  },
];
```

### Zero-Knowledge Proof of Execution
```typescript
const program = [
  { opcode: OpCode.SET, args: ['x', 5] },
  { opcode: OpCode.ADD, args: ['x', 10] },
  // Prove execution without revealing x's value
  { opcode: OpCode.ZK_PROVE, args: ['trace_1'] },
  // Verify the proof
  { opcode: OpCode.ZK_VERIFY, args: ['trace_1', 'digest_1'] },
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
- `ENCRYPTION_ERROR`: Homomorphic encryption operation failed
- `DECRYPTION_ERROR`: Decryption or key error
- `KEY_ERROR`: Missing or invalid cryptographic key
- `PROOF_ERROR`: Zero-knowledge proof generation or verification failed
- `SMPC_ERROR`: Secret sharing or multi-party computation error
- `CHANNEL_ERROR`: Secure channel communication error

## Configuration

```typescript
interface NullVMConfig {
  maxCycles?: number;           // Max execution cycles (default: 10000)
  enableTracing?: boolean;       // Enable execution tracing (default: false)
  fuzzyBitConfig?: FuzzyBitConfig;
  vmId?: string;                // Unique VM identifier
  hybridRuntime?: {             // Hybrid runtime configuration
    enabled: boolean;
    manager?: HybridExecutionManager;
    capabilities?: Partial<VMCapabilities>;
    config?: HybridExecutionConfig;
  };
}

interface FuzzyBitConfig {
  probabilityThreshold?: number; // Probability threshold (default: 0.5)
  noiseLevel?: number;          // Noise level (default: 0)
}
```

## Hybrid Runtime (Distributed Execution)

The hybrid runtime layer enables multiple VMs to work together cooperatively. See [docs/hybrid_runtime.md](docs/hybrid_runtime.md) for full documentation.

### Quick Start

```typescript
import { NullVM, HybridExecutionManager, WorkerThreadAdapter } from './vm';

// Create manager
const adapter = new WorkerThreadAdapter();
const manager = new HybridExecutionManager(adapter, {
  loadBalancingStrategy: 'round-robin',
  enableAutoRestart: true,
});
await manager.initialize();

// Create VMs
const vm1 = new NullVM({
  vmId: 'worker-1',
  hybridRuntime: { enabled: true, manager }
});

const vm2 = new NullVM({
  vmId: 'worker-2',
  hybridRuntime: { enabled: true, manager }
});

// Send message between VMs
await vm1.sendMessageToVM('worker-2', 'DATA', { value: 42 });

// Synchronize at barrier
await manager.createBarrier('sync', 2);
await Promise.all([
  vm1.joinBarrier('sync'),
  vm2.joinBarrier('sync')
]);
```

### New Opcodes

- **SPAWN_VM**: Spawn a child VM
- **SEND_MSG**: Send message to another VM
- **RECV_MSG**: Receive message from queue
- **SYNC_BARRIER**: Synchronize at barrier point

### Example

Run the distributed execution example:

```bash
npx ts-node examples/distributed_execution.ts
```

## License

MIT
