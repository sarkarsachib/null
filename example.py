#!/usr/bin/env python3
"""
Example usage of the Null-Lang parser.
"""

from src.null_system.lang import parse, SyntaxError

# Example 1: Simple statement
print("Example 1: Simple SET statement")
print("-" * 40)
source1 = 'SET x TO 42'
ast1 = parse(source1)
print(f"Source: {source1}")
print(f"AST: {ast1}")
print(f"Statement type: {type(ast1.statements[0]).__name__}")
print()

# Example 2: Control flow
print("Example 2: IF statement")
print("-" * 40)
source2 = """
IF x IS GREATER THAN 10 THEN
    SHOW "Large"
ELSE
    SHOW "Small"
END IF
"""
ast2 = parse(source2)
print(f"Source: {source2.strip()}")
print(f"Number of statements: {len(ast2.statements)}")
print(f"Statement type: {type(ast2.statements[0]).__name__}")
print()

# Example 3: Function definition
print("Example 3: Function definition")
print("-" * 40)
source3 = """
DEFINE greet WITH name
    SHOW "Hello"
    SHOW name
END DEFINE
"""
ast3 = parse(source3)
func_def = ast3.statements[0]
print(f"Function name: {func_def.name}")
print(f"Parameters: {func_def.parameters}")
print(f"Body statements: {len(func_def.body)}")
print()

# Example 4: Collections
print("Example 4: Collections")
print("-" * 40)
source4 = """
SET numbers TO [1, 2, 3]
SET person TO { name: "Alice", age: 30 }
"""
ast4 = parse(source4)
print(f"Number of statements: {len(ast4.statements)}")
print(f"First statement assigns: {type(ast4.statements[0].value).__name__}")
print(f"Second statement assigns: {type(ast4.statements[1].value).__name__}")
print()

# Example 5: Error handling
print("Example 5: Error handling")
print("-" * 40)
try:
    bad_source = "SET x TO"
    parse(bad_source)
except SyntaxError as e:
    print(f"Caught syntax error:")
    print(str(e))
print()

print("All examples completed successfully!")
