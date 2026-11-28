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


def test_array_workload_is_vectorised(tmp_path, monkeypatch):
    ir = (ROOT / "bench" / "ir" / "array_map.ir").read_text()
    workdir, _ = _run_backend(tmp_path, monkeypatch, ir)

    asm = (workdir / "bootstrap" / "program.s").read_text()
    report = (workdir / "bootstrap" / "backend.report").read_text()
    # both loops in the workload have a vector form: the fill stores four lanes at
    # a time, and the map reads both arrays four lanes at a time into two
    # accumulators. No 105/103 scalar access is left inside either loop.
    assert "VECTORIZED array-fill-loop" in report
    assert "VECTORIZED array-map-loop" in report
    assert "LOWERED 105" not in report
    assert re.search(r"vmovdqu ymmword ptr \[r\d+ \+ r\d+\*8 \+ 8\], ymm1", asm)
    assert "vpsllq ymm4, ymm0, 1" in asm  # a[i] * 3 as (a << 1) + a
    assert "call null_array_zero" in asm
    # 121 SIMD_MUL must stay AVX2: vpmullq is AVX512DQ+VL and traps on an AVX2-only
    # machine, so the lane product is three vpmuludq plus shifts.
    assert "vpmullq" not in asm
    assert "vpmuludq" in asm

    exe = _build(workdir, "array_map")
    run = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    assert run.stdout.strip() == "159999980000000"


def test_index_store_and_array_zero_still_lower(tmp_path, monkeypatch):
    # A single store outside any loop: neither vector pass applies, so the
    # specialised 105/107 lowerings still have to carry it.
    ir = (
        "IR\t1\t4\tscalar\nIR\t107\t\tscalar\nIR\t3\ta\tscalar\n"
        "IR\t2\ta\tscalar\nIR\t1\t2\tscalar\nIR\t1\t42\tscalar\nIR\t105\t\tscalar\nIR\t3\ta\tscalar\n"
        "IR\t2\ta\tscalar\nIR\t1\t2\tscalar\nIR\t103\t\tscalar\n"
        "IR\t30\t\tscalar\nIR\t255\tHALT\tscalar\n"
    )
    workdir, _ = _run_backend(tmp_path, monkeypatch, ir)

    asm = (workdir / "bootstrap" / "program.s").read_text()
    report = (workdir / "bootstrap" / "backend.report").read_text()
    assert "LOWERED 107 fast-array-zero" in report
    assert "LOWERED 105 fast-index-store" in report
    assert "mov qword ptr [rcx + rdx * 8 + 8], rax" in asm

    exe = _build(workdir, "index_store")
    run = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    assert run.stdout.strip() == "42"


def _run_pipeline(tmp_path, monkeypatch, program: str):
    """Lower a Null source program with the self-hosted emitter, then the backend."""
    emitter = NullLangCompiler().compile(
        ModernRustParser().parse((ROOT / "bootstrap" / "emitter.null").read_text())
    )
    backend = NullLangCompiler().compile(
        ModernRustParser().parse((ROOT / "bootstrap" / "native.null").read_text())
    )
    workdir = tmp_path / "run"
    (workdir / "bootstrap").mkdir(parents=True)
    (workdir / "bootstrap" / "input.null").write_text(program)
    monkeypatch.chdir(workdir)

    emitted = NullVM().execute(emitter)
    assert emitted.success, emitted.error
    lowered = NullVM().execute(backend)
    assert lowered.success, lowered.error
    return workdir, lowered


def test_source_array_write_compiles_end_to_end(tmp_path, monkeypatch):
    # `a[i] = x` lowers to CALL set_index, whose checked store the backend now
    # implements; before that the source could not write to an array at all.
    program = "let a = [10, 20, 30];\na[1] = 42;\nprintln(a[0] + a[1] + a[2]);\n"
    workdir, _ = _run_pipeline(tmp_path, monkeypatch, program)

    report = (workdir / "bootstrap" / "backend.report").read_text()
    assert "LOWERED 70 set-index-bounds-checked" in report
    assert "FALLBACK" not in report

    exe = _build(workdir, "array_write")
    run = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    assert run.stdout.strip() == "82"


def test_source_function_call_survives_an_intervening_print(tmp_path, monkeypatch):
    # A function-scoped `let regs` in the backend's fn-definition handler used to
    # overwrite the promoted-register table: the caller's `x` moved into `rdx` and
    # the println between the calls clobbered it, so add(x, 7) returned 8.
    program = (
        "fn add(a: Num, b: Num) -> Num {\n"
        "    return a + b;\n"
        "}\n"
        "let x = 0;\n"
        "let i = 0;\n"
        "while i < 10 {\n"
        "    x = x + i;\n"
        "    i = i + 1;\n"
        "}\n"
        "println(x);\n"
        "println(add(x, 7));\n"
    )
    workdir, _ = _run_pipeline(tmp_path, monkeypatch, program)

    exe = _build(workdir, "call_after_print")
    run = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    assert run.stdout.split() == ["45", "52"]


def test_source_string_runtime_matches_the_vm(tmp_path, monkeypatch):
    # Literals, print, LEN, ==/!=, +, CHAR_AT, ORD and READ_FILE all lower to the
    # byte-oriented string runtime instead of trapping.
    program = (
        'let s = "abc";\n'
        "println(s);\n"
        "println(LEN(s));\n"
        "println(CHAR_AT(s, 1));\n"
        'println(s + "def");\n'
        'println(CHAR_AT(s, 1) == "b");\n'
        'println(CHAR_AT(s, 1) != "b");\n'
        'println(ORD("A"));\n'
        'let t = READ_FILE("bootstrap/notes.txt");\n'
        "println(t);\n"
        "println(LEN(t));\n"
    )
    workdir, _ = _run_pipeline(tmp_path, monkeypatch, program)
    (workdir / "bootstrap" / "notes.txt").write_text("hello\n")

    report = (workdir / "bootstrap" / "backend.report").read_text()
    assert "LOWERED 70 len-string" in report
    assert "LOWERED 10 str-concat" in report
    assert "LOWERED 70 char_at" in report
    assert "LOWERED 70 read_file" in report
    assert "FALLBACK" not in report

    exe = _build(workdir, "strings")
    run = subprocess.run(
        [str(exe)], capture_output=True, text=True, check=True, cwd=workdir
    )
    # string comparisons yield booleans, printed the way the VM prints them
    assert run.stdout.splitlines() == [
        "abc",
        "3",
        "b",
        "abcdef",
        "true",
        "false",
        "65",
        "hello",
        "",
        "6",
    ]


def test_source_append_grows_the_array(tmp_path, monkeypatch):
    # 106 doubles the capacity from 0 to 4, 8 and 16 while ten values are pushed.
    program = (
        "let a = [];\n"
        "let i = 0;\n"
        "while i < 10 {\n"
        "    a = APPEND(a, i);\n"
        "    i = i + 1;\n"
        "}\n"
        "println(a[9]);\n"
    )
    workdir, _ = _run_pipeline(tmp_path, monkeypatch, program)

    report = (workdir / "bootstrap" / "backend.report").read_text()
    assert "LOWERED 106 fast-array-push" in report
    assert "FALLBACK" not in report

    exe = _build(workdir, "array_push")
    run = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    assert run.stdout.strip() == "9"


def test_source_array_write_past_the_end_traps(tmp_path, monkeypatch):
    program = "let a = [1, 2];\na[5] = 9;\nprintln(a[0]);\n"
    workdir, _ = _run_pipeline(tmp_path, monkeypatch, program)

    exe = _build(workdir, "array_oob")
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    assert run.returncode == 3  # null_panic_oob
    assert run.stdout.strip() == ""


def test_source_division_by_zero_reports_instead_of_trapping(tmp_path, monkeypatch):
    # An unguarded idiv raised SIGFPE (exit 136) with no output. The divisor is
    # checked before every idiv, including `mod`, and routes to a shared panic
    # stub that writes a message and exits 5.
    program = "let zero = 0;\nprintln(10 / zero);\n"
    workdir, _ = _run_pipeline(tmp_path, monkeypatch, program)

    asm = (workdir / "bootstrap" / "program.s").read_text()
    assert "je null_panic_divzero" in asm
    assert ".Ldivzero: .ascii \"DIVISION BY ZERO!!!\\n\"" in asm
    exe = _build(workdir, "divzero")
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    assert run.returncode == 5
    assert run.stdout.strip() == ""
    assert "DIVISION BY ZERO!!!" in run.stderr


def _array_map_ir(bound: int, cmp_op: int = 21) -> str:
    """`a[i] = i; b[i] = i*2` then `total += a[i]*3 + b[i]`, as super-bit IR.

    Both arrays are allocated eight elements longer than the bound so the `<=`
    form can read one past the last filled element without leaving the array.
    """
    return (
        "IR\t1\t0\tscalar\n"
        "IR\t3\ttotal\tscalar\n"
        "IR\t1\t0\tscalar\n"
        "IR\t3\ti\tscalar\n"
        f"IR\t1\t{bound}\tscalar\n"
        "IR\t3\tlimit\tscalar\n"
        "IR\t2\tlimit\tscalar\n"
        "IR\t1\t8\tscalar\n"
        "IR\t100\t\tscalar\n"
        "IR\t107\t\tscalar\n"
        "IR\t3\ta\tscalar\n"
        "IR\t2\tlimit\tscalar\n"
        "IR\t1\t8\tscalar\n"
        "IR\t100\t\tscalar\n"
        "IR\t107\t\tscalar\n"
        "IR\t3\tb\tscalar\n"
        "LABEL\tfill\n"
        "IR\t2\ti\tscalar\n"
        "IR\t2\tlimit\tscalar\n"
        f"IR\t{cmp_op}\t\tscalar\n"
        "IR\t40\tafter_fill\tscalar\n"
        "IR\t2\ta\tscalar\n"
        "IR\t2\ti\tscalar\n"
        "IR\t2\ti\tscalar\n"
        "IR\t105\t\tscalar\n"
        "IR\t3\ta\tscalar\n"
        "IR\t2\tb\tscalar\n"
        "IR\t2\ti\tscalar\n"
        "IR\t2\ti\tscalar\n"
        "IR\t1\t2\tscalar\n"
        "IR\t12\t\tscalar\n"
        "IR\t105\t\tscalar\n"
        "IR\t3\tb\tscalar\n"
        "IR\t2\ti\tscalar\n"
        "IR\t1\t1\tscalar\n"
        "IR\t100\t\tscalar\n"
        "IR\t3\ti\tscalar\n"
        "IR\t41\tfill\tscalar\n"
        "LABEL\tafter_fill\n"
        "IR\t1\t0\tscalar\n"
        "IR\t3\ti\tscalar\n"
        "LABEL\tsum\n"
        "IR\t2\ti\tscalar\n"
        "IR\t2\tlimit\tscalar\n"
        f"IR\t{cmp_op}\t\tscalar\n"
        "IR\t40\tafter_sum\tscalar\n"
        "IR\t2\ttotal\tscalar\n"
        "IR\t2\ta\tscalar\n"
        "IR\t2\ti\tscalar\n"
        "IR\t103\t\tscalar\n"
        "IR\t1\t3\tscalar\n"
        "IR\t12\t\tscalar\n"
        "IR\t2\tb\tscalar\n"
        "IR\t2\ti\tscalar\n"
        "IR\t103\t\tscalar\n"
        "IR\t100\t\tscalar\n"
        "IR\t100\t\tscalar\n"
        "IR\t3\ttotal\tscalar\n"
        "IR\t2\ti\tscalar\n"
        "IR\t1\t1\tscalar\n"
        "IR\t100\t\tscalar\n"
        "IR\t3\ti\tscalar\n"
        "IR\t41\tsum\tscalar\n"
        "LABEL\tafter_sum\n"
        "IR\t2\ttotal\tscalar\n"
        "IR\t30\t\tscalar\n"
        "IR\t255\tHALT\tscalar\n"
    )


@pytest.mark.parametrize(
    "bound, cmp_op",
    [
        (5, 21),   # tail only, both loops
        (8, 21),   # exactly one fill window and one map window
        (9, 21),   # one window plus one tail element each
        (13, 21),  # one map window + 5 tail elements
        (21, 21),  # two map windows + tail
        (16, 25),  # `<=` form: one extra element
        (5, 25),   # `<=` tail only
    ],
)
def test_array_map_vector_tail_is_exact(tmp_path, monkeypatch, bound, cmp_op):
    workdir, _ = _run_backend(tmp_path, monkeypatch, _array_map_ir(bound, cmp_op))
    exe = _build(workdir, f"array_{bound}_{cmp_op}")
    run = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    last = bound - 1 if cmp_op == 21 else bound
    assert run.stdout.strip() == str(5 * sum(range(last + 1)))


def test_modulo_by_power_of_two_becomes_a_bit_test(tmp_path, monkeypatch):
    # The emitter spells `x % 2 == 0` as `x - (x / 2) * 2 == 0`, because `%` is
    # not a lexer token yet; the backend recognises it as a bit test even when the
    # loop has no vector form (the comprehension loop is vectorised instead).
    workdir, _ = _run_backend(tmp_path, monkeypatch, _filtered_sum_ir(2000))

    asm = (workdir / "bootstrap" / "program.s").read_text()
    report = (workdir / "bootstrap" / "backend.report").read_text()
    assert "idiv" not in asm
    assert re.search(r"^  test r\d+, 1$", asm, re.M)
    assert "pow2-branch" in report
    assert "VECTORIZED filtered-square-loop" not in report

    exe = _build(workdir, "mod_pow2")
    run = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    assert run.stdout.strip() == str(sum(x for x in range(2, 2001, 2)))


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


def _filtered_square_ir(n, cmp_op=25):
    """`total = 0; x = 1; while x <cmp_op> n { if x - (x/2)*2 == 0 { total = total + x*x }; x = x + 1 }`

    Same row shape bootstrap/emitter.null produces for the comprehension workload.
    """
    return (
        f"IR\t1\t{n}\tscalar\n"
        "IR\t3\tn\tscalar\n"
        "IR\t1\t0\tscalar\n"
        "IR\t3\ttotal\tscalar\n"
        "IR\t1\t1\tscalar\n"
        "IR\t3\tx\tscalar\n"
        "LABEL\tL_s3_start\n"
        "IR\t2\tx\tscalar\n"
        "IR\t2\tn\tscalar\n"
        f"IR\t{cmp_op}\t\tscalar\n"
        "IR\t40\tL_s3_end\tcontrol\n"
        "IR\t2\tx\tscalar\n"
        "IR\t2\tx\tscalar\n"
        "IR\t1\t2\tscalar\n"
        "IR\t13\t\tscalar\n"
        "IR\t1\t2\tscalar\n"
        "IR\t12\t\tscalar\n"
        "IR\t11\t\tscalar\n"
        "IR\t1\t0\tscalar\n"
        "IR\t22\t\tscalar\n"
        "IR\t40\tL_s3.b.0_else\tcontrol\n"
        "IR\t2\ttotal\tscalar\n"
        "IR\t2\tx\tscalar\n"
        "IR\t2\tx\tscalar\n"
        "IR\t12\t\tscalar\n"
        "IR\t10\t\tscalar\n"
        "IR\t3\ttotal\tscalar\n"
        "IR\t41\tL_s3.b.0_end\tcontrol\n"
        "LABEL\tL_s3.b.0_else\n"
        "LABEL\tL_s3.b.0_end\n"
        "IR\t2\tx\tscalar\n"
        "IR\t1\t1\tscalar\n"
        "IR\t10\t\tscalar\n"
        "IR\t3\tx\tscalar\n"
        "IR\t41\tL_s3_start\tcontrol\n"
        "LABEL\tL_s3_end\n"
        "IR\t2\ttotal\tscalar\n"
        "IR\t30\t\tscalar\n"
        "IR\t255\tHALT\tscalar\n"
    )


def _filtered_sum_ir(n, cmp_op=25):
    """`while x <cmp_op> n { if x - (x/2)*2 == 0 { total = total + x }; x = x + 1 }`.

    Same filter as the comprehension workload but a plain accumulate body, which
    the vector pass does not handle, so the `test`/`jne` lowering is what is left.
    """
    return (
        f"IR\t1\t{n}\tscalar\n"
        "IR\t3\tn\tscalar\n"
        "IR\t1\t0\tscalar\n"
        "IR\t3\ttotal\tscalar\n"
        "IR\t1\t1\tscalar\n"
        "IR\t3\tx\tscalar\n"
        "LABEL\tL_s3_start\n"
        "IR\t2\tx\tscalar\n"
        "IR\t2\tn\tscalar\n"
        f"IR\t{cmp_op}\t\tscalar\n"
        "IR\t40\tL_s3_end\tcontrol\n"
        "IR\t2\tx\tscalar\n"
        "IR\t2\tx\tscalar\n"
        "IR\t1\t2\tscalar\n"
        "IR\t13\t\tscalar\n"
        "IR\t1\t2\tscalar\n"
        "IR\t12\t\tscalar\n"
        "IR\t11\t\tscalar\n"
        "IR\t1\t0\tscalar\n"
        "IR\t22\t\tscalar\n"
        "IR\t40\tL_s3.b.0_else\tcontrol\n"
        "IR\t2\ttotal\tscalar\n"
        "IR\t2\tx\tscalar\n"
        "IR\t10\t\tscalar\n"
        "IR\t3\ttotal\tscalar\n"
        "IR\t41\tL_s3.b.0_end\tcontrol\n"
        "LABEL\tL_s3.b.0_else\n"
        "LABEL\tL_s3.b.0_end\n"
        "IR\t2\tx\tscalar\n"
        "IR\t1\t1\tscalar\n"
        "IR\t10\t\tscalar\n"
        "IR\t3\tx\tscalar\n"
        "IR\t41\tL_s3_start\tcontrol\n"
        "LABEL\tL_s3_end\n"
        "IR\t2\ttotal\tscalar\n"
        "IR\t30\t\tscalar\n"
        "IR\t255\tHALT\tscalar\n"
    )


def test_filtered_reduction_is_vectorised(tmp_path, monkeypatch):
    ir = (ROOT / "bench" / "ir" / "comprehension.ir").read_text()
    workdir, _ = _run_backend(tmp_path, monkeypatch, ir)

    asm = (workdir / "bootstrap" / "program.s").read_text()
    report = (workdir / "bootstrap" / "backend.report").read_text()
    assert "VECTORIZED filtered-square-loop" in report
    # lane parity is a compare against zero after masking, and the second window is
    # iota + 4 per lane so no two lanes hold the same value
    assert "vpcmpeqq" in asm
    assert asm.count("vpmuludq") >= 4
    # the scalar tail still runs (and still skips odd values with a bit test)
    assert "and rax, 1" in asm

    exe = _build(workdir, "comprehension_vec")
    run = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    assert run.stdout.strip() == str(sum(x * x for x in range(2, 20000001, 2)) % 2**64)


@pytest.mark.parametrize(
    "n, cmp_op, expected",
    [
        (5, 25, 4 + 16),            # tail only
        (8, 25, 4 + 16 + 36 + 64),  # exactly one vector window
        (9, 25, 4 + 16 + 36 + 64),  # one window + an odd tail iteration
        (13, 25, 4 + 16 + 36 + 64 + 100 + 144),  # one window + 5 tail iterations
        (21, 25, sum(x * x for x in range(2, 22, 2))),  # two windows + tail
        (16, 21, sum(x * x for x in range(2, 15, 2))),  # `<` form: x stops at n-1
    ],
)
def test_filtered_reduction_tail_is_exact(tmp_path, monkeypatch, n, cmp_op, expected):
    workdir, _ = _run_backend(tmp_path, monkeypatch, _filtered_square_ir(n, cmp_op))
    exe = _build(workdir, f"filtered_{n}_{cmp_op}")
    run = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    assert run.stdout.strip() == str(expected)


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


def test_native_logical_operators_are_not_equality(tmp_path, monkeypatch):
    # `&&` and `||` once had no opcode of their own, so the emitter's cmp_op fell
    # through to its `==` default and every logical operator compiled to equality.
    # The VM-only test above could not see it: it never runs the native backend.
    program = (
        "let x = 5;\n"
        "println(false || true);\n"
        "println(true || false);\n"
        "println(true && false);\n"
        "println(true && true);\n"
        "if x > 1 || x > 9 {\n    println(\"or\");\n}\n"
        "if x > 1 && x > 9 {\n    println(\"and-bad\");\n}\n"
        "if x > 1 && x < 9 {\n    println(\"and\");\n}\n"
    )
    workdir, _ = _run_pipeline(tmp_path, monkeypatch, program)

    ir = (workdir / "bootstrap" / "program.ir").read_text()
    assert "IR\t26\t" in ir, "AND must lower to its own opcode"
    assert "IR\t27\t" in ir, "OR must lower to its own opcode"

    report = (workdir / "bootstrap" / "backend.report").read_text()
    assert "FALLBACK" not in report

    exe = _build(workdir, "logic")
    native = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    expected = ["true", "true", "false", "true", "or", "and"]
    assert native.stdout.splitlines() == expected

    vm = NullVM().execute(NullLangCompiler().compile(ModernRustParser().parse(program)))
    assert vm.success, vm.error
    assert native.stdout.splitlines() == vm.output


def test_boolean_results_print_like_the_vm(tmp_path, monkeypatch):
    # Comparisons now carry the `bool` type through stores, parameters and
    # returns, so print formats them as true/false instead of 1/0. The VM is the
    # reference: both pipelines must produce the same lines.
    program = (
        "fn greater(a: Num, b: Num) -> Bool {\n"
        "    return a > b;\n"
        "}\n"
        "println(greater(2, 1));\n"
        "println(greater(1, 2));\n"
        "let flag = 3 == 3;\n"
        "println(flag);\n"
        "println(flag != false);\n"
    )
    workdir, _ = _run_pipeline(tmp_path, monkeypatch, program)

    report = (workdir / "bootstrap" / "backend.report").read_text()
    assert "FALLBACK" not in report

    exe = _build(workdir, "bools")
    native = subprocess.run([str(exe)], capture_output=True, text=True, check=True)
    assert native.stdout.splitlines() == ["true", "false", "true", "true"]

    vm = NullVM().execute(NullLangCompiler().compile(ModernRustParser().parse(program)))
    assert vm.success, vm.error
    assert native.stdout.splitlines() == vm.output


def test_native_stage1_lexer_matches_the_vm(tmp_path, monkeypatch):
    # The stage-1 lexer compiled by the native backend must tokenise exactly like
    # the same lexer on the VM. This needs the declared parameter/return types
    # (`Array` element types for `ident[0]`, `ident[1]`, `text[0]`) to survive the
    # call boundary, and bool printing for `is_*` results.
    lexer = (ROOT / "bootstrap" / "lexer.null").read_text()
    workdir, _ = _run_pipeline(tmp_path, monkeypatch, lexer)

    report = (workdir / "bootstrap" / "backend.report").read_text()
    assert "FALLBACK" not in report

    sample = (
        "fn add(a: Num, b: Num) -> Num {\n"
        "    return a + b; // doubles\n"
        "}\n"
        "let label = \"a\\\"b\";\n"
        "SET legacy TO 7\n"
        "if a != b { println(label); }\n"
    )
    (workdir / "bootstrap" / "input.null").write_text(sample)

    exe = _build(workdir, "lexer")
    native = subprocess.run(
        [str(exe)], capture_output=True, text=True, check=True
    ).stdout.splitlines()

    vm = NullVM().execute(NullLangCompiler().compile(ModernRustParser().parse(lexer)))
    assert vm.success, vm.error
    assert native == vm.output
    assert "PUNCT ->" in native and "STRING a\"b" in native


def test_native_string_builtins_match_the_vm(tmp_path, monkeypatch):
    # SPLIT/JOIN/SUBSTR/TO_STRING/TO_NUMBER/SLICE/CONTAINS/WRITE_FILE/FILE_EXISTS
    # all lower to the byte-oriented runtime; the VM is the reference for values
    # and for the file the write leaves behind.
    program = (
        'let parts = SPLIT("a,b,c", ",");\n'
        "println(LEN(parts));\n"
        'println(JOIN(parts, "-"));\n'
        'println(SUBSTR("abcdef", 1, 4));\n'
        "println(TO_STRING(42));\n"
        "println(TO_STRING(true));\n"
        'println(TO_NUMBER("123"));\n'
        "let nums = [10, 20, 30, 40];\n"
        "let mid = SLICE(nums, 1, 3);\n"
        "println(LEN(mid));\n"
        "println(mid[0] + mid[1]);\n"
        'println(CONTAINS("hello world", "lo w"));\n'
        'println(FILE_EXISTS("bootstrap/input.null"));\n'
        'WRITE_FILE("bootstrap/out.txt", "written");\n'
        'println(READ_FILE("bootstrap/out.txt"));\n'
    )
    workdir, _ = _run_pipeline(tmp_path, monkeypatch, program)

    report = (workdir / "bootstrap" / "backend.report").read_text()
    assert "FALLBACK" not in report
    for builtin in (
        "split", "join", "substr", "to_string", "to_number",
        "slice", "contains", "write_file", "file_exists",
    ):
        assert f"LOWERED 70 {builtin}" in report

    exe = _build(workdir, "builtins")
    native = subprocess.run(
        [str(exe)], capture_output=True, text=True, check=True, cwd=workdir
    ).stdout.splitlines()

    vm = NullVM().execute(NullLangCompiler().compile(ModernRustParser().parse(program)))
    assert vm.success, vm.error
    assert native == vm.output
    assert (workdir / "bootstrap" / "out.txt").read_text() == "written"


def test_break_and_continue_resolve_to_loop_labels(tmp_path, monkeypatch):
    # A `break` used to stay a jump to `__break__`, which no stage resolved: the
    # VM ignored it and a native link failed on the missing label.
    program = (
        "let i = 0;\n"
        "let acc = 0;\n"
        "while i < 10 {\n"
        "    i = i + 1;\n"
        "    if i == 3 { continue; }\n"
        "    if i == 6 { break; }\n"
        "    acc = acc + i;\n"
        "}\n"
        "println(acc);\n"
    )
    workdir, _ = _run_pipeline(tmp_path, monkeypatch, program)

    ir = (workdir / "bootstrap" / "program.ir").read_text()
    assert "__break__" not in ir and "__continue__" not in ir

    exe = _build(workdir, "break_continue")
    native = subprocess.run(
        [str(exe)], capture_output=True, text=True, check=True, cwd=workdir
    ).stdout.splitlines()

    vm = NullVM().execute(NullLangCompiler().compile(ModernRustParser().parse(program)))
    assert vm.success, vm.error
    assert native == vm.output == ["12"]
