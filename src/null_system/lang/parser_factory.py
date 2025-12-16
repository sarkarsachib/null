"""
Parser Factory for Null-Lang.

Provides a dispatcher that selects the appropriate parser based on syntax mode
and returns a unified interface for parsing different syntaxes.
"""

from typing import Union
from enum import Enum

from .parser import NullLangParser, parse, parse_statement
from .syntax_router import SyntaxMode
from .modern import ModernRustParser, ModernPythonParser
from .ast_nodes import Program, ASTNode


class ParserFactory:
    """Factory for creating and managing parsers for different syntax modes."""

    def __init__(self):
        self.english_parser = NullLangParser()
        self.rust_parser = ModernRustParser()
        self.python_parser = ModernPythonParser()

    def parse(self, source: str, mode: SyntaxMode) -> Program:
        """Parse source code in the specified syntax mode.

        Args:
            source: Source code to parse
            mode: SyntaxMode indicating which parser to use

        Returns:
            A Program AST node

        Raises:
            ValueError: If mode is unknown
            SyntaxError: If parsing fails
        """
        if mode == SyntaxMode.english:
            return self.english_parser.parse(source)
        elif mode == SyntaxMode.modern or mode == "rust":
            return self.rust_parser.parse(source)
        elif mode == "python":
            return self.python_parser.parse(source)
        else:
            raise ValueError(f"Unknown syntax mode: {mode}")

    def parse_statement(self, source: str, mode: SyntaxMode) -> ASTNode:
        """Parse a single statement in the specified syntax mode.

        Args:
            source: Statement source to parse
            mode: SyntaxMode indicating which parser to use

        Returns:
            An ASTNode representing the statement

        Raises:
            ValueError: If mode is unknown
            SyntaxError: If parsing fails
        """
        if mode == SyntaxMode.english:
            return self.english_parser.parse_statement(source)
        elif mode == SyntaxMode.modern or mode == "rust":
            return self.rust_parser.parse_statement(source)
        elif mode == "python":
            return self.python_parser.parse_statement(source)
        else:
            raise ValueError(f"Unknown syntax mode: {mode}")


# Global factory instance
_factory = ParserFactory()


def get_parser(mode: SyntaxMode) -> Union[NullLangParser, ModernRustParser, ModernPythonParser]:
    """Get a parser instance for the specified syntax mode.

    Args:
        mode: SyntaxMode indicating which parser to use

    Returns:
        A parser instance

    Raises:
        ValueError: If mode is unknown
    """
    if mode == SyntaxMode.english:
        return _factory.english_parser
    elif mode == SyntaxMode.modern or mode == "rust":
        return _factory.rust_parser
    elif mode == "python":
        return _factory.python_parser
    else:
        raise ValueError(f"Unknown syntax mode: {mode}")
