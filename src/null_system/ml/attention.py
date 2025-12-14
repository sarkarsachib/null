"""Probabilistic attention mechanisms."""

from typing import Tuple, Optional
import numpy as np


class MultiHeadAttention:
    """Multi-head self-attention mechanism."""

    def __init__(self, hidden_dim: int, num_heads: int = 8):
        """Initialize attention.
        
        Args:
            hidden_dim: Hidden dimension
            num_heads: Number of attention heads
        """
        if hidden_dim % num_heads != 0:
            raise ValueError("hidden_dim must be divisible by num_heads")
        
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        self.scale = 1 / np.sqrt(self.head_dim)

    def attention(
        self,
        query: np.ndarray,
        key: np.ndarray,
        value: np.ndarray,
        mask: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute attention scores.
        
        Args:
            query: Query matrix (seq_len, hidden_dim)
            key: Key matrix (seq_len, hidden_dim)
            value: Value matrix (seq_len, hidden_dim)
            mask: Optional attention mask
            
        Returns:
            Tuple of (output, attention_weights)
        """
        seq_len = query.shape[0]
        
        # Compute scores
        scores = np.dot(query, key.T) * self.scale
        
        # Apply mask if provided
        if mask is not None:
            scores = scores + (mask * -1e9)
        
        # Softmax
        weights = self._softmax(scores)
        
        # Apply attention
        output = np.dot(weights, value)
        
        return output, weights

    def multi_head_attention(
        self,
        query: np.ndarray,
        key: np.ndarray,
        value: np.ndarray,
        mask: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Multi-head attention.
        
        Args:
            query: Query matrix
            key: Key matrix
            value: Value matrix
            mask: Optional mask
            
        Returns:
            Tuple of (output, weights)
        """
        seq_len = query.shape[0]
        
        # Split into heads
        q_heads = self._split_heads(query)
        k_heads = self._split_heads(key)
        v_heads = self._split_heads(value)
        
        # Attention for each head
        outputs = []
        weights_list = []
        
        for i in range(self.num_heads):
            q = q_heads[:, i * self.head_dim:(i + 1) * self.head_dim]
            k = k_heads[:, i * self.head_dim:(i + 1) * self.head_dim]
            v = v_heads[:, i * self.head_dim:(i + 1) * self.head_dim]
            
            output, weights = self.attention(q, k, v, mask)
            outputs.append(output)
            weights_list.append(weights)
        
        # Concatenate
        final_output = np.concatenate(outputs, axis=1)
        avg_weights = np.mean(weights_list, axis=0)
        
        return final_output, avg_weights

    def _split_heads(self, matrix: np.ndarray) -> np.ndarray:
        """Split into multiple heads."""
        return matrix

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Compute softmax."""
        e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e_x / np.sum(e_x, axis=-1, keepdims=True)


class ProbabilisticAttention:
    """Probabilistic attention with uncertainty."""

    def __init__(self, hidden_dim: int, num_samples: int = 100):
        """Initialize probabilistic attention.
        
        Args:
            hidden_dim: Hidden dimension
            num_samples: Number of Monte Carlo samples
        """
        self.hidden_dim = hidden_dim
        self.num_samples = num_samples

    def forward(
        self,
        query: np.ndarray,
        key: np.ndarray,
        value: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Forward pass with uncertainty estimation.
        
        Args:
            query: Query matrix
            key: Key matrix
            value: Value matrix
            
        Returns:
            Tuple of (mean, variance, samples)
        """
        samples = []
        
        for _ in range(self.num_samples):
            # Add Gaussian noise
            noise_q = query + np.random.randn(*query.shape) * 0.01
            noise_k = key + np.random.randn(*key.shape) * 0.01
            noise_v = value + np.random.randn(*value.shape) * 0.01
            
            # Compute attention with noise
            output, _ = self._attention(noise_q, noise_k, noise_v)
            samples.append(output)
        
        samples = np.array(samples)
        mean = np.mean(samples, axis=0)
        variance = np.var(samples, axis=0)
        
        return mean, variance, samples

    def _attention(
        self,
        query: np.ndarray,
        key: np.ndarray,
        value: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Basic attention computation."""
        scores = np.dot(query, key.T)
        weights = self._softmax(scores)
        output = np.dot(weights, value)
        return output, weights

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax implementation."""
        e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e_x / np.sum(e_x, axis=-1, keepdims=True)


class AttentionVisualizer:
    """Visualize attention weights."""

    @staticmethod
    def format_weights(weights: np.ndarray) -> str:
        """Format attention weights for display.
        
        Args:
            weights: Attention weight matrix
            
        Returns:
            Formatted string representation
        """
        lines = []
        lines.append("[Attention Weights]")
        
        seq_len = weights.shape[0]
        max_w = np.max(weights)
        
        for i in range(seq_len):
            row = weights[i]
            bar = "".join(
                "█" * int((w / max_w) * 10) for w in row
            )
            lines.append(f"  {i}: {bar}")
        
        return "\n".join(lines)
