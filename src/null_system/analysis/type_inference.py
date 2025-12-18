"""Type inference pass for Null-Lang.

This module implements a type inference system that annotates AST nodes with:
- Inferred types
- Nullable vs non-nullable distinctions
- Generic type parameters
- Sealed/data class metadata
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union as UnionType
from enum import Enum


class PrimitiveType(Enum):
    """Primitive type names."""
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    NULL = "null"
    ARRAY = "array"
    OBJECT = "object"


@dataclass(frozen=True)
class InferredType:
    """Represents an inferred type with nullability information."""
    
    base_type: str
    is_nullable: bool = False
    type_parameters: List[InferredType] = field(default_factory=list)
    
    @property
    def full_name(self) -> str:
        if self.type_parameters:
            params = ", ".join(p.full_name for p in self.type_parameters)
            return f"{self.base_type}<{params}>"
        return self.base_type
    
    @property
    def nullable_name(self) -> str:
        name = self.full_name
        if self.is_nullable:
            return f"{name}?"
        return name
    
    def make_nullable(self) -> InferredType:
        """Return a nullable version of this type."""
        if self.is_nullable:
            return self
        return InferredType(
            base_type=self.base_type,
            is_nullable=True,
            type_parameters=self.type_parameters,
        )
    
    def make_non_nullable(self) -> InferredType:
        """Return a non-nullable version of this type."""
        if not self.is_nullable:
            return self
        return InferredType(
            base_type=self.base_type,
            is_nullable=False,
            type_parameters=self.type_parameters,
        )


@dataclass(frozen=True)
class TypeVar:
    """Represents a type variable for generics."""
    name: str
    bounds: List[str] = field(default_factory=list)


@dataclass
class NullableType:
    """Represents a nullable type."""
    inner_type: InferredType
    is_option: bool = False


@dataclass
class UnionType:
    """Represents a union type (e.g., Result, Option)."""
    variants: Dict[str, InferredType]
    
    def get_ok_type(self) -> Optional[InferredType]:
        return self.variants.get("Ok")
    
    def get_err_type(self) -> Optional[InferredType]:
        return self.variants.get("Err")
    
    def get_some_type(self) -> Optional[InferredType]:
        return self.variants.get("Some")
    
    def get_none_type(self) -> Optional[InferredType]:
        return self.variants.get("None")


@dataclass
class SealedClassInfo:
    """Information about a sealed class/trait."""
    name: str
    subtypes: List[str]
    
    def is_exhaustive(self, covered: Set[str]) -> bool:
        """Check if all subtypes are covered."""
        return all(subtype in covered for subtype in self.subtypes)


@dataclass
class DataClassInfo:
    """Information about a data class."""
    name: str
    fields: Dict[str, InferredType]
    
    def all_fields_non_nullable(self) -> bool:
        """Check if all fields are non-nullable."""
        return all(not field_type.is_nullable for field_type in self.fields.values())


@dataclass
class TypeContext:
    """Type inference context."""
    variables: Dict[str, InferredType] = field(default_factory=dict)
    type_aliases: Dict[str, InferredType] = field(default_factory=dict)
    sealed_classes: Dict[str, SealedClassInfo] = field(default_factory=dict)
    data_classes: Dict[str, DataClassInfo] = field(default_factory=dict)
    generics: Dict[str, TypeVar] = field(default_factory=dict)
    
    def clone(self) -> TypeContext:
        """Create a copy of this context."""
        return TypeContext(
            variables=self.variables.copy(),
            type_aliases=self.type_aliases.copy(),
            sealed_classes=self.sealed_classes.copy(),
            data_classes=self.data_classes.copy(),
            generics=self.generics.copy(),
        )


class TypeInference:
    """Type inference engine for Null-Lang AST."""
    
    def __init__(self):
        self.context = TypeContext()
        self.node_types: Dict[int, InferredType] = {}
        self.errors: List[str] = []
        self._init_builtins()
    
    def _init_builtins(self):
        """Initialize built-in types."""
        self.context.type_aliases["number"] = InferredType("number")
        self.context.type_aliases["string"] = InferredType("string")
        self.context.type_aliases["boolean"] = InferredType("boolean")
        self.context.type_aliases["null"] = InferredType("null", is_nullable=True)
        self.context.type_aliases["array"] = InferredType("array")
        self.context.type_aliases["object"] = InferredType("object")
    
    def infer(self, node: Any) -> InferredType:
        """Infer the type of a node."""
        method_name = f"_infer_{node.__class__.__name__}"
        method = getattr(self, method_name, self._infer_generic)
        result = method(node)
        self.node_types[id(node)] = result
        return result
    
    def _infer_generic(self, node: Any) -> InferredType:
        """Generic type inference for unknown nodes."""
        return InferredType("unknown")
    
    def _infer_Program(self, node: Any) -> InferredType:
        """Infer type of a program."""
        for stmt in node.statements:
            self.infer(stmt)
        return InferredType("null", is_nullable=True)
    
    def _infer_NumLiteral(self, node: Any) -> InferredType:
        """Number literals are numbers."""
        return InferredType("number")
    
    def _infer_TextLiteral(self, node: Any) -> InferredType:
        """Text literals are strings."""
        return InferredType("string")
    
    def _infer_BoolLiteral(self, node: Any) -> InferredType:
        """Boolean literals are booleans."""
        return InferredType("boolean")
    
    def _infer_ArrayLiteral(self, node: Any) -> InferredType:
        """Array literals are arrays."""
        if hasattr(node, 'elements') and node.elements:
            element_type = self.infer(node.elements[0])
            return InferredType("array", type_parameters=[element_type])
        return InferredType("array", type_parameters=[InferredType("unknown")])
    
    def _infer_ObjectLiteral(self, node: Any) -> InferredType:
        """Object literals are objects."""
        return InferredType("object")
    
    def _infer_Identifier(self, node: Any) -> InferredType:
        """Infer type from variable lookup."""
        if node.name in self.context.variables:
            return self.context.variables[node.name]
        if node.name in self.context.type_aliases:
            return self.context.type_aliases[node.name]
        self.errors.append(f"Undefined variable: {node.name}")
        return InferredType("unknown")
    
    def _infer_BinaryExpression(self, node: Any) -> InferredType:
        """Infer type of binary expressions."""
        left_type = self.infer(node.left)
        right_type = self.infer(node.right)
        
        from ..lang.ast_nodes import BinaryOperator
        
        if node.operator in (BinaryOperator.ADD, BinaryOperator.SUBTRACT, 
                             BinaryOperator.MULTIPLY, BinaryOperator.DIVIDE):
            return InferredType("number")
        elif node.operator in (BinaryOperator.EQUALS, BinaryOperator.NOT_EQUALS,
                               BinaryOperator.GREATER_THAN, BinaryOperator.LESS_THAN,
                               BinaryOperator.GREATER_EQUAL, BinaryOperator.LESS_EQUAL):
            return InferredType("boolean")
        elif node.operator in (BinaryOperator.AND, BinaryOperator.OR):
            return InferredType("boolean")
        
        return InferredType("unknown")
    
    def _infer_UnaryExpression(self, node: Any) -> InferredType:
        """Infer type of unary expressions."""
        operand_type = self.infer(node.operand)
        
        from ..lang.ast_nodes import UnaryOperator
        
        if node.operator == UnaryOperator.NOT:
            return InferredType("boolean")
        elif node.operator == UnaryOperator.NEGATE:
            return InferredType("number")
        
        return operand_type
    
    def _infer_ComparisonExpression(self, node: Any) -> InferredType:
        """Comparison expressions are booleans."""
        self.infer(node.left)
        self.infer(node.right)
        return InferredType("boolean")
    
    def _infer_FunctionCall(self, node: Any) -> InferredType:
        """Infer type from function call (limited without semantic info)."""
        for arg in node.arguments:
            self.infer(arg)
        return InferredType("unknown")
    
    def _infer_MemberAccess(self, node: Any) -> InferredType:
        """Infer type from member access."""
        obj_type = self.infer(node.object)
        return InferredType("unknown")
    
    def _infer_SetCommand(self, node: Any) -> InferredType:
        """Infer type from SET command."""
        value_type = self.infer(node.value)
        
        if hasattr(node.target, 'name'):
            var_name = node.target.name
            self.context.variables[var_name] = value_type
        
        return InferredType("null", is_nullable=True)
    
    def _infer_IfCommand(self, node: Any) -> InferredType:
        """Infer type from IF command."""
        self.infer(node.condition)
        
        then_type = InferredType("null", is_nullable=True)
        for stmt in node.then_block:
            then_type = self.infer(stmt)
        
        else_type = InferredType("null", is_nullable=True)
        if node.else_block:
            for stmt in node.else_block:
                else_type = self.infer(stmt)
        
        return then_type
    
    def _infer_ShowCommand(self, node: Any) -> InferredType:
        """SHOW command returns null."""
        self.infer(node.value)
        return InferredType("null", is_nullable=True)
    
    def _infer_SafeCallExpression(self, node: Any) -> InferredType:
        """Infer type from safe call (?.) expression."""
        obj_type = self.infer(node.object)
        if obj_type.is_nullable:
            inner_type = obj_type.make_non_nullable()
            return inner_type.make_nullable()
        return obj_type.make_nullable()
    
    def _infer_ElvisExpression(self, node: Any) -> InferredType:
        """Infer type from elvis (?:) expression."""
        left_type = self.infer(node.left)
        right_type = self.infer(node.right)
        
        if left_type.is_nullable and not right_type.is_nullable:
            return right_type
        
        return left_type.make_non_nullable() if left_type.is_nullable else left_type
    
    def _infer_NotNullExpression(self, node: Any) -> InferredType:
        """Infer type from not-null assertion (!!) expression."""
        inner_type = self.infer(node.value)
        return inner_type.make_non_nullable()
    
    def _infer_TypeAnnotation(self, node: Any) -> InferredType:
        """Infer type from explicit type annotation."""
        if hasattr(node, 'type_name'):
            base_type = node.type_name
            is_nullable = getattr(node, 'is_nullable', False)
            type_parameters = getattr(node, 'type_parameters', [])
            param_types = [self.infer(p) if hasattr(p, '__class__') else InferredType(str(p))
                          for p in type_parameters]
            return InferredType(base_type, is_nullable=is_nullable, type_parameters=param_types)
        return InferredType("unknown")
    
    def _infer_LetBindingExpression(self, node: Any) -> InferredType:
        """Infer type from let binding."""
        if hasattr(node, 'type_annotation') and node.type_annotation:
            return self.infer(node.type_annotation)
        if hasattr(node, 'value') and node.value:
            return self.infer(node.value)
        return InferredType("unknown")
    
    def add_type_annotation(self, var_name: str, type_info: InferredType):
        """Add a type annotation for a variable."""
        self.context.variables[var_name] = type_info
    
    def add_type_alias(self, alias_name: str, target_type: InferredType):
        """Add a type alias."""
        self.context.type_aliases[alias_name] = target_type
    
    def add_sealed_class(self, name: str, subtypes: List[str]):
        """Register a sealed class."""
        self.context.sealed_classes[name] = SealedClassInfo(name=name, subtypes=subtypes)
    
    def add_data_class(self, name: str, fields: Dict[str, InferredType]):
        """Register a data class."""
        self.context.data_classes[name] = DataClassInfo(name=name, fields=fields)
    
    def get_sealed_class_info(self, name: str) -> Optional[SealedClassInfo]:
        """Get info about a sealed class."""
        return self.context.sealed_classes.get(name)
    
    def get_data_class_info(self, name: str) -> Optional[DataClassInfo]:
        """Get info about a data class."""
        return self.context.data_classes.get(name)
    
    def is_assignable_to(self, from_type: InferredType, to_type: InferredType) -> bool:
        """Check if from_type is assignable to to_type."""
        if from_type.base_type == to_type.base_type:
            if to_type.is_nullable:
                return True
            if from_type.is_nullable:
                return False
            return True
        return False
    
    def check_exhaustive_match(self, sealed_class_name: str, covered: Set[str]) -> bool:
        """Check if a match is exhaustive for a sealed class."""
        sealed_info = self.get_sealed_class_info(sealed_class_name)
        if not sealed_info:
            return True
        return sealed_info.is_exhaustive(covered)
    
    def validate_non_null(self, expr_type: InferredType, context: str) -> bool:
        """Check if an expression's type is non-nullable."""
        if expr_type.is_nullable:
            self.errors.append(f"Expected non-nullable type in {context}, got {expr_type.nullable_name}")
            return False
        return True
    
    def clone_context(self) -> TypeContext:
        """Clone the current type context."""
        return self.context.clone()
    
    def restore_context(self, ctx: TypeContext):
        """Restore a saved type context."""
        self.context = ctx
