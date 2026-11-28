# Null — Engineering Roadmap

Status: plan of record. Phase 0 is complete (see [`ROADMAP_STATUS.md`](ROADMAP_STATUS.md)).
Every phase below is gated on measured evidence, not on a class or document existing.

## Definition of done for the project

Null is a **self-contained, self-hosting language** when all of the following hold
on a machine with no Python, no Node, and no third-party libraries installed:

1. `nullc` is a native binary produced by Null's own compiler.
2. That binary compiles its own source to byte-identical output (native fixed point).
3. The standard library is written in Null, not in Python.
4. No build step, test, or tool in the shipped pipeline invokes an interpreter
   other than the Null binary.
5. The language has one authoritative grammar, and its native syntax is its own —
   not a Rust or Python dialect.
6. Performance claims are reproducible by a checked-in harness that measures
   against a fair baseline.

## Phase 0 — Verified implementation audit (complete)

Inspect the real repository and record what actually works, with commands and
numbers, not with intent. Produces the documents in `docs/` and the prioritized
defect list in [`IMPLEMENTATION_GAPS.md`](IMPLEMENTATION_GAPS.md).

Exit criteria: full test suite run and counted; both fixed points reproduced
independently; every claimed subsystem classified as working / partial / broken /
absent.

## Phase 1 — One grammar, native syntax

The repository currently ships **four** syntax surfaces:

| Surface | File | Status |
| --- | --- | --- |
| English-like v1 | `src/null_system/lang/grammar.lark` (237 lines, 50 rules) | parses, compiles to super-bit IR |
| "Modern Rust" | `src/null_system/lang/modern/modern_rust.lark` (145 lines) | partial, 8 test failures |
| "Modern Python" | `src/null_system/lang/modern/modern_python.lark` (142 lines) | partial |
| Bootstrap emitter | `bootstrap/emitter.null` (2944 lines) | most complete front end |

The two "modern" dialects are explicitly Rust-like and Python-like. That
contradicts the requirement that Null have its own native syntax. Phase 1
converges on **one** grammar, expressed in Null's own keywords, and deletes the
dialect parsers once the bootstrap emitter covers the same surface.

Exit criteria: a single normative grammar file; a conformance corpus that all
front ends agree on; the dialect grammars removed rather than left as aliases.

## Phase 2 — Compiler correctness

The IR pipeline has defects that make it produce wrong programs, not merely
incomplete ones. Measured in Phase 0:

- ~~`match` emits no comparison and no branch~~ — fixed in Phase 1: one `EQ` +
  `JUMP_IF_FALSE` per literal arm, asserted by `test_semantic_conformance.py`.
- ~~Float literals are lexed as `3` plus `get_member field=5`~~ — fixed in
  Phase 1; float arithmetic is still refused rather than miscompiled.
- `AST_TO_SUPERBIT_TABLE` stores bare strings where `SuperBitOpCode` members are
  required, so `to_bytes()` raises `ValueError: invalid literal for int() … 'BINARY_ADD'`.
- The optimizer passes still use a removed token API (`symbol` / `bits`).

Exit criteria: every IR opcode emitted by a front end is lowered, never
`FALLBACK`; a differential test compares VM and native output for the same
source; no `invalid literal for int()` path remains reachable.

## Phase 3 — Native runtime and memory model

The runtime is x86-64 assembly emitted by `bootstrap/native.null`. It calls
`malloc`/`calloc` at 9 sites and `realloc` at 2, and **never** calls `free`.
There is no GC, no `mmap`, and no ownership enforcement despite `own` / `borrow`
/ `move` appearing in the lexer's keyword table.

Exit criteria: a documented allocation strategy; reclamation that a long-running
program can survive; panic paths that report instead of trapping (division by
zero currently raises SIGFPE, exit 136, uncaught); float64 arithmetic in the
backend rather than a fallback.

## Phase 4 — Self-hosting without Python

Both fixed points currently pass, but the *host* is still Python:
`bench/stage_runner.py` imports `null_system.lang.compiler` and
`null_system.vm.vm`. The native fixed point proves the compiler is real; it does
not prove Python is gone, because the emitter stage still runs on the Python VM.

Exit criteria: a build script that uses only the previously built Null binary to
produce the next one; `stage_runner.py` reduced to a test harness, not a build
dependency; the chain reproducible from a committed seed artifact.

## Phase 5 — Standard library in Null

`src/null_system/stdlib/` contains two files. `math.null` misuses the accumulator
(`SET i TO total`, `SET total TO math.ADD(i, val)`), so it does not compute a sum.
`strings.null` states in its own header that "most implementations are in Python
stdlib". The real library is 12 Python modules, 1,328 LOC, in `src/null_system/lib/`.

Exit criteria: each `lib/*.py` module has a Null equivalent with tests; the Python
versions are either deleted or demoted to reference implementations.

## Phase 6 — Toolchain

The CLI exposes `show-subsystems, observe, compile, run, lsp, visualize, info,
tokenize, translate, codegen, init, query, reason, link-external, metrics`.
A language needs `build`, `test`, `fmt`, `clean`, `add`, `doc`, `bench`. None
exist. `bench/stage_runner.py` is Python and is the only way to run a `.null`
stage.

Exit criteria: those commands exist and are implemented in Null; the toolchain
runs from the native binary.

## Phase 7 — Dependency elimination

16 third-party packages are imported from `src/` (see
[`DEPENDENCY_AUDIT.md`](DEPENDENCY_AUDIT.md)). Each is either ported to Null or
removed with a documented replacement. The parser dependency (`lark`, 6 sites) is
the highest priority because it sits on the critical path of the front end.

Exit criteria: zero third-party imports in the shipped path; the list in
`DEPENDENCY_AUDIT.md` closed item by item with evidence.

## Phase 8 — Honest performance

`bench/results/latest.md` claims `sum_loop` is 4.00x faster than C. The C baseline
declares `volatile int64_t n` (`bench/c/sum_loop.c:6`), which forces the loop to
memory and is not a fair comparison. `array_map` shows 0.96x, and its RSS is
127 MB against 2184 KiB for `sum_loop`.

Exit criteria: baselines without defeating optimizations; every published number
regenerated by a checked-in command; the claim in `performance_contract.md`
either substantiated or withdrawn.

## Phase 9 — Platform support

The backend emits GNU `as` Intel-syntax System V ABI x86-64 assembly and is
assembled with `cc -O0`. There is no other target. See
[`PLATFORM_SUPPORT.md`](PLATFORM_SUPPORT.md).

Exit criteria: a stated supported matrix; either a second target or an explicit
statement that one target is the deliverable.

## Phase 10 — Stabilization

A conformance suite that both front ends and both backends must pass; the
specification frozen against it; versioned releases.

Exit criteria: the conformance suite is the definition of the language, and CI
runs it.

## Ordering constraint

Phases 2 and 3 are prerequisites for 4. Phase 1 can proceed in parallel with 2.
Phase 5 cannot start before 2, because the stdlib needs correct codegen. Phase 7
is last for the parser only if Phase 1 keeps `lark`; if Phase 1 replaces the
front end, `lark` disappears as a side effect.
