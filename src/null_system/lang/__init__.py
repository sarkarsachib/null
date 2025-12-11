"""
Null-Lang Parser Module

This module provides lexing, parsing, and AST construction for the Null-Lang
English-like programming language.
"""

from .parser import NullLangParser, parse, parse_statement
from .ast_nodes import (
    ASTNode, Program, SourceSpan,
    TextLiteral, NumLiteral, BoolLiteral, ArrayLiteral, ObjectLiteral,
    Identifier, MemberAccess,
    SetCommand, AddCommand, IfCommand, ShowCommand, RepeatCommand, DefineCommand,
    BinaryExpression, UnaryExpression, ComparisonExpression,
    BinaryOperator, UnaryOperator,
    FunctionCall, NullLibAnnotation, Comment
)
from .errors import NullLangError, SyntaxError, SemanticError, LexerError

__all__ = [
    'NullLangParser', 'parse', 'parse_statement',
    'ASTNode', 'Program', 'SourceSpan',
    'TextLiteral', 'NumLiteral', 'BoolLiteral', 'ArrayLiteral', 'ObjectLiteral',
    'Identifier', 'MemberAccess',
    'SetCommand', 'AddCommand', 'IfCommand', 'ShowCommand', 'RepeatCommand', 'DefineCommand',
    'BinaryExpression', 'UnaryExpression', 'ComparisonExpression',
    'BinaryOperator', 'UnaryOperator',
    'FunctionCall', 'NullLibAnnotation', 'Comment',
    'NullLangError', 'SyntaxError', 'SemanticError', 'LexerError'
]
