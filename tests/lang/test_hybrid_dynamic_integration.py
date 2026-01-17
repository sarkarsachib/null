import pytest
from null_system.lang import HybridDynamicParser, OutputMode, NullLangCompiler
from null_system.ast.validator import ASTValidator

def test_full_hybrid_program_integration():
    source = """
    SET count TO 10
    
    # mode:modern
    let total = 0;
    for i in [1, 2, 3] {
        total = total + i;
    }
    
    # mode:english
    IF total IS GREATER THAN 5 THEN
        SHOW total
    END IF
    
    @syntax:modern
    print("Program finished");
    """
    
    parser = HybridDynamicParser()
    validator = ASTValidator()
    compiler = NullLangCompiler()
    
    # 1. Parsing
    program = parser.parse(source, OutputMode.AUTO)
    assert len(program.statements) == 5 # SET, let, for, IF, print
    
    # 2. Validation
    assert validator.validate(program)
    
    # 3. Compilation
    ir_stream = compiler.compile(program)
    assert len(ir_stream.tokens) > 0
    
    # Verify metadata in IR
    modes = [t.metadata.get("syntax_mode") for t in ir_stream.tokens]
    assert "english" in modes
    assert "modern" in modes

def test_manual_mode_strict_directives():
    source = """
    @syntax:english
    SET a TO 1
    @syntax:modern
    let b = 2;
    """
    parser = HybridDynamicParser()
    program = parser.parse(source, OutputMode.MANUAL)
    assert program.statements[0].syntax_mode == "english"
    assert program.statements[1].syntax_mode == "modern"
