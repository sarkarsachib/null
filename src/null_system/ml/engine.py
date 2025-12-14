"""Production-ready ML inference engine."""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from pathlib import Path

from .quantization import SuperBitQuantizer, SuperBitTensor
from .embeddings import SemanticEmbedder, EmbeddingCache
from .attention import MultiHeadAttention, ProbabilisticAttention
from .optimizers import NelderMeadOptimizer, CMAESOptimizer, RandomSearchOptimizer
from .benchmarks import ModelBenchmark, BenchmarkMetrics, LatencyProfiler


class MLRuntimeConfig:
    """Configuration for ML runtime."""

    def __init__(
        self,
        device: str = "cpu",
        quantization_bits: int = 8,
        enable_caching: bool = True,
        cache_size: int = 10000,
        enable_profiling: bool = False,
    ):
        """Initialize config.
        
        Args:
            device: Device to use ('cpu' or 'cuda')
            quantization_bits: Quantization bits
            enable_caching: Enable embedding caching
            cache_size: Cache size
            enable_profiling: Enable profiling
        """
        self.device = device
        self.quantization_bits = quantization_bits
        self.enable_caching = enable_caching
        self.cache_size = cache_size
        self.enable_profiling = enable_profiling


class NullMLEngine:
    """Production-ready ML inference engine for Null-Lang."""

    def __init__(self, config: Optional[MLRuntimeConfig] = None):
        """Initialize ML engine.
        
        Args:
            config: Runtime configuration
        """
        self.config = config or MLRuntimeConfig()
        self.quantizer = SuperBitQuantizer(bits=self.config.quantization_bits)
        self.embedder = SemanticEmbedder(embedding_dim=768)
        self.embedding_cache = EmbeddingCache(max_size=self.config.cache_size)
        self.attention = MultiHeadAttention(hidden_dim=768)
        self.profiler = LatencyProfiler() if self.config.enable_profiling else None
        
        # Try to load PyTorch backend
        try:
            from .backends.torch_backend import TorchInferenceEngine
            self.torch_engine = TorchInferenceEngine(device=self.config.device)
        except Exception:
            self.torch_engine = None
        
        self.loaded_models = {}

    def load_model(self, model_name: str) -> Dict[str, Any]:
        """Load a model.
        
        Args:
            model_name: Model name
            
        Returns:
            Model metadata
        """
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        if model_name == "resnet18":
            if self.torch_engine is None:
                raise RuntimeError("PyTorch engine not available")
            
            model = self.torch_engine.load_resnet18()
            size = self.torch_engine.backend.get_model_size(model)
            
            metadata = {
                "name": model_name,
                "type": "image_classification",
                "input_shape": (3, 224, 224),
                "output_size": 1000,
                "size_bytes": size,
                "quantized": False,
            }
            
            self.loaded_models[model_name] = metadata
            return metadata
        
        raise ValueError(f"Unknown model: {model_name}")

    def infer(self, model_name: str, input_data: np.ndarray) -> Dict[str, Any]:
        """Run inference.
        
        Args:
            model_name: Model name
            input_data: Input data
            
        Returns:
            Inference result
        """
        metadata = self.load_model(model_name)
        
        if self.profiler:
            def _infer():
                if model_name == "resnet18":
                    return self.torch_engine.infer_resnet18(input_data)
                raise ValueError(f"Unknown model: {model_name}")
            
            output = self.profiler.measure("infer", _infer)
        else:
            if model_name == "resnet18":
                output = self.torch_engine.infer_resnet18(input_data)
            else:
                raise ValueError(f"Unknown model: {model_name}")
        
        return {
            "model": model_name,
            "output": output,
            "output_shape": output.shape,
            "output_dtype": str(output.dtype),
        }

    def embed(self, model_name: str, input_data: np.ndarray) -> np.ndarray:
        """Get embeddings.
        
        Args:
            model_name: Model name
            input_data: Input data
            
        Returns:
            Embedding vector
        """
        # Check cache
        cache_key = f"{model_name}:{hash(tuple(input_data.flat))}"
        cached = self.embedding_cache.get(cache_key)
        if cached is not None:
            return cached
        
        if model_name == "resnet18":
            embedding = self.torch_engine.embed_resnet18(input_data)
        else:
            raise ValueError(f"Unknown model: {model_name}")
        
        # Cache result
        if self.config.enable_caching:
            self.embedding_cache.put(cache_key, embedding)
        
        return embedding

    def quantize_tensor(
        self,
        tensor: np.ndarray,
    ) -> SuperBitTensor:
        """Quantize a tensor.
        
        Args:
            tensor: Tensor to quantize
            
        Returns:
            SuperBitTensor
        """
        quantized, min_val, max_val = self.quantizer.quantize(tensor)
        return SuperBitTensor(
            data=quantized,
            min_val=min_val,
            max_val=max_val,
            bits=self.config.quantization_bits,
            shape=tensor.shape,
            dtype=str(tensor.dtype),
        )

    def dequantize_tensor(self, sb_tensor: SuperBitTensor) -> np.ndarray:
        """Dequantize a super-bit tensor.
        
        Args:
            sb_tensor: SuperBitTensor to dequantize
            
        Returns:
            Dequantized tensor
        """
        return sb_tensor.dequantize()

    def attend(
        self,
        query: np.ndarray,
        key: np.ndarray,
        value: np.ndarray,
        probabilistic: bool = False,
    ) -> Dict[str, Any]:
        """Apply attention.
        
        Args:
            query: Query matrix
            key: Key matrix
            value: Value matrix
            probabilistic: Use probabilistic attention
            
        Returns:
            Attention result
        """
        if probabilistic:
            prob_attention = ProbabilisticAttention(hidden_dim=query.shape[-1])
            mean, variance, _ = prob_attention.forward(query, key, value)
            return {
                "output": mean,
                "variance": variance,
                "type": "probabilistic",
            }
        else:
            output, weights = self.attention.attention(query, key, value)
            return {
                "output": output,
                "weights": weights,
                "type": "deterministic",
            }

    def tune(
        self,
        objective_fn,
        initial_params: np.ndarray,
        method: str = "nelder_mead",
        max_iterations: int = 100,
    ) -> Tuple[np.ndarray, float, List[float]]:
        """Tune model parameters without gradients.
        
        Args:
            objective_fn: Function to minimize
            initial_params: Initial parameters
            method: Optimization method
            max_iterations: Maximum iterations
            
        Returns:
            Tuple of (best_params, best_loss, loss_history)
        """
        if method == "nelder_mead":
            optimizer = NelderMeadOptimizer()
        elif method == "cmaes":
            optimizer = CMAESOptimizer()
        elif method == "random_search":
            optimizer = RandomSearchOptimizer()
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return optimizer.optimize(objective_fn, initial_params, max_iterations)

    def benchmark(self, model_name: str) -> BenchmarkMetrics:
        """Benchmark a model.
        
        Args:
            model_name: Model name
            
        Returns:
            Benchmark metrics
        """
        self.load_model(model_name)
        
        if model_name == "resnet18":
            # Create dummy input
            dummy_input = np.random.randn(1, 3, 224, 224).astype(np.float32)
            
            def benchmark_fn():
                self.torch_engine.infer_resnet18(dummy_input)
            
            benchmark = ModelBenchmark(warmup_runs=5, num_runs=100)
            model_size = self.loaded_models[model_name]["size_bytes"]
            return benchmark.benchmark(benchmark_fn, model_size)
        
        raise ValueError(f"Unknown model: {model_name}")

    def get_profiling_stats(self) -> str:
        """Get profiling statistics.
        
        Returns:
            Profiling summary
        """
        if self.profiler is None:
            return "Profiling disabled"
        
        return self.profiler.summary()

    def estimate_memory(self, model_name: str, input_shape: Tuple[int, ...]) -> float:
        """Estimate memory usage.
        
        Args:
            model_name: Model name
            input_shape: Input shape
            
        Returns:
            Estimated memory in MB
        """
        self.load_model(model_name)
        
        model_size = self.loaded_models[model_name]["size_bytes"]
        input_size = np.prod(input_shape) * 4  # Assuming float32
        
        # Rough estimate: model + input + intermediate activations
        total = (model_size + input_size) * 1.5
        
        return total / 1e6  # Convert to MB
