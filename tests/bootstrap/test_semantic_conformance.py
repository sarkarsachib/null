"""Semantic conformance: one corpus, two backends, identical observable behavior.

Phase 1.2 of the roadmap requires the host VM and the native compiler to agree
on observable semantics. Before this file nothing compared them: every existing
test checked one backend, and the two known divergences of Phase 0 (`match` and
float literals) were only found by hand.

Each case in ``CORPUS`` is a Null program plus the exact stdout it must produce.
For every case the suite:

1. compiles the program with ``bootstrap/nullc.null`` on the host VM and runs the
   resulting IR on the bootstrap VM (the reference implementation);
2. compiles the same program with ``bootstrap/emitter.null``, lowers the IR with
   ``bootstrap/native.null``, assembles it with ``cc -O0`` and runs the binary;
3. requires the VM output to equal the expected output, the native output to
   equal the VM output, and the backend report to contain no ``FALLBACK`` row.

The expected output is part of the case, so a program that is wrong on *both*
backends still fails instead of passing as a trivially equal pair.

Adding a case is adding an entry to ``CORPUS``. A case belongs here once both
backends execute it; programs either backend refuses belong in
``test_native_backend.py`` (FALLBACK/trap assertions).
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
    """The stages resolve `bootstrap/input.null` relative to the process cwd."""
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


def _vm_output(stages, workdir: Path, program: str):
    (workdir / "bootstrap").mkdir(parents=True, exist_ok=True)
    (workdir / "bootstrap" / "input.null").write_text(program)
    with _cwd(workdir):
        result = NullVM().execute(copy.deepcopy(stages["nullc"]))
    assert result.success, f"bootstrap VM failed: {result.error}"
    return result.output


def _native_output(stages, workdir: Path, program: str):
    (workdir / "bootstrap").mkdir(parents=True, exist_ok=True)
    (workdir / "bootstrap" / "input.null").write_text(program)
    (workdir / "bootstrap" / "compile-only.flag").write_text("")
    with _cwd(workdir):
        emitted = NullVM().execute(copy.deepcopy(stages["emitter"]))
        assert emitted.success, f"emitter failed: {emitted.error}"
        lowered = NullVM().execute(copy.deepcopy(stages["native"]))
        assert lowered.success, f"native backend failed: {lowered.error}"

    ir = (workdir / "bootstrap" / "program.ir").read_text()
    assert "unsupported:" not in ir, f"front end bailed on the source:\n{ir}"

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
        run = subprocess.run([str(exe)], capture_output=True, text=True)
    assert run.returncode == 0, f"native exit {run.returncode}: {run.stderr}"
    return run.stdout.splitlines()


CORPUS = [
    pytest.param(
        "arithmetic-precedence",
        "println(2 + 3 * 4);\n"
        "println((2 + 3) * 4);\n"
        "println(7 / 2);\n"
        "println(7 - 10);\n",
        ["14", "20", "3", "-3"],
        id="arithmetic-precedence",
    ),
    pytest.param(
        "comparison-and-boolean-operators",
        "println(3 < 4);\n"
        "println(3 >= 4);\n"
        "println(4 == 4);\n"
        "println(4 != 4);\n"
        "println(true && false);\n"
        "println(false || true);\n"
        "println(!true);\n",
        ["true", "false", "true", "false", "false", "true", "false"],
        id="comparison-and-boolean-operators",
    ),
    pytest.param(
        "if-else-chain",
        "let n = 0;\n"
        "if n > 0 { println(\"pos\"); } else { println(\"nonpos\"); }\n"
        "n = 5;\n"
        "if n > 10 { println(\"big\"); } else { if n > 3 { println(\"mid\"); } else { println(\"small\"); } }\n",
        ["nonpos", "mid"],
        id="if-else-chain",
    ),
    pytest.param(
        "while-accumulation",
        "let i = 0;\n"
        "let total = 0;\n"
        "while i < 5 { total = total + i; i = i + 1; }\n"
        "println(total);\n"
        "println(i);\n",
        ["10", "5"],
        id="while-accumulation",
    ),
    pytest.param(
        "for-in-and-array-reads",
        "let nums = [4, 8, 15, 16];\n"
        "let sum = 0;\n"
        "for v in nums { sum = sum + v; }\n"
        "println(sum);\n"
        "println(LEN(nums));\n"
        "println(nums[2]);\n",
        ["43", "4", "15"],
        id="for-in-and-array-reads",
    ),
    pytest.param(
        "array-element-write",
        "let a = [10, 20, 30];\n"
        "a[1] = 42;\n"
        "println(a[0] + a[1] + a[2]);\n",
        ["82"],
        id="array-element-write",
    ),
    pytest.param(
        "append-grows-the-array",
        "let a = [];\n"
        "let i = 0;\n"
        "while i < 10 { a = APPEND(a, i * i); i = i + 1; }\n"
        "println(LEN(a));\n"
        "println(a[9]);\n"
        "println(a[3]);\n",
        ["10", "81", "9"],
        id="append-grows-the-array",
    ),
    pytest.param(
        "string-operations",
        'let s = "abc";\n'
        "println(s + \"def\");\n"
        "println(LEN(s));\n"
        "println(CHAR_AT(s, 1));\n"
        'println(s == "abc");\n'
        'println(s == "abd");\n'
        "println(TO_STRING(42));\n",
        ["abcdef", "3", "b", "true", "false", "42"],
        id="string-operations",
    ),
    pytest.param(
        "string-split-join-substr",
        'let parts = SPLIT("a,b,c", ",");\n'
        "println(LEN(parts));\n"
        'println(JOIN(parts, "-"));\n'
        'println(SUBSTR("abcdef", 1, 4));\n'
        'println(CONTAINS("hello world", "lo w"));\n',
        ["3", "a-b-c", "bcd", "true"],
        id="string-split-join-substr",
    ),
    pytest.param(
        "functions-and-recursion",
        "fn fib(n: Num) -> Num {\n"
        "    if n < 2 { return n; }\n"
        "    return fib(n - 1) + fib(n - 2);\n"
        "}\n"
        "fn add(a: Num, b: Num) -> Num {\n"
        "    return a + b;\n"
        "}\n"
        "println(fib(10));\n"
        "println(add(19, 23));\n",
        ["55", "42"],
        id="functions-and-recursion",
    ),
    pytest.param(
        "match-integer-arms",
        "let n = 2;\n"
        "match n {\n"
        "    1 => println(\"one\"),\n"
        "    2 => println(\"two\"),\n"
        "    _ => println(\"other\")\n"
        "}\n",
        ["two"],
        id="match-integer-arms",
    ),
    pytest.param(
        "match-wildcard-fallthrough",
        "let n = 9;\n"
        "match n {\n"
        "    1 => println(\"one\"),\n"
        "    2 => println(\"two\"),\n"
        "    _ => println(\"other\")\n"
        "}\n",
        ["other"],
        id="match-wildcard-fallthrough",
    ),
    pytest.param(
        "match-string-arms",
        'let s = "b";\n'
        "match s {\n"
        '    "a" => println("A"),\n'
        '    "b" => println("B"),\n'
        '    _ => println("Z")\n'
        "}\n",
        ["B"],
        id="match-string-arms",
    ),
    pytest.param(
        "float-literals",
        "let a = 3.5;\n"
        "let b = 0.5;\n"
        "println(a);\n"
        "println(b);\n"
        "println(12.25);\n",
        ["3.5", "0.5", "12.25"],
        id="float-literals",
    ),
    pytest.param(
        "break-and-continue",
        "let i = 0;\n"
        "let acc = 0;\n"
        "while i < 10 {\n"
        "    i = i + 1;\n"
        "    if i == 3 { continue; }\n"
        "    if i == 6 { break; }\n"
        "    acc = acc + i;\n"
        "}\n"
        "println(acc);\n",
        ["12"],
        id="break-and-continue",
    ),
    pytest.param(
        "nested-loops",
        "let outer = 0;\n"
        "let count = 0;\n"
        "while outer < 3 {\n"
        "    let inner = 0;\n"
        "    while inner < 2 { count = count + 1; inner = inner + 1; }\n"
        "    outer = outer + 1;\n"
        "}\n"
        "println(count);\n",
        ["6"],
        id="nested-loops",
    ),
    pytest.param(
        "integer-division-truncates-toward-zero",
        "println(9 / 4);\n"
        "println(-9 / 4);\n"
        "println(3 / 5);\n"
        "println(1 - (1 / 2) * 2);\n"
        "println(4 - (4 / 2) * 2);\n",
        ["2", "-2", "0", "1", "0"],
        id="integer-division-truncates-toward-zero",
    ),
    pytest.param(
        "builtins-slice-number-and-files",
        "let nums = [10, 20, 30, 40];\n"
        "let mid = SLICE(nums, 1, 3);\n"
        "println(LEN(mid));\n"
        "println(mid[0] + mid[1]);\n"
        'println(TO_NUMBER("123"));\n'
        'WRITE_FILE("bootstrap/out.txt", "written");\n'
        'println(FILE_EXISTS("bootstrap/out.txt"));\n'
        'println(READ_FILE("bootstrap/out.txt"));\n',
        ["2", "50", "123", "true", "written"],
        id="builtins-slice-number-and-files",
    ),
    pytest.param(
        "array-of-strings",
        'let words = ["alpha", "beta"];\n'
        "println(words[0]);\n"
        "println(LEN(words[1]));\n"
        'println(words[0] + "-" + words[1]);\n',
        ["alpha", "4", "alpha-beta"],
        id="array-of-strings",
    ),
]


@pytest.mark.parametrize("name, program, expected", CORPUS)
def test_vm_and_native_agree_with_the_specified_semantics(
    stages, tmp_path, name, program, expected
):
    vm_lines = _vm_output(stages, tmp_path / "vm", program)
    assert vm_lines == expected, f"{name}: the VM contradicts the specification"

    native_lines = _native_output(stages, tmp_path / "native", program)
    assert native_lines == expected, f"{name}: the native backend contradicts the specification"
    assert native_lines == vm_lines, f"{name}: the two backends disagree"
