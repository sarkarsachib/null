# Platform Support

What Null runs on today, what it requires, and what it does not support. Every
claim here is derived from the emitted assembly and the build scripts, not from
intent.

## The only working target

| Property | Value | Evidence |
| --- | --- | --- |
| Architecture | x86-64 | `bootstrap/native.null` emits x86-64 only |
| Assembler syntax | GNU `as`, Intel | `native.null` header |
| ABI | System V AMD64 | `native.null` header; `rdi`/`rsi` argument registers |
| Entry point | `main` | `native.null:2952` |
| Linker | `cc` | `bench/selfhost_check.sh` |
| Kernel interface | Linux syscalls | `syscall` with `rax=1` (write), `rax=60` (exit) |
| Required CPU features | AVX2 | SIMD opcodes; `commit c2f4c33` keeps `SIMD_MUL` in AVX2 rather than AVX512DQ |
| Compiler flags used in CI | `cc -O0` | `bench/selfhost_check.sh` |

## Portability problems in the current backend

These are not hypothetical; they are visible in the emitted code.

### 1. Raw Linux syscalls in the runtime

Panic and print paths bypass libc entirely:

```
"null_panic_oob:"
  lea rsi, [rip + .Loob]
  mov rdx, 12
  mov rax, 1        # SYS_write
  mov rdi, 2        # fd 2
  syscall
  mov rax, 60       # SYS_exit_group
  mov rdi, 3
  syscall
```

`rax=1` / `rax=60` with this argument order is the Linux syscall ABI. macOS uses
`rax=0x2000004` / `0x2000001`; Windows has no `syscall` interface at all. So the
panic path, the unsupported path, and every `println` are Linux-only. Porting to
macOS means routing these through libc (`write`, `exit`) instead.

### 2. `malloc`/`realloc` through the PLT

Allocation uses `malloc@PLT`, `calloc@PLT`, `realloc@PLT` — 11 sites, zero
`free@PLT`. That part is portable to any libc, which is the one portability
decision the backend got right.

### 3. GNU `as` Intel syntax

The emitted text uses `qword ptr [rip + …]`, `.quad`, and `bts`. That is GNU
assembler Intel syntax. It will assemble with `as` on Linux/ELF. Apple's `as` and
MSVC's `ml64` accept different dialects, so the output is not portable as text.

### 4. No object-file format abstraction

The backend writes assembly, not an object file. The target object format is
whatever `cc` produces for the host — ELF on Linux. There is no COFF/Mach-O path.

## What is not supported at all

| Target | Status |
| --- | --- |
| ARM64 / AArch64 | No backend. Would be a second instruction selector. |
| RISC-V | No backend. |
| WebAssembly | No backend. |
| Windows | Not supported — no syscall ABI match, no COFF. |
| macOS | Not supported — no syscall ABI match, no Mach-O. |
| 32-bit x86 | Not supported. |
| Big-endian | Not supported; array layout and tagging assume little-endian. |
| GPU | `GPU_KERNEL` (130) is declared in the IR and has no lowering. |
| Distributed | `DIST_SEND` (140) / `DIST_RECV` (141) declared, no lowering. |

The IR reserves opcodes for GPU and distributed execution, and
`src/null_system/vm/distributed/distributed_executor.ts` exists (3 of the 97
TypeScript errors are there). None of it executes.

## Runtime library availability

Because the backend calls `malloc`/`calloc`/`realloc`, a Null program requires a C
runtime to be linked. It is not freestanding: there is no `_start`, no
syscall-only allocation, and no way to build a static binary without libc. `cc`
supplies `crt0` and the dynamic loader.

That is worth stating explicitly because "self-contained language" is a project
goal: the *compiler* is self-hosted, but its *output* depends on libc for
allocation.

## Development platform

| Requirement | Version | Notes |
| --- | --- | --- |
| Python | 3.11+ (`requires-python = ">=3.11"`) | needed by `bench/stage_runner.py`, all tests, the CLI |
| `lark` / `lark-parser` | `>=0.12.0` | the Python front ends; not needed by the bootstrap chain |
| `cc` | any GCC/Clang | assembles the backend output |
| Node | 24 (measured `v24.22.1`) | TypeScript VM and its tests; **the TS tree does not compile** |
| `npm` | 11 (measured `11.19.1`) | |
| OS | Linux, x86-64 | see above |

`venv/` is present in the repository (3,676 tracked files) but is not a
requirement — it is committed state, not a specification. See
[`DEPENDENCY_AUDIT.md`](DEPENDENCY_AUDIT.md) § Repository hygiene defects.

## The test matrix as it actually runs

```
$ PYTHONPATH=src ./venv/bin/python -m pytest tests -q -p no:randomly \
    --ignore=tests/test_null_system_lib.py --ignore=tests/test_subsystems.py
= 57 failed, 959 passed, 1 skipped, 20 warnings, 11 errors in 191.54s =
```

- One platform: Linux x86-64.
- One Python: 3.12 in `venv/`.
- Two test modules excluded because they import modules that do not exist
  (`null_system.ai.core`) or a compiler API that no longer matches.
- The TypeScript tests are not part of this run and cannot be, because
  `npx tsc --noEmit` reports 97 errors.

## Phase 9 exit criteria

1. State the supported matrix. Today the honest statement is:
   **Linux x86-64 with AVX2, GCC or Clang, and a C runtime.**
2. Either add a second target or state explicitly that one target is the
   deliverable. A "self-contained language" with one target is a defensible
   product; an unspecified number of targets is not.
3. If macOS support is wanted, replace the raw syscalls with libc calls. That is
   the smallest change that unlocks a second OS, and it is confined to the print
   and panic paths.
4. Publish the CPU feature requirement. A program using `SIMD_MUL` will fault on a
   CPU without AVX2, and nothing in the emitted code checks for it.
