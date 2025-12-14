"""Entity resolution module for knowledge graph entity linking."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4

from .graph_store import Entity
from .superbit_encoder import SuperBitEncoder

logger = logging.getLogger(__name__)


@dataclass
class EntityMatch:
    """Represents a match between entities."""
    entity1_id: UUID
    entity2_id: UUID
    confidence: float
    match_type: str  # EXACT, FUZZY, SEMANTIC, CROSS_LINGUAL
    features: Dict[str, float] = field(default_factory=dict)
    reasoning: str = ""


@dataclass
class EntityCluster:
    """Represents a cluster of resolved entities."""
    cluster_id: UUID
    canonical_entity_id: UUID
    member_ids: Set[UUID] = field(default_factory=set)
    confidence_scores: Dict[UUID, float] = field(default_factory=dict)
    merge_rules: List[str] = field(default_factory=list)


class SimilarityCalculator(ABC):
    """Abstract base for similarity calculation strategies."""
    
    @abstractmethod
    def calculate_similarity(
        self,
        entity1: Entity,
        entity2: Entity,
        encoder: Optional[SuperBitEncoder] = None
    ) -> float:
        pass


class PropertyBasedSimilarity(SimilarityCalculator):
    """Calculate similarity based on entity properties."""
    
    def __init__(self, property_weights: Optional[Dict[str, float]] = None):
        self.property_weights = property_weights or {
            "name": 1.0,
            "label": 1.0,
            "title": 1.0,
            "description": 0.8,
            "type": 0.9
        }
    
    def calculate_similarity(
        self,
        entity1: Entity,
        entity2: Entity,
        encoder: Optional[SuperBitEncoder] = None
    ) -> float:
        """Calculate similarity based on overlapping properties."""
        similarities = []
        
        # Type similarity
        type_sim = 1.0 if entity1.type == entity2.type else 0.0
        similarities.append(type_sim)
        
        # Property-based similarities
        for prop_name, weight in self.property_weights.items():
            if prop_name == "type":
                continue  # Already handled above
            
            val1 = entity1.properties.get(prop_name)
            val2 = entity2.properties.get(prop_name)
            
            if val1 is not None and val2 is not None:
                prop_sim = self._calculate_property_similarity(val1, val2, prop_name)
                weighted_sim = prop_sim * weight
                similarities.append(weighted_sim)
        
        # Calculate weighted average
        if similarities:
            return sum(similarities) / len(similarities)
        return 0.0
    
    def _calculate_property_similarity(self, val1: Any, val2: Any, prop_name: str) -> float:
        """Calculate similarity for a specific property."""
        if val1 == val2:
            return 1.0
        
        # Handle string properties
        if isinstance(val1, str) and isinstance(val2, str):
            return self._string_similarity(val1.lower(), val2.lower())
        
        # Handle numeric properties
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            if val1 == 0 and val2 == 0:
                return 1.0
            max_val = max(abs(val1), abs(val2))
            if max_val == 0:
                return 1.0
            similarity = 1.0 - abs(val1 - val2) / max_val
            return max(0.0, similarity)
        
        # Handle list properties
        if isinstance(val1, list) and isinstance(val2, list):
            set1, set2 = set(val1), set(val2)
            if not set1 and not set2:
                return 1.0
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            return intersection / union if union > 0 else 0.0
        
        return 0.0
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using various metrics."""
        import difflib
        
        # Exact match
        if str1 == str2:
            return 1.0
        
        # Substring similarity
        if str1 in str2 or str2 in str1:
            return 0.8
        
        # Sequence matcher similarity
        return difflib.SequenceMatcher(None, str1, str2).ratio()


class EmbeddingBasedSimilarity(SimilarityCalculator):
    """Calculate similarity based on SuperBit embeddings."""
    
    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold
    
    def calculate_similarity(
        self,
        entity1: Entity,
        entity2: Entity,
        encoder: Optional[SuperBitEncoder] = None
    ) -> float:
        """Calculate similarity based on embeddings."""
        if not encoder:
            raise ValueError("SuperBitEncoder required for embedding-based similarity")
        
        if not entity1.superbit_embedding or not entity2.superbit_embedding:
            return 0.0
        
        similarity = encoder.cosine_similarity(
            entity1.superbit_embedding,
            entity2.superbit_embedding
        )
        
        # Boost similarity if above threshold
        if similarity >= self.threshold:
            return similarity
        else:
            return similarity * 0.5  # Reduced weight for low similarity


class HybridSimilarity(SimilarityCalculator):
    """Hybrid similarity combining multiple approaches."""
    
    def __init__(
        self,
        property_calculator: Optional[PropertyBasedSimilarity] = None,
        embedding_calculator: Optional[EmbeddingBasedSimilarity] = None,
        weights: Optional[Dict[str, float]] = None
    ):
        self.property_calculator = property_calculator or PropertyBasedSimilarity()
        self.embedding_calculator = embedding_calculator or EmbeddingBasedSimilarity()
        self.weights = weights or {
            "property": 0.6,
            "embedding": 0.4
        }
    
    def calculate_similarity(
        self,
        entity1: Entity,
        entity2: Entity,
        encoder: Optional[SuperBitEncoder] = None
    ) -> float:
        """Calculate hybrid similarity."""
        similarities = []
        total_weight = 0.0
        
        # Property-based similarity
        if "property" in self.weights:
            prop_sim = self.property_calculator.calculate_similarity(entity1, entity2, encoder)
            similarities.append(prop_sim * self.weights["property"])
            total_weight += self.weights["property"]
        
        # Embedding-based similarity
        if "embedding" in self.weights:
            try:
                emb_sim = self.embedding_calculator.calculate_similarity(entity1, entity2, encoder)
                similarities.append(emb_sim * self.weights["embedding"])
                total_weight += self.weights["embedding"]
            except ValueError:
                # Embedding calculation failed, skip it
                pass
        
        if total_weight == 0:
            return 0.0
        
        return sum(similarities) / total_weight


class EntityResolver:
    """Main entity resolution engine."""
    
    def __init__(
        self,
        graph_store,
        similarity_calculator: Optional[SimilarityCalculator] = None,
        encoder: Optional[SuperBitEncoder] = None,
        min_confidence: float = 0.7
    ):
        self.graph_store = graph_store
        self.similarity_calculator = similarity_calculator or HybridSimilarity()
        self.encoder = encoder or SuperBitEncoder()
        self.min_confidence = min_confidence
        self.matches: List[EntityMatch] = []
        self.clusters: Dict[UUID, EntityCluster] = {}
        
        logger.info(f"Initialized EntityResolver with min_confidence={min_confidence}")
    
    def find_potential_matches(
        self,
        entity: Entity,
        candidate_entities: Optional[List[Entity]] = None,
        entity_type_filter: Optional[str] = None,
        max_candidates: int = 1000
    ) -> List[EntityMatch]:
        """Find potential matches for an entity."""
        # Get candidate entities
        if candidate_entities is None:
            candidate_entities = self.graph_store.list_entities()
        
        # Filter candidates
        if entity_type_filter:
            candidate_entities = [
                e for e in candidate_entities
                if e.id != entity.id and e.type == entity_type_filter
            ]
        else:
            candidate_entities = [
                e for e in candidate_entities
                if e.id != entity.id
            ]
        
        # Limit candidates for performance
        candidate_entities = candidate_entities[:max_candidates]
        
        potential_matches = []
        
        for candidate in candidate_entities:
            confidence = self.similarity_calculator.calculate_similarity(
                entity, candidate, self.encoder
            )
            
            if confidence >= self.min_confidence:
                match_type = self._determine_match_type(entity, candidate, confidence)
                
                match = EntityMatch(
                    entity1_id=entity.id,
                    entity2_id=candidate.id,
                    confidence=confidence,
                    match_type=match_type,
                    features=self._calculate_match_features(entity, candidate)
                )
                
                potential_matches.append(match)
        
        # Sort by confidence
        potential_matches.sort(key=lambda x: x.confidence, reverse=True)
        
        logger.debug(f"Found {len(potential_matches)} potential matches for entity {entity.id}")
        return potential_matches
    
    def resolve_entities(
        self,
        entities: List[Entity],
        auto_cluster: bool = True
    ) -> List[EntityMatch]:
        """Resolve entities in a batch."""
        logger.info(f"Resolving {len(entities)} entities")
        
        all_matches = []
        
        # Find matches for each entity
        for i, entity in enumerate(entities):
            logger.debug(f"Processing entity {i+1}/{len(entities)}: {entity.id}")
            
            potential_matches = self.find_potential_matches(
                entity,
                candidate_entities=entities,
                entity_type_filter=entity.type
            )
            
            all_matches.extend(potential_matches)
        
        # Remove duplicate matches
        unique_matches = self._deduplicate_matches(all_matches)
        self.matches = unique_matches
        
        # Auto-cluster if requested
        if auto_cluster:
            self._cluster_entities(unique_matches)
        
        logger.info(f"Resolved entities: found {len(unique_matches)} matches, {len(self.clusters)} clusters")
        return unique_matches
    
    def _determine_match_type(self, entity1: Entity, entity2: Entity, confidence: float) -> str:
        """Determine the type of match between entities."""
        # Exact match - identical properties and type
        if self._is_exact_match(entity1, entity2):
            return "EXACT"
        
        # High confidence semantic match
        if confidence >= 0.9:
            return "SEMANTIC"
        
        # Medium confidence fuzzy match
        elif confidence >= 0.8:
            return "FUZZY"
        
        # Cross-lingual or weak semantic match
        elif confidence >= self.min_confidence:
            return "CROSS_LINGUAL"
        
        return "WEAK"
    
    def _is_exact_match(self, entity1: Entity, entity2: Entity) -> bool:
        """Check if entities are an exact match."""
        if entity1.type != entity2.type:
            return False
        
        # Check all properties
        all_props = set(entity1.properties.keys()) | set(entity2.properties.keys())
        
        for prop in all_props:
            val1 = entity1.properties.get(prop)
            val2 = entity2.properties.get(prop)
            
            if val1 != val2:
                return False
        
        return True
    
    def _calculate_match_features(self, entity1: Entity, entity2: Entity) -> Dict[str, float]:
        """Calculate detailed features for a match."""
        features = {}
        
        # Property overlap
        props1 = set(entity1.properties.keys())
        props2 = set(entity2.properties.keys())
        
        if props1 or props2:
            features["property_overlap"] = len(props1 & props2) / len(props1 | props2)
        else:
            features["property_overlap"] = 1.0
        
        # Type match
        features["type_match"] = 1.0 if entity1.type == entity2.type else 0.0
        
        # Name similarity
        name1 = entity1.properties.get("name") or entity1.properties.get("label")
        name2 = entity2.properties.get("name") or entity2.properties.get("label")
        
        if name1 and name2:
            features["name_similarity"] = self._string_similarity(str(name1), str(name2))
        else:
            features["name_similarity"] = 0.0
        
        # Embedding similarity
        if entity1.superbit_embedding and entity2.superbit_embedding:
            features["embedding_similarity"] = self.encoder.cosine_similarity(
                entity1.superbit_embedding,
                entity2.superbit_embedding
            )
        else:
            features["embedding_similarity"] = 0.0
        
        return features
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity."""
        import difflib
        return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def _deduplicate_matches(self, matches: List[EntityMatch]) -> List[EntityMatch]:
        """Remove duplicate matches."""
        seen_pairs = set()
        unique_matches = []
        
        for match in matches:
            # Create canonical pair (smaller ID first)
            pair = tuple(sorted([match.entity1_id, match.entity2_id]))
            
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                unique_matches.append(match)
        
        return unique_matches
    
    def _cluster_entities(self, matches: List[EntityMatch]) -> None:
        """Cluster entities based on matches."""
        # Build graph of entity connections
        graph = {}
        for match in matches:
            entity1, entity2 = match.entity1_id, match.entity2_id
            
            if entity1 not in graph:
                graph[entity1] = []
            if entity2 not in graph:
                graph[entity2] = []
            
            graph[entity1].append(entity2)
            graph[entity2].append(entity1)
        
        # Find connected components (clusters)
        visited = set()
        self.clusters = {}
        
        for entity_id in graph:
            if entity_id not in visited:
                cluster = self._find_connected_component(entity_id, graph, visited)
                
                if len(cluster) > 1:  # Only create clusters with multiple entities
                    self._create_cluster(cluster, matches)
    
    def _find_connected_component(self, start_entity: UUID, graph: Dict[UUID, List[UUID]], visited: Set[UUID]) -> Set[UUID]:
        """Find connected component using DFS."""
        component = set()
        stack = [start_entity]
        
        while stack:
            entity_id = stack.pop()
            
            if entity_id in visited:
                continue
            
            visited.add(entity_id)
            component.add(entity_id)
            
            # Add neighbors to stack
            for neighbor in graph.get(entity_id, []):
                if neighbor not in visited:
                    stack.append(neighbor)
        
        return component
    
    def _create_cluster(self, entity_ids: Set[UUID], matches: List[EntityMatch]) -> None:
        """Create a cluster from connected entities."""
        cluster_id = uuid4()
        
        # Find canonical entity (highest confidence with others)
        canonical_entity = self._find_canonical_entity(entity_ids, matches)
        
        # Calculate confidence scores
        confidence_scores = {}
        for entity_id in entity_ids:
            if entity_id == canonical_entity:
                confidence_scores[entity_id] = 1.0
            else:
                # Find best match confidence
                best_confidence = 0.0
                for match in matches:
                    if (match.entity1_id == canonical_entity and match.entity2_id == entity_id) or \
                       (match.entity2_id == canonical_entity and match.entity1_id == entity_id):
                        best_confidence = max(best_confidence, match.confidence)
                
                confidence_scores[entity_id] = best_confidence
        
        cluster = EntityCluster(
            cluster_id=cluster_id,
            canonical_entity_id=canonical_entity,
            member_ids=entity_ids,
            confidence_scores=confidence_scores
        )
        
        self.clusters[cluster_id] = cluster
        logger.debug(f"Created cluster {cluster_id} with {len(entity_ids)} entities")
    
    def _find_canonical_entity(self, entity_ids: Set[UUID], matches: List[EntityMatch]) -> UUID:
        """Find the canonical entity for a cluster."""
        best_entity = None
        best_score = -1
        
        for entity_id in entity_ids:
            # Calculate total confidence with all other entities in cluster
            total_confidence = 0.0
            count = 0
            
            for match in matches:
                if (match.entity1_id == entity_id and match.entity2_id in entity_ids) or \
                   (match.entity2_id == entity_id and match.entity1_id in entity_ids):
                    if match.entity1_id != match.entity2_id:
                        total_confidence += match.confidence
                        count += 1
            
            if count > 0:
                avg_confidence = total_confidence / count
                if avg_confidence > best_score:
                    best_score = avg_confidence
                    best_entity = entity_id
        
        return best_entity or next(iter(entity_ids))
    
    def merge_cluster(self, cluster_id: UUID, merge_strategy: str = "preserve_canonical") -> Optional[Entity]:
        """Merge entities in a cluster into a single entity."""
        if cluster_id not in self.clusters:
            raise ValueError(f"Cluster {cluster_id} not found")
        
        cluster = self.clusters[cluster_id]
        canonical_entity = self.graph_store.get_entity(cluster.canonical_entity_id)
        
        if not canonical_entity:
            raise ValueError(f"Canonical entity {cluster.canonical_entity_id} not found")
        
        # Merge properties from all cluster members
        merged_properties = canonical_entity.properties.copy()
        merged_embedding = canonical_entity.superbit_embedding.copy() if canonical_entity.superbit_embedding else None
        
        for member_id, confidence in cluster.confidence_scores.items():
            if member_id == cluster.canonical_entity_id:
                continue
            
            member_entity = self.graph_store.get_entity(member_id)
            if not member_entity:
                continue
            
            # Merge properties (prefer canonical entity properties)
            for prop_name, prop_value in member_entity.properties.items():
                if prop_name not in merged_properties and confidence >= 0.5:
                    merged_properties[prop_name] = prop_value
            
            # Update embedding if this member has better confidence
            if (member_entity.superbit_embedding and 
                merged_embedding and 
                confidence > 0.8):
                # Weighted average of embeddings
                merged_embedding = [
                    (merged_embedding[i] * (1 - confidence) + member_entity.superbit_embedding[i] * confidence)
                    for i in range(len(merged_embedding))
                ]
        
        # Update canonical entity with merged properties
        canonical_entity.properties = merged_properties
        canonical_entity.superbit_embedding = merged_embedding
        canonical_entity.updated_at = __import__('time').time()
        
        # Store updated entity
        self.graph_store.backend.store_entity(canonical_entity)
        
        # Delete other entities in cluster
        for member_id in cluster.member_ids:
            if member_id != cluster.canonical_entity_id:
                self.graph_store.delete_entity(member_id, cascade=True)
        
        logger.info(f"Merged cluster {cluster_id} into entity {canonical_entity.id}")
        return canonical_entity
    
    def get_cluster_info(self, cluster_id: UUID) -> Optional[Dict[str, Any]]:
        """Get information about a cluster."""
        if cluster_id not in self.clusters:
            return None
        
        cluster = self.clusters[cluster_id]
        canonical_entity = self.graph_store.get_entity(cluster.canonical_entity_id)
        
        return {
            "cluster_id": str(cluster_id),
            "canonical_entity": {
                "id": str(cluster.canonical_entity_id),
                "type": canonical_entity.type if canonical_entity else "unknown",
                "properties": canonical_entity.properties if canonical_entity else {}
            },
            "member_count": len(cluster.member_ids),
            "confidence_scores": {str(k): v for k, v in cluster.confidence_scores.items()},
            "merge_rules": cluster.merge_rules
        }
    
    def export_resolution_results(self) -> Dict[str, Any]:
        """Export resolution results."""
        return {
            "matches": [
                {
                    "entity1_id": str(match.entity1_id),
                    "entity2_id": str(match.entity2_id),
                    "confidence": match.confidence,
                    "match_type": match.match_type,
                    "features": match.features,
                    "reasoning": match.reasoning
                }
                for match in self.matches
            ],
            "clusters": {
                str(cluster_id): {
                    "cluster_id": str(cluster_id),
                    "canonical_entity_id": str(cluster.canonical_entity_id),
                    "member_ids": [str(mid) for mid in cluster.member_ids],
                    "confidence_scores": {str(k): v for k, v in cluster.confidence_scores.items()},
                    "merge_rules": cluster.merge_rules
                }
                for cluster_id, cluster in self.clusters.items()
            }
        }
    
    def get_resolution_statistics(self) -> Dict[str, Any]:
        """Get statistics about entity resolution."""
        match_types = {}
        for match in self.matches:
            match_types[match.match_type] = match_types.get(match.match_type, 0) + 1
        
        confidence_scores = [match.confidence for match in self.matches]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            "total_entities": len(self.graph_store.list_entities()),
            "total_matches": len(self.matches),
            "total_clusters": len(self.clusters),
            "match_types": match_types,
            "average_confidence": avg_confidence,
            "min_confidence_threshold": self.min_confidence,
            "clusters_with_multiple_members": sum(
                1 for cluster in self.clusters.values() 
                if len(cluster.member_ids) > 1
            )
        }