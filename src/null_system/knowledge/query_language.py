"""Query language and engine for knowledge graph traversal and pattern matching."""

from __future__ import annotations

import re
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID

from .graph_store import GraphStore, Entity, Relationship
from .superbit_encoder import SuperBitEncoder

logger = logging.getLogger(__name__)


class QueryOperator(Enum):
    """Query operators for pattern matching."""
    EQUALS = "=="
    NOT_EQUALS = "!="
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = ">"
    LESS_THAN = "<"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"


class LogicalOperator(Enum):
    """Logical operators for combining conditions."""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


@dataclass
class PropertyCondition:
    """Condition for entity or relationship properties."""
    property_name: str
    operator: QueryOperator
    value: Any


@dataclass
class TypeCondition:
    """Condition for entity types."""
    entity_type: str


@dataclass
class RelationshipCondition:
    """Condition for relationships."""
    relationship_type: Optional[str] = None
    target_type: Optional[str] = None
    min_confidence: Optional[float] = None


@dataclass
class EmbeddingCondition:
    """Condition based on SuperBit embeddings."""
    target_embedding: Optional[List[int]] = None
    similarity_threshold: float = 0.8
    property_name: str = "superbit_embedding"


@dataclass
class Condition:
    """Combined condition using logical operators."""
    conditions: List[Condition] = field(default_factory=list)
    logical_operator: LogicalOperator = LogicalOperator.AND
    property_condition: Optional[PropertyCondition] = None
    type_condition: Optional[TypeCondition] = None
    relationship_condition: Optional[RelationshipCondition] = None
    embedding_condition: Optional[EmbeddingCondition] = None


@dataclass
class Pattern:
    """Pattern for matching entities and relationships."""
    name: str
    entity_type: Optional[str] = None
    properties: List[PropertyCondition] = field(default_factory=list)
    embedding_condition: Optional[EmbeddingCondition] = None


@dataclass
class RelationshipPattern:
    """Pattern for relationship matching."""
    name: str
    relationship_type: Optional[str] = None
    source_pattern: Optional[Pattern] = None
    target_pattern: Optional[Pattern] = None
    min_confidence: Optional[float] = None


@dataclass
class PathPattern:
    """Pattern for path traversal."""
    patterns: List[Union[Pattern, RelationshipPattern]] = field(default_factory=list)
    min_length: int = 1
    max_length: Optional[int] = None


@dataclass
class QueryResult:
    """Result of a query execution."""
    matches: List[Dict[str, Any]]
    total_count: int = 0
    execution_time: float = 0.0
    query_string: str = ""


class QueryExecutor(ABC):
    """Abstract query executor."""
    
    @abstractmethod
    def execute_pattern(self, pattern: Pattern, graph_store: GraphStore) -> List[Entity]:
        pass
    
    @abstractmethod
    def execute_relationship_pattern(
        self,
        pattern: RelationshipPattern,
        graph_store: GraphStore
    ) -> List[Tuple[Entity, Relationship, Entity]]:
        pass
    
    @abstractmethod
    def execute_path_pattern(
        self,
        pattern: PathPattern,
        graph_store: GraphStore
    ) -> List[List[Any]]:
        pass


class BasicQueryExecutor(QueryExecutor):
    """Basic query executor implementation."""
    
    def __init__(self, encoder: Optional[SuperBitEncoder] = None):
        self.encoder = encoder or SuperBitEncoder()
    
    def execute_pattern(self, pattern: Pattern, graph_store: GraphStore) -> List[Entity]:
        """Execute a pattern to find matching entities."""
        # Get all entities (filtered by type if specified)
        if pattern.entity_type:
            entities = graph_store.list_entities(pattern.entity_type)
        else:
            entities = graph_store.list_entities()
        
        # Apply property conditions
        matched_entities = []
        for entity in entities:
            if self._match_entity_pattern(entity, pattern):
                matched_entities.append(entity)
        
        return matched_entities
    
    def execute_relationship_pattern(
        self,
        pattern: RelationshipPattern,
        graph_store: GraphStore
    ) -> List[Tuple[Entity, Relationship, Entity]]:
        """Execute a relationship pattern to find matching relationships."""
        results = []
        
        # Get all entities if source pattern is not specified
        if pattern.source_pattern:
            source_entities = self.execute_pattern(pattern.source_pattern, graph_store)
        else:
            source_entities = graph_store.list_entities()
        
        for source_entity in source_entities:
            # Get relationships from this source
            relationships = graph_store.backend.get_relationships_by_source(source_entity.id)
            
            for relationship in relationships:
                # Check relationship type
                if pattern.relationship_type and relationship.relationship_type != pattern.relationship_type:
                    continue
                
                # Check confidence
                if pattern.min_confidence and relationship.confidence < pattern.min_confidence:
                    continue
                
                # Get target entity
                target_entity = graph_store.backend.get_entity(relationship.target_id)
                if not target_entity:
                    continue
                
                # Check target pattern
                if pattern.target_pattern:
                    if not self._match_entity_pattern(target_entity, pattern.target_pattern):
                        continue
                
                results.append((source_entity, relationship, target_entity))
        
        return results
    
    def execute_path_pattern(
        self,
        pattern: PathPattern,
        graph_store: GraphStore
    ) -> List[List[Any]]:
        """Execute a path pattern using BFS."""
        if not pattern.patterns:
            return []
        
        # Start with initial entities (first pattern)
        initial_entities = self.execute_pattern(pattern.patterns[0], graph_store)
        
        paths = []
        
        for start_entity in initial_entities:
            # BFS traversal
            current_paths = [[start_entity]]
            
            for pattern_index in range(1, len(pattern.patterns)):
                next_pattern = pattern.patterns[pattern_index]
                new_paths = []
                
                for path in current_paths:
                    last_entity = path[-1]
                    
                    if isinstance(next_pattern, RelationshipPattern):
                        # Relationship pattern
                        found_relationships = self._find_relationships_from_entity(
                            last_entity, next_pattern, graph_store
                        )
                        
                        for rel, next_entity in found_relationships:
                            new_path = path + [(rel, next_entity)]
                            new_paths.append(new_path)
                    
                    elif isinstance(next_pattern, Pattern):
                        # Entity pattern
                        matching_entities = self._find_entities_from_entity(
                            last_entity, next_pattern, graph_store
                        )
                        
                        for next_entity in matching_entities:
                            new_path = path + [next_entity]
                            new_paths.append(new_path)
                
                current_paths = new_paths
                
                # Filter by path length constraints
                current_paths = [
                    p for p in current_paths
                    if pattern.min_length <= len(p) <= (pattern.max_length or len(p))
                ]
                
                # If no paths found at this level, break
                if not current_paths:
                    break
            
            paths.extend(current_paths)
        
        return paths
    
    def _match_entity_pattern(self, entity: Entity, pattern: Pattern) -> bool:
        """Check if entity matches a pattern."""
        # Check property conditions
        for prop_condition in pattern.properties:
            entity_value = entity.properties.get(prop_condition.property_name)
            
            if not self._match_condition(entity_value, prop_condition):
                return False
        
        # Check embedding condition
        if pattern.embedding_condition and entity.superbit_embedding:
            similarity = self.encoder.cosine_similarity(
                pattern.embedding_condition.target_embedding,
                entity.superbit_embedding
            )
            
            if similarity < pattern.embedding_condition.similarity_threshold:
                return False
        
        return True
    
    def _match_condition(self, value: Any, condition: PropertyCondition) -> bool:
        """Check if a value matches a condition."""
        if condition.operator == QueryOperator.EQUALS:
            return value == condition.value
        elif condition.operator == QueryOperator.NOT_EQUALS:
            return value != condition.value
        elif condition.operator == QueryOperator.CONTAINS:
            return condition.value in (value or [])
        elif condition.operator == QueryOperator.STARTS_WITH:
            return str(value).startswith(str(condition.value))
        elif condition.operator == QueryOperator.ENDS_WITH:
            return str(value).endswith(str(condition.value))
        elif condition.operator == QueryOperator.GREATER_THAN:
            return value > condition.value
        elif condition.operator == QueryOperator.LESS_THAN:
            return value < condition.value
        elif condition.operator == QueryOperator.IN:
            return value in condition.value
        elif condition.operator == QueryOperator.NOT_IN:
            return value not in condition.value
        elif condition.operator == QueryOperator.REGEX:
            return bool(re.search(str(condition.value), str(value)))
        
        return False
    
    def _find_relationships_from_entity(
        self,
        entity: Entity,
        pattern: RelationshipPattern,
        graph_store: GraphStore
    ) -> List[Tuple[Relationship, Entity]]:
        """Find relationships and entities matching a pattern from a given entity."""
        relationships = graph_store.backend.get_relationships_by_source(entity.id)
        results = []
        
        for relationship in relationships:
            # Check relationship type
            if pattern.relationship_type and relationship.relationship_type != pattern.relationship_type:
                continue
            
            # Check confidence
            if pattern.min_confidence and relationship.confidence < pattern.min_confidence:
                continue
            
            # Get target entity
            target_entity = graph_store.backend.get_entity(relationship.target_id)
            if not target_entity:
                continue
            
            # Check target pattern
            if pattern.target_pattern:
                if not self._match_entity_pattern(target_entity, pattern.target_pattern):
                    continue
            
            results.append((relationship, target_entity))
        
        return results
    
    def _find_entities_from_entity(
        self,
        entity: Entity,
        pattern: Pattern,
        graph_store: GraphStore
    ) -> List[Entity]:
        """Find entities matching a pattern from a given entity."""
        # Get all neighbors
        neighbors = graph_store.get_neighbors(entity.id)
        
        matching_neighbors = []
        for neighbor_entity, relationship in neighbors:
            if self._match_entity_pattern(neighbor_entity, pattern):
                matching_neighbors.append(neighbor_entity)
        
        return matching_neighbors


class QueryEngine:
    """Main query engine for knowledge graphs."""
    
    def __init__(
        self,
        graph_store: GraphStore,
        executor: Optional[QueryExecutor] = None
    ):
        self.graph_store = graph_store
        self.executor = executor or BasicQueryExecutor()
        
        logger.info("Initialized QueryEngine")
    
    def find_entities(
        self,
        entity_type: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[int]] = None,
        similarity_threshold: float = 0.8
    ) -> QueryResult:
        """Find entities matching criteria."""
        import time
        start_time = time.time()
        
        # Build pattern
        pattern_conditions = []
        if properties:
            for prop_name, prop_value in properties.items():
                pattern_conditions.append(PropertyCondition(
                    property_name=prop_name,
                    operator=QueryOperator.EQUALS,
                    value=prop_value
                ))
        
        embedding_condition = None
        if embedding:
            embedding_condition = EmbeddingCondition(
                target_embedding=embedding,
                similarity_threshold=similarity_threshold
            )
        
        pattern = Pattern(
            name="find_entities",
            entity_type=entity_type,
            properties=pattern_conditions,
            embedding_condition=embedding_condition
        )
        
        # Execute query
        entities = self.executor.execute_pattern(pattern, self.graph_store)
        
        # Convert to result format
        matches = []
        for entity in entities:
            matches.append({
                "entity": entity,
                "properties": entity.properties,
                "type": entity.type,
                "id": str(entity.id),
                "created_at": entity.created_at,
                "updated_at": entity.updated_at
            })
        
        execution_time = time.time() - start_time
        
        return QueryResult(
            matches=matches,
            total_count=len(matches),
            execution_time=execution_time,
            query_string="find_entities"
        )
    
    def find_relationships(
        self,
        source_type: Optional[str] = None,
        target_type: Optional[str] = None,
        relationship_type: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> QueryResult:
        """Find relationships matching criteria."""
        import time
        start_time = time.time()
        
        # Build pattern
        source_pattern = None
        if source_type:
            source_pattern = Pattern(
                name="source",
                entity_type=source_type
            )
        
        target_pattern = None
        if target_type:
            target_pattern = Pattern(
                name="target",
                entity_type=target_type
            )
        
        relationship_pattern = RelationshipPattern(
            name="find_relationships",
            relationship_type=relationship_type,
            source_pattern=source_pattern,
            target_pattern=target_pattern,
            min_confidence=min_confidence
        )
        
        # Execute query
        relationships = self.executor.execute_relationship_pattern(
            relationship_pattern, self.graph_store
        )
        
        # Convert to result format
        matches = []
        for source_entity, relationship, target_entity in relationships:
            matches.append({
                "source": source_entity,
                "relationship": relationship,
                "target": target_entity,
                "source_id": str(source_entity.id),
                "target_id": str(target_entity.id),
                "relationship_type": relationship.relationship_type,
                "confidence": relationship.confidence,
                "properties": relationship.properties,
                "id": str(relationship.id)
            })
        
        execution_time = time.time() - start_time
        
        return QueryResult(
            matches=matches,
            total_count=len(matches),
            execution_time=execution_time,
            query_string="find_relationships"
        )
    
    def find_paths(
        self,
        start_type: Optional[str] = None,
        end_type: Optional[str] = None,
        relationship_types: Optional[List[str]] = None,
        max_length: int = 5
    ) -> QueryResult:
        """Find paths between entities."""
        import time
        start_time = time.time()
        
        # Build path pattern
        patterns = []
        
        if start_type:
            patterns.append(Pattern(
                name="start",
                entity_type=start_type
            ))
        else:
            # If no start type specified, we need at least one pattern
            patterns.append(Pattern(
                name="any_start",
                entity_type=None
            ))
        
        for i, rel_type in enumerate(relationship_types or []):
            patterns.append(RelationshipPattern(
                name=f"rel_{i}",
                relationship_type=rel_type,
                min_confidence=0.0  # Accept all relationships
            ))
            
            # Add target pattern
            if i == len(relationship_types) - 1 and end_type:
                # Last relationship, add end pattern
                patterns.append(Pattern(
                    name="end",
                    entity_type=end_type
                ))
            else:
                # Intermediate entity pattern
                patterns.append(Pattern(
                    name=f"intermediate_{i}",
                    entity_type=None
                ))
        
        path_pattern = PathPattern(
            patterns=patterns,
            min_length=1,
            max_length=max_length
        )
        
        # Execute query
        paths = self.executor.execute_path_pattern(path_pattern, self.graph_store)
        
        # Convert to result format
        matches = []
        for path in paths:
            path_data = {
                "path": path,
                "length": len(path),
                "entities": [item for item in path if isinstance(item, Entity)],
                "relationships": [item for item in path if isinstance(item, Relationship)]
            }
            matches.append(path_data)
        
        execution_time = time.time() - start_time
        
        return QueryResult(
            matches=matches,
            total_count=len(matches),
            execution_time=execution_time,
            query_string="find_paths"
        )
    
    def aggregate(
        self,
        entity_type: Optional[str] = None,
        group_by: Optional[str] = None,
        aggregate_property: Optional[str] = None,
        aggregation_function: str = "count"
    ) -> QueryResult:
        """Aggregate query results."""
        import time
        start_time = time.time()
        
        # Get entities
        if entity_type:
            entities = self.graph_store.list_entities(entity_type)
        else:
            entities = self.graph_store.list_entities()
        
        # Group entities
        groups = {}
        for entity in entities:
            if group_by:
                key = entity.properties.get(group_by, entity.type)
            else:
                key = entity.type
            
            if key not in groups:
                groups[key] = []
            groups[key].append(entity)
        
        # Calculate aggregates
        results = []
        for group_key, group_entities in groups.items():
            if aggregation_function == "count":
                value = len(group_entities)
            elif aggregation_function == "sum" and aggregate_property:
                value = sum(
                    entity.properties.get(aggregate_property, 0) 
                    for entity in group_entities
                )
            elif aggregation_function == "avg" and aggregate_property:
                values = [
                    entity.properties.get(aggregate_property, 0) 
                    for entity in group_entities
                ]
                value = sum(values) / len(values) if values else 0
            elif aggregation_function == "max" and aggregate_property:
                values = [
                    entity.properties.get(aggregate_property, 0) 
                    for entity in group_entities
                ]
                value = max(values) if values else 0
            elif aggregation_function == "min" and aggregate_property:
                values = [
                    entity.properties.get(aggregate_property, 0) 
                    for entity in group_entities
                ]
                value = min(values) if values else 0
            else:
                value = len(group_entities)  # Default to count
            
            results.append({
                "group": group_key,
                "value": value,
                "count": len(group_entities)
            })
        
        execution_time = time.time() - start_time
        
        return QueryResult(
            matches=results,
            total_count=len(results),
            execution_time=execution_time,
            query_string="aggregate"
        )
    
    def custom_query(self, query_dsl: str) -> QueryResult:
        """Execute a custom query using DSL string."""
        import time
        start_time = time.time()
        
        # Parse DSL and execute
        # For now, this is a placeholder - full DSL parsing would be more complex
        
        # Simple parsing for demonstration
        if query_dsl.startswith("FIND ENTITIES"):
            # Extract entity type from DSL
            match = re.search(r"OF TYPE (\w+)", query_dsl)
            entity_type = match.group(1) if match else None
            
            return self.find_entities(entity_type=entity_type)
        
        elif query_dsl.startswith("FIND RELATIONSHIPS"):
            # Extract relationship type from DSL
            match = re.search(r"OF TYPE (\w+)", query_dsl)
            relationship_type = match.group(1) if match else None
            
            return self.find_relationships(relationship_type=relationship_type)
        
        else:
            raise ValueError(f"Unsupported query DSL: {query_dsl}")
    
    def explain_query(self, query_result: QueryResult) -> Dict[str, Any]:
        """Provide explanation of query execution."""
        return {
            "execution_time": query_result.execution_time,
            "total_matches": query_result.total_count,
            "query_string": query_result.query_string,
            "avg_time_per_match": (
                query_result.execution_time / query_result.total_count 
                if query_result.total_count > 0 else 0
            ),
            "performance": "fast" if query_result.execution_time < 1.0 else "moderate"
        }