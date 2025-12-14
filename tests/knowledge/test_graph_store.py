"""Knowledge graph tests for graph store functionality."""

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from uuid import uuid4

from src.null_system.knowledge.graph_store import (
    GraphStore, InMemoryBackend, SQLiteBackend,
    Entity, Relationship
)
from src.null_system.knowledge.superbit_encoder import SuperBitEncoder


class TestGraphStore:
    """Test cases for GraphStore."""
    
    @pytest.fixture
    def encoder(self):
        return SuperBitEncoder(dimension=64)
    
    @pytest.fixture
    def memory_backend(self):
        return InMemoryBackend()
    
    @pytest.fixture
    def sqlite_backend(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield SQLiteBackend(Path(temp_dir) / "test.db")
    
    @pytest.fixture
    def memory_graph_store(self, memory_backend, encoder):
        return GraphStore(memory_backend, encoder)
    
    @pytest.fixture
    def sqlite_graph_store(self, sqlite_backend, encoder):
        return GraphStore(sqlite_backend, encoder)
    
    def test_upsert_entity_memory(self, memory_graph_store):
        """Test entity upsert with in-memory backend."""
        entity = memory_graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Alice", "age": 30}
        )
        
        assert entity.id is not None
        assert entity.type == "Person"
        assert entity.properties["name"] == "Alice"
        assert entity.properties["age"] == 30
        assert entity.superbit_embedding is not None
    
    def test_upsert_entity_sqlite(self, sqlite_graph_store):
        """Test entity upsert with SQLite backend."""
        entity = sqlite_graph_store.upsert_entity(
            entity_type="Organization",
            properties={"name": "TechCorp", "founded": 2020}
        )
        
        assert entity.id is not None
        assert entity.type == "Organization"
        assert entity.properties["name"] == "TechCorp"
        assert entity.properties["founded"] == 2020
    
    def test_get_entity(self, memory_graph_store):
        """Test entity retrieval."""
        original_entity = memory_graph_store.upsert_entity(
            entity_type="Book",
            properties={"title": "Python Programming", "pages": 400}
        )
        
        retrieved_entity = memory_graph_store.get_entity(original_entity.id)
        
        assert retrieved_entity is not None
        assert retrieved_entity.id == original_entity.id
        assert retrieved_entity.type == "Book"
        assert retrieved_entity.properties["title"] == "Python Programming"
    
    def test_create_relationship(self, memory_graph_store):
        """Test relationship creation."""
        # Create entities first
        person = memory_graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Alice"}
        )
        
        book = memory_graph_store.upsert_entity(
            entity_type="Book",
            properties={"title": "Python Programming"}
        )
        
        # Create relationship
        relationship = memory_graph_store.create_relationship(
            source_id=person.id,
            target_id=book.id,
            relationship_type="AUTHORED",
            properties={"role": "main_author"}
        )
        
        assert relationship.id is not None
        assert relationship.source_id == person.id
        assert relationship.target_id == book.id
        assert relationship.relationship_type == "AUTHORED"
        assert relationship.properties["role"] == "main_author"
    
    def test_find_entities_by_properties(self, memory_graph_store):
        """Test finding entities by properties."""
        # Create test entities
        memory_graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Alice", "city": "New York"}
        )
        
        memory_graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Bob", "city": "New York"}
        )
        
        memory_graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Charlie", "city": "Boston"}
        )
        
        # Find by exact match
        results = memory_graph_store.find_entities_by_properties(
            properties={"city": "New York"}
        )
        
        assert len(results) == 2
        cities = [entity.properties["city"] for entity in results]
        assert "New York" in cities
        assert "Boston" not in cities
    
    def test_find_entities_by_embedding(self, memory_graph_store):
        """Test finding entities by embedding similarity."""
        encoder = memory_graph_store.encoder
        
        # Create entities with known embeddings
        entity1 = memory_graph_store.upsert_entity(
            entity_type="City",
            properties={"name": "Paris"}
        )
        
        entity2 = memory_graph_store.upsert_entity(
            entity_type="City", 
            properties={"name": "Lyon"}
        )
        
        entity3 = memory_graph_store.upsert_entity(
            entity_type="Country",
            properties={"name": "France"}
        )
        
        # Find similar entities
        similar_entities = memory_graph_store.find_entities_by_embedding(
            embedding=entity1.superbit_embedding,
            threshold=0.5,
            limit=10
        )
        
        assert len(similar_entities) >= 1
        # Entity1 should be most similar to itself (or at least appear in results)
        found_entity1 = any(entity.id == entity1.id for entity, score in similar_entities)
        assert found_entity1
    
    def test_get_neighbors(self, memory_graph_store):
        """Test neighbor retrieval."""
        # Create entities and relationships
        alice = memory_graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Alice"}
        )
        
        bob = memory_graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Bob"}
        )
        
        charlie = memory_graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Charlie"}
        )
        
        # Create relationships
        memory_graph_store.create_relationship(alice.id, bob.id, "FRIEND_OF")
        memory_graph_store.create_relationship(alice.id, charlie.id, "COLLEAGUE_OF")
        
        # Get Alice's neighbors
        neighbors = memory_graph_store.get_neighbors(alice.id)
        
        assert len(neighbors) == 2
        neighbor_names = [neighbor[0].properties["name"] for neighbor in neighbors]
        assert "Bob" in neighbor_names
        assert "Charlie" in neighbor_names
    
    def test_delete_entity_cascade(self, memory_graph_store):
        """Test entity deletion with cascade."""
        # Create entities and relationships
        person = memory_graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Alice"}
        )
        
        book = memory_graph_store.upsert_entity(
            entity_type="Book",
            properties={"title": "Python Programming"}
        )
        
        relationship = memory_graph_store.create_relationship(
            person.id, book.id, "AUTHORED"
        )
        
        # Delete person with cascade
        success = memory_graph_store.delete_entity(person.id, cascade=True)
        assert success
        
        # Verify person is deleted
        assert memory_graph_store.get_entity(person.id) is None
        
        # Verify relationship is also deleted
        assert memory_graph_store.backend.get_relationship(relationship.id) is None
    
    def test_graph_statistics(self, memory_graph_store):
        """Test graph statistics."""
        # Add some data
        memory_graph_store.upsert_entity(entity_type="Person", properties={"name": "Alice"})
        memory_graph_store.upsert_entity(entity_type="Person", properties={"name": "Bob"})
        memory_graph_store.upsert_entity(entity_type="Book", properties={"title": "Python Guide"})
        
        stats = memory_graph_store.get_graph_stats()
        
        assert stats["total_entities"] == 3
        assert stats["entity_types"]["Person"] == 2
        assert stats["entity_types"]["Book"] == 1
        assert stats["total_relationships"] == 0
        assert stats["snapshots"] == 0
    
    def test_snapshot_and_restore(self, memory_graph_store):
        """Test snapshot creation and restoration."""
        # Add initial data
        entity1 = memory_graph_store.upsert_entity(
            entity_type="Book",
            properties={"title": "Original Title"}
        )
        
        snapshot = memory_graph_store.create_snapshot()
        assert snapshot.id is not None
        
        # Modify data
        memory_graph_store.upsert_entity(
            entity_type="Book",
            properties={"title": "Modified Title"}
        )
        
        # Verify modification
        entities = memory_graph_store.list_entities()
        assert len(entities) == 2
        
        # Restore from snapshot
        success = memory_graph_store.restore_snapshot(snapshot.id)
        assert success
        
        # Verify restoration
        entities_after_restore = memory_graph_store.list_entities()
        assert len(entities_after_restore) == 1
        assert entities_after_restore[0].properties["title"] == "Original Title"


class TestInMemoryBackend:
    """Test cases for InMemoryBackend."""
    
    def test_entity_operations(self):
        """Test basic entity operations."""
        backend = InMemoryBackend()
        encoder = SuperBitEncoder()
        
        # Create entity
        entity = Entity(
            id=uuid4(),
            type="Test",
            properties={"name": "test"}
        )
        
        backend.store_entity(entity)
        
        # Retrieve entity
        retrieved = backend.get_entity(entity.id)
        assert retrieved is not None
        assert retrieved.id == entity.id
        assert retrieved.type == "Test"
        
        # List entities
        entities = backend.list_entities("Test")
        assert len(entities) == 1
        
        # Delete entity
        success = backend.delete_entity(entity.id)
        assert success
        
        # Verify deletion
        retrieved = backend.get_entity(entity.id)
        assert retrieved is None
    
    def test_relationship_operations(self):
        """Test basic relationship operations."""
        backend = InMemoryBackend()
        
        # Create entities
        entity1 = Entity(id=uuid4(), type="A")
        entity2 = Entity(id=uuid4(), type="B")
        
        backend.store_entity(entity1)
        backend.store_entity(entity2)
        
        # Create relationship
        relationship = Relationship(
            id=uuid4(),
            source_id=entity1.id,
            target_id=entity2.id,
            relationship_type="TEST_REL"
        )
        
        backend.store_relationship(relationship)
        
        # Retrieve relationship
        retrieved = backend.get_relationship(relationship.id)
        assert retrieved is not None
        assert retrieved.relationship_type == "TEST_REL"
        
        # Find relationships by source
        source_rels = backend.get_relationships_by_source(entity1.id)
        assert len(source_rels) == 1
        
        # Find relationships by target
        target_rels = backend.get_relationships_by_target(entity2.id)
        assert len(target_rels) == 1
        
        # Delete relationship
        success = backend.delete_relationship(relationship.id)
        assert success


class TestSQLiteBackend:
    """Test cases for SQLiteBackend."""
    
    def test_entity_persistence(self):
        """Test entity persistence in SQLite."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            backend = SQLiteBackend(db_path)
            
            # Create entity
            entity = Entity(
                id=uuid4(),
                type="Test",
                properties={"name": "test", "value": 42},
                superbit_embedding=[1, 0, 1, 0]
            )
            
            backend.store_entity(entity)
            
            # Create new backend instance (simulating restart)
            new_backend = SQLiteBackend(db_path)
            
            # Retrieve entity
            retrieved = new_backend.get_entity(entity.id)
            assert retrieved is not None
            assert retrieved.id == entity.id
            assert retrieved.type == "Test"
            assert retrieved.properties["name"] == "test"
            assert retrieved.properties["value"] == 42
            assert retrieved.superbit_embedding == [1, 0, 1, 0]
    
    def test_relationship_persistence(self):
        """Test relationship persistence in SQLite."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            backend = SQLiteBackend(db_path)
            
            # Create entities
            entity1 = Entity(id=uuid4(), type="A")
            entity2 = Entity(id=uuid4(), type="B")
            
            backend.store_entity(entity1)
            backend.store_entity(entity2)
            
            # Create relationship
            relationship = Relationship(
                id=uuid4(),
                source_id=entity1.id,
                target_id=entity2.id,
                relationship_type="TEST_REL",
                properties={"weight": 0.8},
                confidence=0.9
            )
            
            backend.store_relationship(relationship)
            
            # Create new backend instance
            new_backend = SQLiteBackend(db_path)
            
            # Retrieve relationship
            retrieved = new_backend.get_relationship(relationship.id)
            assert retrieved is not None
            assert retrieved.relationship_type == "TEST_REL"
            assert retrieved.properties["weight"] == 0.8
            assert retrieved.confidence == 0.9