"""Tests for machine translation."""

import pytest
from null_system.nlp.translation import Translator, Translation


class TestTranslator:
    """Test suite for translation."""

    def test_translate_english_to_spanish(self):
        """Test translation from English to Spanish."""
        translator = Translator()
        result = translator.translate("set", "en", "es")

        assert isinstance(result, Translation)
        assert result.source_language == "en"
        assert result.target_language == "es"
        assert result.target_text  # Should have some translation

    def test_translate_english_to_chinese(self):
        """Test translation from English to Chinese."""
        translator = Translator()
        result = translator.translate("set", "en", "zh")

        assert isinstance(result, Translation)
        assert result.target_language == "zh"
        assert result.target_text

    def test_translate_same_language(self):
        """Test that translating to same language returns original."""
        translator = Translator()
        result = translator.translate("hello", "en", "en")

        assert result.source_text == result.target_text
        assert result.confidence == 1.0

    def test_translation_confidence(self):
        """Test that translations have confidence scores."""
        translator = Translator()
        result = translator.translate("set x to 5", "en", "es")

        assert 0.0 <= result.confidence <= 1.0

    def test_batch_translation(self):
        """Test batch translation."""
        translator = Translator()
        texts = ["set", "show", "add"]

        results = translator.batch_translate(texts, "en", "es")

        assert len(results) == 3
        assert all(isinstance(r, Translation) for r in results)

    def test_add_translation_pair(self):
        """Test adding custom translation pairs."""
        translator = Translator()

        translator.add_translation_pair("en", "es", "custom", "personalizado")

        result = translator.translate("custom word", "en", "es")
        assert "personalizado" in result.target_text

    def test_supported_languages(self):
        """Test getting list of supported languages."""
        translator = Translator()
        langs = translator.get_supported_languages()

        assert isinstance(langs, list)
        assert "en" in langs

    def test_can_translate(self):
        """Test checking if translation is supported."""
        translator = Translator()

        assert translator.can_translate("en", "es")
        assert translator.can_translate("en", "zh")
        assert translator.can_translate("en", "en")  # Same language

    def test_detect_language(self):
        """Test language detection."""
        translator = Translator()

        lang = translator.detect_language("Hello world")
        assert lang in ("en", "unknown")

    def test_empty_input(self):
        """Test with empty input."""
        translator = Translator()
        result = translator.translate("", "en", "es")

        assert isinstance(result, Translation)

    def test_translation_roundtrip(self):
        """Test translation roundtrip."""
        translator = Translator()

        original = "set"
        to_spanish = translator.translate(original, "en", "es")
        back_to_english = translator.translate(to_spanish.target_text, "es", "en")

        # Should be able to translate back
        assert back_to_english.target_text  # Should have some result

    def test_multilingual_vocabulary(self):
        """Test translation with various vocabulary."""
        translator = Translator()

        words = ["set", "show", "add", "repeat", "if"]
        results = translator.batch_translate(words, "en", "es")

        assert len(results) == 5
        assert all(r.target_text for r in results)

    def test_unsupported_language_pair(self):
        """Test translation of unsupported language pair."""
        translator = Translator()

        # Try unsupported pair (though we might add support)
        result = translator.translate("test", "fr", "de")

        # Should return something (likely original text with low confidence)
        assert isinstance(result, Translation)


class TestTranslatorPerformance:
    """Test translator performance."""

    def test_translation_speed(self):
        """Test that translation is reasonably fast."""
        import time
        translator = Translator()

        start = time.time()
        result = translator.translate("set x to 5 and show result", "en", "es")
        elapsed_ms = (time.time() - start) * 1000

        # Should be fast (under 50ms)
        assert elapsed_ms < 50.0
        assert result.target_text

    def test_batch_translation_speed(self):
        """Test batch translation performance."""
        import time
        translator = Translator()

        texts = ["set"] * 10

        start = time.time()
        results = translator.batch_translate(texts, "en", "es")
        elapsed_ms = (time.time() - start) * 1000

        # Should be reasonably fast
        assert elapsed_ms < 500.0  # <50ms per item on average
        assert len(results) == 10


class TestTranslationIntegration:
    """Integration tests for translation."""

    def test_english_spanish_coverage(self):
        """Test coverage of English-Spanish translation."""
        translator = Translator()

        english_words = ["set", "to", "add", "and", "show"]
        results = translator.batch_translate(english_words, "en", "es")

        # Should have reasonable coverage
        translated = [r.target_text for r in results]
        assert len(translated) == len(english_words)

    def test_english_chinese_coverage(self):
        """Test coverage of English-Chinese translation."""
        translator = Translator()

        english_words = ["set", "show", "add"]
        results = translator.batch_translate(english_words, "en", "zh")

        # Should have translations
        translated = [r.target_text for r in results]
        assert len(translated) == len(english_words)

    def test_reverse_translation(self):
        """Test that reverse translation works."""
        translator = Translator()

        # Spanish to English
        result = translator.translate("mostrar", "es", "en")
        assert isinstance(result, Translation)

        # Chinese to English
        result = translator.translate("设置", "zh", "en")
        assert isinstance(result, Translation)
