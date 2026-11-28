# Implementation Gaps — Prioritized

Every item below was reproduced in this session unless marked otherwise. Each has
a reproduction, the root cause with a file reference, and the scope of the fix.

Priority: **P0** = produces wrong results or blocks a phase; **P1** = missing
capability the roadmap requires; **P2** = unverified or dead code.

## Resolved in Phase 1 (2026-11-28)

These were reproduced, fixed in `bootstrap/`, and are now covered by tests. The
original analysis is kept below because the reproductions still describe the
failure modes.

| Item | Defect | Fix | Test |
| --- | --- | --- | --- |
| P0-1 | `match` emitted no compare and no branch | `emit_match`: hidden subject slot, `EQ` + `JUMP_IF_FALSE` per literal arm | `test_phase1_match_and_float.py`, conformance corpus |
| P0-2 | `3.5` lexed as `3` + `get_member field=5` | `scan_number` takes a fractional part only when a digit follows the dot; float constants load from `.double` rodata | same |
| P0-5 | nothing compared the VM against native output | `test_semantic_conformance.py`: 18 programs, VM vs native vs specified stdout | that file |
| P0-6 | an array of strings lost its element type after index 0 (`words[1]` printed as a tagged pointer, `LEN(words[1])` garbage, then SIGSEGV) | the array-literal element spec was built from `types` while the store loop shrank it; it is now built first | conformance `array-of-strings` |
| P0-7 | `7 / 2` printed `3.5` on the VM and `3` natively | VM division now truncates toward zero with a doubling long-division helper, matching `idiv` | conformance `integer-division-*` |
| P1-7 | `SPLIT`, `JOIN`, `SUBSTR`, `SLICE`, `CONTAINS`, `TO_STRING`, `TO_NUMBER`, `WRITE_FILE`, `FILE_EXISTS` were unknown calls on the bootstrap VM while the native runtime implemented them | implemented in `bootstrap/vm.null` | conformance `string-*`, `integer-division-*` |
| P0-8 | a syntax error became `IR 255 unsupported:…`, a silent no-op in both backends (exit 0, truncated program) | emitter reports `ERROR: unsupported construct …`; VM stops; native routes to `null_unsupported` (exit 4) | `test_diagnostics.py` |

---

## P0-1 — `match` emits no branch, in both backends

**Reproduction**

```null
let n = 2;
match n {
    1 => { println("one"); }
    2 => { println("two"); }
}
```

Native: prints `one`. Python VM: prints `one` **and** `two`.

**Emitted IR** (`bootstrap/emitter.null`):

```
IR  1  2  scalar
IR  3  n  scalar
IR  2  n  scalar
IR 50  NUM 1  match
IR  1  one  scalar  str
IR 30  ""   scalar
IR 41  L_s1_end  control
LABEL L_s1_a0
IR 50  NUM 2  match
IR  1  two  scalar  str
IR 30  ""   scalar
IR 41  L_s1_end  control
LABEL L_s1_a1
IR 52  no_match  match
LABEL L_s1_end
```

There is no `COMPARE_EQ` between the subject and the pattern, and no
`JUMP_IF_FALSE` to `L_s1_aN`. `MATCH_TAG` (50) is emitted as a marker only. The
`JUMP` (41) to `L_s1_end` after each arm is unconditional, so arm 0 always runs
and its label is never a jump target.

**Root cause** — the `match` arm handler in `bootstrap/emitter.null` emits the
pattern and the body but not the test. `IR 52 MATCH_PATTERN` exists in
`bootstrap/ir.null` and is emitted as the fallthrough, but nothing consumes it.

**Scope** — one emitter change plus backend lowering for `MATCH_TAG`/`MATCH_PATTERN`.
Not a grammar change. Must be fixed before any `match` test is written, because
current tests would encode wrong behavior.

---

## P0-2 — Float literals are broken in the bootstrap front end

**Reproduction**

```null
let x = 3.5;
println(x);
```

```
--- backend.report ---
STAT reg x -> r12
FALLBACK 70 unknown-call-get_member
--- IR ---
IR   1  3   scalar
IR  70  get_member  scalar  field=5
IR   3  x   scalar
...
--- RUN ---
UNSUPPORTED OP!!   exit=4
```

**Root cause** — the bootstrap lexer tokenizes `3.5` as the integer `3` followed
by `.5`, and the emitter reads `.5` as member access `get_member field=5`. The
Python VM's lexer handles the float correctly (`println(x)` → `3.5`), so this is a
bootstrap-lexer defect, not a language decision.

**Scope** — number lexing in `bootstrap/lexer.null` (or the emitter's number
handler), plus `FAST_ADD_FLOAT` (101) lowering in `bootstrap/native.null`, which
currently reports `FALLBACK 101 fast-add-float-float64-not-in-this-stage`
(`native.null:3965`). Until then floats must not appear in the advertised surface.

---

## P0-3 — `AST_TO_SUPERBIT_TABLE` stores strings where opcodes are required

**Reproduction**

```
$ pytest tests/test_integration.py::TestIntegration::test_simple_arithmetic
src/null_system/superbit/ir.py:94: in to_bytes
    return bytes([int(self.opcode)]) + payload
E   ValueError: invalid literal for int() with base 10: 'BINARY_ADD'
```

**Root cause** — `src/null_system/superbit/emitter.py` maps AST node types to
bare strings (`"BINARY_ADD"`, `"COMPARE_GT"`) rather than `SuperBitOpCode`
members. `SuperBitIRToken.to_bytes()` coerces with `int()`, which fails.

**Blast radius** — 9 failures in `tests/test_integration.py`, 3 in
`tests/test_compiler.py`, plus `tests/test_compression.py` (2). Every
compile-to-binary path in the Python toolchain.

**Scope** — small and localized. Change the table values to enum members. Then
verify `binary/generator.py:102` → `superbit_stream.to_bytes()` succeeds.

---

## P0-4 — The optimizer uses a removed token API

**Reproduction** — `pytest tests/test_compiler.py::TestOptimizationPasses`:

```
AttributeError: 'SuperBitIRToken' object has no attribute 'symbol'
```

**Root cause** — `src/null_system/compiler/optimization.py` `DeduplicationPass`
and `CompressionPass` read `token.symbol` and `token.bits`. The token class now
exposes `opcode` and `operand`. `CompressionPass` also handles `//` (integer
division) with no matching opcode.

**Blast radius** — 3 failures in `tests/test_compiler.py`, 2 in
`tests/test_compression.py`, and the `test_optimization_passes` /
`test_constant_folding` failures in `test_integration.py`.

**Scope** — small. Update the two passes to the current token API.

---

## P0-5 — VM and native backend disagree on observable behavior

**Reproduction** — the same two programs from P0-1 and P0-2:

| Program | Python VM | Native |
| --- | --- | --- |
| `let x = 3.5; println(x);` | `3.5` | `UNSUPPORTED OP!!`, exit 4 |
| `match 2 {1=>"one" 2=>"two"}` | `one`, `two` | `one` |

**Root cause** — two independent implementations of the same IR semantics with
no differential test. Nothing in the repo compares their outputs.

**Scope** — this is the defect that makes every other test untrustworthy. The fix
is a harness: for each program in a corpus, run on both backends and require
identical stdout and exit code. That harness is the Phase 2 deliverable.

---

## P1-1 — Maps and object literals do not work

**Reproduction**

```null
let m = { "k": 1 };
```

Python: `SyntaxError: Unexpected input: Unexpected token Token('LBRACE', '{')`.
Native: `FALLBACK 1` → `UNSUPPORTED OP!!`.

**Root cause** — no map type in the runtime and no `LBRACE` object rule in
`modern_rust.lark`. Note `bootstrap/dual_modern.null` uses
`{ name: "null", version: 2 }` and the emitter produces `IR 70 object arity=2`,
but `object` has no backend lowering, so the fixture's IR is not executable.

**Scope** — a new runtime type. This is a design decision (hash map vs ordered
map, key types, literal syntax) before it is a coding task.

---

## P1-2 — No memory reclamation

**Measured** in `bootstrap/native.null`:

- `malloc@PLT` / `calloc@PLT`: 9 sites
- `realloc@PLT`: 2 sites
- `free@PLT`: **0**
- `mmap`: **0**
- GC: none

Every string concat, array grow, and slice allocates and never frees. The
`array_map` benchmark's 127 MB RSS against 2,184 KiB for `sum_loop`
(`bench/results/latest.md`) is consistent with this.

**Scope** — Phase 3. Needs a strategy decision (arena, refcount, tracing GC)
before code. `own`/`borrow`/`move`/`ref` are already lexed, so ownership-based
reclamation is the option the syntax already anticipates.

---

## P1-3 — The standard library is not written in Null

**Measured** — `src/null_system/stdlib/` contains exactly two files.

`math.null`:

```null
DEFINE sum WITH arr
    SET total TO 0
    SET len TO array.LENGTH(arr)
    REPEAT len TIMES
        SET i TO total                    # loop counter overwritten by the accumulator
        SET val TO array.SLICE(arr, total, 1)
        SET total TO math.ADD(i, val)
    END REPEAT
    RETURN total
END DEFINE
```

`SET i TO total` assigns the accumulator to the loop variable, and `i` is then
never used as an index. The function does not compute a sum. `min_in_array` and
`max_in_array` have the same pattern.

`strings.null` states in its own header: *"Currently, most implementations are in
Python stdlib. This file demonstrates the module structure."*

The real standard library is `src/null_system/lib/` — 12 Python modules, 1,328
LOC: `array_ops, io_ops, kg_ops, math_ops, ml_ops, nlp_ops, object_ops,
option_ops, registry, result_ops, text_ops`.

**Scope** — Phase 5. Each `lib/*.py` needs a Null equivalent. Blocked on P0-1
because a stdlib written in Null will use `match`.

---

## P1-4 — Ownership is lexed but never checked

**Measured** — `own`, `borrow`, `borrow_mut`, `move`, `ref` are in
`bootstrap/lexer.null`'s keyword table. `bootstrap/features_modern.null` uses
`fn apply(own value: Num) -> Num { let borrowed = &value; return borrowed * 2; }`.
The emitter emits `IR 3 borrowed` and `IR 2 borrowed` — a plain store and load.
No analysis runs.

**Scope** — Phase 3, and it should be decided together with P1-2, because
ownership is the reclamation strategy the syntax implies.

---

## P1-5 — The CLI is not a language toolchain

**Measured** — `src/null_system/cli.py` commands: `show-subsystems, observe,
compile, run, lsp, visualize, info, tokenize, translate, codegen, init, query,
reason, link-external, metrics`.

Absent: `build`, `test`, `fmt`, `clean`, `add`, `doc`, `bench`. Also absent: any
way to invoke the native backend. `bench/stage_runner.py` (Python) is the only
way to run a `.null` stage.

**Scope** — Phase 6. Depends on Phase 4 (a native driver binary).

---

## P1-8 — Diagnostics have no source location (open)

**Measured** — a program with `let y = ;` now reports
`ERROR: unsupported construct: unsupported:eof:PUNCT:;`, but nothing says which
line it is on. `tokenize` emits tokens as `"KIND value"` with no position, and
the AST nodes carry no span, so no stage can name a location.

**Scope** — Phase 1.4. Needs positional tokens (`line:col` prefix in the token
text, or a parallel offsets array) threaded from `tokenize` to the `eof`
fallback in `parse_primary`, then `line:col: error: message` formatting in
`report_compile_errors`. Touching the token format touches the fixed point, so
it must be followed by `bench/selfhost_check.sh`.

## P1-6 — Division by zero traps instead of reporting

**Reproduction** — a native program dividing by zero exits with SIGFPE, code 136,
and no output. An out-of-bounds index, by contrast, prints `OOB PANIC!!!` and
exits 3.

**Root cause** — integer division is lowered to the `idiv` instruction with no
zero check, while array access calls `null_panic_oob`.

**Scope** — small, in `bootstrap/native.null`'s binary-op lowering. Needed before
any program can be trusted with computed divisors.

---

## P2-1 — The TypeScript VM does not compile

`npx tsc --noEmit` → 97 errors across 7 files; 67 in `vm/null_vm.ts`
(`LayerKind`, `layerExecutionManager`, `pushLayer` undefined), 23 in
`vm/memory.ts`. 18,856 LOC unbuildable, including all of `v10/`, `ai/`,
`quantum/`, `distributed/` and `security/`.

**Scope** — a decision, not a repair: either fix the type errors or delete the
tree. It is not in the shipped path, so repairing it has no language benefit.

---

## P2-2 — `NullCallContext` signature drift breaks ML and KG

**Reproduction** — 11 errors: `TypeError: NullCallContext.__init__() missing 2
required positional arguments: 'registry' and 'io'`.

**Blast radius** — 7 errors in `tests/integration/test_null_ml_lang.py`, 4 in
`tests/integration/test_null_kg_lang.py`.

**Scope** — small. Either default the two parameters or update the call sites.

---

## P2-3 — `numpy.uint4` does not exist

**Reproduction** — `pytest tests/ml/test_quantization.py`:
`AttributeError: module 'numpy' has no attribute 'uint4'`.

**Root cause** — 4-bit quantization is implemented by referencing a dtype NumPy
does not provide.

**Scope** — small, but only worth fixing if ML ships. See
[`DEPENDENCY_AUDIT.md`](DEPENDENCY_AUDIT.md).

---

## P2-4 — Performance claims are not supportable

**Measured** — `bench/results/latest.md` reports `sum_loop` at 4.00x faster than
C. `bench/c/sum_loop.c:6` declares `volatile int64_t n = 100000000;`, which
prevents the compiler from hoisting the loop bound out of memory. The comparison
is against a deliberately weakened baseline. `array_map` is 0.96x, i.e. slower.

**Scope** — Phase 8. Regenerate every number with baselines that do not defeat
optimization, and withdraw the 4.00x claim until then.

---

## P2-5 — Module resolution and loop control defects

- `tests/test_module_loader.py` (3): `ModuleNotFoundError: Module 'test.module'
  not found` — dot-separated names are not resolved
  (`src/null_system/lang/module_loader.py:132`). Circular-import detection also
  fails (2 of the 3).
- `tests/lang/test_loop_control.py` (2): `continue` inside `for` skips the
  increment step, so the loop does not advance.
- `tests/test_io_operations.py` (1): writing multiline content produces literal
  `\n` instead of newlines — an escaping bug in the write path.

**Scope** — small, independent fixes.

---

## P2-6 — Repository hygiene

- `venv/` is tracked: 3,676 files, 1,067 of them `.pyc`, despite `.gitignore`
  listing both. Every test run dirties the tree.
- A file literally named `=0.12.0` is tracked at the repo root; it is 57 lines of
  `pip install` output from an unquoted version specifier.
- `pyproject.toml` declares 6 dependencies, `requirements.txt` declares 16, three
  of those (`scipy`, `onnxruntime`, `httpx`) are imported nowhere, and four
  imported packages (`opentelemetry`, `sentry_sdk`, `prometheus_client`,
  `requests`) are declared nowhere.

**Scope** — trivial, and it should be done first because it makes every later
diff readable.

---

## Suggested order

1. **P2-6** — hygiene. Trivial, unblocks clean diffs.
2. **P0-3, P0-4** — two small localized fixes that unblock ~15 tests and the whole
   super-bit encode path.
3. **P0-1, P0-2** — correctness bugs in the only pipeline that reaches machine
   code.
4. **P0-5** — the differential harness, which makes the remaining work verifiable.
5. **P1-6, P2-5, P2-2** — small independent fixes.
6. **P1-1, P1-2/P1-4, P1-3** — design decisions, in that order.
7. **P2-1** — decide whether the TypeScript tree lives.
8. **P2-4** — regenerate performance numbers honestly.
