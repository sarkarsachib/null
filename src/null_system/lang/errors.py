"""
Error reporting for Null-Lang parser.

Provides detailed syntax and semantic error messages with source location information.
"""

from typing import Optional
from .ast_nodes import SourceSpan


class NullLangError(Exception):
    """Base class for all Null-Lang errors."""
    
    def __init__(self, message: str, span: Optional[SourceSpan] = None, source: Optional[str] = None):
        self.message = message
        self.span = span
        self.source = source
        super().__init__(self.format_error())
    
    def format_error(self) -> str:
        """Format the error with source location and context."""
        if not self.span:
            return f"Error: {self.message}"
        
        location = f"Line {self.span.start_line}, Column {self.span.start_col}"
        error_msg = f"Error at {location}: {self.message}"
        
        if self.source:
            lines = self.source.split('\n')
            if 0 <= self.span.start_line - 1 < len(lines):
                error_line = lines[self.span.start_line - 1]
                error_msg += f"\n\n{error_line}\n"
                
                # Add caret indicator
                error_msg += " " * (self.span.start_col - 1) + "^"
                if self.span.start_line == self.span.end_line and self.span.end_col > self.span.start_col:
                    error_msg += "~" * (self.span.end_col - self.span.start_col - 1)
        
        return error_msg


class SyntaxError(NullLangError):
    """Syntax error during parsing."""
    pass


class SemanticError(NullLangError):
    """Semantic error during analysis."""
    pass


class LexerError(NullLangError):
    """Lexical analysis error."""
    pass


def create_syntax_error(message: str, line: int, column: int, source: str) -> SyntaxError:
    """Helper to create a syntax error with source information."""
    span = SourceSpan(line, column, line, column + 1)
    return SyntaxError(message, span, source)


def create_semantic_error(message: str, span: SourceSpan, source: str) -> SemanticError:
    """Helper to create a semantic error with source information."""
    return SemanticError(message, span, source)
