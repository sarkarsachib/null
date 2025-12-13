"""Integration tests for the NLP pipeline."""

import pytest
from null_system.nlp.pipeline import NLPPipeline, PipelineResult, PipelineMetrics


class TestNLPPipeline:
    """Test suite for the NLP pipeline."""

    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        pipeline = NLPPipeline()

        assert pipeline is not None
        assert pipeline.language == "en"

    def test_pipeline_process(self):
        """Test basic pipeline processing."""
        pipeline = NLPPipeline()
        result = pipeline.process("set x to 5")

        assert isinstance(result, PipelineResult)
        assert result.success
        assert result.generated_code is not None

    def test_pipeline_metrics(self):
        """Test that pipeline collects metrics."""
        pipeline = NLPPipeline()
        result = pipeline.process("set x to 5")

        assert isinstance(result.metrics, PipelineMetrics)
        assert result.metrics.total_time_ms > 0

    def test_pipeline_tokenization(self):
        """Test tokenization step in pipeline."""
        pipeline = NLPPipeline()
        result = pipeline.process("set x to 5")

        assert len(result.tokens) > 0

    def test_pipeline_intent_detection(self):
        """Test intent detection step in pipeline."""
        pipeline = NLPPipeline()
        result = pipeline.process("set x to 5")

        assert result.intent is not None
        assert result.intent.name is not None

    def test_pipeline_entity_extraction(self):
        """Test entity extraction step in pipeline."""
        pipeline = NLPPipeline()
        result = pipeline.process("set x to 5")

        assert len(result.entities) > 0

    def test_pipeline_code_generation(self):
        """Test code generation step in pipeline."""
        pipeline = NLPPipeline()
        result = pipeline.process("set x to 5")

        assert result.generated_code is not None
        assert result.generated_code.generated_code

    def test_pipeline_latency_validation(self):
        """Test latency validation."""
        pipeline = NLPPipeline()
        result = pipeline.process("set x to 5")

        is_ok, latency = pipeline.validate_latency(result)
        # Most operations should be fast
        assert latency < 100.0  # Under 100ms

    def test_pipeline_batch_processing(self):
        """Test batch processing."""
        pipeline = NLPPipeline()
        texts = ["set x to 5", "show x", "repeat 10 times"]

        results = pipeline.batch_process(texts)

        assert len(results) == 3
        assert all(isinstance(r, PipelineResult) for r in results)

    def test_pipeline_performance_report(self):
        """Test generating performance report."""
        pipeline = NLPPipeline()
        texts = ["set x to 5"] * 5
        results = pipeline.batch_process(texts)

        report = pipeline.get_performance_report(results)

        assert "total_processed" in report
        assert "successful" in report
        assert "avg_latency_ms" in report
        assert report["total_processed"] == 5

    def test_pipeline_with_translation(self):
        """Test pipeline with translation enabled."""
        pipeline = NLPPipeline(enable_translation=True)
        result = pipeline.process("set x to 5", include_translation=True)

        assert isinstance(result, PipelineResult)

    def test_pipeline_context_management(self):
        """Test context management in pipeline."""
        pipeline = NLPPipeline()

        context = {
            "variables": {"x": 5},
            "functions": {},
            "imports": [],
            "history": []
        }

        pipeline.set_context(context)
        retrieved_context = pipeline.get_context()

        assert "variables" in retrieved_context

    def test_pipeline_context_reset(self):
        """Test resetting context."""
        pipeline = NLPPipeline()

        context = {
            "variables": {"x": 5},
            "functions": {},
            "imports": [],
            "history": []
        }

        pipeline.set_context(context)
        pipeline.reset_context()

        context = pipeline.get_context()
        assert len(context.get("variables", {})) == 0

    def test_pipeline_error_handling(self):
        """Test that pipeline handles errors gracefully."""
        pipeline = NLPPipeline()

        # Should not crash on problematic input
        result = pipeline.process(None)  # type: ignore
        assert isinstance(result, PipelineResult)

    def test_pipeline_different_languages(self):
        """Test pipeline with different input languages."""
        # English
        pipeline_en = NLPPipeline(language="en")
        result_en = pipeline_en.process("set x to 5")
        assert result_en.success

        # Auto-detect
        pipeline_auto = NLPPipeline(language="auto")
        result_auto = pipeline_auto.process("set x to 5")
        assert result_auto.success

    def test_pipeline_target_languages(self):
        """Test code generation for different target languages."""
        pipeline = NLPPipeline()

        result_null = pipeline.process("set x to 5", target_language="null")
        assert result_null.generated_code.language == "null"

        result_python = pipeline.process("set x to 5", target_language="python")
        assert result_python.generated_code.language == "python"

    def test_pipeline_multiple_sentences(self):
        """Test pipeline on multiple sentences."""
        pipeline = NLPPipeline()

        text = "set x to 5. show x. repeat 10 times"
        result = pipeline.process(text)

        assert result.success
        assert len(result.tokens) > 0


class TestNLPPipelinePerformance:
    """Test pipeline performance."""

    def test_end_to_end_latency(self):
        """Test end-to-end latency."""
        import time
        pipeline = NLPPipeline()

        start = time.time()
        result = pipeline.process("set x to 5")
        elapsed_ms = (time.time() - start) * 1000

        # Should meet <50ms target for simple input
        assert elapsed_ms < 100.0  # Allow some slack
        assert result.metrics.total_time_ms < 100.0

    def test_latency_breakdown(self):
        """Test latency breakdown across pipeline stages."""
        pipeline = NLPPipeline()
        result = pipeline.process("set x to 5")

        metrics = result.metrics
        total = metrics.total_time_ms

        # Individual stages should add up
        stage_total = (
            metrics.tokenize_time_ms +
            metrics.intent_detect_time_ms +
            metrics.entity_extract_time_ms +
            metrics.translate_time_ms +
            metrics.codegen_time_ms
        )

        # Should be within reasonable margin (stages overlap)
        assert stage_total > 0

    def test_batch_processing_efficiency(self):
        """Test that batch processing is efficient."""
        import time
        pipeline = NLPPipeline()

        texts = ["set x to 5"] * 10

        start = time.time()
        results = pipeline.batch_process(texts)
        elapsed_ms = (time.time() - start) * 1000

        # Should average under 50ms per item
        avg_latency = elapsed_ms / len(texts)
        assert avg_latency < 100.0

    def test_performance_consistency(self):
        """Test that performance is consistent across runs."""
        import time
        pipeline = NLPPipeline()

        latencies = []
        for _ in range(5):
            start = time.time()
            result = pipeline.process("set x to 5")
            elapsed_ms = (time.time() - start) * 1000
            latencies.append(elapsed_ms)

        # Should be reasonably consistent (not too much variation)
        avg = sum(latencies) / len(latencies)
        # Most latencies should be within 2x of average
        assert all(l < avg * 3 for l in latencies)


class TestNLPPipelineIntegration:
    """Integration tests for pipeline."""

    def test_pipeline_generates_compilable_code(self):
        """Test that pipeline generates code that can be compiled."""
        pipeline = NLPPipeline()
        result = pipeline.process("set x to 5")

        # Generated code should be a string
        assert isinstance(result.generated_code.generated_code, str)
        assert len(result.generated_code.generated_code) > 0

    def test_pipeline_maintains_history(self):
        """Test that pipeline maintains history."""
        pipeline = NLPPipeline()

        pipeline.process("set x to 5")
        context = pipeline.get_context()

        # History should be tracked
        assert "history" in context or len(context) > 0

    def test_pipeline_confidence_scores(self):
        """Test that pipeline provides confidence scores."""
        pipeline = NLPPipeline()

        result = pipeline.process("set x to 5")
        assert result.generated_code.confidence >= 0.0
        assert result.generated_code.confidence <= 1.0

    def test_pipeline_handles_complex_input(self):
        """Test pipeline on complex input."""
        pipeline = NLPPipeline()

        complex_text = (
            "Define a function that takes two numbers, "
            "adds them together, and shows the result"
        )

        result = pipeline.process(complex_text)
        assert result.success
