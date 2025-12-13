"""Multilingual tokenizer for Null-Lang NLP engine.

Supports English, Chinese, and Spanish with proper Unicode handling.
"""

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class TokenType(Enum):
    """Token types for the tokenizer."""
    WORD = "WORD"
    PUNCTUATION = "PUNCTUATION"
    NUMBER = "NUMBER"
    WHITESPACE = "WHITESPACE"
    SYMBOL = "SYMBOL"
    CJK = "CJK"  # Chinese, Japanese, Kanji characters
    UNKNOWN = "UNKNOWN"


@dataclass
class Token:
    """Represents a single token."""
    text: str
    token_type: TokenType
    position: int
    length: int

    def __repr__(self) -> str:
        return f"Token({self.text!r}, {self.token_type.value}, {self.position})"


class Tokenizer:
    """Multilingual tokenizer with support for English, Chinese, and Spanish."""

    def __init__(self, language: str = "en"):
        """
        Initialize the tokenizer.

        Args:
            language: Language code ('en', 'zh', 'es', or 'auto' for auto-detection)
        """
        self.language = language
        self._cjk_ranges = [
            (0x4E00, 0x9FFF),  # CJK Unified Ideographs
            (0x3400, 0x4DBF),  # CJK Extension A
            (0x20000, 0x2A6DF),  # CJK Extension B
            (0x2A700, 0x2B73F),  # CJK Extension C
            (0x2B740, 0x2B81F),  # CJK Extension D
        ]

    def _is_cjk(self, char: str) -> bool:
        """Check if a character is CJK (Chinese/Japanese/Korean)."""
        code_point = ord(char)
        return any(start <= code_point <= end for start, end in self._cjk_ranges)

    def _detect_language(self, text: str) -> str:
        """Auto-detect language from text."""
        if self.language != "auto":
            return self.language

        cjk_count = sum(1 for c in text if self._is_cjk(c))
        cjk_ratio = cjk_count / len(text) if text else 0

        if cjk_ratio > 0.3:
            return "zh"
        # Simple heuristic for Spanish: look for common Spanish characters
        if any(c in text for c in "áéíóúñ¿¡"):
            return "es"
        return "en"

    def _tokenize_cjk(self, text: str) -> List[Token]:
        """Tokenize CJK text (Chinese, Japanese, Korean)."""
        tokens = []
        position = 0
        i = 0

        while i < len(text):
            if self._is_cjk(text[i]):
                tokens.append(Token(text[i], TokenType.CJK, position, 1))
                position += 1
                i += 1
            elif text[i].isspace():
                # Skip whitespace but track position
                position += 1
                i += 1
            elif text[i].isdigit():
                num_str = ""
                start_pos = position
                while i < len(text) and text[i].isdigit():
                    num_str += text[i]
                    position += 1
                    i += 1
                tokens.append(Token(num_str, TokenType.NUMBER, start_pos, len(num_str)))
            else:
                # Collect Latin characters
                word = ""
                start_pos = position
                while i < len(text) and not self._is_cjk(text[i]) and not text[i].isspace():
                    word += text[i]
                    position += 1
                    i += 1
                if word:
                    tokens.append(Token(word, TokenType.WORD, start_pos, len(word)))

        return tokens

    def _tokenize_latin(self, text: str) -> List[Token]:
        """Tokenize Latin-based text (English, Spanish, etc.)."""
        tokens = []
        position = 0

        # Split by whitespace and punctuation while preserving positions
        pattern = r'\b\w+\b|[\d.]+|[^\w\s]'
        for match in re.finditer(pattern, text):
            token_text = match.group()
            token_position = match.start()

            if token_text.isspace():
                continue

            if token_text.isdigit() or (token_text[0].isdigit() and '.' in token_text):
                token_type = TokenType.NUMBER
            elif token_text.isalpha() or token_text.isalnum():
                token_type = TokenType.WORD
            elif token_text in '.,;:!?-—–()[]{}"\'\n\t':
                token_type = TokenType.PUNCTUATION
            elif token_text[0].isdigit():
                token_type = TokenType.NUMBER
            else:
                token_type = TokenType.SYMBOL

            tokens.append(Token(token_text, token_type, token_position, len(token_text)))

        return tokens

    def tokenize(self, text: str, language: Optional[str] = None) -> List[Token]:
        """
        Tokenize input text.

        Args:
            text: The text to tokenize
            language: Override language setting (optional)

        Returns:
            List of tokens
        """
        if not text:
            return []

        lang = language or self.language
        if lang == "auto":
            lang = self._detect_language(text)

        # Normalize Unicode
        text = unicodedata.normalize("NFC", text)

        if lang == "zh":
            return self._tokenize_cjk(text)
        else:
            return self._tokenize_latin(text)

    def detokenize(self, tokens: List[Token]) -> str:
        """
        Reconstruct text from tokens.

        Args:
            tokens: List of tokens

        Returns:
            Reconstructed text
        """
        if not tokens:
            return ""

        result = []
        last_position = 0

        for token in tokens:
            if token.position > last_position:
                # Add spacing if there's a gap
                result.append(" ")

            result.append(token.text)
            last_position = token.position + token.length

        return "".join(result)

    def get_vocabulary(self, tokens: List[Token]) -> dict[str, int]:
        """
        Build vocabulary frequency from tokens.

        Args:
            tokens: List of tokens

        Returns:
            Dictionary mapping token text to frequency
        """
        vocab = {}
        for token in tokens:
            vocab[token.text] = vocab.get(token.text, 0) + 1
        return vocab
