"""Super-bit IR (intermediate representation) for the compiler/VM pipeline.

This is distinct from the bit-level Super-Bit encoding layer implemented in
`null_system.superbit.tokens`.

The compiler pipeline emits opcode/operand tokens that are executed by the
Python NullVM and serialized into the binary frame code section.

Layer Annotation Metadata
=========================

The compiler threads layer annotation metadata into each SuperBitIRToken via the
`metadata` dictionary. This metadata allows downstream tooling (VMs, debuggers,
profilers) to route instructions to specific execution layers.

Metadata Keys:
- 'layer' (str): Name of the layer this instruction executes on (e.g., 'binary', 'superbit')
- 'requires' (list[str]): List of layers that must be available for this instruction
- 'prefers' (list[str]): List of preferred/optimized layers for this instruction
- 'source_layer_line' (int): Source line number where layer annotation appeared

Example:
    token = SuperBitIRToken(
        opcode=SuperBitOpCode.LOAD_CONST,
        operand=42,
        metadata={'layer': 'binary', 'requires': ['superbit']}
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Iterable, List, Optional


class SuperBitOpCode(IntEnum):
    LOAD_CONST = 1
    LOAD_VAR = 2
    STORE_VAR = 3

    BINARY_ADD = 10
    BINARY_SUB = 11
    BINARY_MUL = 12
    BINARY_DIV = 13

    COMPARE_GT = 20
    COMPARE_LT = 21
    COMPARE_EQ = 22

    PRINT = 30
    INPUT = 31
    FILE_READ = 32
    FILE_WRITE = 33
    FILE_EXISTS = 34
    LIST_FILES = 35

    JUMP_IF_FALSE = 40
    JUMP = 41

    MATCH_TAG = 50
    UNWRAP_UNION = 51
    MATCH_PATTERN = 52
    
    SAFE_CALL = 60
    ELVIS_CHECK = 61
    NOT_NULL_CHECK = 62
    SMART_CAST = 63

    NOP = 255


@dataclass(frozen=True)
class SuperBitIRToken:
    opcode: SuperBitOpCode
    operand: Any = None
    source_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_bytes(self) -> bytes:
        payload = self._encode_operand(self.operand)
        return bytes([int(self.opcode)]) + payload

    @staticmethod
    def _encode_operand(operand: Any) -> bytes:
        if operand is None:
            return b"\x00"

        if isinstance(operand, bool):
            return b"\x01" + (b"\x01" if operand else b"\x00")

        if isinstance(operand, int) and not isinstance(operand, bool):
            return b"\x02" + int(operand).to_bytes(4, "big", signed=True)

        if isinstance(operand, float):
            import struct

            return b"\x03" + struct.pack(">d", float(operand))

        if isinstance(operand, str):
            data = operand.encode("utf-8")
            if len(data) > 255:
                raise ValueError("String operand too long")
            return b"\x04" + bytes([len(data)]) + data

        raise TypeError(f"Unsupported operand type: {type(operand)}")


@dataclass(frozen=True)
class SuperBitStream:
    tokens: List[SuperBitIRToken]

    def __iter__(self) -> Iterable[SuperBitIRToken]:
        return iter(self.tokens)

    def to_bytes(self) -> bytes:
        return b"".join(t.to_bytes() for t in self.tokens)

    def token_bytes(self) -> List[bytes]:
        return [t.to_bytes() for t in self.tokens]
