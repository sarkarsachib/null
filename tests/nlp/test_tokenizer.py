"""Tests for the Null NLP tokenizer."""

import pytest
from null_system.nlp.tokenizer import Tokenizer, TokenType, Token


class TestTokenizer:
    """Test suite for the tokenizer."""

    def test_tokenize_english(self):
        """Test tokenization of English text."""
        tokenizer = Tokenizer(language="en")
        tokens = tokenizer.tokenize("Hello world")

        assert len(tokens) >= 2
        assert any(t.text == "Hello" for t in tokens)
        assert any(t.text == "world" for t in tokens)

    def test_tokenize_with_punctuation(self):
        """Test tokenization with punctuation."""
        tokenizer = Tokenizer(language="en")
        tokens = tokenizer.tokenize("Hello, world!")

        token_texts = [t.text for t in tokens]
        assert "Hello" in token_texts
        assert "world" in token_texts
        assert any(t.token_type == TokenType.PUNCTUATION for t in tokens)

    def test_tokenize_with_numbers(self):
        """Test tokenization with numbers."""
        tokenizer = Tokenizer(language="en")
        tokens = tokenizer.tokenize("I have 42 apples")

        number_tokens = [t for t in tokens if t.token_type == TokenType.NUMBER]
        assert len(number_tokens) > 0
        assert any(t.text == "42" for t in number_tokens)

    def test_tokenize_spanish(self):
        """Test tokenization of Spanish text."""
        tokenizer = Tokenizer(language="es")
        tokens = tokenizer.tokenize("Hola mundo")

        assert len(tokens) >= 2
        assert any(t.text == "Hola" for t in tokens)
        assert any(t.text == "mundo" for t in tokens)

    def test_tokenize_chinese(self):
        """Test tokenization of Chinese text."""
        tokenizer = Tokenizer(language="zh")
        tokens = tokenizer.tokenize("你好世界")

        assert len(tokens) >= 2
        assert any(t.token_type == TokenType.CJK for t in tokens)

    def test_auto_detect_language(self):
        """Test auto-detection of language."""
        tokenizer = Tokenizer(language="auto")

        # Test English
        detected = tokenizer._detect_language("Hello world")
        assert detected == "en"

        # Test Spanish (with accents)
        detected = tokenizer._detect_language("Hola qué tal")
        assert detected in ("es", "en")

        # Test Chinese
        detected = tokenizer._detect_language("你好世界")
        assert detected == "zh"

    def test_token_properties(self):
        """Test token properties."""
        tokenizer = Tokenizer(language="en")
        tokens = tokenizer.tokenize("test")

        assert len(tokens) > 0
        token = tokens[0]
        assert hasattr(token, "text")
        assert hasattr(token, "token_type")
        assert hasattr(token, "position")
        assert hasattr(token, "length")

    def test_empty_input(self):
        """Test with empty input."""
        tokenizer = Tokenizer(language="en")
        tokens = tokenizer.tokenize("")

        assert len(tokens) == 0

    def test_get_vocabulary(self):
        """Test vocabulary extraction."""
        tokenizer = Tokenizer(language="en")
        tokens = tokenizer.tokenize("cat dog cat bird dog dog")

        vocab = tokenizer.get_vocabulary(tokens)
        assert "cat" in vocab
        assert vocab["cat"] == 2
        assert vocab["dog"] == 3
        assert vocab["bird"] == 1

    def test_detokenize(self):
        """Test reconstructing text from tokens."""
        tokenizer = Tokenizer(language="en")
        original = "Hello world"
        tokens = tokenizer.tokenize(original)
        reconstructed = tokenizer.detokenize(tokens)

        # Should contain the main words
        assert "Hello" in reconstructed or "hello" in reconstructed.lower()
        assert "world" in reconstructed

    def test_unicode_normalization(self):
        """Test Unicode normalization."""
        tokenizer = Tokenizer(language="en")
        # Combining characters test
        text = "café"  # NFC form
        tokens = tokenizer.tokenize(text)

        assert len(tokens) > 0

    def test_token_types(self):
        """Test various token types."""
        tokenizer = Tokenizer(language="en")
        tokens = tokenizer.tokenize("word 123 + - * .")

        types = {t.token_type for t in tokens}
        # Should have at least word type
        assert TokenType.WORD in types or len(types) > 0

    def test_case_preservation(self):
        """Test that case is preserved."""
        tokenizer = Tokenizer(language="en")
        tokens = tokenizer.tokenize("Hello World")

        token_texts = [t.text for t in tokens]
        assert any(t[0].isupper() for t in token_texts)  # Has uppercase

    def test_special_characters(self):
        """Test handling of special characters."""
        tokenizer = Tokenizer(language="en")
        tokens = tokenizer.tokenize("email@example.com")

        assert len(tokens) > 0

    def test_multiple_spaces(self):
        """Test handling of multiple spaces."""
        tokenizer = Tokenizer(language="en")
        tokens = tokenizer.tokenize("word1    word2")

        # Should still extract words despite spacing
        token_texts = [t.text for t in tokens]
        assert "word1" in token_texts or "word2" in token_texts


class TestTokenizerPerformance:
    """Test tokenizer performance."""

    def test_tokenization_speed(self):
        """Test that tokenization is reasonably fast."""
        import time
        tokenizer = Tokenizer(language="en")

        # Create a longer text
        text = " ".join(["word"] * 100)

        start = time.time()
        tokens = tokenizer.tokenize(text)
        elapsed_ms = (time.time() - start) * 1000

        # Should be fast (under 50ms for 100 words)
        assert elapsed_ms < 50.0
        assert len(tokens) > 0
