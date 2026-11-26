# Null benchmark results

- timestamp: `2026-11-26T21:14:15Z`
- machine: `Linux 4.19.0-gvisor` (2 cores, unknown)
- cpu flags: `fma,sse4_2,avx2,avx512f`
- runs per configuration: 5 (median reported)
- baseline flags: `-O3 -march=native`

## Median wall time (ms) and peak RSS (KiB)

| workload | Null native | C -O3 | C/Null | Null RSS | C RSS |
| --- | --- | --- | --- | --- | --- |
| `sum_loop` | 10.1 | 36.5 | 3.61x | 2356 | 3148 |
| `comprehension` | 6.4 | 19.7 | 3.08x | 3204 | 3660 |
| `array_map` | 63.9 | 75.9 | 1.19x | 127416 | 128776 |
