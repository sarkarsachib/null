"""Data representation layer for Null-Lang.

This module provides core data type classes and serialization utilities
for representing runtime values.
"""

from .types import (
    NullValue,
    TextValue,
    NumValue,
    BoolValue,
    ArrayValue,
    ObjectValue,
    to_superbit_stream,
    from_superbit_stream,
)

__all__ = [
    "NullValue",
    "TextValue",
    "NumValue",
    "BoolValue",
    "ArrayValue",
    "ObjectValue",
    "to_superbit_stream",
    "from_superbit_stream",
]
