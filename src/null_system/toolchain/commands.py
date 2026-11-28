"""Toolchain commands built on the dependency-free CLI framework.

These commands are deliberately thin: they invoke the repository's existing
compile/test/format mechanisms with explicit paths and exit codes. They are the
place where each Python-backed action will be replaced by a native Null stage.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from .cli import Argument, CLI, CLIError, Command, Option

ROOT = Path(__file__).resolve().parents[3]
VENV_PYTHON = ROOT / "venv" / "bin" / "python"


def _python() -> str:
    """Use the project venv interpreter when present, else the running one."""
    return str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable


def _run(command: list[str], *, cwd: Path | None = None) -> int:
    try:
        return subprocess.call(command, cwd=str(cwd or ROOT))
    except FileNotFoundError as error:
        raise CLIError(f"program not found: {command[0]}") from error


def _existing_file(path: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    if not candidate.is_file():
        raise CLIError(f"file not found: {path}")
    return candidate


def _compile_stage(path: Path, workdir: Path) -> Path:
    """Compile a .null stage with the existing host pipeline into program.ir."""
    sys.path.insert(0, str(ROOT / "src"))
    from null_system.lang.compiler import NullLangCompiler
    from null_system.lang.modern.modern_rust import ModernRustParser
    from null_system.vm.vm import NullVM

    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "bootstrap").mkdir(exist_ok=True)
    (workdir / "bootstrap" / "input.null").write_text(path.read_text(), encoding="utf-8")
    stream = NullLangCompiler().compile(ModernRustParser().parse(path.read_text()))
    result = NullVM().execute(stream)
    if not result.success:
        raise CLIError(f"compilation failed: {result.error}")
    for line in result.output:
        print(line)
    ir = workdir / "bootstrap" / "program.ir"
    if not ir.is_file():
        raise CLIError("compiler produced no program.ir")
    return ir


def build(source: str, output: str | None, stage: str) -> int:
    """Compile a Null source file to IR or to a native executable."""
    path = _existing_file(source)
    if stage == "ir":
        target = Path(output) if output else ROOT / "bootstrap" / "program.ir"
        ir = _compile_stage(path, target.parent)
        if ir.resolve() != target.resolve():
            shutil.copyfile(ir, target)
        print(f"IR written to {target}")
        return 0
    if stage != "native":
        raise CLIError(f"unknown build stage: {stage}")
    work = ROOT / "bench" / "build" / "toolchain" / path.stem
    ir = _compile_stage(path, work)
    shutil.copyfile(ir, work / "bootstrap" / "program.ir")
    (work / "bootstrap" / "compile-only.flag").write_text("")
    shutil.copyfile(ROOT / "bootstrap" / "native.null", work / "bootstrap" / "native.null")
    sys.path.insert(0, str(ROOT / "src"))
    from null_system.lang.compiler import NullLangCompiler
    from null_system.lang.modern.modern_rust import ModernRustParser
    from null_system.vm.vm import NullVM

    previous = Path.cwd()
    try:
        os.chdir(work)
        source_text = (ROOT / "bootstrap" / "native.null").read_text()
        backend = NullLangCompiler().compile(ModernRustParser().parse(source_text))
        result = NullVM().execute(backend)
    finally:
        os.chdir(previous)
    if not result.success:
        raise CLIError(f"native lowering failed: {result.error}")
    report = work / "bootstrap" / "backend.report"
    if report.is_file() and any(
        line.startswith("FALLBACK") for line in report.read_text().splitlines()
    ):
        raise CLIError("native lowering reported FALLBACK rows")
    asm = work / "bootstrap" / "program.s"
    target = Path(output) if output else work / path.stem
    status = _run(["cc", "-O0", "-o", str(target), str(asm)])
    if status == 0:
        print(f"executable written to {target}")
    return status


def test(target: str | None) -> int:
    """Run the project test suite, or one focused test path."""
    command = [_python(), "-m", "pytest", "-q"]
    if target:
        command.append(target)
    else:
        command.append("tests")
    return _run(command)


def fmt(target: str | None) -> int:
    """Check formatting with the project's configured formatter."""
    command = [_python(), "-m", "ruff", "format", "--check"]
    command.append(target or "src")
    return _run(command)


def clean() -> int:
    """Remove generated compiler outputs, keeping tracked files."""
    removed = 0
    for pattern in ("bootstrap/program.ir", "bootstrap/program.s"):
        path = ROOT / pattern
        if path.is_file():
            path.unlink()
            removed += 1
    build = ROOT / "bench" / "build" / "toolchain"
    if build.is_dir():
        shutil.rmtree(build)
        removed += 1
    print(f"removed {removed} generated artifacts")
    return 0


def bench(name: str | None) -> int:
    """Run the repository benchmark script with an optional workload name."""
    script = ROOT / "bench" / "run_bench.sh"
    if not script.is_file():
        raise CLIError(f"benchmark script not found: {script}")
    command = ["bash", str(script)]
    if name:
        command.append(name)
    return _run(command)


def create_cli() -> CLI:
    cli = CLI("nulltool", "Null language toolchain")
    cli.add(
        Command(
            name="build",
            callback=build,
            help="Compile a .null file to IR or a native executable",
            arguments=(Argument("source", "Source file"),),
            options=(
                Option("output", ("-o", "--output"), "Output path"),
                Option("stage", ("--stage",), "Output stage: ir or native", default="ir"),
            ),
        )
    )
    cli.add(
        Command(
            name="test",
            callback=test,
            help="Run tests",
            arguments=(Argument("target", "Test path", required=False),),
        )
    )
    cli.add(
        Command(
            name="fmt",
            callback=fmt,
            help="Check formatting",
            arguments=(Argument("target", "Path to check", required=False),),
        )
    )
    cli.add(Command(name="clean", callback=clean, help="Remove generated artifacts"))
    cli.add(
        Command(
            name="bench",
            callback=bench,
            help="Run benchmarks",
            arguments=(Argument("name", "Benchmark name", required=False),),
        )
    )
    return cli


cli = create_cli()


def main(argv: list[str] | None = None) -> int:
    return cli.main(sys.argv[1:] if argv is None else argv)
