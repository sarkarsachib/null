"""Symbol registry for Super-Bit encoding.

This module manages the mapping between symbols, commands, and bit patterns,
providing a centralized registry for efficient encoding/decoding operations.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Callable, List
from .tokens import SuperBitToken


@dataclass
class SymbolRegistry:
    """Manages bidirectional mapping between symbols and bit patterns."""

    # Symbol to (bits, bit_width) mapping
    symbol_to_bits: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    # Bits to symbol mapping (by bit_width)
    bits_to_symbol: Dict[int, Dict[int, str]] = field(default_factory=dict)
    # Compression hooks: name -> function
    compression_hooks: Dict[str, Callable] = field(default_factory=dict)
    # Encryption hooks: name -> function
    encryption_hooks: Dict[str, Callable] = field(default_factory=dict)
    # Fuzzy-bit extensions: context -> alternative meanings
    fuzzy_extensions: Dict[str, Dict[int, str]] = field(default_factory=dict)

    def register_symbol(self, symbol: str, bits: int, bit_width: int) -> None:
        """Register a symbol with its bit pattern.

        Args:
            symbol: The symbol name (e.g., 'SET', 'ADD', 'IF')
            bits: The bit pattern
            bit_width: Number of bits used
        """
        self.symbol_to_bits[symbol] = (bits, bit_width)
        if bit_width not in self.bits_to_symbol:
            self.bits_to_symbol[bit_width] = {}
        self.bits_to_symbol[bit_width][bits] = symbol

    def lookup_bits(self, symbol: str) -> Optional[Tuple[int, int]]:
        """Look up bits for a symbol.

        Returns:
            Tuple of (bits, bit_width) or None if not found
        """
        return self.symbol_to_bits.get(symbol)

    def lookup_by_bits(self, bits: int, bit_width: int) -> Optional[str]:
        """Look up symbol by bit pattern.

        Args:
            bits: The bit pattern
            bit_width: Number of bits

        Returns:
            Symbol name or None if not found
        """
        return self.bits_to_symbol.get(bit_width, {}).get(bits)

    def register_compression_hook(
        self, name: str, hook: Callable[[bytes], bytes]
    ) -> None:
        """Register a compression hook.

        Args:
            name: Identifier for the hook
            hook: Callable that takes bytes and returns compressed bytes
        """
        self.compression_hooks[name] = hook

    def register_encryption_hook(self, name: str, hook: Callable[[bytes], bytes]) -> None:
        """Register an encryption hook.

        Args:
            name: Identifier for the hook
            hook: Callable that takes bytes and returns encrypted bytes
        """
        self.encryption_hooks[name] = hook

    def register_fuzzy_extension(self, context: str, bits: int, alternative: str) -> None:
        """Register a fuzzy-bit extension.

        Allows a bit pattern to have different meanings in different contexts.

        Args:
            context: The context name
            bits: The bit pattern
            alternative: Alternative meaning in this context
        """
        if context not in self.fuzzy_extensions:
            self.fuzzy_extensions[context] = {}
        self.fuzzy_extensions[context][bits] = alternative

    def get_fuzzy_extension(self, context: str, bits: int) -> Optional[str]:
        """Get fuzzy-bit extension for a context."""
        return self.fuzzy_extensions.get(context, {}).get(bits)

    def apply_compression(self, data: bytes, hook_name: str) -> bytes:
        """Apply compression using a registered hook."""
        if hook_name not in self.compression_hooks:
            raise ValueError(f"Unknown compression hook: {hook_name}")
        return self.compression_hooks[hook_name](data)

    def apply_encryption(self, data: bytes, hook_name: str) -> bytes:
        """Apply encryption using a registered hook."""
        if hook_name not in self.encryption_hooks:
            raise ValueError(f"Unknown encryption hook: {hook_name}")
        return self.encryption_hooks[hook_name](data)

    def get_all_symbols(self) -> List[str]:
        """Get all registered symbols."""
        return list(self.symbol_to_bits.keys())

    def __len__(self) -> int:
        """Return the number of registered symbols."""
        return len(self.symbol_to_bits)


def get_default_registry() -> SymbolRegistry:
    """Get the default Super-Bit symbol registry with built-in keywords.

    Returns:
        SymbolRegistry pre-populated with Null-Lang keywords
    """
    registry = SymbolRegistry()

    # Commands (6 bits) - 0x00 to 0x3F
    commands = [
        ("SET", 0x01, 6),
        ("ADD", 0x02, 6),
        ("IF", 0x03, 6),
        ("THEN", 0x04, 6),
        ("ELSE", 0x05, 6),
        ("SHOW", 0x06, 6),
        ("REPEAT", 0x07, 6),
        ("DEFINE", 0x08, 6),
        ("CALL", 0x09, 6),
        ("END", 0x0A, 6),
        ("TO", 0x0B, 6),
        ("WITH", 0x0C, 6),
        ("TIMES", 0x0D, 6),
    ]

    for symbol, bits, width in commands:
        registry.register_symbol(symbol, bits, width)

    # Keywords for types (4 bits) - 0x0 to 0xF
    types = [
        ("TEXT", 0x0, 4),
        ("NUM", 0x1, 4),
        ("BOOL", 0x2, 4),
        ("ARRAY", 0x3, 4),
        ("OBJECT", 0x4, 4),
    ]

    for symbol, bits, width in types:
        registry.register_symbol(symbol, bits, width)

    # Operators (5 bits) - 0x00 to 0x1F
    operators = [
        ("PLUS", 0x01, 5),
        ("MINUS", 0x02, 5),
        ("TIMES_OP", 0x03, 5),
        ("DIVIDED_BY", 0x04, 5),
        ("IS", 0x05, 5),
        ("IS_NOT", 0x06, 5),
        ("GREATER", 0x07, 5),
        ("LESS", 0x08, 5),
        ("GREATER_EQ", 0x09, 5),
        ("LESS_EQ", 0x0A, 5),
        ("AND", 0x0B, 5),
        ("OR", 0x0C, 5),
        ("NOT", 0x0D, 5),
    ]

    for symbol, bits, width in operators:
        registry.register_symbol(symbol, bits, width)

    # Literals (3 bits) - 0x0 to 0x7
    literals = [
        ("TRUE", 0x1, 3),
        ("FALSE", 0x0, 3),
    ]

    for symbol, bits, width in literals:
        registry.register_symbol(symbol, bits, width)

    # Delimiters and special (4 bits)
    special = [
        ("LPAREN", 0x10, 4),
        ("RPAREN", 0x11, 4),
        ("LBRACKET", 0x12, 4),
        ("RBRACKET", 0x13, 4),
        ("COMMA", 0x14, 4),
        ("COLON", 0x15, 4),
        ("DOT", 0x16, 4),
        ("EOF", 0x1F, 4),
    ]

    for symbol, bits, width in special:
        registry.register_symbol(symbol, bits, width)

    # Register built-in compression and encryption hooks
    # (Can be extended later with actual implementations)
    registry.register_compression_hook("identity", lambda x: x)
    registry.register_encryption_hook("identity", lambda x: x)

    # Register fuzzy-bit extensions
    # Example: TIMES can mean multiplication or "TIMES" keyword
    registry.register_fuzzy_extension("arithmetic", 0x03, "MULTIPLY")
    registry.register_fuzzy_extension("keywords", 0x0D, "REPEAT_COUNT")

    return registry
