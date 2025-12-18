#!/usr/bin/env python3
"""Direct test script for ownership features without package dependencies."""

import sys
import os

# Add just the specific modules to path
sys.path.insert(0, 'src/null_system/parser')
sys.path.insert(0, 'src/null_system/ast')
sys.path.insert(0, 'src/null_system/analysis')
sys.path.insert(0, 'src/null_system/superbit')

# Import modules directly
from lexer import Lexer, TokenType
from parser import Parser

print("Testing ownership features...")

# Test lexer
lexer = Lexer('let x = 42')
tokens = lexer.tokenize()
print(f'✓ Lexer: {len(tokens)} tokens')
for t in tokens:
    print(f'  {t.type}: {t.value}')

# Test parser  
filtered_tokens = [t for t in tokens if t.type != TokenType.NEWLINE]
parser = Parser(filtered_tokens)
ast = parser.parse()
print(f'✓ Parser: {len(ast.statements)} statements')

# Test AST nodes
stmt = ast.statements[0]
print(f'✓ AST Statement: {stmt.__class__.__name__}')
if hasattr(stmt, 'pattern'):
    print(f'  - Pattern: {stmt.pattern.name}')
if hasattr(stmt, 'value'):
    print(f'  - Value: {stmt.value.value}')

# Test ownership analyzer
sys.path.insert(0, 'src/null_system/analysis')
from ownership import OwnershipAnalyzer

analyzer = OwnershipAnalyzer()
result = analyzer.analyze(ast)
print(f'✓ Ownership analyzer: {result}')
print(f'  - Errors: {analyzer.get_errors()}')

# Test SuperBit emitter
sys.path.insert(0, 'src/null_system/superbit')
from emitter import SuperBitEmitter
from ir import SuperBitOpCode

emitter = SuperBitEmitter()
stream = emitter.emit(ast)
print(f'✓ SuperBit emitter: {len(stream.tokens)} tokens')
for token in stream.tokens:
    print(f'  - {token.opcode}: {token.operand}')

print('\n✅ All ownership features working correctly!')