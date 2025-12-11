"""Super-bit token definitions."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, List


class SuperBitOpCode(Enum):
    """Super-bit operation codes."""
    LOAD_CONST = auto()
    LOAD_VAR = auto()
    STORE_VAR = auto()
    BINARY_ADD = auto()
    BINARY_SUB = auto()
    BINARY_MUL = auto()
    BINARY_DIV = auto()
    COMPARE_GT = auto()
    COMPARE_LT = auto()
    COMPARE_EQ = auto()
    PRINT = auto()
    JUMP_IF_FALSE = auto()
    JUMP = auto()
    NOP = auto()


@dataclass
class SuperBitToken:
    """A single super-bit instruction token."""
    opcode: SuperBitOpCode
    operand: Any = None
    
    def to_bytes(self) -> bytes:
        """Convert token to bytes."""
        opcode_byte = self.opcode.value.to_bytes(1, 'big')
        
        if self.operand is None:
            return opcode_byte
        
        if isinstance(self.operand, int):
            return opcode_byte + self.operand.to_bytes(4, 'big', signed=True)
        elif isinstance(self.operand, float):
            import struct
            return opcode_byte + struct.pack('d', self.operand)
        elif isinstance(self.operand, str):
            operand_bytes = self.operand.encode('utf-8')
            length = len(operand_bytes)
            return opcode_byte + length.to_bytes(2, 'big') + operand_bytes
        else:
            return opcode_byte


@dataclass
class SuperBitStream:
    """A stream of super-bit tokens."""
    tokens: List[SuperBitToken]
    
    def to_bytes(self) -> bytes:
        """Convert entire stream to bytes."""
        result = b''
        for token in self.tokens:
            result += token.to_bytes()
        return result
    
    def __repr__(self) -> str:
        """String representation."""
        lines = []
        for i, token in enumerate(self.tokens):
            operand_str = f", {token.operand}" if token.operand is not None else ""
            lines.append(f"  {i:04d}: {token.opcode.name}{operand_str}")
        return "\n".join(lines)
