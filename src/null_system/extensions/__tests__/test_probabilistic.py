"""Tests for probabilistic extension."""

import pytest
import tempfile
from pathlib import Path
import asyncio
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from probabilistic import (
    ProbabilisticValue,
    ProbabilisticSuperBit,
    NullDecisionEngine,
    ModelConfig,
    ModelType,
    ProbabilisticEvaluator,
    ConfidenceLevel
)


class TestProbabilisticValue:
    """Test ProbabilisticValue class."""
    
    def test_creation(self):
        """Test creating probabilistic values."""
        val = ProbabilisticValue(42, confidence=0.8, uncertainty=0.2)
        assert val.value == 42
        assert val.confidence == 0.8
        assert val.uncertainty == 0.2
        
    def test_validation(self):
        """Test value validation."""
        with pytest.raises(ValueError):
            ProbabilisticValue(42, confidence=1.5)  # Invalid confidence
        
        with pytest.raises(ValueError):
            ProbabilisticValue(42, uncertainty=1.5)  # Invalid uncertainty
    
    def test_combine_weighted(self):
        """Test weighted combination."""
        val1 = ProbabilisticValue(10, confidence=0.8)
        val2 = ProbabilisticValue(20, confidence=0.6)
        
        combined = val1.combine(val2, 'weighted')
        
        # Should average the values
        assert combined.value == 15.0
        assert combined.confidence == 0.7  # Average of 0.8 and 0.6
        
    def test_combine_conservative(self):
        """Test conservative combination."""
        val1 = ProbabilisticValue(True, confidence=0.9, uncertainty=0.1)
        val2 = ProbabilisticValue(True, confidence=0.7, uncertainty=0.2)
        
        combined = val1.combine(val2, 'conservative')
        
        assert combined.value == True
        assert combined.confidence == 0.7  # Minimum confidence
        assert combined.uncertainty == 0.2  # Maximum uncertainty


class TestProbabilisticSuperBit:
    """Test ProbabilisticSuperBit class."""
    
    def test_creation(self):
        """Test creating probabilistic super bits."""
        bit = ProbabilisticSuperBit(True, 0.85, source_line=10)
        assert bit.bit_value == True
        assert bit.confidence == 0.85
        assert bit.source_line == 10
        
    def test_validation(self):
        """Test confidence validation."""
        with pytest.raises(ValueError):
            ProbabilisticSuperBit(True, 1.5)  # Invalid confidence
    
    def test_serialization(self):
        """Test dictionary conversion."""
        bit = ProbabilisticSuperBit(False, 0.7, source_line=5, metadata={'test': 'value'})
        
        data = bit.to_dict()
        assert data['bit_value'] == False
        assert data['confidence'] == 0.7
        assert data['source_line'] == 5
        assert data['metadata']['test'] == 'value'
        
        restored = ProbabilisticSuperBit.from_dict(data)
        assert restored.bit_value == bit.bit_value
        assert restored.confidence == bit.confidence


class TestNullDecisionEngine:
    """Test NullDecisionEngine class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = NullDecisionEngine()
    
    def test_initialization(self):
        """Test engine initialization."""
        assert len(self.engine.models) == 0
        assert len(self.engine.loaded_models) == 0
        assert len(self.engine.hooks) == 0
    
    def test_register_model(self):
        """Test model registration."""
        config = ModelConfig(
            model_path=Path("test.pkl"),
            model_type=ModelType.SKLEARN,
            input_features=["x", "y"],
            output_mapping={"result": 0}
        )
        
        self.engine.register_model("test_model", config)
        assert "test_model" in self.engine.models
    
    def test_load_model(self):
        """Test model loading."""
        config = ModelConfig(
            model_path=Path("test.pkl"),
            model_type=ModelType.SKLEARN,
            input_features=["x", "y"],
            output_mapping={"result": 0}
        )
        
        self.engine.register_model("test_model", config)
        
        with patch('pathlib.Path.exists', return_value=True):
            success = self.engine.load_model("test_model")
            assert success  # Should succeed in mock
        
        assert "test_model" in self.engine.loaded_models
    
    def test_heuristic_decision(self):
        """Test heuristic decision making."""
        features = {"confidence": 0.8, "value": 42, "uncertainty": 0.2}
        
        decision = self.engine._heuristic_decision(features)
        
        assert isinstance(decision, ProbabilisticValue)
        assert 0.0 <= decision.confidence <= 1.0
        assert 0.0 <= decision.uncertainty <= 1.0
    
    def test_add_decision_hook(self):
        """Test adding decision hooks."""
        def mock_hook(context, features):
            return ProbabilisticValue("hook_result", confidence=0.9)
        
        self.engine.add_decision_hook(mock_hook)
        assert len(self.engine.hooks) == 1
    
    def test_make_decision_with_hook(self):
        """Test decision making with hooks."""
        hook_called = []
        
        def mock_hook(context, features):
            hook_called.append((context, features))
            return ProbabilisticValue("hook_result", confidence=0.9)
        
        self.engine.add_decision_hook(mock_hook)
        
        result = self.engine.make_decision("test_context", {"x": 0.8})
        
        assert len(hook_called) == 1
        assert result.value == "hook_result"
        assert result.confidence == 0.9
    
    def test_make_decision_with_model(self):
        """Test decision making with AI model."""
        config = ModelConfig(
            model_path=Path("test.pkl"),
            model_type=ModelType.SKLEARN,
            input_features=["x"],
            output_mapping={"decision": 0}
        )
        
        self.engine.register_model("test_model", config)
        self.engine.loaded_models["test_model"] = {
            'type': 'sklearn',
            'path': 'test.pkl',
            'input_features': ["x"],
            'output_mapping': {"decision": 0},
            'threshold': 0.5
        }
        
        result = self.engine.make_decision("test_context", {"x": 0.8}, "test_model")
        
        assert isinstance(result, ProbabilisticValue)


class TestProbabilisticEvaluator:
    """Test ProbabilisticEvaluator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = ProbabilisticEvaluator()
    
    def test_evaluate_simple_condition(self):
        """Test simple condition evaluation."""
        variables = {"x": 5, "y": 3}
        
        result, confidence = self.evaluator._evaluate_simple_condition("x > y", variables)
        assert result == True
        assert confidence > 0.5
    
    def test_evaluate_equality(self):
        """Test equality evaluation."""
        variables = {"x": 5, "y": 5}
        
        result, confidence = self.evaluator._evaluate_simple_condition("x == y", variables)
        assert result == True
        assert confidence >= 0.9  # High confidence for equality
    
    def test_parse_value(self):
        """Test value parsing."""
        variables = {"x": 10, "y": "hello"}
        
        assert self.evaluator._parse_value("x", variables) == 10
        assert self.evaluator._parse_value("y", variables) == "hello"
        assert self.evaluator._parse_value("42", variables) == 42
        assert self.evaluator._parse_value("3.14", variables) == 3.14
    
    def test_confidence_calculation(self):
        """Test confidence calculation for comparisons."""
        # High confidence for large differences
        confidence1 = self.evaluator._calculate_comparison_confidence(10, 1, ">")
        confidence2 = self.evaluator._calculate_comparison_confidence(1.1, 1.0, ">")
        
        assert confidence1 > confidence2
    
    def test_propagate_through_expression(self):
        """Test confidence propagation through expressions."""
        inputs = {
            "x": ProbabilisticValue(10, confidence=0.8),
            "y": ProbabilisticValue(5, confidence=0.9)
        }
        
        result = self.evaluator.propagate_through_expression("x + y", inputs)
        
        assert isinstance(result, ProbabilisticValue)
        assert result.value == 15
        assert result.confidence == 0.8  # Minimum of inputs
    
    def test_evaluate_condition_with_confidence(self):
        """Test full condition evaluation with confidence."""
        variables = {
            "x": ProbabilisticValue(10, confidence=0.8),
            "y": ProbabilisticValue(5, confidence=0.9)
        }
        
        result = self.evaluator.evaluate_condition_with_confidence("x > y", variables)
        
        assert isinstance(result, ProbabilisticValue)
        assert result.value == True
        assert result.confidence > 0.5
    
    def test_evaluate_condition_with_ai(self):
        """Test condition evaluation with AI integration."""
        decision_engine = NullDecisionEngine()
        evaluator = ProbabilisticEvaluator(decision_engine)
        
        variables = {
            "x": ProbabilisticValue(10, confidence=0.8),
            "y": ProbabilisticValue(5, confidence=0.9)
        }
        
        # Mock the decision engine to return a specific result
        with patch.object(decision_engine, 'make_decision') as mock_decision:
            mock_decision.return_value = ProbabilisticValue(True, confidence=0.85)
            
            result = evaluator.evaluate_condition_with_confidence("x > y", variables, use_ai=True)
            
            assert result.value == True
            mock_decision.assert_called_once()


class TestIntegration:
    """Integration tests for probabilistic system."""
    
    def test_end_to_end_workflow(self):
        """Test complete probabilistic workflow."""
        # Create decision engine
        engine = NullDecisionEngine()
        
        # Add decision hook
        def custom_hook(context, features):
            if context == "high_confidence":
                return ProbabilisticValue(True, confidence=0.95)
            return None
        
        engine.add_decision_hook(custom_hook)
        
        # Create evaluator
        evaluator = ProbabilisticEvaluator(engine)
        
        # Test variables
        variables = {
            "score": ProbabilisticValue(85, confidence=0.9, uncertainty=0.1),
            "threshold": ProbabilisticValue(80, confidence=1.0, uncertainty=0.0)
        }
        
        # Evaluate condition
        result = evaluator.evaluate_condition_with_confidence("score > threshold", variables)
        
        assert isinstance(result, ProbabilisticValue)
        assert result.value == True
        assert result.confidence > 0.5
        
        # Test expression propagation
        expression_result = evaluator.propagate_through_expression("score - threshold", variables)
        
        assert isinstance(expression_result, ProbabilisticValue)
        assert expression_result.value == 5
        assert expression_result.confidence == min(variables["score"].confidence, variables["threshold"].confidence)
    
    def test_multiple_confidence_levels(self):
        """Test working with different confidence levels."""
        values = [
            ProbabilisticValue(True, confidence=0.9),
            ProbabilisticValue(True, confidence=0.7),
            ProbabilisticValue(False, confidence=0.8)
        ]
        
        # Test conservative combination
        combined = values[0].combine(values[1], 'conservative')
        assert combined.confidence == 0.7
        
        # Test weighted combination of numeric values
        num_values = [
            ProbabilisticValue(10, confidence=0.8),
            ProbabilisticValue(20, confidence=0.9)
        ]
        
        combined_num = num_values[0].combine(num_values[1], 'weighted')
        assert combined_num.value == 15.0
        assert 0.8 <= combined_num.confidence <= 0.9


@pytest.mark.asyncio
async def test_async_decision_engine():
    """Test async aspects of decision engine."""
    engine = NullDecisionEngine()
    
    # This tests that the engine can be used in async contexts
    # In a real implementation, this would test actual async model loading
    decisions = []
    
    def async_hook(context, features):
        # Simulate async operation
        decisions.append((context, features))
        return ProbabilisticValue("async_result", confidence=0.8)
    
    engine.add_decision_hook(async_hook)
    result = engine.make_decision("async_context", {"async": True})
    
    assert len(decisions) == 1
    assert result.value == "async_result"