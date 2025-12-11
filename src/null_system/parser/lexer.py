"""Lexer for tokenizing Null-Lang source code."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List


class TokenType(Enum):
    """Token types for Null-Lang."""
    SET = auto()
    TO = auto()
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    AND = auto()
    PRINT = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    IS = auto()
    GREATER = auto()
    LESS = auto()
    THAN = auto()
    EQUALS = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    NEWLINE = auto()
    EOF = auto()


@dataclass
class Token:
    """A single token from the source code."""
    type: TokenType
    value: str
    line: int
    column: int


class Lexer:
    """Tokenizes Null-Lang source code."""
    
    KEYWORDS = {
        "set": TokenType.SET,
        "to": TokenType.TO,
        "add": TokenType.ADD,
        "subtract": TokenType.SUBTRACT,
        "multiply": TokenType.MULTIPLY,
        "divide": TokenType.DIVIDE,
        "and": TokenType.AND,
        "print": TokenType.PRINT,
        "if": TokenType.IF,
        "then": TokenType.THEN,
        "else": TokenType.ELSE,
        "is": TokenType.IS,
        "greater": TokenType.GREATER,
        "less": TokenType.LESS,
        "than": TokenType.THAN,
        "equals": TokenType.EQUALS,
    }
    
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def tokenize(self) -> List[Token]:
        """Tokenize the source code."""
        while self.position < len(self.source):
            self._skip_whitespace_except_newlines()
            
            if self.position >= len(self.source):
                break
            
            if self._current_char() == '\n':
                self._add_token(TokenType.NEWLINE, '\n')
                self._advance()
                self.line += 1
                self.column = 1
                continue
            
            if self._current_char() == '#':
                self._skip_comment()
                continue
            
            if self._current_char() == '"' or self._current_char() == "'":
                self._read_string()
                continue
            
            if self._current_char().isdigit():
                self._read_number()
                continue
            
            if self._current_char().isalpha():
                self._read_word()
                continue
            
            self._advance()
        
        self._add_token(TokenType.EOF, "")
        return self.tokens
    
    def _current_char(self) -> str:
        """Get the current character."""
        if self.position < len(self.source):
            return self.source[self.position]
        return '\0'
    
    def _advance(self) -> str:
        """Move to the next character."""
        char = self._current_char()
        self.position += 1
        self.column += 1
        return char
    
    def _skip_whitespace_except_newlines(self):
        """Skip whitespace but not newlines."""
        while self._current_char() in ' \t\r':
            self._advance()
    
    def _skip_comment(self):
        """Skip a comment line."""
        while self._current_char() != '\n' and self.position < len(self.source):
            self._advance()
    
    def _read_string(self):
        """Read a string literal."""
        quote_char = self._advance()
        start_line = self.line
        start_column = self.column - 1
        value = ""
        
        while self._current_char() != quote_char and self.position < len(self.source):
            value += self._advance()
        
        if self._current_char() == quote_char:
            self._advance()
        
        self.tokens.append(Token(TokenType.STRING, value, start_line, start_column))
    
    def _read_number(self):
        """Read a number literal."""
        start_line = self.line
        start_column = self.column
        value = ""
        
        while self._current_char().isdigit() or self._current_char() == '.':
            value += self._advance()
        
        self.tokens.append(Token(TokenType.NUMBER, value, start_line, start_column))
    
    def _read_word(self):
        """Read a word (keyword or identifier)."""
        start_line = self.line
        start_column = self.column
        value = ""
        
        while self._current_char().isalnum() or self._current_char() == '_':
            value += self._advance()
        
        token_type = self.KEYWORDS.get(value.lower(), TokenType.IDENTIFIER)
        self.tokens.append(Token(token_type, value, start_line, start_column))
    
    def _add_token(self, token_type: TokenType, value: str):
        """Add a token to the list."""
        self.tokens.append(Token(token_type, value, self.line, self.column))
