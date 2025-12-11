"""Super-Bit encoder for converting AST and data types to bit groups.

This module implements the encoding of Null-Lang constructs (commands, literals,
expressions) into efficient Super-Bit groups (4-8 bit containers).
"""

from typing import List, Optional, Union
import io

from ..lang.ast_nodes import (
    ASTNode,
    TextLiteral,
    NumLiteral,
    BoolLiteral,
    ArrayLiteral,
    ObjectLiteral,
    Identifier,
    SetCommand,
    AddCommand,
    ShowCommand,
    RepeatCommand,
    DefineCommand,
    IfCommand,
)
from ..data.types import NullValue, TextValue, NumValue, BoolValue, ArrayValue, ObjectValue
from .tokens import SuperBitToken, SuperBitGroup
from .registry import SymbolRegistry, get_default_registry


class SuperBitEncoder:
    """Encodes Null-Lang AST and data types to Super-Bit groups."""

    def __init__(self, registry: Optional[SymbolRegistry] = None):
        """Initialize encoder with optional custom registry.

        Args:
            registry: SymbolRegistry to use. Uses default if None.
        """
        self.registry = registry or get_default_registry()
        self.groups: List[SuperBitGroup] = []

    def encode_node(self, node: ASTNode) -> List[SuperBitGroup]:
        """Encode an AST node to Super-Bit groups.

        Args:
            node: The AST node to encode

        Returns:
            List of SuperBitGroup objects
        """
        self.groups = []
        self._encode_node_internal(node)
        return self.groups

    def encode_value(self, value: NullValue) -> List[SuperBitGroup]:
        """Encode a data type value to Super-Bit groups.

        Args:
            value: The data value to encode

        Returns:
            List of SuperBitGroup objects
        """
        self.groups = []
        self._encode_value_internal(value)
        return self.groups

    def _encode_node_internal(self, node: ASTNode) -> None:
        """Internal recursive node encoding."""
        if isinstance(node, TextLiteral):
            self._encode_token("TEXT", 4)
            self._encode_string(node.value)
        elif isinstance(node, NumLiteral):
            self._encode_token("NUM", 4)
            self._encode_number(node.value)
        elif isinstance(node, BoolLiteral):
            self._encode_token("BOOL", 4)
            symbol = "TRUE" if node.value else "FALSE"
            self._encode_token(symbol, 3)
        elif isinstance(node, ArrayLiteral):
            self._encode_token("ARRAY", 4)
            self._encode_count(len(node.elements))
            for element in node.elements:
                self._encode_node_internal(element)
        elif isinstance(node, ObjectLiteral):
            self._encode_token("OBJECT", 4)
            self._encode_count(len(node.pairs))
            for key, value in node.pairs:
                self._encode_string(key)
                self._encode_node_internal(value)
        elif isinstance(node, Identifier):
            self._encode_identifier(node.name)
        elif isinstance(node, SetCommand):
            self._encode_token("SET", 6)
            self._encode_node_internal(node.target)
            self._encode_token("TO", 6)
            self._encode_node_internal(node.value)
        elif isinstance(node, AddCommand):
            self._encode_token("ADD", 6)
            for i, operand in enumerate(node.operands):
                if i > 0:
                    self._encode_token("AND", 5)
                self._encode_node_internal(operand)
        elif isinstance(node, ShowCommand):
            self._encode_token("SHOW", 6)
            self._encode_node_internal(node.value)
        elif isinstance(node, RepeatCommand):
            self._encode_token("REPEAT", 6)
            self._encode_node_internal(node.count)
            self._encode_token("TIMES", 6)
            for statement in node.body:
                self._encode_node_internal(statement)
            self._encode_token("END", 6)
        elif isinstance(node, DefineCommand):
            self._encode_token("DEFINE", 6)
            self._encode_identifier(node.name)
            self._encode_token("WITH", 6)
            self._encode_count(len(node.parameters))
            for param in node.parameters:
                self._encode_identifier(param)
            for statement in node.body:
                self._encode_node_internal(statement)
            self._encode_token("END", 6)
        elif isinstance(node, IfCommand):
            self._encode_token("IF", 6)
            self._encode_node_internal(node.condition)
            self._encode_token("THEN", 6)
            for statement in node.then_block:
                self._encode_node_internal(statement)
            if node.else_block:
                self._encode_token("ELSE", 6)
                for statement in node.else_block:
                    self._encode_node_internal(statement)
            self._encode_token("END", 6)

    def _encode_value_internal(self, value: NullValue) -> None:
        """Internal recursive value encoding."""
        if isinstance(value, TextValue):
            self._encode_token("TEXT", 4)
            self._encode_string(value.value)
        elif isinstance(value, NumValue):
            self._encode_token("NUM", 4)
            self._encode_number(value.value)
        elif isinstance(value, BoolValue):
            self._encode_token("BOOL", 4)
            symbol = "TRUE" if value.value else "FALSE"
            self._encode_token(symbol, 3)
        elif isinstance(value, ArrayValue):
            self._encode_token("ARRAY", 4)
            self._encode_count(len(value.elements))
            for element in value.elements:
                self._encode_value_internal(element)
        elif isinstance(value, ObjectValue):
            self._encode_token("OBJECT", 4)
            self._encode_count(len(value.pairs))
            for key, val in value.pairs.items():
                self._encode_string(key)
                self._encode_value_internal(val)

    def _encode_token(self, symbol: str, default_width: int) -> None:
        """Encode a symbol token."""
        bits_info = self.registry.lookup_bits(symbol)
        if bits_info:
            bits, bit_width = bits_info
        else:
            # Use default width, bits can be 0 for unknown symbols
            bits = 0
            bit_width = default_width

        token = SuperBitToken(symbol, bits, bit_width)
        self._add_token_to_group(token)

    def _add_token_to_group(self, token: SuperBitToken) -> None:
        """Add a token to the current group or create new group if needed."""
        if not self.groups or not self.groups[-1].add_token(token):
            # Create new group
            group = SuperBitGroup([token], token.bit_width)
            self.groups.append(group)

    def _encode_string(self, value: str) -> None:
        """Encode a string value."""
        # Encode length as count
        self._encode_count(len(value))
        # Encode each character
        for char in value:
            code = ord(char)
            # Encode as 8-bit chunks
            token = SuperBitToken(f"CHAR:{code}", code, 8)
            if not self.groups or not self.groups[-1].add_token(token):
                group = SuperBitGroup([token], 8)
                self.groups.append(group)

    def _encode_number(self, value: Union[int, float]) -> None:
        """Encode a numeric value."""
        # Encode type (int vs float)
        is_float = isinstance(value, float)
        token = SuperBitToken("FLOAT" if is_float else "INT", 1 if is_float else 0, 1)
        self._add_token_to_group(token)

        # Encode value as bytes
        if isinstance(value, float):
            import struct

            bytes_data = struct.pack(">d", value)
        else:
            # Encode integer in variable-length format
            abs_val = abs(value)
            is_negative = value < 0
            token = SuperBitToken(
                "NEGATIVE" if is_negative else "POSITIVE", 1 if is_negative else 0, 1
            )
            self._add_token_to_group(token)
            bytes_data = abs_val.to_bytes(
                (abs_val.bit_length() + 7) // 8 or 1, byteorder="big"
            )

        # Encode byte count and data
        self._encode_count(len(bytes_data))
        for byte_val in bytes_data:
            token = SuperBitToken(f"BYTE:{byte_val}", byte_val, 8)
            if not self.groups or not self.groups[-1].add_token(token):
                group = SuperBitGroup([token], 8)
                self.groups.append(group)

    def _encode_count(self, count: int) -> None:
        """Encode a count value (for arrays, strings, etc.)."""
        if count < 256:
            token = SuperBitToken(f"COUNT:{count}", count, 8)
            if not self.groups or not self.groups[-1].add_token(token):
                group = SuperBitGroup([token], 8)
                self.groups.append(group)
        else:
            # For larger counts, use multiple bytes
            bytes_data = count.to_bytes((count.bit_length() + 7) // 8, byteorder="big")
            for byte_val in bytes_data:
                token = SuperBitToken(f"COUNT_BYTE:{byte_val}", byte_val, 8)
                if not self.groups or not self.groups[-1].add_token(token):
                    group = SuperBitGroup([token], 8)
                    self.groups.append(group)

    def _encode_identifier(self, name: str) -> None:
        """Encode an identifier/variable name."""
        self._encode_string(name)

    def to_bytes(self, groups: Optional[List[SuperBitGroup]] = None) -> bytes:
        """Serialize encoded groups to bytes.

        Args:
            groups: Groups to serialize. Uses last encoded if None.

        Returns:
            Byte representation of encoded data
        """
        groups = groups or self.groups
        output = io.BytesIO()
        output.write(bytes([len(groups)]))  # Group count
        for group in groups:
            output.write(group.to_bytes())
        return output.getvalue()
