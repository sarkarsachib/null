import pytest

from src.null_system.lang.advisor import DiagnosticLevel, SyntaxConfig, SyntaxMode
from src.null_system.lang.hybrid_parser import HybridParser
from src.null_system.parser.parser import ParseError
from src.null_system.ast.nodes import PrintStatement, Program, SetStatement


HYBRID_SOURCE_WITH_DIRECTIVE = """@syntax hybrid
SET x TO 5
let y = 10;
SHOW x
print(y);
"""


def test_hybrid_sample_parses_with_syntax_directive() -> None:
    parser = HybridParser()
    result = parser.parse(HYBRID_SOURCE_WITH_DIRECTIVE)

    assert isinstance(result.ast, Program)
    assert len(result.ast.statements) == 4
    assert isinstance(result.ast.statements[0], SetStatement)
    assert isinstance(result.ast.statements[1], SetStatement)
    assert isinstance(result.ast.statements[2], PrintStatement)
    assert isinstance(result.ast.statements[3], PrintStatement)

    stmt0 = result.ast.statements[0]
    stmt1 = result.ast.statements[1]

    assert getattr(stmt0, "syntax_segment").mode == SyntaxMode.english
    assert getattr(stmt1, "syntax_segment").mode == SyntaxMode.modern


def test_mixing_without_permission_emits_error_diagnostic() -> None:
    source = "SET x TO 5\nlet y = 10;\n"
    parser = HybridParser()

    mode, diags = parser.check(source, config=SyntaxConfig(allow_hybrid_mode=False, mode=SyntaxMode.auto))
    assert mode == SyntaxMode.hybrid
    assert any(d.level == DiagnosticLevel.error and "Hybrid syntax is disabled" in d.message for d in diags)

    with pytest.raises(ParseError):
        parser.parse(source, config=SyntaxConfig(allow_hybrid_mode=False, mode=SyntaxMode.auto))


def test_hints_include_feature3_wording() -> None:
    source = "SET x TO 5\nlet y = 10;\nSHOW x\n"
    parser = HybridParser()

    _mode, diags = parser.check(source, config=SyntaxConfig(allow_hybrid_mode=True, mode=SyntaxMode.auto))
    hints = [d.message for d in diags if d.level == DiagnosticLevel.hint]

    assert "Mixed English and modern syntax detected. Add '@syntax hybrid' to make this explicit." in hints
    assert "In modern syntax, prefer 'let' over 'SET' for variable declarations." in hints
