"""Null-ML: Production-ready ML inference engine for Null-Lang.

This module provides:
- PyTorch/TensorFlow-backed inference
- Super-bit quantization (<10MB models)
- Semantic embeddings
- Probabilistic attention
- Gradient-free optimization
- Benchmarking utilities
"""

from .engine import NullMLEngine, MLRuntimeConfig
from .quantization import SuperBitQuantizer, SuperBitTensor
from .embeddings import SemanticEmbedder, PoolingStrategy, EmbeddingCache
from .attention import MultiHeadAttention, ProbabilisticAttention
from .optimizers import (
    GradientFreeOptimizer,
    NelderMeadOptimizer,
    CMAESOptimizer,
    RandomSearchOptimizer,
)
from .benchmarks import BenchmarkMetrics, ModelBenchmark, LatencyProfiler, MemoryProfiler

__all__ = [
    "NullMLEngine",
    "MLRuntimeConfig",
    "SuperBitQuantizer",
    "SuperBitTensor",
    "SemanticEmbedder",
    "PoolingStrategy",
    "EmbeddingCache",
    "MultiHeadAttention",
    "ProbabilisticAttention",
    "GradientFreeOptimizer",
    "NelderMeadOptimizer",
    "CMAESOptimizer",
    "RandomSearchOptimizer",
    "BenchmarkMetrics",
    "ModelBenchmark",
    "LatencyProfiler",
    "MemoryProfiler",
]
