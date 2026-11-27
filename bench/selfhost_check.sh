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

# --- native fixed point -----------------------------------------------------
# The checks above prove the compiler's fixed point, but both stages still run on
# the host VM. This stage compiles bootstrap/native.null itself into a real
# x86-64 binary and has that binary compile nullc.null; its IR must match the
# VM's byte for byte. This is the check that Python is out of the pipeline.
if [ "${SKIP_NATIVE:-0}" = "1" ]; then
    echo "SKIP native fixed point (SKIP_NATIVE=1)"
    exit 0
fi

NATIVE_WORK="$ROOT/bench/build/selfhost_native"
rm -rf "$NATIVE_WORK"
mkdir -p "$NATIVE_WORK/emit/bootstrap" "$NATIVE_WORK/native/bootstrap" \
         "$NATIVE_WORK/native_run/bootstrap" "$NATIVE_WORK/vm_run/bootstrap"
cp "$ROOT/bootstrap/nullc.null" "$NATIVE_WORK/emit/bootstrap/input.null"

echo "== native backend compiles nullc.null =="
( cd "$NATIVE_WORK/emit" && ${STAGES_CMD} "$RUNNER" "$ROOT/bootstrap/emitter.null" ) >"$NATIVE_WORK/emit.log" 2>&1
if [ $? -ne 0 ]; then
    echo "FAIL emitter exited $?; log: $NATIVE_WORK/emit.log"
    tail -5 "$NATIVE_WORK/emit.log"
    exit 1
fi
cp "$NATIVE_WORK/emit/bootstrap/program.ir" "$NATIVE_WORK/native/bootstrap/program.ir"
( cd "$NATIVE_WORK/native" && ${STAGES_CMD} "$RUNNER" "$ROOT/bootstrap/native.null" ) >"$NATIVE_WORK/native.log" 2>&1
if [ $? -ne 0 ]; then
    echo "FAIL backend exited $?; log: $NATIVE_WORK/native.log"
    tail -5 "$NATIVE_WORK/native.log"
    exit 1
fi
if [ "$(grep -c '^FALLBACK' "$NATIVE_WORK/native/bootstrap/backend.report" || true)" != "0" ]; then
    echo "FAIL the native backend fell back on its own source"
    grep '^FALLBACK' "$NATIVE_WORK/native/bootstrap/backend.report" | head -5
    exit 1
fi
cc -O0 -o "$NATIVE_WORK/nullc" "$NATIVE_WORK/native/bootstrap/program.s" || {
    echo "FAIL cc could not assemble the backend"; exit 1; }

echo "== that binary compiles nullc.null ==="
cp "$ROOT/bootstrap/nullc.null" "$NATIVE_WORK/native_run/bootstrap/input.null"
cp "$ROOT/bootstrap/nullc.null" "$NATIVE_WORK/vm_run/bootstrap/input.null"
touch "$NATIVE_WORK/native_run/bootstrap/compile-only.flag" \
      "$NATIVE_WORK/vm_run/bootstrap/compile-only.flag"
( cd "$NATIVE_WORK/native_run" && "$NATIVE_WORK/nullc" ) >"$NATIVE_WORK/native_run.log" 2>&1
if [ $? -ne 0 ]; then
    echo "FAIL natively built nullc exited $?; log: $NATIVE_WORK/native_run.log"
    tail -5 "$NATIVE_WORK/native_run.log"
    exit 1
fi
( cd "$NATIVE_WORK/vm_run" && ${STAGES_CMD} "$RUNNER" "$ROOT/bootstrap/nullc.null" ) >"$NATIVE_WORK/vm_run.log" 2>&1
if [ $? -ne 0 ]; then
    echo "FAIL VM nullc exited $?; log: $NATIVE_WORK/vm_run.log"
    tail -5 "$NATIVE_WORK/vm_run.log"
    exit 1
fi
if ! cmp -s "$NATIVE_WORK/native_run/bootstrap/program.ir" "$NATIVE_WORK/vm_run/bootstrap/program.ir"; then
    echo "FAIL native and VM IR differ; first divergence:"
    diff "$NATIVE_WORK/vm_run/bootstrap/program.ir" "$NATIVE_WORK/native_run/bootstrap/program.ir" | head -10
    exit 1
fi
nrows=$(wc -l <"$NATIVE_WORK/native_run/bootstrap/program.ir")
echo "PASS native fixed point: ${nrows} rows, identical to the VM, no FALLBACK"
