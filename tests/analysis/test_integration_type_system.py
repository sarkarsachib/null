"""Integration tests for type system with Null-Lang."""

import pytest
from src.null_system.analysis.type_inference import (
    TypeInference, InferredType, TypeContext, TypeKind, Nullability,
    DataClassDef, SealedTraitDef
)
from src.null_system.ast.validator import ASTValidator
from src.null_system.superbit.emitter import SuperBitEmitter
from src.null_system.superbit.ir import SuperBitOpCode


class TestTypeSystemIntegration:
    """Test type system integration with AST and validation."""
    
    def test_variable_type_tracking(self):
        """Test tracking variable types through scope."""
        ctx = TypeContext()
        inference = TypeInference(ctx)
        
        int_type = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        ctx.define_variable("x", int_type)
        
        assert ctx.lookup_variable("x") == int_type
    
    def test_type_alias_resolution(self):
        """Test type alias definition and lookup."""
        ctx = TypeContext()
        inference = TypeInference(ctx)
        
        string_type = InferredType("string", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        ctx.define_type_alias("UserId", string_type)
        
        result = ctx.lookup_type_alias("UserId")
        assert result == string_type
    
    def test_data_class_definition(self):
        """Test data class definition and field access."""
        ctx = TypeContext()
        
        fields = {
            "id": InferredType("string", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE),
            "name": InferredType("string", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE),
            "email": InferredType("string", TypeKind.PRIMITIVE, Nullability.NULLABLE),
        }
        user_class = DataClassDef("User", fields=fields)
        ctx.define_data_class("User", user_class)
        
        result = ctx.lookup_data_class("User")
        assert result == user_class
        assert "email" in result.fields
        assert result.fields["email"].nullable == Nullability.NULLABLE
    
    def test_sealed_trait_exhaustiveness(self):
        """Test exhaustive match checking for sealed traits."""
        ctx = TypeContext()
        inference = TypeInference(ctx)
        
        trait_def = SealedTraitDef("Result", subclasses={"Ok", "Error"})
        ctx.define_sealed_trait("Result", trait_def)
        
        result_type = InferredType("Result", TypeKind.SEALED_TRAIT)
        
        is_exhaustive = inference.check_exhaustive_match(result_type, {"Ok", "Error"})
        assert is_exhaustive
    
    def test_validator_with_type_inference(self):
        """Test validator consuming type inference results."""
        inferred_types = {}
        validator = ASTValidator(inferred_types)
        
        validator.set_nullable_variable("x")
        assert "x" in validator.nullable_variables
        
        validator.narrow_type("x", "is_not_null")
        assert "x" not in validator.nullable_variables
    
    def test_null_safety_enforcement(self):
        """Test null safety validation."""
        validator = ASTValidator()
        validator.set_nullable_variable("user")
        
        class MockNode:
            line = 1
        
        result = validator.check_non_null_safety("user", MockNode())
        assert not result
        assert len(validator.errors) > 0
    
    def test_safe_call_emitter(self):
        """Test emitter producing safe-call opcodes."""
        emitter = SuperBitEmitter()
        
        class MockNode:
            def __init__(self):
                self.name = "user"
                self.line = 1
        
        node = MockNode()
        
        emitter.emit_safe_access(node, "email", line=1)
        assert len(emitter.tokens) >= 1
        assert emitter.tokens[-1].opcode == SuperBitOpCode.SAFE_LOAD
    
    def test_elvis_operator_emitter(self):
        """Test emitter for elvis operator."""
        emitter = SuperBitEmitter()
        
        class MockNode:
            def __init__(self, name):
                self.name = name
                self.line = 1
        
        node1 = MockNode("x")
        node2 = MockNode("default")
        
        emitter.emit_elvis_operator(node1, node2, line=1)
        
        found_elvis = any(t.opcode == SuperBitOpCode.ELVIS_OP for t in emitter.tokens)
        assert found_elvis
    
    def test_not_null_assertion_emitter(self):
        """Test emitter for not-null assertion."""
        emitter = SuperBitEmitter()
        
        class MockNode:
            def __init__(self):
                self.name = "x"
                self.line = 1
        
        node = MockNode()
        emitter.emit_not_null_assertion(node, line=1)
        
        assert any(t.opcode == SuperBitOpCode.NOT_NULL_ASSERT for t in emitter.tokens)
    
    def test_type_check_emitter(self):
        """Test emitter for runtime type checks."""
        emitter = SuperBitEmitter()
        
        class MockNode:
            def __init__(self):
                self.name = "x"
                self.line = 1
        
        node = MockNode()
        emitter.emit_type_check(node, "User", line=1)
        
        assert any(t.opcode == SuperBitOpCode.TYPE_CHECK for t in emitter.tokens)
    
    def test_smart_cast_emitter(self):
        """Test emitter for smart casts."""
        emitter = SuperBitEmitter()
        
        emitter.emit_smart_cast("x", "Int", line=1)
        
        assert any(t.opcode == SuperBitOpCode.SMART_CAST for t in emitter.tokens)


class TestTypeNarrowingScenarios:
    """Test complex type narrowing scenarios."""
    
    def test_nested_null_checks(self):
        """Test type narrowing in nested conditions."""
        ctx = TypeContext()
        inference = TypeInference(ctx)
        
        nullable_type = InferredType("User", TypeKind.DATA_CLASS, Nullability.NULLABLE)
        narrowed_once = inference.narrow_type_in_condition(nullable_type, "is_not_null")
        assert narrowed_once.nullable == Nullability.NON_NULLABLE
        
        narrowed_again = inference.narrow_type_in_condition(narrowed_once, "is_not_null")
        assert narrowed_again.nullable == Nullability.NON_NULLABLE
    
    def test_type_widening(self):
        """Test type widening after assignment."""
        ctx = TypeContext()
        inference = TypeInference(ctx)
        
        non_null_int = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        
        nullable_or = inference.create_nullable_type(non_null_int)
        assert nullable_or.nullable == Nullability.NULLABLE
        assert nullable_or.name == "int"


class TestComprehensiveTypeScenarios:
    """Test comprehensive real-world type scenarios."""
    
    def test_optional_field_access(self):
        """Test accessing optional fields in data classes."""
        ctx = TypeContext()
        
        fields = {
            "required": InferredType("string", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE),
            "optional": InferredType("string", TypeKind.PRIMITIVE, Nullability.NULLABLE),
        }
        user_class = DataClassDef("User", fields=fields)
        ctx.define_data_class("User", user_class)
        
        user_def = ctx.lookup_data_class("User")
        required_field = user_def.fields["required"]
        optional_field = user_def.fields["optional"]
        
        assert required_field.nullable == Nullability.NON_NULLABLE
        assert optional_field.nullable == Nullability.NULLABLE
    
    def test_generic_type_instantiation(self):
        """Test instantiation of generic types."""
        ctx = TypeContext()
        
        int_type = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        array_of_int = InferredType("array", TypeKind.GENERIC, Nullability.NON_NULLABLE,
                                    type_args=[int_type])
        
        ctx.define_variable("numbers", array_of_int)
        result = ctx.lookup_variable("numbers")
        
        assert result.name == "array"
        assert len(result.type_args) == 1
        assert result.type_args[0].name == "int"
    
    def test_union_type_handling(self):
        """Test handling of union types."""
        inference = TypeInference()
        
        int_type = InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        string_type = InferredType("string", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
        
        result = inference.unify_types(int_type, string_type)
        assert result is None
