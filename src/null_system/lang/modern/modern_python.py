"""
Python-like Modern Parser for Null-Lang.

Provides a parser that understands Python-like syntax and emits Null-Lang AST nodes.
"""

import os
from typing import List, Optional
from lark import Lark, Token, Tree, Transformer
from lark.exceptions import LarkError, UnexpectedInput, UnexpectedCharacters

from ..ast_nodes import (
    ASTNode, Program, SourceSpan,
    TextLiteral, NumLiteral, BoolLiteral, ArrayLiteral, ObjectLiteral,
    Identifier,
    SetCommand, IfCommand, ForCommand, WhileCommand, ReturnCommand, BreakCommand, ContinueCommand,
    DefineCommand, FunctionCall, Comment,
    BinaryExpression, UnaryExpression, BinaryOperator, UnaryOperator,
    ClassDefinition, TryStatement, ExceptionHandler,
    PrintCommand,
)
from ..errors import SyntaxError, LexerError


class ModernPythonTransformer(Transformer):
    """Transforms Python-like parse tree into Null-Lang AST."""

    def __init__(self, source: str):
        super().__init__()
        self.source = source

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

    def none_literal(self, items):
        return TextLiteral(value="None")

    def literal(self, items):
        return items[0]

    def array_literal(self, items):
        elements = list(items)
        return ArrayLiteral(elements=elements)

    def dict_literal(self, items):
        pairs = [(pair[0], pair[1]) for pair in items]
        return ObjectLiteral(pairs=pairs)

    def dict_pair(self, items):
        key_item = items[0]
        if isinstance(key_item, Token):
            if key_item.type == 'ESCAPED_STRING':
                key = str(key_item)[1:-1]
            else:
                key = str(key_item)
        elif isinstance(key_item, Identifier):
            key = key_item.name
        else:
            key = str(key_item)

        value = items[1]
        return (key, value)

    def identifier(self, items):
        token = items[0]
        node = Identifier(name=str(token))
        node.span = self._get_span(token)
        return node

    # Comments
    def comment(self, items):
        token = items[0]
        text = str(token)
        if text.startswith('#'):
            text = text[1:].strip()
        node = Comment(text=text)
        node.span = self._get_span(token)
        return node

    # Variables and Assignment
    def py_assign(self, items):
        name = str(items[0])
        value = items[1]
        target = Identifier(name=name)
        return SetCommand(target=target, value=value)

    # Control Flow
    def if_stmt(self, items):
        condition = items[0]
        then_block = items[1] if isinstance(items[1], list) else [items[1]]
        else_block = None
        return IfCommand(condition=condition, then_block=then_block, else_block=else_block)

    def while_stmt(self, items):
        condition = items[0]
        body = items[1] if isinstance(items[1], list) else [items[1]]
        return WhileCommand(condition=condition, body=body)

    def for_stmt(self, items):
        var_name = str(items[0])
        iterable = items[1]
        body = items[2] if isinstance(items[2], list) else [items[2]]
        return ForCommand(variable=var_name, iterable=iterable, body=body)

    # Functions
    def fn_def(self, items):
        idx = 0
        name = str(items[idx])
        idx += 1

        params = []
        if idx < len(items) and isinstance(items[idx], list):
            params = items[idx]
            idx += 1

        body = items[idx] if idx < len(items) else []
        if not isinstance(body, list):
            body = [body]

        return DefineCommand(name=name, parameters=params, body=body)

    def param_list(self, items):
        return [str(item) for item in items]

    # Return/Break/Continue
    def return_stmt(self, items):
        value = items[0] if items else None
        return ReturnCommand(value=value)

    def break_stmt(self, items):
        return BreakCommand()

    def continue_stmt(self, items):
        return ContinueCommand()

    # Print
    def print_stmt(self, items):
        value = items[0] if items else TextLiteral(value="")
        return PrintCommand(value=value, with_newline=True)

    def argument_list(self, items):
        return items

    # Classes
    def class_def_stmt(self, items):
        name = str(items[0])
        body = items[1] if len(items) > 1 else []
        if not isinstance(body, list):
            body = [body]

        return ClassDefinition(name=name, base_classes=[], body=body)

    # Try/Except
    def try_stmt(self, items):
        body = items[0] if isinstance(items[0], list) else [items[0]]
        return TryStatement(body=body, handlers=[], finally_block=None)

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

    def not_expr(self, items):
        return UnaryExpression(operator=UnaryOperator.NOT, operand=items[0])

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

    def negate_expr(self, items):
        return UnaryExpression(operator=UnaryOperator.NEGATE, operand=items[0])

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
        return items[0]


class ModernPythonParser:
    """Parser for Python-like Modern Null-Lang syntax."""

    def __init__(self):
        grammar_path = os.path.join(
            os.path.dirname(__file__),
            'modern_python.lark'
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
        """Parse Python-like syntax and return a Program AST node."""
        try:
            tree = self.lark.parse(source)
            transformer = ModernPythonTransformer(source)
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
        """Parse a single Python-like statement."""
        try:
            # Wrap the statement in a program for parsing
            tree = self.lark.parse(source)
            transformer = ModernPythonTransformer(source)
            result = transformer.transform(tree)
            
            # Return the first statement if it's a program
            if isinstance(result, Program) and len(result.statements) > 0:
                return result.statements[0]
            return result
        except Exception as e:
            raise SyntaxError(message=str(e))
