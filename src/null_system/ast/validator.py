"""AST validation logic."""

from typing import List, Set, Optional, Dict, Any

from .nodes import (
    ASTNode,
    Program,
    SetStatement,
    BinaryOp,
    PrintStatement,
    IfStatement,
    Identifier,
    Literal,
)


class ValidationError(Exception):
    """AST validation error."""
    pass


class ASTValidator:
    """Validates AST for semantic correctness.
    
    Can optionally consume type inference results for null-safety checking.
    """
    
    def __init__(self, inferred_types: Optional[Dict[int, Any]] = None):
        self.defined_variables: Set[str] = set()
        self.inferred_types = inferred_types or {}
        self.errors: List[str] = []
        self.nullable_variables: Set[str] = set()
        self.sealed_trait_handlers: Dict[str, Set[str]] = {}
    
    def validate(self, node: ASTNode) -> bool:
        """Validate an AST node and its children."""
        self.errors = []
        self.defined_variables = set()
        
        try:
            self._visit(node)
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
    
    def check_non_null_safety(self, var_name: str, node: ASTNode) -> bool:
        """Check if a variable is safely accessed (not null-unsafe)."""
        if var_name in self.nullable_variables:
            self.errors.append(f"Potentially null reference: {var_name} at line {node.line}")
            return False
        return True
    
    def enforce_exhaustive_match(self, sealed_trait: str, 
                                handlers: Set[str]) -> bool:
        """Enforce exhaustive handling for sealed traits."""
        if sealed_trait not in self.sealed_trait_handlers:
            return True
        
        required = self.sealed_trait_handlers[sealed_trait]
        if not required.issubset(handlers):
            missing = required - handlers
            self.errors.append(f"Non-exhaustive match for {sealed_trait}. Missing: {missing}")
            return False
        return True
    
    def set_nullable_variable(self, var_name: str) -> None:
        """Mark a variable as nullable."""
        self.nullable_variables.add(var_name)
    
    def narrow_type(self, var_name: str, condition: str) -> None:
        """Narrow a variable type based on null-check condition."""
        if condition == "is_not_null":
            self.nullable_variables.discard(var_name)
        elif condition == "is_null":
            self.nullable_variables.add(var_name)
