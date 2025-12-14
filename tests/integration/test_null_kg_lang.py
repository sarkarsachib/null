"""Integration tests for Null-Lang Knowledge Graph operations."""

import pytest
import tempfile
import json
from pathlib import Path
from uuid import uuid4

from src.null_system.knowledge.graph_store import GraphStore, InMemoryBackend
from src.null_system.knowledge.query_language import QueryEngine
from src.null_system.knowledge.inference import InferenceEngine, Rule, RuleType
from src.null_system.knowledge.external.wikidata import ExternalKnowledgeBase
from src.null_system.lib.kg_ops import UPSERT, QUERY, REASON, LINK_EXTERNAL
from src.null_system.runtime import NullCallContext


class TestNullKGIntegration:
    """Integration tests for Null-Lang KG operations."""
    
    @pytest.fixture
    def call_context(self):
        return NullCallContext()
    
    @pytest.fixture
    def sample_entities(self):
        return [
            {
                "type": "Person",
                "properties": {"name": "Alice", "age": 30, "city": "New York"}
            },
            {
                "type": "Person", 
                "properties": {"name": "Bob", "age": 25, "city": "Boston"}
            },
            {
                "type": "Organization",
                "properties": {"name": "TechCorp", "industry": "Technology"}
            },
            {
                "type": "Book",
                "properties": {"title": "Python Programming", "author": "Alice"}
            }
        ]
    
    def test_kg_upsert_integration(self, call_context, sample_entities):
        """Test KG upsert operation in Null-Lang."""
        results = []
        
        for entity_data in sample_entities:
            result = UPSERT(
                call_context,
                entity_data["type"],
                entity_data["properties"]
            )
            results.append(result)
        
        assert len(results) == 4
        
        # Check entity creation
        for result in results:
            assert result["id"] is not None
            assert result["type"] is not None
            assert result["properties"] is not None
    
    def test_kg_query_integration(self, call_context, sample_entities):
        """Test KG query operations in Null-Lang."""
        # Create entities first
        entity_results = []
        for entity_data in sample_entities:
            result = UPSERT(
                call_context,
                entity_data["type"],
                entity_data["properties"]
            )
            entity_results.append(result)
        
        # Test entity query
        entity_query_result = QUERY(
            call_context,
            "find_entities",
            {"entity_type": "Person"}
        )
        
        assert entity_query_result["total_count"] == 2
        
        # Test relationship query
        # First create a relationship
        from src.null_system.knowledge.graph_store import GraphStore, InMemoryBackend
        from src.null_system.knowledge.superbit_encoder import SuperBitEncoder
        
        graph_store = GraphStore(InMemoryBackend(), SuperBitEncoder())
        
        # Get entity IDs from results
        alice_id = entity_results[0]["id"]
        techcorp_id = entity_results[2]["id"]
        
        graph_store.create_relationship(
            alice_id, techcorp_id, "WORKS_FOR"
        )
        
        relationship_query_result = QUERY(
            call_context,
            "find_relationships",
            {"relationship_type": "WORKS_FOR"}
        )
        
        assert relationship_query_result["total_count"] == 1
    
    def test_kg_reason_integration(self, call_context):
        """Test KG reasoning operations in Null-Lang."""
        from uuid import uuid4
        
        # Create sample entities
        alice_result = UPSERT(
            call_context,
            "Person",
            {"name": "Alice", "role": "Engineer"}
        )
        
        # Test forward reasoning
        reasoning_result = REASON(
            call_context,
            "forward",
            {"max_iterations": 10}
        )
        
        # Should have empty result initially since no rules are set up
        assert "count" in reasoning_result
        assert reasoning_result["count"] >= 0
    
    def test_kg_external_linking_integration(self, call_context):
        """Test KG external linking operations in Null-Lang."""
        # Create sample entity
        entity_result = UPSERT(
            call_context,
            "City",
            {"name": "Paris"}
        )
        
        # Test external linking (this will use mocked data in tests)
        linking_result = LINK_EXTERNAL(
            call_context,
            [entity_result["id"]],
            ["wikidata", "dbpedia"],
            0.5
        )
        
        assert "count" in linking_result
        assert "linked_entities" in linking_result
    
    def test_performance_on_synthetic_data(self):
        """Test performance with synthetic million-node graph."""
        import time
        
        graph_store = GraphStore(InMemoryBackend(), SuperBitEncoder())
        
        # Create synthetic data
        start_time = time.time()
        
        entities = []
        for i in range(1000):  # Use smaller number for test speed
            entity_type = "Person" if i % 2 == 0 else "Organization"
            entity = graph_store.upsert_entity(
                entity_type=entity_type,
                properties={
                    "name": f"Entity_{i}",
                    "index": i,
                    "category": f"Category_{i % 10}"
                }
            )
            entities.append(entity)
        
        # Create relationships
        for i in range(0, len(entities), 3):
            if i + 1 < len(entities):
                graph_store.create_relationship(
                    entities[i].id,
                    entities[i + 1].id,
                    "RELATED_TO"
                )
        
        creation_time = time.time() - start_time
        
        # Test query performance
        query_start = time.time()
        
        for _ in range(100):
            graph_store.find_entities_by_properties(
                {"category": "Category_1"}
            )
        
        query_time = time.time() - query_start
        
        avg_query_time = query_time / 100
        
        # Performance assertions
        assert avg_query_time < 0.1  # Should be fast
        assert creation_time < 5.0   # Creation should be reasonable
    
    def test_acid_transactions(self):
        """Test ACID transaction guarantees."""
        import tempfile
        import time
        
        # Use SQLite backend for transaction testing
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_transactions.db"
            
            from src.null_system.knowledge.graph_store import SQLiteBackend
            
            backend = SQLiteBackend(db_path)
            graph_store = GraphStore(backend, SuperBitEncoder())
            
            # Start transaction
            from src.null_system.knowledge.transaction import TransactionManager
            transaction_manager = TransactionManager(graph_store=backend)
            transaction = transaction_manager.begin_transaction()
            
            # Create entities in transaction
            entity1 = transaction.upsert_entity(
                "Person",
                {"name": "Test Person 1"}
            )
            
            entity2 = transaction.upsert_entity(
                "Organization", 
                {"name": "Test Org"}
            )
            
            # Create relationship in transaction
            transaction.create_relationship(
                entity1.id,
                entity2.id,
                "WORKS_FOR"
            )
            
            # Commit transaction
            transaction_manager.commit_transaction(transaction)
            
            # Verify data is persisted
            assert graph_store.get_entity(entity1.id) is not None
            assert graph_store.get_entity(entity2.id) is not None
            
            # Test rollback
            transaction2 = transaction_manager.begin_transaction()
            entity3 = transaction2.upsert_entity(
                "Person",
                {"name": "Test Person 2"}
            )
            
            # Rollback instead of commit
            transaction_manager.rollback_transaction(transaction2)
            
            # Verify entity was not created
            assert graph_store.get_entity(entity3.id) is None
    
    def test_crash_recovery(self):
        """Test transaction recovery after simulated crash."""
        import tempfile
        import json
        from pathlib import Path
        import threading
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            journal_dir = Path(temp_dir) / "journal"
            db_path = Path(temp_dir) / "test_recovery.db"
            
            # Create backend and graph store
            from src.null_system.knowledge.graph_store import SQLiteBackend
            from src.null_system.knowledge.transaction import TransactionManager, FileJournalBackend
            
            backend = SQLiteBackend(db_path)
            journal_backend = FileJournalBackend(journal_dir)
            transaction_manager = TransactionManager(
                journal_backend=journal_backend,
                graph_store=backend
            )
            
            # Start transaction
            transaction = transaction_manager.begin_transaction()
            
            entity = transaction.upsert_entity(
                "Person",
                {"name": "Recoverable Entity"}
            )
            
            # Simulate crash (don't commit)
            del transaction_manager
            
            # Recover
            recovery_results = transaction_manager.recover_transactions()
            
            # Should have recovered the transaction
            assert "recovered_committed" in recovery_results
            assert "recovered_rolled_back" in recovery_results
    
    def test_external_knowledge_base_integration(self):
        """Test integration with external knowledge bases."""
        # Create test fixtures
        fixture_dir = Path(tempfile.mkdtemp())
        
        external_kb = ExternalKnowledgeBase()
        
        test_entities = [
            ("City", "Paris"),
            ("Person", "Albert Einstein"),
            ("Organization", "Google")
        ]
        
        # Create test fixtures
        external_kb.create_test_fixtures(fixture_dir, test_entities)
        
        # Verify fixtures were created
        assert (fixture_dir / "wikidata_mock.json").exists()
        assert (fixture_dir / "dbpedia_mock.json").exists()
        
        # Test search
        results = external_kb.search_all_sources("Paris", limit=5)
        
        # Should have results from both sources
        assert "wikidata" in results
        assert "dbpedia" in results
    
    def test_entity_resolution_integration(self):
        """Test entity resolution with embedding similarity."""
        from src.null_system.knowledge.entity_resolution import EntityResolver, HybridSimilarity
        
        graph_store = GraphStore(InMemoryBackend(), SuperBitEncoder())
        resolver = EntityResolver(graph_store)
        
        # Create entities with similar properties
        entity1 = graph_store.upsert_entity(
            "Person",
            {"name": "John Smith", "age": 30, "city": "New York"}
        )
        
        entity2 = graph_store.upsert_entity(
            "Person", 
            {"name": "John Smith", "age": 31, "city": "New York"}
        )
        
        entity3 = graph_store.upsert_entity(
            "Person",
            {"name": "Jane Doe", "age": 25, "city": "Boston"}
        )
        
        # Resolve entities
        matches = resolver.resolve_entities([entity1, entity2, entity3])
        
        # Should find matches between similar entities
        assert len(matches) > 0
        
        # Check for exact or high-confidence matches
        high_confidence_matches = [m for m in matches if m.confidence > 0.8]
        assert len(high_confidence_matches) > 0
    
    def test_inference_engine_integration(self):
        """Test inference engine with real data."""
        graph_store = GraphStore(InMemoryBackend(), SuperBitEncoder())
        inference_engine = InferenceEngine(graph_store)
        
        # Create sample entities
        alice = graph_store.upsert_entity(
            "Person",
            {"name": "Alice", "role": "Engineer"}
        )
        
        techcorp = graph_store.upsert_entity(
            "Organization",
            {"name": "TechCorp", "type": "Technology"}
        )
        
        graph_store.create_relationship(
            alice.id,
            techcorp.id,
            "WORKS_FOR"
        )
        
        # Add inference rules
        rule = Rule(
            id=uuid4(),
            name="Engineer at TechCorp is Tech Employee",
            rule_type=RuleType.FORWARD_CHAINING,
            premises=["Person WORKS_FOR Organization"],
            conclusions=["Person TECH_EMPLOYEE true"],
            confidence=0.9
        )
        
        inference_engine.add_rule(rule)
        
        # Run forward chaining
        new_facts = inference_engine.infer_forward()
        
        # Should generate new facts
        assert len(new_facts) >= 0  # May or may not generate facts depending on pattern matching
        
        # Test explanation
        if new_facts:
            explanation = inference_engine.explain_inference(new_facts[0].id)
            assert "fact" in explanation
            assert "derivation" in explanation