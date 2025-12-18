"""Ownership analysis for memory safety in Null-Lang.

This module implements Phase 1 memory safety features including:
- Variable ownership tracking
- Borrow state management (mutable/immutable borrows)
- RAII scope enforcement
- Detection of ownership violations
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from ..ast.nodes import ASTNode, Program, LetBinding, BorrowExpr, DropStatement, Identifier


class BorrowType(Enum):
    """Types of borrows in the ownership system."""
    IMMUTABLE = "immutable"  # &T
    MUTABLE = "mutable"      # &mut T


class OwnershipError(Exception):
    """Exception raised when ownership rules are violated."""
    pass


@dataclass
class VariableInfo:
    """Information about a variable in the ownership system."""
    name: str
    mutable: bool
    lifetime_start: int
    lifetime_end: Optional[int] = None
    active_borrows: int = 0
    mutable_borrows: int = 0
    is_borrowed: bool = False
    is_dropped: bool = False


@dataclass
class BorrowInfo:
    """Information about a borrow relationship."""
    variable_name: str
    borrow_type: BorrowType
    start_line: int
    end_line: Optional[int] = None


class OwnershipAnalyzer:
    """Analyzes ownership and borrowing patterns for memory safety."""
    
    def __init__(self):
        self.variables: Dict[str, VariableInfo] = {}
        self.active_borrows: List[BorrowInfo] = []
        self.errors: List[str] = []
        self.current_scope_start = 0
        
    def analyze(self, node: ASTNode) -> bool:
        """Analyze an AST node for ownership violations.
        
        Returns True if no violations found, False otherwise.
        """
        self.errors = []
        self.variables.clear()
        self.active_borrows.clear()
        
        try:
            self._visit(node)
            return len(self.errors) == 0
        except OwnershipError as e:
            self.errors.append(str(e))
            return False
    
    def _visit(self, node: ASTNode):
        """Visit a node and dispatch to appropriate handler."""
        method_name = f"_visit_{node.__class__.__name__}"
        method = getattr(self, method_name, self._visit_generic)
        method(node)
    
    def _visit_generic(self, node: ASTNode):
        """Generic visitor for unknown nodes."""
        # Visit children
        for field_name, field_value in node.__dict__.items():
            if isinstance(field_value, ASTNode):
                self._visit(field_value)
            elif isinstance(field_value, list):
                for item in field_value:
                    if isinstance(item, ASTNode):
                        self._visit(item)
    
    def _visit_Program(self, node: Program):
        """Analyze a program."""
        for stmt in node.statements:
            self._visit(stmt)
        
        # Check for dangling references
        self._check_dangling_references()
    
    def _visit_LetBinding(self, node: LetBinding):
        """Analyze a let binding for ownership rules."""
        if node.pattern and isinstance(node.pattern, Identifier):
            var_name = node.pattern.name
            
            # Check if variable already exists in scope
            if var_name in self.variables:
                self.errors.append(f"Variable '{var_name}' already defined at line {node.line}")
                return
            
            # Create variable info
            var_info = VariableInfo(
                name=var_name,
                mutable=node.mutable,
                lifetime_start=node.line
            )
            
            self.variables[var_name] = var_info
        
        # Analyze the value expression
        self._visit(node.value)
    
    def _visit_BorrowExpr(self, node: BorrowExpr):
        """Analyze a borrow expression."""
        if node.expr and isinstance(node.expr, Identifier):
            var_name = node.expr.name
            
            # Check if the variable exists
            if var_name not in self.variables:
                self.errors.append(f"Cannot borrow undefined variable '{var_name}' at line {node.line}")
                return
            
            var_info = self.variables[var_name]
            
            # Check borrowing rules
            self._check_borrow_rules(var_name, node.mutable, node.line)
            
            # Record the borrow
            borrow_info = BorrowInfo(
                variable_name=var_name,
                borrow_type=BorrowType.MUTABLE if node.mutable else BorrowType.IMMUTABLE,
                start_line=node.line
            )
            self.active_borrows.append(borrow_info)
            
            # Update variable info
            var_info.active_borrows += 1
            if node.mutable:
                var_info.mutable_borrows += 1
            var_info.is_borrowed = True
        
        # Analyze the expression being borrowed
        if node.expr:
            self._visit(node.expr)
    
    def _visit_DropStatement(self, node: DropStatement):
        """Analyze a drop statement."""
        if node.target and isinstance(node.target, Identifier):
            var_name = node.target.name
            
            # Check if variable exists
            if var_name not in self.variables:
                self.errors.append(f"Cannot drop undefined variable '{var_name}' at line {node.line}")
                return
            
            var_info = self.variables[var_name]
            
            # Check if variable is already dropped
            if var_info.is_dropped:
                self.errors.append(f"Variable '{var_name}' already dropped at line {node.line}")
                return
            
            # Check if there are active borrows
            if var_info.active_borrows > 0:
                self.errors.append(f"Cannot drop '{var_name}' while it is borrowed at line {node.line}")
                return
            
            # Mark as dropped
            var_info.is_dropped = True
            var_info.lifetime_end = node.line
        
        # Analyze the target expression
        if node.target:
            self._visit(node.target)
    
    def _visit_Identifier(self, node: Identifier):
        """Analyze identifier usage."""
        # Check if identifier refers to a valid variable
        if node.name in self.variables:
            var_info = self.variables[node.name]
            
            # Check if variable has been dropped
            if var_info.is_dropped:
                self.errors.append(f"Use of dropped variable '{node.name}' at line {node.line}")
        else:
            # Check if this is a reference to an undefined variable
            self.errors.append(f"Undefined variable '{node.name}' at line {node.line}")
    
    def _check_borrow_rules(self, var_name: str, mutable: bool, line: int):
        """Check if a borrow follows the rules."""
        var_info = self.variables[var_name]
        
        # Rule 1: Cannot create mutable borrow if variable is immutable
        if mutable and not var_info.mutable:
            raise OwnershipError(
                f"Cannot create mutable borrow of immutable variable '{var_name}' at line {line}"
            )
        
        # Rule 2: Cannot create multiple mutable borrows
        if mutable and var_info.mutable_borrows > 0:
            raise OwnershipError(
                f"Cannot create mutable borrow while mutable borrow already exists for '{var_name}' at line {line}"
            )
        
        # Rule 3: Cannot create mutable borrow while immutable borrows exist
        if mutable and var_info.active_borrows > var_info.mutable_borrows:
            raise OwnershipError(
                f"Cannot create mutable borrow while immutable borrows exist for '{var_name}' at line {line}"
            )
    
    def _check_dangling_references(self):
        """Check for dangling references at the end of the scope."""
        for borrow in self.active_borrows:
            if borrow.end_line is None:
                # Find the variable info
                if borrow.variable_name in self.variables:
                    var_info = self.variables[borrow.variable_name]
                    if var_info.is_dropped:
                        self.errors.append(
                            f"Dangling reference: '{borrow.variable_name}' used after drop"
                        )
    
    def get_variable_state(self, var_name: str) -> Optional[VariableInfo]:
        """Get the current state of a variable."""
        return self.variables.get(var_name)
    
    def get_errors(self) -> List[str]:
        """Get the list of ownership errors found during analysis."""
        return self.errors.copy()