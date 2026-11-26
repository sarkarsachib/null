"""Tests for the fourth self-hosted stage (bootstrap/emitter.null).

The emitter lowers the unified AST to super-bit IR tokens:
["IR", opcode, operand, layer, meta?] and ["LABEL", name].
"""

import re
from pathlib import Path

from null_system.lang.compiler import NullLangCompiler
from null_system.lang.modern.modern_rust import ModernRustParser
from null_system.vm.vm import NullVM

ROOT = Path(__file__).resolve().parents[2]

SAMPLE_IR = [
    "IR 74 add @lang arity=2 params=a,b types=Num,Num ret=Num",
    "IR 2 a @scalar",
    "IR 2 b @scalar",
    "IR 10  @scalar",
    "IR 71  @scalar",
    "IR 255 end_fn @lang decl",
    "IR 1 2 @scalar",
    "IR 1 3 @scalar",
    "IR 70 add @scalar arity=2",
    "IR 3 total @scalar",
    "IR 2 total @scalar",
    "IR 30  @scalar",
    "IR 1 null @scalar str",
    "IR 3 label @scalar",
    "IR 1 7 @scalar",
    "IR 3 legacy @scalar",
    "IR 255 HALT @scalar end",
    "TOKENS 17",
]


def _compile_emitter():
    source = (ROOT / "bootstrap" / "emitter.null").read_text()
    return NullLangCompiler().compile(ModernRustParser().parse(source))


def test_break_semicolons_and_literal_braces_do_not_derail_the_parser(tmp_path, monkeypatch):
    # `break;` used to leave the `;` unconsumed, so the block's closing `}` was
    # parsed as an expression statement; and a `"{"` element in a table was read
    # as string interpolation, swallowing the rest of the file to EOF.
    program = (
        "fn f(n: Num) -> Num {\n"
        "    let i = 0;\n"
        "    while i < n {\n"
        "        if i == 2 {\n"
        "            break;\n"
        "        }\n"
        "        i = i + 1;\n"
        "    }\n"
        "    return i;\n"
        "}\n"
        'let puncts = ["(", ")", "[", "]", "{", "}", ",", ";"];\n'
        "println(f(9));\n"
    )
    lines = _emit(tmp_path, monkeypatch, program)

    assert not [line for line in lines if "unsupported:" in line]
    assert "IR 1 { @scalar str" in lines
    assert "IR 72  @scalar arity=8" in lines


def _emit(tmp_path, monkeypatch, program: str) -> list[str]:
    stream = _compile_emitter()
    workdir = tmp_path / "run"
    (workdir / "bootstrap").mkdir(parents=True)
    (workdir / "bootstrap" / "input.null").write_text(program)
    monkeypatch.chdir(workdir)
    result = NullVM().execute(stream)
    assert result.success, result.error
    return result.output


def test_emitter_lowers_sample_program_to_superbit(tmp_path, monkeypatch):
    sample = (ROOT / "bootstrap" / "input.null").read_text()

    assert _emit(tmp_path, monkeypatch, sample) == SAMPLE_IR


def _without_declared_types(lines: list[str]) -> list[str]:
    # The function marker carries the declared parameter and return types for
    # backends that type calls. English-dialect functions have no type syntax, so
    # that surface-only annotation is the one legitimate difference between the
    # two dialect dumps; the instructions themselves must still agree.
    return [re.sub(r" types=\S* ret=\S*$", "", line) for line in lines]


def test_english_and_modern_programs_emit_identical_ir(tmp_path, monkeypatch):
    english = (ROOT / "bootstrap" / "dual_english.null").read_text()
    modern = (ROOT / "bootstrap" / "dual_modern.null").read_text()

    english_ir = _emit(tmp_path / "e", monkeypatch, english)
    modern_ir = _emit(tmp_path / "m", monkeypatch, modern)

    assert _without_declared_types(english_ir) == _without_declared_types(modern_ir)
    assert "types=Num,Num" in "\n".join(modern_ir)
    instructions = [line for line in english_ir if line.startswith("IR ")]
    assert len(instructions) >= 60
    assert english_ir[-1].startswith("TOKENS ")


def test_language_features_reach_the_right_layers(tmp_path, monkeypatch):
    english = (ROOT / "bootstrap" / "dual_english.null").read_text()
    ir = "\n".join(_emit(tmp_path, monkeypatch, english))

    # fused, data-parallel lowering
    assert "IR 113 " in ir and "@simd fused" in ir
    assert "filter @simd fused arity=2" in ir
    assert "map @simd fused arity=2" in ir
    # null safety is explicit in the stream, not an exception path
    assert "IR 60 name @scalar" in ir
    assert "IR 61  @scalar" in ir
    # match dispatch and control flow
    assert "IR 50 Ok(bind value) @match" in ir
    assert "IR 52 no_match @match" in ir
    assert "IR 40 L_s6_else @control" in ir
    assert "IR 41 L_s6_end @control" in ir
    assert "LABEL L_s6_else" in ir
    # calls keep their arity as metadata
    assert "IR 70 add @scalar arity=2" in ir


def test_emitter_writes_the_ir_file(tmp_path, monkeypatch):
    sample = (ROOT / "bootstrap" / "input.null").read_text()
    output = _emit(tmp_path, monkeypatch, sample)

    rows = (tmp_path / "run" / "bootstrap" / "program.ir").read_text().splitlines()
    assert rows[0] == "IR\t74\tadd\tlang\tarity=2 params=a,b types=Num,Num ret=Num"
    assert rows[-1] == "IR\t255\tHALT\tscalar\tend"
    assert len(rows) == len(output) - 1
    assert [row.split("\t")[1] for row in rows if row.startswith("IR")] == [
        line.split(" ")[1] for line in output[:-1] if line.startswith("IR ")
    ]
