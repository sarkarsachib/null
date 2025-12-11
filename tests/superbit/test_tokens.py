"""Tests for Super-Bit tokens and groups."""

import pytest
from null_system.superbit.tokens import SuperBitToken, SuperBitGroup


class TestSuperBitToken:
    """Test SuperBitToken class."""

    def test_token_creation(self):
        """Test creating a token."""
        token = SuperBitToken("SET", 0x01, 6)
        assert token.symbol == "SET"
        assert token.bits == 0x01
        assert token.bit_width == 6

    def test_token_serialization(self):
        """Test token serialization to bytes."""
        token = SuperBitToken("SET", 0x01, 6)
        data = token.to_bytes()
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_token_deserialization(self):
        """Test token deserialization from bytes."""
        original = SuperBitToken("SET", 0x01, 6)
        data = original.to_bytes()
        restored, consumed = SuperBitToken.from_bytes(data)
        assert restored.symbol == original.symbol
        assert restored.bits == original.bits
        assert restored.bit_width == original.bit_width

    def test_token_equality(self):
        """Test token equality."""
        token1 = SuperBitToken("SET", 0x01, 6)
        token2 = SuperBitToken("SET", 0x01, 6)
        token3 = SuperBitToken("ADD", 0x02, 6)
        assert token1 == token2
        assert token1 != token3

    def test_token_repr(self):
        """Test token string representation."""
        token = SuperBitToken("SET", 0x01, 6)
        repr_str = repr(token)
        assert "SET" in repr_str
        assert "bits=" in repr_str


class TestSuperBitGroup:
    """Test SuperBitGroup class."""

    def test_group_creation(self):
        """Test creating a group."""
        token = SuperBitToken("SET", 0x01, 6)
        group = SuperBitGroup([token], 6)
        assert len(group.tokens) == 1
        assert group.total_bits == 6

    def test_group_is_full(self):
        """Test is_full property."""
        token6bit = SuperBitToken("SET", 0x01, 6)
        token4bit = SuperBitToken("TEXT", 0x0, 4)

        group = SuperBitGroup([token6bit], 6)
        assert not group.is_full

        group = SuperBitGroup([token6bit, token4bit], 10)
        assert group.is_full  # 8-bit limit

    def test_group_remaining_bits(self):
        """Test remaining_bits property."""
        token = SuperBitToken("SET", 0x01, 6)
        group = SuperBitGroup([token], 6)
        assert group.remaining_bits == 2

        group = SuperBitGroup([token], 8)
        assert group.remaining_bits == 0

    def test_add_token_success(self):
        """Test adding token to group."""
        group = SuperBitGroup([], 0)
        token = SuperBitToken("SET", 0x01, 6)
        assert group.add_token(token) is True
        assert len(group.tokens) == 1
        assert group.total_bits == 6

    def test_add_token_overflow(self):
        """Test adding token when group is full."""
        token6 = SuperBitToken("SET", 0x01, 6)
        token4 = SuperBitToken("TEXT", 0x0, 4)
        group = SuperBitGroup([token6], 6)
        # 6 + 4 = 10 > 8, should fail
        assert group.add_token(token4) is False
        assert len(group.tokens) == 1

    def test_to_byte(self):
        """Test packing tokens into a byte."""
        token6 = SuperBitToken("SET", 0x01, 6)
        token2 = SuperBitToken("END", 0x3, 2)
        group = SuperBitGroup([token6, token2], 8)
        byte_val = group.to_byte()
        assert isinstance(byte_val, int)
        assert 0 <= byte_val <= 255

    def test_to_byte_overflow(self):
        """Test to_byte with overflow."""
        token6 = SuperBitToken("SET", 0x01, 6)
        token4 = SuperBitToken("TEXT", 0x0, 4)
        group = SuperBitGroup([token6, token4], 10)
        with pytest.raises(ValueError):
            group.to_byte()

    def test_group_serialization(self):
        """Test group serialization."""
        token = SuperBitToken("SET", 0x01, 6)
        group = SuperBitGroup([token], 6)
        data = group.to_bytes()
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_group_equality(self):
        """Test group equality."""
        token1 = SuperBitToken("SET", 0x01, 6)
        token2 = SuperBitToken("SET", 0x01, 6)
        group1 = SuperBitGroup([token1], 6)
        group2 = SuperBitGroup([token2], 6)
        assert group1 == group2

    def test_group_repr(self):
        """Test group string representation."""
        token = SuperBitToken("SET", 0x01, 6)
        group = SuperBitGroup([token], 6)
        repr_str = repr(group)
        assert "bits=" in repr_str
        assert "tokens=" in repr_str


class TestSuperBitGroupPacking:
    """Test Super-Bit group packing and unpacking."""

    def test_pack_single_token(self):
        """Test packing single token."""
        # SET = 0x01, 6 bits
        token = SuperBitToken("SET", 0x01, 6)
        group = SuperBitGroup([token], 6)
        byte_val = group.to_byte()
        # 0x01 << 2 = 0x04
        assert byte_val == 0x04

    def test_pack_two_tokens(self):
        """Test packing two tokens."""
        token1 = SuperBitToken("SET", 0x01, 6)  # 0b000001 at top 6 bits
        token2 = SuperBitToken("TRUE", 0x1, 2)  # 0b01 at bottom 2 bits
        group = SuperBitGroup([token1, token2], 8)
        byte_val = group.to_byte()
        # (0x01 << 2) | 0x01 = 0x04 | 0x01 = 0x05
        assert byte_val == 0x05

    def test_unpack_from_byte(self):
        """Test unpacking tokens from byte."""
        # This would need a registry, test basic structure
        packed_byte = 0x05
        token_format = [6, 2]  # Two tokens: 6 bits + 2 bits
        group = SuperBitGroup.from_byte(packed_byte, token_format)
        assert len(group.tokens) == 2
        assert group.total_bits == 8
