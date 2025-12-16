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
    FunctionCall, NullLibAnnotation, Comment,
    LayerAnnotation, RequireAnnotation, PreferAnnotation,
    SuperBitLiteral, MacroInvocation, SuperBitPattern, PatternArm, MatchCommand
)
from .compiler import NullLangCompiler, compile_program
from .errors import NullLangError, SyntaxError, SemanticError, LexerError
from .syntax_router import SyntaxMode, SyntaxAdvisor, ParserDispatcher, HybridParser, DiagnosticIssue
from .transpiler import to_english, to_modern

__all__ = [
    'NullLangParser', 'parse', 'parse_statement',
    'NullLangCompiler', 'compile_program',
    'ASTNode', 'Program', 'SourceSpan',
    'TextLiteral', 'NumLiteral', 'BoolLiteral', 'ArrayLiteral', 'ObjectLiteral',
    'Identifier', 'MemberAccess',
    'SetCommand', 'AddCommand', 'IfCommand', 'ShowCommand', 'RepeatCommand', 'DefineCommand',
    'BinaryExpression', 'UnaryExpression', 'ComparisonExpression',
    'BinaryOperator', 'UnaryOperator',
    'FunctionCall', 'NullLibAnnotation', 'Comment',
    'LayerAnnotation', 'RequireAnnotation', 'PreferAnnotation',
    'SuperBitLiteral', 'MacroInvocation', 'SuperBitPattern', 'PatternArm', 'MatchCommand',
    'NullLangError', 'SyntaxError', 'SemanticError', 'LexerError',
    'SyntaxMode', 'SyntaxAdvisor', 'ParserDispatcher', 'HybridParser', 'DiagnosticIssue',
    'to_english', 'to_modern',
]
