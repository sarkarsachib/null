# Null-Lang Type System - Phase 3-4 Upgrade

## Overview

Phase 3-4 introduces a comprehensive type system with full null-safety support, type inference, and advanced features like sealed classes and data classes.

## Key Features

### 1. Type Inference

The `TypeInference` class in `analysis/type_inference.py` provides:
- **Automatic type inference** for all AST nodes
- **Type context** for tracking variable and type alias definitions
- **Nullable vs non-nullable** distinctions
- **Generic type parameters** support
- **Sealed class** and **data class** metadata tracking

#### Type Inference Usage

```python
from src.null_system.analysis.type_inference import TypeInference, InferredType
from src.null_system.lang.parser import NullLangParser

parser = NullLangParser()
inference = TypeInference()

# Parse and infer types
program = parser.parse("SET x TO 42")
inferred_type = inference.infer(program)
```

#### InferredType

Represents a type with nullability information:

```python
# Non-nullable number
num_type = InferredType("number", is_nullable=False)

# Nullable string
str_type = InferredType("string", is_nullable=True)
print(str_type.nullable_name)  # "string?"

# Generic array of numbers
array_type = InferredType(
    "array",
    type_parameters=[InferredType("number")]
)
print(array_type.full_name)  # "array<number>"
```

### 2. Type Annotations

#### Explicit Type Annotations

```null
let user: UserId = 123
let name: string = "Alice"
let items: array<number> = [1, 2, 3]
let optional: string? = null
```

#### Type Aliases

Define custom type names:

```null
type UserId = number
type Email = string
type Result<T, E> = union { Ok(T), Err(E) }
```

#### Data Classes

Define structured types with named fields:

```null
class data Point {
  x: number,
  y: number
}

class data Person {
  name: string,
  age: number,
  email: string?
}
```

#### Sealed Traits

Define constrained union types:

```null
sealed trait Result<T, E> {
  Ok(T),
  Err(E)
}

sealed trait Option<T> {
  Some(T),
  None
}

sealed trait Status {
  Active,
  Inactive,
  Pending
}
```

### 3. Null-Safety Operators

#### Safe Call Operator (?.)

Short-circuits on null values:

```null
SET result TO obj?. property
SET item TO array?. [0]
SET value TO obj?. method()
```

Equivalent short-circuit logic:
```
if obj is not null {
  SET result TO obj.property
} else {
  SET result TO null
}
```

#### Elvis Operator (?:)

Provides a default value for null:

```null
SET name TO user?. name ?: "Anonymous"
SET count TO items?. length ?: 0
```

Equivalent logic:
```
SET temp TO user?. name
if temp is not null {
  SET name TO temp
} else {
  SET name TO "Anonymous"
}
```

#### Not-Null Assertion (!!)

Asserts and unwraps a nullable value:

```null
SET x TO value!!
```

Raises an error if `value` is null. Used after smart casts:

```null
if x is string {
  SET str TO x!!
  SET upper TO str.toUpperCase()
}
```

### 4. Smart Casts in Conditions

Type narrowing based on conditions:

```null
if x is string {
  SHOW x.toUpperCase()
}

if result is Ok {
  SHOW result.value
}

if status is Active {
  SET active_items TO all_items
}
```

### 5. Exhaustive Match for Sealed Classes

Compiler ensures all cases are handled:

```null
sealed trait Color { Red, Green, Blue }

MATCH color
  WHEN Red => SET rgb TO [255, 0, 0]
  WHEN Green => SET rgb TO [0, 255, 0]
  WHEN Blue => SET rgb TO [0, 0, 255]
END
```

Missing cases cause compilation errors.

## Architecture

### Type Inference Pass

**Location**: `src/null_system/analysis/type_inference.py`

1. **TypeInference Class**: Main inference engine
   - Maintains type context across AST traversal
   - Infers types for all node types
   - Tracks sealed classes and data classes
   - Validates type assignability

2. **InferredType**: Represents a type
   - Base type name (e.g., "number", "string", "MyClass")
   - Nullability flag
   - Type parameters for generics

3. **TypeContext**: Inference state
   - Variable type bindings
   - Type alias definitions
   - Sealed class registry
   - Data class registry

### Parser Extensions

**Location**: `src/null_system/lang/grammar.lark` and `src/null_system/lang/parser.py`

New grammar rules:
- `type_annotation`: Parse type expressions with nullability
- `type_alias_statement`: Parse type alias declarations
- `data_class_statement`: Parse data class declarations
- `sealed_trait_statement`: Parse sealed trait declarations
- `let_binding_statement`: Parse let bindings with types
- `safe_call_expr`: Parse `?.` operator
- `elvis_expr`: Parse `?:` operator
- `not_null_expr`: Parse `!!` operator

### Compiler Code Generation

**Location**: `src/null_system/lang/compiler.py`

New opcodes for null-safety:
- `SAFE_CALL` (60): Execute property/method access with null check
- `ELVIS_CHECK` (61): Check for null and return alternative
- `NOT_NULL_CHECK` (62): Assert non-null or raise error
- `SMART_CAST` (63): Narrow type based on condition

### Validator Extensions

**Location**: `src/null_system/ast/validator.py`

Enhanced validation:
- Type consistency checking
- Sealed class exhaustiveness checking
- Nullable/non-nullable conformance
- Data class field validation
- Integrates with TypeInference for semantic analysis

## Implementation Examples

### Type Inference Example

```python
from src.null_system.analysis.type_inference import TypeInference
from src.null_system.lang.ast_nodes import (
    NumLiteral, TextLiteral, BinaryExpression, BinaryOperator
)

inference = TypeInference()

# Infer number type
num = NumLiteral(value=42)
assert inference.infer(num).base_type == "number"

# Infer string type
text = TextLiteral(value="hello")
assert inference.infer(text).base_type == "string"

# Infer arithmetic result type
left = NumLiteral(value=10)
right = NumLiteral(value=20)
add = BinaryExpression(operator=BinaryOperator.ADD, left=left, right=right)
assert inference.infer(add).base_type == "number"
```

### Type Annotation Example

```python
from src.null_system.lang.ast_nodes import TypeAnnotation

# Non-nullable type
number_type = TypeAnnotation(type_name="number", is_nullable=False)

# Nullable type
optional_string = TypeAnnotation(type_name="string", is_nullable=True)

# Generic type
array_of_numbers = TypeAnnotation(
    type_name="array",
    is_nullable=False,
    type_parameters=[
        TypeAnnotation(type_name="number", is_nullable=False)
    ]
)
```

### Data Class Example

```python
from src.null_system.lang.ast_nodes import (
    DataClassDeclaration, TypeAnnotation
)

person_class = DataClassDeclaration(
    name="Person",
    fields=[
        ("name", TypeAnnotation(type_name="string", is_nullable=False)),
        ("age", TypeAnnotation(type_name="number", is_nullable=False)),
        ("email", TypeAnnotation(type_name="string", is_nullable=True)),
    ]
)
```

### Sealed Class Example

```python
from src.null_system.lang.ast_nodes import (
    SealedTraitDeclaration, TypeAnnotation
)

result_type = SealedTraitDeclaration(
    name="Result",
    type_parameters=["T", "E"],
    variants=[
        ("Ok", TypeAnnotation(type_name="T", is_nullable=False)),
        ("Err", TypeAnnotation(type_name="E", is_nullable=False)),
    ]
)
```

### Safe Call Example

```python
from src.null_system.lang.ast_nodes import (
    SafeCallExpression, Identifier
)

safe_call = SafeCallExpression(
    object=Identifier(name="user"),
    member="email",
    is_call=False
)
```

### Elvis Operator Example

```python
from src.null_system.lang.ast_nodes import (
    ElvisExpression, Identifier, TextLiteral
)

elvis = ElvisExpression(
    left=Identifier(name="name"),
    right=TextLiteral(value="Anonymous")
)
```

## Type Inference Rules

### Literals
- `number` → `number`
- `string` → `string`
- `true`/`false` → `boolean`
- `[...]` → `array<T>` where T is inferred from elements
- `{...}` → `object`

### Binary Operators
- Arithmetic (+, -, *, /) → `number`
- Comparison (==, !=, <, >, <=, >=) → `boolean`
- Logical (AND, OR) → `boolean`

### Unary Operators
- NOT → `boolean`
- NEGATE (-) → `number`

### Safe Call (?.)
- Input: `T?` → Output: `T?`
- Input: `T` (non-null) → Output: `T?`

### Elvis (?:)
- Left: `T?`, Right: `U` → Output: `T | U`
- Removes nullability if right side is non-null

### Not-Null (!!)
- Input: `T?` → Output: `T`
- Runtime error if input is null

## Validation Rules

### Non-Null Defaults
- Variables without type annotations assume non-nullable
- Explicit `Type?` syntax required for nullable types

### Sealed Class Exhaustiveness
- All match/when statements on sealed types must cover all cases
- Compiler error if coverage is incomplete

### Type Assignability
- Non-nullable types assignable to nullable types
- Nullable types NOT assignable to non-nullable types without assertion

### Data Class Fields
- All fields must have explicit types
- Fields are non-nullable by default

## Error Handling

Common type errors:

```
1. Null Access Without Safe Call
   ERROR: Cannot access property on nullable type without ?.
   
2. Non-Exhaustive Match
   ERROR: Sealed class Result not fully covered
   Missing cases: Err
   
3. Nullable Assignment to Non-Nullable
   ERROR: Cannot assign nullable string? to non-nullable string
   Use !! to assert non-null or ?: to provide default
   
4. Undefined Variable/Type
   ERROR: Undefined type: UserId
   
5. Type Mismatch
   ERROR: Expected number but got string
```

## Performance Considerations

- **Single-pass inference**: Type inference runs in one traversal
- **Lazy evaluation**: Types computed on-demand
- **Context caching**: Sealed/data class info cached for exhaustiveness checks
- **Incremental validation**: Errors collected without early exit

## Future Enhancements

1. **Variance Annotations**: Covariance/contravariance for generics
2. **Type Bounds**: Constrained type parameters
3. **Implicit Conversions**: Automatic type coercions
4. **Union Type Operators**: `|` for union types
5. **Intersection Types**: `&` for intersection types
6. **Recursive Types**: Self-referential type definitions
7. **Existential Types**: `exists T. ...`
8. **Higher-Rank Types**: Polymorphic function types

## Testing

Run type system tests:

```bash
# Type inference tests
pytest tests/test_type_inference.py -v

# Null-safety operator tests
pytest tests/test_null_safety.py -v

# All type-related tests
pytest tests/test_type_inference.py tests/test_null_safety.py -v
```

## Integration Points

- **Parser**: Type annotations and operators parsed into AST
- **Compiler**: Inference results threaded through code generation
- **Validator**: Uses inference for semantic analysis
- **VM**: Runtime type tags for smart casts
- **Debugger**: Type info available for inspection

## Resources

- [Type System Theory](https://en.wikipedia.org/wiki/Type_system)
- [Null Safety](https://en.wikipedia.org/wiki/Null_pointer#Null_safety)
- [Sealed Classes](https://en.wikipedia.org/wiki/Sealed_class)
- [Type Inference](https://en.wikipedia.org/wiki/Type_inference)
