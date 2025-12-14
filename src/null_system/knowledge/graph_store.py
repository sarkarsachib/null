"""Graph store implementation for knowledge graphs with Super-Bit encoding."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4

import sqlite3

from .superbit_encoder import SuperBitEncoder

# Import at runtime to avoid circular imports
def _get_transaction_manager_class():
    from .transaction import TransactionManager
    return TransactionManager

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents a graph entity with Super-Bit encoding."""
    id: UUID
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    superbit_embedding: Optional[List[int]] = None
    created_at: float = field(default_factory=lambda: __import__('time').time())
    updated_at: float = field(default_factory=lambda: __import__('time').time())


@dataclass 
class Relationship:
    """Represents a directed relationship between entities."""
    id: UUID
    source_id: UUID
    target_id: UUID
    relationship_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: float = field(default_factory=lambda: __import__('time').time())


@dataclass
class GraphSnapshot:
    """Represents a point-in-time snapshot of the graph."""
    id: UUID
    entities: Dict[UUID, Entity] = field(default_factory=dict)
    relationships: Dict[UUID, Relationship] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: __import__('time').time())


class Backend(ABC):
    """Abstract backend for graph storage."""
    
    @abstractmethod
    def store_entity(self, entity: Entity) -> None:
        pass
    
    @abstractmethod
    def get_entity(self, entity_id: UUID) -> Optional[Entity]:
        pass
    
    @abstractmethod
    def delete_entity(self, entity_id: UUID) -> bool:
        pass
    
    @abstractmethod
    def list_entities(self, entity_type: Optional[str] = None) -> List[Entity]:
        pass
    
    @abstractmethod
    def store_relationship(self, relationship: Relationship) -> None:
        pass
    
    @abstractmethod
    def get_relationship(self, relationship_id: UUID) -> Optional[Relationship]:
        pass
    
    @abstractmethod
    def delete_relationship(self, relationship_id: UUID) -> bool:
        pass
    
    @abstractmethod
    def get_relationships_by_source(self, source_id: UUID) -> List[Relationship]:
        pass
    
    @abstractmethod
    def get_relationships_by_target(self, target_id: UUID) -> List[Relationship]:
        pass


class InMemoryBackend(Backend):
    """In-memory backend for development and testing."""
    
    def __init__(self):
        self._entities: Dict[UUID, Entity] = {}
        self._relationships: Dict[UUID, Relationship] = {}
    
    def store_entity(self, entity: Entity) -> None:
        self._entities[entity.id] = entity
    
    def get_entity(self, entity_id: UUID) -> Optional[Entity]:
        return self._entities.get(entity_id)
    
    def delete_entity(self, entity_id: UUID) -> bool:
        return self._entities.pop(entity_id, None) is not None
    
    def list_entities(self, entity_type: Optional[str] = None) -> List[Entity]:
        if entity_type is None:
            return list(self._entities.values())
        return [e for e in self._entities.values() if e.type == entity_type]
    
    def store_relationship(self, relationship: Relationship) -> None:
        self._relationships[relationship.id] = relationship
    
    def get_relationship(self, relationship_id: UUID) -> Optional[Relationship]:
        return self._relationships.get(relationship_id)
    
    def delete_relationship(self, relationship_id: UUID) -> bool:
        return self._relationships.pop(relationship_id, None) is not None
    
    def get_relationships_by_source(self, source_id: UUID) -> List[Relationship]:
        return [r for r in self._relationships.values() if r.source_id == source_id]
    
    def get_relationships_by_target(self, target_id: UUID) -> List[Relationship]:
        return [r for r in self._relationships.values() if r.target_id == target_id]


class SQLiteBackend(Backend):
    """SQLite backend for persistent storage."""
    
    def __init__(self, db_path: Union[str, Path]):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    properties TEXT NOT NULL,
                    superbit_embedding TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    properties TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 1.0,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (source_id) REFERENCES entities (id),
                    FOREIGN KEY (target_id) REFERENCES entities (id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entities_type ON entities (type)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships (source_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships (target_id)
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def _row_to_entity(self, row) -> Entity:
        """Convert database row to Entity object."""
        return Entity(
            id=UUID(row[0]),
            type=row[1],
            properties=json.loads(row[2]),
            superbit_embedding=json.loads(row[3]) if row[3] else None,
            created_at=row[4],
            updated_at=row[5]
        )
    
    def _row_to_relationship(self, row) -> Relationship:
        """Convert database row to Relationship object."""
        return Relationship(
            id=UUID(row[0]),
            source_id=UUID(row[1]),
            target_id=UUID(row[2]),
            relationship_type=row[3],
            properties=json.loads(row[4]),
            confidence=row[5],
            created_at=row[6]
        )
    
    def store_entity(self, entity: Entity) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO entities 
                (id, type, properties, superbit_embedding, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(entity.id),
                entity.type,
                json.dumps(entity.properties),
                json.dumps(entity.superbit_embedding) if entity.superbit_embedding else None,
                entity.created_at,
                entity.updated_at
            ))
            conn.commit()
        finally:
            conn.close()
    
    def get_entity(self, entity_id: UUID) -> Optional[Entity]:
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute("""
                SELECT id, type, properties, superbit_embedding, created_at, updated_at
                FROM entities WHERE id = ?
            """, (str(entity_id),)).fetchone()
            
            return self._row_to_entity(row) if row else None
        finally:
            conn.close()
    
    def delete_entity(self, entity_id: UUID) -> bool:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("DELETE FROM entities WHERE id = ?", (str(entity_id),))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def list_entities(self, entity_type: Optional[str] = None) -> List[Entity]:
        conn = sqlite3.connect(self.db_path)
        try:
            if entity_type:
                rows = conn.execute("""
                    SELECT id, type, properties, superbit_embedding, created_at, updated_at
                    FROM entities WHERE type = ?
                    ORDER BY created_at
                """, (entity_type,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, type, properties, superbit_embedding, created_at, updated_at
                    FROM entities ORDER BY created_at
                """).fetchall()
            
            return [self._row_to_entity(row) for row in rows]
        finally:
            conn.close()
    
    def store_relationship(self, relationship: Relationship) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO relationships
                (id, source_id, target_id, relationship_type, properties, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(relationship.id),
                str(relationship.source_id),
                str(relationship.target_id),
                relationship.relationship_type,
                json.dumps(relationship.properties),
                relationship.confidence,
                relationship.created_at
            ))
            conn.commit()
        finally:
            conn.close()
    
    def get_relationship(self, relationship_id: UUID) -> Optional[Relationship]:
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute("""
                SELECT id, source_id, target_id, relationship_type, properties, confidence, created_at
                FROM relationships WHERE id = ?
            """, (str(relationship_id),)).fetchone()
            
            return self._row_to_relationship(row) if row else None
        finally:
            conn.close()
    
    def delete_relationship(self, relationship_id: UUID) -> bool:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("DELETE FROM relationships WHERE id = ?", (str(relationship_id),))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def get_relationships_by_source(self, source_id: UUID) -> List[Relationship]:
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT id, source_id, target_id, relationship_type, properties, confidence, created_at
                FROM relationships WHERE source_id = ?
                ORDER BY created_at
            """, (str(source_id),)).fetchall()
            
            return [self._row_to_relationship(row) for row in rows]
        finally:
            conn.close()
    
    def get_relationships_by_target(self, target_id: UUID) -> List[Relationship]:
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT id, source_id, target_id, relationship_type, properties, confidence, created_at
                FROM relationships WHERE target_id = ?
                ORDER BY created_at
            """, (str(target_id),)).fetchall()
            
            return [self._row_to_relationship(row) for row in rows]
        finally:
            conn.close()


class GraphStore:
    """Main graph store with ACID guarantees and Super-Bit encoding."""
    
    def __init__(
        self,
        backend: Backend,
        encoder: Optional[SuperBitEncoder] = None,
        transaction_manager: Optional[TransactionManager] = None
    ):
        self.backend = backend
        self.encoder = encoder or SuperBitEncoder()
        TransactionManager = _get_transaction_manager_class()
        self.transaction_manager = transaction_manager or TransactionManager()
        self._snapshots: Dict[UUID, GraphSnapshot] = {}
        
        logger.info(f"Initialized GraphStore with {type(backend).__name__} backend")
    
    def upsert_entity(
        self,
        entity_type: str,
        properties: Dict[str, Any],
        entity_id: Optional[UUID] = None,
        embedding: Optional[List[int]] = None,
        transaction: Optional[Transaction] = None
    ) -> Entity:
        """Create or update an entity with Super-Bit encoding."""
        
        if transaction:
            return transaction.upsert_entity(
                entity_type, properties, entity_id, embedding
            )
        
        entity_id = entity_id or uuid4()
        
        # Generate Super-Bit embedding if not provided
        if embedding is None and self.encoder:
            embedding = self.encoder.encode_entity(entity_type, properties)
        
        # Check if entity exists
        existing = self.backend.get_entity(entity_id)
        current_time = __import__('time').time()
        
        if existing:
            # Update existing entity
            entity = Entity(
                id=entity_id,
                type=entity_type,
                properties=properties,
                superbit_embedding=embedding,
                created_at=existing.created_at,
                updated_at=current_time
            )
        else:
            # Create new entity
            entity = Entity(
                id=entity_id,
                type=entity_type,
                properties=properties,
                superbit_embedding=embedding,
                created_at=current_time,
                updated_at=current_time
            )
        
        self.backend.store_entity(entity)
        logger.debug(f"Upserted entity {entity_id} of type {entity_type}")
        return entity
    
    def create_relationship(
        self,
        source_id: UUID,
        target_id: UUID,
        relationship_type: str,
        properties: Dict[str, Any] = None,
        confidence: float = 1.0,
        transaction: Optional[Transaction] = None
    ) -> Relationship:
        """Create a relationship between entities."""
        
        if transaction:
            return transaction.create_relationship(
                source_id, target_id, relationship_type, properties, confidence
            )
        
        # Validate entities exist
        if not self.backend.get_entity(source_id):
            raise ValueError(f"Source entity {source_id} does not exist")
        
        if not self.backend.get_entity(target_id):
            raise ValueError(f"Target entity {target_id} does not exist")
        
        relationship = Relationship(
            id=uuid4(),
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            properties=properties or {},
            confidence=confidence
        )
        
        self.backend.store_relationship(relationship)
        logger.debug(f"Created relationship {relationship.id}: {source_id} -> {target_id}")
        return relationship
    
    def get_entity(self, entity_id: UUID) -> Optional[Entity]:
        """Retrieve an entity by ID."""
        return self.backend.get_entity(entity_id)
    
    def list_entities(self, entity_type: Optional[str] = None) -> List[Entity]:
        """List all entities, optionally filtered by type."""
        return self.backend.list_entities(entity_type)
    
    def find_entities_by_properties(
        self,
        properties: Dict[str, Any],
        entity_type: Optional[str] = None
    ) -> List[Entity]:
        """Find entities by exact property matches."""
        all_entities = self.list_entities(entity_type)
        matches = []
        
        for entity in all_entities:
            if all(entity.properties.get(k) == v for k, v in properties.items()):
                matches.append(entity)
        
        return matches
    
    def find_entities_by_embedding(
        self,
        embedding: List[int],
        threshold: float = 0.8,
        limit: int = 100
    ) -> List[Tuple[Entity, float]]:
        """Find entities with similar embeddings using cosine similarity."""
        if not self.encoder:
            raise ValueError("SuperBitEncoder required for embedding search")
        
        candidates = self.list_entities()
        scored = []
        
        for entity in candidates:
            if entity.superbit_embedding:
                similarity = self.encoder.cosine_similarity(embedding, entity.superbit_embedding)
                if similarity >= threshold:
                    scored.append((entity, similarity))
        
        # Sort by similarity descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]
    
    def get_neighbors(
        self,
        entity_id: UUID,
        relationship_types: Optional[List[str]] = None
    ) -> List[Tuple[Entity, Relationship]]:
        """Get neighboring entities with relationships."""
        neighbors = []
        
        # Get relationships where entity is source
        out_relationships = self.backend.get_relationships_by_source(entity_id)
        
        # Get relationships where entity is target
        in_relationships = self.backend.get_relationships_by_target(entity_id)
        
        # Process outgoing relationships
        for rel in out_relationships:
            if not relationship_types or rel.relationship_type in relationship_types:
                target_entity = self.backend.get_entity(rel.target_id)
                if target_entity:
                    neighbors.append((target_entity, rel))
        
        # Process incoming relationships
        for rel in in_relationships:
            if not relationship_types or rel.relationship_type in relationship_types:
                source_entity = self.backend.get_entity(rel.source_id)
                if source_entity:
                    neighbors.append((source_entity, rel))
        
        return neighbors
    
    def delete_entity(self, entity_id: UUID, cascade: bool = True, transaction: Optional[Transaction] = None) -> bool:
        """Delete an entity, optionally cascading to relationships."""
        
        if transaction:
            return transaction.delete_entity(entity_id, cascade)
        
        # Delete all relationships involving this entity if cascade=True
        if cascade:
            relationships = []
            relationships.extend(self.backend.get_relationships_by_source(entity_id))
            relationships.extend(self.backend.get_relationships_by_target(entity_id))
            
            for rel in relationships:
                self.backend.delete_relationship(rel.id)
        
        return self.backend.delete_entity(entity_id)
    
    def delete_relationship(self, relationship_id: UUID, transaction: Optional[Transaction] = None) -> bool:
        """Delete a relationship."""
        
        if transaction:
            return transaction.delete_relationship(relationship_id)
        
        return self.backend.delete_relationship(relationship_id)
    
    def create_snapshot(self, name: Optional[str] = None) -> GraphSnapshot:
        """Create a point-in-time snapshot of the graph."""
        snapshot = GraphSnapshot(
            id=uuid4(),
            entities={e.id: e for e in self.list_entities()},
            relationships={r.id: r for r in self._get_all_relationships()}
        )
        self._snapshots[snapshot.id] = snapshot
        logger.info(f"Created graph snapshot {snapshot.id}")
        return snapshot
    
    def restore_snapshot(self, snapshot_id: UUID) -> bool:
        """Restore graph from a snapshot."""
        if snapshot_id not in self._snapshots:
            return False
        
        snapshot = self._snapshots[snapshot_id]
        
        # Clear current data
        for entity in self.list_entities():
            self.backend.delete_entity(entity.id)
        
        # Restore from snapshot
        for entity in snapshot.entities.values():
            self.backend.store_entity(entity)
        
        for relationship in snapshot.relationships.values():
            self.backend.store_relationship(relationship)
        
        logger.info(f"Restored graph from snapshot {snapshot_id}")
        return True
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the graph."""
        entities = self.list_entities()
        relationships = self._get_all_relationships()
        
        entity_types = {}
        relationship_types = {}
        
        for entity in entities:
            entity_types[entity.type] = entity_types.get(entity.type, 0) + 1
        
        for relationship in relationships:
            rel_type = relationship.relationship_type
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
        
        return {
            "total_entities": len(entities),
            "total_relationships": len(relationships),
            "entity_types": entity_types,
            "relationship_types": relationship_types,
            "snapshots": len(self._snapshots)
        }
    
    def _get_all_relationships(self) -> List[Relationship]:
        """Get all relationships (helper method)."""
        all_entities = self.list_entities()
        relationships = []
        
        for entity in all_entities:
            out_rels = self.backend.get_relationships_by_source(entity.id)
            in_rels = self.backend.get_relationships_by_target(entity.id)
            relationships.extend(out_rels)
            relationships.extend(in_rels)
        
        # Remove duplicates
        seen = set()
        unique_relationships = []
        for rel in relationships:
            if rel.id not in seen:
                seen.add(rel.id)
                unique_relationships.append(rel)
        
        return unique_relationships
    
    @classmethod
    def create_sqlite_backend(cls, db_path: Union[str, Path]) -> SQLiteBackend:
        """Create a SQLite backend."""
        return SQLiteBackend(db_path)