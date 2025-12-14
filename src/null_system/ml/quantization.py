"""Super-bit quantization for neural network models."""

from typing import Union, Tuple
import numpy as np


class SuperBitQuantizer:
    """Quantize tensors to 4-8 bit super-bit representation."""

    def __init__(self, bits: int = 8):
        """Initialize quantizer.
        
        Args:
            bits: Number of bits for quantization (4 or 8)
        """
        if bits not in (4, 8):
            raise ValueError("bits must be 4 or 8")
        self.bits = bits
        self.scale = 2 ** bits - 1

    def quantize(
        self, tensor: np.ndarray
    ) -> Tuple[np.ndarray, float, float]:
        """Quantize tensor to super-bit representation.
        
        Args:
            tensor: Input tensor to quantize
            
        Returns:
            Tuple of (quantized_tensor, min_val, max_val)
        """
        min_val = float(np.min(tensor))
        max_val = float(np.max(tensor))
        
        if min_val == max_val:
            return np.zeros_like(tensor, dtype=np.uint8), min_val, max_val
        
        # Normalize to [0, 1]
        normalized = (tensor - min_val) / (max_val - min_val)
        
        # Quantize to [0, scale]
        quantized = np.round(normalized * self.scale).astype(
            np.uint8 if self.bits == 8 else np.uint4
        )
        
        return quantized, min_val, max_val

    def dequantize(
        self, quantized: np.ndarray, min_val: float, max_val: float
    ) -> np.ndarray:
        """Dequantize super-bit tensor back to float.
        
        Args:
            quantized: Quantized tensor
            min_val: Minimum value from quantization
            max_val: Maximum value from quantization
            
        Returns:
            Dequantized tensor
        """
        if min_val == max_val:
            return np.full_like(quantized, min_val, dtype=np.float32)
        
        # Normalize quantized values to [0, 1]
        normalized = quantized.astype(np.float32) / self.scale
        
        # Scale back to original range
        return normalized * (max_val - min_val) + min_val

    def estimate_size(self, shape: Tuple[int, ...]) -> int:
        """Estimate memory footprint after quantization.
        
        Args:
            shape: Shape of tensor
            
        Returns:
            Estimated size in bytes
        """
        total_elements = np.prod(shape)
        bytes_per_element = self.bits / 8
        return int(total_elements * bytes_per_element)


class SuperBitTensor:
    """Super-bit encoded tensor representation."""

    def __init__(
        self,
        data: np.ndarray,
        min_val: float,
        max_val: float,
        bits: int = 8,
        shape: Tuple[int, ...] = None,
        dtype: str = "float32",
    ):
        """Initialize super-bit tensor.
        
        Args:
            data: Quantized tensor data
            min_val: Minimum value
            max_val: Maximum value
            bits: Number of bits used
            shape: Original shape
            dtype: Original dtype
        """
        self.data = data
        self.min_val = min_val
        self.max_val = max_val
        self.bits = bits
        self.shape = shape or data.shape
        self.dtype = dtype

    def dequantize(self) -> np.ndarray:
        """Dequantize to float tensor.
        
        Returns:
            Dequantized tensor
        """
        if self.min_val == self.max_val:
            return np.full(self.shape, self.min_val, dtype=self.dtype)
        
        # Normalize quantized values to [0, 1]
        scale = 2 ** self.bits - 1
        normalized = self.data.astype(np.float32) / scale
        
        # Scale back to original range
        result = normalized * (self.max_val - self.min_val) + self.min_val
        return result.reshape(self.shape)

    def to_bytes(self) -> bytes:
        """Serialize to bytes.
        
        Returns:
            Byte representation
        """
        metadata = (
            f"{self.bits},{self.min_val},{self.max_val},"
            f"{self.dtype},{','.join(map(str, self.shape))}"
        ).encode()
        
        return metadata + b":" + self.data.tobytes()

    @classmethod
    def from_bytes(cls, data: bytes) -> "SuperBitTensor":
        """Deserialize from bytes.
        
        Args:
            data: Byte representation
            
        Returns:
            SuperBitTensor instance
        """
        metadata_bytes, array_bytes = data.split(b":", 1)
        metadata = metadata_bytes.decode().split(",")
        
        bits = int(metadata[0])
        min_val = float(metadata[1])
        max_val = float(metadata[2])
        dtype = metadata[3]
        shape = tuple(int(x) for x in metadata[4:])
        
        array_data = np.frombuffer(array_bytes, dtype=np.uint8)
        array_data = array_data.reshape(shape)
        
        return cls(array_data, min_val, max_val, bits, shape, dtype)
