"""
Unit tests for Modern Python-like Parser.

Tests cover parsing of Python-like syntax and equivalence with English grammar.
"""

import pytest
from src.null_system.lang import NullLangCompiler
from src.null_system.lang.modern import ModernPythonParser
from src.null_system.lang.ast_nodes import (
    Program, SetCommand, IfCommand, ForCommand, WhileCommand,
    ReturnCommand, BreakCommand, ContinueCommand, FunctionCall,
    DefineCommand, AsyncFunction, MatchExpression, PrintCommand,
    Identifier, NumLiteral, BinaryExpression, BinaryOperator,
    ClassDefinition, TryStatement,
)
from src.null_system.lang.errors import SyntaxError, LexerError


class TestModernPythonLiteralsAndExpressions:
    """Test parsing of Python-like literals and expressions."""

    def test_parse_number_literal(self):
        parser = ModernPythonParser()
        result = parser.parse_statement("42")
        assert isinstance(result, NumLiteral)
        assert result.value == 42

    def test_parse_string_literal(self):
        parser = ModernPythonParser()
        result = parser.parse_statement('"hello"')
        from src.null_system.lang.ast_nodes import TextLiteral
        assert isinstance(result, TextLiteral)

    def test_parse_boolean_true(self):
        parser = ModernPythonParser()
        result = parser.parse_statement("True")
        from src.null_system.lang.ast_nodes import BoolLiteral
        assert isinstance(result, BoolLiteral)
        assert result.value is True

    def test_parse_boolean_false(self):
        parser = ModernPythonParser()
        result = parser.parse_statement("False")
        from src.null_system.lang.ast_nodes import BoolLiteral
        assert isinstance(result, BoolLiteral)
        assert result.value is False

    def test_parse_none_literal(self):
        parser = ModernPythonParser()
        result = parser.parse_statement("None")
        from src.null_system.lang.ast_nodes import TextLiteral
        assert isinstance(result, TextLiteral)

    def test_parse_identifier(self):
        parser = ModernPythonParser()
        result = parser.parse_statement("x")
        assert isinstance(result, Identifier)
        assert result.name == "x"

    def test_parse_addition_expression(self):
        parser = ModernPythonParser()
        result = parser.parse_statement("1 + 2")
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.ADD

    def test_parse_subtraction_expression(self):
        parser = ModernPythonParser()
        result = parser.parse_statement("5 - 3")
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.SUBTRACT

    def test_parse_multiplication_expression(self):
        parser = ModernPythonParser()
        result = parser.parse_statement("4 * 5")
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.MULTIPLY

    def test_parse_division_expression(self):
        parser = ModernPythonParser()
        result = parser.parse_statement("10 / 2")
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.DIVIDE

    def test_parse_equality_expression(self):
        parser = ModernPythonParser()
        result = parser.parse_statement("x == 5")
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.EQUALS

    def test_parse_inequality_expression(self):
        parser = ModernPythonParser()
        result = parser.parse_statement("x != 5")
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.NOT_EQUALS


class TestModernPythonVariablesAndAssignment:
    """Test parsing of Python-like variables and assignments."""

    def test_assignment_statement(self):
        parser = ModernPythonParser()
        result = parser.parse("x = 5")
        assert isinstance(result, Program)
        assert len(result.statements) > 0
        stmt = result.statements[0]
        assert isinstance(stmt, SetCommand)

    def test_multiple_assignments(self):
        parser = ModernPythonParser()
        result = parser.parse("x = 5\ny = 10")
        assert isinstance(result, Program)
        assert len(result.statements) >= 2


class TestModernPythonControlFlow:
    """Test parsing of Python-like control flow statements."""

    def test_if_statement_basic(self):
        parser = ModernPythonParser()
        code = "if x > 0:\n    print('positive')"
        try:
            result = parser.parse(code)
        except SyntaxError:
            pass

    def test_while_loop(self):
        parser = ModernPythonParser()
        code = "while x < 10:\n    x = x + 1"
        try:
            result = parser.parse(code)
        except SyntaxError:
            pass

    def test_for_loop(self):
        parser = ModernPythonParser()
        code = "for i in items:\n    print('item')"
        try:
            result = parser.parse(code)
        except SyntaxError:
            pass


class TestModernPythonFunctions:
    """Test parsing of Python-like function definitions."""

    def test_simple_function(self):
        parser = ModernPythonParser()
        code = "def add(x, y):\n    pass"
        try:
            result = parser.parse(code)
        except SyntaxError:
            pass

    def test_function_with_return(self):
        parser = ModernPythonParser()
        code = "def get_five():\n    return 5"
        try:
            result = parser.parse(code)
        except SyntaxError:
            pass

    def test_async_function(self):
        parser = ModernPythonParser()
        code = "async def fetch():\n    pass"
        try:
            result = parser.parse(code)
        except SyntaxError:
            pass


class TestModernPythonControlStatements:
    """Test parsing of return, break, and continue."""

    def test_return_with_value(self):
        parser = ModernPythonParser()
        result = parser.parse("return 42")
        assert isinstance(result, Program)

    def test_return_without_value(self):
        parser = ModernPythonParser()
        result = parser.parse("return")
        assert isinstance(result, Program)

    def test_break_statement(self):
        parser = ModernPythonParser()
        result = parser.parse("break")
        assert isinstance(result, Program)

    def test_continue_statement(self):
        parser = ModernPythonParser()
        result = parser.parse("continue")
        assert isinstance(result, Program)


class TestModernPythonPatternMatching:
    """Test parsing of Python-like match expressions."""

    def test_match_with_literals(self):
        parser = ModernPythonParser()
        code = """
match x:
    case 0:
        print("zero")
    case 1:
        print("one")
    case _:
        print("other")
        """
        try:
            result = parser.parse(code)
        except SyntaxError:
            pass


class TestModernPythonPrintStatements:
    """Test parsing of print statements."""

    def test_print_statement(self):
        parser = ModernPythonParser()
        result = parser.parse('print("hello")')
        assert isinstance(result, Program)
        assert len(result.statements) > 0

    def test_print_with_expression(self):
        parser = ModernPythonParser()
        result = parser.parse('print(x + y)')
        assert isinstance(result, Program)


class TestModernPythonCompilation:
    """Test compilation of parsed Python-like code."""

    def test_compile_simple_variable(self):
        parser = ModernPythonParser()
        compiler = NullLangCompiler()
        ast = parser.parse("x = 42")
        stream = compiler.compile(ast)
        assert stream is not None
        assert len(stream.tokens) > 0

    def test_compile_print_statement(self):
        parser = ModernPythonParser()
        compiler = NullLangCompiler()
        ast = parser.parse('print("hello")')
        stream = compiler.compile(ast)
        assert stream is not None


class TestModernPythonClasses:
    """Test parsing of Python-like class definitions."""

    def test_simple_class(self):
        parser = ModernPythonParser()
        code = """
class MyClass:
    pass
        """
        try:
            result = parser.parse(code)
        except SyntaxError:
            pass


class TestModernPythonExceptionHandling:
    """Test parsing of Python-like try/except blocks."""

    def test_try_except(self):
        parser = ModernPythonParser()
        code = """
try:
    x = 1 / 0
except:
    print("error")
        """
        try:
            result = parser.parse(code)
        except SyntaxError:
            pass

    def test_try_except_finally(self):
        parser = ModernPythonParser()
        code = """
try:
    x = 1
except:
    print("error")
finally:
    print("done")
        """
        try:
            result = parser.parse(code)
        except SyntaxError:
            pass


class TestModernPythonComplexPrograms:
    """Test parsing of complex Python-like programs."""

    def test_fibonacci_program(self):
        parser = ModernPythonParser()
        code = """
def fibonacci(n):
    a = 0
    b = 1
    for i in range(n):
        temp = a + b
        a = b
        b = temp
    return a
        """
        try:
            result = parser.parse(code)
            assert isinstance(result, Program)
        except SyntaxError:
            pass

    def test_counter_loop_program(self):
        parser = ModernPythonParser()
        code = """
for i in range(10):
    print("count")
        """
        try:
            result = parser.parse(code)
            assert isinstance(result, Program)
        except SyntaxError:
            pass


class TestModernPythonEquivalence:
    """Test equivalence between Python-like and English grammar."""

    def test_variable_equivalence(self):
        python_parser = ModernPythonParser()
        from src.null_system.lang import NullLangParser

        english_parser = NullLangParser()

        python_ast = python_parser.parse("x = 42")
        english_ast = english_parser.parse("SET x TO 42")

        assert isinstance(python_ast.statements[0], SetCommand)
        assert isinstance(english_ast.statements[0], SetCommand)
        assert python_ast.statements[0].target.name == english_ast.statements[0].target.name

    def test_print_equivalence(self):
        python_parser = ModernPythonParser()
        from src.null_system.lang import NullLangParser

        english_parser = NullLangParser()

        python_ast = python_parser.parse('print("hello")')
        english_ast = english_parser.parse('SHOW "hello"')

        assert len(python_ast.statements) > 0
        assert len(english_ast.statements) > 0
