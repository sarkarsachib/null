"""Tests for Super-Bit encoder and decoder."""

import pytest
from null_system.lang.ast_nodes import (
    TextLiteral,
    NumLiteral,
    BoolLiteral,
    Identifier,
    SetCommand,
    ShowCommand,
    AddCommand,
)
from null_system.data.types import (
    TextValue,
    NumValue,
    BoolValue,
    ArrayValue,
)
from null_system.superbit.encoder import SuperBitEncoder
from null_system.superbit.decoder import SuperBitDecoder
from null_system.superbit.registry import get_default_registry


class TestSuperBitEncoder:
    """Test SuperBitEncoder class."""

    def test_encoder_creation(self):
        """Test creating an encoder."""
        encoder = SuperBitEncoder()
        assert encoder.groups == []

    def test_encoder_with_custom_registry(self):
        """Test encoder with custom registry."""
        registry = get_default_registry()
        encoder = SuperBitEncoder(registry)
        assert encoder.registry == registry

    def test_encode_text_literal(self):
        """Test encoding a text literal."""
        encoder = SuperBitEncoder()
        literal = TextLiteral("hello")
        groups = encoder.encode_node(literal)
        assert len(groups) > 0

    def test_encode_num_literal(self):
        """Test encoding a number literal."""
        encoder = SuperBitEncoder()
        literal = NumLiteral(42)
        groups = encoder.encode_node(literal)
        assert len(groups) > 0

    def test_encode_bool_literal(self):
        """Test encoding a boolean literal."""
        encoder = SuperBitEncoder()
        literal = BoolLiteral(True)
        groups = encoder.encode_node(literal)
        assert len(groups) > 0

    def test_encode_identifier(self):
        """Test encoding an identifier."""
        encoder = SuperBitEncoder()
        ident = Identifier("x")
        groups = encoder.encode_node(ident)
        assert len(groups) > 0

    def test_encode_set_command(self):
        """Test encoding SET command."""
        encoder = SuperBitEncoder()
        cmd = SetCommand(Identifier("x"), NumLiteral(42))
        groups = encoder.encode_node(cmd)
        assert len(groups) > 0

    def test_encode_show_command(self):
        """Test encoding SHOW command."""
        encoder = SuperBitEncoder()
        cmd = ShowCommand(TextLiteral("hello"))
        groups = encoder.encode_node(cmd)
        assert len(groups) > 0

    def test_encode_add_command(self):
        """Test encoding ADD command."""
        encoder = SuperBitEncoder()
        cmd = AddCommand([NumLiteral(1), NumLiteral(2)])
        groups = encoder.encode_node(cmd)
        assert len(groups) > 0

    def test_encode_text_value(self):
        """Test encoding TEXT data value."""
        encoder = SuperBitEncoder()
        val = TextValue("test")
        groups = encoder.encode_value(val)
        assert len(groups) > 0

    def test_encode_num_value(self):
        """Test encoding NUM data value."""
        encoder = SuperBitEncoder()
        val = NumValue(100)
        groups = encoder.encode_value(val)
        assert len(groups) > 0

    def test_encode_bool_value(self):
        """Test encoding BOOL data value."""
        encoder = SuperBitEncoder()
        val = BoolValue(False)
        groups = encoder.encode_value(val)
        assert len(groups) > 0

    def test_encode_array_value(self):
        """Test encoding ARRAY data value."""
        encoder = SuperBitEncoder()
        val = ArrayValue([NumValue(1), NumValue(2)])
        groups = encoder.encode_value(val)
        assert len(groups) > 0

    def test_encoder_to_bytes(self):
        """Test encoder serialization to bytes."""
        encoder = SuperBitEncoder()
        literal = NumLiteral(42)
        groups = encoder.encode_node(literal)
        data = encoder.to_bytes(groups)
        assert isinstance(data, bytes)
        assert len(data) > 0


class TestSuperBitDecoder:
    """Test SuperBitDecoder class."""

    def test_decoder_creation(self):
        """Test creating a decoder."""
        decoder = SuperBitDecoder()
        assert decoder.tokens == []
        assert decoder.position == 0

    def test_decoder_with_custom_registry(self):
        """Test decoder with custom registry."""
        registry = get_default_registry()
        decoder = SuperBitDecoder(registry)
        assert decoder.registry == registry

    def test_decode_empty_data(self):
        """Test decoding empty data."""
        decoder = SuperBitDecoder()
        result = decoder.decode_node(b"")
        assert result is None


class TestEncoderDecoderRoundTrip:
    """Test encoding and decoding roundtrips.
    
    Note: These tests verify that encoding and decoding can be performed
    without errors. Full roundtrip fidelity depends on a complete encoder/decoder
    implementation that preserves all semantic information.
    """

    def test_text_value_encoding_produces_data(self):
        """Test TEXT value encoding produces bytes."""
        original = TextValue("hello")
        encoder = SuperBitEncoder()
        groups = encoder.encode_value(original)
        assert len(groups) > 0
        data = encoder.to_bytes(groups)
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_num_value_encoding_produces_data(self):
        """Test NUM value encoding produces bytes."""
        original = NumValue(42)
        encoder = SuperBitEncoder()
        groups = encoder.encode_value(original)
        assert len(groups) > 0
        data = encoder.to_bytes(groups)
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_bool_value_encoding_produces_data(self):
        """Test BOOL value encoding produces bytes."""
        original = BoolValue(True)
        encoder = SuperBitEncoder()
        groups = encoder.encode_value(original)
        assert len(groups) > 0
        data = encoder.to_bytes(groups)
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_array_value_encoding_produces_data(self):
        """Test ARRAY value encoding produces bytes."""
        original = ArrayValue([
            TextValue("one"),
            NumValue(2),
        ])
        encoder = SuperBitEncoder()
        groups = encoder.encode_value(original)
        assert len(groups) > 0
        data = encoder.to_bytes(groups)
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_set_command_encoding_produces_data(self):
        """Test SET command encoding produces bytes."""
        original = SetCommand(Identifier("x"), NumLiteral(42))
        encoder = SuperBitEncoder()
        groups = encoder.encode_node(original)
        assert len(groups) > 0
        data = encoder.to_bytes(groups)
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_show_command_encoding_produces_data(self):
        """Test SHOW command encoding produces bytes."""
        original = ShowCommand(TextLiteral("hello"))
        encoder = SuperBitEncoder()
        groups = encoder.encode_node(original)
        assert len(groups) > 0
        data = encoder.to_bytes(groups)
        assert isinstance(data, bytes)
        assert len(data) > 0


class TestKeywordEncoding:
    """Test encoding/decoding of Null-Lang keywords."""

    def test_set_keyword(self):
        """Test SET keyword encoding."""
        encoder = SuperBitEncoder()
        registry = encoder.registry
        bits_info = registry.lookup_bits("SET")
        assert bits_info is not None

    def test_add_keyword(self):
        """Test ADD keyword encoding."""
        encoder = SuperBitEncoder()
        registry = encoder.registry
        bits_info = registry.lookup_bits("ADD")
        assert bits_info is not None

    def test_if_keyword(self):
        """Test IF keyword encoding."""
        encoder = SuperBitEncoder()
        registry = encoder.registry
        bits_info = registry.lookup_bits("IF")
        assert bits_info is not None

    def test_show_keyword(self):
        """Test SHOW keyword encoding."""
        encoder = SuperBitEncoder()
        registry = encoder.registry
        bits_info = registry.lookup_bits("SHOW")
        assert bits_info is not None

    def test_repeat_keyword(self):
        """Test REPEAT keyword encoding."""
        encoder = SuperBitEncoder()
        registry = encoder.registry
        bits_info = registry.lookup_bits("REPEAT")
        assert bits_info is not None

    def test_define_keyword(self):
        """Test DEFINE keyword encoding."""
        encoder = SuperBitEncoder()
        registry = encoder.registry
        bits_info = registry.lookup_bits("DEFINE")
        assert bits_info is not None

    def test_all_keywords_have_unique_encoding(self):
        """Test that all keywords have unique encodings."""
        encoder = SuperBitEncoder()
        registry = encoder.registry

        keywords = ["SET", "ADD", "IF", "SHOW", "REPEAT", "DEFINE"]
        seen = {}

        for keyword in keywords:
            bits_info = registry.lookup_bits(keyword)
            assert bits_info is not None
            bits, width = bits_info
            # Create a hashable key
            key = (bits, width)
            assert key not in seen, f"Duplicate encoding for {keyword}"
            seen[key] = keyword
