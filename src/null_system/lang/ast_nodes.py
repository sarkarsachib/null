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
    
    def __init__(self, start_line: int, start_col: int, end_line: int, end_col: int, text: str = ""):
        self.start_line = start_line
        self.start_col = start_col
        self.end_line = end_line
        self.end_col = end_col
        self.text = text
    
    def __repr__(self):
        return f"SourceSpan({self.start_line}:{self.start_col}-{self.end_line}:{self.end_col})"


class ASTNode:
    """Base class for all AST nodes."""
    def __init__(self, span: Optional[SourceSpan] = None):
        self.span = span


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


@dataclass
class AddCommand(ASTNode):
    """Represents an ADD command: ADD operand1 AND operand2."""
    operands: List[ASTNode]


@dataclass
class IfCommand(ASTNode):
    """Represents an IF command with optional ELSE."""
    condition: ASTNode
    then_block: List[ASTNode]
    else_block: Optional[List[ASTNode]] = None


@dataclass
class ShowCommand(ASTNode):
    """Represents a SHOW command to display output."""
    value: ASTNode


@dataclass
class RepeatCommand(ASTNode):
    """Represents a REPEAT command for loops."""
    count: ASTNode
    body: List[ASTNode]


@dataclass
class DefineCommand(ASTNode):
    """Represents a DEFINE command for function definitions."""
    name: str
    parameters: List[str]
    body: List[ASTNode]


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
    statements: List[ASTNode]


# Comment Node

@dataclass
class Comment(ASTNode):
    """Represents a comment in the source code."""
    text: str


# Type Declaration Nodes

@dataclass
class TypeAnnotation(ASTNode):
    """Represents a type annotation."""
    type_name: str
    nullable: bool = False
    type_args: List[str] = field(default_factory=list)


@dataclass
class TypeAlias(ASTNode):
    """Represents a type alias declaration: type UserId = String"""
    name: str
    target_type: str


@dataclass
class DataClass(ASTNode):
    """Represents a data class declaration."""
    name: str
    fields: List[tuple[str, str]]
    type_params: List[str] = field(default_factory=list)


@dataclass
class SealedTrait(ASTNode):
    """Represents a sealed trait declaration."""
    name: str
    subclasses: List[str] = field(default_factory=list)
    type_params: List[str] = field(default_factory=list)


# Null-Safety Nodes

class SafeCallOperator(Enum):
    """Null-safety operators."""
    SAFE_ACCESS = "?."
    ELVIS = "?:"
    NOT_NULL = "!!"


@dataclass
class SafeAccess(ASTNode):
    """Represents safe access: obj?.property"""
    object: ASTNode
    member: Union[str, ASTNode]


@dataclass
class ElvisOperator(ASTNode):
    """Represents elvis operator: value ?: default"""
    value: ASTNode
    default: ASTNode


@dataclass
class NotNullAssertion(ASTNode):
    """Represents not-null assertion: value!!"""
    value: ASTNode


@dataclass
class SmartCast(ASTNode):
    """Represents a smart cast in a conditional context."""
    variable: str
    target_type: str


# Extended Set Command with Type Annotation

@dataclass
class SetCommandTyped(ASTNode):
    """Represents a SET command with type annotation: SET x: Int TO 5"""
    target: Union[Identifier, MemberAccess]
    type_annotation: Optional[TypeAnnotation]
    value: ASTNode


# Match/When for Sealed Classes

@dataclass
class MatchCase(ASTNode):
    """Represents a single case in a match statement."""
    pattern: str
    body: List[ASTNode]


@dataclass
class MatchStatement(ASTNode):
    """Represents a match expression for sealed types."""
    value: ASTNode
    cases: List[MatchCase]
