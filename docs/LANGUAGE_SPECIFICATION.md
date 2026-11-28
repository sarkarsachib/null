# Null Language Specification — as implemented

This document describes the syntax that exists in the repository **today**. It is
not a design proposal. Where the implementation and the aspirational documents
(`docs/null_v2_language_spec.md`, marked "Status: Blueprint/Roadmap") disagree,
this document follows the code.

## The central problem: there is no single language

There are four front ends with four different grammars:

| # | Front end | Grammar | Reaches native backend |
| --- | --- | --- | --- |
| 1 | Bootstrap (hand-written) | `bootstrap/lexer.null` + `parser.null` + `emitter.null` | **Yes** |
| 2 | English-like | `src/null_system/lang/grammar.lark` (237 lines, 50 rules) | No |
| 3 | "Modern Rust" | `src/null_system/lang/modern/modern_rust.lark` (145 lines) | No |
| 4 | "Modern Python" | `src/null_system/lang/modern/modern_python.lark` (142 lines) | No |

Surfaces 3 and 4 are explicitly modeled on Rust and Python. That directly
contradicts the requirement that Null have its own native syntax. Phase 1 must
converge on one grammar; until then this document records all four.

---

## Surface 1 — Bootstrap (the only one that produces executables)

Keywords in `bootstrap/lexer.null`:

```
async  borrow  break  class  continue  data  else  false  fn  for  if
import in  let  match  module  move  mut  own  print  println  return
sealed trait  true  while
```

This surface is Rust-shaped: `fn`, `let`, `mut`, `match`, `->`, `//` comments,
`{ }` blocks, `;` terminators.

### Verified working

```null
// functions, typed params, recursion
fn fib(n: Num) -> Num {
    if n < 2 { return n; }
    return fib(n - 1) + fib(n - 2);
}
println(fib(15));            // 610

// let, with and without annotation
let a = 7;
let b: Num = 5;
let total = a + b;
println(total);              // 12

// while
let i = 0;
while i < 3 { println(i); i = i + 1; }

// for-in over an array
let nums = [1, 2, 3, 4];
let sum = 0;
for v in nums { sum = sum + v; }
println(sum);                // 10

// arrays
println(LEN(nums));          // 4
println(nums[1]);            // 2

// strings
let s = "hi";
println(s);                  // hi
println(s + "!");            // hi!

// if / else
if total > 3 { println("big"); } else { println("small"); }
```

Each of the above was run through `emitter.null` → `native.null` → `cc -O0` with
`FALLBACK 0` and produced the output shown.

### Verified broken

| Construct | Observed |
| --- | --- |
| `let m = { "k": 1 };` | `FALLBACK 1`; `UNSUPPORTED OP!!` |
| `own` / `borrow` / `move` / `ref` | lexed, emitted as plain store/load, never checked |
| `async` / `await` | partially emitted (`__await__`), no runtime |
| `trait` / `sealed` | lexed, no semantics |
| `data class` | tokens consumed, lowered as `INDEX`/`STORE_VAR` — not a struct |
| `?.` `?:` `!!` | emitted as `SAFE_CALL` (60), `ELVIS_CHECK` (61), `NOT_NULL_CHECK` (62); no backend lowering |
| `Type<T>` generics | lexed, no semantics |

Two constructs that were listed here as broken are fixed and covered by the
conformance corpus: `match` now lowers to one compare-and-branch per arm, and a
float literal is a single tagged constant that prints its fractional value.

### Numeric semantics

`Num` is a signed 64-bit integer. The rules both backends implement, and the
conformance suite asserts:

| Operation | Rule |
| --- | --- |
| `+ - *` | 64-bit two's-complement wraparound |
| `/` | truncates toward zero (`7 / 2 == 3`, `-9 / 4 == -2`); not float division |
| `/` by zero | native traps (SIGFPE, exit 136) — still a defect, see `IMPLEMENTATION_GAPS.md` P1-6 |
| float literals | stored and printed; float **arithmetic** is refused, not miscompiled |
| comparison | signed; results are `Bool`, printed `true`/`false` |

Float division is therefore not implemented: `3.5 / 2` is not a supported
operation in this stage, and the backend refuses rather than producing an
integer from IEEE-754 bits.

### Runtime builtins both backends implement

`LEN`, `APPEND`, `SPLIT`, `JOIN`, `SUBSTR`, `SLICE`, `CONTAINS`, `CHAR_AT`,
`ORD`, `TO_STRING`, `TO_NUMBER`, `READ_FILE`, `WRITE_FILE`, `FILE_EXISTS`,
`println`, `print`. Anything else is a compile error in the native backend
(``FALLBACK 70 unknown-call-…``) and a ``VM ERROR: unknown call …`` on the VM.

### Diagnostics

A construct the front end cannot lower produces one `IR 255 … todo` row per
site, the compiler prints `ERROR: unsupported construct: <construct>`, the VM
stops with `VM ERROR: unsupported construct …`, and the native binary refuses to
run (`UNSUPPORTED OP!!`, exit 4). Diagnostics do **not** carry a source location
yet: tokens have no line/column, so the message names the construct only. This
is the main open item of Phase 1.4.

---

## Surface 2 — English-like (`grammar.lark`)

The full rule set, 50 rules:

```
program module_header import_section import_statement module_name
annotated_statement annotation layer_annotation require_annotation
prefer_annotation identifier_list type_alias_statement data_class_statement
sealed_trait_statement let_binding_statement type_annotation generic_params
field_list field_decl variant_list variant_decl set_statement target
add_statement if_statement show_statement input_statement
write_file_statement repeat_statement define_statement return_statement
expression_statement block parameter_list comparison_op safe_call_expr
elvis_expr not_null_expr literal text_literal num_literal bool_literal
array_literal object_literal object_pair member_access function_call
argument_list legacy_null_lib_annotation comment
```

Notable properties of this grammar that the others lack:

- **Numbers include floats**: `NUMBER: /[0-9]+(\.[0-9]+)?/`.
- **Object literals are real**: `object_literal: "OBJECT" "{" … "}" | "{" … "}"`
  with `object_pair: (identifier | ESCAPED_STRING) ":" expression`.
- **Comparison operators are spelled out**: `IS GREATER THAN`,
  `IS LESS OR EQUAL TO`, `EQUALS`, `NOT EQUALS`, alongside `>`, `<`, `==`, `!=`.
- **Arithmetic is spelled out**: `PLUS`, `MINUS`, `TIMES`, `DIVIDED BY`,
  alongside `+`, `-`, `*`, `/`.
- **File I/O is in the grammar**: `SET x TO READ_FILE expr`,
  `SET x TO FILE_EXISTS expr`, `SET x TO LIST_FILES expr`,
  `WRITE_FILE expr WITH expr`.
- **Layer annotations**: `@layer(name)`, `@require(a, b)`, `@prefer(a, b)`.
- **Comments are `#`**.

Example:

```null
DEFINE add WITH a, b
    RETURN a + b
END DEFINE

SET total TO add(2, 3)
SHOW total

IF total IS GREATER THAN 3 THEN
    SHOW "big"
ELSE
    SHOW "small"
END IF

SET config TO { name: "null", version: 2 }
SHOW config.name
```

There is a recorded grammar bug in a comment at `grammar.lark:73-80`: the three
file commands once spelled the left side as a bare `identifier` while
`set_statement` used `target`, and the resulting reduce/reduce conflict made Lark
drop the `expression` branch of `set_statement`, so `SET x TO 10` did not parse.
The fix was to route every branch through `target`.

This is the only grammar that parses object literals and floats. That is a
capability the bootstrap surface does not have — and the bootstrap surface is the
one that produces executables.

---

## Surface 3 — "Modern Rust" (`modern_rust.lark`)

14 rules: `program variable_decl assignment if_statement else_clause
while_statement for_statement function_def _return_type param param_list
return_statement break_statement continue_statement print_stmt match_stmt
match_arm expression_statement argument_list literal string_literal
number_literal array_literal function_call identifier comment`.

It is a strict subset of the bootstrap surface, and it is **less capable**: it has
no object literal and no float in its `number_literal`. 8 test failures:

- `test_let_mut_statement` — `mut` is not in the grammar
- `test_for_loop_with_range` — `0..3` range syntax unsupported (`Token('DOT', '.')`)
- `test_match_with_literals`, `test_match_with_boolean_patterns` — `match` arms
- `test_compile_for_loop` — downstream of the range failure
- `test_fibonacci_program`, `test_counter_loop_program` — same causes
- `test_function_equivalence` — English/modern round-trip mismatch

The failure signature is consistent: `Previous tokens: [Token('DOT', '.')]` (8
occurrences across the suite) and `Unexpected token Token('RBRACE', '}')`.

---

## Surface 4 — "Modern Python" (`modern_python.lark`)

17 rules, adding `class_def`, `try_statement`, `dict_literal`, `dict_pair` over
surface 3. This is the only grammar with a dict literal, but it is not wired to a
backend that can execute one.

---

## Type system

What is parsed (`grammar.lark`):

```
type_annotation: identifier generic_params? ("?")?     -- T, T<A,B>, T?
type_alias_statement: "type" identifier "=" type_annotation
data_class_statement: "class" "data" identifier "{" field_list "}"
sealed_trait_statement: "sealed" "trait" identifier generic_params? "{" variant_list "}"
field_decl: identifier ":" type_annotation
variant_decl: identifier ("(" type_annotation ")")?
```

What is enforced: `src/null_system/analysis/type_inference.py` (387 lines)
performs inference over the AST, and `src/null_system/ast/validator.py` validates
nodes. `docs/type_system_phase3-4.md` documents this.

What is **not** enforced: the native backend is dynamically typed. A typed
`let a: Num = 4` works, but the annotation is not checked against the value at
runtime or compile time in the native path. `docs/bootstrap_phase2_runtime_status.md`
records that GC and `@extern` were never finished.

The four primitive types the native runtime actually distinguishes are recorded
in [`NATIVE_RUNTIME.md`](NATIVE_RUNTIME.md): numbers (signed 64-bit), strings
(tagged pointer, bit 62), arrays (tagged pointer, bit 63), and booleans.

---

## IR — the real interchange format

Whatever the surface, all front ends target the same super-bit IR. 53 opcodes,
documented in `bootstrap/ir.null` and mirrored in
`src/null_system/superbit/ir.py`. See
[`COMPILER_PIPELINE.md`](COMPILER_PIPELINE.md) for the encoding.

Text form is TSV:

```
IR	<opcode>	<operand>	<layer>[	<meta>]
LABEL	<name>
```

Layers: `scalar`, `simd`, `lang`, `control`, `match`.

---

## What a real specification must decide

Phase 1 cannot be completed by writing this document; it requires decisions:

1. **Which surface is Null?** The bootstrap surface is the only one that produces
   executables, but it is Rust-shaped. Keeping it means Null's syntax is Rust's.
2. **Keyword set.** The current bootstrap keywords (`fn`, `let`, `mut`, `match`,
   `own`, `borrow`) are Rust's. A native syntax needs its own vocabulary, or the
   requirement is unmet by definition.
3. **Object literals and floats.** Only surface 2 has them; only surface 1
   executes. One of the two must gain the other's capability.
4. **Statement termination.** Surface 1 requires `;`, surface 2 does not.
5. **Comments.** `//` (surface 1) vs `#` (surface 2).
6. **Ownership.** If `own`/`borrow` stay, they need semantics (see
   [`IMPLEMENTATION_GAPS.md`](IMPLEMENTATION_GAPS.md) P1-4). If they go, memory
   reclamation needs another strategy.

Until those are decided, this document is a description, not a specification.
