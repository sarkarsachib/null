"""Super-Bit semantic embeddings for Null-Lang NLP engine.

Provides lightweight word embeddings compatible with Super-Bit encoding.
"""

import math
import hashlib
from typing import List, Dict, Tuple


class EmbeddingModel:
    """Super-Bit compatible embedding model using hashing and cosine similarity."""

    def __init__(self, dimension: int = 128, seed: int = 42):
        """
        Initialize the embedding model.

        Args:
            dimension: Dimension of embedding vectors
            seed: Random seed for reproducibility
        """
        self.dimension = dimension
        self.seed = seed
        self._embedding_cache: Dict[str, List[float]] = {}

    def _hash_to_float(self, text: str, index: int) -> float:
        """Convert text hash to float value in [-1, 1] range."""
        hash_input = f"{text}:{index}:{self.seed}".encode()
        hash_obj = hashlib.sha256(hash_input)
        hash_int = int(hash_obj.hexdigest(), 16)
        # Map to [-1, 1] range
        return 2.0 * ((hash_int % 1000000) / 1000000.0) - 1.0

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a text string.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding
        """
        if text in self._embedding_cache:
            return self._embedding_cache[text]

        embedding = [self._hash_to_float(text, i) for i in range(self.dimension)]
        self._embedding_cache[text] = embedding
        return embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings
        """
        return [self.embed(text) for text in texts]

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score in [-1, 1] range
        """
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have same dimension")

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    def semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score in [0, 1] range (normalized from [-1, 1])
        """
        emb1 = self.embed(text1)
        emb2 = self.embed(text2)
        similarity = self.cosine_similarity(emb1, emb2)
        # Normalize to [0, 1] range
        return (similarity + 1.0) / 2.0

    def find_most_similar(self, query: str, candidates: List[str]) -> Tuple[str, float]:
        """
        Find the most similar candidate to a query.

        Args:
            query: Query text
            candidates: List of candidate texts

        Returns:
            Tuple of (most_similar_text, similarity_score)
        """
        if not candidates:
            return "", 0.0

        query_emb = self.embed(query)
        best_candidate = candidates[0]
        best_score = 0.0

        for candidate in candidates:
            cand_emb = self.embed(candidate)
            score = self.semantic_similarity(query, candidate)
            if score > best_score:
                best_score = score
                best_candidate = candidate

        return best_candidate, best_score

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._embedding_cache.clear()

    def attention_weights(self, query: str, keys: List[str]) -> List[float]:
        """
        Calculate attention weights using embeddings.

        Implements scaled dot-product attention mechanism.

        Args:
            query: Query text
            keys: List of key texts

        Returns:
            List of normalized attention weights
        """
        query_emb = self.embed(query)
        scale = math.sqrt(self.dimension)

        # Calculate scores
        scores = []
        for key in keys:
            key_emb = self.embed(key)
            # Scaled dot product
            score = sum(q * k for q, k in zip(query_emb, key_emb)) / scale
            scores.append(score)

        # Softmax normalization
        max_score = max(scores) if scores else 0
        exp_scores = [math.exp(s - max_score) for s in scores]
        sum_exp = sum(exp_scores)

        if sum_exp == 0:
            return [1.0 / len(keys) for _ in keys] if keys else []

        return [e / sum_exp for e in exp_scores]
