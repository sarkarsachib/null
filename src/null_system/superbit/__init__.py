"""Super-Bit encoding layer for Null-Lang.

This module provides efficient 4-8 bit encoding for Null-Lang constructs,
with support for compression, encryption, and fuzzy-bit extensions.
"""

from .tokens import (
    SuperBitToken,
    SuperBitGroup,
    SuperBitOpCode,
    SuperBitStream,
    EnhancedSuperBitToken,
    SourceSpan,
    InstructionDebugInfo,
)
from .registry import SymbolRegistry, get_default_registry
from .encoder import SuperBitEncoder
from .decoder import SuperBitDecoder

__all__ = [
    "SuperBitToken",
    "SuperBitGroup",
    "SuperBitOpCode",
    "SuperBitStream",
    "EnhancedSuperBitToken",
    "SourceSpan",
    "InstructionDebugInfo",
    "SymbolRegistry",
    "get_default_registry",
    "SuperBitEncoder",
    "SuperBitDecoder",
]
