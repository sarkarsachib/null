"""Super-bit emitter that converts AST to super-bit tokens."""

from typing import List

from ..ast.nodes import (
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
    MatchExpression,
    MatchCase,
    Pattern,
    WhenGuard,
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
    
    def _visit_LetBinding(self, node: LetBinding):
        """Emit tokens for let binding."""
        self._visit(node.value)
        if node.pattern and isinstance(node.pattern, Identifier):
            self._emit(SuperBitOpCode.STORE_VAR, node.pattern.name, line=node.line)
    
    def _visit_BorrowExpr(self, node: BorrowExpr):
        """Emit tokens for borrow expression."""
        self._visit(node.expr)
        
        # Choose appropriate borrow opcode
        if node.mutable:
            self._emit(SuperBitOpCode.BORROW_MUT, line=node.line)
        else:
            self._emit(SuperBitOpCode.BORROW_IMM, line=node.line)
    
    def _visit_DropStatement(self, node: DropStatement):
        """Emit tokens for drop statement."""
        self._visit(node.target)
        self._emit(SuperBitOpCode.DROP, line=node.line)

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

    def _visit_MatchExpression(self, node: MatchExpression):
        """Emit tokens for match expression."""
        self._visit(node.expr)

        case_jump_indices = []
        for case in node.cases:
            if case.pattern:
                self._emit_pattern_match(case.pattern, line=node.line)
                pattern_jump_idx = len(self.tokens)
                self._emit(SuperBitOpCode.JUMP_IF_FALSE, 0, line=node.line)
                case_jump_indices.append(pattern_jump_idx)

            if case.guard and case.guard.condition:
                self._visit(case.guard.condition)
                guard_jump_idx = len(self.tokens)
                self._emit(SuperBitOpCode.JUMP_IF_FALSE, 0, line=node.line)
                case_jump_indices.append(guard_jump_idx)

            for stmt in case.body:
                self._visit(stmt)

            end_jump = len(self.tokens)
            self._emit(SuperBitOpCode.JUMP, 0, line=node.line)
            case_jump_indices.append(end_jump)

        end_idx = len(self.tokens)
        for jump_idx in case_jump_indices:
            token = self.tokens[jump_idx]
            self.tokens[jump_idx] = SuperBitIRToken(
                opcode=token.opcode,
                operand=end_idx,
                source_line=token.source_line,
            )

    def _emit_pattern_match(self, pattern: Pattern, *, line: int | None = None):
        """Emit tokens for pattern matching."""
        if pattern.pattern_type == "tag":
            self._emit(SuperBitOpCode.MATCH_TAG, pattern.tag, line=line)
            if pattern.binding_name:
                self._emit(SuperBitOpCode.UNWRAP_UNION, None, line=line)
                self._emit(SuperBitOpCode.STORE_VAR, pattern.binding_name, line=line)
        elif pattern.pattern_type == "binding":
            if pattern.binding_name:
                self._emit(SuperBitOpCode.STORE_VAR, pattern.binding_name, line=line)
        elif pattern.pattern_type == "tuple" or pattern.pattern_type == "list":
            if pattern.inner_patterns:
                for inner in pattern.inner_patterns:
                    self._emit_pattern_match(inner, line=line)
