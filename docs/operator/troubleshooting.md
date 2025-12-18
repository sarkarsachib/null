# Troubleshooting Guide

This guide helps operators diagnose and resolve issues with the Null-Lang Compiler, VM, and Runtime.

## Compiler Issues

### Symptom: `SyntaxError: Unexpected token` during build

**Diagnosis**: The source code uses syntax not supported by the current parser version or layer configuration.
**Remediation**:
1. Check `@layer` annotations. Ensure the file imports necessary layers.
2. Verify syntax version compatibility.
3. Run with verbose parser logging: `NULL_LOG_LEVEL=DEBUG nullc compile main.null`

### Symptom: Compilation hangs indefinitely

**Diagnosis**: Circular dependency in imports or infinite recursion in macro expansion.
**Remediation**:
1. Inspect import graph.
2. Check for recursive macros.
3. Use `nullc --timeout 60s` to enforce build timeouts.

## VM / Runtime Issues

### Symptom: VM Crash with `Segmentation Fault`

**Diagnosis**: Memory corruption in native extensions or stack overflow in deep recursion.
**Remediation**:
1. Check if the code uses unsafe native bindings.
2. Increase stack size if using deep recursion: `NULL_VM_STACK_SIZE=8M`.
3. Capture core dump and analyze with gdb.

### Symptom: High Latency / Slow Execution

**Diagnosis**: Code is running in interpreted mode instead of JIT-compiled SuperBit.
**Remediation**:
1. Ensure JIT is enabled (default in production).
2. Check logs for "JIT Compilation Failed" warnings.
3. Profile the application using the observability stack.

### Symptom: `SuperBitDecodeError`

**Diagnosis**: Version mismatch between Compiler and VM.
**Remediation**:
1. Ensure `nullc` and `null-vm` versions match.
2. Recompile the application with the target VM version.

## ML / Native Module Issues

### Symptom: "Module not found: torch"

**Diagnosis**: Using standard runtime image for ML workload.
**Remediation**:
1. Switch to `null-lang/ml` base image.
2. Verify `requirements.txt` includes necessary packages.

## General Debugging

- **Logs**: extensive logging is available. Set `NULL_LOG_LEVEL=DEBUG` or `TRACE` for detailed output.
- **Observability**: Refer to `docs/observability/` for integrating with Prometheus/Grafana.
