"""
Transpiler for Null-Lang.

Provides automatic translation between English, modern_rust, and modern_python syntaxes
with learning-path suggestions and explanatory comments.
"""

from .api import transpile, TranspileOptions
from .english_printer import EnglishPrinter
from .rust_printer import RustPrinter
from .python_printer import PythonPrinter
from .learning_comments import LearningCommentGenerator

__all__ = [
    'transpile',
    'TranspileOptions',
    'EnglishPrinter', 
    'RustPrinter',
    'PythonPrinter',
    'LearningCommentGenerator',
]