"""Super-Bit tokens and groups for compact binary encoding.

This module defines the fundamental data structures for Super-Bit encoding:
- SuperBitToken: Atomic units representing symbols or data
- SuperBitGroup: 4-8 bit containers for tokens or packed data
- SuperBitStream: A stream of tokens with optional debug metadata
- SuperBitOpCode: Enumeration of super-bit operation codes
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union, Any, Dict
from enum import Enum
import struct


@dataclass
class SuperBitToken:
    """An atomic unit in the Super-Bit encoding system.

    Represents a single symbol, command, or data value with variable bit width.
    """

    symbol: str
    bits: int
    bit_width: int
    metadata: Optional[dict] = None

    def to_bytes(self) -> bytes:
        """Serialize token to bytes.

        Returns a variable-length byte representation suitable for streaming.
        """
        # Pack: bit_width (1 byte) + bits (variable) + symbol_len (1 byte) + symbol
        symbol_bytes = self.symbol.encode("utf-8")
        byte_count = (self.bit_width + 7) // 8
        bits_bytes = self._int_to_bytes(self.bits, byte_count)
        return (
            struct.pack("B", self.bit_width)
            + bits_bytes
            + struct.pack("B", len(symbol_bytes))
            + symbol_bytes
        )

    @staticmethod
    def from_bytes(data: bytes) -> tuple["SuperBitToken", int]:
        """Deserialize token from bytes.

        Returns:
            Tuple of (SuperBitToken, bytes_consumed)
        """
        if len(data) < 2:
            raise ValueError("Token requires at least 2 bytes")
        bit_width = data[0]
        byte_count = (bit_width + 7) // 8
        if len(data) < 1 + byte_count + 1:
            raise ValueError("Incomplete token data")
        bits = int.from_bytes(data[1 : 1 + byte_count], byteorder="big")
        symbol_len = data[1 + byte_count]
        if len(data) < 1 + byte_count + 1 + symbol_len:
            raise ValueError("Incomplete token symbol")
        symbol = data[2 + byte_count : 2 + byte_count + symbol_len].decode("utf-8")
        return SuperBitToken(symbol, bits, bit_width), 2 + byte_count + symbol_len

    @staticmethod
    def _int_to_bytes(value: int, length: Optional[int] = None) -> bytes:
        """Convert an integer to bytes with optional length."""
        if value == 0:
            return b"\x00"
        # Calculate required bytes
        byte_length = (value.bit_length() + 7) // 8
        if length and length > byte_length:
            byte_length = length
        return value.to_bytes(byte_length, byteorder="big")

    def __repr__(self) -> str:
        return f"SuperBitToken({self.symbol!r}, bits={self.bits:0{self.bit_width}b}, width={self.bit_width})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, SuperBitToken):
            return False
        return (
            self.symbol == other.symbol
            and self.bits == other.bits
            and self.bit_width == other.bit_width
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


class SuperBitOpCode(Enum):
    """Enumeration of super-bit operation codes for the VM."""
    
    NOP = "NOP"
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
    PRINT = "PRINT"
    JUMP = "JUMP"
    JUMP_IF_FALSE = "JUMP_IF_FALSE"
    HALT = "HALT"


@dataclass
class SourceSpan:
    """Source code location information for debug mapping."""
    
    filename: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None


@dataclass
class InstructionDebugInfo:
    """Debug information for a single instruction."""
    
    index: int
    source_span: Optional[SourceSpan] = None
    binary_offset: Optional[int] = None


@dataclass
class SuperBitStream:
    """A stream of super-bit tokens with optional debug metadata.
    
    This dataclass bundles tokens with optional debug information
    to enable source-to-binary mapping for the debugger.
    """
    
    tokens: List["EnhancedSuperBitToken"]
    debug_info: Dict[int, InstructionDebugInfo] = field(default_factory=dict)
    source_file: Optional[str] = None
    
    def to_bytes(self) -> bytes:
        """Serialize the super-bit stream to bytes."""
        data = b''
        for token in self.tokens:
            data += token.to_bytes()
        return data
    
    def add_debug_info(self, index: int, info: InstructionDebugInfo):
        """Add debug information for a token at the given index."""
        self.debug_info[index] = info
    
    def get_debug_info(self, index: int) -> Optional[InstructionDebugInfo]:
        """Get debug information for a token at the given index."""
        return self.debug_info.get(index)


@dataclass
class EnhancedSuperBitToken:
    """Enhanced super-bit token with opcode and operand for VM execution.
    
    This is the token format used by the NullVM and compiler pipeline.
    It differs from the low-level SuperBitToken which is used for
    binary encoding with bits and bit widths.
    """
    
    opcode: SuperBitOpCode
    operand: Any = None
    source_span: Optional[SourceSpan] = None
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes for binary frames."""
        opcode_byte = list(SuperBitOpCode).index(self.opcode).to_bytes(1, 'big')
        
        if self.operand is None:
            operand_bytes = b'\x00'
        elif isinstance(self.operand, int):
            operand_bytes = self.operand.to_bytes(4, 'big', signed=True)
        elif isinstance(self.operand, float):
            operand_bytes = struct.pack('d', self.operand)
        elif isinstance(self.operand, str):
            operand_str_bytes = self.operand.encode('utf-8')
            operand_bytes = len(operand_str_bytes).to_bytes(2, 'big') + operand_str_bytes
        elif isinstance(self.operand, bool):
            operand_bytes = (1 if self.operand else 0).to_bytes(1, 'big')
        else:
            operand_bytes = b'\x00'
        
        return opcode_byte + operand_bytes
    
    def __repr__(self) -> str:
        if self.operand is not None:
            return f"SuperBitToken({self.opcode.name}, {self.operand!r})"
        return f"SuperBitToken({self.opcode.name})"
