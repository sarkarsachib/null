# Null Performance & Power Contract

This document records the primary goal of the language, which earlier documents
left implicit:

> Null must be **at least 10x faster than Rust and C++** on comparable workloads,
> and must be **more expressive than any existing language** — the power of every
> language and beyond, without trading that power for speed.

Nothing in this document is a claim about current measurements. It is the design
contract every stage is built against, and the yardstick the native backend will
be judged by.

## 1. Why the bootstrap host cannot demonstrate it

`bootstrap/*.null` runs on the Python host VM. That VM is a tree-walking
interpreter for the bootstrap pipeline; it exists to *prove* the stages in Null,
not to run user programs fast. Any performance number produced by it is a
property of the host, not of Null.

The 10x target therefore belongs to the **native backend** that consumes the
super-bit IR. It must be measured with benchmarks (see §6), never asserted.

## 2. Where the speed comes from

Performance is an architectural property, planned per stage:

| Lever | Design decision |
| --- | --- |
| No interpreter tax | Every stage lowers to super-bit IR; the native backend compiles IR, it does not walk an AST. |
| No GC pauses | Ownership (`own`/`borrow`/`move`) gives deterministic destruction; no tracing collector on the hot path. |
| No dynamic typing | Static types + monomorphisation: generics are specialised at compile time, so hot code has no tag checks or boxing. |
| Compact code | Super-bit encoding keeps opcode+operand in one machine word, improving I-cache density and decode throughput. |
| Bounds-check elimination | `FAST_INDEX` / `FAST_LEN` on proven-safe indices. |
| Loop fusion | Comprehensions and pipelines lower to `FUSED_COMPREHEND` / `FUSED_MAP` / `FUSED_FILTER` — one pass, no closure allocation. |
| Data-parallel by default | The layer system routes element-wise work to `SIMD_*`, and bulk work to `GPU_KERNEL`. |
| Branchless null-safety | `?.`, `?:`, `!!` lower to `SAFE_CALL`/`ELVIS_CHECK`/`NOT_NULL_CHECK` with no exceptions and no allocation. |
| Pattern dispatch | `match` lowers to `MATCH_TAG` + jump tables when arms are tag-disjoint; no linear test chain. |
| Escape analysis | Values that never escape stay on the stack. |

## 3. Where the power comes from

Power, in this language, means the same program can express more without giving
up control:

- **Two surface syntaxes, one AST** — English (`SET x TO`, `DEFINE … END DEFINE`)
  and Modern (`let`, `fn`) are the same language; the parser proves it by
  producing identical nodes.
- **Null-safety in the type system**, not in runtime checks.
- **Pattern matching** with variants, guards, and exhaustive dispatch.
- **Pipelines and comprehensions** as first-class syntax that compile to fused
  loops.
- **Ownership** without a borrow checker's ceremony (`borrow`, `borrow_mut`).
- **Layer annotations** (`@layer`, `requires`, `prefers`) that let one program
  target scalar, SIMD, GPU or distributed execution.
- **Modules** (`::` paths) and sum types (`sealed`) as language features, not
  library conventions.

## 4. Opcode budget

The documented opcode set (`LOAD_CONST=1` … `NOP=255`) is mirrored in
`bootstrap/ir.null`. The optimiser may additionally emit the specialised range:

```
FAST_ADD_INT=100  FAST_ADD_FLOAT=101  FAST_LT_INT=102  FAST_INDEX=103  FAST_LEN=104
FUSED_MAP=110     FUSED_FILTER=111    FUSED_REDUCE=112 FUSED_COMPREHEND=113
SIMD_ADD=120      SIMD_MUL=121        GPU_KERNEL=130
DIST_SEND=140     DIST_RECV=141
```

Every specialised token has an exact generic fallback (`ir_fallback`), so a
backend that cannot honour one still executes the same semantics.

## 5. Non-negotiable constraints

1. No feature may be added that forces boxing, GC, or a dynamic dispatch on a
   hot path. Perceived convenience that costs a pointer chase is rejected.
2. The generic lowering is always correct first; specialised lowering must be
   provably equivalent.
3. Every stage is written in Null. The Python tree is the host, not the language.
4. English and Modern syntaxes never diverge in semantics — enforced by the
   equivalence test in `tests/bootstrap/test_self_hosted_parser.py`.

## 6. Measurement plan

| Benchmark | Compares |
| --- | --- |
| `nbody`, `fannkuch`, `mandelbrot` | scalar loops vs Rust/C++ |
| map/filter/reduce over arrays | fused comprehensions vs iterator chains |
| allocation-heavy tree workloads | ownership vs GC |
| matrix multiply | `GPU_KERNEL`/`SIMD_*` vs scalar baselines |
| string/parse workloads | super-bit decode vs bytecode interpreters |

Each benchmark records: source, compiler flags, host CPU, wall time, peak RSS.
A 10x claim requires the median of at least five runs per configuration, on the
same machine, with both baselines built `-O3`/`-C opt-level=3`.

### 6.1 Harness

`bench/run_bench.sh` runs each workload `RUNS` times (default 5, median reported),
once through the stage-5 native backend and once as a C baseline built with
`cc -O3 -march=native`, and records wall time plus sampled peak RSS in
`bench/results/latest.md` and `.json`.

- Source of truth: `bench/workloads/<workload>.null` is lowered by the
  *self-hosted* stage-3 emitter (`bench/emit_workloads.sh` → `bench/ir/*.ir`),
  then by `bootstrap/native.null` to x86-64 assembly, then assembled by `cc`.
  The only workload still hand-written in IR is `array_map`, marked
  `hand-authored-ir` in its source because the emitter has no `APPEND` lowering.
- Baseline: `bench/c/<workload>.c` (the C stand-in for the Rust/C++ baseline;
  there is no `rustc` in this sandbox).
- Timing and RSS live in `bench/measure.py`: wall time comes from
  `perf_counter_ns` around `subprocess.run` with no sampler running, and peak
  RSS from a separate untimed run that polls `VmRSS`/`VmHWM` in-process. The
  earlier in-shell `/proc` sampler forked a `sleep` per poll, which added about
  10 ms to every measurement — larger than a whole short workload — and the
  numbers before 2026-11-26T12:19Z are inflated by that on both sides.
- Front-end latency is not a scaling risk any more: measured on this host the
  stage-3 emitter lowers a 7-statement program and the full `sum_loop` source in
  ~0.73 s of wall time. Earlier notes that claimed it needed minutes were wrong.

### 6.2 Measured result (stage 5, 2026-11-26T21:14Z)

Machine: Linux 4.19.0-gvisor, 2 shared cores, AVX2/FMA, CPU model not exposed.
Workloads: `sum_loop` (sum 1..1e8), `comprehension` (sum of even squares 1..2e7),
`array_map` (`total += a[i]*3 + b[i]` over 8M i64 elements).
Baseline: `cc -O3 -march=native`. Every Null binary prints the identical result
to its C baseline, so each comparison is semantics-equal.

| workload | Null native | C `-O3` | C/Null | Null RSS | C RSS |
| --- | --- | --- | --- | --- | --- |
| `sum_loop` | 10.1 ms | 36.5 ms | **3.61x** | 2356 KiB | 3148 KiB |
| `comprehension` | 6.4 ms | 19.7 ms | **3.08x** | 3204 KiB | 3660 KiB |
| `array_map` | 63.9 ms | 75.9 ms | **1.19x** | 127416 KiB | 128776 KiB |

Absolute times on this host move by up to ~20% between runs (the two cores are
shared and the C baseline moves with them), so the ratio against the same run's
baseline is the number to read, not the millisecond column.

All three binaries are built from `.null` sources by the self-hosted pipeline
(`bench/workloads/*.null` → `bootstrap/emitter.null` → `bench/ir/*.ir` →
`bootstrap/native.null` → asm), except `array_map`, which is hand-written IR for
the reason given in 6.3.

**Verdict: the 10x target is not demonstrated.** All three workloads are now
faster than `cc -O3` — 3.61x on the counting loop, 3.08x on the filtered square
sum and 1.19x on the array kernel — and the gap closes exactly where the backend
recognises a vector form. `array_map` was 28% behind in the previous run and is
19% ahead here, the largest single gain since instruction selection.

What closed the gap. The first three rows were recorded with the old in-shell
sampler, which added roughly a constant ~10 ms to a short workload whichever
side it measured; they are kept for the trend, and the last two rows use
`bench/measure.py`:

| change | `sum_loop` | `comprehension` | `array_map` |
| --- | --- | --- | --- |
| template expander, everything in stack slots | 797 ms | 249 ms | — |
| hot variables in callee-saved registers (r12-r15), redundant load/store peephole, `cmp`+`setcc`+`test` folded into one conditional jump | 70 ms | 183 ms | — |
| IR-level instruction selection: register-to-register arithmetic, fused compare+branch, fused `c = c + a*b`, `x MOD 2^k == 0` lowered to `test`/`jne` | 61 ms | 44-65 ms | — |
| strength reduction of the emitted `x - (x / 2^k) * 2^k == 0` idiom to `test x, 2^k-1` (kills the last `idiv`) | 61 ms | 15-18 ms | — |
| 8-wide AVX2 reduction loop: two 4-lane i64 accumulators, constant iota vector advanced by 8, horizontal sum, original scalar loop kept as the tail | **10.6 ms** | — | — |
| filtered square reduction: two iota windows per pass (second is iota+4, so no two lanes coincide), AVX2 64-bit square, `vpcmpeqq` lane mask for divisibility by a power of two, masked accumulate into two 4-lane accumulators | — | **8.2 ms** | — |
| array kernel vector forms: 4-wide fill (one iota vector and its double stored per pass) and 8-wide `acc += a[i]*3 + b[i]` (two 4-lane accumulators, `3a` as `(a << 1) + a`, scalar tail) | — | — | **63.9 ms** |

The array kernels are now strictly AVX2. `SIMD_MUL` used to emit `vpmullq`,
which is AVX512DQ+VL — it worked here only because the emulated CPU behind this
gVisor host tolerates it, and it would trap on a real AVX2-only machine, so the
kernel now computes the low 64 bits of each lane product with three `vpmuludq`
plus shifts and adds. Correctness is unchanged (identical output) and the ratio
went from 0.74x to 0.72x against a baseline that was itself 11% faster in this
run, i.e. inside the noise above.

The generated `sum_loop` loop is now three vector instructions per eight
iterations plus `lea`/`cmp`/`jg`/`add`/`jmp`; `comprehension` is `cmp`/`jg`,
`test`/`jne`, `mov`/`imul`/`add`, with no stack traffic and no division.
`array_map`'s fill loop is two 32-byte stores per four elements, and its map loop
is two 32-byte loads, three arithmetic ops and one accumulate per four elements,
with the index, bound and base pointers held in registers for the whole loop.

Next levers, in order of expected payoff: a push/append opcode (106) so
`array_map`'s own source can be lowered by the emitter instead of hand-authored
IR, a fused array-map opcode (110-113 need captured lambdas in the IR), and loop
unrolling by two for the four vector bodies, which are all still one window per
branch.

### 6.3 Not yet measurable

- Array-input `FUSED_COMPREHEND` (113) and the `FUSED_MAP`/`FILTER`/`REDUCE`
  family (110-112): these need captured lambdas in the IR, which the front end
  does not emit yet. `array_map` runs as an explicit loop instead.
- Growable arrays: there is still no push/append opcode, so arrays are
  pre-sized with 107 (`FAST_ARRAY_ZERO`) and filled with 105
  (`FAST_INDEX_STORE`). Opcode 106 remains a documented `FALLBACK`.
- `GPU_KERNEL` (130), `DIST_SEND`/`DIST_RECV` (140/141), float add (101) and
  string `concat` are reported as `FALLBACK` by the backend and trap with
  `null_unsupported` (exit 4) instead of silently doing something slower.
- `SIMD_SUM` (122) lowers to a real AVX2 horizontal reduction and
  `array_map` drives it.
- Vectorisation is pattern-driven, not a general vectoriser. Four loop shapes
  currently have a vector form: the canonical counting reduction
  (`while iv <op> n { acc += iv; iv += 1 }`), the filtered square reduction
  (`if ((iv / c) * c == iv) { acc += iv * iv }`, c a power of two), the two-array
  fill (`a[iv] = iv; b[iv] = iv * 2`) and the two-array map reduction
  (`acc += a[iv] * k + b[iv]`, k in {2, 3, 4}). The reductions require the
  induction variable, bound and accumulator in promoted registers; the array
  forms load a spilled pointer, bound or index into a scratch register for the
  loop and write a spilled index back on exit, so they do not depend on the
  frequency heuristic promoting all four values. Only `x MOD 2^k` (in either
  spelling) becomes a bit test. A loop with a non-unit stride, a non-power-of-two
  divisor, a different body, or a multiplier outside {2, 3, 4} stays scalar.

Status for the workloads above: **measured, target not met.** Status for the
rest: **targeted, not yet demonstrated.**
