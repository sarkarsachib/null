"""Tests for the fifth self-hosted stage (bootstrap/native.null).

The backend lowers super-bit IR to x86-64 assembly (GNU as, Intel syntax).
Specialised super-bit opcodes become single instructions; opcodes the target
cannot honour yet are reported as FALLBACK and trap at run time.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from null_system.lang.compiler import NullLangCompiler
from null_system.lang.modern.modern_rust import ModernRustParser
from null_system.vm.vm import NullVM

ROOT = Path(__file__).resolve().parents[2]


def _run_backend(tmp_path, monkeypatch, ir_text: str):
    stream = NullLangCompiler().compile(
        ModernRustParser().parse((ROOT / "bootstrap" / "native.null").read_text())
    )
    workdir = tmp_path / "run"
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


def test_backend_lowers_specialised_opcodes(tmp_path, monkeypatch):
    ir = (ROOT / "bench" / "ir" / "sum_loop.ir").read_text()
    workdir, result = _run_backend(tmp_path, monkeypatch, ir)

    asm = (workdir / "bootstrap" / "program.s").read_text()
    report = (workdir / "bootstrap" / "backend.report").read_text()

    # 100 FAST_ADD_INT -> a bare integer add on registers, no tag checks
    assert re.search(r"^  add r\d+, r\d+$", asm, re.M)
    # 102 FAST_LT_INT + JUMP_IF_FALSE -> cmp/conditional jump, no setcc round-trip
    assert "setl al" not in asm
    assert re.search(r"^  cmp r\d+, r\d+$", asm, re.M)
    # 40/41 stay branches over the same labels the IR named
    labels = re.findall(r"^LABEL\t(\S+)", ir, re.M)
    assert f".L{labels[0]}:" in asm and f".L{labels[1]}:" in asm
    assert re.search(rf"^  j(ge|g) \.L{labels[1]}$", asm, re.M)

    # the arithmetic never round-trips through the operand stack slots: either
    # the register-op selection fired or the whole loop was vectorised
    assert "LOWERED reg-op" in report or "VECTORIZED" in report
    assert "FALLBACK" not in report
    assert any(line.startswith("LOWERED ") for line in result.output)
    assert "FALLBACK 0" in result.output


def test_generated_code_computes_the_c_baseline_result(tmp_path, monkeypatch):
    ir = (ROOT / "bench" / "ir" / "comprehension.ir").read_text()
    workdir, _ = _run_backend(tmp_path, monkeypatch, ir)
    exe = _build(workdir, "comprehension")

    run = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    assert run.stdout.strip() == "5167960026252283648"


def test_unhonourable_opcode_is_reported_and_traps(tmp_path, monkeypatch):
    ir = "IR\t140\tdemo_kernel\tgpu\tkernel=demo_kernel\nIR\t255\tHALT\tscalar\n"
    workdir, _ = _run_backend(tmp_path, monkeypatch, ir)

    report = (workdir / "bootstrap" / "backend.report").read_text()
    asm = (workdir / "bootstrap" / "program.s").read_text()
    assert "FALLBACK 140" in report
    assert "call null_unsupported" in asm

    exe = _build(workdir, "fallback")
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    assert run.returncode == 4


def test_array_workload_uses_index_store_and_array_zero(tmp_path, monkeypatch):
    ir = (ROOT / "bench" / "ir" / "array_map.ir").read_text()
    workdir, _ = _run_backend(tmp_path, monkeypatch, ir)

    asm = (workdir / "bootstrap" / "program.s").read_text()
    report = (workdir / "bootstrap" / "backend.report").read_text()
    # 107 FAST_ARRAY_ZERO allocates through calloc, 105 stores without a bounds check
    assert "call null_array_zero" in asm
    assert "mov qword ptr [rcx + rdx * 8 + 8], rax" in asm
    assert "LOWERED 107 fast-array-zero" in report
    assert "LOWERED 105 fast-index-store" in report

    exe = _build(workdir, "array_map")
    run = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    assert run.stdout.strip() == "159999980000000"


def test_modulo_by_power_of_two_becomes_a_bit_test(tmp_path, monkeypatch):
    # The emitter spells `x % 2 == 0` as `x - (x / 2) * 2 == 0`, because `%` is
    # not a lexer token yet; the backend still recognises it as a bit test.
    ir = (ROOT / "bench" / "ir" / "comprehension.ir").read_text()
    workdir, _ = _run_backend(tmp_path, monkeypatch, ir)

    asm = (workdir / "bootstrap" / "program.s").read_text()
    report = (workdir / "bootstrap" / "backend.report").read_text()
    assert "idiv" not in asm
    assert re.search(r"^  test r\d+, 1$", asm, re.M)
    assert "pow2-branch" in report

    exe = _build(workdir, "comprehension")
    run = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    assert run.stdout.strip() == "5167960026252283648"


def _reduction_ir(n: int, cmp_opcode: int) -> str:
    """`total = 0; i = 1; while i <cmp> n { total += i; i += 1 }` as super-bit IR."""
    return (
        f"IR\t1\t{n}\tscalar\n"
        "IR\t3\tn\tscalar\n"
        "IR\t1\t0\tscalar\n"
        "IR\t3\ttotal\tscalar\n"
        "IR\t1\t1\tscalar\n"
        "IR\t3\ti\tscalar\n"
        "LABEL\tloop\n"
        "IR\t2\ti\tscalar\n"
        "IR\t2\tn\tscalar\n"
        f"IR\t{cmp_opcode}\t\tscalar\n"
        "IR\t40\tend\tscalar\n"
        "IR\t2\ttotal\tscalar\n"
        "IR\t2\ti\tscalar\n"
        "IR\t100\t\tscalar\n"
        "IR\t3\ttotal\tscalar\n"
        "IR\t2\ti\tscalar\n"
        "IR\t1\t1\tscalar\n"
        "IR\t100\t\tscalar\n"
        "IR\t3\ti\tscalar\n"
        "IR\t41\tloop\tscalar\n"
        "LABEL\tend\n"
        "IR\t2\ttotal\tscalar\n"
        "IR\t30\t\tscalar\n"
        "IR\t255\tHALT\tscalar\n"
    )


def test_reduction_loop_is_vectorised(tmp_path, monkeypatch):
    ir = (ROOT / "bench" / "ir" / "sum_loop.ir").read_text()
    workdir, _ = _run_backend(tmp_path, monkeypatch, ir)

    asm = (workdir / "bootstrap" / "program.s").read_text()
    report = (workdir / "bootstrap" / "backend.report").read_text()
    assert "VECTORIZED reduction-loop" in report
    assert "vpbroadcastq ymm1, xmm0" in asm
    assert "vpaddq ymm2, ymm2, ymm1" in asm
    # the scalar loop survives as the tail, so a short trip count stays exact
    assert asm.count(".LL_s3_start:") == 1
    assert "jmp .LL_s3_start" in asm

    exe = _build(workdir, "sum_loop_vec")
    run = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    assert run.stdout.strip() == "5000000050000000"


@pytest.mark.parametrize(
    "n, expected",
    [
        (5, "10"),    # shorter than one vector iteration: the tail does it all
        (8, "28"),    # one vector iteration, nothing left over
        (13, "78"),   # one vector iteration + 4 tail iterations
        (21, "210"),  # two vector iterations + 4 tail iterations
    ],
)
def test_reduction_vector_tail_is_exact(tmp_path, monkeypatch, n, expected):
    # 102 is FAST_LT_INT: i < n, so the sum is 1+..+(n-1).
    workdir, _ = _run_backend(tmp_path, monkeypatch, _reduction_ir(n, 102))
    exe = _build(workdir, f"reduce_{n}")
    run = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    assert run.stdout.strip() == expected


def test_logical_and_or_evaluate_both_operands():
    source = (
        "let x = 5;\n"
        "if x > 1 || x > 9 {\n    println(\"or\");\n}\n"
        "if x > 1 && x > 9 {\n    println(\"and-bad\");\n}\n"
        "if x > 1 && x < 9 {\n    println(\"and\");\n}\n"
    )
    stream = NullLangCompiler().compile(ModernRustParser().parse(source))
    result = NullVM().execute(stream)
    assert result.success, result.error
    assert result.output == ["or", "and"]
