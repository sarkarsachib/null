# Architecture

The authoritative description of how Null is put together **today**. The root
[`ARCHITECTURE.md`](../ARCHITECTURE.md) describes only the Python pipeline and
predates the bootstrap chain; this document supersedes it as the overall picture
and links to the audit for per-subsystem verdicts.

## There are two pipelines

This is the most important fact about the codebase.

```
PIPELINE A — Python toolchain (produces super-bit binaries, executes on a Python VM)

  source
    → lark grammar (grammar.lark / modern_rust.lark / modern_python.lark)
    → AST (ast_nodes.py)
    → validator (ast/validator.py)
    → super-bit emitter (superbit/emitter.py)      [BROKEN: string opcodes]
    → optimizer (compiler/optimization.py)          [BROKEN: stale token API]
    → binary generator (binary/generator.py)        [BROKEN: calls to_bytes()]
    → NullVM (vm/vm.py)  or  TypeScript NullVM      [TS: 97 type errors]


PIPELINE B — Bootstrap chain (produces native executables)

  source
    → bootstrap/lexer.null        (or inlined in emitter.null)
    → bootstrap/emitter.null      parser + IR emitter
    → bootstrap/program.ir
    → bootstrap/native.null       x86-64 codegen
    → bootstrap/program.s
    → cc -O0
    → executable
```

Only Pipeline B reaches machine code, and only Pipeline B is exercised by the
fixed-point check. Pipeline A is where the tests live (959 of 1,016 pass) but its
binary-generation path raises on the first encode.

Both target the **same IR**. `bootstrap/ir.null` and
`src/null_system/superbit/ir.py` agree on all 53 opcode numbers.

## Layer map

| Layer | Pipeline A | Pipeline B |
| --- | --- | --- |
| Front end | `src/null_system/lang/` (3 grammars, 3,973 LOC) | `bootstrap/lexer.null`, `bootstrap/emitter.null` (3,200 LOC) |
| AST | `src/null_system/lang/ast_nodes.py`, `ast/` (303 LOC) | unified AST inside `emitter.null` |
| Validation | `src/null_system/ast/validator.py`, `analysis/type_inference.py` (387 LOC) | none — dynamically typed |
| IR | `src/null_system/superbit/` (1,643 LOC) | `bootstrap/ir.null` (311 LOC) |
| Optimization | `src/null_system/compiler/optimization.py` (898 LOC) | none |
| Backend | `src/null_system/binary/generator.py` (130 LOC) | `bootstrap/native.null` (4,363 LOC) |
| Runtime | `src/null_system/vm/vm.py` (480 LOC), `vm/` TS (18,856 LOC) | inline asm in `native.null`, `bootstrap/vm.null` (715 LOC) |
| Stdlib | `src/null_system/lib/` (1,328 LOC Python) | none — builtins only |
| Toolchain | `src/null_system/cli.py` (typer) | `bench/stage_runner.py` (Python) |

## Data formats

### Source

Four surface syntaxes, described in
[`LANGUAGE_SPECIFICATION.md`](LANGUAGE_SPECIFICATION.md). Only the bootstrap
surface (Rust-shaped: `fn`, `let`, `match`, `->`) reaches the native backend.

### Super-bit IR

TSV text:

```
IR	<opcode>	<operand>	<layer>[	<meta>]
LABEL	<name>
```

53 opcodes, layers `scalar` / `simd` / `lang` / `control` / `match`. Full table in
[`ARCHITECTURE_AUDIT.md`](ARCHITECTURE_AUDIT.md) § The IR.

### Native assembly

GNU `as`, Intel syntax, System V AMD64. Value representation: 64-bit words,
strings tagged with bit 62, arrays with bit 63, mask `0x3fffffffffffffff`. Array
header is `[cap][len][elem0]…` with the tagged pointer aimed at `len`. See
[`NATIVE_RUNTIME.md`](NATIVE_RUNTIME.md).

### Binary frames (Pipeline A only)

`binary/generator.py` writes a header with magic `"NULL"` plus a version, then
encodes the super-bit stream via `SuperBitIRStream.to_bytes()`. That call raises
`ValueError: invalid literal for int() … 'BINARY_ADD'` for any program, so no
binary frame has ever been produced by this path.

## Component inventory

`src/null_system/` — 24 packages, 110 Python files, 22,533 LOC; 85 TypeScript
files, 21,535 LOC.

| Package | Python | TypeScript | Role |
| --- | --- | --- | --- |
| `lang/` | 15 files, 3,973 | — | 3 grammars, parsers, transpiler, module loader, LSP glue |
| `vm/` | 4 files, 725 | 71 files, 18,856 | interpreters (Python + TypeScript) |
| `superbit/` | 7 files, 1,643 | — | IR tokens, encoding, emitter |
| `compiler/` | 5 files, 898 | — | orchestration + optimization passes |
| `knowledge/` | 8 files, 4,112 | — | graph, query language, reasoning |
| `nlp/` | 10 files, 2,288 | — | intent, codegen, embeddings |
| `ml/` | 9 files, 1,608 | — | quantization, attention, torch backend |
| `lib/` | 12 files, 1,328 | — | **the real standard library** |
| `extensions/` | 3 files, 886 | — | extension mechanism |
| `observability/` | 5 files, 619 | — | OTel, metrics, health |
| `lsp/` | 2 files, 421 | — | language server |
| `parser/` | 3 files, 452 | — | a second, older lexer/parser |
| `security/` | — | 9 files, 2,003 | homomorphic crypto, ZKP, SMPC |
| `analysis/` | 1 file, 387 | — | type inference |
| `data/` | 2 files, 365 | — | data types |
| `ast/` | 3 files, 303 | — | nodes + validator |
| `debugger/` | 2 files, 158 | — | debugger hooks |
| `storage/` | 2 files, 145 | — | persistence |
| `quantum/` | 2 files, 139 | — | "quantum simulation" |
| `binary/` | 2 files, 130 | — | binary frame writer |
| `visualizer/` | 2 files, 115 | — | execution timeline |
| `compression/` | 2 files, 93 | — | RLE and compression pass |
| `ai/` | 2 files, 80 | — | imports a module that does not exist |
| `stdlib/` | — | — | 2 `.null` files, both wrong |

`bootstrap/` — 13 files, 14,661 LOC of Null.

## Control flow through the native path

```
bootstrap/input.null
   │  READ_FILE
   ▼
lexer  →  token array
   │
   ▼
parser →  unified AST (accepts both surfaces, records origin in __mode_log)
   │
   ▼
IR emitter → program.ir  (TSV)
   │
   ▼
native backend → program.s + backend.report
   │            (variables assigned fixed frame offsets in a pre-pass;
   │             no dispatch loop, no runtime name lookup, no boxing)
   ▼
cc -O0 → ELF executable
```

The `backend.report` is a first-class artifact: `LOWERED` / `FALLBACK` / `STAT`
per decision. It is what makes the backend auditable and what the fixed-point
check asserts on (zero `FALLBACK` when lowering its own source).

## Execution models

**Native**: no interpreter. Each IR token expands to a fixed instruction
sequence. Functions are real `call`/`ret` with SysV register arguments. Values are
frame slots addressed at compile time.

**Python VM**: a tree-walking interpreter over IR tokens, 480 lines. Reads files
directly in `_call_builtin`.

**TypeScript VM**: 18,856 lines with coroutines, channels, structured concurrency,
distributed execution and JIT/GC scaffolding. Does not compile.

The three disagree on observable behavior. Measured:

| Program | Python VM | Native |
| --- | --- | --- |
| `let x = 3.5; println(x);` | `3.5` | `UNSUPPORTED OP!!`, exit 4 |
| `match 2 {1=>…, 2=>…}` | `one` and `two` | `one` |

That is why [`IMPLEMENTATION_GAPS.md`](IMPLEMENTATION_GAPS.md) P0-5 — a
differential harness — is a prerequisite for trusting any test.

## Architectural decisions worth recording

1. **The IR is the contract, and it is sound.** 53 opcodes, agreed by both
   toolchains. This is the best-designed part of the system.
2. **`FALLBACK` instead of silent miscompilation.** The backend refuses to guess.
   This is why its correctness can be established at all.
3. **`cc` as the assembler.** Defensible: it keeps the backend to one job
   (instruction selection) and does not require writing an object-file writer.
4. **No module system.** `link.null` concatenates top-level `fn` blocks and
   deduplicates by name. A top-level `}` must be at column 0.
5. **Two toolchains instead of one.** The cost is visible everywhere: two IR
   emitters, three runtimes, four grammars, and no differential test.

## What should collapse

The recommendation in [`ARCHITECTURE_AUDIT.md`](ARCHITECTURE_AUDIT.md) is to
converge on:

```
one grammar → one AST → one IR → one backend
```

Pipeline B is the only one that already reaches machine code, so it is the
foundation. Pipeline A's value is its test coverage and its object-literal and
float support — capabilities Pipeline B lacks. Those should be moved into
Pipeline B rather than keeping Pipeline A alive for them.
