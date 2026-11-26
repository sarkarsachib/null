# Bootstrap Phase 2 — VM/Runtime Essentials: status

Phase 2 of the bootstrap plan is *not* complete. This document records what
exists, what was added in this session, and what is still missing, so the
completion claim in `bootstrap_phase1_completion.md` is not read as covering it.

## 2c. Error handling — **shipped**

Runtime errors now carry a Null-level stack trace with source lines.

```
Invalid index 9: list index out of range
stack trace (innermost first):
  in inner at line 3
  in outer at line 7
  in main at line 11
```

What made that possible, and is worth knowing before touching the front end:

- **The parser used to throw away positions.** `ModernRustParser` parses with
  `propagate_positions=True`, but every rule method builds its AST node by hand,
  so the spans Lark computed were dropped. `ModernRustTransformer._call_userfunc`
  now stamps `node.span` from `tree.meta` for any `ASTNode` that does not set
  one, which gives every statement and expression a `SourceSpan` without
  touching the forty rule methods.
- **The compiler used to emit no lines.** `NullLangCompiler._visit` records
  `node.span.start_line` and `_emit` writes it to `SuperBitIRToken.source_line`,
  so `LOAD_VAR`/`STORE_VAR`/`CALL`/… all know where they came from. The VM's
  `debugger_session` reads the same field, so single-step debugging and traces
  now agree.
- **The VM kept no call frames for reporting.** `self.frames` existed only to
  swap local scopes. A parallel `self.call_sites` records the entered function
  and the call line, `self.current_function` tracks the innermost one, and
  `_format_trace(fault_line)` renders innermost-first. The implicit entry call to
  `main` is marked `entry` in its metadata and is not reported as a frame, so
  `main` appears once.
- `ExecutionResult.trace` holds the same lines as a list (empty on success), and
  the formatted block is appended to `ExecutionResult.error` so existing callers
  that only print `error` show the trace too.

Tests: `tests/test_stack_traces.py` (nested frames and lines; no trace on
success).

Not done in 2c: there is no `try`/`catch` in the grammar and no error values
beyond the VM's `RuntimeError` path, so "stack traces" here means *reporting* a
runtime error, not recovering from one.

## 2a. Memory management — **not done**

- Host VM: values are Python objects, so collection is Python's.
- Native backend: `null_array_new`/`null_array_zero` `malloc`/`calloc` array
  headers and nothing ever frees them. Programs are short-lived batch processes,
  so nothing leaks across a process boundary, but a server-shaped program would.
- What a real implementation needs, in order: a header word that can mark an
  allocation (the layout currently starts with the length), roots from frame
  slots, registers and the operand stack, and a policy. Reference counting fits
  the current codegen better than tracing — every array value lives in one frame
  slot or register, so increments and decrements are insertable at `STORE_VAR`
  and `CALL` without a stack map — but it needs cycle handling for closures,
  which do not exist in the IR yet.

## 2b. FFI / `@extern` — **not done**

The pieces that exist: the backend emits real `call <label>` sequences with a
System V frame (`rbp` frame, `r12`-`r15` saved), and `CALL` of an unknown name
is the builtin path. What is missing is a way to *declare* an external symbol:
the modern grammar has no `extern` form, the IR has no declaration row, and the
link step (`cc -o <bin> program.s`) would need extra objects through
`bench/run_bench.sh`.

Minimum viable shape, so nobody re-derives it: an `extern fn f(a: Num) -> Num`
declaration that emits a `FUNCTION` row with `metadata["extern"]="f"`; the
backend then skips the body and lowers `CALL f` to `mov rdi/rsi/rdx/rcx/r8/r9`
from the argument slots, `xor eax, eax`, `call f@PLT`. Only integer and pointer
arguments fit that mapping without a type-mapping table, so a first cut is
`Num`-only and the contract's "nothing silently degrades" rule applies to
everything else.

## Phase 4 (self-compilation) — **fixed point reached, native binary pending**

`bootstrap/nullc.null` is a compiler now: `bootstrap/link.null` links the front
end from `emitter.null` with the interpreter from `vm.null` plus a driver, and
the result compiles its own source. `bench/selfhost_check.sh` checks that the IR
from `nullc.null` and from `emitter.null` is byte-identical (12,854 rows,
260,961 bytes). The stage-1 lexer moved to `bootstrap/lexer.null`.

What is still missing for "zero Python in the pipeline" is a native `nullc`
binary. `native.null` now has string literals, `LEN`, `+`, `==`/`!=`, `CHAR_AT`,
`ORD` and `READ_FILE`, but no aggregate typing (an index load and a call result
are still `int`), so stage 1's `[text, pos]` returns cannot be compiled yet; see
`bootstrap_stage5_native_backend.md`. Until that lands the fixed point is real,
but both compilers execute on the host VM.
