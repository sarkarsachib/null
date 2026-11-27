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
    InputCommand,
    FileReadCommand,
    FileWriteCommand,
    FileExistsCommand,
    ListFilesCommand,
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
    ForCommand,
    WhileCommand,
    ReturnCommand,
    BreakCommand,
    ContinueCommand,
    MatchExpression,
    MatchArm,
    BorrowCommand,
    AsyncFunction,
    AwaitExpression,
    TraitDefinition,
    ImplBlock,
    PrintCommand,
    ClassDefinition,
    TryStatement,
    ModuleDeclaration,
    ImportStatement,
    QualifiedIdentifier,
    TypeAliasDeclaration,
    DataClassDeclaration,
    SealedTraitDeclaration,
    SafeCallExpression,
    ElvisExpression,
    NotNullExpression,
    LetBindingExpression,
)
from ..superbit.ir import SuperBitIRToken, SuperBitOpCode, SuperBitStream


class NullLangCompiler:
    """Compiles Null-Lang AST to Super-Bit IR with layer metadata."""

    def __init__(self):
        self.tokens: List[SuperBitIRToken] = []
        self.current_metadata: Dict[str, Any] = {}
        self.current_module: str = "__main__"
        self.imported_modules: Dict[str, str] = {}
        self.current_syntax_mode: Optional[str] = None
        self.current_line: Optional[int] = None
        self._loop_stack: List[Dict[str, Any]] = []
        self._hidden_local_seq = 0
        self._has_main = False

    def compile(self, ast: ASTNode) -> SuperBitStream:
        """Compile an AST node to a Super-Bit IR stream.

        Args:
            ast: The AST node to compile

        Returns:
            A SuperBitStream containing IR tokens with metadata
        """
        self.tokens = []
        self.current_metadata = {}
        self._loop_stack = []
        self._hidden_local_seq = 0
        self.current_module = "__main__"
        self.imported_modules = {}
        self.current_line = None
        self._has_main = False
        self._visit(ast)
        if self._has_main:
            # The program entry point is `main`, as in Rust/C: the top level
            # only contains definitions, so the stream calls it explicitly.
            self._emit(
                SuperBitOpCode.CALL,
                "main",
                {"argc": 0, "arity": 0, "entry": True},
            )
        return SuperBitStream(tokens=self.tokens)

    def _emit(
        self,
        opcode: SuperBitOpCode,
        operand: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit an IR token with optional metadata."""
        token_metadata = self.current_metadata.copy()
        if self.current_module != "__main__":
            token_metadata["module"] = self.current_module
        if self.current_syntax_mode:
            token_metadata["syntax_mode"] = self.current_syntax_mode
        if metadata:
            token_metadata.update(metadata)

        token = SuperBitIRToken(
            opcode=opcode,
            operand=operand,
            source_line=self.current_line,
            metadata=token_metadata,
        )
        self.tokens.append(token)

    def _visit(self, node: ASTNode) -> None:
        """Visit a node and emit appropriate tokens."""
        old_mode = self.current_syntax_mode
        old_line = self.current_line
        if hasattr(node, "syntax_mode") and node.syntax_mode:
            self.current_syntax_mode = node.syntax_mode.value
        # Carry the statement's source line onto every token it emits, so the VM
        # can report where a runtime error happened.
        span = getattr(node, "span", None)
        if span is not None and getattr(span, "start_line", None) is not None:
            self.current_line = span.start_line

        method_name = f"_visit_{node.__class__.__name__}"
        method = getattr(self, method_name, self._visit_generic)
        method(node)

        self.current_syntax_mode = old_mode
        self.current_line = old_line

    def _visit_generic(self, node: ASTNode) -> None:
        """Generic visitor for unknown nodes."""
        pass

    def _visit_Program(self, node: Program) -> None:
        """Emit tokens for a program."""
        if hasattr(node, 'module_declaration') and node.module_declaration:
            self.current_module = node.module_declaration.name.full_name
        
        if hasattr(node, 'imports'):
            for import_stmt in node.imports:
                module_name = import_stmt.module_name.full_name
                alias = import_stmt.alias or module_name
                self.imported_modules[alias] = module_name
        
        for stmt in node.statements:
            self._visit(stmt)

    def _visit_SetCommand(self, node: SetCommand) -> None:
        """Emit tokens for SET command."""
        self._apply_annotations(node)
        self._visit(node.value)
        self._emit(SuperBitOpCode.STORE_VAR, self._get_target_name(node.target))

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

    def _visit_InputCommand(self, node: InputCommand) -> None:
        """Emit tokens for INPUT command."""
        self._apply_annotations(node)
        if node.prompt:
            self._visit(node.prompt)
            self._emit(SuperBitOpCode.PRINT)
        self._emit(SuperBitOpCode.INPUT)
        self._emit(SuperBitOpCode.STORE_VAR, node.variable)

    def _visit_FileReadCommand(self, node: FileReadCommand) -> None:
        """Emit tokens for READ_FILE command."""
        self._apply_annotations(node)
        self._visit(node.path)
        self._emit(SuperBitOpCode.FILE_READ)
        if node.target:
            self._emit(SuperBitOpCode.STORE_VAR, node.target)

    def _visit_FileWriteCommand(self, node: FileWriteCommand) -> None:
        """Emit tokens for WRITE_FILE command."""
        self._apply_annotations(node)
        self._visit(node.path)
        self._visit(node.content)
        self._emit(SuperBitOpCode.FILE_WRITE)

    def _visit_FileExistsCommand(self, node: FileExistsCommand) -> None:
        """Emit tokens for FILE_EXISTS command."""
        self._apply_annotations(node)
        self._visit(node.path)
        self._emit(SuperBitOpCode.FILE_EXISTS)
        if node.target:
            self._emit(SuperBitOpCode.STORE_VAR, node.target)

    def _visit_ListFilesCommand(self, node: ListFilesCommand) -> None:
        """Emit tokens for LIST_FILES command."""
        self._apply_annotations(node)
        self._visit(node.path)
        self._emit(SuperBitOpCode.LIST_FILES)
        if node.target:
            self._emit(SuperBitOpCode.STORE_VAR, node.target)

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

    def _new_hidden_local(self, kind: str) -> str:
        """Return a fresh name for a compiler-generated local.

        REPEAT needs a counter slot that the source cannot name. The prefix is
        outside the identifier grammar's reach in practice, and the sequence
        makes the name unique per compilation, so nested REPEATs cannot share
        a counter.
        """
        self._hidden_local_seq += 1
        return f"__null_{kind}_{self._hidden_local_seq}"

    def _visit_RepeatCommand(self, node: RepeatCommand) -> None:
        """Emit tokens for REPEAT command.

        The count used to be evaluated and then dropped: the body followed an
        unconditional JUMP back to its own start, so every REPEAT looped
        forever. The count now lives in a hidden counter slot that is tested
        before each pass and decremented at the end of one, which is also where
        CONTINUE goes.
        """
        self._apply_annotations(node)
        counter = self._new_hidden_local("repeat")
        self._visit(node.count)
        self._emit(SuperBitOpCode.STORE_VAR, counter)

        # Loop while the counter is still positive, so a count of 0 runs the
        # body zero times and the last pass decrements to exactly 0.
        loop_start = len(self.tokens)
        self._emit(SuperBitOpCode.LOAD_VAR, counter)
        self._emit(SuperBitOpCode.LOAD_CONST, 0)
        self._emit(SuperBitOpCode.COMPARE_GT)
        jump_exit_idx = len(self.tokens)
        self._emit(SuperBitOpCode.JUMP_IF_FALSE, 0)

        decrement = len(self.tokens)
        self._loop_stack.append({"continue": decrement, "breaks": []})
        for stmt in node.body:
            self._visit(stmt)
        loop_ctx = self._loop_stack.pop()

        self._emit(SuperBitOpCode.LOAD_VAR, counter)
        self._emit(SuperBitOpCode.LOAD_CONST, 1)
        self._emit(SuperBitOpCode.BINARY_SUB)
        self._emit(SuperBitOpCode.STORE_VAR, counter)
        self._emit(SuperBitOpCode.JUMP, loop_start)

        end_idx = len(self.tokens)
        self.tokens[jump_exit_idx] = SuperBitIRToken(
            opcode=SuperBitOpCode.JUMP_IF_FALSE, operand=end_idx
        )
        for break_idx in loop_ctx["breaks"]:
            self.tokens[break_idx] = SuperBitIRToken(
                opcode=SuperBitOpCode.JUMP, operand=end_idx
            )

    def _visit_DefineCommand(self, node: DefineCommand) -> None:
        """Emit tokens for DEFINE command.

        The body is emitted inline after a jump, so the enclosing top-level
        program never falls into a definition; the FUNCTION/RETURN pair gives
        the VM everything it needs to call it.
        """
        self._apply_annotations(node)
        if node.name == "main":
            self._has_main = True
        jump_idx = len(self.tokens)
        self._emit(SuperBitOpCode.JUMP, 0)
        self._emit(
            SuperBitOpCode.FUNCTION,
            node.name,
            {"arity": len(node.parameters), "params": list(node.parameters)},
        )
        for stmt in node.body:
            self._visit(stmt)
        self._emit(SuperBitOpCode.RETURN, None, {"unit": True})
        self._emit(SuperBitOpCode.NOP, "end_fn")
        end = len(self.tokens)
        self.tokens[jump_idx] = SuperBitIRToken(
            opcode=SuperBitOpCode.JUMP, operand=end, metadata={"arity": "jump"}
        )

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
            BinaryOperator.NOT_EQUALS: SuperBitOpCode.COMPARE_NE,
            BinaryOperator.GREATER_THAN: SuperBitOpCode.COMPARE_GT,
            BinaryOperator.LESS_THAN: SuperBitOpCode.COMPARE_LT,
            BinaryOperator.GREATER_EQUAL: SuperBitOpCode.COMPARE_GE,
            BinaryOperator.LESS_EQUAL: SuperBitOpCode.COMPARE_LE,
            BinaryOperator.AND: SuperBitOpCode.LOGICAL_AND,
            BinaryOperator.OR: SuperBitOpCode.LOGICAL_OR,
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
        self._emit(SuperBitOpCode.ARRAY, None, {"arity": len(node.elements)})

    def _visit_ObjectLiteral(self, node: ObjectLiteral) -> None:
        """Emit tokens for object literal."""
        for _, value in node.pairs:
            self._visit(value)

    def _visit_MemberAccess(self, node: MemberAccess) -> None:
        """Emit tokens for member access."""
        self._visit(node.object)
        if node.is_index:
            self._visit(node.member)
            self._emit(SuperBitOpCode.INDEX)

    def _visit_FunctionCall(self, node: FunctionCall) -> None:
        """Emit tokens for function call."""
        for arg in node.arguments:
            self._visit(arg)
        self._emit(
            SuperBitOpCode.CALL,
            node.name,
            {"argc": len(node.arguments), "arity": len(node.arguments)},
        )

    def _visit_NullLibAnnotation(self, node: NullLibAnnotation) -> None:
        """Emit tokens for null-lib annotation."""
        for arg in node.arguments:
            self._visit(arg)

    def _visit_ForCommand(self, node: ForCommand) -> None:
        """Emit tokens for for loop."""
        self._apply_annotations(node)
        self._visit(node.iterable)
        loop_start = len(self.tokens)

        for stmt in node.body:
            self._visit(stmt)

        self._emit(SuperBitOpCode.JUMP, loop_start)

    def _visit_WhileCommand(self, node: WhileCommand) -> None:
        """Emit tokens for while loop, patching break/continue targets."""
        self._apply_annotations(node)
        loop_start = len(self.tokens)
        self._visit(node.condition)
        jump_false_idx = len(self.tokens)
        self._emit(SuperBitOpCode.JUMP_IF_FALSE, 0)

        self._loop_stack.append({"continue": loop_start, "breaks": []})
        for stmt in node.body:
            self._visit(stmt)
        loop_ctx = self._loop_stack.pop()

        self._emit(SuperBitOpCode.JUMP, loop_start)
        end_idx = len(self.tokens)
        self.tokens[jump_false_idx] = SuperBitIRToken(
            opcode=SuperBitOpCode.JUMP_IF_FALSE, operand=end_idx
        )
        for break_idx in loop_ctx["breaks"]:
            self.tokens[break_idx] = SuperBitIRToken(
                opcode=SuperBitOpCode.JUMP, operand=end_idx
            )

    def _visit_ReturnCommand(self, node: ReturnCommand) -> None:
        """Emit tokens for return statement."""
        self._apply_annotations(node)
        unit = not bool(node.value)
        if node.value:
            self._visit(node.value)
        self._emit(SuperBitOpCode.RETURN, None, {"unit": unit})

    def _visit_BreakCommand(self, node: BreakCommand) -> None:
        """Emit tokens for break statement (patched to the loop exit)."""
        self._apply_annotations(node)
        break_idx = len(self.tokens)
        self._emit(SuperBitOpCode.JUMP, 0)
        if self._loop_stack:
            self._loop_stack[-1]["breaks"].append(break_idx)

    def _visit_ContinueCommand(self, node: ContinueCommand) -> None:
        """Emit tokens for continue statement."""
        self._apply_annotations(node)
        target = self._loop_stack[-1]["continue"] if self._loop_stack else 0
        self._emit(SuperBitOpCode.JUMP, target)

    def _visit_MatchExpression(self, node: MatchExpression) -> None:
        """Emit tokens for match expression."""
        self._apply_annotations(node)
        self._visit(node.expr)

        for arm in node.arms:
            self._visit(arm)

    def _visit_MatchArm(self, node: MatchArm) -> None:
        """Emit tokens for match arm."""
        for stmt in node.body:
            self._visit(stmt)

    def _visit_BorrowCommand(self, node: BorrowCommand) -> None:
        """Emit tokens for borrow/reference."""
        self._apply_annotations(node)
        self._visit(node.target)

    def _visit_AsyncFunction(self, node: AsyncFunction) -> None:
        """Emit tokens for async function."""
        self._apply_annotations(node)

    def _visit_AwaitExpression(self, node: AwaitExpression) -> None:
        """Emit tokens for await expression."""
        self._visit(node.expr)

    def _visit_TraitDefinition(self, node: TraitDefinition) -> None:
        """Emit tokens for trait definition."""
        self._apply_annotations(node)

    def _visit_ImplBlock(self, node: ImplBlock) -> None:
        """Emit tokens for impl block."""
        self._apply_annotations(node)

    def _visit_PrintCommand(self, node: PrintCommand) -> None:
        """Emit tokens for print command."""
        self._apply_annotations(node)
        self._visit(node.value)
        self._emit(SuperBitOpCode.PRINT)

    def _visit_ClassDefinition(self, node: ClassDefinition) -> None:
        """Emit tokens for class definition."""
        self._apply_annotations(node)

    def _visit_TryStatement(self, node: TryStatement) -> None:
        """Emit tokens for try/except statement."""
        self._apply_annotations(node)
        for stmt in node.body:
            self._visit(stmt)

        if node.finally_block:
            for stmt in node.finally_block:
                self._visit(stmt)
    
    def _visit_TypeAliasDeclaration(self, node: TypeAliasDeclaration) -> None:
        """Emit tokens for type alias declaration."""
        pass
    
    def _visit_DataClassDeclaration(self, node: DataClassDeclaration) -> None:
        """Emit tokens for data class declaration."""
        pass
    
    def _visit_SealedTraitDeclaration(self, node: SealedTraitDeclaration) -> None:
        """Emit tokens for sealed trait declaration."""
        pass
    
    def _visit_LetBindingExpression(self, node: LetBindingExpression) -> None:
        """Emit tokens for let binding."""
        if node.value:
            self._visit(node.value)
            self._emit(SuperBitOpCode.STORE_VAR, node.name)
    
    def _visit_SafeCallExpression(self, node: SafeCallExpression) -> None:
        """Emit tokens for safe call (?.) expression."""
        self._visit(node.object)
        self._emit(SuperBitOpCode.SAFE_CALL, node.member)
        
        if node.is_call:
            for arg in node.arguments:
                self._visit(arg)
    
    def _visit_ElvisExpression(self, node: ElvisExpression) -> None:
        """Emit tokens for elvis (?:) expression."""
        self._visit(node.left)
        self._emit(SuperBitOpCode.ELVIS_CHECK)
        jump_idx = len(self.tokens)
        self._emit(SuperBitOpCode.JUMP_IF_FALSE, 0)
        
        self._visit(node.right)
        end_idx = len(self.tokens)
        self.tokens[jump_idx] = SuperBitIRToken(
            opcode=SuperBitOpCode.JUMP_IF_FALSE, operand=end_idx
        )
    
    def _visit_NotNullExpression(self, node: NotNullExpression) -> None:
        """Emit tokens for not-null assertion (!!)."""
        self._visit(node.value)
        self._emit(SuperBitOpCode.NOT_NULL_CHECK)

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
