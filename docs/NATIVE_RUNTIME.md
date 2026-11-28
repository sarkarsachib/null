# Native Runtime

`bootstrap/native.null` is 4,363 lines of Null that lowers super-bit IR to
x86-64 assembly. It is the only stage in the repository that produces a real
executable, and it is itself written in Null and compiled by the pipeline it
implements.

## Design, in the backend's own words

From the file header:

```
* no dispatch loop - every IR token becomes a fixed instruction sequence,
  so there is no per-instruction opcode fetch/decode/switch;
* values live in frame slots addressed at compile time; there is no runtime
  name lookup, no map, no boxing;
* variables get fixed frame offsets in a pre-pass (load/store are a single
  mov), and functions are real `call`/`ret` with the SysV register ABI;
* specialised opcodes lower to their typed form: FAST_INDEX drops the
  bounds check, FAST_LEN reads the array header, SIMD_ADD/SIMD_MUL run an
  AVX2 loop with a scalar tail, FUSED_COMPREHEND becomes one fused loop
  with a single output allocation;
* anything this stage cannot honour is reported as FALLBACK and lowered to
  a trapping stub rather than silently miscompiled.
```

## Output contract

| Artifact | Content |
| --- | --- |
| `bootstrap/program.s` | GNU `as`, Intel syntax, System V AMD64, `main` entry at line 2952 |
| `bootstrap/backend.report` | one `LOWERED` / `FALLBACK` / `STAT` line per decision |

The report is the audit trail and the reason this backend can be trusted: it
never claims to have lowered something it stubbed out.

## Value representation

Values are 64-bit words. Pointer-typed values carry a tag in the top bits:

| Kind | Tag | Encoding |
| --- | --- | --- |
| Number | none | signed 64-bit integer in the word |
| String | bit 62 (`bts rax, 62`) | tagged pointer to NUL-terminated bytes |
| Array | bit 63 | tagged pointer to the array header |
| Boolean | none | `0` / `1` |

The mask is emitted once:

```
.Lmask: .quad 0x3fffffffffffffff
```

Masking recovers a real pointer: `and rdi, qword ptr [rip + .Lmask]`. There are
46 `and …, .Lmask` sites, 9 `bts …, 62` (string tag) and 10 `bts …, 63`
(array tag).

Runtime type dispatch is done by shifting the tag down:

```
"null_dyn_eq:"
  mov r8, rbx
  shr r8, 62          # tag of left
  mov r9, r12
  shr r9, 62          # tag of right
  cmp r8, r9
  jne .Lde_no         # different tags -> not equal
  cmp r8, 1
  je  .Lde_str        # string -> byte compare
  cmp r8, 2
  je  .Lde_ptr        # array -> pointer compare
  ...                 # tag 0 -> integer compare
```

`null_dyn_len` and `null_dyn_index` use the same shape, so one IR opcode serves
all three value kinds.

## Array layout

```
offset -8   capacity
offset  0   length          <-- tagged pointer points here
offset +8   element 0
offset +16  element 1
...
```

Evidence, from `null_array_new`:

```
lea rdi, [rdi * 8 + 16]     # cap*8 + 16 bytes
call malloc@PLT
mov qword ptr [rax], rbx    # [0]  = cap
mov qword ptr [rax + 8], rbx # [8] = len
add rax, 8                  # returned pointer -> the len word
```

`FAST_LEN` reads `[ptr]`; `FAST_INDEX_STORE` writes `[ptr + idx*8 + 8]`;
`null_array_grow` reads capacity at `[ptr - 8]`, doubles it (floor 4), and
`realloc`s.

A string is a bare NUL-terminated byte buffer; `null_str_len` walks it byte by
byte (`cmp byte ptr [rdi + rax], 0`). There is no cached length, so every
`LEN(s)` on a string is O(n).

## Runtime entry points

34 `null_*` labels. Grouped:

**Dynamic dispatch (type-generic IR opcodes)**

`null_dyn_add`, `null_dyn_eq`, `null_dyn_index`, `null_dyn_len`,
`null_dyn_print`, `null_dyn_to_string`, `null_truthy`

**Strings (12)**

`null_str_len`, `null_str_eq`, `null_str_concat`, `null_str_dup`,
`null_str_find`, `null_str_substr`, `null_str_split`, `null_str_join`,
`null_str_char_at`, `null_str_ord`, `null_str_to_number`

**Arrays (4)**

`null_array_new`, `null_array_zero`, `null_array_grow`, `null_array_slice`

**Printing**

`null_print_str`, `null_print_bool`, `null_int_to_str`, `null_contains`

**File I/O (3)**

`null_read_file`, `null_write_file`, `null_file_exists`

Opcode 35 `LIST_FILES` is defined in `bootstrap/ir.null` but has **no** runtime
entry point, so directory listing is not implemented.

**SIMD (3)**

`null_simd_add`, `null_simd_mul`, `null_simd_sum`

**Failure paths (3)**

`null_panic_oob`, `null_unsupported`, `null_panic_divzero`

Note there is **no** `null_str_compare`, no map/hash function, no float
arithmetic, and no allocation-free path.

## Failure behavior

| Condition | Behavior | Exit code |
| --- | --- | --- |
| Index out of bounds | writes `OOB PANIC!!!` to stderr, `exit_group(3)` | 3 |
| Unlowered opcode reached | writes `UNSUPPORTED OP!!` to stderr, `exit_group(4)` | 4 |
| Integer division by zero | writes `DIVISION BY ZERO!!!` to stderr, `exit_group(5)` | 5 |

All three handled paths use `syscall` directly (`rax=1` write, `rax=60` exit), so
panics do not depend on libc stdio. Every integer `idiv` is preceded by a
divisor test (`bootstrap/native.null`), so a zero divisor can no longer reach
the instruction and trap as SIGFPE.

## Memory model

| Call | Sites |
| --- | --- |
| `malloc@PLT` | 8 |
| `calloc@PLT` | 1 |
| `realloc@PLT` | 2 |
| **total allocation sites** | **11** |
| `free@PLT` | **0** |
| `mmap` | **0** |

**Nothing is ever freed.** There is no garbage collector, no arena, no
reference counting, and no ownership enforcement — even though `own`, `borrow`,
`borrow_mut`, `move` and `ref` are in the lexer's keyword table and the emitter
accepts them.

Consequences, measured:

- Every string concatenation allocates (`null_str_concat` → `malloc`).
- Every array append beyond capacity `realloc`s, and the old block's contents are
  copied but the array never shrinks.
- `array_map` in `bench/results/latest.md` shows 127,532 KiB peak RSS against
  2,184 KiB for `sum_loop`. That ratio is the leak, not the algorithm.
- A long-running program will exhaust memory. There is no test that runs long
  enough to expose it.

This is the single largest gap between the backend's design and a usable
language. It is Phase 3, and it interacts with the ownership keywords: if
`own`/`borrow` are to stay in the syntax, ownership-based reclamation is the
strategy the language has already promised.

## Specialised opcodes

| Opcode | Lowering | Report line |
| --- | --- | --- |
| 100 `FAST_ADD_INT` | unchecked integer add | `LOWERED 100` |
| 102 `FAST_LT_INT` | unchecked integer compare | `LOWERED 102` |
| 103 `FAST_INDEX` | load with no bounds check | `LOWERED 103 fast-index-unchecked` |
| 104 `FAST_LEN` | read `[ptr]` directly | `LOWERED 104 fast-len-header` |
| 105 `FAST_INDEX_STORE` | store, no bounds check | `LOWERED 105` |
| 107 `FAST_ARRAY_ZERO` | `calloc` a zeroed array | `LOWERED 107` |
| 120 `SIMD_ADD` | AVX2 loop + scalar tail | `LOWERED 120` |
| 121 `SIMD_MUL` | AVX2 loop + scalar tail | `LOWERED 121` |
| 122 `SIMD_SUM` | AVX2 horizontal sum + tail | `LOWERED 122` |

`FAST_INDEX` and `FAST_INDEX_STORE` deliberately drop the bounds check. That is
sound only if the optimizer proved the index in range. The optimizer is the
component with the broken token API
([`IMPLEMENTATION_GAPS.md`](IMPLEMENTATION_GAPS.md) P0-4), so nothing currently
proves it — the safety of these two opcodes is asserted, not established.

## Fallback set

Nine `FALLBACK` sites. These are honest but they mean the advertised surface is
wider than the implementation:

| Opcode | Reason | Line |
| --- | --- | --- |
| 70 | `concat-string-runtime-not-in-this-stage` | 3730 |
| 70 | `range-object-not-in-this-stage` | 3735 |
| 70 | `filter-lambda-capture-not-in-this-stage` | 3740 |
| 70 | `map-lambda-capture-not-in-this-stage` | 3745 |
| 70 | `unknown-call-<name>` | 3751 |
| 101 | `fast-add-float-float64-not-in-this-stage` | 3965 |
| 110 | `fused-map-needs-captured-lambda` | 4054 |
| 111 | `fused-filter-needs-captured-lambda` | 4058 |
| 112 | `fused-reduce-needs-captured-lambda` | 4062 |

Note the tension: `null_str_concat` exists and works (verified with
`println(s + "!")` → `hi!`), yet opcode 70 with a `concat` operand still reports
`concat-string-runtime-not-in-this-stage`. The concat path is reached through a
different lowering than the fallback site, so the fallback reason string is stale
and misleading. It should be re-verified rather than trusted.

## What is verified working

Each of these was compiled through `emitter.null` → `native.null` → `cc -O0` with
`FALLBACK 0` and produced the stated output:

| Program | Output |
| --- | --- |
| `a=7; b=5; total=a+b; println(total); println("hi")` | `12`, `hi` |
| user `fn add(a, b)` | correct |
| `while` loop | correct |
| `let nums=[1,2,3]; LEN(nums); nums[1]` | `3`, `2` |
| string concat, string index | correct |
| `if`/`else` | correct |
| `for v in nums` summing | `10` |
| `fib(15)` | `610` |
| `let a: Num = 4` | correct |

The strongest evidence is the native fixed point: the backend lowers its own
4,363-line source with zero `FALLBACK` rows, and the resulting binary reproduces
the Python VM's IR byte for byte (13,665 rows). See [`BOOTSTRAP.md`](BOOTSTRAP.md).

## What is verified broken

| Construct | Observed |
| --- | --- |
| `let x = 3.5;` | `FALLBACK 70 unknown-call-get_member`, prints `UNSUPPORTED OP!!`, exit 4 |
| `match n { 1=>… 2=>… }` | prints only the first arm; no branch emitted |
| `let m = { "k": 1 };` | `FALLBACK 1`, prints `UNSUPPORTED OP!!` |
| `x / 0` | `DIVISION BY ZERO!!!`, exit 5 |
| `own` / `borrow` / `move` | no enforcement |
| `?.` `?:` `!!` | opcodes 60/61/62 emitted, no lowering |
| `data class` | lowered as `INDEX`/`STORE_VAR`, not a struct |
| `async` / `await` | `__await__` emitted, no runtime |

## Requirements to run the backend

- A POSIX system with `cc` (assembler + linker) and an x86-64 CPU.
- `AVX2` for the SIMD opcodes. Note `bench/results/latest.md` records
  `avx512f` as available, but `commit c2f4c33` says the backend deliberately
  keeps `SIMD_MUL` inside AVX2 rather than AVX512DQ — so AVX2 is the requirement,
  not AVX-512.
- Linux syscall ABI for the panic and print paths (`syscall`, `rax=1`/`60`).
  This is not portable to macOS, whose syscall convention differs.

See [`PLATFORM_SUPPORT.md`](PLATFORM_SUPPORT.md).
