"""Tests for null-safety operator behavior."""

import pytest
from src.null_system.analysis.type_inference import (
    TypeInference, InferredType, TypeContext, TypeKind, Nullability
)


class TestSafeCallOperator:
    """Test safe-call operator behavior."""
    
    def test_safe_access_on_nullable_type(self):
        inference = TypeInference()
        
        nullable_type = InferredType("User", TypeKind.DATA_CLASS, Nullability.NULLABLE)
        
        result = inference.narrow_type_in_condition(nullable_type, "is_not_null")
        assert result.nullable == Nullability.NON_NULLABLE
    
    def test_safe_access_chaining(self):
        inference = TypeInference()
        
        nested_type = InferredType("Address", TypeKind.DATA_CLASS, Nullability.NULLABLE)
        user_type = InferredType("User", TypeKind.DATA_CLASS, Nullability.NULLABLE)
        
        narrowed = inference.narrow_type_in_condition(user_type, "is_not_null")
        assert narrowed.nullable == Nullability.NON_NULLABLE


class TestElvisOperator:
    """Test elvis operator (?) behavior."""
    
    def test_elvis_with_null_value(self):
        inference = TypeInference()
        
        nullable = InferredType("int", TypeKind.PRIMITIVE, Nullability.NULLABLE)
        non_null = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        
        result = inference.unify_types(nullable, non_null)
        assert result.nullable == Nullability.NULLABLE
    
    def test_elvis_returns_non_null(self):
        inference = TypeInference()
        
        nullable = InferredType("int", TypeKind.PRIMITIVE, Nullability.NULLABLE)
        default_int = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        
        result = inference.unify_types(nullable, default_int)
        assert result.name == "int"


class TestNotNullAssertion:
    """Test not-null assertion operator (!)."""
    
    def test_assertion_on_nullable(self):
        inference = TypeInference()
        
        nullable = InferredType("int", TypeKind.PRIMITIVE, Nullability.NULLABLE)
        non_null = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        
        assert not inference.is_assignable(nullable, non_null)
    
    def test_assertion_converts_to_non_null(self):
        inference = TypeInference()
        
        nullable = InferredType("int", TypeKind.PRIMITIVE, Nullability.NULLABLE)
        asserted = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        
        assert inference.is_assignable(asserted, 
                                      InferredType("int", TypeKind.PRIMITIVE, 
                                                  Nullability.NON_NULLABLE))


class TestSmartCasting:
    """Test smart casting in conditional contexts."""
    
    def test_smart_cast_in_null_check(self):
        inference = TypeInference()
        
        var_type = InferredType("object", TypeKind.GENERIC, Nullability.NULLABLE)
        narrowed_type = inference.narrow_type_in_condition(var_type, "is_not_null")
        
        assert narrowed_type.nullable == Nullability.NON_NULLABLE
    
    def test_smart_cast_type_narrowing(self):
        inference = TypeInference()
        
        general_type = InferredType("Any", TypeKind.GENERIC, Nullability.NON_NULLABLE)
        
        specific_type = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        
        result = inference.unify_types(general_type, specific_type)
        assert result is None or result.name in ["Any", "int"]


class TestExhaustiveMatching:
    """Test exhaustive matching for sealed types."""
    
    def test_exhaustive_match_all_cases(self):
        from src.null_system.analysis.type_inference import SealedTraitDef
        
        inference = TypeInference()
        trait_def = SealedTraitDef("Status", subclasses={"Active", "Inactive", "Deleted"})
        inference.global_context.define_sealed_trait("Status", trait_def)
        
        status_type = InferredType("Status", TypeKind.SEALED_TRAIT)
        is_exhaustive = inference.check_exhaustive_match(
            status_type, 
            {"Active", "Inactive", "Deleted"}
        )
        assert is_exhaustive
    
    def test_exhaustive_match_missing_cases(self):
        from src.null_system.analysis.type_inference import SealedTraitDef
        
        inference = TypeInference()
        trait_def = SealedTraitDef("Status", subclasses={"Active", "Inactive", "Deleted"})
        inference.global_context.define_sealed_trait("Status", trait_def)
        
        status_type = InferredType("Status", TypeKind.SEALED_TRAIT)
        is_exhaustive = inference.check_exhaustive_match(
            status_type,
            {"Active", "Inactive"}
        )
        assert not is_exhaustive
    
    def test_get_missing_cases(self):
        from src.null_system.analysis.type_inference import SealedTraitDef
        
        inference = TypeInference()
        trait_def = SealedTraitDef("Result", subclasses={"Ok", "Error"})
        inference.global_context.define_sealed_trait("Result", trait_def)
        
        result_type = InferredType("Result", TypeKind.SEALED_TRAIT)
        subclasses = inference.get_sealed_subclasses(result_type)
        
        assert subclasses == {"Ok", "Error"}


class TestTypeNarrowing:
    """Test type narrowing in different contexts."""
    
    def test_narrow_after_null_check(self):
        inference = TypeInference()
        
        var_type = InferredType("User", TypeKind.DATA_CLASS, Nullability.NULLABLE)
        
        narrowed = inference.narrow_type_in_condition(var_type, "is_not_null")
        assert narrowed.nullable == Nullability.NON_NULLABLE
        assert narrowed.name == "User"
    
    def test_widen_after_null_assignment(self):
        inference = TypeInference()
        
        non_null = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        nullable_int = inference.create_nullable_type(non_null)
        
        assert nullable_int.nullable == Nullability.NULLABLE
        assert nullable_int.name == "int"
