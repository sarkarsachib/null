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


@dataclass
class Pattern(ASTNode):
    """Pattern for destructuring in match expressions."""
    pattern_type: str = ""
    name: Optional[str] = None
    tag: Optional[str] = None
    inner_patterns: Optional[List["Pattern"]] = None
    binding_name: Optional[str] = None


@dataclass
class WhenGuard(ASTNode):
    """Guard clause for pattern match cases."""
    condition: Optional[ASTNode] = None


@dataclass
class MatchCase(ASTNode):
    """A single case in a match expression."""
    pattern: Optional[Pattern] = None
    guard: Optional[WhenGuard] = None
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class MatchExpression(ASTNode):
    """Pattern matching expression."""
    expr: Optional[ASTNode] = None
    cases: List[MatchCase] = field(default_factory=list)


@dataclass
class LetBinding(ASTNode):
    """Rust-like let binding statement."""
    pattern: Optional[ASTNode] = None
    mutable: bool = False
    value: Optional[ASTNode] = None


@dataclass
class BorrowExpr(ASTNode):
    """Rust-like borrow expression (&var or &mut var)."""
    expr: Optional[ASTNode] = None
    mutable: bool = False
    lifetime: Optional[str] = None


@dataclass
class LifetimeAnnotation(ASTNode):
    """Lifetime annotation ('a, 'b, etc.)."""
    lifetime: str = ""


@dataclass
class DropStatement(ASTNode):
    """Explicit drop statement."""
    target: Optional[ASTNode] = None
