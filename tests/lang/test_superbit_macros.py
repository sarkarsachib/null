"""
Unit tests for Super-Bit specific syntax: literals, macros, and pattern matching.

Tests cover parsing and compilation of:
- Super-bit literals (0x@NAME, 0b@NAME)
- Macro invocations (@encode, @compress, @encrypt, @quantize)
- Pattern matching (MATCH with @pattern)
"""

import pytest
from src.null_system.lang import (
    parse, parse_statement, compile_program,
    SuperBitLiteral, MacroInvocation, SuperBitPattern, PatternArm, MatchCommand,
    SetCommand, ShowCommand, Identifier, NumLiteral, TextLiteral,
    SyntaxError
)
from src.null_system.superbit.ir import SuperBitOpCode


class TestSuperBitLiterals:
    """Test parsing of super-bit literals."""
    
    def test_hex_literal(self):
        result = parse_statement('0x@HELLO')
        assert isinstance(result, SuperBitLiteral)
        assert result.prefix == '0x'
        assert result.symbol == 'HELLO'
    
    def test_bin_literal(self):
        result = parse_statement('0b@custom_map')
        assert isinstance(result, SuperBitLiteral)
        assert result.prefix == '0b'
        assert result.symbol == 'custom_map'
    
    def test_hex_literal_in_set(self):
        result = parse_statement('SET x TO 0x@DATA')
        assert isinstance(result, SetCommand)
        assert isinstance(result.value, SuperBitLiteral)
        assert result.value.symbol == 'DATA'
    
    def test_bin_literal_in_show(self):
        result = parse_statement('SHOW 0b@bits')
        assert isinstance(result, ShowCommand)
        assert isinstance(result.value, SuperBitLiteral)
        assert result.value.symbol == 'bits'
    
    def test_hex_literal_with_underscore(self):
        result = parse_statement('0x@my_symbol')
        assert isinstance(result, SuperBitLiteral)
        assert result.symbol == 'my_symbol'
    
    def test_bin_literal_with_numbers(self):
        result = parse_statement('0b@symbol123')
        assert isinstance(result, SuperBitLiteral)
        assert result.symbol == 'symbol123'


class TestMacroInvocations:
    """Test parsing of macro invocations."""
    
    def test_encode_macro_no_args(self):
        result = parse_statement('@encode()')
        assert isinstance(result, MacroInvocation)
        assert result.name == 'encode'
        assert len(result.arguments) == 0
    
    def test_encode_macro_with_literal(self):
        result = parse_statement('@encode("hello")')
        assert isinstance(result, MacroInvocation)
        assert result.name == 'encode'
        assert len(result.arguments) == 1
        assert isinstance(result.arguments[0], TextLiteral)
        assert result.arguments[0].value == 'hello'
    
    def test_compress_macro(self):
        result = parse_statement('@compress(42)')
        assert isinstance(result, MacroInvocation)
        assert result.name == 'compress'
        assert len(result.arguments) == 1
        assert isinstance(result.arguments[0], NumLiteral)
        assert result.arguments[0].value == 42
    
    def test_encrypt_macro(self):
        result = parse_statement('@encrypt("secret")')
        assert isinstance(result, MacroInvocation)
        assert result.name == 'encrypt'
        assert len(result.arguments) == 1
    
    def test_quantize_macro(self):
        result = parse_statement('@quantize(3.14)')
        assert isinstance(result, MacroInvocation)
        assert result.name == 'quantize'
        assert len(result.arguments) == 1
        assert isinstance(result.arguments[0], NumLiteral)
    
    def test_macro_multiple_args(self):
        result = parse_statement('@encode("data", 42, TRUE)')
        assert isinstance(result, MacroInvocation)
        assert result.name == 'encode'
        assert len(result.arguments) == 3
    
    def test_macro_in_set(self):
        result = parse_statement('SET result TO @encode("test")')
        assert isinstance(result, SetCommand)
        assert isinstance(result.value, MacroInvocation)
        assert result.value.name == 'encode'
    
    def test_macro_in_show(self):
        result = parse_statement('SHOW @compress(data)')
        assert isinstance(result, ShowCommand)
        assert isinstance(result.value, MacroInvocation)
        assert result.value.name == 'compress'


class TestPatternMatching:
    """Test parsing of pattern matching constructs."""
    
    def test_simple_match_with_literal(self):
        source = '''
MATCH x {
    42 => { SHOW "found" }
}
'''
        result = parse(source)
        assert len(result.statements) == 1
        match_stmt = result.statements[0]
        assert isinstance(match_stmt, MatchCommand)
        assert isinstance(match_stmt.value, Identifier)
        assert match_stmt.value.name == 'x'
        assert len(match_stmt.arms) == 1
        assert isinstance(match_stmt.arms[0].pattern, NumLiteral)
    
    def test_match_with_identifier_pattern(self):
        source = '''
MATCH value {
    result => { SHOW result }
}
'''
        result = parse(source)
        match_stmt = result.statements[0]
        assert isinstance(match_stmt, MatchCommand)
        assert len(match_stmt.arms) == 1
        assert isinstance(match_stmt.arms[0].pattern, Identifier)
        assert match_stmt.arms[0].pattern.name == 'result'
    
    def test_match_with_superbit_pattern(self):
        source = '''
MATCH value {
    @pattern(letters) => { SHOW "letters" }
}
'''
        result = parse(source)
        match_stmt = result.statements[0]
        assert isinstance(match_stmt, MatchCommand)
        assert len(match_stmt.arms) == 1
        arm = match_stmt.arms[0]
        assert isinstance(arm.pattern, SuperBitPattern)
        assert arm.pattern.pattern_type == 'letters'
        assert arm.pattern.binding is None
    
    def test_match_with_superbit_pattern_binding(self):
        source = '''
MATCH value {
    @pattern(numbers) AS n => { SHOW n }
}
'''
        result = parse(source)
        match_stmt = result.statements[0]
        arm = match_stmt.arms[0]
        assert isinstance(arm.pattern, SuperBitPattern)
        assert arm.pattern.pattern_type == 'numbers'
        assert arm.pattern.binding == 'n'
    
    def test_match_multiple_arms(self):
        source = '''
MATCH value {
    @pattern(letters) => { SHOW "letters" }
    @pattern(numbers) => { SHOW "numbers" }
    default => { SHOW "other" }
}
'''
        result = parse(source)
        match_stmt = result.statements[0]
        assert isinstance(match_stmt, MatchCommand)
        assert len(match_stmt.arms) == 3
        assert isinstance(match_stmt.arms[0].pattern, SuperBitPattern)
        assert isinstance(match_stmt.arms[1].pattern, SuperBitPattern)
        assert isinstance(match_stmt.arms[2].pattern, Identifier)
    
    def test_match_with_multiple_statements_in_arm(self):
        source = '''
MATCH x {
    42 => {
        SET result TO "found"
        SHOW result
    }
}
'''
        result = parse(source)
        match_stmt = result.statements[0]
        arm = match_stmt.arms[0]
        assert len(arm.body) == 2
        assert isinstance(arm.body[0], SetCommand)
        assert isinstance(arm.body[1], ShowCommand)


class TestCompilation:
    """Test compilation of super-bit constructs to IR."""
    
    def test_compile_superbit_literal_hex(self):
        source = 'SET x TO 0x@SET'
        stream = compile_program(source)
        assert len(stream.tokens) > 0
        load_superbit_tokens = [t for t in stream.tokens if t.opcode == SuperBitOpCode.LOAD_SUPERBIT]
        assert len(load_superbit_tokens) > 0
        token = load_superbit_tokens[0]
        assert 'superbit_symbol' in token.metadata
        assert token.metadata['superbit_symbol'] == 'SET'
    
    def test_compile_encode_macro(self):
        source = 'SET result TO @encode("data")'
        stream = compile_program(source)
        encode_tokens = [t for t in stream.tokens if t.opcode == SuperBitOpCode.ENCODE_VALUE]
        assert len(encode_tokens) == 1
        token = encode_tokens[0]
        assert 'macro' in token.metadata
        assert token.metadata['macro'] == 'encode'
    
    def test_compile_compress_macro(self):
        source = '@compress(42)'
        stream = compile_program(source)
        compress_tokens = [t for t in stream.tokens if t.opcode == SuperBitOpCode.COMPRESS_VALUE]
        assert len(compress_tokens) == 1
        token = compress_tokens[0]
        assert token.metadata['macro'] == 'compress'
    
    def test_compile_encrypt_macro(self):
        source = '@encrypt("secret")'
        stream = compile_program(source)
        encrypt_tokens = [t for t in stream.tokens if t.opcode == SuperBitOpCode.ENCRYPT_VALUE]
        assert len(encrypt_tokens) == 1
    
    def test_compile_quantize_macro(self):
        source = '@quantize(3.14)'
        stream = compile_program(source)
        quantize_tokens = [t for t in stream.tokens if t.opcode == SuperBitOpCode.QUANTIZE_VALUE]
        assert len(quantize_tokens) == 1
    
    def test_compile_match_with_pattern(self):
        source = '''
MATCH x {
    @pattern(letters) => { SHOW "letters" }
}
'''
        stream = compile_program(source)
        pattern_tokens = [t for t in stream.tokens if t.opcode == SuperBitOpCode.MATCH_PATTERN]
        assert len(pattern_tokens) == 1
        token = pattern_tokens[0]
        assert 'pattern_type' in token.metadata
        assert token.metadata['pattern_type'] == 'letters'
    
    def test_compile_match_multiple_arms(self):
        source = '''
MATCH value {
    @pattern(letters) => { SHOW "a" }
    @pattern(numbers) => { SHOW "b" }
}
'''
        stream = compile_program(source)
        pattern_tokens = [t for t in stream.tokens if t.opcode == SuperBitOpCode.MATCH_PATTERN]
        assert len(pattern_tokens) == 2


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_nested_macro_calls(self):
        source = '@encode(@compress("data"))'
        result = parse_statement(source)
        assert isinstance(result, MacroInvocation)
        assert result.name == 'encode'
        assert isinstance(result.arguments[0], MacroInvocation)
        assert result.arguments[0].name == 'compress'
    
    def test_superbit_literal_with_macro(self):
        source = 'SET x TO @encode(0x@DATA)'
        result = parse_statement(source)
        assert isinstance(result, SetCommand)
        assert isinstance(result.value, MacroInvocation)
        assert isinstance(result.value.arguments[0], SuperBitLiteral)
    
    def test_match_with_annotations(self):
        source = '''
@layer(superbit)
MATCH value {
    @pattern(test) => { SHOW "ok" }
}
'''
        result = parse(source)
        match_stmt = result.statements[0]
        assert isinstance(match_stmt, MatchCommand)
        assert len(match_stmt.annotations) > 0


class TestIntegration:
    """Integration tests combining multiple features."""
    
    def test_full_program_with_superbit_features(self):
        source = '''
SET data TO 0x@SET
SET encoded TO @encode(data)
SET compressed TO @compress(encoded)

MATCH compressed {
    @pattern(small) AS s => { SHOW "Small data" }
    @pattern(large) AS l => { SHOW "Large data" }
    default => { SHOW "Unknown" }
}
'''
        program = parse(source)
        assert len(program.statements) == 4
        
        stream = compile_program(source)
        assert any(t.opcode == SuperBitOpCode.LOAD_SUPERBIT for t in stream.tokens)
        assert any(t.opcode == SuperBitOpCode.ENCODE_VALUE for t in stream.tokens)
        assert any(t.opcode == SuperBitOpCode.COMPRESS_VALUE for t in stream.tokens)
        assert any(t.opcode == SuperBitOpCode.MATCH_PATTERN for t in stream.tokens)
    
    def test_macro_with_multiple_superbit_literals(self):
        source = '@encode(0x@A, 0b@B, 0x@C)'
        result = parse_statement(source)
        assert isinstance(result, MacroInvocation)
        assert len(result.arguments) == 3
        assert all(isinstance(arg, SuperBitLiteral) for arg in result.arguments)
    
    def test_complex_match_expression(self):
        source = '''
MATCH @compress(value) {
    @pattern(compressed) AS c => {
        SET result TO c
        SHOW result
    }
    fallback => {
        SHOW "No match"
    }
}
'''
        program = parse(source)
        match_stmt = program.statements[0]
        assert isinstance(match_stmt, MatchCommand)
        assert isinstance(match_stmt.value, MacroInvocation)
        assert len(match_stmt.arms) == 2
