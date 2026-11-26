#!/usr/bin/env bash
# Null benchmark harness (docs/performance_contract.md §6).
#
# For every workload it builds:
#   * the Null native backend output  (bootstrap/program.s -> bench/build/<name>.null)
#   * the Rust/C++ baseline           (bench/c/<name>.c -> bench/build/<name>.c)
# with the baselines at -O3, runs each binary RUNS times on the same machine,
# and records wall time + peak RSS.  The reported number is the median run.
#
# Usage: bench/run_bench.sh [workload ...]
#        RUNS=7 bench/run_bench.sh sum_loop
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1
RUNS="${RUNS:-5}"
CC="${CC:-cc}"
CFLAGS="${CFLAGS:--O3 -march=native}"
STAGES_CMD="${STAGES_CMD:-env PYTHONPATH=src venv/bin/python}"
WORKLOADS=("$@")
if [ ${#WORKLOADS[@]} -eq 0 ]; then
    WORKLOADS=(sum_loop comprehension array_map)
fi

mkdir -p bench/build bench/results
RESULTS_MD="bench/results/latest.md"
RESULTS_JSON="bench/results/latest.json"

cpu_model=$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | sed 's/^ *//')
[ -z "$cpu_model" ] && cpu_model="unknown"
flags=$(grep -m1 '^flags' /proc/cpuinfo | cut -d: -f2- | tr -s ' ' '\n' | grep -E '^(avx2|avx512f|sse4_2|fma)$' | paste -sd, -)
kern=$(uname -sr)
stamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# median <file-with-numbers>
median() {
    sort -n "$1" | awk '{a[NR]=$1} END {if (NR==0) {print "nan"; exit}
        if (NR%2) print a[(NR+1)/2]; else print (a[NR/2]+a[NR/2+1])/2}'
}

# measure <binary> <out-file>: RUNS runs, writes "wall_ms rss_kb" per run.
# Delegated to bench/measure.py: the old in-shell /proc sampler slept 10 ms per
# poll, which added roughly that much to every short workload.
measure() {
    local bin="$1" out="$2"
    if ! PYTHONPATH=src python3 bench/measure.py --runs "$RUNS" "$bin" > "$out"; then
        echo "  ! measurement of $bin failed" >&2
    fi
}

printf '# Null benchmark results\n\n' > "$RESULTS_MD"
{
    printf -- '- timestamp: `%s`\n' "$stamp"
    printf -- '- machine: `%s` (%s cores, %s)\n' "$kern" "$(nproc)" "$cpu_model"
    printf -- '- cpu flags: `%s`\n' "${flags:-unknown}"
    printf -- '- runs per configuration: %s (median reported)\n' "$RUNS"
    printf -- '- baseline flags: `%s`\n\n' "$CFLAGS"
} >> "$RESULTS_MD"
{
    printf '## Median wall time (ms) and peak RSS (KiB)\n\n'
    printf '| workload | Null native | C -O3 | C/Null | Null RSS | C RSS |\n| --- | --- | --- | --- | --- | --- |\n'
} >> "$RESULTS_MD"
printf '{"timestamp":"%s","machine":"%s","cores":%s,"cpu":"%s","flags":"%s","runs":%s,"workloads":[' \
    "$stamp" "$kern" "$(nproc)" "$cpu_model" "${flags:-}" "$RUNS" > "$RESULTS_JSON"

first=1
for name in "${WORKLOADS[@]}"; do
    ir="bench/ir/$name.ir"
    csrc="bench/c/$name.c"
    printf '\n== %s ==\n' "$name"

    # --- Null: IR -> x86-64 asm -> binary -----------------------------------
    nbin="bench/build/$name.null"
    if [ -f "$ir" ]; then
        cp "$ir" bootstrap/program.ir
        rm -f bootstrap/program.s bootstrap/backend.report
        if ! $STAGES_CMD bench/stage_runner.py bootstrap/native.null > "bench/build/$name.backend.log" 2>&1; then
            printf '  ! backend stage failed, see bench/build/%s.backend.log\n' "$name"
            continue
        fi
        cp bootstrap/program.s "bench/build/$name.s"
        cp bootstrap/backend.report "bench/build/$name.report"
        if ! $CC -o "$nbin" "bench/build/$name.s"; then
            printf '  ! assembler rejected bench/build/%s.s\n' "$name"
            continue
        fi
    else
        printf '  ! missing %s (run bench/emit_workloads.sh)\n' "$ir"
        continue
    fi

    # --- C++/C baseline at -O3 ---------------------------------------------
    cbin="bench/build/$name.c-bin"
    if ! $CC $CFLAGS -o "$cbin" "$csrc"; then
        printf '  ! failed to build %s\n' "$csrc"
        continue
    fi

    measure "$nbin" "bench/build/$name.null.runs"
    measure "$cbin" "bench/build/$name.c.runs"

    awk '{print $1}' "bench/build/$name.null.runs" > "bench/build/$name.null.wall"
    awk '{print $2}' "bench/build/$name.null.runs" > "bench/build/$name.null.rss"
    awk '{print $1}' "bench/build/$name.c.runs" > "bench/build/$name.c.wall"
    awk '{print $2}' "bench/build/$name.c.runs" > "bench/build/$name.c.rss"

    null_ms=$(median "bench/build/$name.null.wall")
    c_ms=$(median "bench/build/$name.c.wall")
    null_rss=$(median "bench/build/$name.null.rss")
    c_rss=$(median "bench/build/$name.c.rss")
    ratio=$(awk -v c="$c_ms" -v n="$null_ms" 'BEGIN {if (n>0) printf "%.2f", c/n; else print "nan"}')

    printf '  null  %8s ms  %7s KiB\n' "$null_ms" "$null_rss"
    printf '  c -O3 %8s ms  %7s KiB\n' "$c_ms" "$c_rss"
    printf '  C/Null speed ratio: %sx  (10x target: %s)\n' "$ratio" \
        "$(awk -v r="$ratio" 'BEGIN {print (r+0 >= 10) ? "MET" : "not met"}')"

    printf '| `%s` | %s | %s | %sx | %s | %s |\n' "$name" "$null_ms" "$c_ms" "$ratio" \
        "$null_rss" "$c_rss" >> "$RESULTS_MD"
    [ $first -eq 1 ] || printf ',' >> "$RESULTS_JSON"; first=0
    printf '{"name":"%s","null_ms":%s,"c_ms":%s,"ratio":%s,"null_rss_kb":%s,"c_rss_kb":%s}' \
        "$name" "$null_ms" "$c_ms" "$ratio" "$null_rss" "$c_rss" >> "$RESULTS_JSON"
done
printf ']}\n' >> "$RESULTS_JSON"

 >> "$RESULTS_MD"

printf '\nWrote %s and %s\n' "$RESULTS_MD" "$RESULTS_JSON"
