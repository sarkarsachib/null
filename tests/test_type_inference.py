"""Tests for type inference system."""

import pytest
from src.null_system.analysis.type_inference import (
    TypeInference,
    InferredType,
    TypeVar,
    SealedClassInfo,
    DataClassInfo,
)
from src.null_system.lang.parser import NullLangParser
from src.null_system.lang.ast_nodes import (
    NumLiteral,
    TextLiteral,
    BoolLiteral,
    ArrayLiteral,
    Identifier,
    BinaryExpression,
    BinaryOperator,
)


class TestTypeInference:
    """Tests for type inference."""
    
    def test_infer_number_literal(self):
        inference = TypeInference()
        node = NumLiteral(value=42)
        result = inference.infer(node)
        
        assert result.base_type == "number"
        assert not result.is_nullable
    
    def test_infer_string_literal(self):
        inference = TypeInference()
        node = TextLiteral(value="hello")
        result = inference.infer(node)
        
        assert result.base_type == "string"
        assert not result.is_nullable
    
    def test_infer_boolean_literal(self):
        inference = TypeInference()
        node = BoolLiteral(value=True)
        result = inference.infer(node)
        
        assert result.base_type == "boolean"
        assert not result.is_nullable
    
    def test_infer_array_literal(self):
        inference = TypeInference()
        node = ArrayLiteral(elements=[NumLiteral(value=1), NumLiteral(value=2)])
        result = inference.infer(node)
        
        assert result.base_type == "array"
        assert len(result.type_parameters) > 0
    
    def test_infer_binary_addition(self):
        inference = TypeInference()
        left = NumLiteral(value=1)
        right = NumLiteral(value=2)
        node = BinaryExpression(operator=BinaryOperator.ADD, left=left, right=right)
        result = inference.infer(node)
        
        assert result.base_type == "number"
    
    def test_infer_binary_comparison(self):
        inference = TypeInference()
        left = NumLiteral(value=1)
        right = NumLiteral(value=2)
        node = BinaryExpression(operator=BinaryOperator.GREATER_THAN, left=left, right=right)
        result = inference.infer(node)
        
        assert result.base_type == "boolean"
    
    def test_inferred_type_nullable(self):
        type_info = InferredType("string", is_nullable=True)
        assert type_info.is_nullable
        assert type_info.nullable_name == "string?"
    
    def test_inferred_type_non_nullable(self):
        type_info = InferredType("number", is_nullable=False)
        assert not type_info.is_nullable
        assert type_info.nullable_name == "number"
    
    def test_make_type_nullable(self):
        type_info = InferredType("string", is_nullable=False)
        nullable = type_info.make_nullable()
        
        assert nullable.is_nullable
        assert nullable.base_type == "string"
    
    def test_make_type_non_nullable(self):
        type_info = InferredType("string", is_nullable=True)
        non_nullable = type_info.make_non_nullable()
        
        assert not non_nullable.is_nullable
        assert non_nullable.base_type == "string"
    
    def test_inferred_type_with_generics(self):
        elem_type = InferredType("number")
        array_type = InferredType("array", type_parameters=[elem_type])
        
        assert len(array_type.type_parameters) == 1
        assert array_type.full_name == "array<number>"
    
    def test_type_var_bounds(self):
        type_var = TypeVar(name="T", bounds=["Comparable"])
        
        assert type_var.name == "T"
        assert "Comparable" in type_var.bounds
    
    def test_sealed_class_info(self):
        sealed_info = SealedClassInfo(
            name="Result",
            subtypes=["Ok", "Err"]
        )
        
        assert sealed_info.name == "Result"
        assert len(sealed_info.subtypes) == 2
    
    def test_sealed_class_exhaustive_check(self):
        sealed_info = SealedClassInfo(
            name="Result",
            subtypes=["Ok", "Err"]
        )
        
        covered = {"Ok", "Err"}
        assert sealed_info.is_exhaustive(covered)
        
        covered = {"Ok"}
        assert not sealed_info.is_exhaustive(covered)
    
    def test_data_class_info(self):
        fields = {
            "x": InferredType("number"),
            "y": InferredType("number"),
        }
        data_info = DataClassInfo(name="Point", fields=fields)
        
        assert data_info.name == "Point"
        assert len(data_info.fields) == 2
    
    def test_data_class_all_non_nullable(self):
        fields = {
            "x": InferredType("number", is_nullable=False),
            "y": InferredType("number", is_nullable=False),
        }
        data_info = DataClassInfo(name="Point", fields=fields)
        
        assert data_info.all_fields_non_nullable()
    
    def test_data_class_has_nullable_field(self):
        fields = {
            "x": InferredType("number", is_nullable=False),
            "y": InferredType("number", is_nullable=True),
        }
        data_info = DataClassInfo(name="Point", fields=fields)
        
        assert not data_info.all_fields_non_nullable()
    
    def test_add_type_annotation(self):
        inference = TypeInference()
        type_info = InferredType("number", is_nullable=False)
        
        inference.add_type_annotation("x", type_info)
        
        assert "x" in inference.context.variables
        assert inference.context.variables["x"] == type_info
    
    def test_add_sealed_class(self):
        inference = TypeInference()
        
        inference.add_sealed_class("Option", ["Some", "None"])
        
        assert "Option" in inference.context.sealed_classes
        sealed_info = inference.get_sealed_class_info("Option")
        assert sealed_info is not None
        assert sealed_info.subtypes == ["Some", "None"]
    
    def test_add_data_class(self):
        inference = TypeInference()
        fields = {
            "name": InferredType("string"),
            "age": InferredType("number"),
        }
        
        inference.add_data_class("Person", fields)
        
        assert "Person" in inference.context.data_classes
        data_info = inference.get_data_class_info("Person")
        assert data_info is not None
        assert len(data_info.fields) == 2
    
    def test_is_assignable_to(self):
        inference = TypeInference()
        
        from_type = InferredType("number", is_nullable=False)
        to_type = InferredType("number", is_nullable=False)
        
        assert inference.is_assignable_to(from_type, to_type)
    
    def test_is_assignable_to_nullable(self):
        inference = TypeInference()
        
        from_type = InferredType("number", is_nullable=False)
        to_type = InferredType("number", is_nullable=True)
        
        assert inference.is_assignable_to(from_type, to_type)
    
    def test_is_not_assignable_to_non_nullable(self):
        inference = TypeInference()
        
        from_type = InferredType("number", is_nullable=True)
        to_type = InferredType("number", is_nullable=False)
        
        assert not inference.is_assignable_to(from_type, to_type)
    
    def test_check_exhaustive_match(self):
        inference = TypeInference()
        inference.add_sealed_class("Result", ["Ok", "Err"])
        
        covered = {"Ok", "Err"}
        assert inference.check_exhaustive_match("Result", covered)
        
        covered = {"Ok"}
        assert not inference.check_exhaustive_match("Result", covered)
    
    def test_validate_non_null(self):
        inference = TypeInference()
        
        non_null_type = InferredType("number", is_nullable=False)
        assert inference.validate_non_null(non_null_type, "assignment")
        
        nullable_type = InferredType("number", is_nullable=True)
        assert not inference.validate_non_null(nullable_type, "assignment")
    
    def test_clone_context(self):
        inference = TypeInference()
        inference.add_type_annotation("x", InferredType("number"))
        
        cloned = inference.clone_context()
        
        assert "x" in cloned.variables
        assert cloned.variables["x"].base_type == "number"
    
    def test_restore_context(self):
        inference = TypeInference()
        inference.add_type_annotation("x", InferredType("number"))
        
        saved = inference.clone_context()
        inference.add_type_annotation("y", InferredType("string"))
        
        assert "y" in inference.context.variables
        
        inference.restore_context(saved)
        
        assert "y" not in inference.context.variables
        assert "x" in inference.context.variables


class TestTypeInferenceWithParser:
    """Integration tests with parser."""
    
    def test_infer_from_parsed_program(self):
        parser = NullLangParser()
        source = """
        SET x TO 42
        """
        program = parser.parse(source)
        
        inference = TypeInference()
        inference.infer(program)
        
        assert "x" in inference.context.variables or len(inference.errors) == 0
    
    def test_infer_let_binding_type(self):
        inference = TypeInference()
        
        from src.null_system.lang.ast_nodes import LetBindingExpression, TypeAnnotation
        
        type_ann = TypeAnnotation(type_name="number", is_nullable=False)
        node = LetBindingExpression(
            name="x",
            type_annotation=type_ann,
            value=NumLiteral(value=42)
        )
        
        result = inference.infer(node)
        assert result.base_type in ("null", "number")
