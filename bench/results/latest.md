# Null benchmark results

- timestamp: `2026-11-26T12:45:14Z`
- machine: `Linux 4.19.0-gvisor` (2 cores, unknown)
- cpu flags: `fma,sse4_2,avx2`
- runs per configuration: 5 (median reported)
- baseline flags: `-O3 -march=native`

## Median wall time (ms) and peak RSS (KiB)

| workload | Null native | C -O3 | C/Null | Null RSS | C RSS |
| --- | --- | --- | --- | --- | --- |
| `sum_loop` | 8.4 | 33.5 | 3.99x | 2784 | 3888 |
| `comprehension` | 16.9 | 12.6 | 0.75x | 3260 | 3444 |
| `array_map` | 218.0 | 156.2 | 0.72x | 128356 | 128952 |
