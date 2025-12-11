"""Core data types and serialization for Null-Lang.

This module defines the fundamental data types used in Null-Lang runtime,
including TEXT, NUM, BOOL, ARRAY, and OBJECT types with serialization
helpers for converting to/from Super-Bit streams.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
import struct
import io


class NullValue(ABC):
    """Abstract base class for all Null-Lang values."""

    @property
    @abstractmethod
    def type_name(self) -> str:
        """Return the type name as a string."""
        pass

    @abstractmethod
    def to_bytes(self) -> bytes:
        """Serialize value to bytes for Super-Bit encoding."""
        pass

    @staticmethod
    @abstractmethod
    def from_bytes(data: bytes) -> "NullValue":
        """Deserialize value from bytes."""
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass


@dataclass
class TextValue(NullValue):
    """Represents a TEXT (string) value."""

    value: str

    @property
    def type_name(self) -> str:
        return "TEXT"

    def to_bytes(self) -> bytes:
        """Serialize TEXT value: length (2 bytes) + UTF-8 encoded text."""
        encoded = self.value.encode("utf-8")
        length = len(encoded)
        return struct.pack(">H", length) + encoded

    @staticmethod
    def from_bytes(data: bytes) -> "TextValue":
        """Deserialize TEXT value from bytes."""
        if len(data) < 2:
            raise ValueError("TEXT requires at least 2 bytes for length header")
        length = struct.unpack(">H", data[:2])[0]
        text = data[2 : 2 + length].decode("utf-8")
        return TextValue(text)

    def __repr__(self) -> str:
        return f'TextValue("{self.value}")'

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TextValue):
            return self.value == other.value
        return False


@dataclass
class NumValue(NullValue):
    """Represents a NUM (numeric) value (int or float)."""

    value: Union[int, float]

    @property
    def type_name(self) -> str:
        return "NUM"

    def to_bytes(self) -> bytes:
        """Serialize NUM value: type flag (1 byte) + value (8 bytes)."""
        if isinstance(self.value, float):
            return b"\x01" + struct.pack(">d", self.value)
        else:
            return b"\x00" + struct.pack(">q", self.value)

    @staticmethod
    def from_bytes(data: bytes) -> "NumValue":
        """Deserialize NUM value from bytes."""
        if len(data) < 9:
            raise ValueError("NUM requires at least 9 bytes (type flag + value)")
        is_float = data[0]
        if is_float:
            value = struct.unpack(">d", data[1:9])[0]
        else:
            value = struct.unpack(">q", data[1:9])[0]
        return NumValue(value)

    def __repr__(self) -> str:
        return f"NumValue({self.value})"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, NumValue):
            return self.value == other.value
        return False


@dataclass
class BoolValue(NullValue):
    """Represents a BOOL (boolean) value."""

    value: bool

    @property
    def type_name(self) -> str:
        return "BOOL"

    def to_bytes(self) -> bytes:
        """Serialize BOOL value: 1 byte (0x00 or 0x01)."""
        return b"\x01" if self.value else b"\x00"

    @staticmethod
    def from_bytes(data: bytes) -> "BoolValue":
        """Deserialize BOOL value from bytes."""
        if len(data) < 1:
            raise ValueError("BOOL requires at least 1 byte")
        return BoolValue(data[0] != 0)

    def __repr__(self) -> str:
        return f"BoolValue({self.value})"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BoolValue):
            return self.value == other.value
        return False


@dataclass
class ArrayValue(NullValue):
    """Represents an ARRAY (list) value."""

    elements: List[NullValue]

    @property
    def type_name(self) -> str:
        return "ARRAY"

    def to_bytes(self) -> bytes:
        """Serialize ARRAY: count (2 bytes) + serialized elements."""
        count = len(self.elements)
        data = struct.pack(">H", count)
        for element in self.elements:
            # Encode type indicator + element bytes
            type_byte = _get_type_byte(element.type_name)
            element_bytes = element.to_bytes()
            data += type_byte + struct.pack(">H", len(element_bytes)) + element_bytes
        return data

    @staticmethod
    def from_bytes(data: bytes) -> "ArrayValue":
        """Deserialize ARRAY from bytes."""
        if len(data) < 2:
            raise ValueError("ARRAY requires at least 2 bytes for count")
        count = struct.unpack(">H", data[:2])[0]
        elements = []
        offset = 2
        for _ in range(count):
            if offset >= len(data):
                raise ValueError("Incomplete ARRAY data")
            type_byte = data[offset]
            offset += 1
            if offset + 2 > len(data):
                raise ValueError("Incomplete ARRAY element header")
            elem_len = struct.unpack(">H", data[offset : offset + 2])[0]
            offset += 2
            if offset + elem_len > len(data):
                raise ValueError("Incomplete ARRAY element data")
            elem_data = data[offset : offset + elem_len]
            offset += elem_len
            elem_type = _get_type_name(type_byte)
            elements.append(_deserialize_by_type(elem_type, elem_data))
        return ArrayValue(elements)

    def __repr__(self) -> str:
        return f"ArrayValue({self.elements})"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ArrayValue):
            return self.elements == other.elements
        return False


@dataclass
class ObjectValue(NullValue):
    """Represents an OBJECT (dictionary) value."""

    pairs: Dict[str, NullValue]

    @property
    def type_name(self) -> str:
        return "OBJECT"

    def to_bytes(self) -> bytes:
        """Serialize OBJECT: count (2 bytes) + key-value pairs."""
        count = len(self.pairs)
        data = struct.pack(">H", count)
        for key, value in self.pairs.items():
            # Encode key (as TEXT) + type indicator + value bytes
            key_bytes = key.encode("utf-8")
            data += struct.pack(">H", len(key_bytes)) + key_bytes
            type_byte = _get_type_byte(value.type_name)
            value_bytes = value.to_bytes()
            data += type_byte + struct.pack(">H", len(value_bytes)) + value_bytes
        return data

    @staticmethod
    def from_bytes(data: bytes) -> "ObjectValue":
        """Deserialize OBJECT from bytes."""
        if len(data) < 2:
            raise ValueError("OBJECT requires at least 2 bytes for count")
        count = struct.unpack(">H", data[:2])[0]
        pairs = {}
        offset = 2
        for _ in range(count):
            if offset + 2 > len(data):
                raise ValueError("Incomplete OBJECT key header")
            key_len = struct.unpack(">H", data[offset : offset + 2])[0]
            offset += 2
            if offset + key_len > len(data):
                raise ValueError("Incomplete OBJECT key data")
            key = data[offset : offset + key_len].decode("utf-8")
            offset += key_len
            if offset >= len(data):
                raise ValueError("Incomplete OBJECT value type")
            type_byte = data[offset]
            offset += 1
            if offset + 2 > len(data):
                raise ValueError("Incomplete OBJECT value header")
            value_len = struct.unpack(">H", data[offset : offset + 2])[0]
            offset += 2
            if offset + value_len > len(data):
                raise ValueError("Incomplete OBJECT value data")
            value_data = data[offset : offset + value_len]
            offset += value_len
            value_type = _get_type_name(type_byte)
            pairs[key] = _deserialize_by_type(value_type, value_data)
        return ObjectValue(pairs)

    def __repr__(self) -> str:
        return f"ObjectValue({self.pairs})"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ObjectValue):
            return self.pairs == other.pairs
        return False


def _get_type_byte(type_name: str) -> bytes:
    """Get the single-byte type indicator for a type name."""
    type_map = {
        "TEXT": b"\x01",
        "NUM": b"\x02",
        "BOOL": b"\x03",
        "ARRAY": b"\x04",
        "OBJECT": b"\x05",
    }
    if type_name not in type_map:
        raise ValueError(f"Unknown type: {type_name}")
    return type_map[type_name]


def _get_type_name(type_byte: int) -> str:
    """Get the type name from a single-byte type indicator."""
    type_map = {
        1: "TEXT",
        2: "NUM",
        3: "BOOL",
        4: "ARRAY",
        5: "OBJECT",
    }
    if type_byte not in type_map:
        raise ValueError(f"Unknown type byte: {type_byte}")
    return type_map[type_byte]


def _deserialize_by_type(type_name: str, data: bytes) -> NullValue:
    """Deserialize a value based on its type name."""
    deserializers = {
        "TEXT": TextValue.from_bytes,
        "NUM": NumValue.from_bytes,
        "BOOL": BoolValue.from_bytes,
        "ARRAY": ArrayValue.from_bytes,
        "OBJECT": ObjectValue.from_bytes,
    }
    if type_name not in deserializers:
        raise ValueError(f"Unknown type: {type_name}")
    return deserializers[type_name](data)


def to_superbit_stream(value: NullValue) -> bytes:
    """Convert a Null-Lang value to a Super-Bit stream (byte sequence).

    Args:
        value: A NullValue instance to serialize

    Returns:
        Byte sequence with type indicator + serialized data
    """
    type_byte = _get_type_byte(value.type_name)
    value_bytes = value.to_bytes()
    return type_byte + struct.pack(">H", len(value_bytes)) + value_bytes


def from_superbit_stream(data: bytes) -> NullValue:
    """Reconstruct a Null-Lang value from a Super-Bit stream.

    Args:
        data: Byte sequence containing type indicator + serialized data

    Returns:
        Reconstructed NullValue instance

    Raises:
        ValueError: If data is malformed or incomplete
    """
    if len(data) < 3:
        raise ValueError("Super-Bit stream requires at least 3 bytes")
    type_byte = data[0]
    length = struct.unpack(">H", data[1:3])[0]
    value_data = data[3 : 3 + length]
    if len(value_data) < length:
        raise ValueError("Incomplete Super-Bit stream data")
    type_name = _get_type_name(type_byte)
    return _deserialize_by_type(type_name, value_data)
