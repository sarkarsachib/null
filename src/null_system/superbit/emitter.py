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
from .tokens import SuperBitToken, SuperBitOpCode, SuperBitStream


class SuperBitEmitter:
    """Emits super-bit tokens from an AST."""
    
    AST_TO_SUPERBIT_TABLE = {
        "add": SuperBitOpCode.BINARY_ADD,
        "subtract": SuperBitOpCode.BINARY_SUB,
        "multiply": SuperBitOpCode.BINARY_MUL,
        "divide": SuperBitOpCode.BINARY_DIV,
        "greater_than": SuperBitOpCode.COMPARE_GT,
        "less_than": SuperBitOpCode.COMPARE_LT,
        "equals": SuperBitOpCode.COMPARE_EQ,
    }
    
    def __init__(self):
        self.tokens: List[SuperBitToken] = []
    
    def emit(self, ast: ASTNode) -> SuperBitStream:
        """Emit super-bit tokens from an AST."""
        self.tokens = []
        self._visit(ast)
        return SuperBitStream(tokens=self.tokens)
    
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
        self.tokens.append(SuperBitToken(SuperBitOpCode.STORE_VAR, node.identifier))
    
    def _visit_BinaryOp(self, node: BinaryOp):
        """Emit tokens for binary operation."""
        self._visit(node.left)
        self._visit(node.right)
        
        opcode = self.AST_TO_SUPERBIT_TABLE.get(node.op)
        if opcode:
            self.tokens.append(SuperBitToken(opcode))
    
    def _visit_PrintStatement(self, node: PrintStatement):
        """Emit tokens for print statement."""
        self._visit(node.value)
        self.tokens.append(SuperBitToken(SuperBitOpCode.PRINT))
    
    def _visit_IfStatement(self, node: IfStatement):
        """Emit tokens for if statement."""
        self._visit(node.condition)
        
        jump_if_false_idx = len(self.tokens)
        self.tokens.append(SuperBitToken(SuperBitOpCode.JUMP_IF_FALSE, 0))
        
        for stmt in node.then_branch:
            self._visit(stmt)
        
        if node.else_branch:
            jump_idx = len(self.tokens)
            self.tokens.append(SuperBitToken(SuperBitOpCode.JUMP, 0))
            
            else_start = len(self.tokens)
            self.tokens[jump_if_false_idx] = SuperBitToken(
                SuperBitOpCode.JUMP_IF_FALSE, else_start
            )
            
            for stmt in node.else_branch:
                self._visit(stmt)
            
            end_idx = len(self.tokens)
            self.tokens[jump_idx] = SuperBitToken(SuperBitOpCode.JUMP, end_idx)
        else:
            end_idx = len(self.tokens)
            self.tokens[jump_if_false_idx] = SuperBitToken(
                SuperBitOpCode.JUMP_IF_FALSE, end_idx
            )
    
    def _visit_Identifier(self, node: Identifier):
        """Emit tokens for identifier."""
        self.tokens.append(SuperBitToken(SuperBitOpCode.LOAD_VAR, node.name))
    
    def _visit_Literal(self, node: Literal):
        """Emit tokens for literal value."""
        self.tokens.append(SuperBitToken(SuperBitOpCode.LOAD_CONST, node.value))
