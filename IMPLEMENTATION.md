# Null-Lang Parser Implementation

## Summary

This implementation provides a complete English-like programming language parser for Null-Lang, built using the Lark parsing library.

## Components Implemented

### 1. **AST Node Definitions** (`src/null_system/lang/ast_nodes.py`)
- Base `ASTNode` class with source span tracking
- **Literal nodes**: TextLiteral, NumLiteral, BoolLiteral, ArrayLiteral, ObjectLiteral
- **Command nodes**: SetCommand, AddCommand, IfCommand, ShowCommand, RepeatCommand, DefineCommand
- **Expression nodes**: BinaryExpression, UnaryExpression, ComparisonExpression
- **Annotation nodes**: LayerAnnotation, RequireAnnotation, PreferAnnotation
- **Other nodes**: Identifier, MemberAccess, FunctionCall, NullLibAnnotation, Program, Comment
- **Source tracking**: SourceSpan class for error reporting with line/column information
- **Annotation support**: All command nodes have optional `annotations` field for layer metadata

### 2. **Grammar Definition** (`src/null_system/lang/grammar.lark`)
- Lark-based LALR grammar
- English-like command syntax
- Expression hierarchy with proper precedence
- Support for:
  - Commands: SET, ADD, IF/THEN/ELSE, SHOW, REPEAT, DEFINE
  - Literals: strings, numbers, booleans, arrays, objects
  - Operators: arithmetic, comparison, logical
  - Member access: property and index notation
  - Function calls: CALL syntax and parentheses syntax
  - Layer annotations: @layer(name), @require(layer1, layer2), @prefer(layer1, layer2)
  - Legacy Null-Lib annotations: @lib.function(args) - fully backward compatible
  - Comments: hash-style (#)

### 3. **Parser Implementation** (`src/null_system/lang/parser.py`)
- `NullLangTransformer`: Lark transformer that converts parse tree to AST
- `NullLangParser`: Main parser class
- Convenience functions: `parse()`, `parse_statement()`
- Comprehensive span tracking for all nodes
- Detailed error handling
- Annotation transformation: Converts layer annotation syntax to AST nodes with proper attachment to statements

### 3.5. **Compiler to Super-Bit IR** (`src/null_system/lang/compiler.py`)
- `NullLangCompiler`: Compiles Null-Lang AST to Super-Bit IR tokens
- Threads layer annotation metadata into each IR token via `metadata` dictionary
- Metadata keys: `layer`, `requires`, `prefers`, `source_layer_line`
- Allows downstream VMs/tooling to route instructions to specific execution layers
- Convenience function: `compile_program()` for end-to-end source-to-IR compilation

### 4. **Error Reporting** (`src/null_system/lang/errors.py`)
- Base `NullLangError` class
- Specific error types: `SyntaxError`, `LexerError`, `SemanticError`
- Rich error formatting with:
  - Source location (line and column)
  - Context showing the error line
  - Caret indicators pointing to the error

### 5. **Test Fixtures** (`fixtures/lang/`)
Seven comprehensive fixture files demonstrating all language features:
- `simple_statements.null`: Basic SET, SHOW, ADD statements
- `control_flow.null`: IF/THEN/ELSE and REPEAT loops
- `functions.null`: DEFINE and CALL with parameters
- `collections.null`: Arrays and objects with member access
- `expressions.null`: Arithmetic, comparisons, logical operations
- `null_lib_annotations.null`: @lib.function syntax
- `complete_program.null`: Complex multi-feature program

### 6. **Unit Tests** (`tests/lang/test_parser.py` and `tests/lang/test_annotations.py`)
**Parser Tests** - 75 comprehensive tests organized into 10 test classes:
- **TestLiterals**: 14 tests for all literal types
- **TestIdentifiersAndMemberAccess**: 4 tests for identifiers and access patterns
- **TestCommands**: 11 tests for all command types
- **TestExpressions**: 14 tests for expressions and operators
- **TestFunctionCalls**: 4 tests for function invocation
- **TestNullLibAnnotations**: 3 tests for Null-Lib calls
- **TestPrograms**: 4 tests for multi-statement programs
- **TestComments**: 1 test for comment handling
- **TestErrorHandling**: 6 tests for error diagnostics
- **TestFixtures**: 7 tests verifying all fixture files parse correctly
- **TestEdgeCases**: 6 tests for edge cases and complex scenarios

**Layer Annotation Tests** - 32 comprehensive tests organized into 6 test classes:
- **TestLayerAnnotationParsing**: 15 tests for @layer, @require, @prefer syntax
- **TestAnnotationCompilation**: 6 tests for IR metadata threading
- **TestAnnotationErrors**: 5 tests for error handling
- **TestAnnotationIntegration**: 3 tests for end-to-end workflows
- **TestEdgeCases**: 3 tests for corner cases

All tests cover:
- ✅ Happy paths (correct syntax)
- ✅ Malformed input diagnostics
- ✅ Error message quality
- ✅ Source span accuracy
- ✅ Legacy construct compatibility (@lib.fn still works)
- ✅ Metadata round-trip through parse→compile

## Language Syntax Examples

### Variables and Literals
```null
SET x TO 42
SET name TO "Alice"
SET active TO TRUE
SET numbers TO [1, 2, 3]
SET person TO { name: "Bob", age: 25 }
```

### Arithmetic and Expressions
```null
SET result TO 10 PLUS 5
SET result TO (2 PLUS 3) TIMES 4
SET opposite TO NOT TRUE
```

### Comparisons
```null
IF x IS GREATER THAN 10 THEN
    SHOW "Large"
ELSE
    SHOW "Small"
END IF
```

### Loops
```null
REPEAT 5 TIMES
    SHOW "Hello"
END REPEAT
```

### Functions
```null
DEFINE greet WITH name
    SHOW "Hello"
    SHOW name
END DEFINE

CALL greet WITH "Alice"
```

### Null-Lib Annotations
```null
SET data TO @http.get("https://api.example.com")
SET result TO @math.calculate("sum", 10, 20, 30)
```

### Layer Annotations (Multi-Layer Execution)
Layer annotations specify which execution layer(s) should handle a statement:

```null
# Execute on binary layer
@layer(binary) SET x TO 42

# Require superbit and binary layers
@require(superbit, binary) SET y TO x

# Prefer GPU execution with fallback to CPU
@prefer(gpu, cpu) SET z TO y PLUS 100

# Multiple annotations on a single statement
@layer(superbit) @require(binary) SET result TO x TIMES y

# Annotations work on all statement types
@layer(binary) IF x IS GREATER THAN 10 THEN
    SHOW "Greater"
END IF

@prefer(gpu) REPEAT 1000 TIMES
    SET x TO x PLUS 1
END REPEAT

@require(ml) DEFINE neural_forward WITH input
    # Neural network forward pass
END DEFINE
```

Metadata is threaded into the compiled IR:
- `@layer(name)` → `metadata['layer'] = 'name'`
- `@require(l1, l2)` → `metadata['requires'] = ['l1', 'l2']`
- `@prefer(l1, l2)` → `metadata['prefers'] = ['l1', 'l2']`

Downstream tooling (VMs, debuggers) can use this metadata to route instructions to the appropriate execution layer.

## Technical Decisions

### 1. Expression Precedence
Implemented standard precedence hierarchy:
1. OR (lowest)
2. AND
3. Comparisons (IS, IS GREATER THAN, etc.)
4. Arithmetic (PLUS, MINUS)
5. Term (TIMES, DIVIDED BY)
6. Unary (NOT, MINUS)
7. Atoms (literals, identifiers, etc.)

### 2. Ambiguity Resolution
- **REPEAT COUNT**: Uses `atom` instead of `expression` to prevent "TIMES" being interpreted as multiplication
- **ADD AND**: Uses `comparison_expression` to prevent "AND" being interpreted as logical AND
- **Grammar markers**: Uses `?` prefix for inline rules to flatten the parse tree

### 3. Error Recovery
- Catches Lark exceptions and wraps them with detailed context
- Provides source spans for all errors
- Shows problematic source line with caret indicators

### 4. AST Design
- Base class is regular class (not dataclass) to avoid initialization ordering issues
- All derived nodes are dataclasses for clean syntax
- Span tracking is inherited from base class

## Usage

```python
from src.null_system.lang import parse, SyntaxError

try:
    ast = parse('SET x TO 42')
    print(f"Parsed successfully: {ast}")
except SyntaxError as e:
    print(f"Parse error: {e}")
```

## Testing

```bash
# Run parser tests
pytest tests/lang/test_parser.py -v

# Run annotation tests
pytest tests/lang/test_annotations.py -v

# Run all lang tests
pytest tests/lang/ -v

# Run with coverage
pytest tests/lang/ --cov=src/null_system/lang

# Run specific test class
pytest tests/lang/test_parser.py::TestLiterals -v
pytest tests/lang/test_annotations.py::TestLayerAnnotationParsing -v

# Run with detailed output
pytest tests/lang/test_annotations.py::TestAnnotationCompilation -xvs
```

## Files Created/Modified

```
src/null_system/lang/
├── __init__.py              # Public API exports (updated for annotations)
├── ast_nodes.py             # 225 lines - AST definitions (added annotation nodes)
├── compiler.py              # 280 lines NEW - Null-Lang to Super-Bit IR compiler
├── errors.py                # 64 lines - Error classes
├── grammar.lark             # 175 lines - Language grammar (added layer annotation rules)
└── parser.py                # 420+ lines - Parser implementation (added annotation handling)

src/null_system/superbit/
└── ir.py                    # Updated docstring with metadata contract

tests/lang/
├── __init__.py
├── test_parser.py           # 541 lines - 75 comprehensive tests
└── test_annotations.py      # 400+ lines NEW - 32 comprehensive layer annotation tests

fixtures/lang/
├── collections.null         # Array and object examples
├── complete_program.null    # Complex multi-feature program
├── control_flow.null        # IF and REPEAT examples
├── expressions.null         # Expression examples
├── functions.null           # Function definition examples
├── null_lib_annotations.null # Null-Lib annotation examples
└── simple_statements.null   # Basic statement examples

requirements.txt             # Dependencies
setup.py                     # Package configuration
README.md                    # Documentation
IMPLEMENTATION.md            # Updated with annotation features
example.py                   # Usage examples
.gitignore                   # Git ignore rules
```

## Dependencies

- **lark-parser** (>=0.12.0): Parser generator
- **pytest** (>=7.0.0): Testing framework

## Future Enhancements

Potential areas for extension:
1. Semantic analysis phase
2. Type checking
3. Code generation/interpretation
4. Additional operators or constructs
5. Standard library integration
6. REPL implementation
7. Syntax highlighting support
8. LSP (Language Server Protocol) implementation
