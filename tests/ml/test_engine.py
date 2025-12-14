"""Tests for ML inference engine."""

import pytest
import numpy as np
from null_system.ml import (
    NullMLEngine,
    MLRuntimeConfig,
    SuperBitQuantizer,
    SemanticEmbedder,
)


class TestMLEngine:
    """Test ML engine basics."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        config = MLRuntimeConfig(device="cpu")
        engine = NullMLEngine(config=config)
        
        assert engine is not None
        assert engine.config.device == "cpu"
        assert engine.config.quantization_bits == 8

    def test_quantizer_initialization(self):
        """Test quantizer initialization."""
        quantizer = SuperBitQuantizer(bits=8)
        assert quantizer.bits == 8
        assert quantizer.scale == 255

    def test_quantizer_invalid_bits(self):
        """Test quantizer with invalid bits."""
        with pytest.raises(ValueError):
            SuperBitQuantizer(bits=16)

    def test_quantization_simple(self):
        """Test basic quantization."""
        quantizer = SuperBitQuantizer(bits=8)
        tensor = np.array([0.0, 0.5, 1.0], dtype=np.float32)
        
        quantized, min_val, max_val = quantizer.quantize(tensor)
        
        assert quantized is not None
        assert min_val == 0.0
        assert max_val == 1.0

    def test_dequantization(self):
        """Test dequantization."""
        quantizer = SuperBitQuantizer(bits=8)
        original = np.array([-1.0, 0.0, 1.0], dtype=np.float32)
        
        quantized, min_val, max_val = quantizer.quantize(original)
        dequantized = quantizer.dequantize(quantized, min_val, max_val)
        
        # Check that dequantized is close to original
        assert dequantized.shape == original.shape
        assert np.allclose(dequantized, original, atol=0.1)

    def test_embedding_generation(self):
        """Test semantic embedding generation."""
        embedder = SemanticEmbedder(embedding_dim=768)
        text = "hello world"
        
        embedding = embedder.embed(text)
        
        assert embedding.shape == (768,)
        assert np.all(np.isfinite(embedding))

    def test_embedding_deterministic(self):
        """Test that embeddings are deterministic."""
        embedder = SemanticEmbedder(embedding_dim=768)
        text = "hello world"
        
        emb1 = embedder.embed(text)
        emb2 = embedder.embed(text)
        
        assert np.allclose(emb1, emb2)

    def test_embedding_similarity(self):
        """Test embedding similarity."""
        embedder = SemanticEmbedder(embedding_dim=768)
        
        text1 = "hello world"
        text2 = "hello world"
        text3 = "goodbye world"
        
        emb1 = embedder.embed(text1)
        emb2 = embedder.embed(text2)
        emb3 = embedder.embed(text3)
        
        sim_same = embedder.similarity(emb1, emb2)
        sim_diff = embedder.similarity(emb1, emb3)
        
        assert sim_same > 0.9  # Same text
        assert 0 <= sim_diff <= 1


class TestSuperBitTensor:
    """Test SuperBitTensor."""

    def test_superbit_tensor_creation(self):
        """Test creating a SuperBitTensor."""
        from null_system.ml.quantization import SuperBitTensor
        
        data = np.array([0, 128, 255], dtype=np.uint8)
        tensor = SuperBitTensor(data, min_val=0.0, max_val=1.0, bits=8, shape=(3,))
        
        assert tensor.bits == 8
        assert tensor.shape == (3,)

    def test_superbit_tensor_dequantize(self):
        """Test SuperBitTensor dequantization."""
        from null_system.ml.quantization import SuperBitTensor
        
        data = np.array([0, 128, 255], dtype=np.uint8)
        tensor = SuperBitTensor(data, min_val=0.0, max_val=1.0, bits=8, shape=(3,))
        
        dequantized = tensor.dequantize()
        
        assert dequantized.shape == (3,)
        assert np.all(dequantized >= 0.0)
        assert np.all(dequantized <= 1.0)

    def test_superbit_tensor_serialization(self):
        """Test SuperBitTensor serialization."""
        from null_system.ml.quantization import SuperBitTensor
        
        data = np.array([0, 128, 255], dtype=np.uint8)
        tensor = SuperBitTensor(data, min_val=0.0, max_val=1.0, bits=8, shape=(3,))
        
        # Serialize
        serialized = tensor.to_bytes()
        assert isinstance(serialized, bytes)
        
        # Deserialize
        restored = SuperBitTensor.from_bytes(serialized)
        assert restored.bits == 8
        assert restored.shape == (3,)


class TestMemoryEstimation:
    """Test memory estimation."""

    def test_quantizer_size_estimation(self):
        """Test quantizer size estimation."""
        quantizer = SuperBitQuantizer(bits=8)
        
        shape = (1000, 1000)
        size = quantizer.estimate_size(shape)
        
        expected = 1000000  # bytes for 8-bit
        assert size == expected

    def test_quantizer_size_4bit(self):
        """Test quantizer size estimation for 4-bit."""
        quantizer = SuperBitQuantizer(bits=4)
        
        shape = (1000, 1000)
        size = quantizer.estimate_size(shape)
        
        expected = 500000  # bytes for 4-bit
        assert size == expected
