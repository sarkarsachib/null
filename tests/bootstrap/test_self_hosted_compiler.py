"""Tests for the linked self-hosted compiler (bootstrap/nullc.null).

bootstrap/link.null assembles nullc.null from the stage libraries: the front end
from emitter.null and the interpreter from vm.null. These tests pin the
properties that make it one compiler rather than a pipeline of scripts: it runs
a program in a single process, its IR is the emitter stage's IR byte for byte,
and the checked-in file is what the link step produces today.

Compiling the compiler itself (12,854 IR rows, ~60 s per stage on the host VM)
is the Phase 4 check in bench/selfhost_check.sh, not part of this suite.
"""

from pathlib import Path

from null_system.lang.compiler import NullLangCompiler
from null_system.lang.modern.modern_rust import ModernRustParser
from null_system.vm.vm import NullVM

ROOT = Path(__file__).resolve().parents[2]

PROGRAM = """fn add(a: Num, b: Num) -> Num {
    return a + b;
}
let x = 0;
let i = 0;
while i < 10 {
    x = x + i;
    i = i + 1;
}
println(x);
println(add(x, 7));
let a = [3, 1, 4];
a[1] = a[0] + a[2];
println(a[1]);
"""


def _stage_stream(name: str):
    source = (ROOT / "bootstrap" / name).read_text()
    return NullLangCompiler().compile(ModernRustParser().parse(source))


def _run_in(workdir: Path, monkeypatch, stage: str):
    monkeypatch.chdir(workdir)
    return NullVM().execute(_stage_stream(stage))


def _workdir(tmp_path: Path, source: str, compile_only: bool = False) -> Path:
    workdir = tmp_path / "run"
    (workdir / "bootstrap").mkdir(parents=True)
    (workdir / "bootstrap" / "input.null").write_text(source)
    if compile_only:
        (workdir / "bootstrap" / "compile-only.flag").write_text("")
    return workdir


def test_nullc_compiles_and_runs_a_program_in_one_process(tmp_path, monkeypatch):
    workdir = _workdir(tmp_path, PROGRAM)
    result = _run_in(workdir, monkeypatch, "nullc.null")

    assert result.success, result.error
    assert result.output == ["45", "52", "7"]
    assert (workdir / "bootstrap" / "program.ir").exists()


def test_nullc_emits_the_same_ir_as_the_emitter_stage(tmp_path, monkeypatch):
    linked = _workdir(tmp_path / "linked", PROGRAM, compile_only=True)
    _run_in(linked, monkeypatch, "nullc.null")
    staged = _workdir(tmp_path / "staged", PROGRAM)
    _run_in(staged, monkeypatch, "emitter.null")

    assert (linked / "bootstrap" / "program.ir").read_bytes() == (
        staged / "bootstrap" / "program.ir"
    ).read_bytes()


def test_link_step_reproduces_the_checked_in_compiler(tmp_path, monkeypatch):
    workdir = tmp_path / "link"
    (workdir / "bootstrap").mkdir(parents=True)
    for part in ("emitter.null", "vm.null"):
        (workdir / "bootstrap" / part).write_text((ROOT / "bootstrap" / part).read_text())

    result = _run_in(workdir, monkeypatch, "link.null")

    assert result.success, result.error
    assert (workdir / "bootstrap" / "nullc.null").read_bytes() == (
        ROOT / "bootstrap" / "nullc.null"
    ).read_bytes()
