"""Tests for the second self-hosted Null compiler stage (bootstrap/parser.null).

The parser is a dual-syntax front end: the English surface and the Modern
surface must produce one unified AST.  These tests pin the canonical outline of
a small program and then require both syntaxes of a larger program to agree.
"""

from pathlib import Path

from null_system.lang.compiler import NullLangCompiler
from null_system.lang.modern.modern_rust import ModernRustParser
from null_system.vm.vm import NullVM

ROOT = Path(__file__).resolve().parents[2]

SAMPLE_EXPECTED = [
    "PROGRAM",
    "  FN add -> Num",
    "    PARAM a",
    "    PARAM b",
    "    RETURN",
    "      BINARY + IDENT a IDENT b",
    "  LET total",
    "    CALL add(NUM 2, NUM 3)",
    "  PRINTLN",
    "    IDENT total",
    "  LET label",
    "    STR null",
    "  LET legacy",
    "    NUM 7",
]

DUAL_PROGRAM_EXPECTED = [
    "PROGRAM",
    "  MODULE demo",
    "  FN add",
    "    PARAM a",
    "    PARAM b",
    "    RETURN",
    "      BINARY + IDENT a IDENT b",
    "  LET total",
    "    CALL add(NUM 2, NUM 3)",
    "  PRINTLN",
    "    IDENT total",
    "  LET doubled",
    "    COMPREHEND BINARY * IDENT x NUM 2 FOR x IN RANGE NUM 0 NUM 3 "
    "WHERE BINARY == BINARY % IDENT x NUM 2 NUM 0",
    "  PRINTLN",
    "    IDENT doubled",
    "  IF",
    "    BINARY > IDENT total NUM 3",
    "    THEN",
    "      PRINTLN",
    "        STR big",
    "    ELSE",
    "      PRINTLN",
    "        STR small",
    "  LET config",
    "    OBJECT {name: STR null, version: NUM 2}",
    "  PRINTLN",
    "    MEMBER IDENT config.name",
    "  LET result",
    "    PIPELINE IDENT numbers |> filter(LAMBDA (x) -> BINARY > IDENT x NUM 0) "
    "|> map(LAMBDA (x) -> BINARY * IDENT x NUM 2)",
    "  PRINTLN",
    "    IDENT result",
    "  LET name",
    "    ELVIS SAFE_MEMBER IDENT user?.name STR anonymous",
    "  PRINTLN",
    "    IDENT name",
    "  MATCH",
    "    IDENT total",
    "    ARM Ok(bind value)",
    "      PRINTLN",
    "        IDENT value",
    "    ARM _",
    "      PRINTLN",
    "        STR none",
]


def _compile_parser():
    source = (ROOT / "bootstrap" / "parser.null").read_text()
    return NullLangCompiler().compile(ModernRustParser().parse(source))


def _parse_program(tmp_path, monkeypatch, program: str) -> list[str]:
    """Run bootstrap/parser.null on ``program`` staged as bootstrap/input.null."""
    stream = _compile_parser()
    workdir = tmp_path / "run"
    (workdir / "bootstrap").mkdir(parents=True)
    (workdir / "bootstrap" / "input.null").write_text(program)
    monkeypatch.chdir(workdir)
    result = NullVM().execute(stream)
    assert result.success, result.error
    return result.output


def test_self_hosted_parser_builds_ast_for_dual_syntax_sample(tmp_path, monkeypatch):
    sample = (ROOT / "bootstrap" / "input.null").read_text()

    assert _parse_program(tmp_path, monkeypatch, sample) == SAMPLE_EXPECTED


def test_english_and_modern_programs_produce_the_same_ast(tmp_path, monkeypatch):
    english = (ROOT / "bootstrap" / "dual_english.null").read_text()
    modern = (ROOT / "bootstrap" / "dual_modern.null").read_text()

    english_ast = _parse_program(tmp_path / "e", monkeypatch, english)
    modern_ast = _parse_program(tmp_path / "m", monkeypatch, modern)

    assert modern_ast == DUAL_PROGRAM_EXPECTED
    assert english_ast == modern_ast


def test_modern_forms_lower_to_the_documented_nodes(tmp_path, monkeypatch):
    program = (ROOT / "bootstrap" / "features_modern.null").read_text()

    outline = "\n".join(_parse_program(tmp_path, monkeypatch, program))

    for expected in (
        "TYPE UserId = Num",
        "DATA User",
        "SEALED Shape",
        "ASYNC FN fetch_all",
        "CONSTRUCT User {name: STR null, id: IDENT id}",
        "MEMBER NOTNULL IDENT u.name",
        "INTERP [STR user , IDENT n, STR  loaded , IDENT id]",
        "AWAIT IDENT out",
        "BORROW False IDENT value",
        "SET_OP IDENT counter +",
        "MODULE app::net",
    ):
        assert expected in outline, expected
