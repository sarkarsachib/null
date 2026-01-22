"""
Null-Lang Parser implementation using Lark.

Provides lexing, parsing, and AST construction for Null-Lang source code.
"""

import os
from typing import List, Union
from lark import Lark, Token, Tree, Transformer
from lark.exceptions import LarkError, UnexpectedInput, UnexpectedCharacters

from .ast_nodes import (
    ASTNode, Program, SourceSpan,
    TextLiteral, NumLiteral, BoolLiteral, ArrayLiteral, ObjectLiteral,
    Identifier, MemberAccess,
    SetCommand, AddCommand, IfCommand, ShowCommand, InputCommand,
    FileReadCommand, FileWriteCommand, FileExistsCommand, ListFilesCommand,
    RepeatCommand, DefineCommand, ReturnCommand,
    BinaryExpression, UnaryExpression, ComparisonExpression, BinaryOperator, UnaryOperator,
    FunctionCall, NullLibAnnotation, Comment,
    LayerAnnotation, RequireAnnotation, PreferAnnotation,
    ModuleDeclaration, ImportStatement, QualifiedIdentifier,
    TypeAnnotation, TypeAliasDeclaration, DataClassDeclaration, SealedTraitDeclaration,
    SafeCallExpression, ElvisExpression, NotNullExpression, LetBindingExpression,
)
from .errors import SyntaxError, LexerError


class NullLangTransformer(Transformer):
    """Transforms Lark parse tree into Null-Lang AST."""
    
    def __init__(self, source: str):
        super().__init__()
        self.source = source
    
    def _get_span(self, meta) -> SourceSpan:
        """Extract source span from Lark meta information."""
        from .ast_nodes import SyntaxMode
        if hasattr(meta, 'line') and hasattr(meta, 'column'):
            # For tokens
            text = getattr(meta, 'value', '')
            end_line = meta.line
            end_col = meta.column + len(str(text))
            return SourceSpan(meta.line, meta.column, end_line, end_col, str(text), syntax_mode=SyntaxMode.english)
        elif hasattr(meta, 'start_pos') and hasattr(meta, 'end_pos'):
            # For tree nodes
            lines = self.source[:meta.start_pos].split('\n')
            start_line = len(lines)
            start_col = len(lines[-1]) + 1 if lines else 1
            
            lines = self.source[:meta.end_pos].split('\n')
            end_line = len(lines)
            end_col = len(lines[-1]) + 1 if lines else 1
            
            text = self.source[meta.start_pos:meta.end_pos]
            return SourceSpan(start_line, start_col, end_line, end_col, text, syntax_mode=SyntaxMode.english)
        return SourceSpan(0, 0, 0, 0, syntax_mode=SyntaxMode.english)
    
    # Program
    
    def program(self, items):
        module_declaration = None
        imports = []
        statements = []
        
        for item in items:
            if item is None:
                continue
            elif isinstance(item, ModuleDeclaration):
                module_declaration = item
            elif isinstance(item, list) and len(item) > 0 and isinstance(item[0], ImportStatement):
                imports.extend(item)
            elif isinstance(item, ImportStatement):
                imports.append(item)
            else:
                statements.append(item)
        
        return Program(
            module_declaration=module_declaration,
            imports=imports,
            statements=statements
        )
    
    # Module System
    
    def module_header(self, items):
        module_name = items[0]
        return ModuleDeclaration(name=module_name)
    
    def import_section(self, items):
        return list(items)
    
    def import_statement(self, items):
        annotations = []
        module_name = None
        alias = None
        
        for item in items:
            if isinstance(item, (LayerAnnotation, RequireAnnotation, PreferAnnotation)):
                annotations.append(item)
            elif isinstance(item, QualifiedIdentifier):
                module_name = item
            elif isinstance(item, Identifier):
                if module_name is None:
                    module_name = QualifiedIdentifier(parts=[item.name])
                else:
                    alias = item.name
        
        return ImportStatement(
            module_name=module_name,
            alias=alias,
            annotations=annotations
        )
    
    def module_name(self, items):
        parts = [str(token) for token in items]
        node = QualifiedIdentifier(parts=parts)
        if items:
            node.span = self._get_span(items[0])
        return node
    
    def qualified_name(self, items):
        parts = [str(token) for token in items]
        node = QualifiedIdentifier(parts=parts)
        if items:
            node.span = self._get_span(items[0])
        return node
    
    # Literals
    
    def text_literal(self, items):
        token = items[0]
        # Remove quotes
        value = str(token)[1:-1]
        # Handle escape sequences
        value = value.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
        node = TextLiteral(value=value)
        node.span = self._get_span(token)
        return node
    
    def num_literal(self, items):
        token = items[0]
        value = float(token) if '.' in str(token) else int(token)
        node = NumLiteral(value=value)
        node.span = self._get_span(token)
        return node
    
    def true_literal(self, items):
        return BoolLiteral(value=True)
    
    def false_literal(self, items):
        return BoolLiteral(value=False)
    
    def literal(self, items):
        return items[0]
    
    def array_literal(self, items):
        elements = list(items)
        return ArrayLiteral(elements=elements)
    
    def object_literal(self, items):
        pairs = [(pair[0], pair[1]) for pair in items]
        return ObjectLiteral(pairs=pairs)
    
    def object_pair(self, items):
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
    
    # Identifiers
    
    def identifier(self, items):
        token = items[0]
        node = Identifier(name=str(token))
        node.span = self._get_span(token)
        return node
    
    # Member Access
    
    def property_access(self, items):
        obj = items[0]
        prop = items[1]
        return MemberAccess(object=obj, member=prop.name if isinstance(prop, Identifier) else str(prop), is_index=False)
    
    def index_access(self, items):
        obj = items[0]
        index = items[1]
        return MemberAccess(object=obj, member=index, is_index=True)
    
    # Commands
    
    def target(self, items):
        return items[0]
    
    def set_cmd(self, items):
        target = items[0]
        value = items[1]
        return SetCommand(target=target, value=value)
    
    def add_cmd(self, items):
        return AddCommand(operands=list(items))
    
    def if_cmd(self, items):
        condition = items[0]
        then_block = items[1] if isinstance(items[1], list) else [items[1]]
        else_block = None
        if len(items) > 2:
            else_block = items[2] if isinstance(items[2], list) else [items[2]]
        return IfCommand(condition=condition, then_block=then_block, else_block=else_block)
    
    def show_cmd(self, items):
        return ShowCommand(value=items[0])

    def input_cmd(self, items):
        variable = items[0].name if isinstance(items[0], Identifier) else str(items[0])
        prompt = items[1] if len(items) > 1 else None
        return InputCommand(variable=variable, prompt=prompt)

    def read_file_cmd(self, items):
        target = items[0].name if isinstance(items[0], Identifier) else str(items[0])
        path = items[1]
        return FileReadCommand(path=path, target=target)

    def write_file_cmd(self, items):
        path = items[0]
        content = items[1]
        return FileWriteCommand(path=path, content=content)

    def file_exists_cmd(self, items):
        target = items[0].name if isinstance(items[0], Identifier) else str(items[0])
        path = items[1]
        return FileExistsCommand(path=path, target=target)

    def list_files_cmd(self, items):
        target = items[0].name if isinstance(items[0], Identifier) else str(items[0])
        path = items[1]
        return ListFilesCommand(path=path, target=target)

    def repeat_cmd(self, items):
        count = items[0]
        body = items[1] if isinstance(items[1], list) else [items[1]]
        return RepeatCommand(count=count, body=body)
    
    def define_cmd(self, items):
        name = items[0].name if isinstance(items[0], Identifier) else str(items[0])
        
        # Check if we have parameters
        param_idx = 1
        parameters = []
        if param_idx < len(items) and isinstance(items[param_idx], list) and all(isinstance(p, Identifier) for p in items[param_idx]):
            parameters = [p.name for p in items[param_idx]]
            param_idx += 1
        
        body = []
        if param_idx < len(items):
            body = items[param_idx] if isinstance(items[param_idx], list) else [items[param_idx]]
        
        return DefineCommand(name=name, parameters=parameters, body=body)
    
    def return_cmd(self, items):
        return ReturnCommand(value=items[0])
    
    def block(self, items):
        return list(items)
    
    def parameter_list(self, items):
        return list(items)
    
    def argument_list(self, items):
        return list(items)
    
    # Expressions
    
    def or_expression(self, items):
        result = items[0]
        for item in items[1:]:
            result = BinaryExpression(operator=BinaryOperator.OR, left=result, right=item)
        return result
    
    def and_expression(self, items):
        result = items[0]
        for item in items[1:]:
            result = BinaryExpression(operator=BinaryOperator.AND, left=result, right=item)
        return result
    
    def not_expr(self, items):
        return UnaryExpression(operator=UnaryOperator.NOT, operand=items[0])
    
    def comparison_expression(self, items):
        left = items[0]
        operator = items[1]
        right = items[2]
        return ComparisonExpression(left=left, operator=operator, right=right)
    
    def is_equal(self, items):
        return "IS"
    
    def is_not(self, items):
        return "IS NOT"
    
    def is_greater(self, items):
        return "IS GREATER THAN"
    
    def is_less(self, items):
        return "IS LESS THAN"
    
    def is_greater_equal(self, items):
        return "IS GREATER OR EQUAL TO"
    
    def is_less_equal(self, items):
        return "IS LESS OR EQUAL TO"
    
    def equals(self, items):
        return "EQUALS"
    
    def not_equals(self, items):
        return "NOT EQUALS"
    
    def add_expr(self, items):
        return BinaryExpression(operator=BinaryOperator.ADD, left=items[0], right=items[1])
    
    def subtract_expr(self, items):
        return BinaryExpression(operator=BinaryOperator.SUBTRACT, left=items[0], right=items[1])
    
    def multiply_expr(self, items):
        return BinaryExpression(operator=BinaryOperator.MULTIPLY, left=items[0], right=items[1])
    
    def divide_expr(self, items):
        return BinaryExpression(operator=BinaryOperator.DIVIDE, left=items[0], right=items[1])
    
    def negate_expr(self, items):
        return UnaryExpression(operator=UnaryOperator.NEGATE, operand=items[0])
    
    # Function Calls
    
    def call_func(self, items):
        if isinstance(items[0], Identifier):
            name = items[0].name
        elif isinstance(items[0], QualifiedIdentifier):
            name = items[0].full_name
        else:
            name = str(items[0])
        arguments = []
        if len(items) > 1:
            arguments = items[1] if isinstance(items[1], list) else [items[1]]
        return FunctionCall(name=name, arguments=arguments)
    
    def call_func_parens(self, items):
        if isinstance(items[0], Identifier):
            name = items[0].name
        elif isinstance(items[0], QualifiedIdentifier):
            name = items[0].full_name
        else:
            name = str(items[0])
        arguments = []
        if len(items) > 1:
            arguments = items[1] if isinstance(items[1], list) else [items[1]]
        return FunctionCall(name=name, arguments=arguments)
    
    # Null-Lib Annotations
    
    def null_lib_call(self, items):
        lib_name = items[0].name if isinstance(items[0], Identifier) else str(items[0])
        function = items[1].name if isinstance(items[1], Identifier) else str(items[1])
        arguments = []
        if len(items) > 2:
            arguments = items[2] if isinstance(items[2], list) else [items[2]]
        return NullLibAnnotation(lib_name=lib_name, function=function, arguments=arguments)
    
    # Annotations
    
    def annotation(self, items):
        return items[0]
    
    def make_layer_annotation(self, items):
        layer_name = items[0].name if isinstance(items[0], Identifier) else str(items[0])
        return LayerAnnotation(layer=layer_name)
    
    def make_require_annotation(self, items):
        layers = []
        for item in items:
            if isinstance(item, Identifier):
                layers.append(item.name)
            elif isinstance(item, list):
                layers.extend([id.name if isinstance(id, Identifier) else str(id) for id in item])
        return RequireAnnotation(layers=layers)
    
    def make_prefer_annotation(self, items):
        layers = []
        for item in items:
            if isinstance(item, Identifier):
                layers.append(item.name)
            elif isinstance(item, list):
                layers.extend([id.name if isinstance(id, Identifier) else str(id) for id in item])
        return PreferAnnotation(layers=layers)
    
    def identifier_list(self, items):
        return items
    
    def attach_annotations(self, items):
        annotations = []
        base_stmt = None
        
        for item in items:
            if isinstance(item, (LayerAnnotation, RequireAnnotation, PreferAnnotation)):
                annotations.append(item)
            elif isinstance(item, list):
                for sub_item in item:
                    if isinstance(sub_item, (LayerAnnotation, RequireAnnotation, PreferAnnotation)):
                        annotations.append(sub_item)
                    else:
                        base_stmt = sub_item
            else:
                base_stmt = item
        
        if base_stmt is not None:
            if hasattr(base_stmt, 'annotations'):
                base_stmt.annotations = annotations
        
        return base_stmt if base_stmt is not None else annotations
    
    # Statements
    
    def expression_statement(self, items):
        return items[0]
    
    def comment(self, items):
        token = items[0]
        text = str(token)[1:].strip()  # Remove # and strip whitespace
        node = Comment(text=text)
        node.span = self._get_span(token)
        return node
    
    # Type System
    
    def parse_type_annotation(self, items):
        type_name = items[0].name if isinstance(items[0], Identifier) else str(items[0])
        is_nullable = False
        type_parameters = []
        
        for item in items[1:]:
            if isinstance(item, list):
                type_parameters = item
            elif item == "?":
                is_nullable = True
        
        return TypeAnnotation(
            type_name=type_name,
            is_nullable=is_nullable,
            type_parameters=type_parameters
        )
    
    def make_type_alias(self, items):
        name = items[0].name if isinstance(items[0], Identifier) else str(items[0])
        target_type = items[1]
        return TypeAliasDeclaration(name=name, target_type=target_type)
    
    def make_data_class(self, items):
        name = items[0].name if isinstance(items[0], Identifier) else str(items[0])
        fields = items[1] if isinstance(items[1], list) else [items[1]]
        return DataClassDeclaration(name=name, fields=fields)
    
    def make_sealed_trait(self, items):
        name = items[0].name if isinstance(items[0], Identifier) else str(items[0])
        type_params = []
        variants = []
        
        for item in items[1:]:
            if isinstance(item, list):
                if item and isinstance(item[0], str):
                    type_params = item
                else:
                    variants = item
        
        return SealedTraitDeclaration(
            name=name,
            type_parameters=type_params,
            variants=variants
        )
    
    def make_let_binding(self, items):
        name = items[0].name if isinstance(items[0], Identifier) else str(items[0])
        type_annotation = None
        value = None
        
        for item in items[1:]:
            if isinstance(item, TypeAnnotation):
                type_annotation = item
            else:
                value = item
        
        return LetBindingExpression(
            name=name,
            type_annotation=type_annotation,
            value=value
        )
    
    def field_list(self, items):
        return list(items)
    
    def field_decl(self, items):
        name = items[0].name if isinstance(items[0], Identifier) else str(items[0])
        type_annotation = items[1]
        return (name, type_annotation)
    
    def generic_params(self, items):
        return [str(item.name) if isinstance(item, Identifier) else str(item) for item in items]
    
    def variant_list(self, items):
        return list(items)
    
    def variant_decl(self, items):
        name = items[0].name if isinstance(items[0], Identifier) else str(items[0])
        type_annotation = items[1] if len(items) > 1 else None
        return (name, type_annotation)
    
    # Null-Safety Operators
    
    def safe_call_property(self, items):
        obj = items[0]
        member = items[1].name if isinstance(items[1], Identifier) else str(items[1])
        return SafeCallExpression(object=obj, member=member, is_call=False)
    
    def safe_call_index(self, items):
        obj = items[0]
        index = items[1]
        return SafeCallExpression(object=obj, member=index, is_call=False)
    
    def safe_call_method(self, items):
        obj = items[0]
        arguments = []
        if len(items) > 1:
            arguments = items[1] if isinstance(items[1], list) else [items[1]]
        method_name = getattr(obj, 'name', str(obj))
        return SafeCallExpression(
            object=obj,
            member=method_name,
            is_call=True,
            arguments=arguments
        )
    
    def make_elvis(self, items):
        left = items[0]
        right = items[1]
        return ElvisExpression(left=left, right=right)
    
    def make_not_null(self, items):
        value = items[0]
        return NotNullExpression(value=value)


class NullLangParser:
    """Main parser for Null-Lang."""
    
    def __init__(self):
        grammar_path = os.path.join(os.path.dirname(__file__), 'grammar.lark')
        with open(grammar_path, 'r') as f:
            grammar = f.read()
        
        self.lark_parser = Lark(grammar, parser='lalr', start='program', 
                                propagate_positions=True, maybe_placeholders=False)
    
    def parse(self, source: str) -> Program:
        """
        Parse Null-Lang source code into an AST.
        
        Args:
            source: The source code to parse
            
        Returns:
            A Program AST node
            
        Raises:
            SyntaxError: If the source contains syntax errors
            LexerError: If the source contains lexical errors
        """
        try:
            tree = self.lark_parser.parse(source)
            transformer = NullLangTransformer(source)
            ast = transformer.transform(tree)
            return ast
        except UnexpectedCharacters as e:
            span = SourceSpan(e.line, e.column, e.line, e.column + 1)
            raise LexerError(f"Unexpected character: {e.char!r}", span, source)
        except UnexpectedInput as e:
            span = SourceSpan(e.line, e.column, e.line, e.column + 1)
            expected = ', '.join(e.expected) if hasattr(e, 'expected') else 'valid syntax'
            raise SyntaxError(f"Unexpected input. Expected: {expected}", span, source)
        except LarkError as e:
            raise SyntaxError(str(e), None, source)
    
    def parse_statement(self, source: str) -> ASTNode:
        """
        Parse a single statement.
        
        Args:
            source: The statement source code
            
        Returns:
            An AST node representing the statement
        """
        program = self.parse(source)
        if not program.statements:
            raise SyntaxError("No statement found", None, source)
        return program.statements[0]
    
    def parse_expression(self, source: str) -> ASTNode:
        """
        Parse a single expression.
        
        Args:
            source: The expression source code
            
        Returns:
            An AST node representing the expression
        """
        statement = self.parse_statement(source)
        return statement


def parse(source: str) -> Program:
    """
    Convenience function to parse Null-Lang source code.
    
    Args:
        source: The source code to parse
        
    Returns:
        A Program AST node
    """
    parser = NullLangParser()
    return parser.parse(source)


def parse_statement(source: str) -> ASTNode:
    """
    Convenience function to parse a single Null-Lang statement.
    
    Args:
        source: The statement source code
        
    Returns:
        An AST node representing the statement
    """
    parser = NullLangParser()
    return parser.parse_statement(source)
