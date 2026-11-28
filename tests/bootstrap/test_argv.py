"""Process arguments and subprocesses: the primitives a native driver needs.

A native bootstrap driver cannot be written in Null unless the language can read
its own argv and run a compiler. These tests pin that behavior on both backends:
the host VM (which gets argv injected) and a real native binary run with real
arguments.
"""

import copy
import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest

from null_system.lang.compiler import NullLangCompiler
from null_system.lang.modern.modern_rust import ModernRustParser
from null_system.vm.vm import NullVM

ROOT = Path(__file__).resolve().parents[2]


@contextmanager
def _cwd(path: Path):
    previous = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _compile_stage(name: str):
    source = (ROOT / "bootstrap" / name).read_text()
    return NullLangCompiler().compile(ModernRustParser().parse(source))


@pytest.fixture(scope="module")
def stages():
    if shutil.which("cc") is None:
        pytest.skip("cc is required to assemble the generated code")
    return {
        "nullc": _compile_stage("nullc.null"),
        "emitter": _compile_stage("emitter.null"),
        "native": _compile_stage("native.null"),
    }


def _vm_output(stages, workdir: Path, program: str, argv):
    (workdir / "bootstrap").mkdir(parents=True, exist_ok=True)
    (workdir / "bootstrap" / "input.null").write_text(program)
    vm = NullVM()
    vm.argv = list(argv)
    # Compile the small program directly: nullc.null is itself argv-driven and
    # would treat argv[1] as a source filename.
    stream = NullLangCompiler().compile(ModernRustParser().parse(program))
    with _cwd(workdir):
        result = vm.execute(stream)
    assert result.success, f"bootstrap VM failed: {result.error}"
    return result.output


def _native_output(stages, workdir: Path, program: str, argv):
    (workdir / "bootstrap").mkdir(parents=True, exist_ok=True)
    (workdir / "bootstrap" / "input.null").write_text(program)
    (workdir / "bootstrap" / "compile-only.flag").write_text("")
    with _cwd(workdir):
        emitted = NullVM().execute(copy.deepcopy(stages["emitter"]))
        assert emitted.success, f"emitter failed: {emitted.error}"
        lowered = NullVM().execute(copy.deepcopy(stages["native"]))
        assert lowered.success, f"native backend failed: {lowered.error}"

    report = (workdir / "bootstrap" / "backend.report").read_text()
    fallbacks = [line for line in report.splitlines() if line.startswith("FALLBACK")]
    assert not fallbacks, f"backend fell back: {fallbacks}"

    exe = workdir / "prog"
    subprocess.run(
        ["cc", "-O0", "-o", str(exe), str(workdir / "bootstrap" / "program.s")],
        check=True,
        capture_output=True,
        text=True,
    )
    with _cwd(workdir):
        run = subprocess.run([str(exe), *argv], capture_output=True, text=True)
    assert run.returncode == 0, f"native exit {run.returncode}: {run.stderr}"
    return run.stdout.splitlines()


ARGC_ARGV_PROGRAM = (
    "println(ARGC());\n"
    "println(ARGV(1));\n"
    "println(ARGV(99));\n"
)


def test_argc_and_argv_agree_between_backends(stages, tmp_path):
    # argv[0] is the executable path on a real process; only the arguments at
    # index 1 onward are portable across the host VM and a native binary.
    argv = ["prog", "alpha"]
    expected = ["3", "prog", ""]
    # subprocess.run puts the executable path at argv[0], so the native binary
    # sees [exe, *argv]. Inject the same shape into the host VM.
    assert _vm_output(stages, tmp_path / "vm", ARGC_ARGV_PROGRAM, ["exe", *argv]) == expected
    assert _native_output(stages, tmp_path / "native", ARGC_ARGV_PROGRAM, argv) == expected


SHELL_PROGRAM = (
    'let code = SHELL("exit 3");\n'
    "println(code);\n"
)


def test_shell_returns_the_child_exit_status(stages, tmp_path):
    expected = ["3"]
    assert _vm_output(stages, tmp_path / "vm", SHELL_PROGRAM, ["prog"]) == expected
    assert _native_output(stages, tmp_path / "native", SHELL_PROGRAM, ["prog"]) == expected


SHELL_OUTPUT_PROGRAM = (
    'let code = SHELL("echo from-child");\n'
    "println(code);\n"
)


def test_shell_child_output_reaches_stdout(stages, tmp_path):
    native = _native_output(stages, tmp_path / "native", SHELL_OUTPUT_PROGRAM, ["prog"])
    assert "from-child" in native
    assert native[-1] == "0"
