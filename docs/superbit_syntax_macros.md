# Super-Bit Syntax Macros

## Overview

Super-Bit Syntax Macros extend the Null-Lang front end with compile-time constructs that emit optimized super-bit metadata and opcodes. These features enable zero-overhead encoding, compression, encryption, and pattern matching at the language level.

## Features

### 1. Super-Bit Literals

Super-bit literals provide a way to reference super-bit symbol encodings directly in source code. At compile time, these are resolved to their bit patterns and emitted as `LOAD_SUPERBIT` opcodes.

#### Syntax

```null
0x@SYMBOL_NAME   # Hexadecimal notation
0b@SYMBOL_NAME   # Binary notation
```

#### Examples

```null
# Reference command tokens
SET cmd TO 0x@SET
SET add_cmd TO 0x@ADD

# Use type symbols
SET text_type TO 0b@TEXT
SET num_type TO 0b@NUM

# Compose with other operations
SHOW 0x@SHOW
```

#### Compilation

Super-bit literals compile to `LOAD_SUPERBIT` opcodes with embedded metadata:
- `superbit_symbol`: The symbol name
- `prefix`: '0x' or '0b'
- `bits`: The bit pattern from the registry
- `bit_width`: Number of bits used

If the symbol is not found in the registry, falls back to `LOAD_CONST` with the symbol name as a string.

### 2. Macro Invocations

Macros are compile-time operations that transform data using super-bit utilities. They emit specialized opcodes that VMs can optimize.

#### Available Macros

| Macro | Purpose | Opcode |
|-------|---------|--------|
| `@encode(...)` | Super-bit encode values | `ENCODE_VALUE` |
| `@compress(...)` | Compress using super-bit dictionary/RLE | `COMPRESS_VALUE` |
| `@encrypt(...)` | Encrypt using super-bit security layer | `ENCRYPT_VALUE` |
| `@quantize(...)` | Quantize tensors to 4-8 bit super-bit | `QUANTIZE_VALUE` |

#### Syntax

```null
@macro_name(argument1, argument2, ...)
```

#### Examples

```null
# Encode a string
SET encoded TO @encode("Hello")

# Compress data
SET compressed TO @compress(large_data)

# Encrypt sensitive information
SET encrypted TO @encrypt("secret")

# Quantize ML weights
SET quantized TO @quantize(3.14159)

# Chain macros
SET result TO @encrypt(@compress(@encode(data)))

# Multiple arguments
SET multi TO @encode(value1, value2, value3)
```

#### Compilation

Each macro invocation:
1. Visits all argument expressions
2. Emits corresponding opcode (`ENCODE_VALUE`, `COMPRESS_VALUE`, etc.)
3. Includes metadata:
   - `macro`: The macro name
   - `arg_count`: Number of arguments

### 3. Pattern Matching

Pattern matching provides a structured way to handle super-bit encoded data with type-safe destructuring.

#### Syntax

```null
MATCH expression {
    pattern1 => { statements }
    pattern2 => { statements }
    ...
}
```

#### Pattern Types

##### Super-Bit Patterns

Match encoded super-bit data by pattern type:

```null
@pattern(type_name)              # Match without binding
@pattern(type_name) AS binding   # Match and bind to variable
```

Examples:
```null
MATCH value {
    @pattern(letters) => {
        SHOW "Contains letters"
    }
    @pattern(numbers) AS nums => {
        SHOW "Contains numbers"
        SHOW nums
    }
}
```

##### Literal Patterns

Match against specific values:

```null
MATCH x {
    42 => { SHOW "Forty-two" }
    "hello" => { SHOW "Greeting" }
    TRUE => { SHOW "Truth" }
}
```

##### Identifier Patterns (Fallback)

Catch-all pattern that binds to a variable:

```null
MATCH value {
    @pattern(special) => { SHOW "Special case" }
    default => { SHOW "Default case" }
}
```

#### Compilation

Pattern matching compiles to:
1. Load the match value
2. For each arm:
   - Emit `MATCH_PATTERN` opcode with pattern metadata
   - Emit `JUMP_IF_FALSE` to next arm
   - Emit arm body statements
   - Emit `JUMP` to end
3. Patch all jump targets

Metadata for super-bit patterns:
- `pattern_type`: The pattern type name
- `binding`: Optional variable binding name

## Integration with Layer Annotations

Super-bit features work seamlessly with layer annotations:

```null
@layer(superbit)
SET data TO @encode(0x@SET)

@require(superbit, binary)
MATCH data {
    @pattern(encoded) => {
        SHOW "Processing on super-bit layer"
    }
}

@prefer(gpu, cpu)
SET quantized TO @quantize(weights)
```

## IR Opcodes

New opcodes added to `SuperBitOpCode`:

```python
LOAD_SUPERBIT = 60    # Load pre-encoded super-bit literal
ENCODE_VALUE = 61     # Encode using super-bit encoding
COMPRESS_VALUE = 62   # Compress using super-bit compression
ENCRYPT_VALUE = 63    # Encrypt using super-bit security
QUANTIZE_VALUE = 64   # Quantize to super-bit representation
```

Existing opcodes used:
```python
MATCH_PATTERN = 52    # Pattern matching
JUMP_IF_FALSE = 40    # Conditional branching
JUMP = 41             # Unconditional branching
```

## Complete Example

```null
# Super-bit data pipeline
SET raw_input TO "Sensitive Data"

# Encode using super-bit symbols
SET encoded TO @encode(raw_input)

# Compress for efficiency
SET compressed TO @compress(encoded)

# Encrypt for security
SET secure TO @encrypt(compressed)

# Pattern match on result
MATCH secure {
    @pattern(encrypted) AS e => {
        SHOW "Data secured successfully"
        
        # Store literal token
        SET token TO 0x@SET
        SHOW token
    }
    @pattern(error) AS err => {
        SHOW "Encryption failed"
        SHOW err
    }
    fallback => {
        SHOW "Unknown result"
    }
}

# ML quantization workflow
SET model_weights TO [3.14159, 2.71828, 1.41421]

MATCH model_weights {
    weights => {
        SET quantized TO @quantize(weights)
        SHOW "Quantized to 4-8 bit super-bit"
        SHOW quantized
    }
}
```

## Zero-Overhead Guarantee

All super-bit macros execute at **compile time**, producing optimized IR:

1. **Super-bit literals**: Resolved to bit patterns at parse time
2. **Encoding macros**: Use existing encoder utilities during compilation
3. **Pattern matching**: Compiles to efficient jump tables
4. **No runtime overhead**: VMs execute pre-optimized opcodes

## Best Practices

### 1. Use Super-Bit Literals for Known Symbols

```null
# Good - compile-time resolution
SET cmd TO 0x@SET

# Less optimal - runtime string
SET cmd TO "SET"
```

### 2. Chain Macros for Data Pipelines

```null
# Efficient pipeline
SET result TO @encrypt(@compress(@encode(data)))
```

### 3. Use Pattern Matching for Type Safety

```null
MATCH response {
    @pattern(success) AS s => { # Handle success }
    @pattern(error) AS e => { # Handle error }
}
```

### 4. Combine with Layer Annotations

```null
@layer(superbit)
@require(gpu)
SET quantized TO @quantize(tensor)
```

## Registry Symbols

Symbols available for super-bit literals (from `superbit/registry.py`):

### Commands (6-bit)
- `SET`, `ADD`, `IF`, `THEN`, `ELSE`
- `SHOW`, `REPEAT`, `DEFINE`, `CALL`
- `END`, `TO`, `WITH`, `TIMES`

### Types (4-bit)
- `TEXT`, `NUM`, `BOOL`, `ARRAY`, `OBJECT`

### Operators (5-bit)
- `PLUS`, `MINUS`, `TIMES`, `DIVIDED`
- `AND`, `OR`, `NOT`

### Boolean Values (3-bit)
- `TRUE`, `FALSE`

Custom symbols can be registered via the SymbolRegistry API.

## Error Handling

### Unknown Symbols

If a super-bit literal references an unknown symbol:
```null
SET x TO 0x@UNKNOWN  # Falls back to LOAD_CONST with "UNKNOWN" string
```

### Macro Errors

Macro argument errors are caught at compile time:
```null
@encode()  # OK - zero arguments
@encode(x, y)  # OK - multiple arguments
```

### Pattern Matching

Unmatched patterns fall through to next arm or end:
```null
MATCH value {
    @pattern(type1) => { # Arm 1 }
    @pattern(type2) => { # Arm 2 }
    # If neither matches, control flow exits match
}
```

## Implementation Details

### AST Nodes

New AST node types:

```python
@dataclass
class SuperBitLiteral(ASTNode):
    prefix: str      # '0x' or '0b'
    symbol: str      # Symbol name

@dataclass
class MacroInvocation(ASTNode):
    name: str                  # Macro name
    arguments: List[ASTNode]   # Argument expressions

@dataclass
class SuperBitPattern(ASTNode):
    pattern_type: str          # Pattern type
    binding: Optional[str]     # Optional variable binding

@dataclass
class PatternArm(ASTNode):
    pattern: ASTNode           # Pattern to match
    body: List[ASTNode]        # Arm body statements

@dataclass
class MatchCommand(ASTNode):
    value: ASTNode             # Expression to match
    arms: List[PatternArm]     # Match arms
    annotations: List[...]     # Layer annotations
```

### Grammar Rules

```lark
superbit_literal: SUPERBIT_HEX_LITERAL
                | SUPERBIT_BIN_LITERAL

macro_invocation: "@" "encode" "(" (argument_list)? ")"
                | "@" "compress" "(" (argument_list)? ")"
                | "@" "encrypt" "(" (argument_list)? ")"
                | "@" "quantize" "(" (argument_list)? ")"

match_statement: "MATCH" expression "{" match_arm+ "}"

match_arm: pattern "=>" "{" match_body "}"

pattern: superbit_pattern
       | identifier_pattern
       | literal

superbit_pattern: "@pattern" "(" identifier ")" ("AS" identifier)?

SUPERBIT_HEX_LITERAL: /0x@[a-zA-Z_][a-zA-Z0-9_]*/
SUPERBIT_BIN_LITERAL: /0b@[a-zA-Z_][a-zA-Z0-9_]*/
```

## Future Enhancements

1. **Pattern Guards**: Add `WHEN` clauses to patterns
2. **Destructuring**: Extract nested values in patterns
3. **Macro Composition**: Define custom macros
4. **Optimizations**: Macro fusion and constant folding
5. **SIMD Patterns**: Vectorized pattern matching

## See Also

- [Super-Bit Encoding](../TRANSLATION_TABLE.md)
- [Layer Annotations](../IMPLEMENTATION.md#layer-annotations)
- [Compiler Architecture](architecture.md)
- [Super-Bit IR](../src/null_system/superbit/ir.py)
