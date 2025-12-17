"""
Modern Parsers for Null-Lang

Provides Rust-like and Python-like syntax parsers that emit the same AST
structures as the English grammar.
"""

from .modern_rust import ModernRustParser
from .modern_python import ModernPythonParser

__all__ = [
    'ModernRustParser',
    'ModernPythonParser',
]
