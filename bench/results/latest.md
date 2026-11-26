# Null benchmark results

- timestamp: `2026-11-26T12:19:28Z`
- machine: `Linux 4.19.0-gvisor` (2 cores, unknown)
- cpu flags: `fma,sse4_2,avx2`
- runs per configuration: 5 (median reported)
- baseline flags: `-O3 -march=native`

## Median wall time (ms) and peak RSS (KiB)

| workload | Null native | C -O3 | C/Null | Null RSS | C RSS |
| --- | --- | --- | --- | --- | --- |
| `sum_loop` | 10.6 | 44.5 | 4.20x | 3024 | 4420 |
| `comprehension` | 18.0 | 13.6 | 0.76x | 2276 | 3964 |
| `array_map` | 235.1 | 174.7 | 0.74x | 127872 | 127872 |
