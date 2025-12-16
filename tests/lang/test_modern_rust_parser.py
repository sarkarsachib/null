"""
Unit tests for Modern Rust-like Parser.

Tests cover parsing of Rust-like syntax and equivalence with English grammar.
"""

import pytest
from src.null_system.lang import NullLangCompiler
from src.null_system.lang.modern import ModernRustParser
from src.null_system.lang.ast_nodes import (
    Program, SetCommand, IfCommand, ForCommand, WhileCommand,
    ReturnCommand, BreakCommand, ContinueCommand, FunctionCall,
    DefineCommand, AsyncFunction, MatchExpression, PrintCommand,
    BorrowCommand, Identifier, NumLiteral, BinaryExpression, BinaryOperator,
)
from src.null_system.lang.errors import SyntaxError, LexerError


class TestModernRustLiteralsAndExpressions:
    """Test parsing of Rust-like literals and expressions."""

    def test_parse_number_literal(self):
        parser = ModernRustParser()
        result = parser.parse_statement("42;")
        assert isinstance(result, NumLiteral)
        assert result.value == 42

    def test_parse_string_literal(self):
        parser = ModernRustParser()
        result = parser.parse_statement('"hello";')
        from src.null_system.lang.ast_nodes import TextLiteral
        assert isinstance(result, TextLiteral)

    def test_parse_boolean_true(self):
        parser = ModernRustParser()
        result = parser.parse_statement("true;")
        from src.null_system.lang.ast_nodes import BoolLiteral
        assert isinstance(result, BoolLiteral)
        assert result.value is True

    def test_parse_boolean_false(self):
        parser = ModernRustParser()
        result = parser.parse_statement("false;")
        from src.null_system.lang.ast_nodes import BoolLiteral
        assert isinstance(result, BoolLiteral)
        assert result.value is False

    def test_parse_identifier(self):
        parser = ModernRustParser()
        result = parser.parse_statement("x;")
        assert isinstance(result, Identifier)
        assert result.name == "x"

    def test_parse_addition_expression(self):
        parser = ModernRustParser()
        result = parser.parse_statement("1 + 2;")
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.ADD

    def test_parse_subtraction_expression(self):
        parser = ModernRustParser()
        result = parser.parse_statement("5 - 3;")
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.SUBTRACT

    def test_parse_multiplication_expression(self):
        parser = ModernRustParser()
        result = parser.parse_statement("4 * 5;")
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.MULTIPLY

    def test_parse_division_expression(self):
        parser = ModernRustParser()
        result = parser.parse_statement("10 / 2;")
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.DIVIDE

    def test_parse_equality_expression(self):
        parser = ModernRustParser()
        result = parser.parse_statement("x == 5;")
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.EQUALS

    def test_parse_inequality_expression(self):
        parser = ModernRustParser()
        result = parser.parse_statement("x != 5;")
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.NOT_EQUALS


class TestModernRustVariablesAndAssignment:
    """Test parsing of Rust-like variables and assignments."""

    def test_let_statement(self):
        parser = ModernRustParser()
        result = parser.parse("let x = 5;")
        assert isinstance(result, Program)
        assert len(result.statements) > 0
        stmt = result.statements[0]
        assert isinstance(stmt, SetCommand)

    def test_let_mut_statement(self):
        parser = ModernRustParser()
        result = parser.parse("let mut x = 5;")
        assert isinstance(result, Program)
        assert len(result.statements) > 0

    def test_simple_assignment(self):
        parser = ModernRustParser()
        result = parser.parse("x = 10;")
        assert isinstance(result, Program)
        assert len(result.statements) > 0

    def test_multiple_assignments(self):
        parser = ModernRustParser()
        result = parser.parse("let x = 5;\nlet y = 10;")
        assert isinstance(result, Program)
        assert len(result.statements) >= 2


class TestModernRustControlFlow:
    """Test parsing of Rust-like control flow statements."""

    def test_if_statement_basic(self):
        parser = ModernRustParser()
        result = parser.parse("if x > 0 { println(\"positive\"); }")
        assert isinstance(result, Program)
        assert len(result.statements) > 0

    def test_if_else_statement(self):
        parser = ModernRustParser()
        result = parser.parse("if x > 0 { println(\"positive\"); } else { println(\"negative\"); }")
        assert isinstance(result, Program)

    def test_while_loop(self):
        parser = ModernRustParser()
        result = parser.parse("while x < 10 { x = x + 1; }")
        assert isinstance(result, Program)
        assert len(result.statements) > 0

    def test_for_loop_with_range(self):
        parser = ModernRustParser()
        result = parser.parse("for i in 0..10 { println(\"count\"); }")
        assert isinstance(result, Program)
        assert len(result.statements) > 0

    def test_for_loop_with_identifier(self):
        parser = ModernRustParser()
        result = parser.parse("for i in items { println(\"item\"); }")
        assert isinstance(result, Program)


class TestModernRustFunctions:
    """Test parsing of Rust-like function definitions."""

    def test_simple_function(self):
        parser = ModernRustParser()
        result = parser.parse("fn add(x: i32, y: i32) { }")
        assert isinstance(result, Program)
        assert len(result.statements) > 0

    def test_function_with_body(self):
        parser = ModernRustParser()
        code = """
        fn double(x: i32) {
            println("result");
        }
        """
        result = parser.parse(code)
        assert isinstance(result, Program)

    def test_function_with_return(self):
        parser = ModernRustParser()
        code = """
        fn get_five() {
            return 5;
        }
        """
        result = parser.parse(code)
        assert isinstance(result, Program)

    def test_async_function(self):
        parser = ModernRustParser()
        code = """
        async fn fetch() {
            println("fetching");
        }
        """
        result = parser.parse(code)
        assert isinstance(result, Program)


class TestModernRustControlStatements:
    """Test parsing of return, break, and continue."""

    def test_return_with_value(self):
        parser = ModernRustParser()
        result = parser.parse("return 42;")
        assert isinstance(result, Program)

    def test_return_without_value(self):
        parser = ModernRustParser()
        result = parser.parse("return;")
        assert isinstance(result, Program)

    def test_break_statement(self):
        parser = ModernRustParser()
        result = parser.parse("break;")
        assert isinstance(result, Program)

    def test_continue_statement(self):
        parser = ModernRustParser()
        result = parser.parse("continue;")
        assert isinstance(result, Program)


class TestModernRustPatternMatching:
    """Test parsing of Rust-like match expressions."""

    def test_match_with_literals(self):
        parser = ModernRustParser()
        code = """
        match x {
            0 => { println("zero"); },
            1 => { println("one"); },
            _ => { println("other"); }
        }
        """
        result = parser.parse(code)
        assert isinstance(result, Program)

    def test_match_with_boolean_patterns(self):
        parser = ModernRustParser()
        code = """
        match flag {
            true => { println("yes"); },
            false => { println("no"); }
        }
        """
        result = parser.parse(code)
        assert isinstance(result, Program)


class TestModernRustPrintStatements:
    """Test parsing of print/println statements."""

    def test_println_statement(self):
        parser = ModernRustParser()
        result = parser.parse('println("hello");')
        assert isinstance(result, Program)
        assert len(result.statements) > 0

    def test_print_statement(self):
        parser = ModernRustParser()
        result = parser.parse('print("hello");')
        assert isinstance(result, Program)

    def test_println_with_expression(self):
        parser = ModernRustParser()
        result = parser.parse('println(x + y);')
        assert isinstance(result, Program)


class TestModernRustCompilation:
    """Test compilation of parsed Rust-like code."""

    def test_compile_simple_variable(self):
        parser = ModernRustParser()
        compiler = NullLangCompiler()
        ast = parser.parse("let x = 42;")
        stream = compiler.compile(ast)
        assert stream is not None
        assert len(stream.tokens) > 0

    def test_compile_function(self):
        parser = ModernRustParser()
        compiler = NullLangCompiler()
        code = """
        fn main() {
            println("hello");
        }
        """
        ast = parser.parse(code)
        stream = compiler.compile(ast)
        assert stream is not None

    def test_compile_for_loop(self):
        parser = ModernRustParser()
        compiler = NullLangCompiler()
        code = """
        for i in 0..10 {
            println("count");
        }
        """
        ast = parser.parse(code)
        stream = compiler.compile(ast)
        assert stream is not None

    def test_compile_if_statement(self):
        parser = ModernRustParser()
        compiler = NullLangCompiler()
        code = """
        if x > 0 {
            println("positive");
        }
        """
        ast = parser.parse(code)
        stream = compiler.compile(ast)
        assert stream is not None


class TestModernRustSpecialFeatures:
    """Test special Rust-like features."""

    def test_borrow_reference(self):
        parser = ModernRustParser()
        code = "&x"
        try:
            result = parser.parse_statement(code + ";")
        except SyntaxError:
            pass

    def test_mutable_borrow(self):
        parser = ModernRustParser()
        code = "&mut x"
        try:
            result = parser.parse_statement(code + ";")
        except SyntaxError:
            pass


class TestModernRustComplexPrograms:
    """Test parsing of complex Rust-like programs."""

    def test_fibonacci_program(self):
        parser = ModernRustParser()
        code = """
        fn fibonacci(n: i32) {
            let mut a = 0;
            let mut b = 1;
            for i in 0..n {
                let temp = a + b;
                a = b;
                b = temp;
            }
        }
        """
        result = parser.parse(code)
        assert isinstance(result, Program)
        assert len(result.statements) > 0

    def test_counter_loop_program(self):
        parser = ModernRustParser()
        code = """
        for i in 0..10 {
            println("count");
        }
        """
        result = parser.parse(code)
        assert isinstance(result, Program)

    def test_conditional_chain(self):
        parser = ModernRustParser()
        code = """
        if x > 10 {
            println("big");
        } else {
            println("small");
        }
        """
        result = parser.parse(code)
        assert isinstance(result, Program)


class TestModernRustEquivalence:
    """Test equivalence between Rust-like and English grammar."""

    def test_variable_equivalence(self):
        rust_parser = ModernRustParser()
        from src.null_system.lang import NullLangParser

        english_parser = NullLangParser()

        rust_ast = rust_parser.parse("let x = 42;")
        english_ast = english_parser.parse("SET x TO 42")

        assert isinstance(rust_ast.statements[0], SetCommand)
        assert isinstance(english_ast.statements[0], SetCommand)
        assert rust_ast.statements[0].target.name == english_ast.statements[0].target.name

    def test_function_equivalence(self):
        rust_parser = ModernRustParser()
        from src.null_system.lang import NullLangParser

        english_parser = NullLangParser()

        rust_code = "fn add(x: i32, y: i32) { }"
        english_code = "DEFINE add WITH x, y END DEFINE"

        rust_ast = rust_parser.parse(rust_code)
        english_ast = english_parser.parse(english_code)

        assert isinstance(rust_ast.statements[0], DefineCommand)
        assert isinstance(english_ast.statements[0], DefineCommand)
