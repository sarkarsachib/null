# Architecture Audit

What each subsystem actually is, measured on 2026-11-27. Classification is
strict: **Working** means a command produced correct output; **Partial** means it
runs but is wrong or incomplete; **Broken** means it raises or miscompiles;
**Absent** means the code does not exist.

There are **three separate implementations** of a Null runtime in this repository
(Python VM, TypeScript VM, native x86-64 backend) and **four** front ends. That
is the central architectural finding: the project has no single pipeline.

## Subsystem inventory

| Directory | Py files | Py LOC | TS files | TS LOC | Verdict |
| --- | --- | --- | --- | --- | --- |
| `lang/` | 15 | 3,973 | — | — | Partial — 3 front ends, 8 test failures |
| `vm/` (Python) | 4 | 725 | 71 | 18,856 | Broken (TS), Partial (Py) |
| `superbit/` | 7 | 1,643 | — | — | Broken — encoder raises |
| `compiler/` | 5 | 898 | — | — | Partial — optimizer API drift |
| `knowledge/` | 8 | 4,112 | — | — | Partial — 5 failures + 4 errors |
| `nlp/` | 10 | 2,288 | — | — | Partial — 6 failures |
| `ml/` | 9 | 1,608 | — | — | Partial — `numpy.uint4` absent |
| `lib/` | 12 | 1,328 | — | — | Working — this *is* the stdlib |
| `stdlib/` | 0 | 0 | — | — | Broken — 2 `.null` files, both wrong |
| `extensions/` | 3 | 886 | — | — | Unverified — no tests in suite |
| `observability/` | 5 | 619 | — | — | Unverified — 4 undeclared deps |
| `parser/` | 3 | 452 | — | — | Partial — parallel to `lang/` |
| `security/` | 0 | 0 | 9 | 2,003 | Unverified — TS only |
| `analysis/` | 1 | 387 | — | — | Partial — type inference |
| `data/` | 2 | 365 | — | — | Unverified |
| `ast/` | 3 | 303 | — | — | Working — nodes + validator |
| `lsp/` | 2 | 421 | — | — | Partial — 3 failures |
| `binary/` | 2 | 130 | — | — | Broken — depends on `superbit` |
| `debugger/` | 2 | 158 | — | — | Unverified |
| `storage/` | 2 | 145 | — | — | Unverified |
| `quantum/` | 2 | 139 | — | — | Unverified — 139 LOC for "quantum simulation" |
| `visualizer/` | 2 | 115 | — | — | Broken — `NullVM` has no `frames` |
| `compression/` | 2 | 93 | — | — | Broken — 2 failures |
| `ai/` | 2 | 80 | — | — | Broken — module imported by tests does not exist |

`src/null_system/ai/` has 80 lines across 2 files; `tests/test_subsystems.py`
imports `null_system.ai.core`, which is not there. That is why the module is
excluded from the suite.

## The four front ends

```
bootstrap/lexer.null (256) ─┐
bootstrap/parser.null (2286)┴→ bootstrap/emitter.null (2944) → IR
src/null_system/lang/grammar.lark (237) → parser.py → lang/compiler.py → IR
src/null_system/lang/modern/modern_rust.lark (145) → modern_rust.py → IR
src/null_system/lang/modern/modern_python.lark (142) → modern_python.py → IR
```

The bootstrap chain is the only one that reaches the native backend, and it is
the only one exercised by `bench/selfhost_check.sh`. The three Python chains
produce super-bit IR for the Python VM and the (broken) TypeScript VM.

This is the reason `tests/lang/test_lsp_server.py` fails: it round-trips source
between the English and modern dialects and neither is authoritative.

### What the bootstrap front end supports

Keywords in `bootstrap/lexer.null`:

```
async borrow break class continue data else false fn for if import in let
match module move mut own print println return sealed trait true while
```

Statement kinds the emitter recognizes (from its string table):
`module import type_alias data_class sealed trait fn let set set_op set_index
set_member if while for repeat return break continue match print println
class async await pipeline comprehension simd lambda object array index
member safe_member safe_method elvis notnull unwrap call call_value unary
binary compare range fused`.

Verified working end-to-end through the native backend: functions, `while`,
`for v in nums`, `if`/`else`, arrays with `LEN` and indexing, string concat and
indexing, recursion, typed `let`.

Verified broken: `match` (no branching emitted), float literals (lexed as
`3` + `get_member field=5`), map/object literals at runtime.

### Fixture files overstate support

`bootstrap/dual_modern.null`, `bootstrap/features_modern.null` and
`bootstrap/dual_english.null` are showcase files. They **do** emit IR with no
`unsupported` rows — the front end handles the syntax. But the IR they produce
contains opcodes the backends cannot execute: `IR 113 FUSED_COMPREHEND`,
`IR 70 filter` with `fused arity=2`, `IR 60 SAFE_CALL`, `IR 61 ELVIS_CHECK`,
`IR 52 MATCH_PATTERN`. The emitter succeeding is not the program running.

`bootstrap/features_modern.null` also uses `data class User(name: Text, id: UserId)`
and `u!!.name`, which the emitter maps to `IR 73 INDEX` and `IR 3 STORE_VAR id`
— not a struct field access. So "data class" is not implemented; the tokens are
merely consumed.

## The three runtimes

### Python VM — `src/null_system/vm/vm.py`, 480 lines

480 lines for an interpreter that executes super-bit IR. It has `_call_builtin`
at line ~212 which reads files directly. It disagrees with the native backend on
observable behavior:

- `let x = 3.5; println(x);` → prints `3.5` (native traps)
- `match 2 {1=>…, 2=>…}` → prints `one` **and** `two` (native prints `one`)

So a program's output depends on which backend ran it. That is the single most
serious architectural problem in the repository, because it means no test can be
trusted without naming the backend.

`src/null_system/visualizer/` calls `NullVM().frames`, which does not exist
(`vm.py:271`), so the visualizer is broken against the current VM.

### TypeScript VM — `src/null_system/vm/`, 71 files, 18,856 LOC

**Does not compile.** `npx tsc --noEmit`:

```
67 src/null_system/vm/null_vm.ts
23 src/null_system/vm/memory.ts
 3 src/null_system/vm/distributed/distributed_executor.ts
 1 src/null_system/vm/v10/execution_pipeline.ts
 1 src/null_system/vm/index.ts
 1 src/null_system/vm/decoder.ts
 1 src/bin/cli.ts
= 97 errors
```

Representative errors: `Cannot find name 'LayerKind'`,
`Property 'layerExecutionManager' does not exist on type 'NullVM'`,
`Module '"./interfaces"' declares 'Instruction' locally, but it is not exported`.

18,856 lines that cannot be built is the largest single block of unverified code
in the project. It contains `v10/` (coroutines, channels, structured concurrency,
JIT/GC scaffolding), `ai/`, `quantum/`, `distributed/` and `security/` — none of
which can be executed.

### Native backend — `bootstrap/native.null`, 4,363 lines

The only runtime that produces a real executable. Documented separately in
[`NATIVE_RUNTIME.md`](NATIVE_RUNTIME.md). 34 `null_*` runtime entry points,
inline x86-64 assembly, `malloc`-based with 11 allocation sites and no `free`.

## The IR

`bootstrap/ir.null` documents 53 opcodes and mirrors
`src/null_system/superbit/ir.py`. The two agree on the numbering:

```
LOAD_CONST=1 LOAD_VAR=2 STORE_VAR=3 BINARY_ADD=10 BINARY_SUB=11 BINARY_MUL=12
BINARY_DIV=13 COMPARE_GT=20 COMPARE_LT=21 COMPARE_EQ=22 COMPARE_NE=23
COMPARE_GE=24 COMPARE_LE=25 LOGICAL_AND=26 LOGICAL_OR=27 PRINT=30 INPUT=31
FILE_READ=32 FILE_WRITE=33 FILE_EXISTS=34 LIST_FILES=35 JUMP_IF_FALSE=40
JUMP=41 MATCH_TAG=50 UNWRAP_UNION=51 MATCH_PATTERN=52 SAFE_CALL=60
ELVIS_CHECK=61 NOT_NULL_CHECK=62 SMART_CAST=63 CALL=70 RETURN=71 ARRAY=72
INDEX=73 FUNCTION=74 NOP=255
FAST_ADD_INT=100 FAST_ADD_FLOAT=101 FAST_LT_INT=102 FAST_INDEX=103
FAST_LEN=104 FAST_INDEX_STORE=105 FAST_ARRAY_ZERO=107 FUSED_MAP=110
FUSED_FILTER=111 FUSED_REDUCE=112 FUSED_COMPREHEND=113 SIMD_ADD=120
SIMD_MUL=121 SIMD_SUM=122 GPU_KERNEL=130 DIST_SEND=140 DIST_RECV=141
```

The IR is well-defined. What is missing is lowering for the upper half of it:
`MATCH_TAG`/`MATCH_PATTERN` are emitted but the backend does not branch on them,
`SAFE_CALL`/`ELVIS_CHECK`/`SMART_CAST` have no implementation, and
`FUSED_*`/`SIMD_*`/`GPU_KERNEL`/`DIST_*` are declared and partially emitted with
no complete backend.

## The super-bit layer

`src/null_system/superbit/` (7 files, 1,643 LOC) is the binary encoding of IR
tokens. It is **broken**:

- `emitter.py` `AST_TO_SUPERBIT_TABLE` maps AST node types to bare strings
  (`"BINARY_ADD"`) instead of `SuperBitOpCode.BINARY_ADD` members.
- `ir.py:94` then does `int(self.opcode)` → `ValueError: invalid literal for
  int() with base 10: 'BINARY_ADD'`.
- `ir.py:129` `to_bytes()` joins tokens, so every encode path fails.
- `tests/superbit/test_tokens.py` fails with `assert 1 == 6`, a second, separate
  encoding defect.
- `SuperBitEncoder` is referenced but not defined (`NameError`).

`src/null_system/binary/generator.py:102` calls `superbit_stream.to_bytes()`, so
the whole compile-to-binary path is down. 12 of the 57 failures trace here.

## Language features claimed vs delivered

`docs/null_v2_language_spec.md` is marked **"Status: Blueprint/Roadmap"** and
lists ownership, pattern matching, async/await, SIMD, null-safety and generics.
`docs/bootstrap_phase1_completion.md` claims Phase 1 "Language Completeness" is
**COMPLETE**, citing 52 passing tests. `docs/bootstrap_phase2_runtime_status.md`
contradicts it and says Phase 2 is "not complete".

Measured reality, feature by feature:

| Feature | Lexed | Parsed | Emitted to IR | Executed correctly |
| --- | --- | --- | --- | --- |
| `fn` + params + return | yes | yes | yes | **yes** (native) |
| `let` / `let x: T` | yes | yes | yes | **yes** |
| `while` / `for … in` | yes | yes | yes | **yes** |
| `if` / `else` | yes | yes | yes | **yes** |
| arrays, `LEN`, index | yes | yes | yes | **yes** |
| strings, concat, index | yes | yes | yes | **yes** |
| recursion | yes | yes | yes | **yes** |
| `match` | yes | yes | yes | **no** — no branch emitted |
| float literals | no | no | no | **no** — lexes as `get_member` |
| map / object literal | yes | partial | yes | **no** — `UNSUPPORTED OP!!` |
| `own` / `borrow` / `move` | yes | yes | no | **no** — never checked |
| `async` / `await` | yes | yes | partial | **no** |
| `trait` / `sealed` | yes | yes | no | **no** |
| `data class` | yes | yes | wrong | **no** — becomes `INDEX`/`STORE_VAR` |
| generics `Type<T>` | yes | yes | no | **no** |
| `?.` / `?:` / `!!` | yes | yes | yes | **no** — no lowering |
| SIMD / fused | — | — | partial | **no** |

The pattern is consistent: the front end accepts a wide surface and the backends
implement a narrow one, with no diagnostic when the two disagree.

## Recommendation

Collapse to one pipeline:

```
one grammar → one AST → one IR → one backend
```

The bootstrap chain is the only one that already reaches machine code. The
Python `lang/` front ends and the TypeScript VM should be retired, not repaired,
unless a specific capability is only available there. That decision belongs to
Phase 1, and it is the blocking decision for everything after it.
