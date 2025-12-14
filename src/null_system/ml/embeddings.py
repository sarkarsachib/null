"""Semantic embeddings for ML models."""

from typing import List, Tuple, Union
import numpy as np


class SemanticEmbedder:
    """Generate semantic embeddings for text and model outputs."""

    def __init__(self, embedding_dim: int = 768):
        """Initialize embedder.
        
        Args:
            embedding_dim: Dimension of embeddings
        """
        self.embedding_dim = embedding_dim
        self._vocab = {}
        self._embeddings = {}

    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        # Deterministic embedding based on text hash
        hash_val = hash(text)
        np.random.seed(abs(hash_val) % (2**31))
        embedding = np.random.randn(self.embedding_dim).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)
        return embedding

    def embed_sequence(self, tokens: List[str]) -> np.ndarray:
        """Embed a sequence of tokens.
        
        Args:
            tokens: List of tokens
            
        Returns:
            Sequence embedding matrix
        """
        embeddings = [self.embed(token) for token in tokens]
        return np.stack(embeddings, axis=0)

    def similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute cosine similarity between embeddings.
        
        Args:
            emb1: First embedding
            emb2: Second embedding
            
        Returns:
            Similarity score in [0, 1]
        """
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        cos_sim = np.dot(emb1, emb2) / (norm1 * norm2)
        return float((cos_sim + 1) / 2)  # Scale to [0, 1]

    def embed_matrix(self, matrix: np.ndarray) -> np.ndarray:
        """Embed a matrix of values.
        
        Args:
            matrix: Input matrix
            
        Returns:
            Embedding vector
        """
        # Flatten and use deterministic hash
        flat = matrix.flatten()
        hash_val = hash(tuple(flat[:100]))  # Hash first 100 elements
        np.random.seed(abs(hash_val) % (2**31))
        embedding = np.random.randn(self.embedding_dim).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)
        return embedding


class PoolingStrategy:
    """Strategies for pooling embeddings."""

    @staticmethod
    def mean_pooling(embeddings: np.ndarray, mask: np.ndarray = None) -> np.ndarray:
        """Mean pooling over embeddings.
        
        Args:
            embeddings: Embedding matrix
            mask: Optional mask for valid positions
            
        Returns:
            Pooled embedding
        """
        if mask is None:
            return np.mean(embeddings, axis=0)
        
        masked = embeddings * mask[:, np.newaxis]
        sum_embeddings = np.sum(masked, axis=0)
        sum_mask = np.sum(mask)
        
        if sum_mask == 0:
            return np.zeros_like(embeddings[0])
        
        return sum_embeddings / sum_mask

    @staticmethod
    def max_pooling(embeddings: np.ndarray) -> np.ndarray:
        """Max pooling over embeddings.
        
        Args:
            embeddings: Embedding matrix
            
        Returns:
            Pooled embedding
        """
        return np.max(embeddings, axis=0)

    @staticmethod
    def cls_pooling(embeddings: np.ndarray) -> np.ndarray:
        """CLS token pooling (first token).
        
        Args:
            embeddings: Embedding matrix
            
        Returns:
            CLS embedding
        """
        return embeddings[0]


class EmbeddingCache:
    """Cache for computed embeddings."""

    def __init__(self, max_size: int = 10000):
        """Initialize cache.
        
        Args:
            max_size: Maximum cache size
        """
        self.max_size = max_size
        self._cache = {}
        self._order = []

    def get(self, key: str) -> Union[np.ndarray, None]:
        """Get embedding from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Embedding or None if not found
        """
        return self._cache.get(key)

    def put(self, key: str, embedding: np.ndarray) -> None:
        """Put embedding in cache.
        
        Args:
            key: Cache key
            embedding: Embedding vector
        """
        if len(self._cache) >= self.max_size:
            oldest = self._order.pop(0)
            del self._cache[oldest]
        
        self._cache[key] = embedding
        self._order.append(key)

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self._order.clear()

    def size(self) -> int:
        """Get current cache size.
        
        Returns:
            Number of cached items
        """
        return len(self._cache)
