from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable, Tuple

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence levels for probabilistic values."""
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.9


@dataclass
class ProbabilisticValue:
    """A value with associated confidence and uncertainty."""
    value: Union[int, float, bool, str]
    confidence: float = 1.0
    uncertainty: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate confidence and uncertainty values."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError(f"Uncertainty must be between 0 and 1, got {self.uncertainty}")
    
    def combine(self, other: 'ProbabilisticValue', method: str = 'weighted') -> 'ProbabilisticValue':
        """Combine two probabilistic values using specified method."""
        if method == 'weighted':
            weight_self = self.confidence
            weight_other = other.confidence
            total_weight = weight_self + weight_other
            
            if total_weight == 0:
                return ProbabilisticValue(self.value, confidence=0.0)
            
            # Weighted average for numeric values
            if isinstance(self.value, (int, float)) and isinstance(other.value, (int, float)):
                combined_value = (self.value * weight_self + other.value * weight_other) / total_weight
            else:
                # For non-numeric values, take the one with higher confidence
                combined_value = self.value if self.confidence >= other.confidence else other.value
            
            combined_confidence = min(1.0, (self.confidence + other.confidence) / 2)
            combined_uncertainty = max(self.uncertainty, other.uncertainty)
            
            return ProbabilisticValue(combined_value, combined_confidence, combined_uncertainty)
        
        elif method == 'conservative':
            # Take minimum confidence
            combined_confidence = min(self.confidence, other.confidence)
            combined_uncertainty = max(self.uncertainty, other.uncertainty)
            return ProbabilisticValue(self.value, combined_confidence, combined_uncertainty)
        
        else:
            raise ValueError(f"Unknown combination method: {method}")


@dataclass
class ProbabilisticSuperBit:
    """A super-bit with probabilistic information."""
    bit_value: bool
    confidence: float
    source_line: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate bit values."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'bit_value': self.bit_value,
            'confidence': self.confidence,
            'source_line': self.source_line,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProbabilisticSuperBit':
        """Create from dictionary."""
        return cls(
            bit_value=data['bit_value'],
            confidence=data['confidence'],
            source_line=data.get('source_line'),
            metadata=data.get('metadata', {})
        )


class ModelType(Enum):
    """Supported AI model types."""
    ONNX = "onnx"
    SKLEARN = "sklearn"
    TORCH = "torch"
    TENSORFLOW = "tensorflow"


@dataclass
class ModelConfig:
    """Configuration for AI models."""
    model_path: Path
    model_type: ModelType
    input_features: List[str]
    output_mapping: Dict[str, int]  # Maps output names to indices
    threshold: float = 0.5
    cache_size: int = 100


class NullDecisionEngine:
    """AI-driven decision engine for probabilistic execution."""
    
    def __init__(self):
        """Initialize the decision engine."""
        self.models: Dict[str, ModelConfig] = {}
        self.loaded_models: Dict[str, Any] = {}
        self.decision_cache: Dict[str, Any] = {}
        self.hooks: List[Callable] = []
    
    def register_model(self, name: str, config: ModelConfig) -> None:
        """Register an AI model for decision making."""
        self.models[name] = config
        logger.info(f"Registered model: {name} ({config.model_type.value})")
    
    def load_model(self, name: str) -> bool:
        """Load a registered model."""
        if name not in self.models:
            raise ValueError(f"Model {name} not registered")
        
        config = self.models[name]
        try:
            if config.model_type == ModelType.ONNX:
                self._load_onnx_model(name, config)
            elif config.model_type == ModelType.SKLEARN:
                self._load_sklearn_model(name, config)
            else:
                logger.warning(f"Model type {config.model_type} not yet supported")
                return False
            
            logger.info(f"Loaded model: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model {name}: {e}")
            return False
    
    def _load_onnx_model(self, name: str, config: ModelConfig) -> None:
        """Load ONNX model (placeholder implementation)."""
        # Placeholder - would use onnxruntime in real implementation
        self.loaded_models[name] = {
            'type': 'onnx',
            'path': str(config.model_path),
            'input_features': config.input_features,
            'output_mapping': config.output_mapping,
            'threshold': config.threshold
        }
        logger.info(f"ONNX model {name} loaded (placeholder)")
    
    def _load_sklearn_model(self, name: str, config: ModelConfig) -> None:
        """Load scikit-learn model (placeholder implementation)."""
        # Placeholder - would use joblib/pickle in real implementation
        self.loaded_models[name] = {
            'type': 'sklearn',
            'path': str(config.model_path),
            'input_features': config.input_features,
            'output_mapping': config.output_mapping,
            'threshold': config.threshold
        }
        logger.info(f"Sklearn model {name} loaded (placeholder)")
    
    def predict(self, model_name: str, features: Dict[str, float]) -> Tuple[Dict[str, float], float]:
        """Make prediction using a loaded model."""
        if model_name not in self.loaded_models:
            raise ValueError(f"Model {model_name} not loaded")
        
        model = self.loaded_models[model_name]
        
        # Placeholder prediction logic
        # In real implementation, this would use actual model inference
        if model['type'] == 'onnx':
            # Simulate ONNX prediction
            prediction = self._simulate_prediction(features, model['threshold'])
        elif model['type'] == 'sklearn':
            # Simulate sklearn prediction
            prediction = self._simulate_prediction(features, model['threshold'])
        else:
            raise ValueError(f"Unsupported model type: {model['type']}")
        
        return prediction, 0.85  # Simulated confidence
    
    def _simulate_prediction(self, features: Dict[str, float], threshold: float) -> Dict[str, float]:
        """Simulate model prediction for testing."""
        # Simple heuristic-based simulation
        score = sum(features.values()) / len(features) if features else 0.0
        
        # Map score to binary decision with confidence
        if score > threshold:
            return {'decision': 1.0, 'score': min(1.0, score)}
        else:
            return {'decision': 0.0, 'score': max(0.0, score)}
    
    def add_decision_hook(self, hook: Callable) -> None:
        """Add a decision hook function."""
        self.hooks.append(hook)
    
    def make_decision(self, 
                     context: str, 
                     features: Dict[str, float], 
                     model_name: Optional[str] = None) -> ProbabilisticValue:
        """Make a probabilistic decision."""
        # Call registered hooks
        for hook in self.hooks:
            try:
                hook_result = hook(context, features)
                if hook_result is not None:
                    return hook_result
            except Exception as e:
                logger.warning(f"Decision hook failed: {e}")
        
        # Use AI model if specified
        if model_name and model_name in self.loaded_models:
            predictions, confidence = self.predict(model_name, features)
            decision_value = predictions.get('decision', 0.0)
            return ProbabilisticValue(decision_value, confidence)
        
        # Fallback to heuristic
        return self._heuristic_decision(features)
    
    def _heuristic_decision(self, features: Dict[str, float]) -> ProbabilisticValue:
        """Fallback heuristic decision making."""
        if not features:
            return ProbabilisticValue(False, confidence=0.1)
        
        # Simple majority vote
        positive_count = sum(1 for v in features.values() if v > 0.5)
        total_count = len(features)
        confidence = abs(positive_count - total_count/2) / (total_count/2) if total_count > 0 else 0.0
        
        result = positive_count > total_count / 2
        return ProbabilisticValue(result, min(1.0, confidence * 2))


class ProbabilisticEvaluator:
    """Enhanced evaluator with probabilistic capabilities."""
    
    def __init__(self, decision_engine: Optional[NullDecisionEngine] = None):
        """Initialize the probabilistic evaluator."""
        self.decision_engine = decision_engine or NullDecisionEngine()
        self.confidence_threshold = 0.5
        self.uncertainty_threshold = 0.3
        
    def evaluate_condition_with_confidence(self, 
                                         condition: str, 
                                         variables: Dict[str, ProbabilisticValue],
                                         use_ai: bool = False) -> ProbabilisticValue:
        """Evaluate condition with confidence propagation."""
        # Extract values and confidences
        var_values = {}
        var_confidences = {}
        
        for name, pval in variables.items():
            var_values[name] = pval.value
            var_confidences[name] = pval.confidence
        
        # Basic condition evaluation
        if condition in ['true', 'false']:
            result = condition == 'true'
            confidence = 1.0
        else:
            # Parse simple conditions like "x > 5" or "y == z"
            result, base_confidence = self._evaluate_simple_condition(condition, var_values)
            
            # Propagate confidence if using AI
            if use_ai and self.decision_engine:
                ai_features = {name: float(val) for name, val in var_values.items() if isinstance(val, (int, float))}
                ai_decision = self.decision_engine.make_decision(condition, ai_features)
                confidence = (base_confidence + ai_decision.confidence) / 2
            else:
                confidence = base_confidence
        
        return ProbabilisticValue(result, confidence)
    
    def _evaluate_simple_condition(self, condition: str, variables: Dict[str, Any]) -> Tuple[bool, float]:
        """Evaluate a simple condition like "x > 5" or "y == z"."""
        try:
            # Simple parsing for common patterns
            if ' > ' in condition:
                left, right = condition.split(' > ', 1)
                left_val = self._parse_value(left.strip(), variables)
                right_val = self._parse_value(right.strip(), variables)
                result = left_val > right_val
                confidence = self._calculate_comparison_confidence(left_val, right_val, '>')
                return result, confidence
            
            elif ' < ' in condition:
                left, right = condition.split(' < ', 1)
                left_val = self._parse_value(left.strip(), variables)
                right_val = self._parse_value(right.strip(), variables)
                result = left_val < right_val
                confidence = self._calculate_comparison_confidence(left_val, right_val, '<')
                return result, confidence
            
            elif ' == ' in condition:
                left, right = condition.split(' == ', 1)
                left_val = self._parse_value(left.strip(), variables)
                right_val = self._parse_value(right.strip(), variables)
                result = left_val == right_val
                confidence = 0.9 if result else 0.7
                return result, confidence
            
            else:
                # Unknown condition format
                logger.warning(f"Unknown condition format: {condition}")
                return False, 0.1
                
        except Exception as e:
            logger.error(f"Error evaluating condition {condition}: {e}")
            return False, 0.1
    
    def _parse_value(self, value_str: str, variables: Dict[str, Any]) -> Any:
        """Parse a value that could be a variable name or literal."""
        value_str = value_str.strip()
        
        # Try to parse as number
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass
        
        # Try to get from variables
        if value_str in variables:
            return variables[value_str]
        
        # Fallback to string
        return value_str
    
    def _calculate_comparison_confidence(self, left: Any, right: Any, operator: str) -> float:
        """Calculate confidence for comparison operations."""
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            return 0.5
        
        # Simple confidence based on difference magnitude
        diff = abs(left - right)
        max_val = max(abs(left), abs(right), 1)
        relative_diff = diff / max_val
        
        if operator in ['>', '<']:
            return min(1.0, 0.7 + relative_diff)
        else:
            return 0.9
    
    def propagate_through_expression(self, 
                                   expression: str, 
                                   inputs: Dict[str, ProbabilisticValue]) -> ProbabilisticValue:
        """Propagate confidence through an expression."""
        # Simplified expression evaluation with confidence propagation
        # This is a placeholder for more sophisticated symbolic computation
        
        if ' + ' in expression:
            left, right = expression.split(' + ', 1)
            left_val = self._parse_probabilistic_value(left.strip(), inputs)
            right_val = self._parse_probabilistic_value(right.strip(), inputs)
            
            if isinstance(left_val.value, (int, float)) and isinstance(right_val.value, (int, float)):
                result_value = left_val.value + right_val.value
                result_confidence = min(left_val.confidence, right_val.confidence)
                return ProbabilisticValue(result_value, result_confidence)
        
        # Fallback: treat as variable lookup
        var_name = expression.strip()
        if var_name in inputs:
            return inputs[var_name]
        
        # Final fallback
        try:
            numeric_result = float(expression)
            return ProbabilisticValue(numeric_result, confidence=1.0)
        except ValueError:
            return ProbabilisticValue(expression, confidence=0.5)
    
    def _parse_probabilistic_value(self, value_str: str, inputs: Dict[str, ProbabilisticValue]) -> ProbabilisticValue:
        """Parse a probabilistic value from string."""
        value_str = value_str.strip()
        
        if value_str in inputs:
            return inputs[value_str]
        
        # Try to parse as number
        try:
            if '.' in value_str:
                return ProbabilisticValue(float(value_str), confidence=1.0)
            else:
                return ProbabilisticValue(int(value_str), confidence=1.0)
        except ValueError:
            pass
        
        # Return as string with low confidence
        return ProbabilisticValue(value_str, confidence=0.3)