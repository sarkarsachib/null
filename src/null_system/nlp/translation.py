"""Machine translation for Null-Lang NLP engine."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from .embeddings import EmbeddingModel
from .tokenizer import Tokenizer


@dataclass
class Translation:
    """Represents a translation result."""
    source_text: str
    source_language: str
    target_text: str
    target_language: str
    confidence: float

    def __repr__(self) -> str:
        return (f"Translation({self.source_language}->"
                f"{self.target_language}, conf={self.confidence:.3f})")


class Translator:
    """Provides machine translation capabilities."""

    def __init__(self):
        """Initialize the translator."""
        self.embedding_model = EmbeddingModel()

        # Translation dictionaries for common phrases
        self._en_to_es: Dict[str, str] = {
            "set": "establecer",
            "to": "a",
            "add": "añadir",
            "and": "y",
            "show": "mostrar",
            "repeat": "repetir",
            "times": "veces",
            "if": "si",
            "then": "entonces",
            "else": "sino",
            "define": "definir",
            "function": "función",
            "return": "retornar",
            "true": "verdadero",
            "false": "falso",
            "not": "no",
            "or": "o",
            "is": "es",
            "greater": "mayor",
            "than": "que",
            "less": "menor",
            "equal": "igual",
        }

        self._en_to_zh: Dict[str, str] = {
            "set": "设置",
            "to": "为",
            "add": "加",
            "and": "和",
            "show": "显示",
            "repeat": "重复",
            "times": "次",
            "if": "如果",
            "then": "那么",
            "else": "否则",
            "define": "定义",
            "function": "函数",
            "return": "返回",
            "true": "真",
            "false": "假",
            "not": "不是",
            "or": "或",
            "is": "是",
            "greater": "大于",
            "than": "比",
            "less": "小于",
            "equal": "等于",
        }

        # Reverse dictionaries
        self._es_to_en = {v: k for k, v in self._en_to_es.items()}
        self._zh_to_en = {v: k for k, v in self._en_to_zh.items()}

        self._translation_tables: Dict[Tuple[str, str], Dict[str, str]] = {
            ("en", "es"): self._en_to_es,
            ("en", "zh"): self._en_to_zh,
            ("es", "en"): self._es_to_en,
            ("zh", "en"): self._zh_to_en,
        }

    def translate(self, text: str, source_lang: str, target_lang: str) -> Translation:
        """
        Translate text from source to target language.

        Args:
            text: Text to translate
            source_lang: Source language code ('en', 'es', 'zh')
            target_lang: Target language code

        Returns:
            Translation object with result
        """
        if source_lang == target_lang:
            return Translation(
                source_text=text,
                source_language=source_lang,
                target_text=text,
                target_language=target_lang,
                confidence=1.0
            )

        # Get translation table
        key = (source_lang.lower(), target_lang.lower())
        trans_table = self._translation_tables.get(key, {})

        if not trans_table:
            # Language pair not supported, return original text
            return Translation(
                source_text=text,
                source_language=source_lang,
                target_text=text,
                target_language=target_lang,
                confidence=0.0
            )

        # Tokenize and translate
        tokenizer = Tokenizer(language=source_lang)
        tokens = tokenizer.tokenize(text)

        translated_parts = []
        match_count = 0

        for token in tokens:
            token_lower = token.text.lower()
            if token_lower in trans_table:
                translated_parts.append(trans_table[token_lower])
                match_count += 1
            else:
                # Keep original if no translation
                translated_parts.append(token.text)

        translated_text = " ".join(translated_parts)
        confidence = match_count / len(tokens) if tokens else 0.0

        return Translation(
            source_text=text,
            source_language=source_lang,
            target_text=translated_text,
            target_language=target_lang,
            confidence=confidence
        )

    def batch_translate(self, texts: List[str], source_lang: str, 
                       target_lang: str) -> List[Translation]:
        """
        Translate multiple texts.

        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            List of Translation objects
        """
        return [self.translate(text, source_lang, target_lang) for text in texts]

    def add_translation_pair(self, source_lang: str, target_lang: str,
                            word_source: str, word_target: str) -> None:
        """
        Add or update a translation pair.

        Args:
            source_lang: Source language code
            target_lang: Target language code
            word_source: Source word
            word_target: Target word
        """
        key = (source_lang.lower(), target_lang.lower())
        if key not in self._translation_tables:
            self._translation_tables[key] = {}

        self._translation_tables[key][word_source.lower()] = word_target

        # Also add reverse mapping
        reverse_key = (target_lang.lower(), source_lang.lower())
        if reverse_key not in self._translation_tables:
            self._translation_tables[reverse_key] = {}
        self._translation_tables[reverse_key][word_target.lower()] = word_source

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.

        Returns:
            List of language codes
        """
        langs = set()
        for source, target in self._translation_tables.keys():
            langs.add(source)
            langs.add(target)
        return sorted(list(langs))

    def detect_language(self, text: str) -> str:
        """
        Detect the language of input text.

        Args:
            text: Input text

        Returns:
            Language code ('en', 'es', 'zh', or 'unknown')
        """
        tokenizer = Tokenizer(language="auto")
        detected = tokenizer._detect_language(text)
        return detected if detected in {"en", "es", "zh"} else "unknown"

    def transliterate_cjk_to_pinyin(self, text: str) -> str:
        """
        Simple transliteration of CJK characters to Pinyin (placeholder).

        In a real implementation, this would use a proper Pinyin conversion library.

        Args:
            text: CJK text

        Returns:
            Pinyin representation (simplified)
        """
        # This is a placeholder - real implementation would use proper mapping
        return text

    def can_translate(self, source_lang: str, target_lang: str) -> bool:
        """
        Check if a translation pair is supported.

        Args:
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            True if translation is supported
        """
        key = (source_lang.lower(), target_lang.lower())
        return key in self._translation_tables or source_lang == target_lang
