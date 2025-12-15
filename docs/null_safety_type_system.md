# Null-Lang Phase 3-4: Type System and Null Safety

## Overview

Phase 3-4 introduces a comprehensive type system with null-safety features, generics support, and sealed/data class declarations. The type inference pass annotates AST nodes with inferred types and enables compile-time null-safety checking.

## Type Inference System

### Architecture

The type inference system consists of three main components:

1. **TypeInference**: Main type inference engine
2. **TypeContext**: Scoped type environment maintaining variable, alias, and class definitions
3. **InferredType**: Represents types with nullability information

### Type Kinds

The system supports multiple type kinds:

- `PRIMITIVE`: Built-in types (int, float, string, bool, null)
- `DATA_CLASS`: User-defined data classes
- `SEALED_TRAIT`: Sealed trait types
- `GENERIC`: Generic/unknown types
- `ALIAS`: Type aliases
- `UNION`: Union types
- `FUNCTION`: Function types

### Nullability

All types carry nullability information:

- `NON_NULLABLE`: Cannot be null
- `NULLABLE`: Can be null
- `UNKNOWN`: Nullability not yet determined

## Type Annotations

### Basic Type Annotations

```
SET x: Int TO 5
SET name: String TO "Alice"
SET active: Bool TO TRUE
```

### Nullable Types

Append `?` to mark types as nullable:

```
SET user: User? TO NULL
SET count: Int? TO 10
```

### Generic Types

```
SET items: Array[Int] TO [1, 2, 3]
SET mapping: Object[String] TO {}
```

## Type Aliases

Define custom type names for existing types:

```
TYPE UserId = String
TYPE Email = String?

SET userId: UserId TO "user123"
```

## Data Classes

Declare structured data types:

```
CLASS DATA User WITH
  id: String,
  name: String,
  email: String?
END CLASS
```

Data classes support:
- Field type declarations
- Optional (nullable) fields
- Generic type parameters

## Sealed Traits

Create sealed type hierarchies for exhaustive matching:

```
SEALED TRAIT Result WITH Ok, Error
END SEALED
```

All subclasses must be listed. Used with MATCH statements to ensure exhaustive handling.

## Null-Safety Operators

### Safe-Call Operator (?.)

Access properties on potentially-null values safely:

```
SET address: String? TO user?.address
```

If `user` is null, the expression short-circuits and returns null.

### Elvis Operator (?:)

Provide a default value if the left side is null:

```
SET displayName: String TO user?.name ?: "Anonymous"
```

### Not-Null Assertion (!!)

Assert a value is non-null (runtime check):

```
SET nonNullUser: User TO user!!
```

Throws an error at runtime if the value is null.

## Smart Type Casting

Type narrowing in conditional contexts:

```
IF user IS NOT NULL THEN
  SET name: String TO user.name
END IF
```

After the null check, `user` is automatically narrowed to non-null within the block.

## Exhaustive Matching

For sealed traits, MATCH statements must cover all cases:

```
MATCH result WHEN
  Ok THEN SET value TO result.value
  Error THEN SET error TO result.error
END MATCH
```

Compiler enforces that all cases are handled.

## Type Inference Rules

### Literal Inference

- `42` → `int`
- `"hello"` → `string`
- `TRUE`/`FALSE` → `bool`
- `[]` → `array`
- `{}` → `object`
- `NULL` → `null`

### Type Unification

When combining types:
- Same types unify to themselves
- Type + null unifies to nullable version
- Different types fail unification (unless via union types)

### Assignability

- `int` assignable to `int?` ✓
- `int?` assignable to `int` ✗
- `null` assignable to `int?` ✓
- `null` assignable to `int` ✗

## Validation

The ASTValidator consumes type inference results to enforce:

1. **Null Safety**: Prevents unsafe access to nullable values without operators
2. **Type Safety**: Ensures type assignments are valid
3. **Exhaustiveness**: Enforces complete case handling for sealed types
4. **Smart Casts**: Validates type narrowing in conditions

### Example: Null Safety Validation

```
SET user: User? TO getUser()

-- Error: potentially null access without safe operator
SET name: String TO user.name  -- ✗

-- OK: safe access
SET name: String? TO user?.name  -- ✓

-- OK: elvis operator with non-null default
SET display: String TO user?.name ?: "Unknown"  -- ✓

-- OK: not-null assertion (runtime check)
SET name: String TO user!!.name  -- ✓
```

## Code Generation

The SuperBit emitter translates null-safety operators into efficient instruction sequences:

### Safe-Call (?.): Short-Circuit Load

```
LOAD_VAR user
SAFE_LOAD address        -- Short-circuits if null
```

### Elvis Operator (?:): Conditional Jump

```
LOAD_VAR value
ELVIS_OP else_branch     -- Jump to default if null
LOAD_VAR default
```

### Not-Null Assertion (!!): Runtime Check

```
LOAD_VAR value
NOT_NULL_ASSERT          -- Throws if null
```

## Type Context Scoping

Type contexts are hierarchical, supporting:

- Global type definitions
- Function-local types
- Block-level type narrowing

```
context = TypeContext(parent=global_context)
context.define_variable("x", InferredType(...))
```

## Error Examples

### Missing Case in Sealed Match

```
SEALED TRAIT Color WITH Red, Green, Blue
END SEALED

MATCH color WHEN
  Red THEN ...
  Green THEN ...
END MATCH
-- Error: Missing case 'Blue'
```

### Unsafe Null Access

```
SET x: Int? TO getValue()
SET y: Int TO x + 1
-- Error: Potentially null reference 'x'
```

### Type Mismatch

```
SET x: String TO 42
-- Error: Cannot assign int to string
```

## Testing

The type inference system includes comprehensive tests:

- `tests/analysis/test_type_inference.py`: Core type inference
- `tests/analysis/test_null_safety.py`: Null-safety operators
- `tests/analysis/test_sealed_traits.py`: Sealed trait exhaustiveness

## API Reference

### TypeInference

```python
inference = TypeInference(global_context)
inferred_type = inference.infer(ast_node)
is_assignable = inference.is_assignable(source, target)
narrowed = inference.narrow_type_in_condition(var_type, "is_not_null")
exhaustive = inference.check_exhaustive_match(trait_type, covered_cases)
```

### TypeContext

```python
context.define_variable(name, inferred_type)
context.define_type_alias(name, target_type)
context.define_data_class(name, DataClassDef(...))
context.define_sealed_trait(name, SealedTraitDef(...))
```

### ASTValidator

```python
validator = ASTValidator(inferred_types)
validator.check_non_null_safety(var_name, node)
validator.enforce_exhaustive_match(sealed_trait, handlers)
validator.set_nullable_variable(var_name)
validator.narrow_type(var_name, "is_not_null")
```

## Future Enhancements

- Variance annotations (covariant, contravariant)
- Recursive type definitions
- Type inference for function parameters
- Union type matching
- Type bounds and constraints
- Protocol/structural typing
