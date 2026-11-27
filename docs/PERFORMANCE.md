# Performance

Phase 0 rule: performance claims must be measured, never asserted. This document
records the harness, the published numbers, and a measurement that **inverts**
the headline claim.

## The harness

`bench/run_bench.sh` builds each workload two ways and measures both:

- Null native: `bench/workloads/<name>.null` → `bootstrap/program.s` → `cc -O0`
- C baseline: `bench/c/<name>.c` → `cc -O3 -march=native`

Then runs each binary `RUNS` times (default 5), records wall time and peak RSS via
`bench/measure.py`, and reports the median. Results go to
`bench/results/latest.md` and `latest.json`.

Workloads: `sum_loop`, `comprehension`, `array_map`.

The methodology is sound in structure — median of repeated runs, same machine,
RSS recorded, timestamps and CPU flags captured. The problem is the baseline.

## Published numbers

From `bench/results/latest.md`, timestamp `2026-11-26T21:23:12Z`,
`Linux 4.19.0-gvisor`, 2 cores, `-O3 -march=native` baselines:

| workload | Null native | C -O3 | C/Null | Null RSS | C RSS |
| --- | --- | --- | --- | --- | --- |
| `sum_loop` | 7.6 ms | 30.4 ms | **4.00x** | 2,184 KiB | 3,700 KiB |
| `comprehension` | 6.2 ms | 9.3 ms | 1.50x | 3,948 KiB | 3,164 KiB |
| `array_map` | 63.4 ms | 61.0 ms | 0.96x | 127,532 KiB | 127,904 KiB |

## The `sum_loop` claim does not survive measurement

`bench/c/sum_loop.c`:

```c
int main(void) {
    volatile int64_t n = 100000000;
    int64_t total = 0;
    for (int64_t i = 1; i <= n; i++) {
        total += i;
    }
    printf("%lld\n", (long long)total);
    return 0;
}
```

`volatile` on `n` forces the comparison bound to be re-read from memory on every
iteration, which prevents the compiler from vectorizing or closed-forming the
loop. The C compiler cannot optimize the loop it is being benchmarked on.

Measured directly, same machine, same compiler, 7 runs, median:

| Baseline | Median | Min | Max |
| --- | --- | --- | --- |
| `sum_loop.c` as committed (`volatile n`) | **30.14 ms** | 29.70 | 31.40 |
| identical file, `volatile` removed | **1.46 ms** | 1.30 | 1.73 |

```
$ cc -O3 -march=native -o vol   bench/c/sum_loop.c
$ cc -O3 -march=native -o novol /tmp/novol.c      # same file, volatile removed
vol    median=  30.14 ms
novol  median=   1.46 ms
```

The `volatile` costs **20.6x**. So the published 4.00x "faster than C" is the
ratio between Null's 7.6 ms and a baseline that is ~20x slower than it should be.

Against the honest baseline:

```
1.46 ms (C, no volatile)  vs  7.6 ms (Null)  =>  Null is ~5.2x slower
```

The direction of the headline claim is wrong. This is the single most important
finding in this document, and the 4.00x figure must be withdrawn.

Note the same defect exists in `bench/c/comprehension.c:6`
(`volatile int64_t n = 20000000;`), so the 1.50x claim is suspect for the same
reason and has not been re-measured here.

## What the numbers do legitimately show

- **`array_map` at 0.96x** is the only honest comparison in the table, and it says
  Null is marginally slower than C. That is a plausible result for a backend that
  allocates on every element.
- **RSS 127,532 KiB for `array_map`** against 2,184 KiB for `sum_loop` is not an
  algorithmic property; it is the leak. `bootstrap/native.null` has 0 `free@PLT`
  sites, so the array workload's allocations are never reclaimed. The C baseline
  shows 127,904 KiB because it allocates a comparable array, but C's memory is
  returned to the allocator and Null's is not.

## Compile-time numbers

Measured in this session, not previously published:

| Measurement | Time |
| --- | --- |
| `nullc.null` compiles itself (host VM) | 73,885–88,528 ms |
| `emitter.null` compiles `nullc.null` (host VM) | 68,972–80,289 ms |
| `native.null` on a small input | ~0.6 s |
| `native.null` compiling itself | ~200–240 s |

The native backend is **slower** than the Python VM at self-compilation. There is
no published compile-speed comparison, and this table is the first honest one.

## Why the numbers are hard to trust

1. **The baseline is weakened by design.** `volatile` in two of three C
   baselines. Whether intentional or not, the effect is a 20x handicap.
2. **`-O0` for Null vs `-O3 -march=native` for C** is defensible — it measures the
   backend's own instruction selection rather than the C compiler's — but it must
   be stated, and it means the comparison is "Null's codegen vs GCC's best", not
   "two languages".
3. **`gvisor` kernel, 2 cores.** `Linux 4.19.0-gvisor` is a sandboxed VM with
   virtualized syscalls. Syscall-heavy workloads (every `println` uses `syscall`
   directly) are penalized in ways that do not reflect bare metal.
4. **The workloads are tiny.** 6-63 ms total runtime is within noise for a
   virtualized kernel; 5 runs and a median helps but does not eliminate it.
5. **`array_map`'s 127 MB RSS** means the measurement is partly measuring the
   allocator, not the language.

## What Phase 8 must do

1. Remove `volatile` from every C baseline, or justify it. Measured effect: 20.6x
   on `sum_loop`.
2. Re-run all three workloads and republish. Expect `sum_loop` and `comprehension`
   to reverse direction.
3. State `-O0` vs `-O3` explicitly in the results table.
4. Add workloads that are not microbenchmarks: something that parses, something
   that allocates strings, something that runs for seconds rather than
   milliseconds.
5. Fix the leak before publishing RSS numbers, or report RSS as a known defect
   rather than a metric.
6. Withdraw the 4.00x claim from `docs/performance_contract.md` until it is
   reproduced against a fair baseline.

## Reproduction

```bash
# the published numbers
RUNS=5 bash bench/run_bench.sh

# the volatile measurement
cc -O3 -march=native -o /tmp/vol   bench/c/sum_loop.c
sed 's/volatile int64_t n/int64_t n/' bench/c/sum_loop.c > /tmp/novol.c
cc -O3 -march=native -o /tmp/novol /tmp/novol.c
```

## Honest summary

| Claim | Status |
| --- | --- |
| Null is 4.00x faster than C on `sum_loop` | **Withdrawn** — measured against a fair baseline Null is ~5.2x slower |
| Null is 1.50x faster on `comprehension` | **Unverified** — same `volatile` defect in the baseline |
| Null is 0.96x on `array_map` | Consistent with the code; plausible |
| Null uses less memory | **False** — `array_map` uses 127 MB because nothing is freed |
| The native backend compiles faster than the VM | **False** — ~200-240 s vs 74 s |
