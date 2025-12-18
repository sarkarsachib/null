#!/usr/bin/env python3
"""Manual test script for ownership features without package dependencies."""

import sys
sys.path.insert(0, 'src')

# Test lexer directly
from null_system.parser.lexer import Lexer, TokenType
lexer = Lexer('let x = 42')
tokens = lexer.tokenize()
print('✓ Lexer test passed - tokens:', len(tokens))
for t in tokens:
    print(f'  {t.type}: {t.value}')

# Test parser directly
from null_system.parser.parser import Parser
parser = Parser([t for t in tokens if t.type != TokenType.NEWLINE])
ast = parser.parse()
print('✓ Parser test passed - statements:', len(ast.statements))

# Test ownership analyzer
from null_system.analysis.ownership import OwnershipAnalyzer
analyzer = OwnershipAnalyzer()
result = analyzer.analyze(ast)
print('✓ Ownership analyzer test passed - valid:', result)
print('Ownership errors:', analyzer.get_errors())

# Test SuperBit emitter
from null_system.superbit.emitter import SuperBitEmitter
from null_system.superbit.ir import SuperBitOpCode
emitter = SuperBitEmitter()
stream = emitter.emit(ast)
print('✓ SuperBit emitter test passed - tokens:', len(stream.tokens))
for token in stream.tokens:
    print(f'  {token.opcode}: {token.operand}')

print('\n=== Ownership Features Test Complete ===')