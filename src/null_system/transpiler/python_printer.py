"""
Python AST Printer for Null-Lang.

Converts AST nodes back to Python-like syntax with indentation,
colons, and Pythonic constructs.
"""

from typing import Dict, List
from ..lang.ast_nodes import (
    Program, SetCommand, AddCommand, IfCommand, ShowCommand, 
    RepeatCommand, DefineCommand, ForCommand, WhileCommand, 
    ReturnCommand, BreakCommand, ContinueCommand, MatchExpression,
    MemberAccess, Identifier, TextLiteral, NumLiteral, BoolLiteral,
    ArrayLiteral, BinaryExpression, UnaryExpression, FunctionCall,
    BorrowCommand, AsyncFunction, AwaitExpression, PrintCommand,
    ClassDefinition, TryStatement, LayerAnnotation, RequireAnnotation,
    PreferAnnotation
)


class PythonPrinter:
    """Prints AST nodes as Python-like syntax."""
    
    def __init__(self):
        self.indent_level = 0
        self.indent_size = 4
        
    def indent(self) -> str:
        """Return current indentation."""
        return " " * (self.indent_level * self.indent_size)
    
    def print_program(self, program: Program) -> str:
        """Print a complete program."""
        lines = []
        
        # Add layer annotations if present
        for annotation in program.annotations:
            lines.append(self._print_annotation(annotation))
            lines.append("")  # Empty line after annotations
        
        for statement in program.statements:
            lines.append(self._print_statement(statement))
        
        return "\n".join(lines)
    
    def _print_annotation(self, annotation) -> str:
        """Print a layer annotation."""
        if isinstance(annotation, LayerAnnotation):
            return f"# @layer({annotation.layer})"
        elif isinstance(annotation, RequireAnnotation):
            return f"# @require({', '.join(annotation.layers)})"
        elif isinstance(annotation, PreferAnnotation):
            return f"# @prefer({', '.join(annotation.layers)})"
        return ""
    
    def _print_statement(self, statement) -> str:
        """Print a single statement."""
        if hasattr(statement, 'annotations') and statement.annotations:
            # Print annotations first
            lines = []
            for annotation in statement.annotations:
                lines.append(f"{self.indent()}{self._print_annotation(annotation)}")
            lines.append(self._print_statement_without_annotations(statement))
            return "\n".join(lines)
        else:
            return self._print_statement_without_annotations(statement)
    
    def _print_statement_without_annotations(self, statement) -> str:
        """Print statement without annotations."""
        if isinstance(statement, SetCommand):
            return f"{self._print_expression(statement.target)} = {self._print_expression(statement.value)}"
        elif isinstance(statement, AddCommand):
            operands_str = " + ".join(self._print_expression(op) for op in statement.operands)
            return operands_str
        elif isinstance(statement, IfCommand):
            condition_str = self._print_expression(statement.condition)
            lines = [f"if {condition_str}:"]
            
            self.indent_level += 1
            for stmt in statement.then_block:
                lines.append(self._print_statement(stmt))
            self.indent_level -= 1
            
            if statement.else_block:
                lines.append(f"{self.indent()}else:")
                self.indent_level += 1
                for stmt in statement.else_block:
                    lines.append(self._print_statement(stmt))
                self.indent_level -= 1
            
            return "\n".join(lines)
        elif isinstance(statement, ShowCommand):
            return f"print({self._print_expression(statement.value)})"
        elif isinstance(statement, PrintCommand):
            return f"print({self._print_expression(statement.value)})"
        elif isinstance(statement, RepeatCommand):
            # Convert REPEAT n TIMES to a for loop
            return f"for _ in range({self._print_expression(statement.count)}):"
        elif isinstance(statement, DefineCommand):
            params_str = ", ".join(statement.parameters)
            lines = [f"def {statement.name}({params_str}):"]
            
            self.indent_level += 1
            for stmt in statement.body:
                lines.append(self._print_statement(stmt))
            self.indent_level -= 1
            
            return "\n".join(lines)
        elif isinstance(statement, ForCommand):
            return f"for {statement.variable} in {self._print_expression(statement.iterable)}:"
        elif isinstance(statement, WhileCommand):
            return f"while {self._print_expression(statement.condition)}:"
        elif isinstance(statement, ReturnCommand):
            return f"return {self._print_expression(statement.value)}"
        elif isinstance(statement, BreakCommand):
            return "break"
        elif isinstance(statement, ContinueCommand):
            return "continue"
        elif isinstance(statement, MatchExpression):
            # Python match is only in 3.10+, use if/elif chain
            expr_str = self._print_expression(statement.expr)
            lines = []
            
            for i, arm in enumerate(statement.arms):
                if i == 0:
                    lines.append(f"if {expr_str} == {self._print_pattern(arm.pattern)}:")
                else:
                    lines.append(f"{self.indent()}elif {expr_str} == {self._print_pattern(arm.pattern)}:")
                
                self.indent_level += 1
                for stmt in arm.body:
                    lines.append(self._print_statement(stmt))
                self.indent_level -= 1
            
            return "\n".join(lines)
        elif isinstance(statement, BorrowCommand):
            mut_keyword = "mut " if statement.is_mutable else ""
            return f"{mut_keyword}{statement.target.name} = {statement.target.name}  # borrowed reference"
        elif isinstance(statement, AsyncFunction):
            params_str = ", ".join(statement.parameters)
            lines = [f"async def {statement.name}({params_str}):"]
            
            self.indent_level += 1
            for stmt in statement.body:
                lines.append(self._print_statement(stmt))
            self.indent_level -= 1
            
            return "\n".join(lines)
        elif isinstance(statement, AwaitExpression):
            return f"await {self._print_expression(statement.value)}"
        elif isinstance(statement, ClassDefinition):
            lines = [f"class {statement.name}:"]
            
            self.indent_level += 1
            for stmt in statement.body:
                lines.append(self._print_statement(stmt))
            self.indent_level -= 1
            
            return "\n".join(lines)
        elif isinstance(statement, TryStatement):
            lines = [f"try:"]
            
            self.indent_level += 1
            for stmt in statement.body:
                lines.append(self._print_statement(stmt))
            self.indent_level -= 1
            
            for handler in statement.handlers:
                exc_type = handler.exception_type if handler.exception_type else "Exception"
                lines.append(f"{self.indent()}except {exc_type} as {handler.var_name}:")
                self.indent_level += 1
                for stmt in handler.body:
                    lines.append(self._print_statement(stmt))
                self.indent_level -= 1
            
            if statement.finally_block:
                lines.append(f"{self.indent()}finally:")
                self.indent_level += 1
                for stmt in statement.finally_block:
                    lines.append(self._print_statement(stmt))
                self.indent_level -= 1
            
            return "\n".join(lines)
        else:
            return f"# Unknown statement: {type(statement).__name__}"
    
    def _print_pattern(self, pattern) -> str:
        """Print a pattern."""
        from ..lang.ast_nodes import (
            WildcardPattern, LiteralPattern, IdentifierPattern
        )
        
        if isinstance(pattern, WildcardPattern):
            return "_"
        elif isinstance(pattern, LiteralPattern):
            return self._print_expression(pattern.value)
        elif isinstance(pattern, IdentifierPattern):
            return pattern.name
        else:
            return f"# Unknown pattern: {type(pattern).__name__}"
    
    def _print_expression(self, expr) -> str:
        """Print an expression."""
        if isinstance(expr, TextLiteral):
            return f"'{expr.value}'"
        elif isinstance(expr, NumLiteral):
            return str(expr.value)
        elif isinstance(expr, BoolLiteral):
            return "True" if expr.value else "False"
        elif isinstance(expr, ArrayLiteral):
            elements_str = ", ".join(self._print_expression(el) for el in expr.elements)
            return f"[{elements_str}]"
        elif isinstance(expr, Identifier):
            return expr.name
        elif isinstance(expr, MemberAccess):
            object_str = self._print_expression(expr.object)
            if expr.is_index:
                member_str = self._print_expression(expr.member)
                return f"{object_str}[{member_str}]"
            else:
                return f"{object_str}.{expr.member}"
        elif isinstance(expr, BinaryExpression):
            left_str = self._print_expression(expr.left)
            right_str = self._print_expression(expr.right)
            operator_map = {
                "ADD": "+",
                "SUBTRACT": "-", 
                "MULTIPLY": "*",
                "DIVIDE": "/",
                "EQUALS": "==",
                "NOT_EQUALS": "!=",
                "GREATER_THAN": ">",
                "LESS_THAN": "<",
                "GREATER_EQUAL": ">=",
                "LESS_EQUAL": "<=",
                "AND": "and",
                "OR": "or"
            }
            operator_str = operator_map.get(str(expr.operator), str(expr.operator))
            return f"({left_str} {operator_str} {right_str})"
        elif isinstance(expr, UnaryExpression):
            operand_str = self._print_expression(expr.operand)
            return f"{expr.operator}({operand_str})"
        elif isinstance(expr, FunctionCall):
            args_str = ", ".join(self._print_expression(arg) for arg in expr.arguments)
            return f"{expr.name}({args_str})"
        else:
            return f"# Unknown expression: {type(expr).__name__}"