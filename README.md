# Null System

This repository contains a small reference implementation of the **Null System** standard library plus a minimal compiler/VM harness used in tests.

- Library primitives live under `src/null_system/lib`.
- A registry (`LibraryRegistry`) exposes those primitives to both the compiler and the VM.

See `docs/null_system_lib.md` for the list of available primitives and the command syntax used by the tiny compiler.
