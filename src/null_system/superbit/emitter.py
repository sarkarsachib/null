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
from .ir import SuperBitIRToken, SuperBitOpCode, SuperBitStream


class SuperBitEmitter:
    """Emits Super-bit IR tokens from an AST."""

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
        self.tokens: List[SuperBitIRToken] = []

    def emit(self, ast: ASTNode) -> SuperBitStream:
        """Emit Super-bit IR tokens from an AST."""
        self.tokens = []
        self._visit(ast)
        return SuperBitStream(tokens=self.tokens)

    def _emit(self, opcode: SuperBitOpCode, operand: object | None = None, *, line: int | None = None):
        self.tokens.append(SuperBitIRToken(opcode=opcode, operand=operand, source_line=line))
    
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
        self._emit(SuperBitOpCode.STORE_VAR, node.identifier, line=node.line)

    def _visit_BinaryOp(self, node: BinaryOp):
        """Emit tokens for binary operation."""
        self._visit(node.left)
        self._visit(node.right)

        opcode = self.AST_TO_SUPERBIT_TABLE.get(node.op)
        if opcode:
            self._emit(opcode, line=node.line)

    def _visit_PrintStatement(self, node: PrintStatement):
        """Emit tokens for print statement."""
        self._visit(node.value)
        self._emit(SuperBitOpCode.PRINT, line=node.line)

    def _visit_IfStatement(self, node: IfStatement):
        """Emit tokens for if statement."""
        self._visit(node.condition)

        jump_if_false_idx = len(self.tokens)
        self._emit(SuperBitOpCode.JUMP_IF_FALSE, 0, line=node.line)

        for stmt in node.then_branch:
            self._visit(stmt)

        if node.else_branch:
            jump_idx = len(self.tokens)
            self._emit(SuperBitOpCode.JUMP, 0, line=node.line)

            else_start = len(self.tokens)
            self.tokens[jump_if_false_idx] = SuperBitIRToken(
                opcode=SuperBitOpCode.JUMP_IF_FALSE,
                operand=else_start,
                source_line=node.line,
            )

            for stmt in node.else_branch:
                self._visit(stmt)

            end_idx = len(self.tokens)
            self.tokens[jump_idx] = SuperBitIRToken(
                opcode=SuperBitOpCode.JUMP,
                operand=end_idx,
                source_line=node.line,
            )
        else:
            end_idx = len(self.tokens)
            self.tokens[jump_if_false_idx] = SuperBitIRToken(
                opcode=SuperBitOpCode.JUMP_IF_FALSE,
                operand=end_idx,
                source_line=node.line,
            )

    def _visit_Identifier(self, node: Identifier):
        """Emit tokens for identifier."""
        self._emit(SuperBitOpCode.LOAD_VAR, node.name, line=node.line)

    def _visit_Literal(self, node: Literal):
        """Emit tokens for literal value."""
        self._emit(SuperBitOpCode.LOAD_CONST, node.value, line=node.line)
