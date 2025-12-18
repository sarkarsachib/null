"""
Rust AST Printer for Null-Lang.

Converts AST nodes back to Rust-like syntax with braces, semicolons,
and idiomatic Rust constructs.
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


class RustPrinter:
    """Prints AST nodes as Rust-like syntax."""
    
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
            return f"// @layer({annotation.layer})"
        elif isinstance(annotation, RequireAnnotation):
            return f"// @require({', '.join(annotation.layers)})"
        elif isinstance(annotation, PreferAnnotation):
            return f"// @prefer({', '.join(annotation.layers)})"
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
            return f"let {self._print_expression(statement.target)} = {self._print_expression(statement.value)};"
        elif isinstance(statement, AddCommand):
            operands_str = " + ".join(self._print_expression(op) for op in statement.operands)
            return f"{operands_str};"
        elif isinstance(statement, IfCommand):
            condition_str = self._print_expression(statement.condition)
            lines = [f"if {condition_str} {{"]
            
            self.indent_level += 1
            for stmt in statement.then_block:
                lines.append(self._print_statement(stmt))
            self.indent_level -= 1
            
            lines.append(f"{self.indent()}}}")
            
            if statement.else_block:
                lines.append(f"{self.indent()}else {{")
                self.indent_level += 1
                for stmt in statement.else_block:
                    lines.append(self._print_statement(stmt))
                self.indent_level -= 1
                lines.append(f"{self.indent()}}}")
            
            return "\n".join(lines)
        elif isinstance(statement, ShowCommand):
            return f"println!(\"{self._print_expression(statement.value)}\");"
        elif isinstance(statement, PrintCommand):
            return f"println!(\"{self._print_expression(statement.value)}\");"
        elif isinstance(statement, RepeatCommand):
            # Convert REPEAT n TIMES to a for loop
            return f"for _ in 0..{self._print_expression(statement.count)} {{"
        elif isinstance(statement, DefineCommand):
            params_str = ", ".join(statement.parameters)
            lines = [f"fn {statement.name}({params_str}) {{"]
            
            self.indent_level += 1
            for stmt in statement.body:
                lines.append(self._print_statement(stmt))
            self.indent_level -= 1
            
            lines.append(f"{self.indent()}}}")
            return "\n".join(lines)
        elif isinstance(statement, ForCommand):
            return f"for {statement.variable} in {self._print_expression(statement.iterable)} {{"
        elif isinstance(statement, WhileCommand):
            return f"while {self._print_expression(statement.condition)} {{"
        elif isinstance(statement, ReturnCommand):
            return f"return {self._print_expression(statement.value)};"
        elif isinstance(statement, BreakCommand):
            return "break;"
        elif isinstance(statement, ContinueCommand):
            return "continue;"
        elif isinstance(statement, MatchExpression):
            expr_str = self._print_expression(statement.expr)
            lines = [f"match {expr_str} {{"]
            
            for arm in statement.arms:
                pattern_str = self._print_pattern(arm.pattern)
                lines.append(f"{self.indent()}{pattern_str} => {{")
                self.indent_level += 1
                for stmt in arm.body:
                    lines.append(self._print_statement(stmt))
                self.indent_level -= 1
                lines.append(f"{self.indent()}}},")
            
            lines.append(f"{self.indent()}}}")
            return "\n".join(lines)
        elif isinstance(statement, BorrowCommand):
            mut_keyword = "mut " if statement.is_mutable else ""
            return f"let {mut_keyword}{statement.target.name} = &{statement.target.name};"
        elif isinstance(statement, AsyncFunction):
            params_str = ", ".join(statement.parameters)
            lines = [f"async fn {statement.name}({params_str}) {{"]
            
            self.indent_level += 1
            for stmt in statement.body:
                lines.append(self._print_statement(stmt))
            self.indent_level -= 1
            
            lines.append(f"{self.indent()}}}")
            return "\n".join(lines)
        elif isinstance(statement, AwaitExpression):
            return f"{self._print_expression(statement.value)}.await"
        elif isinstance(statement, ClassDefinition):
            # Rust doesn't have classes, convert to struct and impl
            lines = [f"struct {statement.name} {{"]
            
            self.indent_level += 1
            for stmt in statement.body:
                lines.append(self._print_statement(stmt))
            self.indent_level -= 1
            
            lines.append(f"{self.indent()}}}")
            return "\n".join(lines)
        elif isinstance(statement, TryStatement):
            # Rust uses ? operator for error handling, convert try/catch to Result handling
            lines = [f"// try {{"]
            
            self.indent_level += 1
            for stmt in statement.body:
                lines.append(self._print_statement(stmt))
            self.indent_level -= 1
            
            for handler in statement.handlers:
                exc_type = handler.exception_type if handler.exception_type else "any"
                lines.append(f"{self.indent()}}} catch({exc_type} {handler.var_name}) {{")
                self.indent_level += 1
                for stmt in handler.body:
                    lines.append(self._print_statement(stmt))
                self.indent_level -= 1
                lines.append(f"{self.indent()}}}")
            
            if statement.finally_block:
                lines.append(f"{self.indent()}finally {{")
                self.indent_level += 1
                for stmt in statement.finally_block:
                    lines.append(self._print_statement(stmt))
                self.indent_level -= 1
            
            lines.append(f"{self.indent()}}} // converted from try/catch")
            return "\n".join(lines)
        else:
            return f"// Unknown statement: {type(statement).__name__}"
    
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
            return f"// Unknown pattern: {type(pattern).__name__}"
    
    def _print_expression(self, expr) -> str:
        """Print an expression."""
        if isinstance(expr, TextLiteral):
            return f'"{expr.value}"'
        elif isinstance(expr, NumLiteral):
            return str(expr.value)
        elif isinstance(expr, BoolLiteral):
            return "true" if expr.value else "false"
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
                "AND": "&&",
                "OR": "||"
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
            return f"// Unknown expression: {type(expr).__name__}"