# Null benchmark results

- timestamp: `2026-11-26T12:55:22Z`
- machine: `Linux 4.19.0-gvisor` (2 cores, unknown)
- cpu flags: `fma,sse4_2,avx2`
- runs per configuration: 5 (median reported)
- baseline flags: `-O3 -march=native`

## Median wall time (ms) and peak RSS (KiB)

| workload | Null native | C -O3 | C/Null | Null RSS | C RSS |
| --- | --- | --- | --- | --- | --- |
| `sum_loop` | 9.6 | 31.2 | 3.25x | 3072 | 4484 |
| `comprehension` | 8.2 | 15.6 | 1.90x | 2348 | 4536 |
| `array_map` | 232.7 | 168.2 | 0.72x | 128764 | 128752 |
