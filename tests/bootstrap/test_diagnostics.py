"""Compile-time diagnostics: a construct the front end cannot lower must be
reported and must stop the program, never silently truncate it.

Reproduced before this file existed: ``let y = ;`` compiled "successfully" to

    IR  255  unsupported:eof:PUNCT:;  lang  todo

which both backends handled as a no-op (the VM ignored the row; the native
backend emitted nothing at all). The program then printed what it could and
exited 0, so a typo looked like a working build.

Now the emitter reports ``2:9: error: unsupported construct: …`` when it emits
such a row: ``tokenize`` tracks the line and column of every token, the parser
records the position on the offending ``eof`` node, and the emitter appends it
to the unsupported marker. The VM stops with ``VM ERROR: unsupported construct
…`` and the native backend routes the row to ``null_unsupported``
(``UNSUPPORTED OP!!``, exit 4).
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from null_system.lang.compiler import NullLangCompiler
from null_system.lang.modern.modern_rust import ModernRustParser
from null_system.vm.vm import NullVM

ROOT = Path(__file__).resolve().parents[2]

DIRTY = "let x = 5;\nlet y = ;\nprintln(x);\n"
CLEAN = "let x = 5;\nprintln(x);\n"


def _compile(name: str):
    source = (ROOT / "bootstrap" / name).read_text()
    return NullLangCompiler().compile(ModernRustParser().parse(source))


def _run_nullc(tmp_path, program: str):
    """Compile and execute on the bootstrap VM (nullc emits, then runs IR)."""
    stream = _compile("nullc.null")
    workdir = tmp_path / "vm"
    (workdir / "bootstrap").mkdir(parents=True)
    (workdir / "bootstrap" / "input.null").write_text(program)
    previous = os.getcwd()
    os.chdir(workdir)
    try:
        result = NullVM().execute(stream)
    finally:
        os.chdir(previous)
    assert result.success, result.error
    return result.output


def _build_native(tmp_path, program: str):
    emitter = _compile("emitter.null")
    backend = _compile("native.null")
    workdir = tmp_path / "native"
    (workdir / "bootstrap").mkdir(parents=True)
    (workdir / "bootstrap" / "input.null").write_text(program)
    (workdir / "bootstrap" / "compile-only.flag").write_text("")
    previous = os.getcwd()
    os.chdir(workdir)
    try:
        emitted = NullVM().execute(emitter)
        lowered = NullVM().execute(backend)
    finally:
        os.chdir(previous)
    assert emitted.success, emitted.error
    assert lowered.success, lowered.error

    if shutil.which("cc") is None:
        pytest.skip("cc is required to assemble the generated code")
    exe = workdir / "prog"
    subprocess.run(
        ["cc", "-O0", "-o", str(exe), str(workdir / "bootstrap" / "program.s")],
        check=True,
        capture_output=True,
        text=True,
    )
    return exe, (workdir / "bootstrap" / "backend.report").read_text()


def test_clean_program_reports_no_errors(tmp_path):
    output = _run_nullc(tmp_path, CLEAN)
    assert output == ["5"]
    assert not [line for line in output if line.startswith("ERROR:")]


def test_vm_reports_and_stops_on_an_unparseable_statement(tmp_path):
    output = _run_nullc(tmp_path, DIRTY)

    # `let y = ;` — the `;` is at line 2, column 9 (1-based).
    assert "2:9: error: unsupported construct: unsupported:eof:PUNCT:;" in output
    # the compile error stops the program; the trailing `println(x)` never runs
    assert "5" not in output
    assert any(line.startswith("VM ERROR: unsupported construct") for line in output)


def test_location_points_at_the_offending_token(tmp_path):
    # Same mistake one line further down: the reported line must follow the source.
    output = _run_nullc(tmp_path, "let x = 5;\nprintln(x);\nlet y = ;\n")
    assert "3:9: error: unsupported construct: unsupported:eof:PUNCT:;" in output


def test_native_binary_refuses_a_program_with_a_compile_error(tmp_path):
    exe, report = _build_native(tmp_path, DIRTY)

    assert "ERROR unsupported:eof:PUNCT:;" in report
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    assert run.returncode == 4
    assert "UNSUPPORTED OP!!" in run.stdout + run.stderr


def test_native_binary_still_runs_a_clean_program(tmp_path):
    exe, report = _build_native(tmp_path, CLEAN)

    assert "ERROR " not in report
    assert "FALLBACK" not in report
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    assert run.returncode == 0
    assert run.stdout.split() == ["5"]
