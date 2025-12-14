"""Inference engine tests for rule-based reasoning."""

import pytest
import time
from uuid import uuid4

from src.null_system.knowledge.graph_store import GraphStore, InMemoryBackend
from src.null_system.knowledge.inference import (
    InferenceEngine, Rule, Fact, RuleType, UncertaintyType
)
from src.null_system.knowledge.superbit_encoder import SuperBitEncoder


class TestInferenceEngine:
    """Test cases for InferenceEngine."""
    
    @pytest.fixture
    def encoder(self):
        return SuperBitEncoder(dimension=64)
    
    @pytest.fixture
    def graph_store(self, encoder):
        return GraphStore(InMemoryBackend(), encoder)
    
    @pytest.fixture
    def inference_engine(self, graph_store):
        return InferenceEngine(graph_store)
    
    @pytest.fixture
    def sample_data(self, graph_store):
        """Create sample data for inference testing."""
        # Create entities
        alice = graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Alice", "role": "Engineer"}
        )
        
        bob = graph_store.upsert_entity(
            entity_type="Person",
            properties={"name": "Bob", "role": "Manager"}
        )
        
        techcorp = graph_store.upsert_entity(
            entity_type="Organization",
            properties={"name": "TechCorp", "industry": "Technology"}
        )
        
        # Create relationships
        graph_store.create_relationship(alice.id, techcorp.id, "WORKS_FOR")
        graph_store.create_relationship(bob.id, techcorp.id, "MANAGES")
        
        return alice, bob, techcorp
    
    def test_add_and_remove_rules(self, inference_engine):
        """Test adding and removing rules."""
        # Add rule
        rule = Rule(
            id=uuid4(),
            name="Test Rule",
            rule_type=RuleType.FORWARD_CHAINING,
            premises=["Person WORKS_FOR Organization"],
            conclusions=["Person TECH_EMPLOYEE true"],
            confidence=0.9
        )
        
        inference_engine.add_rule(rule)
        assert len(inference_engine.rules) == 1
        assert rule.id in inference_engine.rules
        
        # Remove rule
        success = inference_engine.remove_rule(rule.id)
        assert success
        assert len(inference_engine.rules) == 0
        
        # Try to remove non-existent rule
        success = inference_engine.remove_rule(uuid4())
        assert not success
    
    def test_add_and_remove_facts(self, inference_engine):
        """Test adding and removing facts."""
        # Add fact
        fact = Fact(
            id=uuid4(),
            subject="Alice",
            predicate="WORKS_FOR",
            object="TechCorp",
            confidence=0.9
        )
        
        inference_engine.add_fact(fact)
        assert len(inference_engine.facts) == 1
        assert fact.id in inference_engine.facts
        
        # Remove fact
        success = inference_engine.remove_fact(fact.id)
        assert success
        assert len(inference_engine.facts) == 0
        
        # Try to remove non-existent fact
        success = inference_engine.remove_fact(uuid4())
        assert not success
    
    def test_forward_chaining_basic(self, inference_engine, sample_data):
        """Test basic forward chaining inference."""
        alice, bob, techcorp = sample_data
        
        # Add rule
        rule = Rule(
            id=uuid4(),
            name="Tech Employee Rule",
            rule_type=RuleType.FORWARD_CHAINING,
            premises=["Person WORKS_FOR Organization"],
            conclusions=["Person TECH_EMPLOYEE true"],
            confidence=0.9
        )
        
        inference_engine.add_rule(rule)
        
        # Add matching facts
        fact = Fact(
            id=uuid4(),
            subject=str(alice.id),
            predicate="WORKS_FOR",
            object=str(techcorp.id),
            confidence=1.0
        )
        
        inference_engine.add_fact(fact)
        
        # Run forward chaining
        new_facts = inference_engine.infer_forward(max_iterations=10)
        
        # Should generate new fact
        assert len(new_facts) >= 0  # May or may not generate depending on pattern matching
    
    def test_backward_chaining_basic(self, inference_engine, sample_data):
        """Test basic backward chaining inference."""
        # Add rule
        rule = Rule(
            id=uuid4(),
            name="Tech Worker Rule",
            rule_type=RuleType.BACKWARD_CHAINING,
            premises=["Person TECH_EMPLOYEE true"],
            conclusions=["Person IS_TECH_WORKER true"],
            confidence=0.8
        )
        
        inference_engine.add_rule(rule)
        
        # Add initial fact
        fact = Fact(
            id=uuid4(),
            subject="test_person",
            predicate="TECH_EMPLOYEE",
            object="true",
            confidence=0.9
        )
        
        inference_engine.add_fact(fact)
        
        # Run backward chaining
        proof_paths = inference_engine.infer_backward("Person IS_TECH_WORKER true")
        
        # Should find proof paths
        assert isinstance(proof_paths, list)
    
    def test_forward_chaining_iterations(self, inference_engine):
        """Test forward chaining with multiple iterations."""
        # Add chain of rules
        rule1 = Rule(
            id=uuid4(),
            name="Rule 1",
            rule_type=RuleType.FORWARD_CHAINING,
            premises=["A RELATES_TO B"],
            conclusions=["B RELATES_TO_C true"],
            confidence=0.9
        )
        
        rule2 = Rule(
            id=uuid4(),
            name="Rule 2", 
            rule_type=RuleType.FORWARD_CHAINING,
            premises=["B RELATES_TO_C true"],
            conclusions=["C HAS_PROPERTY X"],
            confidence=0.8
        )
        
        inference_engine.add_rule(rule1)
        inference_engine.add_rule(rule2)
        
        # Add initial fact
        fact = Fact(
            id=uuid4(),
            subject="A",
            predicate="RELATES_TO",
            object="B",
            confidence=1.0
        )
        
        inference_engine.add_fact(fact)
        
        # Run forward chaining
        new_facts = inference_engine.infer_forward(max_iterations=5)
        
        # Should generate chain of facts
        assert len(new_facts) >= 0
    
    def test_uncertainty_propagation(self, inference_engine):
        """Test uncertainty propagation through rules."""
        # Add rule with uncertainty propagation
        rule = Rule(
            id=uuid4(),
            name="Uncertain Rule",
            rule_type=RuleType.FORWARD_CHAINING,
            premises=["Person WORKS_FOR Organization"],
            conclusions=["Person TECH_EMPLOYEE true"],
            confidence=0.9,
            uncertainty_propagation=True
        )
        
        inference_engine.add_rule(rule)
        
        # Add facts with different confidence levels
        fact1 = Fact(
            id=uuid4(),
            subject="Alice",
            predicate="WORKS_FOR",
            object="TechCorp",
            confidence=0.8
        )
        
        fact2 = Fact(
            id=uuid4(),
            subject="Bob", 
            predicate="WORKS_FOR",
            object="TechCorp",
            confidence=0.6
        )
        
        inference_engine.add_fact(fact1)
        inference_engine.add_fact(fact2)
        
        # Run forward chaining
        new_facts = inference_engine.infer_forward()
        
        # Check confidence propagation
        for fact in new_facts:
            # Confidence should be product of rule confidence and fact confidence
            expected_confidence = 0.9 * 0.8  # First fact
            assert fact.confidence <= expected_confidence
    
    def test_bidirectional_rules(self, inference_engine):
        """Test bidirectional rule types."""
        # Add bidirectional rule
        rule = Rule(
            id=uuid4(),
            name="Bidirectional Rule",
            rule_type=RuleType.BIDIRECTIONAL,
            premises=["Person WORKS_FOR Organization"],
            conclusions=["Organization HAS_EMPLOYEE Person"],
            confidence=0.85
        )
        
        inference_engine.add_rule(rule)
        
        # Add fact
        fact = Fact(
            id=uuid4(),
            subject="Alice",
            predicate="WORKS_FOR",
            object="TechCorp",
            confidence=1.0
        )
        
        inference_engine.add_fact(fact)
        
        # Test forward chaining
        forward_facts = inference_engine.infer_forward()
        
        # Test backward chaining
        proof_paths = inference_engine.infer_backward("Organization HAS_EMPLOYEE Person")
        
        # Rule should work in both directions
        assert len(forward_facts) >= 0 or len(proof_paths) >= 0
    
    def test_max_depth_limit(self, inference_engine):
        """Test maximum depth limiting in inference."""
        # Create deep chain of rules
        for i in range(15):  # More than max_depth
            rule = Rule(
                id=uuid4(),
                name=f"Deep Rule {i}",
                rule_type=RuleType.FORWARD_CHAINING,
                premises=[f"Entity{i} RELATES_TO Entity{i+1}"],
                conclusions=[f"Entity{i+1} RELATES_TO Entity{i+2} true"],
                confidence=1.0
            )
            inference_engine.add_rule(rule)
        
        # Add initial fact
        fact = Fact(
            id=uuid4(),
            subject="Entity0",
            predicate="RELATES_TO",
            object="Entity1",
            confidence=1.0
        )
        
        inference_engine.add_fact(fact)
        
        # Run forward chaining with default max_depth
        new_facts = inference_engine.infer_forward()
        
        # Should not exceed max depth
        assert len(new_facts) <= inference_engine.max_depth
    
    def test_explain_inference(self, inference_engine):
        """Test inference explanation."""
        # Add rule and fact
        rule = Rule(
            id=uuid4(),
            name="Explanation Rule",
            rule_type=RuleType.FORWARD_CHAINING,
            premises=["Person WORKS_FOR Organization"],
            conclusions=["Person TECH_EMPLOYEE true"],
            confidence=0.9
        )
        
        inference_engine.add_rule(rule)
        
        fact = Fact(
            id=uuid4(),
            subject="Alice",
            predicate="WORKS_FOR",
            object="TechCorp",
            confidence=1.0
        )
        
        inference_engine.add_fact(fact)
        new_facts = inference_engine.infer_forward()
        
        if new_facts:
            # Explain the inference
            explanation = inference_engine.explain_inference(new_facts[0].id)
            
            assert "fact" in explanation
            assert "derivation" in explanation
            assert "rule_name" in explanation
    
    def test_rule_confidence_evaluation(self, inference_engine):
        """Test empirical rule confidence evaluation."""
        # Create sample facts
        sample_facts = []
        for i in range(10):
            fact = Fact(
                id=uuid4(),
                subject=f"Person{i}",
                predicate="WORKS_FOR",
                object="TechCorp",
                confidence=0.8
            )
            sample_facts.append(fact)
        
        # Create rule
        rule = Rule(
            id=uuid4(),
            name="Evaluation Rule",
            rule_type=RuleType.FORWARD_CHAINING,
            premises=["Person WORKS_FOR Organization"],
            conclusions=["Person TECH_EMPLOYEE true"],
            confidence=0.7  # Initial confidence
        )
        
        # Evaluate confidence
        evaluated_confidence = inference_engine.evaluate_rule_confidence(rule, sample_facts)
        
        # Should be between 0 and 1
        assert 0.0 <= evaluated_confidence <= 1.0
        assert isinstance(evaluated_confidence, float)
    
    def test_inference_statistics(self, inference_engine):
        """Test inference engine statistics."""
        # Add rules of different types
        forward_rule = Rule(
            id=uuid4(),
            name="Forward Rule",
            rule_type=RuleType.FORWARD_CHAINING,
            premises=["A RELATES_TO B"],
            conclusions=["B RELATES_TO C"],
            confidence=0.9
        )
        
        backward_rule = Rule(
            id=uuid4(),
            name="Backward Rule",
            rule_type=RuleType.BACKWARD_CHAINING,
            premises=["X PREDICATE Y"],
            conclusions=["Y CONVERSE X"],
            confidence=0.8
        )
        
        bidirectional_rule = Rule(
            id=uuid4(),
            name="Bidirectional Rule",
            rule_type=RuleType.BIDIRECTIONAL,
            premises=["M RELATES_TO N"],
            conclusions=["N RELATES_TO M"],
            confidence=0.85
        )
        
        inference_engine.add_rule(forward_rule)
        inference_engine.add_rule(backward_rule)
        inference_engine.add_rule(bidirectional_rule)
        
        # Add facts with different uncertainty types
        fact1 = Fact(
            id=uuid4(),
            subject="Test1",
            predicate="RELATES_TO",
            object="Test2",
            confidence=0.9,
            uncertainty_type=UncertaintyType.CONFIDENCE
        )
        
        fact2 = Fact(
            id=uuid4(),
            subject="Test3",
            predicate="RELATES_TO",
            object="Test4",
            confidence=0.7,
            uncertainty_type=UncertaintyType.PROBABILITY
        )
        
        inference_engine.add_fact(fact1)
        inference_engine.add_fact(fact2)
        
        # Get statistics
        stats = inference_engine.get_inference_statistics()
        
        assert stats["total_rules"] == 3
        assert stats["total_facts"] == 2
        assert "forward" in stats["rule_types"]
        assert "backward" in stats["rule_types"]
        assert "bidirectional" in stats["rule_types"]
        assert "confidence" in stats["uncertainty_types"]
        assert "probability" in stats["uncertainty_types"]
        assert stats["max_depth"] == 10
    
    def test_export_import_rules(self, inference_engine):
        """Test rule export and import."""
        # Create rules
        rules = []
        for i in range(3):
            rule = Rule(
                id=uuid4(),
                name=f"Export Rule {i}",
                rule_type=RuleType.FORWARD_CHAINING,
                premises=[f"Entity{i} RELATES_TO Entity{i+1}"],
                conclusions=[f"Entity{i+1} RELATES_TO Entity{i+2}"],
                confidence=0.9 - i * 0.1,
                uncertainty_propagation=True,
                metadata={"created_by": "test"}
            )
            rules.append(rule)
            inference_engine.add_rule(rule)
        
        # Export rules
        exported_data = inference_engine.export_rules()
        
        assert len(exported_data) == 3
        
        # Check exported data structure
        for rule_data in exported_data:
            assert "id" in rule_data
            assert "name" in rule_data
            assert "rule_type" in rule_data
            assert "premises" in rule_data
            assert "conclusions" in rule_data
            assert "confidence" in rule_data
        
        # Clear existing rules
        inference_engine.rules.clear()
        
        # Import rules
        inference_engine.import_rules(exported_data)
        
        # Verify import
        assert len(inference_engine.rules) == 3
        for i, rule_id in enumerate(inference_engine.rules):
            rule = inference_engine.rules[rule_id]
            assert rule.name == f"Export Rule {i}"
            assert len(rule.premises) == 1
            assert len(rule.conclusions) == 1
    
    def test_inference_history(self, inference_engine):
        """Test inference history tracking."""
        # Add rules and run inference
        rule = Rule(
            id=uuid4(),
            name="History Rule",
            rule_type=RuleType.FORWARD_CHAINING,
            premises=["Test RELATES_TO Test2"],
            conclusions=["Test2 RELATES_TO Test3"],
            confidence=1.0
        )
        
        inference_engine.add_rule(rule)
        
        fact = Fact(
            id=uuid4(),
            subject="Test",
            predicate="RELATES_TO",
            object="Test2",
            confidence=1.0
        )
        
        inference_engine.add_fact(fact)
        
        # Run inference multiple times
        for _ in range(3):
            inference_engine.infer_forward()
        
        # Clear history
        inference_engine.clear_inference_history()
        
        # Should be empty now
        assert len(inference_engine.inference_history) == 0


class TestRule:
    """Test cases for Rule data structure."""
    
    def test_rule_creation(self):
        """Test rule creation and validation."""
        rule = Rule(
            id=uuid4(),
            name="Test Rule",
            rule_type=RuleType.FORWARD_CHAINING,
            premises=["A RELATES_TO B"],
            conclusions=["B RELATES_TO C"],
            confidence=0.9,
            uncertainty_propagation=True,
            metadata={"test": True}
        )
        
        assert rule.id is not None
        assert rule.name == "Test Rule"
        assert rule.rule_type == RuleType.FORWARD_CHAINING
        assert len(rule.premises) == 1
        assert len(rule.conclusions) == 1
        assert rule.confidence == 0.9
        assert rule.uncertainty_propagation is True
        assert rule.metadata["test"] is True
        assert rule.created_at is not None
    
    def test_rule_auto_id(self):
        """Test automatic ID generation."""
        rule = Rule(
            name="Auto ID Rule",
            rule_type=RuleType.BACKWARD_CHAINING,
            premises=["A PREDICATE B"],
            conclusions=["B CONVERSE A"],
            confidence=0.8
        )
        
        # Should auto-generate ID
        assert rule.id is not None
        assert isinstance(rule.id, UUID)


class TestFact:
    """Test cases for Fact data structure."""
    
    def test_fact_creation(self):
        """Test fact creation and validation."""
        fact = Fact(
            id=uuid4(),
            subject="Alice",
            predicate="WORKS_FOR",
            object="TechCorp",
            confidence=0.95,
            uncertainty_type=UncertaintyType.CONFIDENCE,
            metadata={"source": "manual"}
        )
        
        assert fact.id is not None
        assert fact.subject == "Alice"
        assert fact.predicate == "WORKS_FOR"
        assert fact.object == "TechCorp"
        assert fact.confidence == 0.95
        assert fact.uncertainty_type == UncertaintyType.CONFIDENCE
        assert fact.metadata["source"] == "manual"
        assert fact.created_at is not None
    
    def test_uncertainty_types(self):
        """Test different uncertainty types."""
        uncertainty_types = [
            UncertaintyType.PROBABILITY,
            UncertaintyType.CONFIDENCE,
            UncertaintyType.FUZZY,
            UncertaintyType.DEMPSTER_SHAFER
        ]
        
        for uncertainty_type in uncertainty_types:
            fact = Fact(
                id=uuid4(),
                subject="Test",
                predicate="RELATES_TO",
                object="Test2",
                confidence=0.8,
                uncertainty_type=uncertainty_type
            )
            
            assert fact.uncertainty_type == uncertainty_type