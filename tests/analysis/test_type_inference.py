"""Tests for type inference system."""

import pytest
from src.null_system.analysis.type_inference import (
    TypeInference, InferredType, TypeContext, TypeKind, Nullability,
    DataClassDef, SealedTraitDef, TypeParameter
)


class TestInferredType:
    """Test InferredType class."""
    
    def test_create_primitive_type(self):
        t = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        assert t.name == "int"
        assert t.kind == TypeKind.PRIMITIVE
        assert t.nullable == Nullability.NON_NULLABLE
    
    def test_nullable_type(self):
        t = InferredType("int", TypeKind.PRIMITIVE, Nullability.NULLABLE)
        assert str(t) == "int?"
    
    def test_non_nullable_type(self):
        t = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        assert str(t) == "int"
    
    def test_generic_type_with_args(self):
        int_type = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        array_type = InferredType("array", TypeKind.GENERIC, Nullability.NON_NULLABLE,
                                 type_args=[int_type])
        assert "array" in str(array_type)
    
    def test_type_equality(self):
        t1 = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        t2 = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        assert t1 == t2
    
    def test_type_inequality(self):
        t1 = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        t2 = InferredType("int", TypeKind.PRIMITIVE, Nullability.NULLABLE)
        assert t1 != t2


class TestTypeContext:
    """Test TypeContext class."""
    
    def test_define_and_lookup_variable(self):
        ctx = TypeContext()
        var_type = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        ctx.define_variable("x", var_type)
        
        result = ctx.lookup_variable("x")
        assert result == var_type
    
    def test_lookup_undefined_variable(self):
        ctx = TypeContext()
        result = ctx.lookup_variable("x")
        assert result is None
    
    def test_parent_context_lookup(self):
        parent = TypeContext()
        child = TypeContext(parent=parent)
        
        var_type = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        parent.define_variable("x", var_type)
        
        result = child.lookup_variable("x")
        assert result == var_type
    
    def test_define_and_lookup_type_alias(self):
        ctx = TypeContext()
        string_type = InferredType("string", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        ctx.define_type_alias("UserId", string_type)
        
        result = ctx.lookup_type_alias("UserId")
        assert result == string_type
    
    def test_define_and_lookup_data_class(self):
        ctx = TypeContext()
        fields = {
            "name": InferredType("string", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE),
            "age": InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE),
        }
        user_class = DataClassDef("User", fields=fields)
        ctx.define_data_class("User", user_class)
        
        result = ctx.lookup_data_class("User")
        assert result == user_class
    
    def test_define_and_lookup_sealed_trait(self):
        ctx = TypeContext()
        trait_def = SealedTraitDef("Result", subclasses={"Ok", "Error"})
        ctx.define_sealed_trait("Result", trait_def)
        
        result = ctx.lookup_sealed_trait("Result")
        assert result == trait_def


class TestTypeInference:
    """Test TypeInference class."""
    
    def test_primitive_types(self):
        inference = TypeInference()
        
        assert inference.PRIMITIVE_TYPES["int"].name == "int"
        assert inference.PRIMITIVE_TYPES["string"].name == "string"
        assert inference.PRIMITIVE_TYPES["bool"].name == "bool"
    
    def test_infer_from_literal_int(self):
        inference = TypeInference()
        
        class MockNode:
            value = 42
        
        result = inference.infer_from_literal(MockNode())
        assert result.name == "int"
        assert result.nullable == Nullability.NON_NULLABLE
    
    def test_infer_from_literal_string(self):
        inference = TypeInference()
        
        class MockNode:
            value = "hello"
        
        result = inference.infer_from_literal(MockNode())
        assert result.name == "string"
    
    def test_infer_from_literal_bool(self):
        inference = TypeInference()
        
        class MockNode:
            value = True
        
        result = inference.infer_from_literal(MockNode())
        assert result.name == "bool"
    
    def test_infer_from_literal_null(self):
        inference = TypeInference()
        
        class MockNode:
            value = None
        
        result = inference.infer_from_literal(MockNode())
        assert result.name == "null"
        assert result.nullable == Nullability.NULLABLE
    
    def test_unify_same_types(self):
        inference = TypeInference()
        
        t1 = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        t2 = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        
        result = inference.unify_types(t1, t2)
        assert result == t1
    
    def test_unify_with_null(self):
        inference = TypeInference()
        
        int_type = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        null_type = InferredType("null", TypeKind.PRIMITIVE, Nullability.NULLABLE)
        
        result = inference.unify_types(int_type, null_type)
        assert result.name == "int"
        assert result.nullable == Nullability.NULLABLE
    
    def test_unify_nullable_types(self):
        inference = TypeInference()
        
        t1 = InferredType("int", TypeKind.PRIMITIVE, Nullability.NULLABLE)
        t2 = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        
        result = inference.unify_types(t1, t2)
        assert result.nullable == Nullability.NULLABLE
    
    def test_is_assignable_same_type(self):
        inference = TypeInference()
        
        int_type = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        assert inference.is_assignable(int_type, int_type)
    
    def test_is_assignable_to_nullable(self):
        inference = TypeInference()
        
        non_null = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        nullable = InferredType("int", TypeKind.PRIMITIVE, Nullability.NULLABLE)
        
        assert inference.is_assignable(non_null, nullable)
    
    def test_is_not_assignable_null_to_non_null(self):
        inference = TypeInference()
        
        non_null = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        null_type = InferredType("null", TypeKind.PRIMITIVE, Nullability.NULLABLE)
        
        assert not inference.is_assignable(null_type, non_null)
    
    def test_create_nullable_type(self):
        inference = TypeInference()
        
        int_type = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        nullable_int = inference.create_nullable_type(int_type)
        
        assert nullable_int.name == "int"
        assert nullable_int.nullable == Nullability.NULLABLE
    
    def test_parse_type_annotation_simple(self):
        inference = TypeInference()
        
        result = inference._parse_type_annotation("int")
        assert result.name == "int"
        assert result.nullable == Nullability.NON_NULLABLE
    
    def test_parse_type_annotation_nullable(self):
        inference = TypeInference()
        
        result = inference._parse_type_annotation("string?")
        assert result.name == "string"
        assert result.nullable == Nullability.NULLABLE
    
    def test_parse_type_annotation_custom_type(self):
        inference = TypeInference()
        
        result = inference._parse_type_annotation("MyClass")
        assert result.name == "MyClass"
        assert result.kind == TypeKind.GENERIC
    
    def test_narrow_type_to_non_null(self):
        inference = TypeInference()
        
        nullable_type = InferredType("int", TypeKind.PRIMITIVE, Nullability.NULLABLE)
        
        result = inference.narrow_type_in_condition(nullable_type, "is_not_null")
        assert result.nullable == Nullability.NON_NULLABLE
    
    def test_narrow_type_to_null(self):
        inference = TypeInference()
        
        type_val = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        
        result = inference.narrow_type_in_condition(type_val, "is_null")
        assert result.nullable == Nullability.NULLABLE
    
    def test_check_exhaustive_match_true(self):
        inference = TypeInference()
        
        trait_def = SealedTraitDef("Result", subclasses={"Ok", "Error"})
        inference.global_context.define_sealed_trait("Result", trait_def)
        
        result = inference.check_exhaustive_match(
            InferredType("Result", TypeKind.SEALED_TRAIT),
            {"Ok", "Error"}
        )
        assert result is True
    
    def test_check_exhaustive_match_false(self):
        inference = TypeInference()
        
        trait_def = SealedTraitDef("Result", subclasses={"Ok", "Error"})
        inference.global_context.define_sealed_trait("Result", trait_def)
        
        result = inference.check_exhaustive_match(
            InferredType("Result", TypeKind.SEALED_TRAIT),
            {"Ok"}
        )
        assert result is False
    
    def test_get_sealed_subclasses(self):
        inference = TypeInference()
        
        trait_def = SealedTraitDef("Result", subclasses={"Ok", "Error"})
        inference.global_context.define_sealed_trait("Result", trait_def)
        
        result = inference.get_sealed_subclasses(
            InferredType("Result", TypeKind.SEALED_TRAIT)
        )
        assert result == {"Ok", "Error"}


class TestTypeParameters:
    """Test generic type parameters."""
    
    def test_create_type_parameter(self):
        param = TypeParameter("T", variance="covariant")
        assert param.name == "T"
        assert param.variance == "covariant"
    
    def test_type_with_parameters(self):
        param = TypeParameter("T")
        t = InferredType("List", TypeKind.GENERIC, Nullability.NON_NULLABLE,
                        parameters=[param])
        assert len(t.parameters) == 1
        assert t.parameters[0].name == "T"
