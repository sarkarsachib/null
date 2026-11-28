# Phase 0 — Roadmap Status

Measured on 2026-11-27, branch `freebuff/ecca3cb8674198d74aea1246`, base commit
`8232c41`. Every number in this document came from a command run against this
working tree. Nothing here is inferred from a class, rule, or doc existing.

## Verdict

Phase 0 is **complete**. Phase 1 is **in progress**: the semantic conformance
suite exists and passes, five divergences it found are fixed, and compile-time
errors are now reported instead of silently halting. Sections 1.1 (normative
decisions), 1.3 (type system) and the source locations of 1.4 remain.

The compiler is real: it self-hosts and produces a native binary that reproduces
its own IR byte for byte. It is also **not yet a usable language**: the standard
library is Python, the syntax is a Rust/Python clone, `match` and floats are
broken, and 57 tests fail.

| Question | Answer | Evidence |
| --- | --- | --- |
| Does it self-host? | Yes, on two axes | `bench/selfhost_check.sh` |
| Is Python gone from the pipeline? | No | `bench/stage_runner.py` is Python |
| Is the stdlib in Null? | No | 2 broken files vs 1,328 LOC of Python |
| Is the syntax Null's own? | No | `modern_rust.lark`, `modern_python.lark` |
| Do the tests pass? | Mostly | 959 passed, 57 failed, 11 errors |
| Does the TS VM compile? | No | 97 `tsc` errors |
| Are the perf claims sound? | No | `volatile` in the C baseline |

## Phase 1 — progress

Measured 2026-11-28 on this working tree. Phase 0's figures above are kept as the
baseline they were measured against.

### 1.2 Semantic conformance — done

`tests/bootstrap/test_semantic_conformance.py` is the shared suite the roadmap
requires. Each case is a Null program plus its specified stdout. For every case
it runs the program on the bootstrap VM (reference) and, separately, lowers it
with `bootstrap/native.null`, assembles it with `cc -O0` and runs the binary. It
requires:

1. the VM output equals the specified output (so a program wrong on both
   backends still fails),
2. the native output equals the VM output,
3. the IR has no `unsupported:` row and `backend.report` has no `FALLBACK` row.

19 cases cover arithmetic and precedence, comparison and logical operators,
if/else, while, for-in, array read/write, APPEND growth, string operations,
SPLIT/JOIN/SUBSTR/CONTAINS, SLICE/TO_NUMBER, file write/exists/read, functions
and recursion, `match` on integers, strings and wildcards, float literals,
break/continue, nested loops, truncating division, and arrays of strings.

```
$ pytest tests/bootstrap/test_semantic_conformance.py -q
19 passed
```

Before it was added there was no test that ran one program on both backends. On
its first run it found five divergences, all now fixed:

| Divergence | Cause | Fix |
| --- | --- | --- |
| `words[1]` printed as a pointer, `LEN(words[1])` garbage, then SIGSEGV | `native.null` built an array literal's element spec from `types` while the store loop shrank that same stack, so every element after the first was typed `""` | build the spec before the store loop |
| `7 / 2` printed `3.5` on the VM, `3` natively | the VM used Python `/`; native uses `idiv` | VM integer division truncating toward zero, by doubling (logarithmic, not repeated subtraction) |
| `SPLIT`, `JOIN`, `SUBSTR`, `CONTAINS`, `TO_STRING`, `TO_NUMBER`, `SLICE`, `WRITE_FILE`, `FILE_EXISTS` were `VM ERROR: unknown call` | builtins existed only in the native runtime | implemented in `bootstrap/vm.null` |

### 1.4 Diagnostics — partial

A syntax error used to become `IR 255 unsupported:eof:PUNCT:;`, which both
backends treated as a no-op: the VM ran on with a missing value, the native
binary emitted nothing and exited 0. A typo therefore looked like a working
build that printed less than expected.

Now:

- the emitter prints `ERROR: unsupported construct: <construct>` for every
  `todo` row (`bootstrap/emitter.null`, `compile_errors` / `report_compile_errors`);
- the VM stops with `VM ERROR: unsupported construct …`;
- the native backend routes the row to `null_unsupported` (`UNSUPPORTED OP!!`,
  exit 4) and records `ERROR …` in `backend.report`;
- `tests/bootstrap/test_diagnostics.py` asserts all three, plus that a clean
  program is unaffected.

Source locations are now included: `tokenize` returns a `["TOKENS", tokens,
positions, eof]` wrapper whose third field holds the `line:col` of each token,
`parse_primary` stamps the position on the `eof` fallback node, and the emitter
prints `2:9: error: unsupported construct: …`. Tokens themselves keep their
`"KIND value"` text, so the canonical IR is byte-identical.

Still missing: locations for constructs that parse but cannot be lowered — the
AST has no spans, so only the `eof` fallback is positioned (P1-8, remaining
work noted in `IMPLEMENTATION_GAPS.md`).

### Regression gate after these changes

`bench/selfhost_check.sh` was re-run after regenerating `bootstrap/nullc.null`
from the modified `emitter.null`, `vm.null` and `native.null`:

```
PASS identical IR: 15041 rows, 318744 bytes, no unsupported rows
     nullc 127879 ms, emitter 121497 ms (host VM, this machine)
PASS native fixed point: 15041 rows, identical to the VM, no FALLBACK
```

The row count grew from 13,894 to 15,041 because the VM now carries the string
builtins and the long-division helper, and the emitter carries positional
tokens. The timings vary with machine load; the row and byte counts are the
assertion.

### Still open in Phase 1

- 1.1: the keyword set, statement termination, comment syntax and ownership
  decision are documented as open questions, not decided.
- 1.3: no static type checking. The native backend is dynamically typed;
  `let a: Num = 4` is not checked against its initialiser.
- 1.4: line/column diagnostics exist for the `eof` fallback only (P1-8); other
  unsupported constructs still report without a location.

## What exists and works

### Self-hosting, verified independently

```
$ SKIP_NATIVE=1 bash bench/selfhost_check.sh
PASS identical IR: 13665 rows, 286648 bytes, no unsupported rows
     nullc 73885 ms, emitter 68972 ms (host VM, this machine)
```

Re-run later in the same session on a loaded machine: `nullc 88528 ms, emitter
80289 ms`, same 13,665 rows and 286,648 bytes. The timings vary with load; the
row and byte counts do not. Treat the counts as the assertion and the times as
indicative.

```
$ bash bench/selfhost_check.sh
PASS identical IR: 13665 rows, 286648 bytes, no unsupported rows
PASS native fixed point: 13665 rows, identical to the VM, no FALLBACK
```

The second check is the strong one. It compiles `bootstrap/native.null` into an
x86-64 binary with `cc -O0`, has *that binary* compile `bootstrap/nullc.null`, and
requires its IR to match the Python VM's output byte for byte. The backend
reported no `FALLBACK` rows while lowering its own source, so the native path is
not silently delegating.

This was re-run in this session rather than taken from an existing document.

### The native backend produces correct executables

Hand probes, each emitted through `emitter.null` → `native.null` → `cc -O0`:

| Program | Backend report | Output |
| --- | --- | --- |
| `a=7; b=5; total=a+b; println(total); println("hi")` | `LOWERED 2 / FALLBACK 0` | `12`, `hi` |
| user `fn add(a,b)` | `FALLBACK 0` | correct |
| `while` loop | `FALLBACK 0` | correct |
| `let nums=[1,2,3]; println(LEN(nums)); println(nums[1])` | `FALLBACK 0` | `3`, `2` |
| string concat and indexing | `FALLBACK 0` | correct |
| `if`/`else` | `FALLBACK 0` | correct |
| `for v in nums` | `FALLBACK 0` | `10` |
| recursion, `fib(15)` | `FALLBACK 0` | `610` |
| typed `let a: Num = 4` | `FALLBACK 0` | correct |

Runtime safety is partly present: an out-of-bounds index prints `OOB PANIC!!!` and
exits 3, and division by zero prints `DIVISION BY ZERO!!!` and exits 5.

### Repository scale

| Area | Files | LOC |
| --- | --- | --- |
| `src/` Python | 110 | 22,533 |
| `.null` sources | 50 | 32,982 |
| `src/` TypeScript | 85 | 21,535 |
| tests (`test_*.py`) | 55 | — |
| `src/null_system/lib/` (the real stdlib) | 12 | 1,328 |

Bootstrap stages: `native.null` 4,363; `nullc.null` 3,557; `emitter.null` 2,944;
`parser.null` 2,286; `vm.null` 715; `ir.null` 311; `lexer.null` 256;
`link.null` 124; `input.null` 7.

## What is missing or broken

Full detail and file references are in [`IMPLEMENTATION_GAPS.md`](IMPLEMENTATION_GAPS.md).
Summary, ordered by severity:

### P0 — produces wrong programs

1. **`match` does not branch.** Native: `match n { 1=>println("one") 2=>println("two") }`
   with `n = 2` prints only `one`. The IR is
   `IR 50 NUM 1 match / IR 1 one / IR 30 / IR 41 L_s1_end / LABEL L_s1_a0 / IR 50 NUM 2 match …`
   — there is no comparison and no conditional jump, so the first arm always runs
   and the arm labels are never targeted. The Python VM prints `one` *and* `two`,
   because arms are not exclusive either.
2. **Floats are broken in the bootstrap front end.** `let x = 3.5; println(x);`
   lexes as `IR 1 3 scalar` + `IR 70 get_member field=5`, reports
   `FALLBACK 70 unknown-call-get_member`, and the binary prints
   `UNSUPPORTED OP!!` with exit 4. The Python VM prints `3.5` correctly, so the
   two paths disagree.
3. **`AST_TO_SUPERBIT_TABLE` stores strings, not opcodes.**
   `src/null_system/superbit/emitter.py` maps to `"BINARY_ADD"` where
   `src/null_system/superbit/ir.py:94` does `int(self.opcode)`. Result:
   `ValueError: invalid literal for int() with base 10: 'BINARY_ADD'`, which is
   the direct cause of 9 failures in `tests/test_integration.py` and 3 in
   `tests/test_compiler.py`.
4. **The optimizer uses a removed token API.** `src/null_system/compiler/optimization.py`
   reads `token.symbol` / `token.bits`; tokens now expose `opcode` / `operand`.
   5 failures.

### P1 — capability gaps

5. **Maps are unsupported.** `let m = { "k": 1 };` fails in the Python parser
   (`Unexpected token Token('LBRACE' …)`) and falls back natively
   (`FALLBACK 1` → `UNSUPPORTED OP!!`). Yet `bootstrap/dual_modern.null` uses an
   object literal and `bootstrap/features_modern.null` uses `data class`.
6. **No memory reclamation.** 9 `malloc`/`calloc` sites, 2 `realloc`, zero `free`,
   no GC, no `mmap`. Every allocation leaks.
7. **The stdlib is not in Null.** `src/null_system/stdlib/math.null` does not
   compute a sum: it sets the loop variable from the accumulator
   (`SET i TO total`) and then adds the accumulator to a slice
   (`SET total TO math.ADD(i, val)`). `strings.null` says in its header that most
   implementations are in Python.
8. **Ownership keywords are lexed but not enforced.** `own`, `borrow`, `borrow_mut`,
   `move`, `ref` appear in `bootstrap/lexer.null`'s keyword table; nothing checks them.
9. **No CLI for a language.** Present: `show-subsystems, observe, compile, run,
   lsp, visualize, info, tokenize, translate, codegen, init, query, reason,
   link-external, metrics`. Absent: `build, test, fmt, clean, add, doc, bench`.

### P2 — dead or unverifiable subsystems

10. **The TypeScript VM does not typecheck.** `npx tsc --noEmit` → 97 errors:
    67 in `vm/null_vm.ts` (missing `layerExecutionManager`, `LayerKind`,
    `pushLayer`), 23 in `vm/memory.ts`, plus `distributed/distributed_executor.ts`
    (3), `v10/execution_pipeline.ts` (1), `vm/index.ts` (1), `decoder.ts` (1),
    `src/bin/cli.ts` (1). A VM that cannot compile is not a working VM.
11. **Performance claims are not supportable as written.** `bench/results/latest.md`
    reports `sum_loop` at 4.00x faster than C; `bench/c/sum_loop.c:6` declares
    `volatile int64_t n`, which prevents the compiler from folding the loop.
    `array_map` is 0.96x with 127 MB RSS.
12. **Four syntax surfaces.** `grammar.lark`, `modern_rust.lark`,
    `modern_python.lark`, and the bootstrap emitter's own grammar. They do not
    agree; `test_lsp_server.py` has 3 failures purely from round-tripping between
    two of them.

## Test suite

```
$ PYTHONPATH=src ./venv/bin/python -m pytest tests -q -p no:randomly \
    --ignore=tests/test_null_system_lib.py --ignore=tests/test_subsystems.py
= 57 failed, 959 passed, 1 skipped, 20 warnings, 11 errors in 191.54s =
```

Two test modules are excluded because they import modules that do not exist
(`null_system.ai.core`) or use a compiler API that no longer matches
(`null_system.compiler`). Their exclusion is a recorded gap, not a fix.

Failures by file:

| File | Failures | Root cause |
| --- | --- | --- |
| `tests/test_integration.py` | 9 | string opcodes in `AST_TO_SUPERBIT_TABLE` |
| `tests/lang/test_modern_rust_parser.py` | 8 | grammar gaps: `mut`, `..` ranges, `match`, `.` |
| `tests/integration/test_null_ml_lang.py` | 7 errors | `NullCallContext.__init__` needs `registry` and `io` |
| `tests/superbit/test_tokens.py` | 6 | token API drift (`assert 1 == 6`) |
| `tests/integration/test_null_kg_lang.py` | 5 + 4 errors | same `NullCallContext` signature |
| `tests/knowledge/test_query_language.py` | 4 | path/embedding query support |
| `tests/test_module_loader.py` | 3 | dot-separated module resolution |
| `tests/test_compiler.py` | 3 | optimizer token API |
| `tests/nlp/test_intent.py` | 3 | intent classifier does not detect `if`/`define`/`call` |
| `tests/nlp/test_codegen.py` | 3 | generated text does not match expected |
| `tests/lang/test_lsp_server.py` | 3 | dialect round-trip, `TimeoutError` on LSP header |
| `tests/visualizer/test_backend_api.py` | 2 | `NullVM` has no attribute `frames` |
| `tests/test_compression.py` | 2 | RLE decode, opcode mismatch |
| `tests/ml/test_quantization.py` | 2 | `numpy` has no `uint4` |
| `tests/lang/test_loop_control.py` | 2 | `continue` in `for` skips the increment |
| `tests/test_io_operations.py` | 1 | newline escaping (`Line 1\nLine 2` vs literal `\n`) |
| `tests/knowledge/test_reasoning.py` | 1 | `Rule.__init__()` missing `id` |

Distinct error signatures across the suite: 26 `Expected one of:` grammar
failures, 11 `NullCallContext.__init__() missing 2 required positional arguments`,
8 `Previous tokens: [Token('DOT', '.')]`, 5
`'SuperBitIRToken' object has no attribute 'symbol'`, 4
`invalid literal for int() … 'BINARY_ADD'`, 3 `invalid literal … 'COMPARE_GT'`,
4 `NameError: name 'SuperBitEncoder' is not defined`, 6
`maximum recursion depth exceeded`.

## What changed in this session

Nothing in tracked source. This session produced documentation only. The working
tree was cleaned of `.pyc` churn before writing; the only untracked files are
`bootstrap/backend.report`, `bootstrap/program.ir`, `bootstrap/program.s`, which
are build artifacts and must not be committed.

## Files added by Phase 0

- `docs/ROADMAP.md` — the ten phases and their exit criteria
- `docs/ROADMAP_STATUS.md` — this document
- `docs/ARCHITECTURE_AUDIT.md` — what each subsystem actually does
- `docs/DEPENDENCY_AUDIT.md` — the 16 third-party dependencies, site by site
- `docs/IMPLEMENTATION_GAPS.md` — the prioritized defect list
- `docs/LANGUAGE_SPECIFICATION.md` — the syntax that exists today
- `docs/COMPILER_PIPELINE.md` — source to IR to assembly, stage by stage
- `docs/NATIVE_RUNTIME.md` — the x86-64 backend and its runtime
- `docs/BOOTSTRAP.md` — the four-stage bootstrap and its fixed points
- `docs/PERFORMANCE.md` — the benchmark harness and why its numbers are unsound
- `docs/PLATFORM_SUPPORT.md` — targets, toolchain requirements, limits

## Next prerequisites before Phase 1

1. Decide the single native syntax (Phase 1 blocking decision).
2. Fix `AST_TO_SUPERBIT_TABLE` and the optimizer token API — these are small,
   localized, and unblock 15 tests plus the whole super-bit encode path.
3. Fix `match` lowering in `bootstrap/emitter.null`; it is a correctness bug in
   both backends and any test written against `match` today asserts wrong behavior.
4. Fix float lexing in the bootstrap front end, or remove floats from the
   advertised surface until the backend lowers them.
5. Freeze the `NullCallContext` signature so the ML/KG integration tests can run.
