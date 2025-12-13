"""NLP operations for Null-Lang library."""

from ..runtime import NullCallContext
from ..types import NullValue, to_null
from ..nlp.pipeline import NLPPipeline
from ..nlp.tokenizer import Tokenizer
from ..nlp.intent import IntentDetector
from ..nlp.entity_extraction import EntityExtractor
from ..nlp.translation import Translator
from ..nlp.codegen import CodeGenerator


# Global pipeline instance (lazy initialized)
_pipeline_instance: NLPPipeline | None = None


def _get_pipeline() -> NLPPipeline:
    """Get or create the global NLP pipeline."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = NLPPipeline(language="auto", enable_translation=True)
    return _pipeline_instance


def TOKENIZE(ctx: NullCallContext, text: NullValue) -> NullValue:
    """
    Tokenize input text.

    Args:
        ctx: Call context
        text: Text to tokenize

    Returns:
        Array of tokens
    """
    text_str = str(text.value) if hasattr(text, 'value') else str(text)
    tokenizer = Tokenizer(language="auto")
    tokens = tokenizer.tokenize(text_str)
    token_list = [to_null(token.text) for token in tokens]
    return to_null(token_list)


def INTENT(ctx: NullCallContext, text: NullValue) -> NullValue:
    """
    Detect intent from input text.

    Args:
        ctx: Call context
        text: Text to analyze

    Returns:
        Object with intent name and confidence
    """
    text_str = str(text.value) if hasattr(text, 'value') else str(text)
    detector = IntentDetector(language="auto")
    intent = detector.get_primary_intent(text_str)

    if intent:
        return to_null({
            "name": intent.name,
            "confidence": intent.confidence,
            "tokens": intent.tokens,
        })
    else:
        return to_null({
            "name": "UNKNOWN",
            "confidence": 0.0,
            "tokens": [],
        })


def ENTITIES(ctx: NullCallContext, text: NullValue) -> NullValue:
    """
    Extract entities from input text.

    Args:
        ctx: Call context
        text: Text to analyze

    Returns:
        Array of entity objects
    """
    text_str = str(text.value) if hasattr(text, 'value') else str(text)
    extractor = EntityExtractor()
    entities = extractor.extract(text_str)

    entity_list = [
        to_null({
            "text": entity.text,
            "type": entity.entity_type.value,
            "position": entity.start_position,
            "confidence": entity.confidence,
        })
        for entity in entities
    ]
    return to_null(entity_list)


def TRANSLATE(ctx: NullCallContext, text: NullValue, target_lang: NullValue) -> NullValue:
    """
    Translate text to target language.

    Args:
        ctx: Call context
        text: Text to translate
        target_lang: Target language code

    Returns:
        Translated text
    """
    text_str = str(text.value) if hasattr(text, 'value') else str(text)
    target_str = str(target_lang.value) if hasattr(target_lang, 'value') else str(target_lang)

    translator = Translator()
    # Auto-detect source language
    from ..nlp.tokenizer import Tokenizer as Tok
    tokenizer = Tok(language="auto")
    source_lang = tokenizer._detect_language(text_str)

    translation = translator.translate(text_str, source_lang, target_str)
    return to_null({
        "original": translation.source_text,
        "translated": translation.target_text,
        "source_lang": translation.source_language,
        "target_lang": translation.target_language,
        "confidence": translation.confidence,
    })


def CODEGEN(ctx: NullCallContext, text: NullValue, target_lang: NullValue) -> NullValue:
    """
    Generate Null code from natural language.

    Args:
        ctx: Call context
        text: Natural language description
        target_lang: Target code language ('null' or 'python')

    Returns:
        Generated code object
    """
    text_str = str(text.value) if hasattr(text, 'value') else str(text)
    target_str = str(target_lang.value) if hasattr(target_lang, 'value') else str(target_lang)

    codegen = CodeGenerator(language="auto")
    result = codegen.generate(text_str, target_language=target_str)

    return to_null({
        "code": result.generated_code,
        "intent": result.intent.name if result.intent else None,
        "confidence": result.confidence,
        "language": result.language,
    })
