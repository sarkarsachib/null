import pytest
from null_system.lang import HybridDynamicParser, OutputMode, SyntaxMode, NullLangCompiler

def test_compiler_ir_metadata():
    parser = HybridDynamicParser()
    compiler = NullLangCompiler()
    
    source = """
    SET x TO 42
    let y = 10;
    """
    program = parser.parse(source, OutputMode.AUTO)
    ir_stream = compiler.compile(program)
    
    # Check that tokens have syntax_mode metadata
    tokens = ir_stream.tokens
    assert len(tokens) > 0
    
    # First tokens should be English (from SET x TO 42)
    # NumLiteral 42 -> STORE_VAR x
    assert tokens[0].metadata.get("syntax_mode") == "english"
    
    # Later tokens should be Modern (from let y = 10;)
    # Depending on how 'let' is compiled.
    # Let's find a token that we know comes from the second statement.
    modern_tokens = [t for t in tokens if t.metadata.get("syntax_mode") == "modern"]
    assert len(modern_tokens) > 0

def test_compiler_continuous_stream():
    parser = HybridDynamicParser()
    compiler = NullLangCompiler()
    
    source = """
    SET a TO 1
    let b = 2;
    SHOW a
    """
    program = parser.parse(source, OutputMode.AUTO)
    ir_stream = compiler.compile(program)
    
    # Stream should be continuous
    assert len(ir_stream.tokens) >= 5 # 2 for SET, 2 for let, 1 for SHOW approx
    modes = [t.metadata.get("syntax_mode") for t in ir_stream.tokens]
    assert "english" in modes
    assert "modern" in modes
