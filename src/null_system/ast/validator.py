"""AST validation logic."""

from typing import List, Set

from .nodes import (
    ASTNode,
    Program,
    SetStatement,
    LetBinding,
    BorrowExpr,
    DropStatement,
    BinaryOp,
    PrintStatement,
    IfStatement,
    Identifier,
    Literal,
)
from ..analysis.ownership import OwnershipAnalyzer


class ValidationError(Exception):
    """AST validation error."""
    pass


class ASTValidator:
    """Validates AST for semantic correctness."""
    
    def __init__(self):
        self.defined_variables: Set[str] = set()
        self.errors: List[str] = []
        self.ownership_analyzer = OwnershipAnalyzer()
    
    def validate(self, node: ASTNode) -> bool:
        """Validate an AST node and its children."""
        self.errors = []
        self.defined_variables = set()
        
        try:
            # Basic semantic validation
            self._visit(node)
            
            # Ownership validation
            if not self.ownership_analyzer.analyze(node):
                self.errors.extend(self.ownership_analyzer.get_errors())
            
            return len(self.errors) == 0
        except ValidationError as e:
            self.errors.append(str(e))
            return False
    
    def _visit(self, node: ASTNode):
        """Visit a node and dispatch to appropriate handler."""
        method_name = f"_visit_{node.__class__.__name__}"
        method = getattr(self, method_name, self._visit_generic)
        method(node)
    
    def _visit_generic(self, node: ASTNode):
        """Generic visitor for unknown nodes."""
        pass
    
    def _visit_Program(self, node: Program):
        """Validate a program node."""
        for stmt in node.statements:
            self._visit(stmt)
    
    def _visit_SetStatement(self, node: SetStatement):
        """Validate a set statement."""
        self._visit(node.value)
        self.defined_variables.add(node.identifier)
    
    def _visit_LetBinding(self, node: LetBinding):
        """Validate a let binding statement."""
        self._visit(node.value)
        if node.pattern and isinstance(node.pattern, Identifier):
            self.defined_variables.add(node.pattern.name)
    
    def _visit_BorrowExpr(self, node: BorrowExpr):
        """Validate a borrow expression."""
        self._visit(node.expr)
    
    def _visit_DropStatement(self, node: DropStatement):
        """Validate a drop statement."""
        self._visit(node.target)
    
    def _visit_BinaryOp(self, node: BinaryOp):
        """Validate a binary operation."""
        self._visit(node.left)
        self._visit(node.right)
        
        valid_ops = {"add", "subtract", "multiply", "divide", "greater_than", "less_than", "equals"}
        if node.op not in valid_ops:
            self.errors.append(f"Invalid operation: {node.op}")
    
    def _visit_PrintStatement(self, node: PrintStatement):
        """Validate a print statement."""
        self._visit(node.value)
    
    def _visit_IfStatement(self, node: IfStatement):
        """Validate an if statement."""
        self._visit(node.condition)
        
        for stmt in node.then_branch:
            self._visit(stmt)
        
        if node.else_branch:
            for stmt in node.else_branch:
                self._visit(stmt)
    
    def _visit_Identifier(self, node: Identifier):
        """Validate an identifier reference."""
        if node.name not in self.defined_variables:
            self.errors.append(f"Undefined variable: {node.name} at line {node.line}")
    
    def _visit_Literal(self, node: Literal):
        """Validate a literal value."""
        pass
