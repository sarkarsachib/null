#!/usr/bin/env bash
# Source -> super-bit IR for the benchmark workloads (docs/performance_contract.md §6.1).
#
# The front end is the self-hosted stage-3 emitter, bootstrap/emitter.null: it
# tokenises, parses and lowers Null source to the IR row format that
# bootstrap/native.null consumes. The Python host VM only runs that Null program,
# it does not contribute any compiler logic of its own.
#
#   bench/workloads/<name>.null  --bootstrap/emitter.null-->  bench/ir/<name>.ir
#
# A workload whose source carries the marker `hand-authored-ir` is skipped: those
# need an IR construct the source cannot express yet (today: growable arrays for
# array_map), so their bench/ir file is maintained by hand and says so.
#
# Usage: bench/emit_workloads.sh [workload ...]
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1
ROOT=$(pwd)
# The stages run from a scratch directory, so the interpreter and import path
# have to be absolute (an override is used verbatim).
STAGES_CMD="${STAGES_CMD:-env PYTHONPATH=$ROOT/src $ROOT/venv/bin/python}"
EMITTER="$ROOT/bootstrap/emitter.null"
OUT_DIR="$ROOT/bench/ir"
WORK_DIR="$ROOT/bench/build/emit"

mkdir -p "$OUT_DIR" "$WORK_DIR"

names=("$@")
if [ ${#names[@]} -eq 0 ]; then
    names=()
    for src in bench/workloads/*.null; do
        names+=("$(basename "$src" .null)")
    done
fi

status=0
for name in "${names[@]}"; do
    src="bench/workloads/$name.null"
    if [ ! -f "$src" ]; then
        printf '  ! missing %s\n' "$src"
        status=1
        continue
    fi
    if grep -q 'hand-authored-ir' "$src"; then
        printf '  %-14s hand-authored IR, source skipped\n' "$name"
        continue
    fi

    work="$WORK_DIR/$name"
    rm -rf "$work"
    mkdir -p "$work/bootstrap"
    cp "$src" "$work/bootstrap/input.null"

    if ! ( cd "$work" && $STAGES_CMD "$ROOT/bench/stage_runner.py" "$EMITTER" ) \
            > "$work/emitter.log" 2>&1; then
        printf '  ! %s: emitter stage failed, see %s\n' "$name" "${work#$ROOT/}"
        status=1
        continue
    fi
    if ! grep -q 'success=True' "$work/emitter.log"; then
        printf '  ! %s: emitter reported an error, see %s\n' "$name" "${work#$ROOT/}"
        status=1
        continue
    fi
    if grep -q 'unsupported:\|@todo' "$work/emitter.log"; then
        printf '  ! %s: source uses a construct the emitter cannot lower yet\n' "$name"
        status=1
        continue
    fi

    cp "$work/bootstrap/program.ir" "$OUT_DIR/$name.ir"
    rows=$(grep -c '' "$OUT_DIR/$name.ir")
    printf '  %-14s %s rows -> bench/ir/%s.ir\n' "$name" "$rows" "$name"
done

exit $status
