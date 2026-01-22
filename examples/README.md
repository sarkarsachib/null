# Null-Lang Calculator Suite Demo

This directory contains a suite of demo programs showcasing the features of Null-Lang, including its English-like syntax, advanced type system, null-safety operators, and module system.

## Demo Programs

### 1. [Basic Arithmetic](basic_arithmetic.null)
Demonstrates core English syntax, function definitions, and basic operations.
- **Key Features**: `DEFINE`, `WITH`, `SHOW`, `SET`, `ADD` (implicitly via `+`), `RETURN`.

### 2. [Type Inference](type_inference.null)
Showcases the powerful type inference engine that automatically determines types for variables.
- **Key Features**: Literal inference (number, string, boolean, array).

### 3. [Null-Safety](null_safety.null)
Highlights the modern null-safety operators that prevent null pointer exceptions.
- **Key Features**: Safe Call (`?.`), Elvis Operator (`?:`).

### 4. [Control Flow](control_flow.null)
Demonstrates loops and conditional statements.
- **Key Features**: `REPEAT`, `IF/THEN/ELSE`.

### 5. [Modules Demo](modules_demo.null)
Shows how Null-Lang handles code organization through modules and imports.
- **Key Features**: `module`, `import`.

### 6. [Function Composition](function_composition.null)
Demonstrates defining and composing multiple functions.
- **Key Features**: Function calls and value transformations.

## Feature Matrix

| Feature | `basic_arithmetic.null` | `type_inference.null` | `null_safety.null` | `control_flow.null` | `modules_demo.null` | `function_composition.null` |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| English Syntax | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Type Inference | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Null-Safety | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Modules | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Functions | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Loops | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |

## Syntax Cheat Sheet

### Variables & Operations
- `SET x TO 10`
- `SET x TO x PLUS 5` or `SET x TO x + 5`
- `SHOW x`

### Functions
```
DEFINE name WITH arg1, arg2
    ...
    RETURN result
END DEFINE
```

### Control Flow
```
IF condition
    THEN ...
    ELSE ...
END IF

REPEAT 5 TIMES
    ...
END REPEAT
```

### Null-Safety
- `obj?.property` (Safe Call)
- `value ?: default` (Elvis)
- `value!!` (Not-null assertion)

### Modules
- `module my::namespace`
- `import other::module`

## Running the Demos

Use the provided demo runner script to parse, analyze, and compile all examples:

```bash
python3 demo_runner.py
```
