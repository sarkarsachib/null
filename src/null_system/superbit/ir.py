"""Super-bit IR (intermediate representation) for the compiler/VM pipeline.

This is distinct from the bit-level Super-Bit encoding layer implemented in
`null_system.superbit.tokens`.

The compiler pipeline emits opcode/operand tokens that are executed by the
Python NullVM and serialized into the binary frame code section.
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

    JUMP_IF_FALSE = 40
    JUMP = 41

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
