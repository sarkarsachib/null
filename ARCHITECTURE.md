# Null Compiler Architecture

## Overview

The Null compiler is a multi-stage compilation system that transforms English-based Null-Lang source code into executable binary frames and optionally executes them in the NullVM.

## Pipeline Stages

### 1. Lexical Analysis (Lexer)
- **Location:** `src/null_system/parser/lexer.py`
- **Input:** Raw source code string
- **Output:** List of tokens
- **Responsibilities:**
  - Tokenize English keywords (set, to, add, print, if, then, else, etc.)
  - Recognize identifiers, numbers, and strings
  - Skip comments (lines starting with #)
  - Track line and column numbers for error reporting

### 2. Syntactic Analysis (Parser)
- **Location:** `src/null_system/parser/parser.py`
- **Input:** Token stream
- **Output:** Abstract Syntax Tree (AST)
- **Responsibilities:**
  - Parse English-like syntax into structured AST nodes
  - Handle statements: set, print, if-then-else
  - Handle expressions: arithmetic, comparisons
  - Generate meaningful parse errors

### 3. Semantic Analysis (AST Validator)
- **Location:** `src/null_system/ast/validator.py`
- **Input:** AST
- **Output:** Validation errors list
- **Responsibilities:**
  - Check for undefined variables
  - Validate operation types
  - Ensure semantic correctness

### 4. Super-bit Emission
- **Location:** `src/null_system/superbit/emitter.py`
- **Input:** Validated AST
- **Output:** Super-bit token stream
- **Responsibilities:**
  - Convert AST nodes to super-bit instructions
  - Apply translation table (see TRANSLATION_TABLE.md)
  - Generate jump offsets for conditionals
  - Maintain stack-based instruction semantics

### 5. Optimization
- **Location:** `src/null_system/compiler/optimization.py`
- **Input:** Super-bit stream
- **Output:** Optimized super-bit stream
- **Responsibilities:**
  - **Deduplication Pass:** Remove duplicate consecutive operations
  - **Compression Pass:** Fold constant expressions at compile time
  - **Extensible:** Easy to add new optimization passes

### 6. Binary Generation
- **Location:** `src/null_system/binary/generator.py`
- **Input:** Super-bit stream
- **Output:** Binary frames
- **Responsibilities:**
  - Generate binary header (magic number "NULL", version)
  - Encode super-bit stream to bytes
  - Package into binary frames

### 7. Virtual Machine Execution (Optional)
- **Location:** `src/null_system/vm/vm.py`
- **Input:** Super-bit stream
- **Output:** Execution result (output, final state)
- **Responsibilities:**
  - Execute super-bit instructions
  - Maintain execution stack
  - Track variable state
  - Collect output from print statements
  - Handle control flow (jumps, conditionals)

## Component Details

### AST Nodes

All AST nodes inherit from `ASTNode` base class with line/column tracking:

- **Program:** Root node containing statement list
- **SetStatement:** Variable assignment
- **BinaryOp:** Binary operations (add, subtract, multiply, divide, comparisons)
- **PrintStatement:** Output statement
- **IfStatement:** Conditional branching
- **Identifier:** Variable reference
- **Literal:** Constant values (numbers, strings)

### Super-bit Instructions

Stack-based intermediate representation:

| Category | Instructions |
|----------|-------------|
| **Data** | LOAD_CONST, LOAD_VAR, STORE_VAR |
| **Arithmetic** | BINARY_ADD, BINARY_SUB, BINARY_MUL, BINARY_DIV |
| **Comparison** | COMPARE_GT, COMPARE_LT, COMPARE_EQ |
| **I/O** | PRINT |
| **Control Flow** | JUMP, JUMP_IF_FALSE |
| **Utility** | NOP |

### Binary Format

```
[Header: 16 bytes]
- Magic Number: "NULL" (4 bytes)
- Version: 1 byte
- Reserved: 11 bytes

[Code Section: Variable]
- Super-bit instructions encoded as bytes

[Constants Section: Variable]
- Future: Pre-allocated constant pool
```

## Compiler API

### NullCompiler Class

```python
compiler = NullCompiler(optimization_passes=[
    DeduplicationPass(),
    CompressionPass()
])

# Compile only
artifact = compiler.compile(source_code)
# Returns: CompilationArtifact with AST, super-bit, binary

# Compile and run
result = compiler.compile_and_run(source_code)
# Returns: ExecutionResult with output and final state
```

### CompilationArtifact

```python
artifact.ast                 # Abstract Syntax Tree
artifact.superbit_stream     # Super-bit token stream
artifact.binary_frames       # List of binary frames
artifact.validation_errors   # List of validation errors
artifact.is_valid()          # Check if compilation succeeded
```

### ExecutionResult

```python
result.success          # True if execution succeeded
result.output           # List of printed strings
result.error            # Error message if failed
result.final_state      # Dictionary of final variable values
```

## CLI Interface

### Commands

**Compile:**
```bash
nullc compile program.null --show-ast --show-superbit -o output.bin
```

**Run:**
```bash
nullc run program.null --verbose
```

**Info:**
```bash
nullc info
```

### Options

- `--show-ast`: Display the Abstract Syntax Tree
- `--show-superbit`: Display super-bit instructions
- `--optimize/--no-optimize`: Enable/disable optimizations
- `--verbose`, `-v`: Verbose output
- `--output`, `-o`: Output file path

## Extension Points

### Adding a New AST Node

1. Define node in `src/null_system/ast/nodes.py`
2. Add visitor method in `src/null_system/ast/validator.py`
3. Add parsing logic in `src/null_system/parser/parser.py`
4. Add emission logic in `src/null_system/superbit/emitter.py`
5. Add VM execution in `src/null_system/vm/vm.py` (if needed)

### Adding a New Optimization Pass

1. Create class extending `OptimizationPass`
2. Implement `optimize(stream: SuperBitStream) -> SuperBitStream`
3. Add to compiler initialization

### Adding a New Super-bit Instruction

1. Add to `SuperBitOpCode` enum
2. Add emission logic in `SuperBitEmitter`
3. Add execution logic in `NullVM`
4. Update translation table documentation

## Testing

### Test Structure

```
tests/
├── test_integration.py  # End-to-end integration tests
└── test_compiler.py     # Unit tests for compiler components
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/null_system --cov-report=html
```

## Performance Considerations

### Optimization Passes

- **Deduplication:** O(n) time, reduces redundant operations
- **Compression:** O(n) time, pre-computes constant expressions
- **Trade-off:** Compilation time vs. runtime performance

### Binary Format

- **Compact:** Minimal header overhead (16 bytes)
- **Streaming:** Instructions can be executed as they're decoded
- **Extensible:** Reserved header space for future features

## Future Enhancements

1. **Function definitions and calls**
2. **Loops (while, for)**
3. **Arrays and data structures**
4. **Module system and imports**
5. **Type inference and checking**
6. **Advanced optimizations** (dead code elimination, inlining)
7. **Debugging support** (breakpoints, step execution)
8. **JIT compilation** for hot code paths
