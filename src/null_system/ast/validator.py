"""AST validation logic."""

from typing import Dict, List, Set, Optional

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
    """Validates AST for semantic correctness."""
    
    def __init__(self):
        self.defined_variables: Set[str] = set()
        self.errors: List[str] = []
        self.current_module: Optional[str] = None
        self.module_symbols: Dict[str, Set[str]] = {}
        self.imported_modules: Set[str] = set()
        self.module_aliases: Dict[str, str] = {}
    
    def validate(self, node: ASTNode) -> bool:
        """Validate an AST node and its children."""
        self.errors = []
        self.defined_variables = set()
        self.current_module = None
        self.module_symbols = {}
        self.imported_modules = set()
        self.module_aliases = {}
        
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
        if hasattr(node, 'module_declaration') and node.module_declaration:
            module_name = node.module_declaration.name.full_name
            self.current_module = module_name
            if module_name not in self.module_symbols:
                self.module_symbols[module_name] = set()
        else:
            self.current_module = "__main__"
            if "__main__" not in self.module_symbols:
                self.module_symbols["__main__"] = set()
        
        if hasattr(node, 'imports'):
            for import_stmt in node.imports:
                module_name = import_stmt.module_name.full_name
                self.imported_modules.add(module_name)
                if import_stmt.alias:
                    self.module_aliases[import_stmt.alias] = module_name
        
        for stmt in node.statements:
            self._visit(stmt)
    
    def _visit_SetStatement(self, node: SetStatement):
        """Validate a set statement."""
        self._visit(node.value)
        identifier = getattr(node, 'identifier', None)
        if identifier is None:
            target = getattr(node, 'target', None)
            if target:
                if hasattr(target, 'name'):
                    identifier = target.name
                else:
                    identifier = str(target)
        if identifier:
            self.defined_variables.add(identifier)
            if self.current_module and self.current_module in self.module_symbols:
                self.module_symbols[self.current_module].add(identifier)
    
    def _visit_SetCommand(self, node):
        """Validate a SetCommand (lang AST node)."""
        self._visit(node.value)
        target = node.target
        if hasattr(target, 'name'):
            identifier = target.name
        else:
            identifier = str(target)
        self.defined_variables.add(identifier)
        if self.current_module and self.current_module in self.module_symbols:
            self.module_symbols[self.current_module].add(identifier)
    
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
