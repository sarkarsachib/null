"""Example: Super-Bit Encoding of Null-Lang Commands.

This example demonstrates how to encode Null-Lang commands and data types
into efficient Super-Bit representations.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from null_system.lang.ast_nodes import (
    TextLiteral,
    NumLiteral,
    BoolLiteral,
    Identifier,
    SetCommand,
    ShowCommand,
)
from null_system.superbit import SuperBitEncoder, SuperBitDecoder, get_default_registry
from null_system.data.types import TextValue, NumValue, BoolValue


def example_command_encoding():
    """Example: Encoding a SET command."""
    print("=" * 60)
    print("Example 1: Encoding a SET Command")
    print("=" * 60)

    # Create AST for: SET x TO 42
    x_identifier = Identifier("x")
    number = NumLiteral(42)
    set_cmd = SetCommand(x_identifier, number)

    # Encode to Super-Bit
    encoder = SuperBitEncoder()
    groups = encoder.encode_node(set_cmd)

    print(f"\nAST Command: SET x TO 42")
    print(f"Encoded to {len(groups)} Super-Bit groups")
    for i, group in enumerate(groups):
        print(f"  Group {i}: {group}")
        for token in group.tokens:
            print(f"    - {token}")

    # Serialize to bytes
    data = encoder.to_bytes(groups)
    print(f"Serialized to {len(data)} bytes: {data.hex()}")


def example_show_command():
    """Example: Encoding a SHOW command."""
    print("\n" + "=" * 60)
    print("Example 2: Encoding a SHOW Command")
    print("=" * 60)

    # Create AST for: SHOW "Hello"
    text = TextLiteral("Hello")
    show_cmd = ShowCommand(text)

    # Encode to Super-Bit
    encoder = SuperBitEncoder()
    groups = encoder.encode_node(show_cmd)

    print(f'\nAST Command: SHOW "Hello"')
    print(f"Encoded to {len(groups)} Super-Bit groups")
    for i, group in enumerate(groups):
        print(f"  Group {i}: {group}")

    data = encoder.to_bytes(groups)
    print(f"Serialized to {len(data)} bytes")


def example_data_type_encoding():
    """Example: Encoding data type values."""
    print("\n" + "=" * 60)
    print("Example 3: Encoding Data Type Values")
    print("=" * 60)

    # Encode various data types
    text_val = TextValue("Null-Lang")
    num_val = NumValue(3.14159)
    bool_val = BoolValue(True)

    encoder = SuperBitEncoder()

    print(f"\nEncoding: TextValue('Null-Lang')")
    groups = encoder.encode_value(text_val)
    print(f"  Encoded to {len(groups)} groups")

    print(f"\nEncoding: NumValue(3.14159)")
    encoder = SuperBitEncoder()
    groups = encoder.encode_value(num_val)
    print(f"  Encoded to {len(groups)} groups")

    print(f"\nEncoding: BoolValue(True)")
    encoder = SuperBitEncoder()
    groups = encoder.encode_value(bool_val)
    print(f"  Encoded to {len(groups)} groups")


def example_registry():
    """Example: Working with the Symbol Registry."""
    print("\n" + "=" * 60)
    print("Example 4: Symbol Registry")
    print("=" * 60)

    registry = get_default_registry()

    print(f"\nRegistry contains {len(registry)} symbols")

    # Look up some symbols
    symbols_to_check = ["SET", "ADD", "IF", "SHOW", "REPEAT", "DEFINE", "TEXT", "NUM"]
    print("\nSymbol Encodings:")
    for symbol in symbols_to_check:
        bits_info = registry.lookup_bits(symbol)
        if bits_info:
            bits, bit_width = bits_info
            print(f"  {symbol:10} -> bits=0x{bits:02x}, width={bit_width}")

    # Reverse lookup
    print("\nReverse Lookups:")
    for bit_width in [6, 5, 4, 3]:
        print(f"  Bit width {bit_width}:")
        all_symbols = registry.get_all_symbols()
        for symbol in all_symbols:
            bits_info = registry.lookup_bits(symbol)
            if bits_info and bits_info[1] == bit_width:
                bits = bits_info[0]
                print(f"    0x{bits:02x} -> {symbol}")


def example_registry_extensions():
    """Example: Registry extensibility hooks."""
    print("\n" + "=" * 60)
    print("Example 5: Registry Extensions")
    print("=" * 60)

    registry = get_default_registry()

    # Demonstrate compression hooks
    print("\nCompression Hooks:")
    print(f"  Available: {list(registry.compression_hooks.keys())}")

    # Demonstrate encryption hooks
    print("\nEncryption Hooks:")
    print(f"  Available: {list(registry.encryption_hooks.keys())}")

    # Demonstrate fuzzy-bit extensions
    print("\nFuzzy-Bit Extensions:")
    contexts = list(registry.fuzzy_extensions.keys())
    for context in contexts:
        print(f"  Context: {context}")
        for bits, meaning in registry.fuzzy_extensions[context].items():
            print(f"    bits={bits:02x} -> {meaning}")


if __name__ == "__main__":
    example_command_encoding()
    example_show_command()
    example_data_type_encoding()
    example_registry()
    example_registry_extensions()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
