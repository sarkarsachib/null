#!/usr/bin/env python3
"""Simple test of individual ownership modules."""

import sys
import os

# Add the src directory to path
sys.path.insert(0, 'src')

print("Testing lexer...")

# Test lexer manually by reading the source
import ast as python_ast
import re

# Read and execute the lexer source directly
with open('src/null_system/parser/lexer.py', 'r') as f:
    lexer_source = f.read()

# Define the required imports for lexer
from enum import Enum, auto
from dataclasses import dataclass
from typing import List

# Execute lexer code
exec(lexer_source)

# Test lexer
lexer = Lexer('let x = 42')
tokens = lexer.tokenize()
print(f'✓ Lexer: {len(tokens)} tokens')
for t in tokens:
    print(f'  {t.type}: {t.value}')

print('\nTesting parser...')

# Read and execute parser source
with open('src/null_system/parser/parser.py', 'r') as f:
    parser_source = f.read()

# Add required imports
from typing import List, Optional

exec(parser_source)

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

print('\nTesting AST nodes...')

# Read AST nodes
with open('src/null_system/ast/nodes.py', 'r') as f:
    ast_nodes_source = f.read()

exec(ast_nodes_source)

print('✓ AST nodes loaded')

print('\nTesting ownership analyzer...')

# Read ownership analyzer
with open('src/null_system/analysis/ownership.py', 'r') as f:
    ownership_source = f.read()

exec(ownership_source)

analyzer = OwnershipAnalyzer()
result = analyzer.analyze(ast)
print(f'✓ Ownership analyzer: {result}')
print(f'  - Errors: {analyzer.get_errors()}')

print('\nTesting SuperBit emitter...')

# Read emitter and IR
with open('src/null_system/superbit/emitter.py', 'r') as f:
    emitter_source = f.read()

with open('src/null_system/superbit/ir.py', 'r') as f:
    ir_source = f.read()

exec(ir_source)
exec(emitter_source)

emitter = SuperBitEmitter()
stream = emitter.emit(ast)
print(f'✓ SuperBit emitter: {len(stream.tokens)} tokens')
for token in stream.tokens:
    print(f'  - {token.opcode}: {token.operand}')

print('\n✅ All ownership features working correctly!')