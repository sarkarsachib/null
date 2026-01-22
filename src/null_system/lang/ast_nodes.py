"""
AST Node definitions for Null-Lang.

This module defines the Abstract Syntax Tree node classes for the Null-Lang
English-like programming language.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional, Union
from enum import Enum


class SourceSpan:
    """Represents a location in the source code."""
    
    def __init__(self, start_line: int, start_col: int, end_line: int, end_col: int, text: str = "", syntax_mode: Optional['SyntaxMode'] = None):
        self.start_line = start_line
        self.start_col = start_col
        self.end_line = end_line
        self.end_col = end_col
        self.text = text
        self.syntax_mode = syntax_mode
    
    def __repr__(self):
        return f"SourceSpan({self.start_line}:{self.start_col}-{self.end_line}:{self.end_col})"


class SyntaxMode(str, Enum):
    """Syntax mode for a statement or expression."""
    english = "english"
    modern = "modern"
    hybrid = "hybrid"
    auto = "auto"


class OutputMode(Enum):
    """Output modes for HybridDynamicParser."""
    AUTO = "auto"
    SEMI_AUTO = "semi_auto"
    MANUAL = "manual"


class ASTNode:
    """Base class for all AST nodes."""
    def __init__(self, span: Optional[SourceSpan] = None, syntax_mode: Optional[SyntaxMode] = None):
        self.span = span
        self.syntax_mode = syntax_mode


# Literal Nodes

@dataclass
class TextLiteral(ASTNode):
    """Represents a text/string literal."""
    value: str


@dataclass
class NumLiteral(ASTNode):
    """Represents a numeric literal (int or float)."""
    value: Union[int, float]


@dataclass
class BoolLiteral(ASTNode):
    """Represents a boolean literal (TRUE or FALSE)."""
    value: bool


# Collection Nodes

@dataclass
class ArrayLiteral(ASTNode):
    """Represents an array/list literal."""
    elements: List[ASTNode]


@dataclass
class ObjectLiteral(ASTNode):
    """Represents an object/dictionary literal."""
    pairs: List[tuple[str, ASTNode]]


# Variable and Identifier Nodes

@dataclass
class Identifier(ASTNode):
    """Represents a variable or function identifier."""
    name: str


@dataclass
class MemberAccess(ASTNode):
    """Represents member access like object.property or array[index]."""
    object: ASTNode
    member: Union[str, ASTNode]
    is_index: bool = False


# Command Nodes

@dataclass
class SetCommand(ASTNode):
    """Represents a SET command: SET variable TO value."""
    target: Union[Identifier, MemberAccess]
    value: ASTNode
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class AddCommand(ASTNode):
    """Represents an ADD command: ADD operand1 AND operand2."""
    operands: List[ASTNode]
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class IfCommand(ASTNode):
    """Represents an IF command with optional ELSE."""
    condition: ASTNode
    then_block: List[ASTNode]
    else_block: Optional[List[ASTNode]] = None
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class ShowCommand(ASTNode):
    """Represents a SHOW command to display output."""
    value: ASTNode
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class InputCommand(ASTNode):
    """Represents an INPUT command to read from stdin: INPUT variable."""
    variable: str
    prompt: Optional[ASTNode] = None
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class FileReadCommand(ASTNode):
    """Represents reading a file: SET content TO READ_FILE path."""
    path: ASTNode
    target: Optional[str] = None
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class FileWriteCommand(ASTNode):
    """Represents writing to a file: WRITE_FILE path WITH content."""
    path: ASTNode
    content: ASTNode
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class FileExistsCommand(ASTNode):
    """Represents checking if a file exists: SET exists TO FILE_EXISTS path."""
    path: ASTNode
    target: Optional[str] = None
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class ListFilesCommand(ASTNode):
    """Represents listing files in a directory: SET files TO LIST_FILES path."""
    path: ASTNode
    target: Optional[str] = None
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class RepeatCommand(ASTNode):
    """Represents a REPEAT command for loops."""
    count: ASTNode
    body: List[ASTNode]
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class DefineCommand(ASTNode):
    """Represents a DEFINE command for function definitions."""
    name: str
    parameters: List[str]
    body: List[ASTNode]
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


# Expression Nodes

class BinaryOperator(Enum):
    """Binary operators."""
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    AND = "AND"
    OR = "OR"


class UnaryOperator(Enum):
    """Unary operators."""
    NOT = "NOT"
    NEGATE = "-"


@dataclass
class BinaryExpression(ASTNode):
    """Represents a binary expression."""
    operator: BinaryOperator
    left: ASTNode
    right: ASTNode


@dataclass
class UnaryExpression(ASTNode):
    """Represents a unary expression."""
    operator: UnaryOperator
    operand: ASTNode


@dataclass
class ComparisonExpression(ASTNode):
    """Represents a comparison expression: IS, IS NOT, etc."""
    left: ASTNode
    operator: str
    right: ASTNode


# Function Call Nodes

@dataclass
class FunctionCall(ASTNode):
    """Represents a function call."""
    name: str
    arguments: List[ASTNode]


@dataclass
class NullLibAnnotation(ASTNode):
    """Represents an inline Null-Lib annotation."""
    lib_name: str
    function: str
    arguments: List[ASTNode]


# Program Node

@dataclass
class Program(ASTNode):
    """Represents a complete program (top-level AST node)."""
    module_declaration: Optional['ModuleDeclaration'] = None
    imports: List['ImportStatement'] = field(default_factory=list)
    statements: List[ASTNode] = field(default_factory=list)


# Annotation Nodes

@dataclass
class LayerAnnotation(ASTNode):
    """Represents a layer annotation: @layer(name)."""
    layer: str


@dataclass
class RequireAnnotation(ASTNode):
    """Represents a require annotation: @require(layer1, layer2, ...)."""
    layers: List[str]


@dataclass
class PreferAnnotation(ASTNode):
    """Represents a prefer annotation: @prefer(layer1, layer2, ...)."""
    layers: List[str]


# Comment Node

@dataclass
class Comment(ASTNode):
    """Represents a comment in the source code."""
    text: str


# Modern Syntax Nodes

@dataclass
class ForCommand(ASTNode):
    """Represents a for loop: for var in expr { body }."""
    variable: str
    iterable: ASTNode
    body: List[ASTNode]
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class WhileCommand(ASTNode):
    """Represents a while loop: while expr { body }."""
    condition: ASTNode
    body: List[ASTNode]
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class ReturnCommand(ASTNode):
    """Represents a return statement."""
    value: Optional[ASTNode] = None
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class BreakCommand(ASTNode):
    """Represents a break statement."""
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class ContinueCommand(ASTNode):
    """Represents a continue statement."""
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class MatchExpression(ASTNode):
    """Represents a match expression."""
    expr: ASTNode
    arms: List['MatchArm']
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class MatchArm(ASTNode):
    """Represents a match arm: pattern => body."""
    pattern: 'Pattern'
    body: List[ASTNode]


@dataclass
class Pattern(ASTNode):
    """Base class for match patterns."""
    pass


@dataclass
class WildcardPattern(Pattern):
    """Represents _ pattern."""
    pass


@dataclass
class LiteralPattern(Pattern):
    """Represents a literal pattern."""
    value: ASTNode


@dataclass
class IdentifierPattern(Pattern):
    """Represents an identifier pattern."""
    name: str


@dataclass
class BorrowCommand(ASTNode):
    """Represents a borrow/reference: &var or &mut var."""
    is_mutable: bool
    target: Identifier
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class AsyncFunction(ASTNode):
    """Represents an async function."""
    name: str
    parameters: List[str]
    body: List[ASTNode]
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class AwaitExpression(ASTNode):
    """Represents an await expression."""
    expr: ASTNode


@dataclass
class TraitDefinition(ASTNode):
    """Represents a trait definition."""
    name: str
    methods: List['TraitMethod']
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class TraitMethod(ASTNode):
    """Represents a trait method signature."""
    name: str
    parameters: List[str]
    return_type: Optional[str] = None


@dataclass
class ImplBlock(ASTNode):
    """Represents an impl block."""
    trait_name: Optional[str]
    type_name: str
    methods: List['ImplMethod']
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class ImplMethod(ASTNode):
    """Represents an impl method."""
    name: str
    parameters: List[str]
    body: List[ASTNode]


@dataclass
class PrintCommand(ASTNode):
    """Represents a print command."""
    value: ASTNode
    with_newline: bool = True
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class ClassDefinition(ASTNode):
    """Represents a class definition (Python-like)."""
    name: str
    base_classes: List[str]
    body: List[ASTNode]
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class TryStatement(ASTNode):
    """Represents a try/except block."""
    body: List[ASTNode]
    handlers: List['ExceptionHandler']
    finally_block: Optional[List[ASTNode]] = None
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class ExceptionHandler(ASTNode):
    """Represents an except clause."""
    exception_type: Optional[str]
    var_name: Optional[str]
    body: List[ASTNode]


# Module System Nodes

@dataclass
class QualifiedIdentifier(ASTNode):
    """Represents a qualified identifier like math::add or std::io::println."""
    parts: List[str]
    
    @property
    def full_name(self) -> str:
        """Return the full qualified name as a string."""
        return "::".join(self.parts)
    
    @property
    def module_path(self) -> List[str]:
        """Return the module path (all parts except the last)."""
        return self.parts[:-1] if len(self.parts) > 1 else []
    
    @property
    def name(self) -> str:
        """Return the final name component."""
        return self.parts[-1] if self.parts else ""


@dataclass
class ModuleDeclaration(ASTNode):
    """Represents a module declaration: module foo::bar."""
    name: QualifiedIdentifier


@dataclass
class ImportStatement(ASTNode):
    """Represents an import statement: import foo or import foo as bar."""
    module_name: QualifiedIdentifier
    alias: Optional[str] = None
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


# Type System Nodes - Phase 3-4

@dataclass
class TypeAnnotation(ASTNode):
    """Represents an explicit type annotation: var: Type or var: Type?."""
    type_name: str
    is_nullable: bool = False
    type_parameters: List['TypeAnnotation'] = field(default_factory=list)


@dataclass
class TypeAliasDeclaration(ASTNode):
    """Represents a type alias: type UserId = number."""
    name: str
    target_type: TypeAnnotation


@dataclass
class DataClassDeclaration(ASTNode):
    """Represents a data class: class data Point { x: number, y: number }."""
    name: str
    fields: List[tuple[str, TypeAnnotation]]
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


@dataclass
class SealedTraitDeclaration(ASTNode):
    """Represents a sealed trait: sealed trait Result<T, E> { Ok(T), Err(E) }."""
    name: str
    type_parameters: List[str]
    variants: List[tuple[str, Optional[TypeAnnotation]]]
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)


# Null-Safety Operators

@dataclass
class SafeCallExpression(ASTNode):
    """Represents a safe call: obj?.method() or obj?.property."""
    object: ASTNode
    member: Union[str, ASTNode]
    is_call: bool = False
    arguments: List[ASTNode] = field(default_factory=list)


@dataclass
class ElvisExpression(ASTNode):
    """Represents an elvis operator: value ?: default."""
    left: ASTNode
    right: ASTNode


@dataclass
class NotNullExpression(ASTNode):
    """Represents a not-null assertion: value!!."""
    value: ASTNode


@dataclass
class SmartCastExpression(ASTNode):
    """Represents a smart cast in a condition: if (x is String) { ... }."""
    value: ASTNode
    target_type: str
    body: Optional[List[ASTNode]] = None


@dataclass
class LetBindingExpression(ASTNode):
    """Represents a let binding with type: let x: number = 42."""
    name: str
    type_annotation: Optional[TypeAnnotation] = None
    value: Optional[ASTNode] = None
    annotations: List['Union[LayerAnnotation, RequireAnnotation, PreferAnnotation]'] = field(default_factory=list)
