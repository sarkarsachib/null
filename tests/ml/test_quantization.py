"""Tests for quantization module."""

import pytest
import numpy as np
from null_system.ml.quantization import SuperBitQuantizer, SuperBitTensor


class TestQuantization:
    """Test quantization functionality."""

    def test_quantize_uniform(self):
        """Test quantization of uniform values."""
        quantizer = SuperBitQuantizer(bits=8)
        tensor = np.ones(10, dtype=np.float32) * 0.5
        
        quantized, min_val, max_val = quantizer.quantize(tensor)
        
        assert quantized.dtype == np.uint8
        assert min_val == 0.5
        assert max_val == 0.5
        assert np.all(quantized == 0)  # Min value

    def test_quantize_range(self):
        """Test quantization of range of values."""
        quantizer = SuperBitQuantizer(bits=8)
        tensor = np.linspace(0, 1, 100, dtype=np.float32)
        
        quantized, min_val, max_val = quantizer.quantize(tensor)
        
        assert quantized.dtype == np.uint8
        assert min_val == 0.0
        assert max_val == 1.0
        assert quantized.min() == 0
        assert quantized.max() == 255

    def test_dequantize_uniform(self):
        """Test dequantization of uniform values."""
        quantizer = SuperBitQuantizer(bits=8)
        original = np.ones(10, dtype=np.float32) * 0.5
        
        quantized, min_val, max_val = quantizer.quantize(original)
        dequantized = quantizer.dequantize(quantized, min_val, max_val)
        
        assert np.allclose(dequantized, original, atol=1e-6)

    def test_dequantize_range(self):
        """Test dequantization of range."""
        quantizer = SuperBitQuantizer(bits=8)
        original = np.linspace(-1, 1, 100, dtype=np.float32)
        
        quantized, min_val, max_val = quantizer.quantize(original)
        dequantized = quantizer.dequantize(quantized, min_val, max_val)
        
        assert dequantized.shape == original.shape
        assert np.allclose(dequantized, original, atol=0.01)

    def test_quantize_4bit(self):
        """Test 4-bit quantization."""
        quantizer = SuperBitQuantizer(bits=4)
        tensor = np.linspace(0, 1, 100, dtype=np.float32)
        
        quantized, min_val, max_val = quantizer.quantize(tensor)
        
        assert quantized.dtype == np.uint8
        assert quantized.max() <= 15  # 4-bit max

    def test_quantize_negative_values(self):
        """Test quantization of negative values."""
        quantizer = SuperBitQuantizer(bits=8)
        tensor = np.array([-2.0, -1.0, 0.0, 1.0, 2.0], dtype=np.float32)
        
        quantized, min_val, max_val = quantizer.quantize(tensor)
        
        assert min_val == -2.0
        assert max_val == 2.0

    def test_quantize_zero_range(self):
        """Test quantization with zero range."""
        quantizer = SuperBitQuantizer(bits=8)
        tensor = np.ones(10, dtype=np.float32) * 5.0
        
        quantized, min_val, max_val = quantizer.quantize(tensor)
        
        # Should handle gracefully
        assert quantized is not None


class TestSuperBitTensor:
    """Test SuperBitTensor class."""

    def test_create_superbit_tensor(self):
        """Test creating SuperBitTensor."""
        data = np.array([[0, 128], [255, 64]], dtype=np.uint8)
        tensor = SuperBitTensor(
            data=data,
            min_val=-1.0,
            max_val=1.0,
            bits=8,
            shape=(2, 2),
            dtype="float32"
        )
        
        assert tensor.bits == 8
        assert tensor.shape == (2, 2)
        assert tensor.dtype == "float32"

    def test_superbit_tensor_dequantize(self):
        """Test dequantizing SuperBitTensor."""
        data = np.array([0, 128, 255], dtype=np.uint8)
        tensor = SuperBitTensor(
            data=data,
            min_val=0.0,
            max_val=1.0,
            bits=8,
            shape=(3,)
        )
        
        dequantized = tensor.dequantize()
        
        assert dequantized.shape == (3,)
        assert np.all(np.isfinite(dequantized))

    def test_superbit_tensor_serialization(self):
        """Test serializing SuperBitTensor."""
        data = np.array([0, 128, 255], dtype=np.uint8)
        tensor = SuperBitTensor(
            data=data,
            min_val=0.0,
            max_val=1.0,
            bits=8,
            shape=(3,),
            dtype="float32"
        )
        
        serialized = tensor.to_bytes()
        
        assert isinstance(serialized, bytes)
        assert len(serialized) > 0

    def test_superbit_tensor_deserialization(self):
        """Test deserializing SuperBitTensor."""
        data = np.array([0, 128, 255], dtype=np.uint8)
        tensor = SuperBitTensor(
            data=data,
            min_val=0.0,
            max_val=1.0,
            bits=8,
            shape=(3,),
            dtype="float32"
        )
        
        serialized = tensor.to_bytes()
        restored = SuperBitTensor.from_bytes(serialized)
        
        assert restored.bits == 8
        assert restored.shape == (3,)
        assert restored.dtype == "float32"

    def test_superbit_tensor_roundtrip(self):
        """Test roundtrip serialization."""
        original_data = np.array([10, 50, 100, 200], dtype=np.uint8)
        tensor = SuperBitTensor(
            data=original_data,
            min_val=-1.0,
            max_val=1.0,
            bits=8,
            shape=(4,)
        )
        
        # Serialize and deserialize
        serialized = tensor.to_bytes()
        restored = SuperBitTensor.from_bytes(serialized)
        
        # Dequantize both
        orig_dequant = tensor.dequantize()
        restored_dequant = restored.dequantize()
        
        assert np.allclose(orig_dequant, restored_dequant)


class TestQuantizationIntegration:
    """Test quantization integration."""

    def test_full_quantization_pipeline(self):
        """Test complete quantization pipeline."""
        quantizer = SuperBitQuantizer(bits=8)
        original_tensor = np.random.randn(100, 100).astype(np.float32)
        
        # Quantize
        quantized, min_val, max_val = quantizer.quantize(original_tensor)
        
        # Create SuperBitTensor
        sb_tensor = SuperBitTensor(
            data=quantized,
            min_val=min_val,
            max_val=max_val,
            bits=8,
            shape=original_tensor.shape
        )
        
        # Serialize
        serialized = sb_tensor.to_bytes()
        
        # Deserialize
        restored = SuperBitTensor.from_bytes(serialized)
        
        # Dequantize
        recovered = restored.dequantize()
        
        assert recovered.shape == original_tensor.shape
        assert np.allclose(recovered, original_tensor, atol=0.01)
