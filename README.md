# NullVM - Virtual Machine for Super-Bit Programs

A TypeScript implementation of a virtual machine that executes super-bit programs with support for instruction decoding, execution contexts, memory management, and binary frame emission.

> **🚀 Null v2 in Development**: We're building the next generation of Null with modern language features including ownership system, pattern matching, async/await, SIMD, and more. See the [**Null v2 Language Specification**](docs/null_v2_language_spec.md) for the complete roadmap and blueprint.

## Features

- **Instruction Set Support**: SET, ADD, SHOW, IF, REPEAT, DEFINE, CALL, RETURN, JMP, NOP, security opcodes, and AI opcodes
- **Memory Model**: Scalar registers, tensor registers (super-bit tensors), stack, and heap abstractions with encrypted value storage
- **Control Flow**: Conditional execution (IF) and loops (REPEAT)
- **Function Definitions**: Define and call custom functions with proper call stack management
- **AI/ML Substrate**: Super-bit tensor operations with embedding registry, dense layers, multi-head attention, and uncertainty quantification
- **AI Instructions**: AI_EMBED (load embeddings), AI_LAYER (dense forward pass), AI_ATTEND (attention with uncertainty reduction), AI_FUZZY (probabilistic uncertainty reduction)
- **Binary Bridge**: Emit binary frames for output, register state, tensor state, and security metadata
- **Error Handling**: Structured error propagation with detailed error types
- **Tracing Hooks**: Hook into execution events for debugging and monitoring
- **Fuzzy Bit Evaluation**: Stubs for probabilistic evaluation support with attention-based refinement
- **Cryptographic Primitives**: Homomorphic encryption, secure channels, zero-knowledge proofs, and secure multi-party computation (SMPC)
- **NLP Module**: Multilingual tokenization, embeddings, translation, and code generation
- **Knowledge Graphs**: Entity-relationship graphs, ontology management, rule-based inference, and RDF/JSON-LD support
- **ML Runtime**: PyTorch-backed inference, super-bit quantization (<10MB), semantic embeddings, probabilistic attention, gradient-free optimization

## Project Structure

```
src/
├── null_system/
│   ├── vm/
│   │   ├── null_vm.ts              # Main NullVM class
│   │   ├── instructions.ts          # Instruction definitions and opcodes (including AI opcodes)
│   │   ├── decoder.ts               # Super-bit program decoder with AI instruction validation
│   │   ├── memory.ts                # Memory model (scalar registers, tensor registers, stack, heap)
│   │   ├── execution_context.ts     # Execution state and call stack management
│   │   ├── binary_bridge.ts         # Binary frame emission (tensor state, proof transcripts, metadata)
│   │   ├── fuzzy_bits.ts            # Fuzzy/probabilistic evaluation with uncertainty quantification
│   │   ├── errors.ts                # Error types and handling
│   │   ├── ai/
│   │   │   ├── superbit_tensor.ts   # Super-bit tensor representation with uncertainty metadata
│   │   │   ├── embedding_registry.ts # Reusable embedding management and caching
│   │   │   ├── neural_engine.ts     # Dense layers with Xavier weight initialization
│   │   │   ├── attention.ts         # Scaled dot-product & multi-head attention mechanisms
│   │   │   └── index.ts             # AI module exports
│   │   ├── index.ts                 # VM module exports
│   │   └── __tests__/
│   │       ├── ai.test.ts           # Comprehensive AI instruction & tensor tests
│   │       └── (other tests)         # Unit tests for VM components
│   ├── security/
│   │   ├── homomorphic_engine.ts           # Homomorphic encryption
│   │   ├── secure_channel.ts               # Key exchange & authenticated transport
│   │   ├── zkp.ts                          # Zero-knowledge proofs
│   │   ├── smpc_orchestrator.ts            # Secret sharing & SMPC
│   │   ├── index.ts
│   │   └── __tests__/                      # Security module tests
│   ├── ml/
│   │   ├── engine.py                       # ML inference engine
│   │   ├── quantization.py                 # Super-bit quantization
│   │   ├── embeddings.py                   # Semantic embeddings
│   │   ├── attention.py                    # Attention mechanisms
│   │   ├── optimizers.py                   # Gradient-free optimizers
│   │   ├── benchmarks.py                   # Performance profiling
│   │   ├── backends/
│   │   │   ├── torch_backend.py            # PyTorch inference engine
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── lib/
│   │   ├── ml_ops.py                       # ML library operations
│   │   ├── registry.py                     # Function registry (including ML)
│   │   └── ...
│   ├── compiler/
│   │   ├── hybrid_runner.py                # Python bridge for distributed execution
│   │   └── ...
│   └── ...
├── bin/
│   └── cli.ts                              # CLI entry point (nullvm command)
├── examples/
│   ├── sample_program.ts                  # Sample super-bit programs
│   ├── distributed_execution.ts           # Distributed workload example
│   ├── ai_inference.ts                    # AI tensor pipeline demonstration
│   ├── phase6/
│   │   └── ml_inference.null              # ML inference example in Null-Lang
│   └── __tests__/                         # End-to-end tests
├── docs/
│   ├── knowledge.md                 # NLP & Knowledge Graph documentation
│   ├── architecture.md              # System architecture
│   ├── hybrid_runtime.md            # Hybrid runtime guide
│   ├── use_cases_market.md          # Use-case & market brief (11 domains)
│   └── phase6/
│       └── null_ml.md               # ML Runtime documentation
└── index.ts                               # Main package exports
```

## Installation

TypeScript (VM):

```bash
npm install
```

Python (compiler tooling + LSP):

```bash
pip install -e .
```

## Language Server (LSP)

Start an editor-friendly LSP server (stdio):

```bash
nullc lsp --syntax auto --stdio
```

Pin the syntax mode:

```bash
nullc lsp --syntax english --stdio
nullc lsp --syntax modern --stdio
nullc lsp --syntax hybrid --stdio
```

See [`docs/ide/dual_syntax.md`](docs/ide/dual_syntax.md) for initialization options, dual-mode highlighting assets, and editor integration notes.

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

## AI/ML Instructions for Tensor Operations

NullVM includes a foundational AI substrate for tensor-aware computation on classical hardware.

### AI_EMBED - Load or Allocate Embedding

```javascript
{ opcode: 'AI_EMBED', args: ['output_register', 'embedding_id', dimension] }
```

Allocates a tensor register and loads an embedding vector:
- Queries the embedding registry for a previously registered embedding
- If not found, creates a random dense embedding of specified dimension
- Stores result in a tensor register (separate from scalar registers)
- Emits frame with embedding metadata

**Example:**
```javascript
{ opcode: 'AI_EMBED', args: ['token_embedding', 'bert_001', 768] }
```

### AI_LAYER - Dense Layer Forward Pass

```javascript
{ opcode: 'AI_LAYER', args: ['input_register', 'output_register', '{"outputDim": N}', 'activation'] }
```

Executes a fully-connected layer with optional activation:
- Reads tensor from `input_register`
- Creates dense layer with Xavier/Glorot weight initialization
- Applies specified activation: `relu`, `sigmoid`, `tanh`, or `linear`
- Outputs to tensor register
- Propagates uncertainty: `new_uncertainty = max(input, weight) × precision_product`

**Example:**
```javascript
{ opcode: 'AI_LAYER', args: ['h0', 'h1', '{"outputDim": 2048}', 'relu'] }
```

### AI_ATTEND - Self-Attention with Uncertainty Reduction

```javascript
{ opcode: 'AI_ATTEND', args: ['input_register', 'output_register', '{"headCount": N}'] }
```

Applies scaled dot-product multi-head self-attention:
- Reads tensor from `input_register`
- Implements `Attention(Q,K,V) = softmax(QK^T/√d_k)V`
- Splits into N attention heads for parallel computation
- **Reduces uncertainty** through pattern focusing (default: 30% reduction)
- Computes precision from head-wise products

**Attention Config:**
- `headCount`: Number of attention heads (default: 1)
- `temperatureScale`: Softmax temperature (default: 1.0)
- `uncertaintyReductionFactor`: Uncertainty reduction per head (default: 0.3)

**Example:**
```javascript
{ opcode: 'AI_ATTEND', args: ['h', 'attended', '{"headCount": 8}'] }
```

### AI_FUZZY - Probabilistic Uncertainty Reduction

```javascript
{ opcode: 'AI_FUZZY', args: ['input_register', 'output_register', uncertaintyReduction] }
```

Applies fuzzy-logic based uncertainty refinement:
- Clones tensor from `input_register`
- Reduces uncertainty by specified amount (capped at 0)
- Models probabilistic evaluation gaining confidence
- Useful after inference steps to quantify certainty

**Example:**
```javascript
{ opcode: 'AI_FUZZY', args: ['logits', 'refined_logits', 0.25] }
```

## Complete AI Program Example

```typescript
import { NullVM, OpCode } from './src';

const vm = new NullVM();

const program = [
  // 1. Load token embedding (512-dim)
  { opcode: OpCode.AI_EMBED, args: ['x', 'token_001', 512] },
  
  // 2. Dense layer: 512 → 2048 with ReLU
  { opcode: OpCode.AI_LAYER, args: ['x', 'h1', '{"outputDim": 2048}', 'relu'] },
  
  // 3. Dense layer: 2048 → 512 with linear
  { opcode: OpCode.AI_LAYER, args: ['h1', 'h2', '{"outputDim": 512}', 'linear'] },
  
  // 4. Multi-head attention (8 heads)
  { opcode: OpCode.AI_ATTEND, args: ['h2', 'attn', '{"headCount": 8}'] },
  
  // 5. Fuzzy refinement
  { opcode: OpCode.AI_FUZZY, args: ['attn', 'logits', 0.1] },
];

vm.execute(program);

// Access tensor result
const registry = vm.getEmbeddingRegistry();
const logits = vm.getState().memory.getTensorRegister('logits');
console.log('Output shape:', logits.getShape().dims);
console.log('Uncertainty:', logits.getMetadata().uncertainty);
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
  getEmbeddingRegistry(): EmbeddingRegistry
  getNeuralEngine(): NeuralEngine
  getAttentionModule(): AttentionModule
  reset(): void
  getExecutionCycle(): number
  getState(): object
}
```

### Memory

Manages scalar registers, tensor registers, stack, heap, encrypted values, and cryptographic keys.

```typescript
class Memory {
  setRegister(name: string, value: number): void
  getRegister(name: string): number
  setTensorRegister(name: string, tensor: SuperBitTensor): void
  getTensorRegister(name: string): SuperBitTensor | null
  hasTensorRegister(name: string): boolean
  getAllTensorRegisters(): Record<string, SuperBitTensor>
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

**Python Tests:**
```bash
# Run all tests (excludes load tests by default)
pytest tests/

# Run specific test suites
pytest tests/test_system_validation.py -v
pytest tests/test_integration.py -v
pytest tests/lang/ -v

# Run load/stress tests (opt-in)
pytest tests/perf/test_load.py -v -m load

# Run without load tests explicitly
pytest tests/ -v -m "not load"
```

**TypeScript Tests:**
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

- **System Validation Tests** (`tests/test_system_validation.py`):
  - End-to-end compilation tests using example .null files
  - Cross-module integration tests (ML/NLP library operations)
  - Hybrid execution tests with mock accelerators (CPU, GPU, ML, NLP)
  - Distributed consistency tests with multiple VM instances
  - Fault injection tests for error handling and recovery
  - Pipeline consistency validation (AST → SuperBit → Binary → VM)

- **Load & Stress Tests** (`tests/perf/test_load.py`) - marked with `@pytest.mark.load`:
  - Compile and execute 1,000+ programs
  - Concurrent execution with 100+ worker threads
  - VM state isolation under concurrent load
  - Memory stability over 1,000 iterations
  - Race condition detection
  - Large program compilation (10,000+ statements)
  - Burst compilation load testing

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

### Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.encoding` - Super-Bit encoding tests
- `@pytest.mark.load` - Load and stress tests (opt-in, use `-m load` to run)

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

## Documentation

### Core Documentation
- **[Null v2 Language Specification](docs/null_v2_language_spec.md)** - Complete roadmap for Null v2 with modern language features (ownership, pattern matching, async/await, SIMD, and more)
- **[v2 Implementation Issues](ISSUES_V2.md)** - Comprehensive task list and open questions for implementing v2 features
- **[Architecture](ARCHITECTURE.md)** - System architecture and compilation pipeline
- **[Architecture Details](docs/architecture.md)** - Five-layer architecture (Lang, Data, Super-Bit, VM, Runtime)

### Feature-Specific Guides
- **[Hybrid Runtime](docs/hybrid_runtime.md)** - Distributed execution with work-stealing scheduler
- **[Hybrid Execution](docs/hybrid_execution.md)** - Comprehensive hybrid executor documentation
- **[Knowledge Graphs & NLP](docs/knowledge.md)** - NLP module and knowledge graph integration
- **[Security](docs/security.md)** - Cryptographic primitives (encryption, ZK proofs, SMPC)

### Reference
- **[Translation Table](TRANSLATION_TABLE.md)** - Super-bit encoding reference
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Implementation details

## License

MIT
