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
    ForCommand, WhileCommand, ReturnCommand, BreakCommand, ContinueCommand,
    MatchExpression, MatchArm, Pattern, WildcardPattern, LiteralPattern, IdentifierPattern,
    BorrowCommand, AsyncFunction, AwaitExpression,
    TraitDefinition, TraitMethod, ImplBlock, ImplMethod,
    PrintCommand, ClassDefinition, TryStatement, ExceptionHandler
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
    'ForCommand', 'WhileCommand', 'ReturnCommand', 'BreakCommand', 'ContinueCommand',
    'MatchExpression', 'MatchArm', 'Pattern', 'WildcardPattern', 'LiteralPattern', 'IdentifierPattern',
    'BorrowCommand', 'AsyncFunction', 'AwaitExpression',
    'TraitDefinition', 'TraitMethod', 'ImplBlock', 'ImplMethod',
    'PrintCommand', 'ClassDefinition', 'TryStatement', 'ExceptionHandler',
    'NullLangError', 'SyntaxError', 'SemanticError', 'LexerError',
    'SyntaxMode', 'SyntaxAdvisor', 'ParserDispatcher', 'HybridParser', 'DiagnosticIssue',
    'to_english', 'to_modern',
]
