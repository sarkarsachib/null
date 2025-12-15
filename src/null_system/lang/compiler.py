"""Compiler for Null-Lang AST to Super-Bit IR with layer annotation metadata.

This module compiles Null-Lang AST nodes into Super-Bit IR tokens, threading
layer annotation metadata into each token to allow downstream VMs/tooling to
route instructions to specific execution layers.
"""

from typing import List, Optional, Dict, Any, Union

from .ast_nodes import (
    ASTNode,
    Program,
    SetCommand,
    AddCommand,
    ShowCommand,
    IfCommand,
    RepeatCommand,
    DefineCommand,
    Identifier,
    TextLiteral,
    NumLiteral,
    BoolLiteral,
    ArrayLiteral,
    ObjectLiteral,
    MemberAccess,
    BinaryExpression,
    UnaryExpression,
    ComparisonExpression,
    FunctionCall,
    NullLibAnnotation,
    BinaryOperator,
    UnaryOperator,
    LayerAnnotation,
    RequireAnnotation,
    PreferAnnotation,
)
from ..superbit.ir import SuperBitIRToken, SuperBitOpCode, SuperBitStream


class NullLangCompiler:
    """Compiles Null-Lang AST to Super-Bit IR with layer metadata."""

    def __init__(self):
        self.tokens: List[SuperBitIRToken] = []
        self.current_metadata: Dict[str, Any] = {}

    def compile(self, ast: ASTNode) -> SuperBitStream:
        """Compile an AST node to a Super-Bit IR stream.

        Args:
            ast: The AST node to compile

        Returns:
            A SuperBitStream containing IR tokens with metadata
        """
        self.tokens = []
        self.current_metadata = {}
        self._visit(ast)
        return SuperBitStream(tokens=self.tokens)

    def _emit(
        self,
        opcode: SuperBitOpCode,
        operand: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit an IR token with optional metadata."""
        token_metadata = self.current_metadata.copy()
        if metadata:
            token_metadata.update(metadata)

        token = SuperBitIRToken(opcode=opcode, operand=operand, metadata=token_metadata)
        self.tokens.append(token)

    def _visit(self, node: ASTNode) -> None:
        """Visit a node and emit appropriate tokens."""
        method_name = f"_visit_{node.__class__.__name__}"
        method = getattr(self, method_name, self._visit_generic)
        method(node)

    def _visit_generic(self, node: ASTNode) -> None:
        """Generic visitor for unknown nodes."""
        pass

    def _visit_Program(self, node: Program) -> None:
        """Emit tokens for a program."""
        for stmt in node.statements:
            self._visit(stmt)

    def _visit_SetCommand(self, node: SetCommand) -> None:
        """Emit tokens for SET command."""
        self._apply_annotations(node)
        self._visit(node.value)
        self._emit(SuperBitOpCode.LOAD_VAR, self._get_target_name(node.target))

    def _visit_AddCommand(self, node: AddCommand) -> None:
        """Emit tokens for ADD command."""
        self._apply_annotations(node)
        for i, operand in enumerate(node.operands):
            self._visit(operand)
            if i > 0:
                self._emit(SuperBitOpCode.BINARY_ADD)

    def _visit_ShowCommand(self, node: ShowCommand) -> None:
        """Emit tokens for SHOW command."""
        self._apply_annotations(node)
        self._visit(node.value)
        self._emit(SuperBitOpCode.PRINT)

    def _visit_IfCommand(self, node: IfCommand) -> None:
        """Emit tokens for IF command."""
        self._apply_annotations(node)
        self._visit(node.condition)
        jump_false_idx = len(self.tokens)
        self._emit(SuperBitOpCode.JUMP_IF_FALSE, 0)

        for stmt in node.then_block:
            self._visit(stmt)

        if node.else_block:
            jump_end_idx = len(self.tokens)
            self._emit(SuperBitOpCode.JUMP, 0)

            else_start = len(self.tokens)
            self.tokens[jump_false_idx] = SuperBitIRToken(
                opcode=SuperBitOpCode.JUMP_IF_FALSE, operand=else_start
            )

            for stmt in node.else_block:
                self._visit(stmt)

            end_idx = len(self.tokens)
            self.tokens[jump_end_idx] = SuperBitIRToken(
                opcode=SuperBitOpCode.JUMP, operand=end_idx
            )
        else:
            end_idx = len(self.tokens)
            self.tokens[jump_false_idx] = SuperBitIRToken(
                opcode=SuperBitOpCode.JUMP_IF_FALSE, operand=end_idx
            )

    def _visit_RepeatCommand(self, node: RepeatCommand) -> None:
        """Emit tokens for REPEAT command."""
        self._apply_annotations(node)
        self._visit(node.count)
        loop_start = len(self.tokens)

        for stmt in node.body:
            self._visit(stmt)

        self._emit(SuperBitOpCode.JUMP, loop_start)

    def _visit_DefineCommand(self, node: DefineCommand) -> None:
        """Emit tokens for DEFINE command."""
        self._apply_annotations(node)

    def _visit_BinaryExpression(self, node: BinaryExpression) -> None:
        """Emit tokens for binary expression."""
        self._visit(node.left)
        self._visit(node.right)

        opcode_map = {
            BinaryOperator.ADD: SuperBitOpCode.BINARY_ADD,
            BinaryOperator.SUBTRACT: SuperBitOpCode.BINARY_SUB,
            BinaryOperator.MULTIPLY: SuperBitOpCode.BINARY_MUL,
            BinaryOperator.DIVIDE: SuperBitOpCode.BINARY_DIV,
            BinaryOperator.EQUALS: SuperBitOpCode.COMPARE_EQ,
            BinaryOperator.NOT_EQUALS: SuperBitOpCode.COMPARE_EQ,
            BinaryOperator.GREATER_THAN: SuperBitOpCode.COMPARE_GT,
            BinaryOperator.LESS_THAN: SuperBitOpCode.COMPARE_LT,
            BinaryOperator.GREATER_EQUAL: SuperBitOpCode.COMPARE_GT,
            BinaryOperator.LESS_EQUAL: SuperBitOpCode.COMPARE_LT,
        }

        if node.operator in opcode_map:
            self._emit(opcode_map[node.operator])

    def _visit_UnaryExpression(self, node: UnaryExpression) -> None:
        """Emit tokens for unary expression."""
        self._visit(node.operand)

    def _visit_ComparisonExpression(self, node: ComparisonExpression) -> None:
        """Emit tokens for comparison expression."""
        self._visit(node.left)
        self._visit(node.right)

    def _visit_Identifier(self, node: Identifier) -> None:
        """Emit tokens for identifier."""
        self._emit(SuperBitOpCode.LOAD_VAR, node.name)

    def _visit_TextLiteral(self, node: TextLiteral) -> None:
        """Emit tokens for text literal."""
        self._emit(SuperBitOpCode.LOAD_CONST, node.value)

    def _visit_NumLiteral(self, node: NumLiteral) -> None:
        """Emit tokens for numeric literal."""
        self._emit(SuperBitOpCode.LOAD_CONST, node.value)

    def _visit_BoolLiteral(self, node: BoolLiteral) -> None:
        """Emit tokens for boolean literal."""
        self._emit(SuperBitOpCode.LOAD_CONST, node.value)

    def _visit_ArrayLiteral(self, node: ArrayLiteral) -> None:
        """Emit tokens for array literal."""
        for element in node.elements:
            self._visit(element)

    def _visit_ObjectLiteral(self, node: ObjectLiteral) -> None:
        """Emit tokens for object literal."""
        for _, value in node.pairs:
            self._visit(value)

    def _visit_MemberAccess(self, node: MemberAccess) -> None:
        """Emit tokens for member access."""
        self._visit(node.object)

    def _visit_FunctionCall(self, node: FunctionCall) -> None:
        """Emit tokens for function call."""
        for arg in node.arguments:
            self._visit(arg)

    def _visit_NullLibAnnotation(self, node: NullLibAnnotation) -> None:
        """Emit tokens for null-lib annotation."""
        for arg in node.arguments:
            self._visit(arg)

    def _apply_annotations(self, node: ASTNode) -> None:
        """Apply annotations from a statement to the current metadata."""
        if not hasattr(node, "annotations"):
            return

        for annotation in node.annotations:
            if isinstance(annotation, LayerAnnotation):
                self.current_metadata["layer"] = annotation.layer
            elif isinstance(annotation, RequireAnnotation):
                self.current_metadata["requires"] = annotation.layers
            elif isinstance(annotation, PreferAnnotation):
                self.current_metadata["prefers"] = annotation.layers

    def _get_target_name(
        self, target: Union[Identifier, MemberAccess]
    ) -> str:
        """Extract target name from identifier or member access."""
        if isinstance(target, Identifier):
            return target.name
        elif isinstance(target, MemberAccess):
            if isinstance(target.member, str):
                return target.member
            elif isinstance(target.member, Identifier):
                return target.member.name
        return ""


def compile_program(source: str) -> SuperBitStream:
    """Convenience function to compile Null-Lang source to IR.

    Args:
        source: Null-Lang source code

    Returns:
        A SuperBitStream with compiled IR tokens
    """
    from .parser import parse

    ast = parse(source)
    compiler = NullLangCompiler()
    return compiler.compile(ast)
