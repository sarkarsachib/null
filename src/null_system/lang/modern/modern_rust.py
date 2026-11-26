"""
Rust-like Modern Parser for Null-Lang.

Provides a parser that understands Rust-like syntax and emits Null-Lang AST nodes.
"""

import os
from typing import List, Optional, Union
from lark import Lark, Token, Tree, Transformer
from lark.exceptions import LarkError, UnexpectedInput, UnexpectedCharacters

from ..ast_nodes import (
    ASTNode, Program, SourceSpan,
    TextLiteral, NumLiteral, BoolLiteral, ArrayLiteral,
    Identifier,
    SetCommand, IfCommand, ForCommand, WhileCommand, ReturnCommand, BreakCommand, ContinueCommand,
    DefineCommand, FunctionCall, Comment,
    BinaryExpression, UnaryExpression, BinaryOperator, UnaryOperator,
    MatchExpression, MatchArm, LiteralPattern, WildcardPattern,
    PrintCommand,
)
from ..errors import SyntaxError, LexerError


def _flatten_block(item):
    """Flatten a parsed block (possibly nested lists) into statements."""
    if item is None:
        return []
    if isinstance(item, list):
        flat = []
        for entry in item:
            flat.extend(_flatten_block(entry))
        return flat
    return [item]


class ModernRustTransformer(Transformer):
    """Transforms Rust-like parse tree into Null-Lang AST."""

    def __init__(self, source: str):
        super().__init__()
        self.source = source

    def _call_userfunc(self, tree, new_children=None):
        """Attach the parse-tree span to every node the rule built.

        The rule methods construct AST nodes by hand, so without this the spans
        Lark already computed (propagate_positions is on) are thrown away and
        runtime errors cannot name a source line.
        """
        node = super()._call_userfunc(tree, new_children)
        if isinstance(node, ASTNode) and getattr(node, "span", None) is None:
            meta = getattr(tree, "meta", None)
            if meta is not None and not getattr(meta, "empty", True):
                node.span = self._get_span(meta)
        return node

    def _get_span(self, meta) -> SourceSpan:
        """Extract source span from Lark meta information."""
        from ..ast_nodes import SyntaxMode
        if hasattr(meta, 'line') and hasattr(meta, 'column'):
            text = getattr(meta, 'value', '')
            end_line = meta.line
            end_col = meta.column + len(str(text))
            return SourceSpan(meta.line, meta.column, end_line, end_col, str(text), syntax_mode=SyntaxMode.modern)
        elif hasattr(meta, 'start_pos') and hasattr(meta, 'end_pos'):
            lines = self.source[:meta.start_pos].split('\n')
            start_line = len(lines)
            start_col = len(lines[-1]) + 1 if lines else 1

            lines = self.source[:meta.end_pos].split('\n')
            end_line = len(lines)
            end_col = len(lines[-1]) + 1 if lines else 1

            text = self.source[meta.start_pos:meta.end_pos]
            return SourceSpan(start_line, start_col, end_line, end_col, text, syntax_mode=SyntaxMode.modern)
        return SourceSpan(0, 0, 0, 0, syntax_mode=SyntaxMode.modern)

    # Program
    def program(self, items):
        statements = [item for item in items if item is not None]
        return Program(statements=statements)

    # Literals
    def text_literal(self, items):
        token = items[0]
        value = str(token)[1:-1]
        value = (
            value.replace('\\n', '\n')
            .replace('\\t', '\t')
            .replace('\\"', '"')
            .replace("\\'", "'")
            .replace('\\\\', '\\')
        )
        node = TextLiteral(value=value)
        node.span = self._get_span(token)
        return node

    def string_literal(self, items):
        return self.text_literal(items)

    def num_literal(self, items):
        token = items[0]
        value = float(token) if '.' in str(token) else int(token)
        node = NumLiteral(value=value)
        node.span = self._get_span(token)
        return node

    def number_literal(self, items):
        return self.num_literal(items)

    def bool_literal_true(self, items):
        return BoolLiteral(value=True)

    def bool_literal_false(self, items):
        return BoolLiteral(value=False)

    def literal(self, items):
        return items[0]

    def array_literal(self, items):
        elements = list(items)
        return ArrayLiteral(elements=elements)

    def identifier(self, items):
        token = items[0]
        node = Identifier(name=str(token))
        node.span = self._get_span(token)
        return node

    # Comments
    def comment(self, items):
        token = items[0]
        text = str(token)
        if text.startswith('//'):
            text = text[2:].strip()
        elif text.startswith('/*'):
            text = text[2:-2].strip()
        node = Comment(text=text)
        node.span = self._get_span(token)
        return node

    # Variables and Assignment
    def let_stmt(self, items):
        name = str(items[0])
        value = items[1]
        target = Identifier(name=name)
        cmd = SetCommand(target=target, value=value)
        return cmd

    def assign_stmt(self, items):
        name = str(items[0])
        value = items[1]
        target = Identifier(name=name)
        cmd = SetCommand(target=target, value=value)
        return cmd

    # Control Flow
    def if_stmt(self, items):
        condition = items[0]
        then_block = []
        else_block = None
        for item in items[1:]:
            if isinstance(item, list):
                else_block = self._block(item)
            elif item is not None:
                then_block.append(item)

        cmd = IfCommand(condition=condition, then_block=then_block, else_block=else_block)
        return cmd

    def else_block(self, items):
        return items

    def _block(self, item):
        """Flatten a block into a list of statements."""
        return _flatten_block(item)

    def while_stmt(self, items):
        condition = items[0]
        body = []
        for item in items[1:]:
            body.extend(self._block(item))
        cmd = WhileCommand(condition=condition, body=body)
        return cmd

    def for_stmt(self, items):
        var_name = str(items[0])
        iterable = items[1]
        body = items[2] if isinstance(items[2], list) else [items[2]]
        cmd = ForCommand(variable=var_name, iterable=iterable, body=body)
        return cmd

    # Functions
    def fn_def(self, items):
        idx = 0
        name = str(items[idx])
        idx += 1

        params = []
        if idx < len(items) and isinstance(items[idx], list):
            params = items[idx]
            idx += 1

        body = []
        while idx < len(items):
            item = items[idx]
            if isinstance(item, list):
                body.extend(item)
            elif isinstance(item, Token):
                # return type annotation ("-> Type")
                pass
            else:
                body.append(item)
            idx += 1

        cmd = DefineCommand(name=name, parameters=params, body=body)
        return cmd

    def param(self, items):
        return str(items[0])

    def param_list(self, items):
        return [str(item) for item in items]

    # Return/Break/Continue
    def return_stmt(self, items):
        value = items[0] if items else None
        cmd = ReturnCommand(value=value)
        return cmd

    def break_stmt(self, items):
        cmd = BreakCommand()
        return cmd

    def continue_stmt(self, items):
        cmd = ContinueCommand()
        return cmd

    # Print
    def println_stmt(self, items):
        value = items[0] if items else TextLiteral(value="")
        cmd = PrintCommand(value=value, with_newline=True)
        return cmd

    def print_stmt(self, items):
        value = items[0] if items else TextLiteral(value="")
        cmd = PrintCommand(value=value, with_newline=False)
        return cmd

    def argument_list(self, items):
        return items

    # Match
    def match_stmt(self, items):
        expr = items[0]
        arms = items[1:] if len(items) > 1 else []
        cmd = MatchExpression(expr=expr, arms=arms)
        return cmd

    def match_arm_expr(self, items):
        pattern = items[0]
        body = items[1] if isinstance(items[1], list) else [items[1]]
        return MatchArm(pattern=pattern, body=body)

    # Expressions
    def or_expr(self, items):
        left = items[0]
        for right in items[1:]:
            left = BinaryExpression(operator=BinaryOperator.OR, left=left, right=right)
        return left

    def and_expr(self, items):
        left = items[0]
        for right in items[1:]:
            left = BinaryExpression(operator=BinaryOperator.AND, left=left, right=right)
        return left

    def eq_expr(self, items):
        return BinaryExpression(operator=BinaryOperator.EQUALS, left=items[0], right=items[1])

    def neq_expr(self, items):
        return BinaryExpression(operator=BinaryOperator.NOT_EQUALS, left=items[0], right=items[1])

    def lt_expr(self, items):
        return BinaryExpression(operator=BinaryOperator.LESS_THAN, left=items[0], right=items[1])

    def gt_expr(self, items):
        return BinaryExpression(operator=BinaryOperator.GREATER_THAN, left=items[0], right=items[1])

    def le_expr(self, items):
        return BinaryExpression(operator=BinaryOperator.LESS_EQUAL, left=items[0], right=items[1])

    def ge_expr(self, items):
        return BinaryExpression(operator=BinaryOperator.GREATER_EQUAL, left=items[0], right=items[1])

    def add_expr(self, items):
        return BinaryExpression(operator=BinaryOperator.ADD, left=items[0], right=items[1])

    def sub_expr(self, items):
        return BinaryExpression(operator=BinaryOperator.SUBTRACT, left=items[0], right=items[1])

    def mul_expr(self, items):
        return BinaryExpression(operator=BinaryOperator.MULTIPLY, left=items[0], right=items[1])

    def div_expr(self, items):
        return BinaryExpression(operator=BinaryOperator.DIVIDE, left=items[0], right=items[1])

    def not_expr(self, items):
        return UnaryExpression(operator=UnaryOperator.NOT, operand=items[0])

    def negate_expr(self, items):
        return UnaryExpression(operator=UnaryOperator.NEGATE, operand=items[0])

    def index_expr(self, items):
        from ..ast_nodes import MemberAccess
        return MemberAccess(object=items[0], member=items[1], is_index=True)

    def property_access(self, items):
        obj = items[0]
        member = str(items[1]) if isinstance(items[1], Token) else items[1].name if isinstance(items[1], Identifier) else str(items[1])
        from ..ast_nodes import MemberAccess
        return MemberAccess(object=obj, member=member, is_index=False)

    def call_expr(self, items):
        func_name = str(items[0]) if isinstance(items[0], Token) else items[0].name if isinstance(items[0], Identifier) else str(items[0])
        args = items[1] if len(items) > 1 and isinstance(items[1], list) else []
        return FunctionCall(name=func_name, arguments=args)

    def function_call(self, items):
        name = str(items[0]) if isinstance(items[0], Token) else items[0].name if isinstance(items[0], Identifier) else str(items[0])
        args = items[1] if len(items) > 1 and isinstance(items[1], list) else []
        return FunctionCall(name=name, arguments=args)

    def expression_statement(self, items):
        return items[0] if items else None


class ModernRustParser:
    """Parser for Rust-like Modern Null-Lang syntax."""

    def __init__(self):
        grammar_path = os.path.join(
            os.path.dirname(__file__),
            'modern_rust.lark'
        )
        with open(grammar_path, 'r') as f:
            grammar = f.read()

        self.lark = Lark(
            grammar,
            start='program',
            parser='lalr',
            transformer=None,
            propagate_positions=True,
        )

    def parse(self, source: str) -> Program:
        """Parse Rust-like syntax and return a Program AST node."""
        try:
            tree = self.lark.parse(source)
            transformer = ModernRustTransformer(source)
            return transformer.transform(tree)
        except UnexpectedCharacters as e:
            raise LexerError(
                message=f"Unexpected character: {e.char}",
                span=SourceSpan(e.line, e.column, e.line, e.column + 1)
            )
        except UnexpectedInput as e:
            raise SyntaxError(
                message=f"Unexpected input: {e}",
                span=SourceSpan(e.line, e.column, e.line, e.column + 1)
            )
        except Exception as e:
            raise SyntaxError(message=str(e))

    def parse_statement(self, source: str) -> ASTNode:
        """Parse a single Rust-like statement."""
        try:
            # Wrap the statement in a program for parsing
            # Only add semicolon if it's not a block statement and doesn't already have one
            stripped = source.strip()
            wrapped_source = source
            if not (stripped.endswith('}') or stripped.endswith(';') or not stripped):
                wrapped_source = source + ';'
                
            tree = self.lark.parse(wrapped_source)
            transformer = ModernRustTransformer(wrapped_source)
            result = transformer.transform(tree)
            
            # Return the first statement if it's a program
            if isinstance(result, Program) and len(result.statements) > 0:
                return result.statements[0]
            return result
        except Exception as e:
            raise SyntaxError(message=str(e))
