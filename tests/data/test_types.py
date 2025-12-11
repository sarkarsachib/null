"""Tests for Null-Lang data types."""

import pytest
from null_system.data.types import (
    TextValue,
    NumValue,
    BoolValue,
    ArrayValue,
    ObjectValue,
    to_superbit_stream,
    from_superbit_stream,
)


class TestTextValue:
    """Test TextValue class."""

    def test_text_creation(self):
        """Test creating a text value."""
        val = TextValue("hello")
        assert val.value == "hello"
        assert val.type_name == "TEXT"

    def test_text_to_bytes(self):
        """Test serializing text to bytes."""
        val = TextValue("hello")
        data = val.to_bytes()
        assert isinstance(data, bytes)
        assert len(data) >= 2  # At least length header

    def test_text_from_bytes(self):
        """Test deserializing text from bytes."""
        original = TextValue("hello")
        data = original.to_bytes()
        restored = TextValue.from_bytes(data)
        assert restored == original
        assert restored.value == "hello"

    def test_text_equality(self):
        """Test text value equality."""
        val1 = TextValue("hello")
        val2 = TextValue("hello")
        val3 = TextValue("world")
        assert val1 == val2
        assert val1 != val3

    def test_text_unicode(self):
        """Test text with unicode characters."""
        val = TextValue("こんにちは")
        data = val.to_bytes()
        restored = TextValue.from_bytes(data)
        assert restored == val

    def test_text_empty_string(self):
        """Test empty text."""
        val = TextValue("")
        data = val.to_bytes()
        restored = TextValue.from_bytes(data)
        assert restored == val

    def test_text_repr(self):
        """Test text repr."""
        val = TextValue("hello")
        repr_str = repr(val)
        assert "hello" in repr_str


class TestNumValue:
    """Test NumValue class."""

    def test_num_int_creation(self):
        """Test creating an integer value."""
        val = NumValue(42)
        assert val.value == 42
        assert val.type_name == "NUM"

    def test_num_float_creation(self):
        """Test creating a float value."""
        val = NumValue(3.14159)
        assert val.value == 3.14159
        assert val.type_name == "NUM"

    def test_num_int_roundtrip(self):
        """Test integer serialization roundtrip."""
        original = NumValue(42)
        data = original.to_bytes()
        restored = NumValue.from_bytes(data)
        assert restored == original

    def test_num_float_roundtrip(self):
        """Test float serialization roundtrip."""
        original = NumValue(3.14159)
        data = original.to_bytes()
        restored = NumValue.from_bytes(data)
        assert restored == original

    def test_num_negative_int(self):
        """Test negative integer."""
        val = NumValue(-42)
        data = val.to_bytes()
        restored = NumValue.from_bytes(data)
        assert restored == val

    def test_num_zero(self):
        """Test zero value."""
        val = NumValue(0)
        data = val.to_bytes()
        restored = NumValue.from_bytes(data)
        assert restored == val

    def test_num_large_int(self):
        """Test large integer."""
        val = NumValue(9223372036854775807)  # Max int64
        data = val.to_bytes()
        restored = NumValue.from_bytes(data)
        assert restored == val

    def test_num_equality(self):
        """Test numeric equality."""
        val1 = NumValue(42)
        val2 = NumValue(42)
        val3 = NumValue(43)
        assert val1 == val2
        assert val1 != val3

    def test_num_repr(self):
        """Test numeric repr."""
        val = NumValue(42)
        repr_str = repr(val)
        assert "42" in repr_str


class TestBoolValue:
    """Test BoolValue class."""

    def test_bool_true(self):
        """Test creating true boolean."""
        val = BoolValue(True)
        assert val.value is True
        assert val.type_name == "BOOL"

    def test_bool_false(self):
        """Test creating false boolean."""
        val = BoolValue(False)
        assert val.value is False

    def test_bool_roundtrip(self):
        """Test boolean serialization roundtrip."""
        for original_val in [True, False]:
            original = BoolValue(original_val)
            data = original.to_bytes()
            restored = BoolValue.from_bytes(data)
            assert restored == original

    def test_bool_equality(self):
        """Test boolean equality."""
        val1 = BoolValue(True)
        val2 = BoolValue(True)
        val3 = BoolValue(False)
        assert val1 == val2
        assert val1 != val3

    def test_bool_repr(self):
        """Test boolean repr."""
        val = BoolValue(True)
        repr_str = repr(val)
        assert "True" in repr_str


class TestArrayValue:
    """Test ArrayValue class."""

    def test_array_creation(self):
        """Test creating an array."""
        elements = [
            TextValue("hello"),
            NumValue(42),
            BoolValue(True),
        ]
        val = ArrayValue(elements)
        assert len(val.elements) == 3
        assert val.type_name == "ARRAY"

    def test_array_empty(self):
        """Test empty array."""
        val = ArrayValue([])
        data = val.to_bytes()
        restored = ArrayValue.from_bytes(data)
        assert restored == val

    def test_array_homogeneous(self):
        """Test array with same-type elements."""
        elements = [NumValue(1), NumValue(2), NumValue(3)]
        val = ArrayValue(elements)
        data = val.to_bytes()
        restored = ArrayValue.from_bytes(data)
        assert restored == val

    def test_array_heterogeneous(self):
        """Test array with mixed-type elements."""
        elements = [
            TextValue("hello"),
            NumValue(42),
            BoolValue(True),
        ]
        val = ArrayValue(elements)
        data = val.to_bytes()
        restored = ArrayValue.from_bytes(data)
        assert restored == val

    def test_array_nested(self):
        """Test nested arrays."""
        inner = ArrayValue([NumValue(1), NumValue(2)])
        outer = ArrayValue([TextValue("array"), inner])
        data = outer.to_bytes()
        restored = ArrayValue.from_bytes(data)
        assert restored == outer

    def test_array_equality(self):
        """Test array equality."""
        val1 = ArrayValue([NumValue(1), NumValue(2)])
        val2 = ArrayValue([NumValue(1), NumValue(2)])
        val3 = ArrayValue([NumValue(1), NumValue(3)])
        assert val1 == val2
        assert val1 != val3

    def test_array_repr(self):
        """Test array repr."""
        val = ArrayValue([NumValue(1)])
        repr_str = repr(val)
        assert "ArrayValue" in repr_str


class TestObjectValue:
    """Test ObjectValue class."""

    def test_object_creation(self):
        """Test creating an object."""
        pairs = {
            "name": TextValue("Alice"),
            "age": NumValue(30),
            "active": BoolValue(True),
        }
        val = ObjectValue(pairs)
        assert len(val.pairs) == 3
        assert val.type_name == "OBJECT"

    def test_object_empty(self):
        """Test empty object."""
        val = ObjectValue({})
        data = val.to_bytes()
        restored = ObjectValue.from_bytes(data)
        assert restored == val

    def test_object_roundtrip(self):
        """Test object serialization roundtrip."""
        pairs = {
            "name": TextValue("Alice"),
            "age": NumValue(30),
        }
        val = ObjectValue(pairs)
        data = val.to_bytes()
        restored = ObjectValue.from_bytes(data)
        assert restored == val

    def test_object_nested(self):
        """Test nested objects."""
        inner = ObjectValue({"x": NumValue(1), "y": NumValue(2)})
        outer = ObjectValue({"name": TextValue("Point"), "coords": inner})
        data = outer.to_bytes()
        restored = ObjectValue.from_bytes(data)
        assert restored == outer

    def test_object_with_array(self):
        """Test object containing array."""
        obj = ObjectValue({
            "numbers": ArrayValue([NumValue(1), NumValue(2), NumValue(3)]),
            "name": TextValue("list"),
        })
        data = obj.to_bytes()
        restored = ObjectValue.from_bytes(data)
        assert restored == obj

    def test_object_equality(self):
        """Test object equality."""
        val1 = ObjectValue({"a": NumValue(1)})
        val2 = ObjectValue({"a": NumValue(1)})
        val3 = ObjectValue({"a": NumValue(2)})
        assert val1 == val2
        assert val1 != val3

    def test_object_repr(self):
        """Test object repr."""
        val = ObjectValue({"key": TextValue("value")})
        repr_str = repr(val)
        assert "ObjectValue" in repr_str


class TestSuperBitStreamConversion:
    """Test to_superbit_stream and from_superbit_stream."""

    def test_stream_text(self):
        """Test text value stream conversion."""
        original = TextValue("hello")
        stream = to_superbit_stream(original)
        restored = from_superbit_stream(stream)
        assert restored == original

    def test_stream_number(self):
        """Test numeric value stream conversion."""
        original = NumValue(42)
        stream = to_superbit_stream(original)
        restored = from_superbit_stream(stream)
        assert restored == original

    def test_stream_boolean(self):
        """Test boolean value stream conversion."""
        original = BoolValue(True)
        stream = to_superbit_stream(original)
        restored = from_superbit_stream(stream)
        assert restored == original

    def test_stream_array(self):
        """Test array value stream conversion."""
        original = ArrayValue([
            NumValue(1),
            TextValue("two"),
            BoolValue(False),
        ])
        stream = to_superbit_stream(original)
        restored = from_superbit_stream(stream)
        assert restored == original

    def test_stream_object(self):
        """Test object value stream conversion."""
        original = ObjectValue({
            "x": NumValue(10),
            "name": TextValue("point"),
        })
        stream = to_superbit_stream(original)
        restored = from_superbit_stream(stream)
        assert restored == original

    def test_stream_complex_nested(self):
        """Test complex nested structure stream conversion."""
        original = ObjectValue({
            "array": ArrayValue([
                NumValue(1),
                NumValue(2),
            ]),
            "nested": ObjectValue({
                "text": TextValue("hello"),
            }),
        })
        stream = to_superbit_stream(original)
        restored = from_superbit_stream(stream)
        assert restored == original

    def test_stream_invalid_data(self):
        """Test stream conversion with invalid data."""
        with pytest.raises(ValueError):
            from_superbit_stream(b"")

    def test_stream_malformed_data(self):
        """Test stream conversion with malformed data."""
        with pytest.raises(ValueError):
            from_superbit_stream(b"\x01\x00\x02")  # Incomplete header
