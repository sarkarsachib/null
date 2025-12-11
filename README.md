# Null-Lang Parser

An English-like programming language parser built with Lark.

## Overview

Null-Lang is a simple, readable programming language with English-like syntax. This parser provides lexing, parsing, and AST construction capabilities.

## Features

- **Commands**: SET, ADD, IF, SHOW, REPEAT, DEFINE
- **Literals**: TEXT (strings), NUM (numbers), BOOL (true/false)
- **Collections**: ARRAY, OBJECT
- **Operators**: Arithmetic (PLUS, MINUS, TIMES, DIVIDED BY), Comparisons (IS, IS GREATER THAN, etc.), Logical (AND, OR, NOT)
- **Control Flow**: IF-THEN-ELSE, REPEAT loops
- **Functions**: DEFINE functions with parameters, CALL functions
- **Member Access**: Property access (obj.prop) and indexing (array[0])
- **Null-Lib Annotations**: Inline library calls with @lib.function syntax
- **Detailed Error Reporting**: Syntax and semantic errors with source location information

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Parse a Program

```python
from src.null_system.lang import parse

source = """
SET x TO 42
SHOW x
"""

ast = parse(source)
```

### Parse a Single Statement

```python
from src.null_system.lang import parse_statement

statement = parse_statement('SET x TO 10')
```

### Error Handling

```python
from src.null_system.lang import parse, SyntaxError

try:
    ast = parse('SET x TO')
except SyntaxError as e:
    print(f"Parse error: {e}")
    print(f"Location: Line {e.span.start_line}, Column {e.span.start_col}")
```

## Language Syntax Examples

### Variable Assignment
```null
SET x TO 42
SET name TO "Alice"
SET active TO TRUE
```

### Arithmetic
```null
SET result TO 10 PLUS 5
SET result TO 20 MINUS 7
SET result TO 4 TIMES 3
SET result TO 15 DIVIDED BY 3
```

### Collections
```null
SET numbers TO [1, 2, 3, 4, 5]
SET person TO { name: "Alice", age: 30 }
SHOW person.name
SHOW numbers[0]
```

### Control Flow
```null
IF x IS GREATER THAN 10 THEN
    SHOW "x is large"
ELSE
    SHOW "x is small"
END IF

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

## Testing

Run the test suite:

```bash
pytest tests/
```

Run tests with verbose output:

```bash
pytest tests/ -v
```

## Project Structure

```
src/null_system/lang/
├── __init__.py           # Module exports
├── ast_nodes.py          # AST node definitions
├── errors.py             # Error classes with detailed reporting
├── grammar.lark          # Lark grammar definition
└── parser.py             # Parser implementation

tests/lang/
└── test_parser.py        # Comprehensive parser tests

fixtures/lang/
├── simple_statements.null      # Basic statement examples
├── control_flow.null           # IF and REPEAT examples
├── functions.null              # Function definition examples
├── collections.null            # Array and object examples
├── expressions.null            # Expression examples
├── null_lib_annotations.null   # Null-Lib annotation examples
└── complete_program.null       # Complete program example
```

## AST Structure

The parser produces a typed AST with the following node types:

- **Program**: Top-level node containing all statements
- **Literals**: TextLiteral, NumLiteral, BoolLiteral, ArrayLiteral, ObjectLiteral
- **Commands**: SetCommand, AddCommand, IfCommand, ShowCommand, RepeatCommand, DefineCommand
- **Expressions**: BinaryExpression, UnaryExpression, ComparisonExpression
- **Other**: Identifier, MemberAccess, FunctionCall, NullLibAnnotation, Comment

Each AST node includes a `span` attribute with source location information for error reporting.

## License

MIT
