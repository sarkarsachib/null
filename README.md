# Null-Lang Compiler System

A compiler and virtual machine for Null-Lang, an English-based programming language.

## Features

- **Natural Language Syntax**: Write code in plain English
- **Multi-stage Compilation**: Parsing → AST → Super-bit → Binary
- **Virtual Machine**: Execute compiled programs directly
- **Rich CLI**: Beautiful command-line interface with diagnostics
- **Optimization**: Configurable optimization passes (deduplication, constant folding)
- **Comprehensive Testing**: 28+ integration and unit tests
- **Translation Tables**: Well-documented AST to super-bit mappings

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

Create a simple program (`hello.null`):
```null
print 'Hello, World!'
```

Run it:
```bash
nullc run hello.null
```

## Usage

### Compile a Null-Lang file:
```bash
nullc compile program.null
```

### Compile with output binary:
```bash
nullc compile program.null -o output.bin
```

### Compile and run:
```bash
nullc run program.null
```

### Show compilation details:
```bash
nullc compile program.null --show-ast --show-superbit
```

### Disable optimizations:
```bash
nullc run program.null --no-optimize
```

### Get help:
```bash
nullc --help
nullc info
```

## Null-Lang Syntax

### Variables
```null
set x to 5
set name to 'Alice'
```

### Arithmetic
```null
set x to 10
set y to 5
add x and y
subtract x and y
multiply x and 2
divide x and 2
```

### Printing
```null
set x to 42
print x
print 'Hello, World!'
```

### Conditionals
```null
set age to 25
if age is greater than 18 then print 'adult' else print 'minor'

set x to 10
if x is less than 20 then print 'small' else print 'big'

set y to 5
if y is equals 5 then print 'exact' else print 'not exact'
```

### Comments
```null
# This is a comment
set x to 5  # Comments are ignored
```

More examples can be found in the `examples/` directory.

## Architecture

The Null compiler uses a 7-stage compilation pipeline:

1. **Lexical Analysis**: Tokenize English-like source code
2. **Parsing**: Build Abstract Syntax Tree (AST)
3. **Validation**: Semantic analysis and error checking
4. **Super-bit Emission**: Convert AST to intermediate representation
5. **Optimization**: Apply optimization passes
6. **Binary Generation**: Produce executable binary frames
7. **Execution**: Run in NullVM (optional)

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.

## Translation Table

The compiler uses a translation table to convert AST nodes to super-bit instructions:

| AST Node | Super-bit Instructions |
|----------|----------------------|
| `Literal(5)` | `LOAD_CONST 5` |
| `Identifier("x")` | `LOAD_VAR x` |
| `SetStatement("x", 5)` | `LOAD_CONST 5, STORE_VAR x` |
| `BinaryOp("add", x, y)` | `LOAD_VAR x, LOAD_VAR y, BINARY_ADD` |

See [TRANSLATION_TABLE.md](TRANSLATION_TABLE.md) for complete mappings.

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=src/null_system
```

All tests (28 total):
- Integration tests: Full compilation pipeline tests
- Unit tests: Individual component tests
- Optimization tests: Verify optimization passes work correctly

## Project Structure

```
src/null_system/
├── ast/              # AST nodes and validation
├── parser/           # Lexer and parser
├── superbit/         # Super-bit emission
├── binary/           # Binary frame generation
├── vm/               # Virtual machine
├── compiler/         # Main compiler orchestration
└── cli.py            # Command-line interface

tests/
├── test_integration.py  # Integration tests
└── test_compiler.py     # Unit tests

examples/
├── hello.null           # Hello World
├── arithmetic.null      # Arithmetic operations
├── conditional.null     # Conditional logic
└── comprehensive.null   # Full feature demo
```

## API Usage

```python
from null_system.compiler import NullCompiler
from null_system.compiler.optimization import DeduplicationPass, CompressionPass

# Create compiler with optimizations
compiler = NullCompiler(optimization_passes=[
    DeduplicationPass(),
    CompressionPass()
])

# Compile source code
source = """
set x to 10
print x
"""
artifact = compiler.compile(source)

# Check for errors
if artifact.is_valid():
    print(f"Compiled {len(artifact.superbit_stream.tokens)} instructions")
    print(f"Binary size: {sum(len(f) for f in artifact.binary_frames)} bytes")

# Compile and run
result = compiler.compile_and_run(source)
if result.success:
    print("Output:", result.output)
    print("Final state:", result.final_state)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details
