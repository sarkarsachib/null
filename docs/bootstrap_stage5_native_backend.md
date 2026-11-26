# Stage 5: The Native Backend

Stage 5 lowers the super-bit IR to x86-64 assembly. It is the first stage whose
output runs on the metal: `bootstrap/native.null` reads the IR, writes assembly,
and the benchmark harness assembles it with `cc`. There is no interpreter, no
dispatch loop and no host VM in the executed path.

Nothing here is a performance claim. Measurements live in
[`performance_contract.md`](performance_contract.md) §6.

## Contract

| | |
| --- | --- |
| Input | `bootstrap/program.ir` — TSV rows `IR\t<opcode>\t<operand>\t<layer>[\t<meta>]`, `LABEL\t<name>` |
| Output | `bootstrap/program.s` — GNU `as`, Intel syntax, System V ABI, `main` entry |
| Report | `bootstrap/backend.report` — one `LOWERED` / `FALLBACK` / `STAT` line per decision |
| Assembled by | `cc` (driven by `bench/run_bench.sh` or by hand) |

The IR format is the one documented by `bootstrap/ir.null`; the backend does not
invent an encoding of its own.

## Codegen model

- **No dispatch.** Every IR token expands to a fixed instruction sequence at
  backend time, so there is no opcode fetch, decode or switch at run time.
- **Fixed frame slots.** A pre-pass assigns each variable an offset; `LOAD_VAR`
  and `STORE_VAR` are single `mov`s. The evaluation stack is a fixed region of
  the same frame, addressed at compile time (`sp` is a compile-time counter).
- **Hot variables in registers.** A frequency pass counts each variable's
  loads+stores and promotes the four hottest to `r12`-`r15` (callee-saved, pushed
  by the prologue, written back at every `RETURN` and at the end of `main`).
  A promoted `LOAD_VAR`/`STORE_VAR` is a register `mov` until the variable is
  live in memory again. Skipped when the program declares functions, because the
  current pass has no interference analysis.
- **Vectorised reduction loops.** A loop whose whole shape is
  `LABEL; LOAD iv; LOAD n; cmp; JUMP_IF_FALSE exit; LOAD acc; LOAD iv; ADD;
  STORE acc; LOAD iv; LOAD 1; ADD; STORE iv; JUMP label` and whose `iv`, `n` and
  `acc` are all in promoted registers becomes an 8-wide AVX2 body: `iv` is
  broadcast into two iota vectors, two 4-lane i64 accumulators absorb eight
  iterations per pass, and the horizontal sum is added into `acc` before the
  original scalar loop runs as the tail. The tail is the same code, so a trip
  count below eight, or a remainder, is exact. `<` and `<=` are both handled; the
  `iv + 8` guard is a `lea`/`cmp`/`jg`, and the pointer arithmetic wraps rather
  than trapping at the top of the range.
- **Instruction selection over IR rows.** Before the per-token handlers run, five
  windows are matched and replaced whole: `LOAD a; LOAD b; arith; STORE c`
  becomes `add c, b` (or `mov`/`imul`/`mov` when the destination differs),
  `LOAD a; LOAD b; cmp; JUMP_IF_FALSE L` becomes `cmp a, b` + inverted `jCC`
  with no `setcc`/`test` round-trip, `c = c + a*b` becomes `mov`/`imul`/`add`,
  `(x MOD 2^k) == 0` becomes `test x, 2^k-1` / `jne` instead of `idiv` — and so
  does the `x - (x / 2^k) * 2^k == 0` spelling the front end emits, because the
  lexer has no `%` token.
  A three-row window (`LOAD a; LOAD b; arith`) keeps the result in `rax` and
  pushes it, which removes the redundant reload without breaking the stack
  invariant later tokens rely on.
- **Real calls.** `FUNCTION`/`CALL`/`RETURN` become `call`/`ret` with arguments
  and return value in registers, one frame per activation.
- **Typed lowering.** The specialised super-bit opcodes keep their guarantees:
  `FAST_ADD_INT` is a bare `add` with no tag check; `FAST_LT_INT` is
  `cmp`/`setl`; `FAST_INDEX` drops the bounds check that `INDEX` emits;
  `FAST_LEN` reads the array header; `SIMD_ADD`/`SIMD_MUL` run an AVX2 loop with
  a scalar tail; `FUSED_COMPREHEND` becomes one loop over the input with one
  output allocation.
- **Nothing silently degrades.** An opcode the target cannot honour yet is
  reported as `FALLBACK` and lowered to `call null_unsupported`, which prints a
  diagnostic and exits 4. A `FALLBACK` line in the report is a promise that the
  binary will refuse to run, not a quiet fallback to a slow path.

## Lowering table

| IR | Mnemonic | Emitted |
| --- | --- | --- |
| 1 | `LOAD_CONST` | immediate into the slot |
| 2 / 3 | `LOAD_VAR` / `STORE_VAR` | `mov` to/from the assigned frame slot, or a register `mov` when promoted |
| 10 / 12 | `ADD` / `MUL` | `add` / `imul` on the stack top |
| 20-25 | `EQ`…`LE` | `cmp` + `setCC` |
| 30 | `PRINT` | `call null_print_i64` |
| 40 / 41 | `JUMP_IF_FALSE` / `JUMP` | `je` / `jmp` to the named label |
| 70 | `CALL` | `call` (builtin calls inside the runtime) |
| 71 | `RETURN` | `leave` / `ret` |
| 100 | `FAST_ADD_INT` | unchecked integer `add` |
| 102 | `FAST_LT_INT` | `cmp` + `setl`, fused into `cmp`/`jge` before a branch |
| 103 | `FAST_INDEX` | unchecked element load |
| 104 | `FAST_LEN` | array header load |
| 105 | `FAST_INDEX_STORE` | unchecked `mov [arr + idx*8 + 8], value` (bounds proven) |
| 107 | `FAST_ARRAY_ZERO` | `call null_array_zero` (`calloc`, length in the header) |
| 113 | `FUSED_COMPREHEND` | one fused loop, `<var>\|<expr>\|<pred>` operand |
| 120 / 121 | `SIMD_ADD` / `SIMD_MUL` | AVX2 loop + scalar tail |
| 122 | `SIMD_SUM` | AVX2 4-lane i64 accumulation + horizontal add + scalar tail |
| — | counting reduction loop | 8-wide AVX2 (two 4-lane accumulators) + scalar tail |
| 255 | `HALT` | exit with the current value |

Reported as `FALLBACK` today: 101 (float add), 106 (`FAST_ARRAY_PUSH` — there
is no growable array yet), 110-112 (`FUSED_MAP`, `FUSED_FILTER`, `FUSED_REDUCE`
— they need captured lambdas), 113 with a malformed operand, 130
(`GPU_KERNEL`), 140/141 (`DIST_SEND`/`DIST_RECV`), and `CALL` of `concat`,
`__range__` and map/filter lambdas.

## Running it

```sh
# source -> IR, for every workload that is not marked hand-authored-ir
bench/emit_workloads.sh

# one program, directly
cp bench/ir/sum_loop.ir bootstrap/program.ir
env PYTHONPATH=src venv/bin/python bench/stage_runner.py bootstrap/native.null
cc -o /tmp/sum bootstrap/program.s && /tmp/sum

# the harness: median of 5 runs, Null vs cc -O3
bench/run_bench.sh
```

## Tests

`tests/bootstrap/test_native_backend.py` checks that the specialised templates
and the instruction-selection forms appear in the assembly (`add r13, r12`,
`cmp r12, r14`/`jge`, `test r12, 1`, `call null_array_zero`, the unchecked index
store), that the reduction loop becomes the AVX2 body (`vpbroadcastq`/`vpaddq`)
and still prints the exact result, that the vector tail is exact for trip counts
of 5, 8, 13 and 21, that the generated binaries print the C baselines' exact
results for `comprehension` and `array_map`, that `MOD 2^k` never emits `idiv`,
and that an unhonourable opcode is both reported and trapped. `tests/bootstrap` also covers
the language-level `&&`/`||` opcodes (26/27), which previously compiled to
nothing at all.

## Known gaps

- Vectorisation is one pattern, not a vectoriser. Only the canonical counting
  reduction (`acc += iv`) gets the 8-wide body; `comprehension` (filter plus
  multiply) and `array_map` stay scalar inside their loops, which is why those
  two are 24-26% behind C `-O3` (see §6.2 of the contract). Nothing is unrolled
  yet.
- Register promotion is frequency-based, not a real allocation (no liveness or
  interference), and is disabled for programs with functions.
- There is no growable array opcode (106 traps), so arrays must be pre-sized with
  107 and filled with 105.
- `array_map` is the one workload still authored directly in IR: its source needs
  `APPEND`, and there is no push opcode. Everything else is generated from
  `.null` source by `bootstrap/emitter.null` via `bench/emit_workloads.sh`
  (~0.7 s per workload, not the "too slow" the earlier revision of this document
  claimed).
- Floating point, string concatenation and distributed/GPU targets are declared
  unsupported rather than half-implemented.
