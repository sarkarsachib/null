"""ML operations for Null-Lang library."""

from typing import Any
import numpy as np

from ..runtime import NullCallContext
from ..types import NullValue, to_null


# Global ML engine instance
_engine_instance = None


def _get_ml_engine():
    """Get or create the global ML engine."""
    global _engine_instance
    if _engine_instance is None:
        from ..ml import NullMLEngine, MLRuntimeConfig
        config = MLRuntimeConfig(
            device="cpu",
            quantization_bits=8,
            enable_caching=True,
            enable_profiling=False,
        )
        _engine_instance = NullMLEngine(config=config)
    return _engine_instance


def LOAD_MODEL(ctx: NullCallContext, model_name: NullValue) -> NullValue:
    """Load a machine learning model.

    Args:
        ctx: Call context
        model_name: Name of model to load (e.g., 'resnet18')

    Returns:
        Model metadata object
    """
    engine = _get_ml_engine()
    model_str = str(model_name.value) if hasattr(model_name, 'value') else str(model_name)
    
    try:
        metadata = engine.load_model(model_str)
        return to_null({
            "name": metadata["name"],
            "type": metadata["type"],
            "size_mb": metadata["size_bytes"] / 1e6,
            "quantized": metadata["quantized"],
        })
    except Exception as e:
        return to_null({"error": str(e)})


def INFER(ctx: NullCallContext, model_name: NullValue, input_data: NullValue) -> NullValue:
    """Run inference on a model.

    Args:
        ctx: Call context
        model_name: Model name
        input_data: Input tensor/array

    Returns:
        Inference result with output and metadata
    """
    engine = _get_ml_engine()
    model_str = str(model_name.value) if hasattr(model_name, 'value') else str(model_name)
    
    try:
        # Convert input to numpy array
        if hasattr(input_data, 'value'):
            data = input_data.value
        else:
            data = input_data
        
        if isinstance(data, list):
            data = np.array(data, dtype=np.float32)
        elif not isinstance(data, np.ndarray):
            data = np.array([data], dtype=np.float32)
        
        result = engine.infer(model_str, data)
        
        return to_null({
            "model": result["model"],
            "output_shape": list(result["output_shape"]),
            "output_size": int(np.prod(result["output_shape"])),
            "success": True,
        })
    except Exception as e:
        return to_null({"error": str(e), "success": False})


def EMBED(ctx: NullCallContext, model_name: NullValue, input_data: NullValue) -> NullValue:
    """Generate embeddings from a model.

    Args:
        ctx: Call context
        model_name: Model name
        input_data: Input tensor/array

    Returns:
        Embedding vector
    """
    engine = _get_ml_engine()
    model_str = str(model_name.value) if hasattr(model_name, 'value') else str(model_name)
    
    try:
        # Convert input to numpy array
        if hasattr(input_data, 'value'):
            data = input_data.value
        else:
            data = input_data
        
        if isinstance(data, list):
            data = np.array(data, dtype=np.float32)
        elif not isinstance(data, np.ndarray):
            data = np.array([data], dtype=np.float32)
        
        embedding = engine.embed(model_str, data)
        
        return to_null({
            "embedding_shape": list(embedding.shape),
            "embedding_dim": int(embedding.shape[-1]),
            "success": True,
        })
    except Exception as e:
        return to_null({"error": str(e), "success": False})


def ATTEND(
    ctx: NullCallContext,
    query: NullValue,
    key: NullValue,
    value: NullValue,
) -> NullValue:
    """Apply attention mechanism.

    Args:
        ctx: Call context
        query: Query tensor
        key: Key tensor
        value: Value tensor

    Returns:
        Attention output
    """
    engine = _get_ml_engine()
    
    try:
        # Convert inputs
        q = np.array(query.value if hasattr(query, 'value') else query, dtype=np.float32)
        k = np.array(key.value if hasattr(key, 'value') else key, dtype=np.float32)
        v = np.array(value.value if hasattr(value, 'value') else value, dtype=np.float32)
        
        result = engine.attend(q, k, v, probabilistic=False)
        
        return to_null({
            "output_shape": list(result["output"].shape),
            "type": result["type"],
            "success": True,
        })
    except Exception as e:
        return to_null({"error": str(e), "success": False})


def TUNE(
    ctx: NullCallContext,
    method: NullValue,
    iterations: NullValue,
) -> NullValue:
    """Tune model parameters without gradients.

    Args:
        ctx: Call context
        method: Optimization method ('nelder_mead', 'cmaes', 'random_search')
        iterations: Maximum iterations

    Returns:
        Tuning metadata
    """
    engine = _get_ml_engine()
    
    try:
        method_str = str(method.value) if hasattr(method, 'value') else str(method)
        iter_int = int(iterations.value) if hasattr(iterations, 'value') else int(iterations)
        
        # Dummy objective for testing
        def dummy_objective(params):
            return np.sum(params ** 2)
        
        initial = np.random.randn(10).astype(np.float32)
        best_params, best_loss, history = engine.tune(
            dummy_objective,
            initial,
            method=method_str,
            max_iterations=iter_int,
        )
        
        return to_null({
            "method": method_str,
            "iterations": iter_int,
            "best_loss": float(best_loss),
            "success": True,
        })
    except Exception as e:
        return to_null({"error": str(e), "success": False})
