# Bootstrap

How Null compiles itself today, what the two fixed points actually prove, and
what still stands between this and "no Python in the pipeline".

## The stages

| Stage | File | Lines | Role |
| --- | --- | --- | --- |
| 1 | `bootstrap/lexer.null` | 256 | character-class lexer |
| 2 | `bootstrap/parser.null` | 2,286 | recursive-descent parser → unified AST |
| 3 | `bootstrap/emitter.null` | 2,944 | lexer + parser + AST → super-bit IR |
| 4 | `bootstrap/native.null` | 4,363 | IR → x86-64 assembly |
| — | `bootstrap/vm.null` | 715 | IR interpreter (the VM path) |
| — | `bootstrap/ir.null` | 311 | opcode table + IR contract |
| — | `bootstrap/link.null` | 124 | assembles `nullc.null` |
| — | `bootstrap/nullc.null` | 3,557 | **generated**, do not edit |
| — | `bootstrap/input.null` | 7 | the source being compiled |

`bootstrap/emitter.null` is a concatenation of stages 1-3, with section headers
at lines 289 and 2341 and the linked entry point at 2914. That is why it opens
with the comment `// bootstrap/parser.null`.

## The link step

Null has no module system. `bootstrap/link.null` builds `nullc.null` by
concatenating every top-level `fn` block from `emitter.null` and `vm.null`, once,
followed by a generated driver:

```null
let parts = ["bootstrap/emitter.null", "bootstrap/vm.null"];
// ...gather every top-level `fn` block, skipping duplicate names...
out = APPEND(out, "let source = READ_FILE(\"bootstrap/input.null\");");
out = APPEND(out, "let ir = compile_to_ir_text(source);");
out = APPEND(out, "WRITE_FILE(\"bootstrap/program.ir\", ir);");
out = APPEND(out, "if FILE_EXISTS(\"bootstrap/compile-only.flag\") == false {");
out = APPEND(out, "    run(parse_rows(ir));");
out = APPEND(out, "}");
WRITE_FILE("bootstrap/nullc.null", JOIN(out, "\n"));
println("LINKED " + TO_STRING(LEN(names)) + " functions -> bootstrap/nullc.null");
```

Two consequences worth knowing before editing those files:

1. **A top-level `}` must be at column 0.** The block scanner finds the end of a
   function by testing `lines[i] == "}"` exactly. Nested braces are assumed to be
   indented, so no brace counting is done. Indenting a top-level closing brace
   breaks the link.
2. **`nullc.null` is generated and checked in.** It is committed so it can be read
   and diffed, but hand edits are lost on the next `link.null` run.

The `compile-only.flag` exists to stop infinite recursion: `nullc` writes
`program.ir` and, unless the flag is present, immediately executes it.

## The VM fixed point

```
$ SKIP_NATIVE=1 bash bench/selfhost_check.sh
PASS identical IR: 13665 rows, 286648 bytes, no unsupported rows
     nullc 73885 ms, emitter 68972 ms (host VM, this machine)
```

What it does:

1. `bootstrap/nullc.null` (the linked compiler) compiles `bootstrap/nullc.null`.
2. `bootstrap/emitter.null` (stage 3 alone) compiles the same source.
3. The two IR texts must be byte-identical.
4. The IR must contain zero `unsupported: … lang … todo` rows.

Step 3 is a genuine fixed point: the linked compiler and the standalone emitter
agree. Step 4 prevents the trivial cheat where both produce the same IR because
both gave up on the same statements.

What it does **not** prove: both stages run on the **Python VM**, via
`bench/stage_runner.py`. So this establishes compiler correctness, not the
absence of Python.

## The native fixed point

```
$ bash bench/selfhost_check.sh
PASS identical IR: 13665 rows, 286648 bytes, no unsupported rows
PASS native fixed point: 13665 rows, identical to the VM, no FALLBACK
```

The extra stage, from `bench/selfhost_check.sh`:

1. `emitter.null` produces `program.ir` for `nullc.null`.
2. `native.null` lowers that IR to `program.s`.
3. `backend.report` must contain **zero** `FALLBACK` lines.
4. `cc -O0` assembles `program.s` into a real binary.
5. **That binary** compiles `nullc.null`.
6. Its IR must be byte-identical to the Python VM's IR for the same source.

This is the strong result. A 4,363-line Null program, lowered to x86-64 by Null's
own backend with no fallbacks, produces a binary that reproduces the reference
compiler's output exactly. The native backend is not delegating and not
miscompiling.

Both fixed points were re-verified in this session rather than taken from
existing documentation.

## Timings

| Measurement | Time |
| --- | --- |
| `nullc.null` compiles itself (host VM) | 73,885–88,528 ms |
| `emitter.null` compiles `nullc.null` (host VM) | 68,972–80,289 ms |
| `native.null` on a small input | ~0.6 s |
| `native.null` compiling itself | ~200–240 s |

The two VM figures are a range from two runs on the same machine at different
loads; the IR size was identical (13,665 rows, 286,648 bytes) both times.

The native backend is **slower** than the Python VM on the self-compile, because
the backend's own runtime is unoptimized and allocates without freeing. No
comparison has been published; this table is the first honest one.

## Why Python is still in the pipeline

`bench/stage_runner.py`, 33 lines:

```python
from null_system.lang.compiler import NullLangCompiler
from null_system.lang.modern.modern_rust import ModernRustParser
from null_system.vm.vm import NullVM

result = NullVM().execute(NullLangCompiler().compile(ModernRustParser().parse(source)))
```

Every `.null` stage is executed by **parsing it with the Python Lark parser and
running it on the Python VM**. The native fixed point proves the *compiler* is
real; it does not prove the *build* is. To rebuild `nullc` from scratch on a
machine without Python, there is no path:

- `stage_runner.py` requires Python, `PYTHONPATH=src`, and `lark`.
- There is no committed seed binary.
- There is no build script that uses only a previously built `nullc`.

That is the Phase 4 gap. Closing it requires a bootstrap chain of the form:

```
seed binary (committed, opaque)  ->  compiles emitter.null  ->  nullc stage 1
                                 ->  compiles emitter.null  ->  nullc stage 2
                                 ->  stage 1 IR == stage 2 IR
```

The pieces exist — `nullc` already compiles itself to a byte-identical IR — what
is missing is committing a seed artifact and writing the driver in Null rather
than in Python.

## Requirements to reproduce

```bash
# VM fixed point (needs Python + lark)
SKIP_NATIVE=1 bash bench/selfhost_check.sh

# full fixed point (also needs cc)
bash bench/selfhost_check.sh
```

`bench/selfhost_check.sh` sets `STAGES_CMD` to
`env PYTHONPATH=$ROOT/src $ROOT/venv/bin/python`, so a working `venv/` is
assumed. It writes into `bench/build/selfhost/` and `bench/build/selfhost_native/`,
both gitignored.

## Invariants a change must not break

1. `bootstrap/nullc.null` stays in sync with `link.null` — regenerate it, never
   hand-edit.
2. Top-level `}` at column 0 in any file fed to `link.null`.
3. The IR format is fixed by `bootstrap/ir.null`; the opcode numbers must match
   `src/null_system/superbit/ir.py`.
4. The IR must stay free of `unsupported:` rows for the compiler's own source,
   or the fixed point check fails by design.
5. `backend.report` must show zero `FALLBACK` when lowering `native.null` itself.

## Known weaknesses in the bootstrap

- Float literals and `match` arms now lower correctly (Phase 1); the remaining
  diagnostic gap is that errors have no source location, so a message names the
  construct but not the line.
- `link.null`'s block scanner is line-based and depends on brace indentation.
- Nothing in the bootstrap chain type-checks; the native backend is dynamically
  typed.
- The bootstrap front end accepts a much wider syntax than the backend lowers,
  so unsupported constructs fail at runtime (`UNSUPPORTED OP!!`, exit 4) rather
  than at compile time.
