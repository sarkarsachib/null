"""Super-bit emitter that converts AST to super-bit tokens."""

from typing import List

from ..ast.nodes import (
    ASTNode,
    Program,
    SetStatement,
    BinaryOp,
    PrintStatement,
    IfStatement,
    Identifier,
    Literal,
)
from .tokens import SuperBitToken, SuperBitGroup


class SuperBitEmitter:
    """Emits super-bit tokens from an AST."""
    
    AST_TO_SUPERBIT_TABLE = {
        "add": "BINARY_ADD",
        "subtract": "BINARY_SUB",
        "multiply": "BINARY_MUL",
        "divide": "BINARY_DIV",
        "greater_than": "COMPARE_GT",
        "less_than": "COMPARE_LT",
        "equals": "COMPARE_EQ",
    }
    
    def __init__(self):
        self.tokens: List[SuperBitToken] = []
    
    def emit(self, ast: ASTNode) -> SuperBitGroup:
        """Emit super-bit tokens from an AST."""
        self.tokens = []
        self._visit(ast)
        return SuperBitGroup(tokens=self.tokens)
    
    def _visit(self, node: ASTNode):
        """Visit a node and emit appropriate tokens."""
        method_name = f"_visit_{node.__class__.__name__}"
        method = getattr(self, method_name, self._visit_generic)
        method(node)
    
    def _visit_generic(self, node: ASTNode):
        """Generic visitor."""
        pass
    
    def _visit_Program(self, node: Program):
        """Emit tokens for a program."""
        for stmt in node.statements:
            self._visit(stmt)
    
    def _visit_SetStatement(self, node: SetStatement):
        """Emit tokens for variable assignment."""
        self._visit(node.value)
        self.tokens.append(SuperBitToken(symbol="STORE_VAR", bits=0, bit_width=8))
    
    def _visit_BinaryOp(self, node: BinaryOp):
        """Emit tokens for binary operation."""
        self._visit(node.left)
        self._visit(node.right)
        
        opcode_name = self.AST_TO_SUPERBIT_TABLE.get(node.op)
        if opcode_name:
            self.tokens.append(SuperBitToken(symbol=opcode_name, bits=0, bit_width=8))
    
    def _visit_PrintStatement(self, node: PrintStatement):
        """Emit tokens for print statement."""
        self._visit(node.value)
        self.tokens.append(SuperBitToken(symbol="PRINT", bits=0, bit_width=8))
    
    def _visit_IfStatement(self, node: IfStatement):
        """Emit tokens for if statement."""
        self._visit(node.condition)
        
        jump_if_false_idx = len(self.tokens)
        self.tokens.append(SuperBitToken(symbol="JUMP_IF_FALSE", bits=0, bit_width=16))
        
        for stmt in node.then_branch:
            self._visit(stmt)
        
        if node.else_branch:
            jump_idx = len(self.tokens)
            self.tokens.append(SuperBitToken(symbol="JUMP", bits=0, bit_width=16))
            
            else_start = len(self.tokens)
            self.tokens[jump_if_false_idx] = SuperBitToken(
                symbol="JUMP_IF_FALSE", bits=else_start, bit_width=16
            )
            
            for stmt in node.else_branch:
                self._visit(stmt)
            
            end_idx = len(self.tokens)
            self.tokens[jump_idx] = SuperBitToken(symbol="JUMP", bits=end_idx, bit_width=16)
        else:
            end_idx = len(self.tokens)
            self.tokens[jump_if_false_idx] = SuperBitToken(
                symbol="JUMP_IF_FALSE", bits=end_idx, bit_width=16
            )
    
    def _visit_Identifier(self, node: Identifier):
        """Emit tokens for identifier."""
        self.tokens.append(SuperBitToken(symbol="LOAD_VAR", bits=hash(node.name) % 256, bit_width=8))
    
    def _visit_Literal(self, node: Literal):
        """Emit tokens for literal value."""
        self.tokens.append(SuperBitToken(symbol="LOAD_CONST", bits=hash(str(node.value)) % 256, bit_width=8))
