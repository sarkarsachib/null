"""Tests for Super-Bit symbol registry."""

import pytest
from null_system.superbit.registry import SymbolRegistry, get_default_registry


class TestSymbolRegistry:
    """Test SymbolRegistry class."""

    def test_registry_creation(self):
        """Test creating an empty registry."""
        registry = SymbolRegistry()
        assert len(registry) == 0
        assert registry.get_all_symbols() == []

    def test_register_symbol(self):
        """Test registering a symbol."""
        registry = SymbolRegistry()
        registry.register_symbol("SET", 0x01, 6)
        assert len(registry) == 1
        assert "SET" in registry.get_all_symbols()

    def test_lookup_bits(self):
        """Test looking up bits by symbol."""
        registry = SymbolRegistry()
        registry.register_symbol("SET", 0x01, 6)
        bits_info = registry.lookup_bits("SET")
        assert bits_info == (0x01, 6)

    def test_lookup_symbol(self):
        """Test looking up symbol by bits."""
        registry = SymbolRegistry()
        registry.register_symbol("SET", 0x01, 6)
        symbol = registry.lookup_by_bits(0x01, 6)
        assert symbol == "SET"

    def test_lookup_nonexistent(self):
        """Test lookup of nonexistent entries."""
        registry = SymbolRegistry()
        registry.register_symbol("SET", 0x01, 6)
        assert registry.lookup_bits("ADD") is None
        assert registry.lookup_by_bits(0x02, 6) is None

    def test_multiple_symbols(self):
        """Test registering multiple symbols."""
        registry = SymbolRegistry()
        symbols = [("SET", 0x01, 6), ("ADD", 0x02, 6), ("IF", 0x03, 6)]
        for symbol, bits, width in symbols:
            registry.register_symbol(symbol, bits, width)
        assert len(registry) == 3

    def test_get_all_symbols(self):
        """Test getting all registered symbols."""
        registry = SymbolRegistry()
        registry.register_symbol("SET", 0x01, 6)
        registry.register_symbol("ADD", 0x02, 6)
        symbols = registry.get_all_symbols()
        assert "SET" in symbols
        assert "ADD" in symbols

    def test_compression_hook_registration(self):
        """Test registering compression hooks."""
        registry = SymbolRegistry()

        def compress(data):
            return data

        registry.register_compression_hook("identity", compress)
        assert "identity" in registry.compression_hooks

    def test_compression_hook_application(self):
        """Test applying compression hooks."""
        registry = SymbolRegistry()
        test_data = b"test data"

        def compress_hook(data):
            return data[::-1]

        registry.register_compression_hook("reverse", compress_hook)
        result = registry.apply_compression(test_data, "reverse")
        assert result == b"atad tset"

    def test_compression_hook_not_found(self):
        """Test applying non-existent compression hook."""
        registry = SymbolRegistry()
        with pytest.raises(ValueError):
            registry.apply_compression(b"test", "nonexistent")

    def test_encryption_hook_registration(self):
        """Test registering encryption hooks."""
        registry = SymbolRegistry()

        def encrypt(data):
            return data

        registry.register_encryption_hook("identity", encrypt)
        assert "identity" in registry.encryption_hooks

    def test_encryption_hook_application(self):
        """Test applying encryption hooks."""
        registry = SymbolRegistry()
        test_data = b"test data"

        def encrypt_hook(data):
            return bytes(b ^ 0xFF for b in data)

        registry.register_encryption_hook("xor_ff", encrypt_hook)
        result = registry.apply_encryption(test_data, "xor_ff")
        assert result == bytes(b ^ 0xFF for b in test_data)

    def test_fuzzy_extension_registration(self):
        """Test registering fuzzy-bit extensions."""
        registry = SymbolRegistry()
        registry.register_fuzzy_extension("arithmetic", 0x03, "MULTIPLY")
        assert registry.get_fuzzy_extension("arithmetic", 0x03) == "MULTIPLY"

    def test_fuzzy_extension_not_found(self):
        """Test getting non-existent fuzzy extension."""
        registry = SymbolRegistry()
        assert registry.get_fuzzy_extension("arithmetic", 0x99) is None

    def test_fuzzy_extensions_multiple_contexts(self):
        """Test fuzzy extensions in multiple contexts."""
        registry = SymbolRegistry()
        registry.register_fuzzy_extension("context1", 0x01, "meaning1")
        registry.register_fuzzy_extension("context2", 0x01, "meaning2")
        assert registry.get_fuzzy_extension("context1", 0x01) == "meaning1"
        assert registry.get_fuzzy_extension("context2", 0x01) == "meaning2"


class TestDefaultRegistry:
    """Test get_default_registry function."""

    def test_default_registry_has_commands(self):
        """Test that default registry includes commands."""
        registry = get_default_registry()
        commands = ["SET", "ADD", "IF", "THEN", "ELSE", "SHOW", "REPEAT", "DEFINE"]
        for cmd in commands:
            assert registry.lookup_bits(cmd) is not None

    def test_default_registry_has_types(self):
        """Test that default registry includes data types."""
        registry = get_default_registry()
        types = ["TEXT", "NUM", "BOOL", "ARRAY", "OBJECT"]
        for typ in types:
            assert registry.lookup_bits(typ) is not None

    def test_default_registry_has_operators(self):
        """Test that default registry includes operators."""
        registry = get_default_registry()
        ops = ["PLUS", "MINUS", "AND", "OR", "NOT"]
        for op in ops:
            assert registry.lookup_bits(op) is not None

    def test_default_registry_has_hooks(self):
        """Test that default registry includes hooks."""
        registry = get_default_registry()
        assert "identity" in registry.compression_hooks
        assert "identity" in registry.encryption_hooks

    def test_default_registry_has_fuzzy_extensions(self):
        """Test that default registry includes fuzzy extensions."""
        registry = get_default_registry()
        assert len(registry.fuzzy_extensions) > 0

    def test_default_registry_command_bits(self):
        """Test specific command encodings in default registry."""
        registry = get_default_registry()

        # Test SET command
        bits, width = registry.lookup_bits("SET")
        assert width == 6

        # Test TEXT type
        bits, width = registry.lookup_bits("TEXT")
        assert width == 4

    def test_default_registry_lookup_by_bits(self):
        """Test reverse lookup in default registry."""
        registry = get_default_registry()

        # Get SET bits
        set_bits, set_width = registry.lookup_bits("SET")
        found_symbol = registry.lookup_by_bits(set_bits, set_width)
        assert found_symbol == "SET"

    def test_default_registry_size(self):
        """Test that default registry has reasonable size."""
        registry = get_default_registry()
        assert len(registry) > 20  # Should have plenty of symbols
