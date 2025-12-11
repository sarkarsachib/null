# Null-Lang Parser Implementation

## Summary

This implementation provides a complete English-like programming language parser for Null-Lang, built using the Lark parsing library.

## Components Implemented

### 1. **AST Node Definitions** (`src/null_system/lang/ast_nodes.py`)
- Base `ASTNode` class with source span tracking
- **Literal nodes**: TextLiteral, NumLiteral, BoolLiteral, ArrayLiteral, ObjectLiteral
- **Command nodes**: SetCommand, AddCommand, IfCommand, ShowCommand, RepeatCommand, DefineCommand
- **Expression nodes**: BinaryExpression, UnaryExpression, ComparisonExpression
- **Other nodes**: Identifier, MemberAccess, FunctionCall, NullLibAnnotation, Program, Comment
- **Source tracking**: SourceSpan class for error reporting with line/column information

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
  - Null-Lib annotations: @lib.function(args)
  - Comments: hash-style (#)

### 3. **Parser Implementation** (`src/null_system/lang/parser.py`)
- `NullLangTransformer`: Lark transformer that converts parse tree to AST
- `NullLangParser`: Main parser class
- Convenience functions: `parse()`, `parse_statement()`
- Comprehensive span tracking for all nodes
- Detailed error handling

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

### 6. **Unit Tests** (`tests/lang/test_parser.py`)
75 comprehensive tests organized into 10 test classes:
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

All tests cover:
- ✅ Happy paths (correct syntax)
- ✅ Malformed input diagnostics
- ✅ Error message quality
- ✅ Source span accuracy

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
# Run all tests
pytest tests/lang/test_parser.py -v

# Run with coverage
pytest tests/lang/test_parser.py --cov=src/null_system/lang

# Run specific test class
pytest tests/lang/test_parser.py::TestLiterals -v
```

## Files Created

```
src/null_system/lang/
├── __init__.py              # Public API exports
├── ast_nodes.py             # 205 lines - AST definitions
├── errors.py                # 64 lines - Error classes
├── grammar.lark             # 142 lines - Language grammar
└── parser.py                # 376 lines - Parser implementation

tests/lang/
├── __init__.py
└── test_parser.py           # 541 lines - 75 comprehensive tests

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
