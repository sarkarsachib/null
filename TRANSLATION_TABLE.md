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

## AI/ML Instructions for Super-Bit Tensor Operations

NullVM extends the instruction set with AI/ML primitives for tensor-aware computation:

### AI Instruction Opcodes

| OpCode | Args | Description |
|--------|------|-------------|
| `AI_EMBED` | `[outputReg, embeddingId, dimension]` | Load or allocate an embedding into a tensor register |
| `AI_LAYER` | `[inputReg, outputReg, layerConfig, activation]` | Execute a dense layer forward pass |
| `AI_ATTEND` | `[inputReg, outputReg, attentionConfig]` | Apply self-attention with uncertainty reduction |
| `AI_FUZZY` | `[inputReg, outputReg, uncertaintyReduction]` | Reduce tensor uncertainty via fuzzy logic |

### Tensor Representation

Tensors in NullVM are represented as `SuperBitTensor` objects with:
- **Shape**: Multi-dimensional array dimensions (e.g., `[batch_size, seq_len, hidden_dim]`)
- **Data**: Float32Array containing values
- **Metadata**:
  - `uncertainty`: Probabilistic uncertainty value [0.0, 1.0]
  - `precision`: Numerical precision multiplier
  - `superbitEncoded`: Whether tensor uses super-bit encoding

### AI Instruction Details

#### AI_EMBED - Embedding Allocation

```javascript
{ opcode: 'AI_EMBED', args: ['output_register', 'embedding_id', dimension] }
```

**Behavior:**
- Queries the embedding registry for `embedding_id`
- If not found, creates a random dense embedding of size `dimension`
- Stores the embedding in `output_register` as a tensor
- Emits a control flow frame with shape and metadata

**Example:**
```javascript
{ opcode: 'AI_EMBED', args: ['token_embed', 'bert_wordpiece_001', 768] }
```

#### AI_LAYER - Dense Layer Forward Pass

```javascript
{ opcode: 'AI_LAYER', args: ['input_reg', 'output_reg', '{"outputDim": N}', 'activation'] }
```

**Behavior:**
- Reads tensor from `input_reg`
- Creates a dense layer with dimensions [inputDim, outputDim]
- Initializes weights using Xavier/Glorot initialization
- Applies activation function (relu, sigmoid, tanh, or linear)
- Stores output in `output_reg`
- Propagates uncertainty: `output_uncertainty = max(input_uncertainty, weight_uncertainty)`

**Supported Activations:**
- `linear`: No activation (identity)
- `relu`: Rectified Linear Unit (max(0, x))
- `sigmoid`: Logistic function (1/(1+e^-x))
- `tanh`: Hyperbolic tangent

**Example:**
```javascript
{ opcode: 'AI_LAYER', args: ['h0', 'h1', '{"outputDim": 2048}', 'relu'] }
```

#### AI_ATTEND - Self-Attention with Uncertainty Reduction

```javascript
{ opcode: 'AI_ATTEND', args: ['input_reg', 'output_reg', '{"headCount": N, ...}'] }
```

**Behavior:**
- Reads tensor from `input_reg`
- Applies multi-head self-attention mechanism
- Computes scaled dot-product attention: `Attention(Q,K,V) = softmax(QK^T/√d_k)V`
- Each attention head operates on input/N dimensions
- **Reduces uncertainty** through focused pattern matching
- Stores output in `output_reg`
- Default uncertainty reduction: 30% of input uncertainty

**Attention Config:**
- `headCount`: Number of attention heads (default: 1)
- `temperatureScale`: Softmax temperature scaling (default: 1.0)
- `uncertaintyReductionFactor`: Fraction of uncertainty to reduce (default: 0.3)

**Example:**
```javascript
{ opcode: 'AI_ATTEND', args: ['seq', 'attended', '{"headCount": 8, "temperatureScale": 1.0}'] }
```

#### AI_FUZZY - Probabilistic Uncertainty Reduction

```javascript
{ opcode: 'AI_FUZZY', args: ['input_reg', 'output_reg', uncertaintyReduction] }
```

**Behavior:**
- Reads tensor from `input_reg`
- Clones tensor to `output_reg`
- Reduces uncertainty by specified amount: `new_uncertainty = max(0, old - reduction)`
- Represents fuzzy logic evaluation refining tensor confidence
- Useful after probabilistic operations

**Example:**
```javascript
{ opcode: 'AI_FUZZY', args: ['noisy_tensor', 'refined_tensor', 0.25] }
```

### Complete AI Pipeline Example

```javascript
const program = [
  // Load embedding for input token
  { opcode: 'AI_EMBED', args: ['x', 'token_embedding_001', 512] },
  
  // First dense layer with ReLU
  { opcode: 'AI_LAYER', args: ['x', 'h1', '{"outputDim": 2048}', 'relu'] },
  
  // Second dense layer (linear)
  { opcode: 'AI_LAYER', args: ['h1', 'h2', '{"outputDim": 512}', 'linear'] },
  
  // Multi-head attention (8 heads)
  { opcode: 'AI_ATTEND', args: ['h2', 'attended', '{"headCount": 8}'] },
  
  // Optional: fuzzy refinement
  { opcode: 'AI_FUZZY', args: ['attended', 'logits', 0.1] },
  
  // Output the result
  { opcode: 'SHOW', args: ['logits'] }
];
```

### Uncertainty Propagation

Uncertainties flow through the computation graph:

1. **Initial embedding uncertainty**: 0.5 (for random embeddings)
2. **After dense layer**: `uncertainty = max(input_unc, weight_unc) × precision_product`
3. **After attention**: `uncertainty -= headCount × uncertaintyReductionFactor`
4. **After fuzzy**: `uncertainty -= specified_reduction`

Final uncertainty reflects cumulative confidence gains from deterministic computations and attention patterns.

### Memory Model Extension

Scalar registers (numeric) and tensor registers (SuperBitTensor) coexist:
- Scalar ops: `SET x 42`, `ADD x y`, `SHOW x`
- Tensor ops: `AI_EMBED t1 emb_001 128`, `AI_LAYER t1 t2 {...}`
- Mixed: Can read scalars, use for loop counts; independently manage tensors

### Binary Frame Emissions

AI instructions emit metadata frames for monitoring:
- `AI_EMBED`: Frame with embedding ID, dimension, loaded shape
- `AI_LAYER`: Frame with input/output shapes, activation used
- `AI_ATTEND`: Frame with input/output uncertainty (showing reduction)
- `AI_FUZZY`: Frame with uncertainty delta applied
