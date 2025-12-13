"""Super-Bit tokens and groups for compact binary encoding.

This module defines the fundamental data structures for Super-Bit encoding:
- SuperBitToken: Atomic units representing symbols or data
- SuperBitGroup: 4-8 bit containers for tokens or packed data
- SuperBitOpCode: Operation codes for the virtual machine
- SuperBitStream: Stream container for tokens
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union
import struct
from enum import Enum


class SuperBitOpCode(str, Enum):
    """Operation codes for the Super-Bit virtual machine."""
    LOAD_CONST = "LOAD_CONST"
    LOAD_VAR = "LOAD_VAR"
    STORE_VAR = "STORE_VAR"
    BINARY_ADD = "BINARY_ADD"
    BINARY_SUB = "BINARY_SUB"
    BINARY_MUL = "BINARY_MUL"
    BINARY_DIV = "BINARY_DIV"
    COMPARE_GT = "COMPARE_GT"
    COMPARE_LT = "COMPARE_LT"
    COMPARE_EQ = "COMPARE_EQ"
    JUMP = "JUMP"
    JUMP_IF_FALSE = "JUMP_IF_FALSE"
    PRINT = "PRINT"
    NOP = "NOP"


@dataclass
class SuperBitToken:
    """An atomic unit in the Super-Bit encoding system.

    Represents a single symbol, command, or data value with variable bit width.
    Can be created with either (symbol, bits, bit_width) or (opcode, [operand]).
    """

    opcode: Union[str, SuperBitOpCode]
    operand: Optional[Union[int, str, object]] = None
    metadata: Optional[dict] = None

    @property
    def symbol(self) -> str:
        """Get symbol/opcode name."""
        if isinstance(self.opcode, SuperBitOpCode):
            return self.opcode.value
        return str(self.opcode)

    @property
    def bits(self) -> int:
        """Get operand bits (for compatibility)."""
        if isinstance(self.operand, int):
            return self.operand
        return 0

    @property
    def bit_width(self) -> int:
        """Get bit width (for compatibility)."""
        if isinstance(self.operand, int):
            return (self.operand.bit_length() or 1)
        return 0

    def to_bytes(self) -> bytes:
        """Serialize token to bytes.

        Returns a variable-length byte representation suitable for streaming.
        """
        opcode_str = self.symbol
        opcode_bytes = opcode_str.encode("utf-8")
        data = struct.pack(">H", len(opcode_bytes)) + opcode_bytes
        
        if self.operand is not None:
            if isinstance(self.operand, (int, float)):
                data += struct.pack(">B", 1) + struct.pack(">Q", int(self.operand))
            elif isinstance(self.operand, str):
                operand_bytes = self.operand.encode("utf-8")
                data += struct.pack(">B", 2) + struct.pack(">H", len(operand_bytes)) + operand_bytes
            else:
                data += struct.pack(">B", 0)
        else:
            data += struct.pack(">B", 0)
        
        return data

    @staticmethod
    def from_bytes(data: bytes) -> tuple["SuperBitToken", int]:
        """Deserialize token from bytes.

        Returns:
            Tuple of (SuperBitToken, bytes_consumed)
        """
        if len(data) < 3:
            raise ValueError("Token requires at least 3 bytes")
        
        opcode_len = struct.unpack(">H", data[:2])[0]
        offset = 2
        
        if offset + opcode_len + 1 > len(data):
            raise ValueError("Incomplete token")
        
        opcode_str = data[offset:offset+opcode_len].decode("utf-8")
        offset += opcode_len
        
        operand_type = data[offset]
        offset += 1
        
        operand = None
        if operand_type == 1:
            if offset + 8 > len(data):
                raise ValueError("Incomplete operand")
            operand = struct.unpack(">Q", data[offset:offset+8])[0]
            offset += 8
        elif operand_type == 2:
            if offset + 2 > len(data):
                raise ValueError("Incomplete operand length")
            operand_len = struct.unpack(">H", data[offset:offset+2])[0]
            offset += 2
            if offset + operand_len > len(data):
                raise ValueError("Incomplete operand")
            operand = data[offset:offset+operand_len].decode("utf-8")
            offset += operand_len
        
        token = SuperBitToken(opcode_str, operand)
        return token, offset

    def __repr__(self) -> str:
        return f"SuperBitToken({self.symbol!r}, operand={self.operand!r})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, SuperBitToken):
            return False
        return (
            self.opcode == other.opcode
            and self.operand == other.operand
        )


@dataclass
class SuperBitGroup:
    """A 4-8 bit container for Super-Bit tokens or packed data.

    Groups multiple tokens into efficient bit patterns, supporting both
    discrete tokens and packed numerical data.
    """

    tokens: List[SuperBitToken]
    total_bits: int
    group_id: Optional[int] = None
    compression_hint: Optional[str] = None
    encryption_hint: Optional[str] = None

    @property
    def is_full(self) -> bool:
        """Check if group is at maximum capacity (8 bits)."""
        return self.total_bits >= 8

    @property
    def remaining_bits(self) -> int:
        """Get remaining bits available in group."""
        return max(0, 8 - self.total_bits)

    def add_token(self, token: SuperBitToken) -> bool:
        """Add token to group if it fits.

        Returns:
            True if token was added, False if not enough space
        """
        if self.total_bits + token.bit_width <= 8:
            self.tokens.append(token)
            self.total_bits += token.bit_width
            return True
        return False

    def to_byte(self) -> int:
        """Pack tokens into a single byte (0-255).

        Returns the byte representation if total_bits <= 8.

        Raises:
            ValueError: If group exceeds 8 bits
        """
        if self.total_bits > 8:
            raise ValueError(f"Group exceeds 8 bits: {self.total_bits}")
        result = 0
        shift = 8
        for token in self.tokens:
            shift -= token.bit_width
            result |= (token.bits & ((1 << token.bit_width) - 1)) << shift
        return result

    @staticmethod
    def from_byte(
        byte_value: int,
        token_format: List[int],
        registry: Optional["SymbolRegistry"] = None,
    ) -> "SuperBitGroup":
        """Unpack tokens from a single byte using a token format.

        Args:
            byte_value: The byte to unpack (0-255)
            token_format: List of bit widths for each token
            registry: Optional SymbolRegistry for token lookup

        Returns:
            SuperBitGroup with unpacked tokens
        """
        from . import registry as reg_module

        if registry is None:
            registry = reg_module.get_default_registry()

        tokens = []
        total_bits = 0
        shift = 8
        for bit_width in token_format:
            shift -= bit_width
            bits = (byte_value >> shift) & ((1 << bit_width) - 1)
            # Try to resolve symbol from registry
            symbol = registry.lookup_by_bits(bits, bit_width) or f"0x{bits:b}"
            token = SuperBitToken(symbol, bits, bit_width)
            tokens.append(token)
            total_bits += bit_width

        return SuperBitGroup(tokens, total_bits)

    def to_bytes(self) -> bytes:
        """Serialize group to bytes."""
        data = struct.pack("B", self.total_bits)
        data += struct.pack("B", len(self.tokens))
        for token in self.tokens:
            data += token.to_bytes()
        if self.compression_hint:
            hint_bytes = self.compression_hint.encode("utf-8")
            data += struct.pack("B", len(hint_bytes)) + hint_bytes
        if self.encryption_hint:
            hint_bytes = self.encryption_hint.encode("utf-8")
            data += struct.pack("B", len(hint_bytes)) + hint_bytes
        return data

    @staticmethod
    def from_bytes(data: bytes) -> tuple["SuperBitGroup", int]:
        """Deserialize group from bytes.

        Returns:
            Tuple of (SuperBitGroup, bytes_consumed)
        """
        if len(data) < 2:
            raise ValueError("Group requires at least 2 bytes")
        total_bits = data[0]
        token_count = data[1]
        offset = 2
        tokens = []
        for _ in range(token_count):
            if offset >= len(data):
                raise ValueError("Incomplete group token")
            token, bytes_consumed = SuperBitToken.from_bytes(data[offset:])
            tokens.append(token)
            offset += bytes_consumed

        group = SuperBitGroup(tokens, total_bits)
        # Parse hints if present (simplified - full implementation would continue parsing)
        return group, offset

    def __repr__(self) -> str:
        return f"SuperBitGroup(bits={self.total_bits}/8, tokens={len(self.tokens)})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, SuperBitGroup):
            return False
        return (
            self.tokens == other.tokens
            and self.total_bits == other.total_bits
        )


@dataclass
class SuperBitStream:
    """A stream of super-bit tokens for execution.
    
    Represents a compiled program as a sequence of tokens.
    """
    
    tokens: List[SuperBitToken] = field(default_factory=list)
    metadata: Optional[dict] = None
    
    def to_bytes(self) -> bytes:
        """Serialize stream to bytes."""
        data = struct.pack(">I", len(self.tokens))
        for token in self.tokens:
            token_bytes = self._token_to_bytes(token)
            data += token_bytes
        return data
    
    @staticmethod
    def _token_to_bytes(token: SuperBitToken) -> bytes:
        """Serialize a single token."""
        opcode_str = token.symbol
        opcode_bytes = opcode_str.encode("utf-8")
        data = struct.pack(">H", len(opcode_bytes)) + opcode_bytes
        
        if token.operand is not None:
            if isinstance(token.operand, (int, float)):
                data += struct.pack(">B", 1) + struct.pack(">Q", int(token.operand))
            elif isinstance(token.operand, str):
                operand_bytes = token.operand.encode("utf-8")
                data += struct.pack(">B", 2) + struct.pack(">H", len(operand_bytes)) + operand_bytes
            else:
                data += struct.pack(">B", 0)
        else:
            data += struct.pack(">B", 0)
        
        return data
    
    @staticmethod
    def from_bytes(data: bytes) -> "SuperBitStream":
        """Deserialize stream from bytes."""
        if len(data) < 4:
            raise ValueError("Stream requires at least 4 bytes")
        
        token_count = struct.unpack(">I", data[:4])[0]
        tokens = []
        offset = 4
        
        for _ in range(token_count):
            if offset + 3 > len(data):
                raise ValueError("Incomplete stream")
            
            opcode_len = struct.unpack(">H", data[offset:offset+2])[0]
            offset += 2
            
            if offset + opcode_len + 1 > len(data):
                raise ValueError("Incomplete opcode")
            
            opcode_str = data[offset:offset+opcode_len].decode("utf-8")
            offset += opcode_len
            
            operand_type = data[offset]
            offset += 1
            
            operand = None
            if operand_type == 1:
                if offset + 8 > len(data):
                    raise ValueError("Incomplete operand")
                operand = struct.unpack(">Q", data[offset:offset+8])[0]
                offset += 8
            elif operand_type == 2:
                if offset + 2 > len(data):
                    raise ValueError("Incomplete operand length")
                operand_len = struct.unpack(">H", data[offset:offset+2])[0]
                offset += 2
                if offset + operand_len > len(data):
                    raise ValueError("Incomplete operand")
                operand = data[offset:offset+operand_len].decode("utf-8")
                offset += operand_len
            
            token = SuperBitToken(opcode_str, operand)
            tokens.append(token)
        
        return SuperBitStream(tokens=tokens)
    
    def __repr__(self) -> str:
        return f"SuperBitStream(tokens={len(self.tokens)})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, SuperBitStream):
            return False
        return self.tokens == other.tokens
