"""Regression tests for two silent-wrong-answer defects in the self-hosted chain.

Both used to compile "successfully" and then do the wrong thing:

* ``match`` emitted no comparison and no branch. Every arm's body was emitted
  inline, so the first arm always ran (and control fell through the rest), on
  both the bootstrap VM and native code.
* A float literal lexed as ``3`` followed by ``.5``, which the parser read as a
  ``get_member`` access on field ``5``: ``let x = 3.5`` produced an integer 3 and
  a member lookup.

The tests assert both the IR the emitter must produce and the value the
generated x86-64 binary actually prints, so a lowering that only looks right in
the IR stream cannot pass.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from null_system.lang.compiler import NullLangCompiler
from null_system.lang.modern.modern_rust import ModernRustParser
from null_system.vm.vm import NullVM

ROOT = Path(__file__).resolve().parents[2]

MATCH_PROGRAM = (
    "let x = 2\n"
    "match x {\n"
    '    1 => println("one"),\n'
    '    2 => println("two"),\n'
    '    _ => println("other")\n'
    "}\n"
)


def _emit_ir(tmp_path, monkeypatch, program: str) -> str:
    """Run the self-hosted emitter on a program and return its IR file."""
    stream = NullLangCompiler().compile(
        ModernRustParser().parse((ROOT / "bootstrap" / "emitter.null").read_text())
    )
    workdir = tmp_path / "emit"
    (workdir / "bootstrap").mkdir(parents=True)
    (workdir / "bootstrap" / "input.null").write_text(program)
    (workdir / "bootstrap" / "compile-only.flag").write_text("")
    monkeypatch.chdir(workdir)
    result = NullVM().execute(stream)
    assert result.success, result.error
    return (workdir / "bootstrap" / "program.ir").read_text()


def _run_backend(tmp_path, monkeypatch, ir_text: str):
    stream = NullLangCompiler().compile(
        ModernRustParser().parse((ROOT / "bootstrap" / "native.null").read_text())
    )
    workdir = tmp_path / "native"
    (workdir / "bootstrap").mkdir(parents=True)
    (workdir / "bootstrap" / "program.ir").write_text(ir_text)
    monkeypatch.chdir(workdir)
    result = NullVM().execute(stream)
    assert result.success, result.error
    return workdir, result


def _build(workdir: Path, name: str) -> Path:
    if shutil.which("cc") is None:
        pytest.skip("cc is required to assemble the generated code")
    asm = workdir / "bootstrap" / "program.s"
    exe = workdir / name
    subprocess.run(["cc", "-o", str(exe), str(asm)], check=True)
    return exe


def _native_stdout_and_report(tmp_path, monkeypatch, program: str):
    ir = _emit_ir(tmp_path, monkeypatch, program)
    workdir, _ = _run_backend(tmp_path, monkeypatch, ir)
    report = (workdir / "bootstrap" / "backend.report").read_text()
    exe = _build(workdir, "prog")
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    return run, report, ir


def test_match_emits_a_compare_and_branch_per_arm(tmp_path, monkeypatch):
    ir = _emit_ir(tmp_path, monkeypatch, MATCH_PROGRAM)

    # one EQ (22) guarding each literal arm, each followed by a conditional
    # branch (40) to the arm's label, and an unconditional jump (41) past the
    # rest of the chain at the end of the arm body.
    assert ir.count("IR\t22\t") == 2
    assert "IR\t40\tL_s1_a0\tcontrol" in ir
    assert "IR\t40\tL_s1_a1\tcontrol" in ir
    assert "IR\t41\tL_s1_end\tcontrol" in ir
    assert "LABEL\tL_s1_a0" in ir and "LABEL\tL_s1_a1" in ir
    # the old stream had a single catch-all row and no branch at all
    assert "IR\t52\tno_match\tmatch" not in ir
    assert "IR\t50\t" not in ir


def test_match_runs_only_the_matching_arm_natively(tmp_path, monkeypatch):
    run, report, _ = _native_stdout_and_report(tmp_path, monkeypatch, MATCH_PROGRAM)

    assert "FALLBACK" not in report
    assert run.returncode == 0
    assert run.stdout.strip() == "two"


def test_match_falls_through_to_the_wildcard_arm(tmp_path, monkeypatch):
    program = MATCH_PROGRAM.replace("let x = 2", "let x = 9")
    run, report, _ = _native_stdout_and_report(tmp_path, monkeypatch, program)

    assert "FALLBACK" not in report
    assert run.returncode == 0
    assert run.stdout.strip() == "other"


def test_match_compares_string_patterns(tmp_path, monkeypatch):
    program = (
        'let s = "b"\n'
        "match s {\n"
        '    "a" => println("A"),\n'
        '    "b" => println("B"),\n'
        '    _ => println("Z")\n'
        "}\n"
    )
    run, report, _ = _native_stdout_and_report(tmp_path, monkeypatch, program)

    assert "FALLBACK" not in report
    assert run.returncode == 0
    assert run.stdout.strip() == "B"


def test_float_literal_is_a_single_tagged_constant(tmp_path, monkeypatch):
    ir = _emit_ir(tmp_path, monkeypatch, "let x = 3.5\n")

    assert "IR\t1\t3.5\tscalar\tfloat" in ir
    # the defect: `3.5` used to become the integer 3 plus a member access
    assert "get_member" not in ir
    assert "IR\t1\t3\tscalar" not in ir


def test_float_literal_prints_its_fractional_value(tmp_path, monkeypatch):
    run, report, _ = _native_stdout_and_report(
        tmp_path, monkeypatch, "let x = 3.5\nprintln(x)\n"
    )

    assert "FALLBACK" not in report
    assert run.returncode == 0
    assert run.stdout.strip() == "3.5"


def test_negative_and_wide_float_literals_survive(tmp_path, monkeypatch):
    program = "let a = 0.5\nlet b = 12.25\nlet c = 100.0\nprintln(a)\nprintln(b)\nprintln(c)\n"
    run, report, _ = _native_stdout_and_report(tmp_path, monkeypatch, program)

    assert "FALLBACK" not in report
    assert run.returncode == 0
    assert run.stdout.split() == ["0.5", "12.25", "100"]


def test_float_arithmetic_is_refused_instead_of_miscompiled(tmp_path, monkeypatch):
    # Integer add on the raw IEEE-754 bits would produce a plausible-looking but
    # wrong number, so the backend must report and trap instead.
    program = "let a = 1.5\nlet b = a + 1.0\nprintln(b)\n"
    run, report, ir = _native_stdout_and_report(tmp_path, monkeypatch, program)

    assert "IR\t10\t" in ir
    assert "FALLBACK 10 float-arith-not-in-this-stage" in report
    assert run.returncode == 4


def test_variant_pattern_traps_instead_of_running_the_first_arm(tmp_path, monkeypatch):
    # `Ok(value)` needs a tagged union to destructure; without one the only
    # honest lowering is an explicit trap, never a silent fall-through.
    program = (
        "let total = 3\n"
        "match total {\n"
        "    Ok(value) => println(value),\n"
        '    _ => println("none")\n'
        "}\n"
    )
    ir = _emit_ir(tmp_path, monkeypatch, program)
    assert "IR\t52\tOk(bind value)\tmatch" in ir

    workdir, _ = _run_backend(tmp_path, monkeypatch, ir)
    report = (workdir / "bootstrap" / "backend.report").read_text()
    assert "FALLBACK 52" in report
    exe = _build(workdir, "variant")
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    assert run.returncode == 4
