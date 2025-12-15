"""Type inference pass for Null-Lang AST.

Supports:
- Type annotation inference (explicit and implicit)
- Nullable vs non-nullable types
- Generics
- Data classes and sealed traits
- Smart casts and type narrowing
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Union, Any
from enum import Enum


class Nullability(Enum):
    """Nullability states for types."""
    NULLABLE = "nullable"
    NON_NULLABLE = "non_nullable"
    UNKNOWN = "unknown"


class TypeKind(Enum):
    """Kinds of types in the type system."""
    PRIMITIVE = "primitive"
    DATA_CLASS = "data_class"
    SEALED_TRAIT = "sealed_trait"
    GENERIC = "generic"
    ALIAS = "alias"
    UNION = "union"
    FUNCTION = "function"


@dataclass
class TypeParameter:
    """Generic type parameter."""
    name: str
    bounds: Optional[str] = None
    variance: str = "invariant"


@dataclass
class InferredType:
    """Represents an inferred type with nullability information."""
    name: str
    kind: TypeKind = TypeKind.PRIMITIVE
    nullable: Nullability = Nullability.UNKNOWN
    type_args: List['InferredType'] = field(default_factory=list)
    parameters: List[TypeParameter] = field(default_factory=list)
    
    def __str__(self) -> str:
        """String representation of the type."""
        base = self.name
        if self.type_args:
            args = ', '.join(str(arg) for arg in self.type_args)
            base = f"{base}[{args}]"
        suffix = "?" if self.nullable == Nullability.NULLABLE else ""
        return f"{base}{suffix}"
    
    def __hash__(self) -> int:
        return hash((self.name, self.kind, self.nullable))
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, InferredType):
            return False
        return (self.name == other.name and 
                self.kind == other.kind and 
                self.nullable == other.nullable)


@dataclass
class DataClassDef:
    """Definition of a data class."""
    name: str
    fields: Dict[str, InferredType] = field(default_factory=dict)
    type_params: List[TypeParameter] = field(default_factory=list)


@dataclass
class SealedTraitDef:
    """Definition of a sealed trait."""
    name: str
    subclasses: Set[str] = field(default_factory=set)
    type_params: List[TypeParameter] = field(default_factory=list)


class TypeContext:
    """Manages type information during inference."""
    
    def __init__(self, parent: Optional['TypeContext'] = None):
        self.parent = parent
        self.variables: Dict[str, InferredType] = {}
        self.type_aliases: Dict[str, InferredType] = {}
        self.data_classes: Dict[str, DataClassDef] = {}
        self.sealed_traits: Dict[str, SealedTraitDef] = {}
        self.function_types: Dict[str, InferredType] = {}
    
    def define_variable(self, name: str, inferred_type: InferredType) -> None:
        """Define a variable with its inferred type."""
        self.variables[name] = inferred_type
    
    def lookup_variable(self, name: str) -> Optional[InferredType]:
        """Look up a variable's type."""
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.lookup_variable(name)
        return None
    
    def define_type_alias(self, name: str, target_type: InferredType) -> None:
        """Define a type alias."""
        self.type_aliases[name] = target_type
    
    def lookup_type_alias(self, name: str) -> Optional[InferredType]:
        """Look up a type alias."""
        if name in self.type_aliases:
            return self.type_aliases[name]
        if self.parent:
            return self.parent.lookup_type_alias(name)
        return None
    
    def define_data_class(self, name: str, cls_def: DataClassDef) -> None:
        """Define a data class."""
        self.data_classes[name] = cls_def
    
    def lookup_data_class(self, name: str) -> Optional[DataClassDef]:
        """Look up a data class definition."""
        if name in self.data_classes:
            return self.data_classes[name]
        if self.parent:
            return self.parent.lookup_data_class(name)
        return None
    
    def define_sealed_trait(self, name: str, trait_def: SealedTraitDef) -> None:
        """Define a sealed trait."""
        self.sealed_traits[name] = trait_def
    
    def lookup_sealed_trait(self, name: str) -> Optional[SealedTraitDef]:
        """Look up a sealed trait definition."""
        if name in self.sealed_traits:
            return self.sealed_traits[name]
        if self.parent:
            return self.parent.lookup_sealed_trait(name)
        return None
    
    def define_function(self, name: str, func_type: InferredType) -> None:
        """Define a function type."""
        self.function_types[name] = func_type
    
    def lookup_function(self, name: str) -> Optional[InferredType]:
        """Look up a function type."""
        if name in self.function_types:
            return self.function_types[name]
        if self.parent:
            return self.parent.lookup_function(name)
        return None


class TypeInference:
    """Type inference pass for Null-Lang AST.
    
    Annotates AST nodes with inferred types and provides type information
    for validation and code generation.
    """
    
    # Built-in primitive types
    PRIMITIVE_TYPES = {
        "int": InferredType("int", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE),
        "float": InferredType("float", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE),
        "string": InferredType("string", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE),
        "bool": InferredType("bool", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE),
        "array": InferredType("array", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE),
        "object": InferredType("object", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE),
        "null": InferredType("null", TypeKind.PRIMITIVE, Nullability.NULLABLE),
    }
    
    def __init__(self, global_context: Optional[TypeContext] = None):
        self.global_context = global_context or TypeContext()
        self.current_context = self.global_context
        self.node_types: Dict[int, InferredType] = {}
        self.errors: List[str] = []
    
    def infer(self, node: Any) -> Optional[InferredType]:
        """Perform type inference on an AST node."""
        if node is None:
            return InferredType("null", TypeKind.PRIMITIVE, Nullability.NULLABLE)
        
        node_id = id(node)
        if node_id in self.node_types:
            return self.node_types[node_id]
        
        method_name = f"_infer_{node.__class__.__name__}"
        method = getattr(self, method_name, self._infer_generic)
        result = method(node)
        
        if result:
            self.node_types[node_id] = result
        return result
    
    def _infer_generic(self, node: Any) -> Optional[InferredType]:
        """Generic inference handler."""
        return None
    
    def infer_from_literal(self, node: Any) -> Optional[InferredType]:
        """Infer type from literal value."""
        if hasattr(node, 'value'):
            value = node.value
            if isinstance(value, bool):
                return self.PRIMITIVE_TYPES["bool"]
            elif isinstance(value, int):
                return self.PRIMITIVE_TYPES["int"]
            elif isinstance(value, float):
                return self.PRIMITIVE_TYPES["float"]
            elif isinstance(value, str):
                return self.PRIMITIVE_TYPES["string"]
            elif isinstance(value, list):
                return InferredType("array", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
            elif isinstance(value, dict):
                return InferredType("object", TypeKind.PRIMITIVE, Nullability.NON_NULLABLE)
            elif value is None:
                return self.PRIMITIVE_TYPES["null"]
        return None
    
    def unify_types(self, type1: InferredType, type2: InferredType) -> Optional[InferredType]:
        """Unify two types, returning the most specific common type."""
        if type1 == type2:
            return type1
        
        if type1.name == "null":
            return InferredType(type2.name, type2.kind, Nullability.NULLABLE, 
                              type2.type_args, type2.parameters)
        
        if type2.name == "null":
            return InferredType(type1.name, type1.kind, Nullability.NULLABLE, 
                              type1.type_args, type1.parameters)
        
        if type1.name == type2.name and type1.kind == type2.kind:
            nullability = (Nullability.NULLABLE if 
                          type1.nullable == Nullability.NULLABLE or 
                          type2.nullable == Nullability.NULLABLE 
                          else Nullability.NON_NULLABLE)
            return InferredType(type1.name, type1.kind, nullability,
                              type1.type_args, type1.parameters)
        
        return None
    
    def is_assignable(self, source: InferredType, target: InferredType) -> bool:
        """Check if source type is assignable to target type."""
        if source == target:
            return True
        
        if source.name == "null":
            return target.nullable == Nullability.NULLABLE
        
        if source.name == target.name and source.kind == target.kind:
            if target.nullable == Nullability.NULLABLE:
                return True
            return source.nullable != Nullability.NULLABLE
        
        return False
    
    def create_nullable_type(self, base_type: InferredType) -> InferredType:
        """Create a nullable version of a type."""
        return InferredType(base_type.name, base_type.kind, Nullability.NULLABLE,
                          base_type.type_args, base_type.parameters)
    
    def get_type_of(self, node: Any, annotation: Optional[str] = None) -> Optional[InferredType]:
        """Get the type of an AST node, optionally with explicit annotation."""
        if annotation:
            return self._parse_type_annotation(annotation)
        return self.infer(node)
    
    def _parse_type_annotation(self, annotation: str) -> Optional[InferredType]:
        """Parse a type annotation string."""
        annotation = annotation.strip()
        
        nullable = False
        if annotation.endswith("?"):
            nullable = True
            annotation = annotation[:-1]
        
        if annotation in self.PRIMITIVE_TYPES:
            base_type = self.PRIMITIVE_TYPES[annotation]
            if nullable:
                return self.create_nullable_type(base_type)
            return base_type
        
        alias = self.current_context.lookup_type_alias(annotation)
        if alias:
            if nullable:
                return self.create_nullable_type(alias)
            return alias
        
        data_class = self.current_context.lookup_data_class(annotation)
        if data_class:
            result = InferredType(annotation, TypeKind.DATA_CLASS,
                                Nullability.NULLABLE if nullable else Nullability.NON_NULLABLE)
            return result
        
        sealed_trait = self.current_context.lookup_sealed_trait(annotation)
        if sealed_trait:
            result = InferredType(annotation, TypeKind.SEALED_TRAIT,
                                Nullability.NULLABLE if nullable else Nullability.NON_NULLABLE)
            return result
        
        result = InferredType(annotation, TypeKind.GENERIC,
                            Nullability.NULLABLE if nullable else Nullability.NON_NULLABLE)
        return result
    
    def narrow_type_in_condition(self, var_type: InferredType, condition: str) -> Optional[InferredType]:
        """Narrow a type based on a condition (smart cast)."""
        if not var_type or condition not in ("is_null", "is_not_null"):
            return var_type
        
        if condition == "is_null":
            return self.create_nullable_type(var_type)
        elif condition == "is_not_null":
            return InferredType(var_type.name, var_type.kind, Nullability.NON_NULLABLE,
                              var_type.type_args, var_type.parameters)
        
        return var_type
    
    def check_exhaustive_match(self, trait_type: InferredType, 
                              covered_cases: Set[str]) -> bool:
        """Check if match statement is exhaustive for a sealed trait."""
        trait_def = self.current_context.lookup_sealed_trait(trait_type.name)
        if not trait_def:
            return False
        
        return trait_def.subclasses.issubset(covered_cases)
    
    def get_sealed_subclasses(self, trait_type: InferredType) -> Set[str]:
        """Get all subclasses of a sealed trait."""
        trait_def = self.current_context.lookup_sealed_trait(trait_type.name)
        if trait_def:
            return trait_def.subclasses
        return set()
