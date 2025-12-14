# Null v2 Language Specification

**Version**: 2.0-draft  
**Date**: December 2024  
**Status**: Blueprint/Roadmap

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Syntax Design](#syntax-design)
4. [Phase-by-Phase Roadmap](#phase-by-phase-roadmap)
5. [Module Mapping](#module-mapping)
6. [Migration Strategy](#migration-strategy)
7. [Testing Strategy](#testing-strategy)
8. [Performance & Concurrency Goals](#performance--concurrency-goals)
9. [Open Questions & Assumptions](#open-questions--assumptions)
10. [Implementation Checklist](#implementation-checklist)

---

## Executive Summary

Null v2 represents a major evolution of the Null-Lang programming language, introducing modern programming language features inspired by Rust, Kotlin, and Go while preserving the unique English-like syntax and Super-Bit encoding foundation. This specification consolidates 10 phases of development that will transform Null into a production-ready language with:

- **Dual Syntax**: English-like syntax (v1) alongside modern, concise syntax (v2)
- **Memory Safety**: Rust-inspired ownership system with borrow checking
- **Advanced Type System**: Sealed classes, union types, inline types, context receivers
- **Modern Control Flow**: Pattern matching, async/await, coroutines with channels
- **Performance**: SIMD intrinsics, zero-cost abstractions, compile-time optimization
- **AI Integration**: Super-bit tensor operations with NLP and knowledge graphs
- **Distributed Runtime**: V10 runtime with fault tolerance and work-stealing scheduler

**Target Timeline**: 18-24 months across 10 phases  
**Backwards Compatibility**: v1 English syntax maintained alongside v2 syntax

---

## Architecture Overview

### Current Architecture (v1)

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Lang (English-like syntax → AST)                   │
│  - parser.py, grammar.lark, ast_nodes.py                     │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Data (Type representations)                        │
│  - types.py, data type classes                               │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Super-Bit (4-8 bit encoding)                       │
│  - encoder.py, decoder.py, registry.py                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: VM (TypeScript execution engine)                   │
│  - null_vm.ts, instructions.ts, memory.ts                    │
│  - AI substrate, NLP, Knowledge Graphs                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 5: Runtime (Hybrid distributed execution)             │
│  - hybrid_execution_manager.ts, work_scheduler.ts            │
│  - Security (encryption, ZK proofs, SMPC)                    │
└─────────────────────────────────────────────────────────────┘
```

### Target Architecture (v2)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Application Layer                               │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 1: Parser & AST                                               │
│  ┌─────────────────┐  ┌────────────────┐                           │
│  │ English Parser  │  │ Modern Parser  │  (Dual Syntax)             │
│  │ (grammar.lark)  │  │ (v2_grammar)   │                           │
│  └────────┬────────┘  └───────┬────────┘                           │
│           └──────────┬─────────┘                                     │
│                      ▼                                                │
│            Unified AST + Source Mapping                              │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 2: Type System & Semantic Analysis                            │
│  - Ownership analysis (borrow checker)                               │
│  - Type inference engine (Hindley-Milner + extensions)               │
│  - Pattern exhaustiveness checking                                   │
│  - Lifetime annotations & region inference                           │
│  - Trait/protocol resolution                                         │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 3: IR & Optimization (MIR/LIR)                                │
│  - High-level IR (control flow graph)                                │
│  - Optimization passes (inlining, DCE, constant folding)             │
│  - SIMD vectorization                                                │
│  - Super-Bit encoding with compression                               │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 4: VM & JIT Compilation                                       │
│  - Bytecode interpreter (enhanced)                                   │
│  - Tier-1 JIT (hot path compilation)                                 │
│  - AI substrate (tensors, NLP, KG)                                   │
│  - Async runtime (coroutines, channels)                              │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 5: V10 Runtime (Distributed + Secure)                         │
│  - Work-stealing scheduler (enhanced)                                │
│  - Actor system for message passing                                  │
│  - Distributed memory management                                     │
│  - Security layer (homomorphic encryption, ZK, SMPC)                 │
│  - Fault tolerance & checkpointing                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Syntax Design

### Philosophy: Dual-Syntax Approach

Null v2 introduces a modern, concise syntax **alongside** the existing English-like syntax. Both compile to the same AST and bytecode, allowing developers to choose their preferred style or mix both in the same project.

### Comparison Table

| Feature | English Syntax (v1) | Modern Syntax (v2) |
|---------|---------------------|-------------------|
| **Variable Declaration** | `SET x TO 42` | `let x = 42` or `let mut x = 42` |
| **Function Definition** | `DEFINE greet WITH name` | `fn greet(name: Text) -> Unit` |
| **Conditionals** | `IF x IS GREATER THAN 10 THEN` | `if x > 10 { ... }` |
| **Loops** | `REPEAT 5 TIMES` | `for i in 0..5 { ... }` |
| **Pattern Matching** | _(not supported)_ | `match value { ... }` |
| **Ownership** | _(implicit)_ | `own x`, `borrow y`, `move z` |
| **Null Safety** | _(implicit)_ | `x?.method()`, `x ?: default` |
| **Async** | _(not supported)_ | `async fn fetch() -> Result<T>` |
| **Data Classes** | `SET person TO { name: "Alice" }` | `data class Person(name: Text, age: Num)` |
| **Sealed Classes** | _(not supported)_ | `sealed class Result<T> { ... }` |
| **Comprehensions** | _(not supported)_ | `[x * 2 for x in list if x > 0]` |
| **Pipelines** | _(not supported)_ | `data \|> filter \|> map \|> collect` |

### Ownership & Memory Safety (Phase 3-4)

Inspired by Rust, Null v2 introduces explicit ownership semantics:

```null
// Ownership keywords
let own x = Vector::new()        // x owns the vector
let borrow y = &x                 // y borrows x immutably
let borrow_mut z = &mut x         // z borrows x mutably
move_to_function(x)               // x is moved, no longer accessible

// Automatic with inference
let data = load_file("data.txt")  // ownership inferred
process(data)                     // move inferred from function signature
// data is no longer valid here

// Lifetimes (explicit when needed)
fn longest<'a>(x: &'a Text, y: &'a Text) -> &'a Text {
    if x.len() > y.len() { x } else { y }
}
```

**English Equivalent:**
```null
CREATE OWNED vector AS Vector::new()
BORROW immutable_ref FROM vector
BORROW MUTABLE mutable_ref FROM vector
MOVE vector TO function_call
```

### Pattern Matching (Phase 2)

Powerful match expressions with exhaustiveness checking:

```null
// Modern syntax
match http_response {
    Ok(data) => process(data),
    Err(NotFound) => log("404"),
    Err(ServerError(code)) => retry(code),
    _ => panic("Unknown error")
}

// English syntax
MATCH http_response WITH
    CASE Ok WITH data THEN process(data)
    CASE Err WITH NotFound THEN log("404")
    CASE Err WITH ServerError code THEN retry(code)
    DEFAULT panic("Unknown error")
END MATCH
```

### Async/Await & Coroutines (Phase 5)

First-class async support with coroutines and channels:

```null
// Modern syntax
async fn fetch_user(id: Num) -> Result<User> {
    let response = await http::get("/users/{id}")
    let user = await response.json()
    Ok(user)
}

// Coroutines with channels
let (tx, rx) = channel::<Message>()

spawn {
    tx.send(Message::Hello).await
}

let msg = rx.recv().await

// English syntax
DEFINE ASYNC fetch_user WITH id RETURNS Result<User>
    SET response TO AWAIT http::get("/users/{id}")
    SET user TO AWAIT response.json()
    RETURN Ok(user)
END DEFINE
```

### Sealed & Data Classes (Phase 2)

Kotlin-inspired sealed hierarchies and data classes:

```null
// Sealed class (algebraic data type)
sealed class Result<T, E> {
    data class Ok(value: T) extends Result<T, E>
    data class Err(error: E) extends Result<T, E>
}

// Data class with automatic methods
data class Point(x: Num, y: Num) {
    // Auto-generated: equals, hashCode, toString, copy
}

let p1 = Point(10, 20)
let p2 = p1.copy(x = 15)  // Structural copying

// English equivalent
DEFINE SEALED Result<T, E>
    DATA CLASS Ok WITH value: T EXTENDS Result
    DATA CLASS Err WITH error: E EXTENDS Result
END DEFINE
```

### Union, Inline & Context Types (Phase 4)

Advanced type system features:

```null
// Union types
type StringOrNum = Text | Num
let value: StringOrNum = "hello"
value = 42  // Valid

// Inline types (zero-cost wrappers)
inline class UserId(value: Num)
inline class Email(value: Text)

let id = UserId(12345)
// Runtime: just a Num, no wrapper overhead

// Context receivers (Kotlin-style)
context(Logger, Database)
fn process_order(order: Order) {
    // implicit access to logger and database
    log("Processing order {order.id}")
    database.save(order)
}
```

### SIMD & Performance Primitives (Phase 7)

Low-level SIMD intrinsics for high-performance computing:

```null
// SIMD vector operations
let a = simd::f32x4([1.0, 2.0, 3.0, 4.0])
let b = simd::f32x4([5.0, 6.0, 7.0, 8.0])
let c = a + b  // Vectorized addition

// Manual SIMD intrinsics
@simd::target("avx2")
fn dot_product(a: &[f32], b: &[f32]) -> f32 {
    let mut sum = simd::f32x8::splat(0.0)
    for i in (0..a.len()).step_by(8) {
        let va = simd::f32x8::from_slice(&a[i..])
        let vb = simd::f32x8::from_slice(&b[i..])
        sum += va * vb
    }
    sum.horizontal_sum()
}
```

### Comprehensions & Pipelines (Phase 6)

Python-style comprehensions and F#-style pipelines:

```null
// List comprehension
let squares = [x * x for x in 0..10 if x % 2 == 0]

// Dict comprehension
let word_lengths = {word: word.len() for word in words}

// Pipeline operator
let result = data
    |> filter(x => x > 0)
    |> map(x => x * 2)
    |> reduce(0, (a, b) => a + b)

// English equivalent
SET squares TO COMPREHEND x * x FOR x IN 0..10 WHERE x MODULO 2 EQUALS 0

SET result TO data
    PIPE TO filter WITH x => x > 0
    PIPE TO map WITH x => x * 2
    PIPE TO reduce WITH 0, (a, b) => a + b
```

---

## Phase-by-Phase Roadmap

### Phase 1: Foundation & Dual Parser (Months 1-2)

**Goal**: Establish v2 parser infrastructure alongside v1, unified AST representation

**Features**:
- New grammar definition for modern syntax
- Dual parser system (route to English or Modern based on file extension or pragma)
- Unified AST that represents both syntaxes
- Source mapping for error reporting
- Syntax highlighting definitions

**Deliverables**:
- `src/null_system/lang/v2_grammar.lark` - Modern syntax grammar
- `src/null_system/lang/v2_parser.py` - Modern parser implementation
- `src/null_system/lang/unified_ast.py` - Extended AST nodes
- `src/null_system/lang/syntax_router.py` - Route between parsers
- `tests/lang/test_v2_parser.py` - Comprehensive test suite
- `docs/syntax_guide.md` - Syntax comparison guide

**Dependencies**: None (foundation)

**Testing**:
- Unit tests: Parser correctness, AST construction
- Integration tests: Round-trip parse → AST → codegen
- Compatibility tests: Ensure v1 parser unaffected

**Acceptance Criteria**:
- ✅ Modern syntax can be parsed to AST
- ✅ Both syntaxes compile to identical bytecode
- ✅ Error messages show correct line/column for both syntaxes
- ✅ All existing v1 tests pass

---

### Phase 2: Type System Enhancements (Months 3-5)

**Goal**: Implement sealed classes, data classes, union types, pattern matching

**Features**:
- Sealed class hierarchy
- Data class with structural equality and copy methods
- Union types (`A | B`)
- Pattern matching with exhaustiveness checking
- Type inference improvements (Hindley-Milner basis)

**Deliverables**:
- `src/null_system/types/sealed_class.py` - Sealed class implementation
- `src/null_system/types/data_class.py` - Data class codegen
- `src/null_system/types/union_type.py` - Union type handling
- `src/null_system/types/pattern_matcher.py` - Pattern matching engine
- `src/null_system/types/type_inference.py` - Enhanced type inference
- Updated AST nodes for match expressions
- VM opcodes: MATCH_BEGIN, MATCH_CASE, MATCH_END

**Dependencies**: Phase 1 (parser infrastructure)

**Testing**:
- Unit tests: Type checking, pattern exhaustiveness
- Integration tests: Sealed hierarchies in real programs
- Performance tests: Type inference speed on large programs

**Acceptance Criteria**:
- ✅ Sealed classes prevent external inheritance
- ✅ Data classes generate equals/hashCode/toString/copy
- ✅ Pattern matching compiles to efficient decision trees
- ✅ Non-exhaustive patterns produce compile errors
- ✅ Union types support type narrowing in branches

---

### Phase 3: Ownership System - Analysis (Months 6-8)

**Goal**: Implement Rust-inspired ownership tracking and borrow checker (analysis only)

**Features**:
- Ownership annotations in AST
- Borrow checker (compile-time analysis)
- Move semantics tracking
- Lifetime annotations (explicit and inferred)
- Region-based memory safety

**Deliverables**:
- `src/null_system/ownership/borrow_checker.py` - Borrow checking implementation
- `src/null_system/ownership/lifetime_inference.py` - Lifetime annotation inference
- `src/null_system/ownership/move_tracker.py` - Track value moves
- AST extensions for ownership annotations
- Comprehensive error messages for ownership violations

**Dependencies**: Phase 2 (type system)

**Testing**:
- Unit tests: Borrow checker correctness (positive/negative cases)
- Integration tests: Complex ownership patterns
- Regression tests: Common ownership errors detected

**Acceptance Criteria**:
- ✅ Prevents use-after-move
- ✅ Prevents multiple mutable borrows
- ✅ Prevents dangling references
- ✅ Lifetime annotations inferred correctly 90% of the time
- ✅ Clear error messages with suggestions

---

### Phase 4: Ownership System - Runtime (Months 9-10)

**Goal**: Implement runtime support for ownership (reference counting, RAII)

**Features**:
- Reference counting for owned values
- Automatic drop/destructor calls
- Move optimization in bytecode
- Stack vs. heap allocation analysis
- Inline types (zero-cost wrappers)
- Context receivers

**Deliverables**:
- `src/null_system/vm/ownership_runtime.ts` - Runtime ownership tracking
- `src/null_system/vm/ref_counting.ts` - Reference counting implementation
- Enhanced bytecode with MOVE, BORROW, DROP opcodes
- Inline type codegen (monomorphization)
- Context receiver implementation

**Dependencies**: Phase 3 (ownership analysis)

**Testing**:
- Unit tests: Reference counting correctness
- Integration tests: Complex ownership patterns execute correctly
- Memory tests: No leaks, proper cleanup
- Performance tests: Overhead of ownership runtime < 10%

**Acceptance Criteria**:
- ✅ Values automatically cleaned up when out of scope
- ✅ Reference counting handles cycles (weak references)
- ✅ Move semantics avoid unnecessary copies
- ✅ Inline types have zero runtime overhead
- ✅ Memory usage similar to manual management

---

### Phase 5: Async Runtime & Coroutines (Months 11-13)

**Goal**: First-class async/await support with green threads and channels

**Features**:
- Async/await syntax
- Coroutine runtime (green threads)
- Channels (MPSC, SPSC, broadcast)
- Async I/O integration
- Futures and promises
- Structured concurrency

**Deliverables**:
- `src/null_system/vm/async_runtime.ts` - Async executor
- `src/null_system/vm/coroutine.ts` - Coroutine implementation
- `src/null_system/vm/channel.ts` - Channel implementations
- Async opcodes: ASYNC_BEGIN, AWAIT, YIELD, SPAWN
- Async standard library (file I/O, networking, timers)

**Dependencies**: Phase 1-2 (parser, type system)

**Testing**:
- Unit tests: Coroutine scheduling, channel operations
- Integration tests: Complex async programs
- Concurrency tests: Race conditions, deadlocks
- Performance tests: Throughput vs. OS threads

**Acceptance Criteria**:
- ✅ Async functions can await other async functions
- ✅ Channels support multi-producer, multi-consumer
- ✅ Coroutines are lightweight (10K+ concurrent coroutines)
- ✅ Structured concurrency prevents orphaned tasks
- ✅ No data races in async code (checked statically)

---

### Phase 6: Modern Language Features (Months 14-15)

**Goal**: Comprehensions, pipelines, null-safety operators, operator overloading

**Features**:
- List/dict/set comprehensions
- Pipeline operator (`|>`)
- Null-safety operators (`?.`, `?:`, `!!`)
- Operator overloading for custom types
- Extension methods
- String interpolation enhancements

**Deliverables**:
- Parser extensions for comprehensions and pipelines
- Desugaring passes (comprehension → loops, pipeline → nested calls)
- Null-safety checking at compile time
- Operator overloading codegen
- Extension method resolution

**Dependencies**: Phase 2 (type system)

**Testing**:
- Unit tests: Comprehension correctness, pipeline execution
- Integration tests: Null-safety prevents runtime errors
- Performance tests: Comprehensions vs. hand-written loops

**Acceptance Criteria**:
- ✅ Comprehensions generate efficient loops
- ✅ Pipelines have zero overhead vs. nested calls
- ✅ Null-safety checked at compile time (no runtime checks)
- ✅ Operator overloading supports arithmetic, comparison, indexing
- ✅ Extension methods resolve correctly with namespacing

---

### Phase 7: SIMD & Performance Optimizations (Months 16-17)

**Goal**: SIMD intrinsics, auto-vectorization, zero-cost abstractions

**Features**:
- SIMD vector types (f32x4, i32x8, etc.)
- SIMD intrinsics (platform-specific)
- Auto-vectorization pass in optimizer
- Zero-cost abstractions (monomorphization)
- Compile-time function evaluation (const fn)
- Profile-guided optimization

**Deliverables**:
- `src/null_system/compiler/simd.py` - SIMD lowering pass
- `src/null_system/compiler/vectorizer.py` - Auto-vectorization
- `src/null_system/vm/simd_runtime.ts` - SIMD runtime support
- SIMD opcodes: SIMD_LOAD, SIMD_STORE, SIMD_OP
- Standard library SIMD functions

**Dependencies**: Phase 4 (ownership runtime)

**Testing**:
- Unit tests: SIMD operations correctness
- Performance tests: SIMD vs. scalar (4-8x speedup expected)
- Cross-platform tests: x86 (SSE, AVX), ARM (NEON), WASM (SIMD128)

**Acceptance Criteria**:
- ✅ Manual SIMD code works correctly
- ✅ Auto-vectorizer handles simple loops
- ✅ Zero-cost abstractions compile to same code as hand-written
- ✅ SIMD performance within 90% of hand-optimized C
- ✅ Cross-platform support (fallback for unsupported platforms)

---

### Phase 8: Enhanced Super-Bit Encoding (Months 16-17)

**Goal**: Optimize Super-Bit encoding for v2 features, compression improvements

**Features**:
- Encoding for new AST nodes (match, async, etc.)
- Improved compression (LZ4, Zstd integration)
- Lazy decoding for faster startup
- Delta encoding for similar programs
- Bytecode versioning and migration

**Deliverables**:
- Updated `src/null_system/superbit/encoder.py` for v2 features
- `src/null_system/superbit/compression.py` - Advanced compression
- `src/null_system/superbit/lazy_decoder.py` - Lazy decoding
- Bytecode versioning scheme
- Migration tools for v1 → v2 bytecode

**Dependencies**: Phase 1-7 (all language features)

**Testing**:
- Unit tests: Encoding/decoding round-trip correctness
- Performance tests: Compression ratio, decode speed
- Compatibility tests: v1 bytecode still loads

**Acceptance Criteria**:
- ✅ v2 bytecode 20-30% smaller than v1 with compression
- ✅ Lazy decoding reduces startup time by 50%
- ✅ Backward compatible (v2 VM can run v1 bytecode)
- ✅ Forward migration path (v1 → v2 bytecode converter)

---

### Phase 9: AI/ML Integration Enhancements (Months 18-19)

**Goal**: Deeper integration of NLP, Knowledge Graphs, and ML with v2 type system

**Features**:
- First-class tensor types in type system
- ML model loading and inference operators
- Knowledge graph query language integration
- Differentiable programming support
- GPU/TPU acceleration hooks

**Deliverables**:
- `src/null_system/types/tensor_type.py` - Tensor type checking
- Enhanced AI opcodes with type safety
- Knowledge graph query DSL
- Automatic differentiation (AD) support
- GPU backend integration (CUDA, Metal, WebGPU)

**Dependencies**: Phase 2 (type system), Phase 7 (SIMD)

**Testing**:
- Unit tests: Tensor operations type safety
- Integration tests: ML model inference end-to-end
- Performance tests: GPU vs. CPU for ML workloads

**Acceptance Criteria**:
- ✅ Tensor shapes checked at compile time
- ✅ ML models can be loaded and executed type-safely
- ✅ Knowledge graph queries integrated with type system
- ✅ GPU acceleration provides 10-100x speedup for ML
- ✅ Automatic differentiation works for optimization

---

### Phase 10: V10 Runtime - Production Hardening (Months 20-24)

**Goal**: Production-grade distributed runtime with fault tolerance and monitoring

**Features**:
- Enhanced work-stealing scheduler
- Actor system for message passing
- Distributed garbage collection
- Fault tolerance (checkpointing, replay)
- Observability (metrics, tracing, profiling)
- Hot code reloading
- Production deployment tools

**Deliverables**:
- `src/null_system/vm/v10_runtime/` - Complete V10 runtime
- Actor system implementation
- Distributed GC
- Checkpoint/restore infrastructure
- Metrics and tracing framework
- CLI tools for deployment and monitoring

**Dependencies**: Phase 5 (async runtime), Phase 8 (bytecode versioning)

**Testing**:
- Integration tests: Distributed programs execute correctly
- Fault tolerance tests: Node failures handled gracefully
- Performance tests: Scalability to 100+ nodes
- Chaos testing: Random failures, network partitions

**Acceptance Criteria**:
- ✅ Work-stealing scheduler achieves 90%+ CPU utilization
- ✅ Actor system handles millions of actors
- ✅ Fault tolerance recovers from node failures in < 1s
- ✅ Observability provides actionable metrics
- ✅ Hot code reloading works without downtime
- ✅ Production deployments stable for weeks+

---

## Module Mapping

This table maps each v2 feature to the specific modules/files in the codebase that will implement it.

| Feature | Modules | Files/Paths |
|---------|---------|-------------|
| **Dual Parser** | `parser`, `lang` | `src/null_system/lang/v2_parser.py`, `v2_grammar.lark`, `syntax_router.py` |
| **Unified AST** | `ast`, `lang` | `src/null_system/lang/unified_ast.py`, `ast/nodes.py` |
| **Sealed Classes** | `types`, `ast` | `src/null_system/types/sealed_class.py`, AST extensions |
| **Data Classes** | `types`, `ast` | `src/null_system/types/data_class.py`, codegen |
| **Union Types** | `types` | `src/null_system/types/union_type.py`, type checker |
| **Pattern Matching** | `ast`, `compiler`, `vm` | AST nodes, `pattern_matcher.py`, VM opcodes |
| **Ownership Analysis** | `ownership` (new) | `src/null_system/ownership/borrow_checker.py`, `lifetime_inference.py` |
| **Ownership Runtime** | `vm`, `runtime` | `src/null_system/vm/ownership_runtime.ts`, `ref_counting.ts` |
| **Async/Await** | `vm`, `compiler` | `src/null_system/vm/async_runtime.ts`, `coroutine.ts` |
| **Coroutines** | `vm` | `src/null_system/vm/coroutine.ts`, scheduler |
| **Channels** | `vm` | `src/null_system/vm/channel.ts` |
| **Comprehensions** | `parser`, `compiler` | Parser extensions, desugaring pass |
| **Pipelines** | `parser`, `compiler` | Parser extensions, desugaring pass |
| **Null Safety** | `types`, `compiler` | Type checker, null analysis |
| **SIMD** | `compiler`, `vm` | `src/null_system/compiler/simd.py`, `vm/simd_runtime.ts` |
| **Auto-Vectorization** | `compiler` | `src/null_system/compiler/vectorizer.py` |
| **Super-Bit v2** | `superbit` | `src/null_system/superbit/encoder.py`, `decoder.py` (enhanced) |
| **Compression** | `superbit` | `src/null_system/superbit/compression.py` |
| **Tensor Types** | `types`, `vm` | `src/null_system/types/tensor_type.py`, VM AI modules |
| **ML Integration** | `vm/ai`, `vm/nlp` | Enhanced opcodes, GPU backends |
| **Knowledge Graphs** | `vm/knowledge` | DSL integration, query optimizer |
| **V10 Runtime** | `vm/hybrid_runtime`, `vm/distributed` | `src/null_system/vm/v10_runtime/` (new) |
| **Actor System** | `vm` | `src/null_system/vm/actor.ts` |
| **Fault Tolerance** | `vm`, `runtime` | Checkpoint/restore, replay |
| **Observability** | `runtime` | Metrics, tracing, profiling |

### New Directories to Create

```
src/null_system/
├── ownership/                    # Phase 3-4: Ownership system
│   ├── borrow_checker.py
│   ├── lifetime_inference.py
│   ├── move_tracker.py
│   └── region_analysis.py
├── lang/
│   ├── v2_grammar.lark          # Phase 1: Modern syntax
│   ├── v2_parser.py
│   ├── unified_ast.py
│   └── syntax_router.py
├── types/
│   ├── sealed_class.py          # Phase 2: Advanced types
│   ├── data_class.py
│   ├── union_type.py
│   ├── pattern_matcher.py
│   └── tensor_type.py           # Phase 9: ML types
├── compiler/
│   ├── simd.py                  # Phase 7: SIMD
│   ├── vectorizer.py
│   ├── optimizer_v2.py
│   └── monomorphizer.py
├── vm/
│   ├── ownership_runtime.ts     # Phase 4: Ownership runtime
│   ├── ref_counting.ts
│   ├── async_runtime.ts         # Phase 5: Async
│   ├── coroutine.ts
│   ├── channel.ts
│   ├── simd_runtime.ts          # Phase 7: SIMD
│   └── v10_runtime/             # Phase 10: V10 runtime
│       ├── actor.ts
│       ├── distributed_gc.ts
│       ├── checkpoint.ts
│       └── metrics.ts
├── superbit/
│   ├── compression.py           # Phase 8: Enhanced encoding
│   └── lazy_decoder.py
└── docs/
    ├── null_v2_language_spec.md # This document
    ├── syntax_guide.md          # Syntax comparison
    ├── ownership_guide.md       # Ownership system guide
    └── migration_guide.md       # v1 → v2 migration
```

---

## Migration Strategy

### Coexistence Model

Both v1 (English) and v2 (Modern) syntax will coexist indefinitely, compiled by the same toolchain.

#### Syntax Selection

1. **File Extension**:
   - `.null` → v1 English syntax
   - `.null2` or `.nl` → v2 Modern syntax

2. **Pragma (alternative)**:
   ```null
   #syntax v2
   // Modern syntax follows...
   ```

3. **Mixed Mode**:
   ```null
   // v1 syntax by default
   SET x TO 42
   
   // Inline v2 block
   #syntax v2 {
       let y = x * 2
   }
   
   // Back to v1
   SHOW y
   ```

### Migration Tools

1. **Syntax Transpiler**: `nullc transpile v1_file.null --to v2 --output v2_file.nl`
   - Best-effort conversion
   - Marks areas needing manual review

2. **Compatibility Layer**: v1 libraries can be called from v2 code and vice versa
   - Unified ABI at bytecode level

3. **Gradual Typing**: Add v2 type annotations to v1 code incrementally

### Breaking Changes (v2 Only)

These changes apply **only** to v2 modern syntax, v1 syntax is unchanged:

- Ownership checking (compile errors for invalid borrows)
- Exhaustive pattern matching (non-exhaustive patterns are errors)
- Null safety (nullable types must be explicitly handled)
- Immutable by default (must use `mut` keyword for mutable variables)

### Deprecation Timeline

- **Years 1-2**: Both syntaxes fully supported, v2 in development
- **Years 3-5**: Both syntaxes production-ready, v1 maintenance mode
- **Years 6+**: v1 supported indefinitely for legacy code, new features v2-only

---

## Testing Strategy

### Unit Testing

**Scope**: Individual components in isolation

| Phase | Unit Test Focus | Tools |
|-------|----------------|-------|
| Phase 1 | Parser correctness, AST construction | pytest, Lark test harness |
| Phase 2 | Type checking, pattern exhaustiveness | pytest, property-based testing |
| Phase 3-4 | Borrow checker, lifetime inference | pytest, negative test cases |
| Phase 5 | Coroutine scheduling, channel operations | Jest, async test utilities |
| Phase 6 | Comprehension desugaring, null analysis | pytest, Jest |
| Phase 7 | SIMD correctness, vectorization | pytest, SIMD test suite |
| Phase 8 | Encoding round-trip, compression ratio | pytest, snapshot testing |
| Phase 9 | Tensor type checking, ML inference | Jest, pytest |
| Phase 10 | Actor system, distributed GC | Jest, mock distributed environment |

**Coverage Goal**: 90%+ line coverage, 80%+ branch coverage

### Integration Testing

**Scope**: End-to-end programs using multiple features

- **Fixture Programs**: Comprehensive programs in `fixtures/v2/` directory
- **Round-Trip Tests**: Parse → AST → Bytecode → Execute → Verify output
- **Cross-Syntax Tests**: Same program in v1 and v2 syntax produces identical results
- **Standard Library Tests**: All stdlib functions work with v2 features

**Coverage Goal**: All feature combinations tested

### Performance Testing

**Scope**: Benchmarking and profiling

| Metric | Target | Test Method |
|--------|--------|-------------|
| Parse Time | < 100ms for 10K line program | Benchmark suite |
| Type Check Time | < 500ms for 10K line program | Benchmark suite |
| Compilation Time | < 1s for 10K line program | Benchmark suite |
| Execution Speed | Within 2x of Python for similar code | Micro-benchmarks |
| SIMD Speedup | 4-8x for vectorizable code | SIMD-specific benchmarks |
| Async Throughput | 100K+ requests/sec | Load testing |
| Memory Overhead | < 10% vs. manual management | Memory profiler |

### Concurrency Testing

**Scope**: Race conditions, deadlocks, data races

- **ThreadSanitizer (TSan)**: Detect data races
- **Stress Tests**: 10K+ concurrent coroutines
- **Chaos Testing**: Random delays, failures
- **Linearizability Tests**: Verify concurrent data structure correctness

**Coverage Goal**: No data races, no deadlocks in test suite

### Compatibility Testing

**Scope**: Ensure v1 code continues to work

- **Regression Test Suite**: All existing v1 tests pass
- **Bytecode Compatibility**: v1 bytecode runs on v2 VM
- **Library Compatibility**: v1 libraries work with v2 code
- **Migration Tests**: Transpiler produces correct v2 code

### Cross-Platform Testing

**Platforms**:
- **OS**: Linux, macOS, Windows
- **Architecture**: x86_64, ARM64, WASM
- **SIMD**: SSE, AVX, AVX-512, NEON, SIMD128

**CI/CD**: GitHub Actions matrix build for all platform combinations

---

## Performance & Concurrency Goals

### Performance Targets

| Workload Type | Target Performance | Measurement |
|---------------|-------------------|-------------|
| **CPU-Bound** | 50-80% of optimized C/Rust | Benchmark vs. reference implementation |
| **I/O-Bound** | 90%+ of async runtime overhead | Throughput in requests/sec |
| **Memory-Bound** | Minimal allocation overhead | GC pause time, allocation rate |
| **SIMD Workloads** | 90%+ of hand-written SIMD | Speedup vs. scalar baseline |
| **ML Inference** | 95%+ of native library (PyTorch/TF) | Inference latency |

### Concurrency Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **Coroutines** | 10K+ concurrent coroutines | Lightweight green threads |
| **Channels** | 1M+ messages/sec | Lock-free MPSC |
| **Actor Throughput** | 100K+ messages/sec per actor | Local message passing |
| **Distributed Nodes** | 100+ nodes | V10 runtime scalability |
| **Fault Recovery** | < 1s recovery time | Node failure to full recovery |

### Optimization Levels

1. **Debug (-O0)**:
   - No optimizations
   - Full debug info
   - Ownership/borrow checking enabled

2. **Release (-O2)**:
   - Standard optimizations
   - Inlining, constant folding, DCE
   - SIMD auto-vectorization

3. **Aggressive (-O3)**:
   - Aggressive optimizations
   - Cross-function inlining
   - Profile-guided optimization

4. **Size (-Os)**:
   - Optimize for binary size
   - Super-Bit compression enabled

---

## Open Questions & Assumptions

### Open Questions

1. **Ownership System Complexity**:
   - Q: Should we simplify lifetimes compared to Rust (e.g., fewer explicit annotations)?
   - A: TBD - user testing in Phase 3 will inform this

2. **SIMD Portability**:
   - Q: How to handle platforms without SIMD support gracefully?
   - A: Fallback to scalar code, possibly with compile-time detection

3. **Backward Compatibility**:
   - Q: At what point do we allow breaking changes to v1 bytecode format?
   - A: Never for v1, but v2 bytecode can evolve with versioning

4. **JIT Compilation**:
   - Q: Is Tier-1 JIT necessary, or is bytecode interpreter sufficient?
   - A: TBD - benchmark in Phase 7, add JIT only if < 50% of C performance

5. **Language Server Protocol (LSP)**:
   - Q: Should we implement LSP for IDE integration?
   - A: High priority but not in critical path - can be Phase 11

6. **Interop with Other Languages**:
   - Q: Should we support FFI to C/Rust/Python?
   - A: Yes, but not in v2 scope - plan for Phase 12

### Assumptions

1. **TypeScript VM**: We assume TypeScript VM remains the primary runtime, with optional Rust rewrite later for performance
2. **Python Compiler**: Python remains the compiler implementation language for Phase 1-8
3. **Single-Threaded Initially**: Phases 1-4 assume single-threaded execution, parallelism added in Phase 5
4. **Super-Bit Encoding**: Super-Bit encoding remains core differentiator, enhanced but not replaced
5. **Gradual Rollout**: v2 features can be developed incrementally without big-bang release
6. **User Feedback**: Major syntax decisions (e.g., keyword choices) subject to community input

### Known Limitations

1. **Performance**: Bytecode interpreter will be slower than JIT/AOT compiled languages initially
2. **Ecosystem**: Limited third-party libraries until v2 is stable
3. **Tooling**: IDE support will lag language features by 6-12 months
4. **Documentation**: Comprehensive docs will take 12+ months to complete
5. **Production Readiness**: Phase 10 required before production use at scale

---

## Implementation Checklist

### Phase 1: Foundation & Dual Parser

- [ ] Design v2 grammar (modern syntax)
- [ ] Implement v2 parser (Lark-based)
- [ ] Create unified AST representation
- [ ] Implement syntax router (file extension/pragma)
- [ ] Update lexer for new keywords
- [ ] Write comprehensive parser tests
- [ ] Create syntax highlighting definitions (VSCode, Vim)
- [ ] Write syntax comparison documentation

**Estimated Effort**: 2 months, 1 engineer

---

### Phase 2: Type System Enhancements

- [ ] Design sealed class hierarchy
- [ ] Implement sealed class codegen
- [ ] Design data class with auto-generated methods
- [ ] Implement data class codegen
- [ ] Implement union types in type system
- [ ] Add pattern matching AST nodes
- [ ] Implement pattern exhaustiveness checker
- [ ] Implement pattern matching compiler
- [ ] Add VM opcodes for pattern matching
- [ ] Enhance type inference engine
- [ ] Write type system tests
- [ ] Document type system features

**Estimated Effort**: 3 months, 1-2 engineers

---

### Phase 3: Ownership System - Analysis

- [ ] Design ownership annotation syntax
- [ ] Extend AST for ownership annotations
- [ ] Implement borrow checker
- [ ] Implement lifetime inference
- [ ] Implement move tracking
- [ ] Implement region analysis
- [ ] Generate ownership error messages
- [ ] Write borrow checker tests (positive/negative cases)
- [ ] Document ownership system

**Estimated Effort**: 3 months, 1-2 engineers

---

### Phase 4: Ownership System - Runtime

- [ ] Design runtime ownership model
- [ ] Implement reference counting
- [ ] Implement automatic drop/destructor
- [ ] Add MOVE, BORROW, DROP opcodes
- [ ] Implement inline types (monomorphization)
- [ ] Implement context receivers
- [ ] Optimize move operations in bytecode
- [ ] Write ownership runtime tests
- [ ] Memory leak testing
- [ ] Performance benchmarking

**Estimated Effort**: 2 months, 1-2 engineers

---

### Phase 5: Async Runtime & Coroutines

- [ ] Design async/await syntax
- [ ] Implement async AST nodes
- [ ] Implement coroutine runtime (green threads)
- [ ] Implement coroutine scheduler
- [ ] Implement channel types (MPSC, SPSC, broadcast)
- [ ] Add async opcodes (ASYNC_BEGIN, AWAIT, YIELD, SPAWN)
- [ ] Implement async I/O layer
- [ ] Implement structured concurrency
- [ ] Write async runtime tests
- [ ] Concurrency testing (race detection)
- [ ] Async standard library (networking, file I/O)
- [ ] Document async programming model

**Estimated Effort**: 3 months, 2 engineers

---

### Phase 6: Modern Language Features

- [ ] Implement comprehension syntax
- [ ] Implement comprehension desugaring
- [ ] Implement pipeline operator
- [ ] Implement null-safety operators
- [ ] Implement null analysis pass
- [ ] Implement operator overloading
- [ ] Implement extension methods
- [ ] Enhance string interpolation
- [ ] Write feature tests
- [ ] Performance benchmarking (comprehensions vs. loops)
- [ ] Document modern features

**Estimated Effort**: 2 months, 1 engineer

---

### Phase 7: SIMD & Performance Optimizations

- [ ] Design SIMD vector types
- [ ] Implement SIMD intrinsics
- [ ] Implement SIMD runtime support
- [ ] Implement auto-vectorization pass
- [ ] Add SIMD opcodes
- [ ] Implement zero-cost abstractions (monomorphization)
- [ ] Implement compile-time function evaluation
- [ ] Implement profile-guided optimization
- [ ] Write SIMD tests (correctness)
- [ ] Cross-platform testing (x86, ARM, WASM)
- [ ] Performance benchmarking
- [ ] Document SIMD programming

**Estimated Effort**: 2 months, 1-2 engineers

---

### Phase 8: Enhanced Super-Bit Encoding

- [ ] Update encoder for v2 AST nodes
- [ ] Implement advanced compression (LZ4, Zstd)
- [ ] Implement lazy decoding
- [ ] Implement delta encoding
- [ ] Design bytecode versioning scheme
- [ ] Implement v1 → v2 bytecode migration
- [ ] Write encoding tests
- [ ] Compression benchmarking
- [ ] Backward compatibility tests
- [ ] Document bytecode format v2

**Estimated Effort**: 2 months, 1 engineer

---

### Phase 9: AI/ML Integration Enhancements

- [ ] Design tensor types in type system
- [ ] Implement tensor type checking
- [ ] Enhance AI opcodes with type safety
- [ ] Implement knowledge graph query DSL
- [ ] Integrate query DSL with type system
- [ ] Implement automatic differentiation
- [ ] Implement GPU backend (CUDA)
- [ ] Implement GPU backend (Metal)
- [ ] Implement GPU backend (WebGPU)
- [ ] Write ML integration tests
- [ ] Performance benchmarking (GPU vs. CPU)
- [ ] Document AI/ML programming

**Estimated Effort**: 2 months, 1-2 engineers

---

### Phase 10: V10 Runtime - Production Hardening

- [ ] Enhance work-stealing scheduler
- [ ] Implement actor system
- [ ] Implement actor supervision
- [ ] Implement distributed garbage collection
- [ ] Implement checkpointing system
- [ ] Implement replay/recovery
- [ ] Implement metrics collection
- [ ] Implement distributed tracing
- [ ] Implement profiling hooks
- [ ] Implement hot code reloading
- [ ] Create deployment CLI tools
- [ ] Write distributed tests
- [ ] Fault tolerance tests
- [ ] Chaos testing
- [ ] Scalability benchmarking (100+ nodes)
- [ ] Production deployment guides

**Estimated Effort**: 4 months, 2-3 engineers

---

## Timeline Summary

| Phase | Duration | Engineers | Dependencies |
|-------|----------|-----------|--------------|
| Phase 1: Foundation & Dual Parser | 2 months | 1 | None |
| Phase 2: Type System Enhancements | 3 months | 1-2 | Phase 1 |
| Phase 3: Ownership - Analysis | 3 months | 1-2 | Phase 2 |
| Phase 4: Ownership - Runtime | 2 months | 1-2 | Phase 3 |
| Phase 5: Async Runtime | 3 months | 2 | Phase 1-2 |
| Phase 6: Modern Features | 2 months | 1 | Phase 2 |
| Phase 7: SIMD & Performance | 2 months | 1-2 | Phase 4 |
| Phase 8: Super-Bit v2 | 2 months | 1 | Phase 1-7 |
| Phase 9: AI/ML Enhancements | 2 months | 1-2 | Phase 2, 7 |
| Phase 10: V10 Runtime | 4 months | 2-3 | Phase 5, 8 |

**Total Duration**: 20-24 months (with parallelization)  
**Team Size**: 2-3 engineers average

### Phase Dependency Diagram

```
Timeline (Months)
0    2    4    6    8   10   12   14   16   18   20   22   24
├────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤
│
│ Phase 1: Parser & AST
├──────────►
│           │
│           │ Phase 2: Type System (sealed, data, union, match)
│           ├───────────────►
│           │               │
│           │               │ Phase 3: Ownership Analysis
│           │               ├───────────────►
│           │               │               │
│           │               │               │ Phase 4: Ownership Runtime
│           │               │               ├──────────►
│           │               │               │           │
│           │               │               │           │ Phase 7: SIMD
│           │               │               │           ├──────────►
│           │                                                       │
│           │ Phase 5: Async/Coroutines                            │
│           ├───────────────────────►                              │
│           │                       │                              │
│           │ Phase 6: Modern Features                             │
│           ├──────────────►        │                              │
│                                   │                              │
│                                   │ Phase 8: Super-Bit v2        │
│                                   ├──────────────────────────────►
│           │                       │                              │
│           │ Phase 9: AI/ML        │                              │
│           ├──────────────►        │                              │
│                                   │                              │
│                                   │ Phase 10: V10 Runtime        │
│                                   ├──────────────────────────────────────►
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                                                   Production
                                                                   Ready
```

**Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 7 → Phase 8  
**Parallel Tracks**: Phases 5, 6, 9 can proceed in parallel with ownership work

---

## Appendix A: Syntax Examples

### Complete Example: v1 vs. v2

**v1 English Syntax:**
```null
# User management system
SET users TO []

DEFINE add_user WITH name, email
    IF email IS NOT NULL THEN
        SET user TO { name: name, email: email, active: TRUE }
        ADD user TO users
        SHOW "User added: " PLUS name
    ELSE
        SHOW "Email required"
    END IF
END DEFINE

REPEAT 3 TIMES
    CALL add_user WITH "Alice", "alice@example.com"
END REPEAT

SHOW users
```

**v2 Modern Syntax:**
```null
// User management system
let mut users: Vec<User> = vec![]

data class User(name: Text, email: Text, active: Bool)

fn add_user(name: Text, email: Text?) -> Result<Unit> {
    match email {
        Some(e) => {
            let user = User(name, e, true)
            users.push(user)
            println("User added: {name}")
            Ok(())
        },
        None => Err("Email required")
    }
}

for i in 0..3 {
    add_user("Alice", Some("alice@example.com"))?
}

println(users)
```

---

## Appendix B: Glossary

- **AST**: Abstract Syntax Tree - tree representation of source code
- **Borrow Checker**: Compiler component that enforces ownership rules
- **Bytecode**: Low-level instructions executed by the VM
- **Coroutine**: Lightweight, cooperative thread (green thread)
- **DCE**: Dead Code Elimination - optimization removing unused code
- **FFI**: Foreign Function Interface - calling code from other languages
- **IR**: Intermediate Representation - internal compiler format
- **JIT**: Just-In-Time compilation - runtime compilation for performance
- **Monomorphization**: Generating specialized code for generic functions
- **MPSC**: Multi-Producer, Single-Consumer (channel type)
- **SIMD**: Single Instruction, Multiple Data - vectorized operations
- **Super-Bit**: Null's compact encoding format (4-8 bits per token)
- **V10 Runtime**: Null's distributed execution runtime

---

## Appendix C: References

### Related Documents

- **[Implementation Issues & TODOs](../ISSUES_V2.md)** - Comprehensive task list for implementing v2 features
- **[Current Architecture](../ARCHITECTURE.md)** - v1 architecture and compilation pipeline
- **[README](../README.md)** - Project overview and quick start

### Language Design Inspirations

- **Rust**: Ownership system, borrow checker, pattern matching
- **Kotlin**: Data classes, sealed classes, null safety, coroutines
- **Go**: Channels, goroutines, simplicity
- **Python**: Comprehensions, readable syntax
- **F#**: Pipeline operator, functional features
- **Swift**: Protocol-oriented programming, value semantics

### Technical References

- [Rust Ownership Model](https://doc.rust-lang.org/book/ch04-00-understanding-ownership.html)
- [Kotlin Coroutines](https://kotlinlang.org/docs/coroutines-overview.html)
- [Pattern Matching Compilation](https://julesjacobs.com/notes/patternmatching/patternmatching.pdf)
- [SIMD Programming Guide](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html)
- [Actor Model](https://en.wikipedia.org/wiki/Actor_model)
- [Type Inference Algorithm](https://en.wikipedia.org/wiki/Hindley%E2%80%93Milner_type_system)

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Next Review**: After Phase 1 completion  
**Status**: Blueprint/Roadmap

For implementation tasks and issues, see [ISSUES_V2.md](../ISSUES_V2.md)
