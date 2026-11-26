"""Tests for the third self-hosted stage (bootstrap/ir.null).

The Null-side IR must agree with the authoritative Python opcode table, because
both backends consume the same stream.
"""

from pathlib import Path

from null_system.lang.compiler import NullLangCompiler
from null_system.lang.modern.modern_rust import ModernRustParser
from null_system.superbit.ir import SuperBitOpCode
from null_system.vm.vm import NullVM

ROOT = Path(__file__).resolve().parents[2]

EXPECTED = [
    "IR 1 2 @scalar",
    "IR 1 3 @scalar",
    "IR 10  @scalar",
    "IR 30  @scalar",
    "IR 113 x*x @simd",
    "IR 130 matmul @gpu requires=superbit prefers=gpu",
    "fast -> generic: 70",
]


def _run_ir_stage() -> list[str]:
    source = (ROOT / "bootstrap" / "ir.null").read_text()
    stream = NullLangCompiler().compile(ModernRustParser().parse(source))
    result = NullVM().execute(stream)
    assert result.success, result.error
    return result.output


def test_ir_stage_emits_annotated_superbit_tokens():
    assert _run_ir_stage() == EXPECTED


def test_ir_opcode_numbers_match_the_python_table():
    from null_system.superbit import ir as py_ir

    table = {
        "LOAD_CONST": 1,
        "LOAD_VAR": 2,
        "STORE_VAR": 3,
        "BINARY_ADD": 10,
        "BINARY_SUB": 11,
        "BINARY_MUL": 12,
        "BINARY_DIV": 13,
        "COMPARE_GT": 20,
        "COMPARE_LT": 21,
        "COMPARE_EQ": 22,
        "COMPARE_NE": 23,
        "COMPARE_GE": 24,
        "COMPARE_LE": 25,
        "PRINT": 30,
        "INPUT": 31,
        "FILE_READ": 32,
        "FILE_WRITE": 33,
        "FILE_EXISTS": 34,
        "LIST_FILES": 35,
        "JUMP_IF_FALSE": 40,
        "JUMP": 41,
        "MATCH_TAG": 50,
        "UNWRAP_UNION": 51,
        "MATCH_PATTERN": 52,
        "SAFE_CALL": 60,
        "ELVIS_CHECK": 61,
        "NOT_NULL_CHECK": 62,
        "SMART_CAST": 63,
        "CALL": 70,
        "RETURN": 71,
        "ARRAY": 72,
        "INDEX": 73,
        "FUNCTION": 74,
        "NOP": 255,
    }
    for name, value in table.items():
        assert int(SuperBitOpCode[name]) == value
    assert py_ir is not None
