"""Tests for the fifth self-hosted stage (bootstrap/vm.null).

The chain under test is entirely Null: source -> parser.null front end ->
emitter.null lowering -> super-bit IR stream -> vm.null execution.
"""

from pathlib import Path

import pytest

from null_system.lang.compiler import NullLangCompiler
from null_system.lang.modern.modern_rust import ModernRustParser
from null_system.vm.vm import NullVM

ROOT = Path(__file__).resolve().parents[2]

CASES = {
    "sum loop with a call": (
        """fn add(a, b) { return a + b; }
let total = 0;
let i = 1;
while i <= 5 {
    total = total + i;
    i = i + 1;
}
println(add(total, 10));
""",
        ["25"],
    ),
    "arrays and LEN": (
        """let xs = [4, 5, 6];
let n = 0;
let i = 0;
while i < LEN(xs) {
    n = n + xs[i];
    i = i + 1;
}
println(n);
println(LEN(xs));
""",
        ["15", "3"],
    ),
    "string function": (
        """fn greet(who) { return "hello, " + who; }
println(greet("null"));
""",
        ["hello, null"],
    ),
    "if / else branch": (
        """let n = 7;
if n > 5 {
    println("big");
} else {
    println("small");
}
""",
        ["big"],
    ),
}


def _pipeline():
    parser = NullLangCompiler().compile(
        ModernRustParser().parse((ROOT / "bootstrap" / "emitter.null").read_text())
    )
    machine = NullLangCompiler().compile(
        ModernRustParser().parse((ROOT / "bootstrap" / "vm.null").read_text())
    )
    return parser, machine


@pytest.fixture(scope="module")
def stages():
    return _pipeline()


@pytest.mark.parametrize("name", sorted(CASES))
def test_end_to_end_execution(tmp_path, monkeypatch, stages, name):
    source, expected = CASES[name]
    parser, machine = stages

    workdir = tmp_path / "run"
    (workdir / "bootstrap").mkdir(parents=True)
    (workdir / "bootstrap" / "input.null").write_text(source)
    monkeypatch.chdir(workdir)

    emitted = NullVM().execute(parser)
    assert emitted.success, emitted.error
    assert (workdir / "bootstrap" / "program.ir").exists()

    executed = NullVM().execute(machine)
    assert executed.success, executed.error
    assert executed.output == expected


def test_vm_reports_unknown_opcode(tmp_path, monkeypatch, stages):
    _, machine = stages
    workdir = tmp_path / "bad"
    (workdir / "bootstrap").mkdir(parents=True)
    (workdir / "bootstrap" / "program.ir").write_text("IR\t249\tmystery\tscalar\t\nIR\t255\tHALT\tscalar\tend\n")
    monkeypatch.chdir(workdir)

    result = NullVM().execute(machine)
    assert result.success
    assert result.output == ["VM ERROR: unsupported opcode 249 mystery"]
