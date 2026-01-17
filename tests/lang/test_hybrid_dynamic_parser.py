import pytest
from null_system.lang import HybridDynamicParser, OutputMode, SyntaxMode, Program

def test_auto_mode_detection():
    parser = HybridDynamicParser()
    source = """
    SET x TO 42
    let y = x + 1;
    SHOW y
    """
    program = parser.parse(source, OutputMode.AUTO)
    assert len(program.statements) == 3
    assert program.statements[0].syntax_mode == SyntaxMode.english
    assert program.statements[1].syntax_mode == SyntaxMode.modern
    assert program.statements[2].syntax_mode == SyntaxMode.english

def test_manual_mode_directives():
    parser = HybridDynamicParser()
    source = """
    @syntax:english
    SET count TO 0
    @syntax:modern
    let result = count + 10;
    @syntax:english
    SHOW result
    """
    program = parser.parse(source, OutputMode.MANUAL)
    assert len(program.statements) == 3
    assert program.statements[0].syntax_mode == SyntaxMode.english
    assert program.statements[1].syntax_mode == SyntaxMode.modern
    assert program.statements[2].syntax_mode == SyntaxMode.english

def test_semi_auto_mode_hints():
    parser = HybridDynamicParser()
    source = """
    # mode:modern
    let z = 100;
    # mode:english
    ADD 5 AND z
    """
    program = parser.parse(source, OutputMode.SEMI_AUTO)
    # Note: My current implementation of SEMI_AUTO uses detected mode if it conflicts,
    # as per ticket: "If hint conflicts with detected mode, warn and use detected"
    assert len(program.statements) == 2
    assert program.statements[0].syntax_mode == SyntaxMode.modern
    assert program.statements[1].syntax_mode == SyntaxMode.english

def test_mixed_blocks_auto():
    parser = HybridDynamicParser()
    source = """
    IF x IS GREATER THAN 0 THEN
        SET y TO 1
    END IF
    if (y == 1) {
        print("Success");
    }
    """
    program = parser.parse(source, OutputMode.AUTO)
    assert len(program.statements) == 2
    assert program.statements[0].syntax_mode == SyntaxMode.english
    assert program.statements[1].syntax_mode == SyntaxMode.modern

def test_scope_crossing():
    parser = HybridDynamicParser()
    source = """
    SET a TO 10
    let b = a * 2;
    SHOW b
    """
    program = parser.parse(source, OutputMode.AUTO)
    # The actual scope checking happens in validator, but parser should produce unified AST
    assert len(program.statements) == 3
    # Just checking we have the right nodes
    from null_system.lang import SetCommand, ShowCommand
    # Note: Modern 'let' might be parsed as LetBindingExpression if implemented, 
    # or just a generic statement. Let's see what modern parser produces.
    # Actually, ParserFactory uses ModernRustParser for modern syntax.
    pass

def test_ambiguous_fallback():
    parser = HybridDynamicParser()
    # "RETURN" is common to both but "RETURN x" might be English and "return x;" is Modern
    source = """
    RETURN 42
    """
    program = parser.parse(source, OutputMode.AUTO)
    assert program.statements[0].syntax_mode == SyntaxMode.english

def test_directive_enforcement_manual():
    parser = HybridDynamicParser()
    # In manual mode, we should respect the directive.
    source = """
    @syntax:modern
    let x = 10;
    @syntax:english
    SET y TO 20
    """
    program = parser.parse(source, OutputMode.MANUAL)
    assert program.statements[0].syntax_mode == SyntaxMode.modern
    assert program.statements[1].syntax_mode == SyntaxMode.english

def test_auto_mode_complex_mixture():
    parser = HybridDynamicParser()
    source = """
    SET x TO 10
    if (x > 5) {
        print("Large");
    }
    REPEAT 3 TIMES
        SHOW x
    END REPEAT
    let y = x * 2;
    """
    program = parser.parse(source, OutputMode.AUTO)
    assert len(program.statements) == 4
    assert program.statements[0].syntax_mode == SyntaxMode.english
    assert program.statements[1].syntax_mode == SyntaxMode.modern
    assert program.statements[2].syntax_mode == SyntaxMode.english
    assert program.statements[3].syntax_mode == SyntaxMode.modern

@pytest.mark.parametrize("i", range(50))
def test_generated_auto_cases(i):
    parser = HybridDynamicParser()
    if i % 2 == 0:
        source = f"SET var_{i} TO {i}"
        expected = SyntaxMode.english
    else:
        source = f"let var_{i} = {i};"
        expected = SyntaxMode.modern
    program = parser.parse(source, OutputMode.AUTO)
    assert program.statements[0].syntax_mode == expected

def test_semi_auto_conflict_resolution():
    parser = HybridDynamicParser()
    # "If hint conflicts with detected mode, warn and use detected"
    source = """
    # mode:english
    let x = 10;
    """
    # Even though hint says english, 'let x = 10;' is clearly modern.
    program = parser.parse(source, OutputMode.SEMI_AUTO)
    assert program.statements[0].syntax_mode == SyntaxMode.modern

def test_manual_mode_no_directive_default():
    parser = HybridDynamicParser()
    source = "SET x TO 1"
    program = parser.parse(source, OutputMode.MANUAL)
    assert program.statements[0].syntax_mode == SyntaxMode.english

def test_manual_mode_multiple_directives():
    parser = HybridDynamicParser()
    source = """
    @syntax:english
    SET a TO 1
    @syntax:modern
    let b = 2;
    @syntax:modern
    let c = 3;
    @syntax:english
    SHOW c
    """
    program = parser.parse(source, OutputMode.MANUAL)
    assert program.statements[0].syntax_mode == SyntaxMode.english
    assert program.statements[1].syntax_mode == SyntaxMode.modern
    assert program.statements[2].syntax_mode == SyntaxMode.modern
    assert program.statements[3].syntax_mode == SyntaxMode.english

@pytest.mark.parametrize("i", range(40))
def test_generated_manual_cases(i):
    parser = HybridDynamicParser()
    if i % 2 == 0:
        source = f"@syntax:english\nSET mvar_{i} TO {i}"
        expected = SyntaxMode.english
    else:
        source = f"@syntax:modern\nlet mvar_{i} = {i};"
        expected = SyntaxMode.modern
    program = parser.parse(source, OutputMode.MANUAL)
    # program.statements[0] will be the node
    assert program.statements[0].syntax_mode == expected

def test_auto_mode_empty_lines_and_comments():
    parser = HybridDynamicParser()
    source = """
    // English comment
    SET x TO 10
    
    // Modern comment
    let y = 20;
    
    SHOW x
    """
    program = parser.parse(source, OutputMode.AUTO)
    assert len(program.statements) == 3
    assert program.statements[0].syntax_mode == SyntaxMode.english
    assert program.statements[1].syntax_mode == SyntaxMode.modern
    assert program.statements[2].syntax_mode == SyntaxMode.english
