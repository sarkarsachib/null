"""Integration tests for Null-Lang with ML operations."""

import pytest
from null_system.lib.registry import default_registry
from null_system.runtime import NullCallContext
from null_system.types import to_null


class TestMLLibraryIntegration:
    """Test ML library integration with Null-Lang."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = default_registry()
        self.context = NullCallContext()

    def test_ml_load_model_available(self):
        """Test that ml.LOAD_MODEL is available."""
        self.registry.require("ml.LOAD_MODEL")
        
        fn = self.registry.resolve("ml.LOAD_MODEL")
        assert fn.path == "ml.LOAD_MODEL"
        assert fn.arity == 1

    def test_ml_infer_available(self):
        """Test that ml.INFER is available."""
        self.registry.require("ml.INFER")
        
        fn = self.registry.resolve("ml.INFER")
        assert fn.path == "ml.INFER"
        assert fn.arity == 2

    def test_ml_embed_available(self):
        """Test that ml.EMBED is available."""
        self.registry.require("ml.EMBED")
        
        fn = self.registry.resolve("ml.EMBED")
        assert fn.path == "ml.EMBED"
        assert fn.arity == 2

    def test_ml_attend_available(self):
        """Test that ml.ATTEND is available."""
        self.registry.require("ml.ATTEND")
        
        fn = self.registry.resolve("ml.ATTEND")
        assert fn.path == "ml.ATTEND"
        assert fn.arity == 3

    def test_ml_tune_available(self):
        """Test that ml.TUNE is available."""
        self.registry.require("ml.TUNE")
        
        fn = self.registry.resolve("ml.TUNE")
        assert fn.path == "ml.TUNE"
        assert fn.arity == 2

    def test_load_model_execution(self):
        """Test executing ml.LOAD_MODEL."""
        result = self.registry.call("ml.LOAD_MODEL", self.context, [to_null("resnet18")])
        
        assert result is not None
        # Result should be a Null value

    def test_all_ml_functions_registered(self):
        """Test that all ML functions are registered."""
        ml_functions = [
            "ml.LOAD_MODEL",
            "ml.INFER",
            "ml.EMBED",
            "ml.ATTEND",
            "ml.TUNE",
        ]
        
        for fn_path in ml_functions:
            self.registry.require(fn_path)


class TestNullMLOpsInitialization:
    """Test NullML ops initialization."""

    def test_ml_ops_imports(self):
        """Test that ML ops can be imported."""
        from null_system.lib import ml_ops
        
        assert hasattr(ml_ops, "LOAD_MODEL")
        assert hasattr(ml_ops, "INFER")
        assert hasattr(ml_ops, "EMBED")
        assert hasattr(ml_ops, "ATTEND")
        assert hasattr(ml_ops, "TUNE")

    def test_ml_engine_creation(self):
        """Test creating ML engine."""
        from null_system.ml import NullMLEngine, MLRuntimeConfig
        
        config = MLRuntimeConfig(device="cpu")
        engine = NullMLEngine(config=config)
        
        assert engine is not None
        assert engine.config.device == "cpu"


class TestMLBenchmark:
    """Test ML benchmarking."""

    def test_benchmark_metrics(self):
        """Test benchmark metrics."""
        from null_system.ml.benchmarks import BenchmarkMetrics
        
        metrics = BenchmarkMetrics()
        metrics.latencies = [10.0, 12.0, 11.5, 13.0, 12.5]
        metrics.memory_peak = 100.0
        metrics.memory_avg = 95.0
        metrics.throughput = 100.0
        
        d = metrics.to_dict()
        
        assert "latency_min" in d
        assert "latency_max" in d
        assert "latency_mean" in d
        assert d["memory_peak_mb"] == 100.0

    def test_latency_profiler(self):
        """Test latency profiler."""
        from null_system.ml.benchmarks import LatencyProfiler
        import time
        
        profiler = LatencyProfiler()
        
        def dummy_fn():
            time.sleep(0.001)
        
        profiler.measure("test_op", dummy_fn)
        stats = profiler.get_stats("test_op")
        
        assert "min" in stats
        assert "max" in stats
        assert "mean" in stats
        assert stats["count"] == 1
