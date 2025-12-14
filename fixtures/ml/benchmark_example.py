"""Example benchmark script for Null-ML."""

import numpy as np
from null_system.ml import NullMLEngine, MLRuntimeConfig
from null_system.ml.benchmarks import ModelBenchmark


def benchmark_resnet18():
    """Benchmark ResNet18 inference."""
    # Initialize engine
    config = MLRuntimeConfig(device="cpu", enable_profiling=True)
    engine = NullMLEngine(config=config)
    
    # Create dummy input
    dummy_input = np.random.randn(1, 3, 224, 224).astype(np.float32)
    
    # Run benchmark
    def inference_fn():
        engine.torch_engine.infer_resnet18(dummy_input)
    
    benchmark = ModelBenchmark(warmup_runs=5, num_runs=100)
    model_meta = engine.load_model("resnet18")
    model_size = model_meta["size_bytes"]
    
    metrics = benchmark.benchmark(inference_fn, model_size)
    
    print("ResNet18 Benchmark Results:")
    print("=" * 50)
    print(metrics)
    print("=" * 50)
    
    # Check acceptance criteria
    latency_mean = np.mean(metrics.latencies)
    memory_peak = metrics.memory_peak
    
    print(f"\nAcceptance Criteria:")
    print(f"  ✓ Mean latency <100ms: {latency_mean:.2f}ms" if latency_mean < 100 else 
          f"  ✗ Mean latency <100ms: {latency_mean:.2f}ms")
    print(f"  ✓ Peak memory <10MB: {memory_peak:.2f}MB" if memory_peak < 10 else 
          f"  ✗ Peak memory <10MB: {memory_peak:.2f}MB")


if __name__ == "__main__":
    benchmark_resnet18()
