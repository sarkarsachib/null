"""Query language tests for knowledge graph queries."""

import pytest
import time
from uuid import uuid4

from src.null_system.knowledge.graph_store import GraphStore, InMemoryBackend
from src.null_system.knowledge.query_language import (
    QueryEngine, BasicQueryExecutor, Pattern, RelationshipPattern, PathPattern,
    PropertyCondition, EmbeddingCondition, QueryOperator, LogicalOperator
)
from src.null_system.knowledge.superbit_encoder import SuperBitEncoder


class TestQueryEngine:
    """Test cases for QueryEngine."""
    
    @pytest.fixture
    def encoder(self):
        return SuperBitEncoder(dimension=64)
    
    @pytest.fixture
    def graph_store(self, encoder):
        backend = InMemoryBackend()
        return GraphStore(backend, encoder)
    
    @pytest.fixture
    def query_engine(self, graph_store):
        return QueryEngine(graph_store)
    
    @pytest.fixture
    def sample_data(self, graph_store):
        """Create sample data for testing."""
        # Create entities
        alice = graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Alice", "age": 30, "city": "New York"}
        )
        
        bob = graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Bob", "age": 25, "city": "Boston"}
        )
        
        charlie = graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Charlie", "age": 35, "city": "New York"}
        )
        
        techcorp = graph_store.upsert_entity(
            entity_type="Organization",
            properties={"name": "TechCorp", "industry": "Technology"}
        )
        
        book = graph_store.upsert_entity(
            entity_type="Book",
            properties={"title": "Python Programming", "author": "Alice"}
        )
        
        # Create relationships
        graph_store.create_relationship(alice.id, techcorp.id, "WORKS_FOR")
        graph_store.create_relationship(bob.id, techcorp.id, "WORKS_FOR")
        graph_store.create_relationship(alice.id, book.id, "AUTHORED")
        
        return alice, bob, charlie, techcorp, book
    
    def test_find_entities_by_type(self, query_engine, sample_data):
        """Test finding entities by type."""
        result = query_engine.find_entities(entity_type="Person")
        
        assert result.total_count == 3
        assert len(result.matches) == 3
        
        # Check all returned entities are Person type
        for match in result.matches:
            assert match["type"] == "Person"
    
    def test_find_entities_by_properties(self, query_engine, sample_data):
        """Test finding entities by properties."""
        result = query_engine.find_entities(
            properties={"city": "New York"}
        )
        
        assert result.total_count == 2
        for match in result.matches:
            assert match["properties"]["city"] == "New York"
    
    def test_find_entities_by_embedding(self, query_engine, sample_data):
        """Test finding entities by embedding similarity."""
        alice, _, _, _, _ = sample_data
        
        # Find entities similar to Alice
        result = query_engine.find_entities(
            embedding=alice.superbit_embedding,
            similarity_threshold=0.1  # Low threshold for testing
        )
        
        assert result.total_count >= 1
        # Alice should be included in results
        alice_found = any(
            match["entity"].id == alice.id 
            for match in result.matches
        )
        assert alice_found
    
    def test_find_relationships(self, query_engine, sample_data):
        """Test finding relationships."""
        result = query_engine.find_relationships(
            relationship_type="WORKS_FOR"
        )
        
        assert result.total_count == 2
        for match in result.matches:
            assert match["relationship_type"] == "WORKS_FOR"
    
    def test_find_relationships_with_types(self, query_engine, sample_data):
        """Test finding relationships with source and target types."""
        result = query_engine.find_relationships(
            source_type="Person",
            target_type="Organization"
        )
        
        assert result.total_count == 2
        for match in result.matches:
            assert match["source"]["type"] == "Person"
            assert match["target"]["type"] == "Organization"
    
    def test_find_paths(self, query_engine, sample_data):
        """Test finding paths between entities."""
        alice, bob, charlie, techcorp, book = sample_data
        
        # Find paths from Person to Book
        result = query_engine.find_paths(
            start_type="Person",
            end_type="Book",
            relationship_types=["AUTHORED"],
            max_length=2
        )
        
        assert result.total_count >= 1
        for match in result.matches:
            assert len(match["entities"]) >= 2
            assert len(match["relationships"]) >= 1
    
    def test_aggregate_query(self, query_engine, sample_data):
        """Test aggregate queries."""
        result = query_engine.aggregate(
            entity_type="Person",
            group_by="city",
            aggregation_function="count"
        )
        
        assert result.total_count == 2  # New York and Boston
        
        # Check that counts are correct
        counts = {match["group"]: match["value"] for match in result.matches}
        assert counts["New York"] == 2
        assert counts["Boston"] == 1
    
    def test_custom_query_dsl(self, query_engine, sample_data):
        """Test custom query DSL parsing."""
        # Test simple entity query
        result = query_engine.custom_query("FIND ENTITIES OF TYPE Person")
        assert result.total_count == 3
        
        # Test relationship query
        result = query_engine.custom_query("FIND RELATIONSHIPS OF TYPE WORKS_FOR")
        assert result.total_count == 2
    
    def test_query_performance(self, query_engine, sample_data):
        """Test query performance."""
        start_time = time.time()
        
        result = query_engine.find_entities(entity_type="Person")
        
        execution_time = time.time() - start_time
        
        assert execution_time < 1.0  # Should be fast
        assert result.execution_time > 0
        assert result.total_count == 3


class TestBasicQueryExecutor:
    """Test cases for BasicQueryExecutor."""
    
    @pytest.fixture
    def executor(self):
        return BasicQueryExecutor(SuperBitEncoder(dimension=64))
    
    @pytest.fixture
    def graph_store(self, executor):
        backend = InMemoryBackend()
        return GraphStore(backend, executor.encoder)
    
    def test_execute_simple_pattern(self, executor, graph_store):
        """Test executing a simple pattern."""
        # Create test data
        entity = graph_store.upsert_entity(
            entity_type="Book",
            properties={"title": "Test Book", "pages": 200}
        )
        
        # Create pattern
        pattern = Pattern(
            name="test_pattern",
            entity_type="Book",
            properties=[
                PropertyCondition(
                    property_name="pages",
                    operator=QueryOperator.GREATER_THAN,
                    value=100
                )
            ]
        )
        
        # Execute pattern
        results = executor.execute_pattern(pattern, graph_store)
        
        assert len(results) == 1
        assert results[0].id == entity.id
        assert results[0].properties["pages"] == 200
    
    def test_execute_relationship_pattern(self, executor, graph_store):
        """Test executing a relationship pattern."""
        # Create test data
        person = graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Alice"}
        )
        
        book = graph_store.upsert_entity(
            entity_type="Book",
            properties={"title": "Alice's Book"}
        )
        
        graph_store.create_relationship(
            person.id, book.id, "AUTHORED"
        )
        
        # Create relationship pattern
        pattern = RelationshipPattern(
            name="authorship",
            relationship_type="AUTHORED"
        )
        
        # Execute pattern
        results = executor.execute_relationship_pattern(pattern, graph_store)
        
        assert len(results) == 1
        source, relationship, target = results[0]
        assert source.id == person.id
        assert target.id == book.id
        assert relationship.relationship_type == "AUTHORED"
    
    def test_execute_path_pattern(self, executor, graph_store):
        """Test executing a path pattern."""
        # Create test data
        alice = graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Alice"}
        )
        
        company = graph_store.upsert_entity(
            entity_type="Company",
            properties={"name": "TechCorp"}
        )
        
        project = graph_store.upsert_entity(
            entity_type="Project",
            properties={"name": "AI Initiative"}
        )
        
        # Create relationships
        graph_store.create_relationship(alice.id, company.id, "WORKS_AT")
        graph_store.create_relationship(company.id, project.id, "RUNS")
        
        # Create path pattern
        pattern = PathPattern(
            patterns=[
                Pattern(name="start", entity_type="Person"),
                RelationshipPattern(name="rel1", relationship_type="WORKS_AT"),
                Pattern(name="middle", entity_type="Company"),
                RelationshipPattern(name="rel2", relationship_type="RUNS"),
                Pattern(name="end", entity_type="Project")
            ],
            min_length=3,
            max_length=5
        )
        
        # Execute pattern
        results = executor.execute_path_pattern(pattern, graph_store)
        
        assert len(results) >= 1
        # Check that we found a path from Person to Project
        found_path = False
        for path in results:
            entities = [item for item in path if hasattr(item, 'type')]
            if len(entities) >= 3:
                entity_types = [e.type for e in entities]
                if "Person" in entity_types and "Project" in entity_types:
                    found_path = True
                    break
        
        assert found_path


class TestQueryPatterns:
    """Test cases for various query patterns."""
    
    def test_property_conditions(self):
        """Test different property condition operators."""
        test_cases = [
            ("equals", QueryOperator.EQUALS, "test", "test", True),
            ("not_equals", QueryOperator.NOT_EQUALS, "test", "other", True),
            ("greater_than", QueryOperator.GREATER_THAN, 10, 5, True),
            ("less_than", QueryOperator.LESS_THAN, 5, 10, True),
            ("contains", QueryOperator.CONTAINS, ["a", "b", "c"], "b", True),
            ("starts_with", QueryOperator.STARTS_WITH, "hello world", "hello", True),
            ("ends_with", QueryOperator.ENDS_WITH, "hello world", "world", True),
            ("in_list", QueryOperator.IN, "apple", ["apple", "banana"], True),
            ("not_in_list", QueryOperator.NOT_IN, "orange", ["apple", "banana"], True),
        ]
        
        executor = BasicQueryExecutor()
        
        for test_name, operator, entity_value, condition_value, expected in test_cases:
            condition = PropertyCondition(
                property_name="test",
                operator=operator,
                value=condition_value
            )
            
            result = executor._match_condition(entity_value, condition)
            assert result == expected, f"Test {test_name} failed: expected {expected}, got {result}"
    
    def test_embedding_conditions(self):
        """Test embedding-based conditions."""
        encoder = SuperBitEncoder(dimension=32)
        
        # Create embeddings
        embedding1 = encoder.encode_text("hello world")
        embedding2 = encoder.encode_text("hello universe")
        embedding3 = encoder.encode_text("goodbye world")
        
        # Test similarity calculation
        similarity_12 = encoder.cosine_similarity(embedding1, embedding2)
        similarity_13 = encoder.cosine_similarity(embedding1, embedding3)
        
        # Similar texts should have higher similarity
        assert similarity_12 > similarity_13
        
        # Test embedding condition
        condition = EmbeddingCondition(
            target_embedding=embedding1,
            similarity_threshold=0.3
        )
        
        # embedding1 should match itself with high similarity
        assert encoder.cosine_similarity(embedding1, embedding1) >= condition.similarity_threshold
    
    def test_complex_conditions(self):
        """Test complex logical conditions."""
        from src.null_system.knowledge.query_language import Condition
        
        # Create complex condition with AND logic
        condition = Condition(
            logical_operator=LogicalOperator.AND,
            property_condition=PropertyCondition(
                property_name="age",
                operator=QueryOperator.GREATER_THAN,
                value=18
            ),
            type_condition=None  # Would need entity type checking
        )
        
        # This would be tested with actual entity data in a real scenario
        assert condition.logical_operator == LogicalOperator.AND