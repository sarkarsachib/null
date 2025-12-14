"""Inference engine with forward and backward chaining for knowledge graphs."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4

from .graph_store import GraphStore, Entity, Relationship
from .superbit_encoder import SuperBitEncoder

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Types of inference rules."""
    FORWARD_CHAINING = "forward"
    BACKWARD_CHAINING = "backward"
    BIDIRECTIONAL = "bidirectional"


class UncertaintyType(Enum):
    """Types of uncertainty in inference."""
    PROBABILITY = "probability"
    CONFIDENCE = "confidence"
    FUZZY = "fuzzy"
    DEMPSTER_SHAFER = "dempster_shafer"


@dataclass
class Fact:
    """Represents a fact in the knowledge base."""
    id: UUID
    subject: str  # Entity ID or type
    predicate: str  # Relationship type
    object: str  # Target entity ID or value
    confidence: float = 1.0
    uncertainty_type: UncertaintyType = UncertaintyType.CONFIDENCE
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: __import__('time').time())


@dataclass
class Rule:
    """Represents an inference rule."""
    id: UUID
    name: str
    rule_type: RuleType
    premises: List[str]  # Pattern strings for matching facts
    conclusions: List[str]  # Pattern strings for conclusions
    confidence: float = 1.0
    uncertainty_propagation: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: __import__('time').time())
    
    def __post_init__(self):
        if self.id is None:
            self.id = uuid4()


class InferenceEngine:
    """Main inference engine with forward and backward chaining."""
    
    def __init__(
        self,
        graph_store: GraphStore,
        encoder: Optional[SuperBitEncoder] = None,
        max_depth: int = 10
    ):
        self.graph_store = graph_store
        self.encoder = encoder or SuperBitEncoder()
        self.max_depth = max_depth
        self.rules: Dict[UUID, Rule] = {}
        self.facts: Dict[UUID, Fact] = {}
        self.inference_history: List[Dict[str, Any]] = []
        
        logger.info("Initialized InferenceEngine")
    
    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the inference engine."""
        self.rules[rule.id] = rule
        logger.debug(f"Added rule: {rule.name}")
    
    def remove_rule(self, rule_id: UUID) -> bool:
        """Remove a rule from the inference engine."""
        if rule_id in self.rules:
            rule = self.rules.pop(rule_id)
            logger.debug(f"Removed rule: {rule.name}")
            return True
        return False
    
    def add_fact(self, fact: Fact) -> None:
        """Add a fact to the knowledge base."""
        self.facts[fact.id] = fact
        logger.debug(f"Added fact: {fact.predicate} {fact.object}")
    
    def remove_fact(self, fact_id: UUID) -> bool:
        """Remove a fact from the knowledge base."""
        if fact_id in self.facts:
            fact = self.facts.pop(fact_id)
            logger.debug(f"Removed fact: {fact.predicate} {fact.object}")
            return True
        return False
    
    def infer_forward(self, max_iterations: int = 100) -> List[Fact]:
        """Perform forward chaining inference."""
        logger.info("Starting forward chaining inference")
        
        new_facts = []
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            facts_generated = 0
            
            for rule in self.rules.values():
                if rule.rule_type in [RuleType.FORWARD_CHAINING, RuleType.BIDIRECTIONAL]:
                    rule_facts = self._apply_forward_rule(rule)
                    facts_generated += len(rule_facts)
                    new_facts.extend(rule_facts)
            
            if facts_generated == 0:
                break  # No more facts can be generated
            
            logger.debug(f"Iteration {iteration}: generated {facts_generated} facts")
        
        logger.info(f"Forward chaining completed: {len(new_facts)} new facts generated")
        return new_facts
    
    def infer_backward(self, goal: str) -> List[List[Fact]]:
        """Perform backward chaining to prove a goal."""
        logger.info(f"Starting backward chaining for goal: {goal}")
        
        proof_paths = self._prove_goal(goal, set(), 0)
        
        logger.info(f"Backward chaining completed: found {len(proof_paths)} proof paths")
        return proof_paths
    
    def _apply_forward_rule(self, rule: Rule) -> List[Fact]:
        """Apply a forward chaining rule."""
        generated_facts = []
        
        # Find matching premises in existing facts
        matching_premises = self._find_matching_premises(rule.premises)
        
        if matching_premises:
            # Generate conclusions
            for conclusion_pattern in rule.conclusions:
                fact = self._generate_fact_from_pattern(conclusion_pattern, matching_premises, rule)
                if fact:
                    # Check if fact already exists
                    if not self._fact_exists(fact):
                        generated_facts.append(fact)
                        self.facts[fact.id] = fact
        
        return generated_facts
    
    def _prove_goal(self, goal: str, visited_rules: Set[UUID], depth: int) -> List[List[Fact]]:
        """Prove a goal using backward chaining."""
        if depth > self.max_depth:
            return []
        
        proof_paths = []
        
        # Check if goal is already a fact
        goal_fact = self._find_matching_fact(goal)
        if goal_fact:
            proof_paths.append([goal_fact])
            return proof_paths
        
        # Find rules that can prove this goal
        for rule in self.rules.values():
            if rule.id in visited_rules:
                continue
            
            if rule.rule_type in [RuleType.BACKWARD_CHAINING, RuleType.BIDIRECTIONAL]:
                if self._can_rule_prove_goal(rule, goal):
                    visited_rules.add(rule.id)
                    
                    # Try to prove the premises of this rule
                    premise_proofs = []
                    for premise in rule.premises:
                        premise_paths = self._prove_goal(premise, visited_rules.copy(), depth + 1)
                        if not premise_paths:
                            break  # Cannot prove this premise
                        premise_proofs.append(premise_paths)
                    
                    if premise_proofs:
                        # Combine proofs for all premises
                        combined_proofs = self._combine_premise_proofs(premise_proofs)
                        
                        # Add the conclusion fact
                        conclusion_fact = self._generate_fact_from_pattern(goal, [], rule)
                        if conclusion_fact:
                            for proof in combined_proofs:
                                proof.append(conclusion_fact)
                                proof_paths.append(proof)
        
        return proof_paths
    
    def _find_matching_premises(self, premises: List[str]) -> List[Fact]:
        """Find facts that match rule premises."""
        matches = []
        
        for premise in premises:
            matching_fact = self._find_matching_fact(premise)
            if matching_fact:
                matches.append(matching_fact)
        
        return matches
    
    def _find_matching_fact(self, pattern: str) -> Optional[Fact]:
        """Find a fact that matches a pattern."""
        # Simple pattern matching - can be enhanced
        # Pattern format: "subject predicate object"
        
        try:
            parts = pattern.split()
            if len(parts) >= 3:
                subject_pattern, predicate_pattern = parts[0], parts[1]
                object_pattern = " ".join(parts[2:]) if len(parts) > 2 else ""
                
                for fact in self.facts.values():
                    if self._pattern_matches(fact.subject, subject_pattern) and \
                       self._pattern_matches(fact.predicate, predicate_pattern) and \
                       self._pattern_matches(fact.object, object_pattern):
                        return fact
        except:
            pass
        
        return None
    
    def _pattern_matches(self, value: str, pattern: str) -> bool:
        """Check if a value matches a pattern."""
        if pattern == "*":
            return True
        return value == pattern
    
    def _generate_fact_from_pattern(
        self,
        pattern: str,
        matching_premises: List[Fact],
        rule: Rule
    ) -> Optional[Fact]:
        """Generate a fact from a pattern using matching premises."""
        try:
            # Extract conclusion from pattern
            parts = pattern.split()
            if len(parts) >= 3:
                subject = parts[0]
                predicate = parts[1]
                object_value = " ".join(parts[2:])
                
                # Try to substitute variables from premises
                subject = self._substitute_variables(subject, matching_premises)
                object_value = self._substitute_variables(object_value, matching_premises)
                
                # Calculate confidence with uncertainty propagation
                confidence = rule.confidence
                if rule.uncertainty_propagation:
                    for premise in matching_premises:
                        confidence *= premise.confidence
                
                # Ensure confidence is in valid range
                confidence = max(0.0, min(1.0, confidence))
                
                return Fact(
                    id=uuid4(),
                    subject=subject,
                    predicate=predicate,
                    object=object_value,
                    confidence=confidence,
                    metadata={
                        "rule_id": str(rule.id),
                        "rule_name": rule.name,
                        "derived": True
                    }
                )
        except Exception as e:
            logger.error(f"Failed to generate fact from pattern '{pattern}': {e}")
        
        return None
    
    def _substitute_variables(self, text: str, premises: List[Fact]) -> str:
        """Substitute variables in text using premise facts."""
        # Simple variable substitution
        # Variables are denoted by $variable_name
        
        for i, premise in enumerate(premises):
            text = text.replace(f"$subject_{i}", premise.subject)
            text = text.replace(f"$object_{i}", premise.object)
        
        return text
    
    def _fact_exists(self, fact: Fact) -> bool:
        """Check if a fact already exists."""
        for existing_fact in self.facts.values():
            if (existing_fact.subject == fact.subject and
                existing_fact.predicate == fact.predicate and
                existing_fact.object == fact.object):
                return True
        return False
    
    def _can_rule_prove_goal(self, rule: Rule, goal: str) -> bool:
        """Check if a rule can prove a specific goal."""
        for conclusion in rule.conclusions:
            if self._pattern_matches_goal(conclusion, goal):
                return True
        return False
    
    def _pattern_matches_goal(self, conclusion: str, goal: str) -> bool:
        """Check if a conclusion pattern matches a goal."""
        goal_parts = goal.split()
        conclusion_parts = conclusion.split()
        
        if len(conclusion_parts) != len(goal_parts):
            return False
        
        for i, (conclusion_part, goal_part) in enumerate(zip(conclusion_parts, goal_parts)):
            if conclusion_part != goal_part and conclusion_part != "*":
                return False
        
        return True
    
    def _combine_premise_proofs(self, premise_proofs: List[List[List[Fact]]]) -> List[List[Fact]]:
        """Combine proofs for multiple premises."""
        if not premise_proofs:
            return []
        
        # Start with proofs from first premise
        combined = premise_proofs[0]
        
        # Combine with proofs from remaining premises
        for premise_path_proofs in premise_proofs[1:]:
            new_combined = []
            for existing_proof in combined:
                for new_proof in premise_path_proofs:
                    combined_proof = existing_proof + new_proof
                    new_combined.append(combined_proof)
            combined = new_combined
        
        return combined
    
    def explain_inference(self, fact_id: UUID) -> Dict[str, Any]:
        """Provide explanation of how a fact was inferred."""
        if fact_id not in self.facts:
            return {}
        
        fact = self.facts[fact_id]
        
        explanation = {
            "fact": {
                "id": str(fact.id),
                "subject": fact.subject,
                "predicate": fact.predicate,
                "object": fact.object,
                "confidence": fact.confidence
            },
            "derivation": fact.metadata.get("derived", False),
            "rule_name": fact.metadata.get("rule_name"),
            "rule_id": fact.metadata.get("rule_id")
        }
        
        if fact.metadata.get("derived"):
            # Find the rule that derived this fact
            rule_id = UUID(fact.metadata["rule_id"]) if fact.metadata.get("rule_id") else None
            if rule_id and rule_id in self.rules:
                rule = self.rules[rule_id]
                explanation["rule"] = {
                    "name": rule.name,
                    "premises": rule.premises,
                    "conclusions": rule.conclusions,
                    "confidence": rule.confidence
                }
        
        return explanation
    
    def get_inference_statistics(self) -> Dict[str, Any]:
        """Get statistics about inference engine state."""
        rule_types = {}
        for rule in self.rules.values():
            rule_type = rule.rule_type.value
            rule_types[rule_type] = rule_types.get(rule_type, 0) + 1
        
        uncertainty_types = {}
        for fact in self.facts.values():
            uncertainty_type = fact.uncertainty_type.value
            uncertainty_types[uncertainty_type] = uncertainty_types.get(uncertainty_type, 0) + 1
        
        return {
            "total_rules": len(self.rules),
            "rule_types": rule_types,
            "total_facts": len(self.facts),
            "uncertainty_types": uncertainty_types,
            "max_depth": self.max_depth,
            "inference_history": len(self.inference_history)
        }
    
    def clear_inference_history(self) -> None:
        """Clear inference history."""
        self.inference_history.clear()
        logger.info("Cleared inference history")
    
    def export_rules(self) -> List[Dict[str, Any]]:
        """Export all rules as dictionaries."""
        exported_rules = []
        
        for rule in self.rules.values():
            exported_rule = {
                "id": str(rule.id),
                "name": rule.name,
                "rule_type": rule.rule_type.value,
                "premises": rule.premises,
                "conclusions": rule.conclusions,
                "confidence": rule.confidence,
                "uncertainty_propagation": rule.uncertainty_propagation,
                "metadata": rule.metadata,
                "created_at": rule.created_at
            }
            exported_rules.append(exported_rule)
        
        return exported_rules
    
    def import_rules(self, rules_data: List[Dict[str, Any]]) -> None:
        """Import rules from dictionaries."""
        for rule_data in rules_data:
            rule = Rule(
                id=UUID(rule_data["id"]),
                name=rule_data["name"],
                rule_type=RuleType(rule_data["rule_type"]),
                premises=rule_data["premises"],
                conclusions=rule_data["conclusions"],
                confidence=rule_data["confidence"],
                uncertainty_propagation=rule_data["uncertainty_propagation"],
                metadata=rule_data.get("metadata", {}),
                created_at=rule_data.get("created_at", 0.0)
            )
            
            self.rules[rule.id] = rule
        
        logger.info(f"Imported {len(rules_data)} rules")
    
    def evaluate_rule_confidence(self, rule: Rule, sample_facts: List[Fact]) -> float:
        """Evaluate rule confidence based on sample facts."""
        if not sample_facts:
            return rule.confidence
        
        matching_count = 0
        total_count = len(sample_facts)
        
        for fact in sample_facts:
            # Check if fact matches rule premises
            matches = self._find_matching_premises(rule.premises)
            if matches:
                matching_count += 1
        
        # Calculate empirical confidence
        empirical_confidence = matching_count / total_count if total_count > 0 else 0.0
        
        # Combine with original rule confidence
        combined_confidence = (rule.confidence + empirical_confidence) / 2
        
        return max(0.0, min(1.0, combined_confidence))