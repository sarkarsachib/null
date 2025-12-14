"""Knowledge graph operations for Null-Lang runtime."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..errors import NullRuntimeError
from ..runtime import NullCallContext
from ..types import NullValue
from ..knowledge import (
    GraphStore, InMemoryBackend, SuperBitEncoder, 
    QueryEngine, InferenceEngine, EntityResolver
)
from ..knowledge.external.wikidata import ExternalKnowledgeBase

logger = logging.getLogger(__name__)

# Global graph store instance for KG operations
_graph_store: Optional[GraphStore] = None
_query_engine: Optional[QueryEngine] = None
_inference_engine: Optional[InferenceEngine] = None
_entity_resolver: Optional[EntityResolver] = None
_external_kb: Optional[ExternalKnowledgeBase] = None


def _ensure_graph_store() -> GraphStore:
    """Ensure global graph store is initialized."""
    global _graph_store, _query_engine, _inference_engine, _entity_resolver, _external_kb
    
    if _graph_store is None:
        # Initialize components
        backend = InMemoryBackend()
        encoder = SuperBitEncoder()
        
        _graph_store = GraphStore(backend, encoder)
        _query_engine = QueryEngine(_graph_store)
        _inference_engine = InferenceEngine(_graph_store)
        _entity_resolver = EntityResolver(_graph_store)
        _external_kb = ExternalKnowledgeBase()
        
        logger.info("Initialized global knowledge graph components")
    
    return _graph_store


def _convert_null_value(value: NullValue) -> Any:
    """Convert NullValue to Python value."""
    if isinstance(value, dict):
        return {k: _convert_null_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_convert_null_value(item) for item in value]
    else:
        return value


def _convert_to_null_value(value: Any) -> NullValue:
    """Convert Python value to NullValue."""
    if isinstance(value, dict):
        return {k: _convert_to_null_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_convert_to_null_value(item) for item in value]
    elif value is None:
        return NullValue()
    else:
        return value


def UPSERT(ctx: NullCallContext, entity_type: NullValue, properties: NullValue, entity_id: NullValue = None) -> NullValue:
    """Upsert an entity in the knowledge graph.
    
    Args:
        entity_type: Type of the entity (string)
        properties: Dictionary of entity properties
        entity_id: Optional UUID for the entity
        
    Returns:
        Dictionary with entity information
    """
    try:
        graph_store = _ensure_graph_store()
        
        # Convert inputs
        entity_type_str = _convert_null_value(entity_type)
        properties_dict = _convert_null_value(properties)
        entity_id_str = _convert_null_value(entity_id) if entity_id else None
        
        # Convert UUID string to UUID if provided
        entity_uuid = UUID(entity_id_str) if entity_id_str else None
        
        # Upsert entity
        entity = graph_store.upsert_entity(
            entity_type=entity_type_str,
            properties=properties_dict,
            entity_id=entity_uuid
        )
        
        # Return entity information
        return _convert_to_null_value({
            "id": str(entity.id),
            "type": entity.type,
            "properties": entity.properties,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at
        })
        
    except Exception as e:
        logger.error(f"Failed to upsert entity: {e}")
        raise NullRuntimeError(f"Failed to upsert entity: {e}")


def QUERY(ctx: NullCallContext, query_type: NullValue, query_params: NullValue) -> NullValue:
    """Query the knowledge graph.
    
    Args:
        query_type: Type of query ("find_entities", "find_relationships", "find_paths", "aggregate")
        query_params: Dictionary of query parameters
        
    Returns:
        Query results
    """
    try:
        graph_store = _ensure_graph_store()
        query_engine = _query_engine
        
        if query_engine is None:
            raise NullRuntimeError("Query engine not initialized")
        
        # Convert inputs
        query_type_str = _convert_null_value(query_type)
        params_dict = _convert_null_value(query_params)
        
        # Execute appropriate query
        if query_type_str == "find_entities":
            result = query_engine.find_entities(
                entity_type=params_dict.get("entity_type"),
                properties=params_dict.get("properties"),
                embedding=params_dict.get("embedding"),
                similarity_threshold=params_dict.get("similarity_threshold", 0.8)
            )
        
        elif query_type_str == "find_relationships":
            result = query_engine.find_relationships(
                source_type=params_dict.get("source_type"),
                target_type=params_dict.get("target_type"),
                relationship_type=params_dict.get("relationship_type"),
                min_confidence=params_dict.get("min_confidence")
            )
        
        elif query_type_str == "find_paths":
            result = query_engine.find_paths(
                start_type=params_dict.get("start_type"),
                end_type=params_dict.get("end_type"),
                relationship_types=params_dict.get("relationship_types"),
                max_length=params_dict.get("max_length", 5)
            )
        
        elif query_type_str == "aggregate":
            result = query_engine.aggregate(
                entity_type=params_dict.get("entity_type"),
                group_by=params_dict.get("group_by"),
                aggregate_property=params_dict.get("aggregate_property"),
                aggregation_function=params_dict.get("aggregation_function", "count")
            )
        
        else:
            raise NullRuntimeError(f"Unknown query type: {query_type_str}")
        
        # Convert results
        return _convert_to_null_value({
            "matches": result.matches,
            "total_count": result.total_count,
            "execution_time": result.execution_time,
            "query_string": result.query_string
        })
        
    except Exception as e:
        logger.error(f"Failed to execute query: {e}")
        raise NullRuntimeError(f"Failed to execute query: {e}")


def REASON(ctx: NullCallContext, reasoning_type: NullValue, parameters: NullValue) -> NullValue:
    """Perform rule-based inference on the knowledge graph.

    Args:
        reasoning_type: Type of reasoning ("forward", "backward", "explain")
        parameters: Dictionary of reasoning parameters
        
    Returns:
        Inference results
    """
    try:
        graph_store = _ensure_graph_store()
        inference_engine = _inference_engine
        
        if inference_engine is None:
            raise NullRuntimeError("Inference engine not initialized")
        
        # Convert inputs
        reasoning_type_str = _convert_null_value(reasoning_type)
        params_dict = _convert_null_value(parameters)
        
        if reasoning_type_str == "forward":
            max_iterations = params_dict.get("max_iterations", 100)
            new_facts = inference_engine.infer_forward(max_iterations)
            
            return _convert_to_null_value({
                "new_facts": [
                    {
                        "id": str(fact.id),
                        "subject": fact.subject,
                        "predicate": fact.predicate,
                        "object": fact.object,
                        "confidence": fact.confidence,
                        "created_at": fact.created_at
                    }
                    for fact in new_facts
                ],
                "count": len(new_facts)
            })
        
        elif reasoning_type_str == "backward":
            goal = params_dict.get("goal")
            if not goal:
                raise NullRuntimeError("Goal is required for backward chaining")
            
            proof_paths = inference_engine.infer_backward(goal)
            
            return _convert_to_null_value({
                "goal": goal,
                "proof_paths": [
                    [
                        {
                            "id": str(fact.id),
                            "subject": fact.subject,
                            "predicate": fact.predicate,
                            "object": fact.object,
                            "confidence": fact.confidence
                        }
                        for fact in path
                    ]
                    for path in proof_paths
                ],
                "count": len(proof_paths)
            })
        
        elif reasoning_type_str == "explain":
            fact_id_str = params_dict.get("fact_id")
            if not fact_id_str:
                raise NullRuntimeError("fact_id is required for explanation")
            
            fact_id = UUID(fact_id_str)
            explanation = inference_engine.explain_inference(fact_id)
            
            return _convert_to_null_value(explanation)
        
        else:
            raise NullRuntimeError(f"Unknown reasoning type: {reasoning_type_str}")
        
    except Exception as e:
        logger.error(f"Failed to perform reasoning: {e}")
        raise NullRuntimeError(f"Failed to perform reasoning: {e}")


def LINK_EXTERNAL(ctx: NullCallContext, entity_ids: NullValue, sources: NullValue, confidence_threshold: NullValue = None) -> NullValue:
    """Link local entities to external knowledge bases.
    
    Args:
        entity_ids: List of entity IDs to link
        sources: List of external sources ("wikidata", "dbpedia")
        confidence_threshold: Minimum confidence for linking (default: 0.7)
        
    Returns:
        Linking results with confidence scores
    """
    try:
        graph_store = _ensure_graph_store()
        entity_resolver = _entity_resolver
        external_kb = _external_kb
        
        if entity_resolver is None or external_kb is None:
            raise NullRuntimeError("Entity resolver or external KB not initialized")
        
        # Convert inputs
        entity_id_strs = _convert_null_value(entity_ids)
        sources_list = _convert_null_value(sources)
        threshold = _convert_null_value(confidence_threshold) if confidence_threshold else 0.7
        
        # Get entities to link
        entities = []
        for entity_id_str in entity_id_strs:
            entity_id = UUID(entity_id_str)
            entity = graph_store.get_entity(entity_id)
            if entity:
                entities.append(entity)
        
        if not entities:
            return _convert_to_null_value({
                "linked_entities": [],
                "count": 0
            })
        
        # Link entities to external sources
        linked_pairs = []
        for entity in entities:
            for source in sources_list:
                try:
                    # Search for matches in external source
                    search_results = external_kb.search_all_sources(
                        entity.properties.get("name", ""), limit=5
                    )
                    
                    for source_name, external_entities in search_results.items():
                        for external_entity in external_entities:
                            # Calculate similarity
                            similarity = external_kb._calculate_similarity(entity, external_entity)
                            
                            if similarity >= threshold:
                                linked_pairs.append({
                                    "local_entity": {
                                        "id": str(entity.id),
                                        "type": entity.type,
                                        "properties": entity.properties
                                    },
                                    "external_entity": {
                                        "source": external_entity.external_source,
                                        "id": external_entity.external_id,
                                        "labels": external_entity.labels,
                                        "descriptions": external_entity.descriptions
                                    },
                                    "confidence": similarity,
                                    "source": source_name
                                })
                except Exception as e:
                    logger.warning(f"Failed to link entity {entity.id} to {source}: {e}")
                    continue
        
        return _convert_to_null_value({
            "linked_entities": linked_pairs,
            "count": len(linked_pairs),
            "threshold": threshold
        })
        
    except Exception as e:
        logger.error(f"Failed to link external entities: {e}")
        raise NullRuntimeError(f"Failed to link external entities: {e}")