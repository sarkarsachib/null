"""Main NLP pipeline for Null-Lang."""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from .tokenizer import Tokenizer, Token
from .embeddings import EmbeddingModel
from .intent import IntentDetector, Intent
from .entity_extraction import EntityExtractor, Entity
from .translation import Translator, Translation
from .codegen import CodeGenerator, GeneratedCode
from .context import ContextManager


@dataclass
class PipelineMetrics:
    """Metrics for pipeline execution."""
    total_time_ms: float
    tokenize_time_ms: float
    intent_detect_time_ms: float
    entity_extract_time_ms: float
    translate_time_ms: float
    codegen_time_ms: float

    def __repr__(self) -> str:
        return (f"PipelineMetrics(total={self.total_time_ms:.2f}ms, "
                f"tokenize={self.tokenize_time_ms:.2f}ms, "
                f"intent={self.intent_detect_time_ms:.2f}ms)")


@dataclass
class PipelineResult:
    """Result of NLP pipeline processing."""
    input_text: str
    tokens: List[Token]
    intent: Optional[Intent]
    entities: List[Entity]
    translation: Optional[Translation]
    generated_code: GeneratedCode
    metrics: PipelineMetrics
    success: bool = True
    error: Optional[str] = None

    def __repr__(self) -> str:
        return f"PipelineResult(success={self.success}, tokens={len(self.tokens)})"


class NLPPipeline:
    """Complete NLP pipeline for Null-Lang."""

    def __init__(self, language: str = "en", enable_translation: bool = False):
        """
        Initialize the NLP pipeline.

        Args:
            language: Input language code ('en', 'es', 'zh', 'auto')
            enable_translation: Whether to enable automatic translation
        """
        self.language = language
        self.enable_translation = enable_translation

        # Initialize components
        self.tokenizer = Tokenizer(language=language)
        self.embedding_model = EmbeddingModel()
        self.intent_detector = IntentDetector(language=language)
        self.entity_extractor = EntityExtractor()
        self.translator = Translator()
        self.codegen = CodeGenerator(language=language)
        self.context_manager = ContextManager()

        # Performance thresholds
        self.max_latency_ms = 50.0

    def process(self, text: str, target_language: str = "null",
               include_translation: bool = False) -> PipelineResult:
        """
        Process text through the complete NLP pipeline.

        Args:
            text: Input text
            target_language: Target code language ('null', 'python')
            include_translation: Whether to translate before processing

        Returns:
            PipelineResult with all processing results
        """
        start_time = time.time()
        metrics_dict = {}

        try:
            # Step 1: Tokenization
            token_start = time.time()
            tokens = self.tokenizer.tokenize(text)
            metrics_dict["tokenize_time_ms"] = (time.time() - token_start) * 1000

            # Step 2: Intent Detection
            intent_start = time.time()
            intent = self.intent_detector.get_primary_intent(text)
            metrics_dict["intent_detect_time_ms"] = (time.time() - intent_start) * 1000

            # Step 3: Entity Extraction
            entity_start = time.time()
            entities = self.entity_extractor.extract(text)
            metrics_dict["entity_extract_time_ms"] = (time.time() - entity_start) * 1000

            # Step 4: Translation (optional)
            translation = None
            metrics_dict["translate_time_ms"] = 0.0
            if include_translation and self.enable_translation:
                trans_start = time.time()
                detected_lang = self.tokenizer._detect_language(text)
                if detected_lang != "en":
                    translation = self.translator.translate(text, detected_lang, "en")
                    text_for_codegen = translation.target_text
                else:
                    text_for_codegen = text
                metrics_dict["translate_time_ms"] = (time.time() - trans_start) * 1000
            else:
                text_for_codegen = text

            # Step 5: Code Generation
            codegen_start = time.time()
            generated_code = self.codegen.generate(text_for_codegen, target_language)
            metrics_dict["codegen_time_ms"] = (time.time() - codegen_start) * 1000

            # Record in context history
            self.context_manager.add_to_history(generated_code.generated_code)

            # Calculate total time
            total_time = (time.time() - start_time) * 1000

            metrics = PipelineMetrics(
                total_time_ms=total_time,
                tokenize_time_ms=metrics_dict.get("tokenize_time_ms", 0.0),
                intent_detect_time_ms=metrics_dict.get("intent_detect_time_ms", 0.0),
                entity_extract_time_ms=metrics_dict.get("entity_extract_time_ms", 0.0),
                translate_time_ms=metrics_dict.get("translate_time_ms", 0.0),
                codegen_time_ms=metrics_dict.get("codegen_time_ms", 0.0),
            )

            return PipelineResult(
                input_text=text,
                tokens=tokens,
                intent=intent,
                entities=entities,
                translation=translation,
                generated_code=generated_code,
                metrics=metrics,
                success=True
            )

        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            metrics = PipelineMetrics(
                total_time_ms=total_time,
                tokenize_time_ms=metrics_dict.get("tokenize_time_ms", 0.0),
                intent_detect_time_ms=metrics_dict.get("intent_detect_time_ms", 0.0),
                entity_extract_time_ms=metrics_dict.get("entity_extract_time_ms", 0.0),
                translate_time_ms=metrics_dict.get("translate_time_ms", 0.0),
                codegen_time_ms=metrics_dict.get("codegen_time_ms", 0.0),
            )

            return PipelineResult(
                input_text=text,
                tokens=[],
                intent=None,
                entities=[],
                translation=None,
                generated_code=GeneratedCode(
                    source_text=text,
                    generated_code="",
                    intent=None,
                    entities=[],
                    confidence=0.0
                ),
                metrics=metrics,
                success=False,
                error=str(e)
            )

    def batch_process(self, texts: List[str], target_language: str = "null",
                     include_translation: bool = False) -> List[PipelineResult]:
        """
        Process multiple texts through the pipeline.

        Args:
            texts: List of input texts
            target_language: Target code language
            include_translation: Whether to translate

        Returns:
            List of PipelineResult objects
        """
        return [
            self.process(text, target_language, include_translation)
            for text in texts
        ]

    def validate_latency(self, result: PipelineResult) -> Tuple[bool, float]:
        """
        Check if processing latency is within acceptable bounds.

        Args:
            result: Pipeline result

        Returns:
            Tuple of (is_within_bounds, latency_ms)
        """
        latency = result.metrics.total_time_ms
        is_ok = latency <= self.max_latency_ms
        return is_ok, latency

    def get_performance_report(self, results: List[PipelineResult]) -> Dict[str, float]:
        """
        Generate a performance report for multiple results.

        Args:
            results: List of pipeline results

        Returns:
            Dictionary with performance metrics
        """
        if not results:
            return {}

        latencies = [r.metrics.total_time_ms for r in results]
        successes = [r.success for r in results]

        return {
            "total_processed": len(results),
            "successful": sum(successes),
            "failed": len(results) - sum(successes),
            "success_rate": sum(successes) / len(results) if results else 0.0,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
            "min_latency_ms": min(latencies) if latencies else 0.0,
            "max_latency_ms": max(latencies) if latencies else 0.0,
            "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0.0,
        }

    def set_context(self, context_dict: Dict) -> None:
        """
        Set the execution context.

        Args:
            context_dict: Dictionary with context information
        """
        self.context_manager.import_context(context_dict)

    def get_context(self) -> Dict:
        """
        Get the current execution context.

        Returns:
            Dictionary with context information
        """
        return self.context_manager.export_context()

    def reset_context(self) -> None:
        """Reset the execution context."""
        self.context_manager.clear_context()

    def enable_profiling(self, enable: bool = True) -> None:
        """
        Enable or disable profiling.

        Args:
            enable: Whether to enable profiling
        """
        self.profiling_enabled = enable
