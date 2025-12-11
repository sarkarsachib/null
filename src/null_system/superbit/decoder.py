"""Super-Bit decoder for reconstructing AST and data types from bit groups.

This module implements the decoding of Super-Bit groups back into Null-Lang
constructs (commands, literals, expressions) and data types.
"""

from typing import List, Optional, Union, Tuple
import io
import struct

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


class SuperBitDecoder:
    """Decodes Super-Bit groups back to Null-Lang AST and data types."""

    def __init__(self, registry: Optional[SymbolRegistry] = None):
        """Initialize decoder with optional custom registry.

        Args:
            registry: SymbolRegistry to use. Uses default if None.
        """
        self.registry = registry or get_default_registry()
        self.tokens: List[SuperBitToken] = []
        self.position = 0

    def decode_node(self, data: bytes) -> Optional[ASTNode]:
        """Decode bytes to an AST node.

        Args:
            data: Byte data to decode

        Returns:
            Decoded AST node or None
        """
        self.tokens = []
        self.position = 0
        self._parse_tokens(data)
        if not self.tokens:
            return None
        return self._decode_node_from_tokens()

    def decode_value(self, data: bytes) -> Optional[NullValue]:
        """Decode bytes to a data value.

        Args:
            data: Byte data to decode

        Returns:
            Decoded data value or None
        """
        self.tokens = []
        self.position = 0
        self._parse_tokens(data)
        if not self.tokens:
            return None
        return self._decode_value_from_tokens()

    def _parse_tokens(self, data: bytes) -> None:
        """Parse bytes into tokens."""
        stream = io.BytesIO(data)
        self.tokens = []

        # Try to parse as Super-Bit groups first
        group_count_byte = stream.read(1)
        if group_count_byte:
            try:
                group_count = group_count_byte[0]
                for _ in range(group_count):
                    group_data = stream.read(100)  # Read chunk
                    if not group_data:
                        break
                    try:
                        group, _ = SuperBitGroup.from_bytes(group_data)
                        self.tokens.extend(group.tokens)
                    except (ValueError, struct.error):
                        # If not valid group format, treat bytes as raw tokens
                        pass
            except (ValueError, IndexError):
                pass

    def _decode_node_from_tokens(self) -> Optional[ASTNode]:
        """Decode AST node from parsed tokens."""
        if self.position >= len(self.tokens):
            return None

        token = self.tokens[self.position]

        # Type tokens
        if token.symbol == "TEXT":
            self.position += 1
            return self._decode_text_node()
        elif token.symbol == "NUM":
            self.position += 1
            return self._decode_num_node()
        elif token.symbol == "BOOL":
            self.position += 1
            return self._decode_bool_node()
        elif token.symbol == "ARRAY":
            self.position += 1
            return self._decode_array_node()
        elif token.symbol == "OBJECT":
            self.position += 1
            return self._decode_object_node()

        # Command tokens
        elif token.symbol == "SET":
            self.position += 1
            return self._decode_set_command()
        elif token.symbol == "ADD":
            self.position += 1
            return self._decode_add_command()
        elif token.symbol == "SHOW":
            self.position += 1
            return self._decode_show_command()
        elif token.symbol == "REPEAT":
            self.position += 1
            return self._decode_repeat_command()
        elif token.symbol == "DEFINE":
            self.position += 1
            return self._decode_define_command()
        elif token.symbol == "IF":
            self.position += 1
            return self._decode_if_command()

        # Default: treat as identifier
        elif not token.symbol.startswith("0x"):
            return self._decode_identifier()

        return None

    def _decode_value_from_tokens(self) -> Optional[NullValue]:
        """Decode data value from parsed tokens."""
        if self.position >= len(self.tokens):
            return None

        token = self.tokens[self.position]

        if token.symbol == "TEXT":
            self.position += 1
            return self._decode_text_value()
        elif token.symbol == "NUM":
            self.position += 1
            return self._decode_num_value()
        elif token.symbol == "BOOL":
            self.position += 1
            return self._decode_bool_value()
        elif token.symbol == "ARRAY":
            self.position += 1
            return self._decode_array_value()
        elif token.symbol == "OBJECT":
            self.position += 1
            return self._decode_object_value()

        return None

    def _decode_text_node(self) -> Optional[TextLiteral]:
        """Decode TEXT literal."""
        text = self._decode_string()
        return TextLiteral(text) if text is not None else None

    def _decode_text_value(self) -> Optional[TextValue]:
        """Decode TEXT value."""
        text = self._decode_string()
        return TextValue(text) if text is not None else None

    def _decode_num_node(self) -> Optional[NumLiteral]:
        """Decode NUM literal."""
        num = self._decode_number()
        return NumLiteral(num) if num is not None else None

    def _decode_num_value(self) -> Optional[NumValue]:
        """Decode NUM value."""
        num = self._decode_number()
        return NumValue(num) if num is not None else None

    def _decode_bool_node(self) -> Optional[BoolLiteral]:
        """Decode BOOL literal."""
        if self.position < len(self.tokens):
            token = self.tokens[self.position]
            self.position += 1
            value = token.symbol == "TRUE"
            return BoolLiteral(value)
        return None

    def _decode_bool_value(self) -> Optional[BoolValue]:
        """Decode BOOL value."""
        if self.position < len(self.tokens):
            token = self.tokens[self.position]
            self.position += 1
            value = token.symbol == "TRUE"
            return BoolValue(value)
        return None

    def _decode_array_node(self) -> Optional[ArrayLiteral]:
        """Decode ARRAY literal."""
        count = self._decode_count()
        if count is None:
            return None
        elements = []
        for _ in range(count):
            elem = self._decode_node_from_tokens()
            if elem:
                elements.append(elem)
        return ArrayLiteral(elements)

    def _decode_array_value(self) -> Optional[ArrayValue]:
        """Decode ARRAY value."""
        count = self._decode_count()
        if count is None:
            return None
        elements = []
        for _ in range(count):
            elem = self._decode_value_from_tokens()
            if elem:
                elements.append(elem)
        return ArrayValue(elements)

    def _decode_object_node(self) -> Optional[ObjectLiteral]:
        """Decode OBJECT literal."""
        count = self._decode_count()
        if count is None:
            return None
        pairs = []
        for _ in range(count):
            key = self._decode_string()
            if key is None:
                break
            value = self._decode_node_from_tokens()
            if value:
                pairs.append((key, value))
        return ObjectLiteral(pairs)

    def _decode_object_value(self) -> Optional[ObjectValue]:
        """Decode OBJECT value."""
        count = self._decode_count()
        if count is None:
            return None
        pairs = {}
        for _ in range(count):
            key = self._decode_string()
            if key is None:
                break
            value = self._decode_value_from_tokens()
            if value:
                pairs[key] = value
        return ObjectValue(pairs)

    def _decode_set_command(self) -> Optional[SetCommand]:
        """Decode SET command."""
        target = self._decode_node_from_tokens()
        if not isinstance(target, (Identifier, ASTNode)):
            return None
        # Expect TO token
        if self.position < len(self.tokens) and self.tokens[self.position].symbol == "TO":
            self.position += 1
        value = self._decode_node_from_tokens()
        if value is None:
            return None
        return SetCommand(target, value)

    def _decode_add_command(self) -> Optional[AddCommand]:
        """Decode ADD command."""
        operands = []
        operand = self._decode_node_from_tokens()
        if operand:
            operands.append(operand)
        while self.position < len(self.tokens) and self.tokens[self.position].symbol == "AND":
            self.position += 1
            operand = self._decode_node_from_tokens()
            if operand:
                operands.append(operand)
            else:
                break
        return AddCommand(operands) if operands else None

    def _decode_show_command(self) -> Optional[ShowCommand]:
        """Decode SHOW command."""
        value = self._decode_node_from_tokens()
        return ShowCommand(value) if value else None

    def _decode_repeat_command(self) -> Optional[RepeatCommand]:
        """Decode REPEAT command."""
        count = self._decode_node_from_tokens()
        if count is None:
            return None
        # Expect TIMES
        if self.position < len(self.tokens) and self.tokens[self.position].symbol == "TIMES":
            self.position += 1
        body = []
        while self.position < len(self.tokens) and self.tokens[self.position].symbol != "END":
            stmt = self._decode_node_from_tokens()
            if stmt:
                body.append(stmt)
            else:
                break
        # Consume END
        if self.position < len(self.tokens) and self.tokens[self.position].symbol == "END":
            self.position += 1
        return RepeatCommand(count, body)

    def _decode_define_command(self) -> Optional[DefineCommand]:
        """Decode DEFINE command."""
        name_node = self._decode_identifier()
        if not isinstance(name_node, Identifier):
            return None
        name = name_node.name
        # Expect WITH
        if self.position < len(self.tokens) and self.tokens[self.position].symbol == "WITH":
            self.position += 1
        param_count = self._decode_count()
        if param_count is None:
            param_count = 0
        parameters = []
        for _ in range(param_count):
            param = self._decode_identifier()
            if isinstance(param, Identifier):
                parameters.append(param.name)
        body = []
        while self.position < len(self.tokens) and self.tokens[self.position].symbol != "END":
            stmt = self._decode_node_from_tokens()
            if stmt:
                body.append(stmt)
            else:
                break
        # Consume END
        if self.position < len(self.tokens) and self.tokens[self.position].symbol == "END":
            self.position += 1
        return DefineCommand(name, parameters, body)

    def _decode_if_command(self) -> Optional[IfCommand]:
        """Decode IF command."""
        condition = self._decode_node_from_tokens()
        if condition is None:
            return None
        # Expect THEN
        if self.position < len(self.tokens) and self.tokens[self.position].symbol == "THEN":
            self.position += 1
        then_block = []
        while (
            self.position < len(self.tokens)
            and self.tokens[self.position].symbol not in ("ELSE", "END")
        ):
            stmt = self._decode_node_from_tokens()
            if stmt:
                then_block.append(stmt)
            else:
                break
        else_block = None
        if self.position < len(self.tokens) and self.tokens[self.position].symbol == "ELSE":
            self.position += 1
            else_block = []
            while self.position < len(self.tokens) and self.tokens[self.position].symbol != "END":
                stmt = self._decode_node_from_tokens()
                if stmt:
                    else_block.append(stmt)
                else:
                    break
        # Consume END
        if self.position < len(self.tokens) and self.tokens[self.position].symbol == "END":
            self.position += 1
        return IfCommand(condition, then_block, else_block)

    def _decode_string(self) -> Optional[str]:
        """Decode a string."""
        count = self._decode_count()
        if count is None:
            return None
        chars = []
        for _ in range(count):
            if self.position < len(self.tokens):
                token = self.tokens[self.position]
                self.position += 1
                if token.symbol.startswith("CHAR:"):
                    code = int(token.symbol.split(":")[1])
                    chars.append(chr(code))
            else:
                break
        return "".join(chars)

    def _decode_number(self) -> Optional[Union[int, float]]:
        """Decode a number."""
        if self.position >= len(self.tokens):
            return None
        type_token = self.tokens[self.position]
        self.position += 1
        is_float = type_token.symbol == "FLOAT"

        if is_float:
            pass  # Not implemented in simple decoder

        # Decode sign (for integers)
        is_negative = False
        if self.position < len(self.tokens):
            sign_token = self.tokens[self.position]
            if sign_token.symbol == "NEGATIVE":
                is_negative = True
                self.position += 1
            elif sign_token.symbol == "POSITIVE":
                self.position += 1

        # Decode byte count
        byte_count = self._decode_count()
        if byte_count is None:
            return None

        # Decode bytes
        bytes_data = bytearray()
        for _ in range(byte_count):
            if self.position < len(self.tokens):
                token = self.tokens[self.position]
                self.position += 1
                if token.symbol.startswith("BYTE:"):
                    byte_val = int(token.symbol.split(":")[1])
                    bytes_data.append(byte_val)

        if not bytes_data:
            return 0
        value = int.from_bytes(bytes(bytes_data), byteorder="big")
        if is_negative:
            value = -value
        return value

    def _decode_count(self) -> Optional[int]:
        """Decode a count value."""
        if self.position >= len(self.tokens):
            return None
        token = self.tokens[self.position]
        if token.symbol.startswith("COUNT:"):
            self.position += 1
            return int(token.symbol.split(":")[1])
        return None

    def _decode_identifier(self) -> Optional[Identifier]:
        """Decode an identifier."""
        name = self._decode_string()
        return Identifier(name) if name else None
