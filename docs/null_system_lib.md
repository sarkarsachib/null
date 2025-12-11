# Null System Library Primitives

The Null System standard library is provided as modular packages under `src/null_system/lib` and is exposed via a shared registry.

## Referencing library functions from programs

The tiny reference compiler included in this repo supports referencing library functions with:

```
DEFINE <name> USE LIB <lib>.<FUNCTION>
```

Example:

```
DEFINE add USE LIB math.ADD
```

Once defined, call it with:

```
CALL <name> <arg_count>
```

Direct calls (without `DEFINE`) are also supported:

```
LIBCALL <lib>.<FUNCTION> <arg_count>
```

Some library features are higher-order; `PUSH_REF <name>` pushes a reference to a previously defined lib function onto the stack (used by `array.MAP`).

## Available libraries and primitives

### `math.*` (`math_ops`)

- `math.ADD(a, b) -> number`
- `math.SUB(a, b) -> number`
- `math.MUL(a, b) -> number`
- `math.DIV(a, b) -> number` (typed error on division by zero)

### `text.*` (`text_ops`)

- `text.CONCAT(a, b) -> string`
- `text.SUBSTR(text, start, length) -> string`

`start` and `length` are numbers, interpreted as integers.

### `array.*` (`array_ops`)

- `array.PUSH(array, value) -> array` (mutates the array)
- `array.POP(array) -> value` (mutates the array; typed error on empty)
- `array.MAP(array, fn_ref, bound_arg) -> array`

`fn_ref` must be a reference to a **binary** library function (typically created via `PUSH_REF`).
`bound_arg` is provided as the second argument when calling the function for each element. For example, to multiply every element by `2`:

```
DEFINE mul USE LIB math.MUL
PUSH [1,2,3]
PUSH_REF mul
PUSH 2
LIBCALL array.MAP 3
SHOW
HALT
```

### `object.*` (`object_ops`)

- `object.READ(obj, key) -> value` (`null` if missing)
- `object.WRITE(obj, key, value) -> value` (mutates the object)

### `io.*` (`io_ops`)

- `io.SHOW(value) -> null` (writes a display string to the VM output)
- `io.READ() -> string` (reads a single line from the VM input)

## Errors

Unknown libraries/functions, type mismatches, arity mismatches, and runtime faults (e.g. division by zero) raise typed `NullError` subclasses.

Errors carry a `code` and `details` for programmatic handling.
