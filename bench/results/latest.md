# Null benchmark results

- timestamp: `2026-11-26T21:23:12Z`
- machine: `Linux 4.19.0-gvisor` (2 cores, unknown)
- cpu flags: `fma,sse4_2,avx2,avx512f`
- runs per configuration: 5 (median reported)
- baseline flags: `-O3 -march=native`

## Median wall time (ms) and peak RSS (KiB)

| workload | Null native | C -O3 | C/Null | Null RSS | C RSS |
| --- | --- | --- | --- | --- | --- |
| `sum_loop` | 7.6 | 30.4 | 4.00x | 2184 | 3700 |
| `comprehension` | 6.2 | 9.3 | 1.50x | 3948 | 3164 |
| `array_map` | 63.4 | 61.0 | 0.96x | 127532 | 127904 |
