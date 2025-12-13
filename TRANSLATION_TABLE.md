# AST to Super-Bit Translation Table

This document describes how AST nodes are translated into Super-bit tokens during compilation.

## Translation Mappings

### Literals and Variables

| AST Node | Super-Bit Token | Operand |
|----------|----------------|---------|
| `Literal(value=X)` | `LOAD_CONST` | X |
| `Identifier(name=X)` | `LOAD_VAR` | X |

### Variable Assignment

| AST Node | Super-Bit Sequence | Description |
|----------|-------------------|-------------|
| `SetStatement(identifier=X, value=V)` | `[emit(V), STORE_VAR(X)]` | Evaluate value, then store in variable |

### Binary Operations

| AST Node | Super-Bit Token | Operand |
|----------|----------------|---------|
| `BinaryOp(op="add", ...)` | `BINARY_ADD` | None |
| `BinaryOp(op="subtract", ...)` | `BINARY_SUB` | None |
| `BinaryOp(op="multiply", ...)` | `BINARY_MUL` | None |
| `BinaryOp(op="divide", ...)` | `BINARY_DIV` | None |

**Pattern:** `[emit(left), emit(right), BINARY_OP]`

### Comparison Operations

| AST Node | Super-Bit Token | Operand |
|----------|----------------|---------|
| `BinaryOp(op="greater_than", ...)` | `COMPARE_GT` | None |
| `BinaryOp(op="less_than", ...)` | `COMPARE_LT` | None |
| `BinaryOp(op="equals", ...)` | `COMPARE_EQ` | None |

**Pattern:** `[emit(left), emit(right), COMPARE_OP]`

### Print Statement

| AST Node | Super-Bit Sequence | Description |
|----------|-------------------|-------------|
| `PrintStatement(value=V)` | `[emit(V), PRINT]` | Evaluate value, then print |

### Conditional Statement

| AST Node | Super-Bit Sequence | Description |
|----------|-------------------|-------------|
| `IfStatement(condition, then_branch, None)` | `[emit(condition), JUMP_IF_FALSE(end), emit(then_branch)]` | If without else |
| `IfStatement(condition, then_branch, else_branch)` | `[emit(condition), JUMP_IF_FALSE(else_start), emit(then_branch), JUMP(end), emit(else_branch)]` | If with else |

## Example Translations

### Example 1: Simple Assignment

**Null-Lang:**
```null
set x to 5
```

**AST:**
```
SetStatement(identifier="x", value=Literal(value=5, type="number"))
```

**Super-bit:**
```
0000: LOAD_CONST, 5
0001: STORE_VAR, x
```

### Example 2: Binary Operation

**Null-Lang:**
```null
add x and y
```

**AST:**
```
BinaryOp(op="add", left=Identifier(name="x"), right=Identifier(name="y"))
```

**Super-bit:**
```
0000: LOAD_VAR, x
0001: LOAD_VAR, y
0002: BINARY_ADD
```

### Example 3: Conditional

**Null-Lang:**
```null
if x is greater than 10 then print 'big' else print 'small'
```

**AST:**
```
IfStatement(
  condition=BinaryOp(op="greater_than", left=Identifier(name="x"), right=Literal(value=10)),
  then_branch=[PrintStatement(value=Literal(value="big"))],
  else_branch=[PrintStatement(value=Literal(value="small"))]
)
```

**Super-bit:**
```
0000: LOAD_VAR, x
0001: LOAD_CONST, 10
0002: COMPARE_GT
0003: JUMP_IF_FALSE, 7
0004: LOAD_CONST, big
0005: PRINT
0006: JUMP, 9
0007: LOAD_CONST, small
0008: PRINT
```

## Optimization Impact

The translation table can be affected by optimization passes:

### Deduplication Pass
Removes consecutive duplicate `LOAD_CONST` operations with the same operand.

### Compression Pass
Folds constant expressions at compile time:

**Before:**
```
LOAD_CONST, 5
LOAD_CONST, 3
BINARY_ADD
```

**After:**
```
LOAD_CONST, 8
```

## Super-Bit OpCode Reference

| OpCode | Value | Stack Effect | Description |
|--------|-------|--------------|-------------|
| `LOAD_CONST` | 1 | +1 | Push constant onto stack |
| `LOAD_VAR` | 2 | +1 | Push variable value onto stack |
| `STORE_VAR` | 3 | -1 | Pop value and store in variable |
| `BINARY_ADD` | 4 | -1 | Pop two values, push sum |
| `BINARY_SUB` | 5 | -1 | Pop two values, push difference |
| `BINARY_MUL` | 6 | -1 | Pop two values, push product |
| `BINARY_DIV` | 7 | -1 | Pop two values, push quotient |
| `COMPARE_GT` | 8 | -1 | Pop two values, push comparison result |
| `COMPARE_LT` | 9 | -1 | Pop two values, push comparison result |
| `COMPARE_EQ` | 10 | -1 | Pop two values, push comparison result |
| `PRINT` | 11 | -1 | Pop value and print to output |
| `JUMP_IF_FALSE` | 12 | -1 | Pop value, jump if false |
| `JUMP` | 13 | 0 | Unconditional jump |
| `NOP` | 14 | 0 | No operation |

## Security and Encryption

### Binary Metadata

When security and compression features are enabled, metadata is embedded in the binary frame:

```json
{
    "compression_algorithm": "lz4" or null,
    "compression_level": "low" | "medium" | "high" or null,
    "encryption_algorithm": "AES-256-GCM" or null,
    "encryption_key_id": "key-abc123",
    "encryption_nonce": "abcd...ef" (hex string),
    "encryption_tag": "1234...5678" (hex string)
}
```

### Advanced Compression

The `AdvancedCompressionPass` provides three levels of compression:

#### LOW Compression
- Run-Length Encoding (RLE) for consecutive identical tokens
- Minimal CPU overhead
- Moderate compression ratio

#### MEDIUM Compression
- RLE + Dictionary encoding
- Balances compression ratio and CPU usage
- Recommended for most use cases

#### HIGH Compression
- Aggressive RLE + Large dictionary (512 entries)
- Best compression ratio
- Higher CPU usage during decompression

#### Compression Impact on OpCodes

Compressed streams introduce new pseudo-opcodes:

| OpCode | Description |
|--------|-------------|
| `RLE:LOAD_CONST` | Run-length encoded LOAD_CONST with count operand |
| `RLE:BINARY_ADD` | Run-length encoded BINARY_ADD |
| `DICT` | Dictionary reference (operand is dictionary code) |

### Security and Key Management

#### Key Manager Configuration

Keys are stored in `~/.null_security/` by default:

- `keys.json` - Metadata for all keys
- `{key_id}.key` - Encrypted key material
- `{key_id}.salt` - Salt for password-derived keys

#### Encryption Flow

1. **Compilation**: Source → AST → SuperBit → Tokens
2. **Optional Compression**: Tokens → Compressed tokens
3. **Optional Encryption**: Stream → AES-256-GCM encrypted data
4. **Binary Generation**: Encrypted data + Metadata → Binary frame

#### Decryption Flow

1. **Binary Loading**: Read binary frame
2. **Metadata Extraction**: Get key_id, nonce, tag
3. **Key Lookup**: Load key from key manager
4. **Decryption**: AES-256-GCM decrypt with key/nonce/tag
5. **Optional Decompression**: Decompress if needed
6. **Execution**: Execute SuperBit stream

## CLI Flags for Security and Compression

### Compilation

```bash
nullc compile <file> \
  --compress <low|medium|high> \
  --security-profile <dev|prod> \
  --key-id <key-id>
```

- `--compress`: Enable advanced compression pass
- `--security-profile`: Enable encryption (prod creates key if needed)
- `--key-id`: Specify which key to use for encryption

### Execution

```bash
nullc run <file> \
  --compress <low|medium|high> \
  --security-profile <dev|prod> \
  --key-id <key-id>
```

The runtime automatically detects and transparently handles:
- Decompression based on metadata
- Decryption based on metadata and key lookup

## Performance Considerations

### Compression Trade-offs

| Level | Compression Ratio | CPU Overhead | Use Case |
|-------|-------------------|--------------|----------|
| LOW | ~80% | Very low | Fast startup, moderate size |
| MEDIUM | ~60% | Low | Balanced (recommended) |
| HIGH | ~40% | Moderate | Space-constrained environments |

### Encryption Overhead

- AES-256-GCM: ~1-5% CPU overhead (hardware accelerated on modern CPUs)
- Key derivation (PBKDF2): ~100ms at default 100k iterations
- Storage overhead: ~28 bytes per frame (nonce + tag)

## Examples with Security

### Compile with Encryption

```bash
# Compile with production security
nullc compile program.null -o program.bin --security-profile prod

# Compile with specific compression and encryption
nullc compile program.null -o program.bin --compress high --security-profile prod
```

### Run with Encryption

```bash
# Run with decryption (automatic)
nullc run program.null --security-profile prod

# Run with both compression and security
nullc run program.null --compress high --security-profile prod
```

## Metadata Structure in Binary Frames

Binary frames with version 2+ include optional metadata:

```
[MAGIC(4)]
[VERSION(1)]
[RESERVED(11)]
[CODE...]
[CONSTANTS...]
[METADATA_LENGTH(2)]
[METADATA_JSON]
```

Where METADATA_JSON contains encryption/compression information that allows downstream tools to properly decode and execute the program.
