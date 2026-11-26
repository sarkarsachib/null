"""Tests for the first self-hosted Null compiler stage (bootstrap/nullc.null)."""

from pathlib import Path

from null_system.lang.compiler import NullLangCompiler
from null_system.lang.modern.modern_rust import ModernRustParser
from null_system.vm.vm import NullVM

ROOT = Path(__file__).resolve().parents[2]

EXPECTED = [
    "KEYWORD fn",
    "IDENT add",
    "PUNCT (",
    "IDENT a",
    "PUNCT :",
    "IDENT Num",
    "PUNCT ,",
    "IDENT b",
    "PUNCT :",
    "IDENT Num",
    "PUNCT )",
    "PUNCT ->",
    "IDENT Num",
    "PUNCT {",
    "KEYWORD return",
    "IDENT a",
    "PUNCT +",
    "IDENT b",
    "PUNCT ;",
    "PUNCT }",
    "KEYWORD let",
    "IDENT total",
    "PUNCT =",
    "IDENT add",
    "PUNCT (",
    "NUMBER 2",
    "PUNCT ,",
    "NUMBER 3",
    "PUNCT )",
    "PUNCT ;",
    "KEYWORD println",
    "PUNCT (",
    "IDENT total",
    "PUNCT )",
    "PUNCT ;",
    "KEYWORD let",
    "IDENT label",
    "PUNCT =",
    "STRING null",
    "PUNCT ;",
    "KEYWORD SET",
    "IDENT legacy",
    "KEYWORD TO",
    "NUMBER 7",
]


def test_self_hosted_lexer_tokenizes_dual_syntax_sample(monkeypatch):
    monkeypatch.chdir(ROOT)
    source = (ROOT / "bootstrap" / "nullc.null").read_text()
    ast = ModernRustParser().parse(source)
    stream = NullLangCompiler().compile(ast)
    result = NullVM().execute(stream)

    assert result.success, result.error
    assert result.output == EXPECTED
