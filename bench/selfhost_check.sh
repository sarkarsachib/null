#!/usr/bin/env bash
# Phase 4 bootstrap check: the linked compiler compiles itself.
#
#   linked: bootstrap/nullc.null compiles its own 3,300-line source, compile-only
#   staged: bootstrap/emitter.null compiles the same source
#
# The two IR texts must be byte-identical. Both stages run on the host VM, which
# only executes the Null programs; this proves the compiler's fixed point, not
# that Python is gone from the pipeline (that is the native-backend goal).
#
# Usage: bench/selfhost_check.sh
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1
ROOT=$(pwd)
STAGES_CMD="${STAGES_CMD:-env PYTHONPATH=$ROOT/src $ROOT/venv/bin/python}"
RUNNER="$ROOT/bench/stage_runner.py"
WORK="$ROOT/bench/build/selfhost"

rm -rf "$WORK"
mkdir -p "$WORK/linked/bootstrap" "$WORK/staged/bootstrap"
cp "$ROOT/bootstrap/nullc.null" "$WORK/linked/bootstrap/input.null"
cp "$ROOT/bootstrap/nullc.null" "$WORK/staged/bootstrap/input.null"
touch "$WORK/linked/bootstrap/compile-only.flag"

echo "== nullc.null compiles nullc.null =="
start=$(date +%s%N)
( cd "$WORK/linked" && ${STAGES_CMD} "$RUNNER" "$ROOT/bootstrap/nullc.null" ) >"$WORK/linked.log" 2>&1
status=$?
linked_ms=$(( ($(date +%s%N) - start) / 1000000 ))
if [ $status -ne 0 ]; then
    echo "FAIL linked compiler exited $status; log: $WORK/linked.log"
    tail -5 "$WORK/linked.log"
    exit 1
fi

echo "== emitter.null compiles nullc.null =="
start=$(date +%s%N)
( cd "$WORK/staged" && ${STAGES_CMD} "$RUNNER" "$ROOT/bootstrap/emitter.null" ) >"$WORK/staged.log" 2>&1
status=$?
staged_ms=$(( ($(date +%s%N) - start) / 1000000 ))
if [ $status -ne 0 ]; then
    echo "FAIL emitter stage exited $status; log: $WORK/staged.log"
    tail -5 "$WORK/staged.log"
    exit 1
fi

linked_ir="$WORK/linked/bootstrap/program.ir"
staged_ir="$WORK/staged/bootstrap/program.ir"
if ! cmp -s "$linked_ir" "$staged_ir"; then
    echo "FAIL IR differs; first divergence:"
    diff "$staged_ir" "$linked_ir" | head -10
    exit 1
fi

# Identical is not enough: the emitter must not have bailed on a statement.
# (Match the marker rows, not the emitter's own "unsupported:" string literal.)
markers=$(grep -cE "unsupported:.*lang.*todo" "$linked_ir" || true)
if [ "$markers" -ne 0 ]; then
    echo "FAIL $markers unsupported rows in the compiler's own IR; first few:"
    grep -nE "unsupported:.*lang.*todo" "$linked_ir" | head -5
    exit 1
fi

rows=$(wc -l <"$linked_ir")
bytes=$(wc -c <"$linked_ir")
echo "PASS identical IR: ${rows} rows, ${bytes} bytes, no unsupported rows"
echo "     nullc ${linked_ms} ms, emitter ${staged_ms} ms (host VM, this machine)"
