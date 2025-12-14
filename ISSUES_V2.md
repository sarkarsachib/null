# Null v2 Implementation Issues & TODOs

This document tracks all issues, tasks, and open questions for implementing Null v2 as defined in the [Null v2 Language Specification](docs/null_v2_language_spec.md).

---

## Phase 1: Foundation & Dual Parser (Months 1-2)

### High Priority

- [ ] **[PARSER-001]** Design v2 grammar for modern syntax (keywords, operators, structural forms)
- [ ] **[PARSER-002]** Implement v2 Lark grammar file (`src/null_system/lang/v2_grammar.lark`)
- [ ] **[PARSER-003]** Create unified AST representation supporting both v1 and v2 features
- [ ] **[PARSER-004]** Implement syntax router to detect and route between v1/v2 parsers
- [ ] **[PARSER-005]** Add new keywords to lexer: `fn`, `let`, `mut`, `match`, `async`, `await`, etc.
- [ ] **[PARSER-006]** Write comprehensive parser tests (>100 test cases)

### Medium Priority

- [ ] **[PARSER-007]** Create VSCode syntax highlighting extension for v2 syntax
- [ ] **[PARSER-008]** Create Vim syntax file for v2 syntax
- [ ] **[PARSER-009]** Write syntax comparison documentation (`docs/syntax_guide.md`)
- [ ] **[PARSER-010]** Add pragma support for inline syntax switching (`#syntax v2`)

### Open Questions

- **[Q-PARSER-001]**: Should we use `.null2`, `.nl`, or pragma for v2 syntax detection?
- **[Q-PARSER-002]**: Should v2 syntax be case-sensitive (unlike v1 English)?
- **[Q-PARSER-003]**: How should we handle syntax errors that are ambiguous between v1/v2?

---

## Phase 2: Type System Enhancements (Months 3-5)

### High Priority

- [ ] **[TYPE-001]** Design sealed class hierarchy system with compile-time closure
- [ ] **[TYPE-002]** Implement sealed class codegen and inheritance checking
- [ ] **[TYPE-003]** Design data class with auto-generated methods (equals, hashCode, toString, copy)
- [ ] **[TYPE-004]** Implement data class codegen and method synthesis
- [ ] **[TYPE-005]** Implement union types (`A | B`) in type checker
- [ ] **[TYPE-006]** Add pattern matching AST nodes (match expression, case arms, guards)
- [ ] **[TYPE-007]** Implement pattern exhaustiveness checker
- [ ] **[TYPE-008]** Implement pattern matching compiler (decision tree generation)
- [ ] **[TYPE-009]** Add VM opcodes: MATCH_BEGIN, MATCH_CASE, MATCH_GUARD, MATCH_END
- [ ] **[TYPE-010]** Enhance type inference engine (Hindley-Milner algorithm)

### Medium Priority

- [ ] **[TYPE-011]** Implement type narrowing in match arms
- [ ] **[TYPE-012]** Add support for nested patterns
- [ ] **[TYPE-013]** Implement destructuring in pattern matching
- [ ] **[TYPE-014]** Add warning for unreachable patterns
- [ ] **[TYPE-015]** Document type system features and examples

### Low Priority

- [ ] **[TYPE-016]** Optimize pattern matching with jump tables for simple cases
- [ ] **[TYPE-017]** Add pattern matching profiler to identify hot paths

### Open Questions

- **[Q-TYPE-001]**: Should sealed classes allow private inheritance from within the module?
- **[Q-TYPE-002]**: Should data classes be immutable by default or mutable?
- **[Q-TYPE-003]**: How deep should pattern matching nesting be allowed (recursion limit)?

---

## Phase 3: Ownership System - Analysis (Months 6-8)

### High Priority

- [ ] **[OWN-001]** Design ownership annotation syntax (own, borrow, borrow_mut, move)
- [ ] **[OWN-002]** Extend AST for lifetime and ownership annotations
- [ ] **[OWN-003]** Implement borrow checker (multi-pass analysis)
- [ ] **[OWN-004]** Implement lifetime inference algorithm
- [ ] **[OWN-005]** Implement move tracking (linear type tracking)
- [ ] **[OWN-006]** Implement region-based analysis for stack/heap allocation
- [ ] **[OWN-007]** Generate clear error messages with suggestions (inspired by rustc)
- [ ] **[OWN-008]** Write comprehensive borrow checker tests (positive and negative cases)

### Medium Priority

- [ ] **[OWN-009]** Implement non-lexical lifetimes (NLL) for better ergonomics
- [ ] **[OWN-010]** Add support for interior mutability patterns (Cell, RefCell equivalents)
- [ ] **[OWN-011]** Implement weak references for breaking ownership cycles
- [ ] **[OWN-012]** Document ownership system with examples and common patterns

### Low Priority

- [ ] **[OWN-013]** Add ownership visualization tool (graphical representation of borrows)
- [ ] **[OWN-014]** Implement lifetime elision rules to reduce annotations

### Open Questions

- **[Q-OWN-001]**: Should we simplify lifetimes compared to Rust (fewer explicit annotations)?
- **[Q-OWN-002]**: How should we handle FFI boundaries (ownership transfer to/from external code)?
- **[Q-OWN-003]**: Should we support implicit move or require explicit `move` keyword?

---

## Phase 4: Ownership System - Runtime (Months 9-10)

### High Priority

- [ ] **[RT-OWN-001]** Design runtime ownership model (reference counting vs. tracing GC)
- [ ] **[RT-OWN-002]** Implement reference counting for owned values
- [ ] **[RT-OWN-003]** Implement automatic drop/destructor calls at scope exit
- [ ] **[RT-OWN-004]** Add VM opcodes: MOVE, BORROW, BORROW_MUT, DROP, INCREF, DECREF
- [ ] **[RT-OWN-005]** Implement inline types (monomorphization pass)
- [ ] **[RT-OWN-006]** Implement context receivers (implicit parameter passing)
- [ ] **[RT-OWN-007]** Optimize move operations in bytecode (eliminate unnecessary copies)
- [ ] **[RT-OWN-008]** Write ownership runtime tests
- [ ] **[RT-OWN-009]** Run memory leak testing (Valgrind, AddressSanitizer)
- [ ] **[RT-OWN-010]** Performance benchmark ownership overhead (should be < 10%)

### Medium Priority

- [ ] **[RT-OWN-011]** Implement cycle detection for reference counting
- [ ] **[RT-OWN-012]** Add arena allocator for bulk allocations
- [ ] **[RT-OWN-013]** Implement stack allocation optimization
- [ ] **[RT-OWN-014]** Document runtime ownership behavior

### Open Questions

- **[Q-RT-OWN-001]**: Should we use pure reference counting or hybrid RC+GC?
- **[Q-RT-OWN-002]**: How to handle destructors that may fail (exceptions in drop)?
- **[Q-RT-OWN-003]**: Should we support custom allocators per type?

---

## Phase 5: Async Runtime & Coroutines (Months 11-13)

### High Priority

- [ ] **[ASYNC-001]** Design async/await syntax and semantics
- [ ] **[ASYNC-002]** Implement async function AST nodes
- [ ] **[ASYNC-003]** Implement coroutine runtime (green thread scheduler)
- [ ] **[ASYNC-004]** Implement coroutine scheduler (work-stealing or round-robin)
- [ ] **[ASYNC-005]** Implement channel types: MPSC, SPSC, broadcast
- [ ] **[ASYNC-006]** Add VM opcodes: ASYNC_BEGIN, AWAIT, YIELD, SPAWN, CHANNEL_SEND, CHANNEL_RECV
- [ ] **[ASYNC-007]** Implement async I/O layer (file, network, timers)
- [ ] **[ASYNC-008]** Implement structured concurrency (task scopes)
- [ ] **[ASYNC-009]** Write async runtime tests
- [ ] **[ASYNC-010]** Run concurrency testing with ThreadSanitizer
- [ ] **[ASYNC-011]** Build async standard library (fs, net, time)
- [ ] **[ASYNC-012]** Document async programming model

### Medium Priority

- [ ] **[ASYNC-013]** Implement async generators (async iteration)
- [ ] **[ASYNC-014]** Add timeout and cancellation support
- [ ] **[ASYNC-015]** Implement select! macro for multiple channel operations
- [ ] **[ASYNC-016]** Add async tracing and profiling hooks

### Low Priority

- [ ] **[ASYNC-017]** Optimize coroutine stack size (lazy growth)
- [ ] **[ASYNC-018]** Add support for async drop (cleanup in async context)

### Open Questions

- **[Q-ASYNC-001]**: Should coroutines have bounded or unbounded queues?
- **[Q-ASYNC-002]**: How should we handle async errors (panic vs. Result)?
- **[Q-ASYNC-003]**: Should we support actor model in addition to async/await?

---

## Phase 6: Modern Language Features (Months 14-15)

### High Priority

- [ ] **[FEAT-001]** Implement list comprehension syntax
- [ ] **[FEAT-002]** Implement dict comprehension syntax
- [ ] **[FEAT-003]** Implement set comprehension syntax
- [ ] **[FEAT-004]** Implement comprehension desugaring to loops
- [ ] **[FEAT-005]** Implement pipeline operator (`|>`) syntax
- [ ] **[FEAT-006]** Implement pipeline desugaring to nested calls
- [ ] **[FEAT-007]** Implement null-safety operators (`?.`, `?:`, `!!`)
- [ ] **[FEAT-008]** Implement null analysis pass (definite assignment)
- [ ] **[FEAT-009]** Implement operator overloading (AST + codegen)
- [ ] **[FEAT-010]** Implement extension methods (module-scoped)
- [ ] **[FEAT-011]** Enhance string interpolation (expressions in strings)
- [ ] **[FEAT-012]** Write feature tests
- [ ] **[FEAT-013]** Performance benchmark comprehensions vs. hand-written loops

### Medium Priority

- [ ] **[FEAT-014]** Add range syntax (`0..10`, `0..=10`)
- [ ] **[FEAT-015]** Implement iterator protocol
- [ ] **[FEAT-016]** Document modern features with examples

### Open Questions

- **[Q-FEAT-001]**: Should pipeline operator be left-to-right or right-to-left?
- **[Q-FEAT-002]**: Should null-safety be opt-in or opt-out?

---

## Phase 7: SIMD & Performance Optimizations (Months 16-17)

### High Priority

- [ ] **[SIMD-001]** Design SIMD vector types (f32x4, i32x8, etc.)
- [ ] **[SIMD-002]** Implement platform-specific SIMD intrinsics
- [ ] **[SIMD-003]** Implement SIMD runtime support in VM
- [ ] **[SIMD-004]** Implement auto-vectorization pass in optimizer
- [ ] **[SIMD-005]** Add VM opcodes: SIMD_LOAD, SIMD_STORE, SIMD_ADD, SIMD_MUL, etc.
- [ ] **[SIMD-006]** Implement zero-cost abstractions (monomorphization)
- [ ] **[SIMD-007]** Implement compile-time function evaluation (`const fn`)
- [ ] **[SIMD-008]** Implement profile-guided optimization (PGO)
- [ ] **[SIMD-009]** Write SIMD correctness tests
- [ ] **[SIMD-010]** Cross-platform testing (x86 SSE/AVX, ARM NEON, WASM SIMD128)
- [ ] **[SIMD-011]** Performance benchmarking (target: 4-8x speedup for vectorizable code)
- [ ] **[SIMD-012]** Document SIMD programming guide

### Medium Priority

- [ ] **[SIMD-013]** Implement SIMD horizontal operations (sum, min, max)
- [ ] **[SIMD-014]** Add SIMD gather/scatter operations
- [ ] **[SIMD-015]** Implement portable SIMD library (fallback for unsupported platforms)

### Open Questions

- **[Q-SIMD-001]**: How to handle platforms without SIMD gracefully (runtime detection vs. compile-time)?
- **[Q-SIMD-002]**: Should we support custom SIMD widths or stick to standard sizes?

---

## Phase 8: Enhanced Super-Bit Encoding (Months 16-17)

### High Priority

- [ ] **[ENC-001]** Update encoder for all v2 AST nodes
- [ ] **[ENC-002]** Integrate LZ4 compression library
- [ ] **[ENC-003]** Integrate Zstd compression library
- [ ] **[ENC-004]** Implement lazy decoding (decode on demand)
- [ ] **[ENC-005]** Implement delta encoding for similar programs
- [ ] **[ENC-006]** Design bytecode versioning scheme (major.minor)
- [ ] **[ENC-007]** Implement v1 → v2 bytecode migration tool
- [ ] **[ENC-008]** Write encoding/decoding round-trip tests
- [ ] **[ENC-009]** Benchmark compression ratio (target: 20-30% reduction)
- [ ] **[ENC-010]** Benchmark decode speed (target: 50% startup time reduction with lazy decoding)
- [ ] **[ENC-011]** Ensure backward compatibility (v2 VM runs v1 bytecode)
- [ ] **[ENC-012]** Document bytecode format v2

### Medium Priority

- [ ] **[ENC-013]** Implement streaming compression for large programs
- [ ] **[ENC-014]** Add bytecode verification pass (detect corruption)
- [ ] **[ENC-015]** Implement bytecode signing for integrity

### Open Questions

- **[Q-ENC-001]**: Should compression be always-on or opt-in?
- **[Q-ENC-002]**: How to handle bytecode incompatibilities across minor versions?

---

## Phase 9: AI/ML Integration Enhancements (Months 18-19)

### High Priority

- [ ] **[ML-001]** Design tensor types in type system (shapes, dtypes)
- [ ] **[ML-002]** Implement tensor type checking (shape inference)
- [ ] **[ML-003]** Enhance AI opcodes with type safety
- [ ] **[ML-004]** Design knowledge graph query DSL syntax
- [ ] **[ML-005]** Implement KG query parser and compiler
- [ ] **[ML-006]** Integrate KG queries with type system
- [ ] **[ML-007]** Implement automatic differentiation (forward and reverse mode)
- [ ] **[ML-008]** Implement CUDA backend for GPU acceleration
- [ ] **[ML-009]** Implement Metal backend (macOS GPU)
- [ ] **[ML-010]** Implement WebGPU backend (browser GPU)
- [ ] **[ML-011]** Write ML integration tests
- [ ] **[ML-012]** Performance benchmarking (GPU vs. CPU, target: 10-100x speedup)
- [ ] **[ML-013]** Document AI/ML programming guide

### Medium Priority

- [ ] **[ML-014]** Add support for quantized models (int8, int4)
- [ ] **[ML-015]** Implement model serialization format
- [ ] **[ML-016]** Add neural architecture search (NAS) support

### Open Questions

- **[Q-ML-001]**: Should tensor shapes be checked at compile-time or runtime?
- **[Q-ML-002]**: How to handle model versioning and migration?
- **[Q-ML-003]**: Should we support custom GPU kernels?

---

## Phase 10: V10 Runtime - Production Hardening (Months 20-24)

### High Priority

- [ ] **[V10-001]** Enhance work-stealing scheduler (NUMA awareness)
- [ ] **[V10-002]** Implement actor system (mailbox, supervision)
- [ ] **[V10-003]** Implement actor supervision strategies (one-for-one, one-for-all)
- [ ] **[V10-004]** Implement distributed garbage collection
- [ ] **[V10-005]** Implement checkpointing system (full state snapshot)
- [ ] **[V10-006]** Implement replay/recovery from checkpoints
- [ ] **[V10-007]** Implement metrics collection (Prometheus format)
- [ ] **[V10-008]** Implement distributed tracing (OpenTelemetry)
- [ ] **[V10-009]** Implement profiling hooks (flamegraphs)
- [ ] **[V10-010]** Implement hot code reloading (zero-downtime updates)
- [ ] **[V10-011]** Create deployment CLI tools (deploy, scale, rollback)
- [ ] **[V10-012]** Write distributed system tests
- [ ] **[V10-013]** Write fault tolerance tests
- [ ] **[V10-014]** Implement chaos testing framework
- [ ] **[V10-015]** Scalability benchmarking (target: 100+ nodes)
- [ ] **[V10-016]** Write production deployment guides

### Medium Priority

- [ ] **[V10-017]** Implement service mesh integration (Istio, Linkerd)
- [ ] **[V10-018]** Add Kubernetes operator for deployment
- [ ] **[V10-019]** Implement distributed consensus (Raft or Paxos)
- [ ] **[V10-020]** Add multi-region support

### Low Priority

- [ ] **[V10-021]** Implement automatic performance tuning
- [ ] **[V10-022]** Add anomaly detection for metrics

### Open Questions

- **[Q-V10-001]**: Should we use custom protocol or gRPC for inter-node communication?
- **[Q-V10-002]**: How to handle network partitions (CAP theorem trade-offs)?
- **[Q-V10-003]**: Should hot code reloading be automatic or manual?

---

## Cross-Cutting Concerns

### Tooling & Infrastructure

- [ ] **[TOOL-001]** Implement Language Server Protocol (LSP) for IDE support
- [ ] **[TOOL-002]** Create debugger with breakpoints and step execution
- [ ] **[TOOL-003]** Implement REPL for interactive development
- [ ] **[TOOL-004]** Create package manager for libraries
- [ ] **[TOOL-005]** Build documentation generator from code comments
- [ ] **[TOOL-006]** Create formatter (like rustfmt, gofmt)
- [ ] **[TOOL-007]** Implement linter for code quality checks
- [ ] **[TOOL-008]** Build playground for online code execution

### Documentation

- [ ] **[DOC-001]** Write comprehensive language reference
- [ ] **[DOC-002]** Create tutorial series (beginner to advanced)
- [ ] **[DOC-003]** Write migration guide (v1 → v2)
- [ ] **[DOC-004]** Create ownership system guide with examples
- [ ] **[DOC-005]** Write async programming guide
- [ ] **[DOC-006]** Document performance best practices
- [ ] **[DOC-007]** Create API documentation for standard library

### Testing & Quality

- [ ] **[TEST-001]** Set up continuous integration (GitHub Actions)
- [ ] **[TEST-002]** Implement fuzzing for parser and compiler
- [ ] **[TEST-003]** Add property-based testing (QuickCheck-style)
- [ ] **[TEST-004]** Create benchmark suite for performance tracking
- [ ] **[TEST-005]** Implement mutation testing for test quality
- [ ] **[TEST-006]** Add differential testing (compare v1 vs. v2 output)

### Performance

- [ ] **[PERF-001]** Profile compilation pipeline for bottlenecks
- [ ] **[PERF-002]** Optimize parser performance (incremental parsing)
- [ ] **[PERF-003]** Optimize type checker performance (caching)
- [ ] **[PERF-004]** Implement parallel compilation
- [ ] **[PERF-005]** Add JIT compilation tier (Phase 11+)

### Security

- [ ] **[SEC-001]** Implement sandboxing for untrusted code
- [ ] **[SEC-002]** Add code signing and verification
- [ ] **[SEC-003]** Implement secure module system
- [ ] **[SEC-004]** Conduct security audit of ownership system
- [ ] **[SEC-005]** Add SAST (static analysis security testing)

---

## Known Limitations & Technical Debt

1. **[DEBT-001]** TypeScript VM may need rewrite in Rust for production performance
2. **[DEBT-002]** Python compiler may need rewrite for better performance
3. **[DEBT-003]** Error recovery in parser is limited (single-error mode)
4. **[DEBT-004]** Type inference may not handle complex recursive types
5. **[DEBT-005]** Ownership system may be too strict initially (need user feedback)
6. **[DEBT-006]** Async runtime may not handle backpressure well
7. **[DEBT-007]** SIMD support may be incomplete on some platforms
8. **[DEBT-008]** Distributed runtime may not handle Byzantine failures

---

## Issue Labels

Use these labels to categorize issues:

- **Priority**: `P0-critical`, `P1-high`, `P2-medium`, `P3-low`
- **Phase**: `phase-1` through `phase-10`
- **Type**: `bug`, `feature`, `enhancement`, `documentation`, `testing`, `performance`
- **Status**: `todo`, `in-progress`, `blocked`, `review`, `done`
- **Area**: `parser`, `types`, `ownership`, `async`, `simd`, `encoding`, `ml`, `runtime`

---

## Contributing

When working on v2 implementation:

1. Reference the issue ID in commit messages (e.g., `[PARSER-001] Implement v2 grammar`)
2. Update this file when issues are resolved
3. Add new issues as they are discovered
4. Link pull requests to relevant issues
5. Update the [Null v2 Language Specification](docs/null_v2_language_spec.md) when designs change

---

**Last Updated**: December 2024  
**Next Review**: After Phase 1 completion
