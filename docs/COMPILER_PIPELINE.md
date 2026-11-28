# Compiler Pipeline

The pipeline that produces an executable, stage by stage, with the exact files and
commands. Everything here was exercised in Phase 0.

## Stage map

```
source.null
    │
    ├── lexer ................ bootstrap/lexer.null (256 lines)
    │                          bootstrap/emitter.null:1-288 (inlined copy)
    │
    ├── parser ............... bootstrap/emitter.null:377-2004
    │                          unified AST; accepts both surface syntaxes
    │
    ├── IR emitter ........... bootstrap/emitter.null:2341-2913
    │                          AST -> super-bit IR text
    │
    ▼
bootstrap/program.ir  ................ TSV: IR / LABEL rows
    │
    ├── native backend ....... bootstrap/native.null (4363 lines)
    │                          IR -> x86-64 GNU as (Intel syntax)
    │
    ▼
bootstrap/program.s
    │
    ├── cc -O0 ............... GNU as / ld
    ▼
executable
```

There is also a VM path that executes the IR directly:
`bootstrap/vm.null` (715 lines), used by `bench/stage_runner.py` on the Python VM.

## Stage 1 — lexer

`bootstrap/lexer.null` is 256 lines and is a **character-class** lexer: it works
on numeric character codes rather than pattern matching.

```null
fn is_digit(code: Num) -> Bool {
    if code >= 48 {
        if code <= 57 {
            return true;
        }
    }
    return false;
}
```

The same functions are inlined at the top of `bootstrap/emitter.null` (lines
1-288), which is why that file begins with the comment `// bootstrap/parser.null`.
`emitter.null` is a **concatenation** of the lexer, the parser and the IR emitter,
with section headers at lines 289, 2341 and 2914 marking the boundaries.

`3.5` is a single `NUMBER` token: `scan_number` takes a fractional part only at
a `.` followed by a digit, so `..` (range) and `1.foo` (member access) are
unaffected. Fixed in Phase 1 (was P0-2).

## Stage 2 — parser

Recursive descent over a token array. The parser normalizes both surface syntaxes
into one AST, recording which surface a construct came from in `__mode_log` for
diagnostics only.

Section structure of `emitter.null`:

| Lines | Content |
| --- | --- |
| 1-288 | lexer (character classes, tokenizer) |
| 289-376 | unified AST node definitions |
| 375-790 | declarations (`parse_type`, `parse_params`, `parse_block`, `parse_fn`, `parse_define`, `parse_let`, `parse_set`, `parse_add`, `parse_type_alias`, `parse_data_class`, `parse_sealed`, `parse_trait`, `parse_module`, `parse_import`) |
| 790-1039 | patterns (`parse_pattern`, `parse_match`) |
| 1040-1656 | expressions (`parse_pipe_step`, `parse_primary`, `parse_arguments`, `parse_array`, …) |
| 1657-2004 | statements |
| 2005-2340 | canonical renderer (syntax-independent) |
| 2341-2913 | IR emitter |
| 2914-end | linked-compiler entry point |

99 `fn` definitions in total.

## Stage 3 — IR emitter

Produces the TSV text form. Each row is:

```
IR	<opcode>	<operand>	<layer>[	<meta>]
LABEL	<name>
```

Example — `let n = 2; match n { 1 => { println("one"); } 2 => { println("two"); } }`:

```
IR	1	2	scalar
IR	3	n	scalar
IR	2	n	scalar
IR	50	NUM 1	match
IR	1	one	scalar	str
IR	30		scalar
IR	41	L_s1_end	control
LABEL	L_s1_a0
IR	50	NUM 2	match
IR	1	two	scalar	str
IR	30		scalar
IR	41	L_s1_end	control
LABEL	L_s1_a1
IR	52	no_match	match
LABEL	L_s1_end
IR	255	HALT	scalar	end
```

Layers: `scalar`, `simd`, `lang`, `control`, `match`. The layer is carried so a
backend can route work by layer.

The IR is documented authoritatively by `bootstrap/ir.null`, which contains a
`fn ir_opcode(name: Text) -> Num` mapping all 53 names to numbers and mirrors
`src/null_system/superbit/ir.py`. The two agree. Full table in
[`ARCHITECTURE_AUDIT.md`](ARCHITECTURE_AUDIT.md) § The IR.

`match` lowers to a real chain: the subject is stored in a hidden slot, each
literal arm emits `EQ` (22) + `JUMP_IF_FALSE` (40) to the next arm, the arm body
ends with an unconditional jump past the chain, and a wildcard arm is fallthrough.
Variant patterns (`Ok(x)`) still emit `MATCH_PATTERN` (52), which traps rather
than running the wrong arm.

A construct the emitter cannot lower becomes `IR 255 … lang todo` and is
reported as `ERROR: unsupported construct: …` — see
[`ROADMAP_STATUS.md`](ROADMAP_STATUS.md) § 1.4.

## Stage 4 — native backend

`bootstrap/native.null`, 4,363 lines. Reads `bootstrap/program.ir`, writes
`bootstrap/program.s` and `bootstrap/backend.report`.

The report is the audit trail:

```
STAT reg x -> r12
FALLBACK 70 unknown-call-get_member
STAT max-operand-sp 1
```

Three line kinds:

- `LOWERED <opcode>` — handled by real instruction selection
- `FALLBACK <opcode> <reason>` — emitted as `call null_unsupported`, which prints
  `UNSUPPORTED OP!!` and exits 4 at runtime
- `STAT <key> <value>` — register allocation and stack statistics

The fallback set, with line references in `native.null`:

| Opcode | Reason | Line |
| --- | --- | --- |
| 70 | `concat-string-runtime-not-in-this-stage` | 3730 |
| 70 | `range-object-not-in-this-stage` | 3735 |
| 70 | `filter-lambda-capture-not-in-this-stage` | 3740 |
| 70 | `map-lambda-capture-not-in-this-stage` | 3745 |
| 70 | `unknown-call-<name>` | 3751 |
| 101 | `fast-add-float-float64-not-in-this-stage` | 3965 |
| 110 | `fused-map-needs-captured-lambda` | 4054 |
| 111 | `fused-filter-needs-captured-lambda` | 4058 |
| 112 | `fused-reduce-needs-captured-lambda` | 4062 |

`FALLBACK` is honest — it does not silently miscompile. But it means the
advertised surface is wider than the implemented one, and the failure appears at
runtime, not at compile time.

Details of the code generator are in [`NATIVE_RUNTIME.md`](NATIVE_RUNTIME.md).

## Stage 5 — assembly

```
cc -O0 -o prog bootstrap/program.s
```

`cc` is the assembler and linker. There is no Null-side assembler. The emitted
assembly is GNU `as`, Intel syntax, System V AMD64 ABI, with `main` as the entry
point. `-O0` is deliberate: the backend's own instruction selection is what is
being tested, not the C compiler's.

## The link step

`bootstrap/link.null` (124 lines) assembles `bootstrap/nullc.null` from the stage
files. The language has no module system yet, so it concatenates every top-level
`fn` block from each part, once, followed by the driver.

```
// A top-level block starts at `fn ` and ends at the first column-0 `}`;
// nested braces are indented, so no brace counting is needed.
```

That is a real constraint on the source: a top-level `}` must be at column 0. It
also means **`nullc.null` is generated and must not be hand-edited**. It is
checked in so it can be read and diffed.

## How to run each stage

```bash
# one stage on the host VM (Python required)
PYTHONPATH=src ./venv/bin/python bench/stage_runner.py bootstrap/emitter.null

# a probe program: emitter -> backend -> assemble -> run
#   writes <dir>/bootstrap/input.null, expects <dir>/bootstrap/program.ir
cd <dir> && PYTHONPATH=src venv/bin/python bench/stage_runner.py .../emitter.null
cc -O0 -o prog <dir>/bootstrap/program.s && ./prog

# the fixed-point oracle
bash bench/selfhost_check.sh              # VM + native
SKIP_NATIVE=1 bash bench/selfhost_check.sh  # VM only
```

`bench/stage_runner.py` requires `PYTHONPATH=src`. It is Python, and it is the
only way to run a `.null` stage — that is the Phase 4 blocker, documented in
[`BOOTSTRAP.md`](BOOTSTRAP.md).

## Measured timings

| Stage | Time | Note |
| --- | --- | --- |
| `nullc.null` compiles itself (host VM) | 73,885–88,528 ms | two runs, different load |
| `emitter.null` compiles `nullc.null` (host VM) | 68,972–80,289 ms | same two runs |
| `native.null` on a small input | ~0.6 s | |
| `native.null` compiling itself | ~200–240 s | |

The VM path is roughly 70 seconds to compile 3,557 lines. That is the performance
baseline the native backend must beat, and no such comparison has been published.

## Output contract

| Artifact | Written by | Consumed by |
| --- | --- | --- |
| `bootstrap/input.null` | caller | lexer |
| `bootstrap/program.ir` | IR emitter | native backend, VM |
| `bootstrap/program.s` | native backend | `cc` |
| `bootstrap/backend.report` | native backend | humans, CI |
| `bootstrap/compile-only.flag` | caller | driver (suppresses execution) |

All five are relative to the process working directory, not the source file. That
is why every command in `bench/selfhost_check.sh` runs inside a prepared work
directory. These are build artifacts and are not committed.
