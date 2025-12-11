"""AST node definitions."""

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int = 0
    column: int = 0


@dataclass
class Identifier(ASTNode):
    """Variable or function identifier."""
    name: str = ""


@dataclass
class Literal(ASTNode):
    """Literal value (number, string, etc.)."""
    value: Any = None
    type: str = "unknown"


@dataclass
class BinaryOp(ASTNode):
    """Binary operation (add, subtract, etc.)."""
    op: str = ""
    left: Optional[ASTNode] = None
    right: Optional[ASTNode] = None


@dataclass
class SetStatement(ASTNode):
    """Variable assignment statement."""
    identifier: str = ""
    value: Optional[ASTNode] = None


@dataclass
class PrintStatement(ASTNode):
    """Print statement."""
    value: Optional[ASTNode] = None


@dataclass
class IfStatement(ASTNode):
    """Conditional statement."""
    condition: Optional[ASTNode] = None
    then_branch: List[ASTNode] = field(default_factory=list)
    else_branch: Optional[List[ASTNode]] = None


@dataclass
class Program(ASTNode):
    """Root program node."""
    statements: List[ASTNode] = field(default_factory=list)
