"""SuperBit encoder for knowledge graph entities and relationships."""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Tuple, Union
import math

logger = logging.getLogger(__name__)


class SuperBitEncoder:
    """SuperBit encoding implementation for knowledge graph entities."""
    
    def __init__(self, dimension: int = 128, seed: int = 42):
        """
        Initialize SuperBit encoder.
        
        Args:
            dimension: Dimension of the embedding vectors
            seed: Random seed for deterministic encoding
        """
        self.dimension = dimension
        self.seed = seed
        
        # Generate random projection vectors for SuperBits
        self._init_projection_vectors()
        
        logger.info(f"Initialized SuperBitEncoder with dimension {dimension}")
    
    def _init_projection_vectors(self):
        """Initialize random projection vectors for SuperBit computation."""
        import random
        random.seed(self.seed)
        
        # Generate random projection vectors (Gaussian distributed)
        self.projection_vectors = []
        for i in range(self.dimension):
            vector = [random.gauss(0, 1) for _ in range(64)]  # 64-dimensional projections
            self.projection_vectors.append(vector)
    
    def encode_entity(self, entity_type: str, properties: Dict[str, Any]) -> List[int]:
        """
        Encode an entity into SuperBit representation.
        
        Args:
            entity_type: Type/category of the entity
            properties: Entity properties
            
        Returns:
            SuperBit embedding as list of 0s and 1s
        """
        # Create text representation for hashing
        text_repr = f"{entity_type}:{str(sorted(properties.items()))}"
        
        # Generate deterministic hash
        hash_value = hashlib.sha256(text_repr.encode('utf-8')).hexdigest()
        
        # Convert hash to binary representation
        binary_repr = bin(int(hash_value, 16))[2:].zfill(256)
        
        # Apply SuperBit projection
        embedding = self._superbit_encode(binary_repr)
        
        return embedding
    
    def encode_relationship(
        self,
        source_type: str,
        target_type: str,
        relationship_type: str,
        properties: Dict[str, Any] = None
    ) -> List[int]:
        """
        Encode a relationship into SuperBit representation.
        
        Args:
            source_type: Type of source entity
            target_type: Type of target entity
            relationship_type: Type of relationship
            properties: Relationship properties
            
        Returns:
            SuperBit embedding as list of 0s and 1s
        """
        # Create text representation for hashing
        text_repr = f"{source_type}->{relationship_type}->{target_type}:{str(sorted((properties or {}).items()))}"
        
        # Generate deterministic hash
        hash_value = hashlib.sha256(text_repr.encode('utf-8')).hexdigest()
        
        # Convert hash to binary representation
        binary_repr = bin(int(hash_value, 16))[2:].zfill(256)
        
        # Apply SuperBit projection
        embedding = self._superbit_encode(binary_repr)
        
        return embedding
    
    def _superbit_encode(self, binary_repr: str) -> List[int]:
        """
        Apply SuperBit projection to binary representation.
        
        Args:
            binary_repr: Binary string representation
            
        Returns:
            SuperBit encoded vector
        """
        embedding = []
        
        # Convert binary string to vector of floats
        binary_vector = [1 if bit == '1' else 0 for bit in binary_repr[:len(self.projection_vectors)]]
        
        # Apply projection vectors to compute SuperBits
        for i, proj_vector in enumerate(self.projection_vectors):
            if i >= len(binary_vector):
                break
                
            # Compute dot product with projection vector
            dot_product = sum(b * p for b, p in zip(binary_vector, proj_vector))
            
            # Convert to SuperBit (1 if positive, 0 if negative)
            bit = 1 if dot_product > 0 else 0
            embedding.append(bit)
        
        return embedding
    
    def encode_text(self, text: str) -> List[int]:
        """
        Encode raw text into SuperBit representation.
        
        Args:
            text: Raw text to encode
            
        Returns:
            SuperBit embedding
        """
        # Generate hash from text
        hash_value = hashlib.sha256(text.encode('utf-8')).hexdigest()
        
        # Convert to binary representation
        binary_repr = bin(int(hash_value, 16))[2:].zfill(256)
        
        # Apply SuperBit projection
        embedding = self._superbit_encode(binary_repr)
        
        return embedding
    
    def cosine_similarity(self, embedding1: List[int], embedding2: List[int]) -> float:
        """
        Compute cosine similarity between two SuperBit embeddings.
        
        Args:
            embedding1: First SuperBit embedding
            embedding2: Second SuperBit embedding
            
        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have the same dimension")
        
        # Convert to -1, 1 representation for cosine similarity
        vec1 = [1 if bit == 1 else -1 for bit in embedding1]
        vec2 = [1 if bit == 1 else -1 for bit in embedding2]
        
        # Compute dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Compute magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Compute cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)
        
        # Normalize to 0-1 range (cosine similarity ranges from -1 to 1)
        normalized_similarity = (similarity + 1) / 2
        
        return normalized_similarity
    
    def hamming_distance(self, embedding1: List[int], embedding2: List[int]) -> int:
        """
        Compute Hamming distance between two SuperBit embeddings.
        
        Args:
            embedding1: First SuperBit embedding
            embedding2: Second SuperBit embedding
            
        Returns:
            Hamming distance (number of differing bits)
        """
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have the same dimension")
        
        return sum(a != b for a, b in zip(embedding1, embedding2))
    
    def jaccard_similarity(self, embedding1: List[int], embedding2: List[int]) -> float:
        """
        Compute Jaccard similarity between two SuperBit embeddings.
        
        Args:
            embedding1: First SuperBit embedding
            embedding2: Second SuperBit embedding
            
        Returns:
            Jaccard similarity score (0.0 to 1.0)
        """
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have the same dimension")
        
        # Convert to sets for Jaccard similarity
        set1 = set(i for i, bit in enumerate(embedding1) if bit == 1)
        set2 = set(i for i, bit in enumerate(embedding2) if bit == 1)
        
        if len(set1) == 0 and len(set2) == 0:
            return 1.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def cluster_embeddings(
        self,
        embeddings: List[List[int]],
        threshold: float = 0.8
    ) -> List[List[int]]:
        """
        Cluster similar embeddings together.
        
        Args:
            embeddings: List of SuperBit embeddings
            threshold: Similarity threshold for clustering
            
        Returns:
            List of clusters, each containing indices of similar embeddings
        """
        clusters = []
        used = set()
        
        for i, embedding in enumerate(embeddings):
            if i in used:
                continue
            
            cluster = [i]
            used.add(i)
            
            for j, other_embedding in enumerate(embeddings[i + 1:], i + 1):
                if j in used:
                    continue
                
                similarity = self.cosine_similarity(embedding, other_embedding)
                if similarity >= threshold:
                    cluster.append(j)
                    used.add(j)
            
            clusters.append(cluster)
        
        return clusters
    
    def find_similar_entities(
        self,
        query_embedding: List[int],
        candidate_embeddings: List[Tuple[Any, List[int]]],
        threshold: float = 0.8,
        limit: int = 100
    ) -> List[Tuple[Any, float]]:
        """
        Find entities with similar embeddings.
        
        Args:
            query_embedding: Query SuperBit embedding
            candidate_embeddings: List of (entity_id, embedding) tuples
            threshold: Similarity threshold
            limit: Maximum number of results
            
        Returns:
            List of (entity_id, similarity_score) tuples
        """
        results = []
        
        for entity_id, embedding in candidate_embeddings:
            similarity = self.cosine_similarity(query_embedding, embedding)
            if similarity >= threshold:
                results.append((entity_id, similarity))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:limit]
    
    def get_embedding_statistics(self, embeddings: List[List[int]]) -> Dict[str, float]:
        """
        Get statistics about a set of embeddings.
        
        Args:
            embeddings: List of SuperBit embeddings
            
        Returns:
            Dictionary with embedding statistics
        """
        if not embeddings:
            return {
                "count": 0,
                "avg_sparsity": 0.0,
                "avg_populated_bits": 0.0,
                "dimension": self.dimension
            }
        
        # Calculate sparsity (percentage of zeros)
        sparsities = []
        populated_bits = []
        
        for embedding in embeddings:
            zeros = sum(1 for bit in embedding if bit == 0)
            ones = sum(1 for bit in embedding if bit == 1)
            
            sparsity = zeros / len(embedding)
            sparsities.append(sparsity)
            populated_bits.append(ones)
        
        return {
            "count": len(embeddings),
            "avg_sparsity": sum(sparsities) / len(sparsities),
            "avg_populated_bits": sum(populated_bits) / len(populated_bits),
            "dimension": len(embeddings[0]) if embeddings else self.dimension
        }
    
    def encode_entity_batch(
        self,
        entities: List[Tuple[str, Dict[str, Any]]]
    ) -> List[List[int]]:
        """
        Encode multiple entities in batch.
        
        Args:
            entities: List of (entity_type, properties) tuples
            
        Returns:
            List of SuperBit embeddings
        """
        embeddings = []
        
        for entity_type, properties in entities:
            embedding = self.encode_entity(entity_type, properties)
            embeddings.append(embedding)
        
        return embeddings
    
    def encode_relationship_batch(
        self,
        relationships: List[Tuple[str, str, str, Dict[str, Any]]]
    ) -> List[List[int]]:
        """
        Encode multiple relationships in batch.
        
        Args:
            relationships: List of (source_type, target_type, relationship_type, properties) tuples
            
        Returns:
            List of SuperBit embeddings
        """
        embeddings = []
        
        for source_type, target_type, relationship_type, properties in relationships:
            embedding = self.encode_relationship(
                source_type, target_type, relationship_type, properties
            )
            embeddings.append(embedding)
        
        return embeddings