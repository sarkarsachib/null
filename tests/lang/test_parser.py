"""
Unit tests for Null-Lang parser.

Tests cover parsing of all language constructs including happy paths
and error cases with detailed diagnostics.
"""

import pytest
from src.null_system.lang import (
    NullLangParser, parse, parse_statement,
    Program, SetCommand, AddCommand, IfCommand, ShowCommand, RepeatCommand, DefineCommand,
    TextLiteral, NumLiteral, BoolLiteral, ArrayLiteral, ObjectLiteral,
    Identifier, MemberAccess, BinaryExpression, UnaryExpression, ComparisonExpression,
    FunctionCall, NullLibAnnotation, Comment,
    BinaryOperator, UnaryOperator,
    SyntaxError, LexerError
)


class TestLiterals:
    """Test parsing of literal values."""
    
    def test_text_literal(self):
        result = parse_statement('"Hello, World!"')
        assert isinstance(result, TextLiteral)
        assert result.value == "Hello, World!"
    
    def test_text_literal_single_quotes(self):
        result = parse_statement("'Hello'")
        assert isinstance(result, TextLiteral)
        assert result.value == "Hello"
    
    def test_text_literal_with_escapes(self):
        result = parse_statement('"Line 1\\nLine 2"')
        assert isinstance(result, TextLiteral)
        assert result.value == "Line 1\nLine 2"
    
    def test_num_literal_integer(self):
        result = parse_statement('42')
        assert isinstance(result, NumLiteral)
        assert result.value == 42
        assert isinstance(result.value, int)
    
    def test_num_literal_float(self):
        result = parse_statement('3.14')
        assert isinstance(result, NumLiteral)
        assert result.value == 3.14
        assert isinstance(result.value, float)
    
    def test_bool_literal_true(self):
        result = parse_statement('TRUE')
        assert isinstance(result, BoolLiteral)
        assert result.value is True
    
    def test_bool_literal_false(self):
        result = parse_statement('FALSE')
        assert isinstance(result, BoolLiteral)
        assert result.value is False
    
    def test_array_literal_with_keyword(self):
        result = parse_statement('ARRAY [1, 2, 3]')
        assert isinstance(result, ArrayLiteral)
        assert len(result.elements) == 3
        assert all(isinstance(e, NumLiteral) for e in result.elements)
    
    def test_array_literal_shorthand(self):
        result = parse_statement('[1, 2, 3]')
        assert isinstance(result, ArrayLiteral)
        assert len(result.elements) == 3
    
    def test_array_literal_empty(self):
        result = parse_statement('[]')
        assert isinstance(result, ArrayLiteral)
        assert len(result.elements) == 0
    
    def test_array_literal_mixed_types(self):
        result = parse_statement('[1, "text", TRUE]')
        assert isinstance(result, ArrayLiteral)
        assert len(result.elements) == 3
        assert isinstance(result.elements[0], NumLiteral)
        assert isinstance(result.elements[1], TextLiteral)
        assert isinstance(result.elements[2], BoolLiteral)
    
    def test_object_literal_with_keyword(self):
        result = parse_statement('OBJECT { name: "Alice", age: 30 }')
        assert isinstance(result, ObjectLiteral)
        assert len(result.pairs) == 2
        assert result.pairs[0][0] == "name"
        assert isinstance(result.pairs[0][1], TextLiteral)
    
    def test_object_literal_shorthand(self):
        result = parse_statement('{ x: 10, y: 20 }')
        assert isinstance(result, ObjectLiteral)
        assert len(result.pairs) == 2
    
    def test_object_literal_empty(self):
        result = parse_statement('{}')
        assert isinstance(result, ObjectLiteral)
        assert len(result.pairs) == 0


class TestIdentifiersAndMemberAccess:
    """Test parsing of identifiers and member access."""
    
    def test_identifier(self):
        result = parse_statement('variable_name')
        assert isinstance(result, Identifier)
        assert result.name == "variable_name"
    
    def test_property_access(self):
        result = parse_statement('person.name')
        assert isinstance(result, MemberAccess)
        assert isinstance(result.object, Identifier)
        assert result.object.name == "person"
        assert result.member == "name"
        assert not result.is_index
    
    def test_index_access(self):
        result = parse_statement('array[0]')
        assert isinstance(result, MemberAccess)
        assert isinstance(result.object, Identifier)
        assert result.is_index
        assert isinstance(result.member, NumLiteral)
    
    def test_nested_member_access(self):
        result = parse_statement('obj.prop[0].nested')
        assert isinstance(result, MemberAccess)


class TestCommands:
    """Test parsing of command statements."""
    
    def test_set_command(self):
        result = parse_statement('SET x TO 42')
        assert isinstance(result, SetCommand)
        assert isinstance(result.target, Identifier)
        assert result.target.name == "x"
        assert isinstance(result.value, NumLiteral)
        assert result.value.value == 42
    
    def test_set_command_with_expression(self):
        result = parse_statement('SET result TO 10 PLUS 5')
        assert isinstance(result, SetCommand)
        assert isinstance(result.value, BinaryExpression)
    
    def test_set_command_member_access(self):
        result = parse_statement('SET person.age TO 30')
        assert isinstance(result, SetCommand)
        assert isinstance(result.target, MemberAccess)
    
    def test_add_command(self):
        result = parse_statement('ADD 5 AND 10')
        assert isinstance(result, AddCommand)
        assert len(result.operands) == 2
        assert isinstance(result.operands[0], NumLiteral)
        assert result.operands[0].value == 5
    
    def test_add_command_multiple(self):
        result = parse_statement('ADD 1 AND 2 AND 3 AND 4')
        assert isinstance(result, AddCommand)
        assert len(result.operands) == 4
    
    def test_show_command(self):
        result = parse_statement('SHOW "Hello"')
        assert isinstance(result, ShowCommand)
        assert isinstance(result.value, TextLiteral)
        assert result.value.value == "Hello"
    
    def test_show_command_variable(self):
        result = parse_statement('SHOW x')
        assert isinstance(result, ShowCommand)
        assert isinstance(result.value, Identifier)
    
    def test_if_command(self):
        source = """
IF x IS 10 THEN
    SHOW "yes"
END IF
"""
        result = parse_statement(source.strip())
        assert isinstance(result, IfCommand)
        assert isinstance(result.condition, ComparisonExpression)
        assert len(result.then_block) == 1
        assert result.else_block is None
    
    def test_if_else_command(self):
        source = """
IF x IS GREATER THAN 5 THEN
    SHOW "large"
ELSE
    SHOW "small"
END IF
"""
        result = parse_statement(source.strip())
        assert isinstance(result, IfCommand)
        assert len(result.then_block) == 1
        assert result.else_block is not None
        assert len(result.else_block) == 1
    
    def test_repeat_command(self):
        source = """
REPEAT 5 TIMES
    SHOW "hello"
END REPEAT
"""
        result = parse_statement(source.strip())
        assert isinstance(result, RepeatCommand)
        assert isinstance(result.count, NumLiteral)
        assert result.count.value == 5
        assert len(result.body) == 1
    
    def test_define_command_no_params(self):
        source = """
DEFINE greet
    SHOW "Hello"
END DEFINE
"""
        result = parse_statement(source.strip())
        assert isinstance(result, DefineCommand)
        assert result.name == "greet"
        assert len(result.parameters) == 0
        assert len(result.body) == 1
    
    def test_define_command_with_params(self):
        source = """
DEFINE add WITH x, y
    SET result TO x PLUS y
END DEFINE
"""
        result = parse_statement(source.strip())
        assert isinstance(result, DefineCommand)
        assert result.name == "add"
        assert result.parameters == ["x", "y"]
        assert len(result.body) == 1


class TestExpressions:
    """Test parsing of expressions."""
    
    def test_arithmetic_add(self):
        result = parse_statement('10 PLUS 5')
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.ADD
    
    def test_arithmetic_subtract(self):
        result = parse_statement('10 MINUS 5')
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.SUBTRACT
    
    def test_arithmetic_multiply(self):
        result = parse_statement('10 TIMES 5')
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.MULTIPLY
    
    def test_arithmetic_divide(self):
        result = parse_statement('10 DIVIDED BY 5')
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.DIVIDE
    
    def test_arithmetic_precedence(self):
        result = parse_statement('2 PLUS 3 TIMES 4')
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.ADD
        assert isinstance(result.right, BinaryExpression)
        assert result.right.operator == BinaryOperator.MULTIPLY
    
    def test_arithmetic_parentheses(self):
        result = parse_statement('(2 PLUS 3) TIMES 4')
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.MULTIPLY
    
    def test_comparison_is(self):
        result = parse_statement('x IS 10')
        assert isinstance(result, ComparisonExpression)
        assert result.operator == "IS"
    
    def test_comparison_is_not(self):
        result = parse_statement('x IS NOT 0')
        assert isinstance(result, ComparisonExpression)
        assert result.operator == "IS NOT"
    
    def test_comparison_greater(self):
        result = parse_statement('x IS GREATER THAN 5')
        assert isinstance(result, ComparisonExpression)
        assert result.operator == "IS GREATER THAN"
    
    def test_comparison_less(self):
        result = parse_statement('x IS LESS THAN 10')
        assert isinstance(result, ComparisonExpression)
        assert result.operator == "IS LESS THAN"
    
    def test_logical_and(self):
        result = parse_statement('TRUE AND FALSE')
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.AND
    
    def test_logical_or(self):
        result = parse_statement('TRUE OR FALSE')
        assert isinstance(result, BinaryExpression)
        assert result.operator == BinaryOperator.OR
    
    def test_logical_not(self):
        result = parse_statement('NOT TRUE')
        assert isinstance(result, UnaryExpression)
        assert result.operator == UnaryOperator.NOT
    
    def test_negate(self):
        result = parse_statement('MINUS 5')
        assert isinstance(result, UnaryExpression)
        assert result.operator == UnaryOperator.NEGATE


class TestFunctionCalls:
    """Test parsing of function calls."""
    
    def test_function_call_with_keyword(self):
        result = parse_statement('CALL greet')
        assert isinstance(result, FunctionCall)
        assert result.name == "greet"
        assert len(result.arguments) == 0
    
    def test_function_call_with_args(self):
        result = parse_statement('CALL add WITH 5, 10')
        assert isinstance(result, FunctionCall)
        assert result.name == "add"
        assert len(result.arguments) == 2
    
    def test_function_call_parens(self):
        result = parse_statement('greet()')
        assert isinstance(result, FunctionCall)
        assert result.name == "greet"
    
    def test_function_call_parens_with_args(self):
        result = parse_statement('add(5, 10)')
        assert isinstance(result, FunctionCall)
        assert len(result.arguments) == 2


class TestNullLibAnnotations:
    """Test parsing of Null-Lib annotations."""
    
    def test_null_lib_basic(self):
        result = parse_statement('@http.get')
        assert isinstance(result, NullLibAnnotation)
        assert result.lib_name == "http"
        assert result.function == "get"
        assert len(result.arguments) == 0
    
    def test_null_lib_with_args(self):
        result = parse_statement('@http.get("https://example.com")')
        assert isinstance(result, NullLibAnnotation)
        assert result.lib_name == "http"
        assert result.function == "get"
        assert len(result.arguments) == 1
    
    def test_null_lib_multiple_args(self):
        result = parse_statement('@math.calculate("sum", 10, 20)')
        assert isinstance(result, NullLibAnnotation)
        assert len(result.arguments) == 3


class TestPrograms:
    """Test parsing of multi-statement programs."""
    
    def test_empty_program(self):
        result = parse('')
        assert isinstance(result, Program)
        assert len(result.statements) == 0
    
    def test_single_statement(self):
        result = parse('SET x TO 5')
        assert isinstance(result, Program)
        assert len(result.statements) == 1
    
    def test_multiple_statements(self):
        source = """
SET x TO 5
SET y TO 10
SHOW x
SHOW y
"""
        result = parse(source)
        assert isinstance(result, Program)
        assert len(result.statements) == 4
    
    def test_complex_program(self):
        source = """
SET numbers TO [1, 2, 3, 4, 5]
SET sum TO 0
REPEAT 5 TIMES
    SET sum TO sum PLUS numbers[0]
END REPEAT
SHOW sum
"""
        result = parse(source)
        assert isinstance(result, Program)
        assert len(result.statements) == 4


class TestComments:
    """Test comment handling."""
    
    def test_comment_ignored_in_parsing(self):
        source = """
# This is a comment
SET x TO 5
# Another comment
"""
        result = parse(source)
        # Comments are ignored by the grammar
        assert isinstance(result, Program)
        assert len(result.statements) == 1


class TestErrorHandling:
    """Test error handling and diagnostics."""
    
    def test_syntax_error_unexpected_token(self):
        with pytest.raises(SyntaxError) as exc_info:
            parse_statement('SET TO 5')
        error = exc_info.value
        assert error.span is not None
    
    def test_syntax_error_missing_end(self):
        with pytest.raises(SyntaxError):
            parse_statement('IF x IS 10 THEN SHOW "yes"')
    
    def test_syntax_error_invalid_command(self):
        with pytest.raises(SyntaxError):
            parse_statement('INVALID x TO 5')
    
    def test_lexer_error_unclosed_string(self):
        with pytest.raises((SyntaxError, LexerError)):
            parse_statement('"unclosed string')
    
    def test_error_with_source_span(self):
        source = 'SET x TO'
        with pytest.raises(SyntaxError) as exc_info:
            parse_statement(source)
        error = exc_info.value
        assert source in str(error) or error.span is not None
    
    def test_error_message_format(self):
        source = 'SET x TO'
        with pytest.raises(SyntaxError) as exc_info:
            parse_statement(source)
        error = exc_info.value
        error_msg = str(error)
        assert "Error" in error_msg or "error" in error_msg.lower()


class TestFixtures:
    """Test that fixture files parse correctly."""
    
    def test_simple_statements_fixture(self):
        with open('fixtures/lang/simple_statements.null', 'r') as f:
            source = f.read()
        result = parse(source)
        assert isinstance(result, Program)
        assert len(result.statements) > 0
    
    def test_control_flow_fixture(self):
        with open('fixtures/lang/control_flow.null', 'r') as f:
            source = f.read()
        result = parse(source)
        assert isinstance(result, Program)
        assert any(isinstance(stmt, IfCommand) for stmt in result.statements)
        assert any(isinstance(stmt, RepeatCommand) for stmt in result.statements)
    
    def test_functions_fixture(self):
        with open('fixtures/lang/functions.null', 'r') as f:
            source = f.read()
        result = parse(source)
        assert isinstance(result, Program)
        assert any(isinstance(stmt, DefineCommand) for stmt in result.statements)
        assert any(isinstance(stmt, FunctionCall) for stmt in result.statements)
    
    def test_collections_fixture(self):
        with open('fixtures/lang/collections.null', 'r') as f:
            source = f.read()
        result = parse(source)
        assert isinstance(result, Program)
    
    def test_expressions_fixture(self):
        with open('fixtures/lang/expressions.null', 'r') as f:
            source = f.read()
        result = parse(source)
        assert isinstance(result, Program)
    
    def test_null_lib_annotations_fixture(self):
        with open('fixtures/lang/null_lib_annotations.null', 'r') as f:
            source = f.read()
        result = parse(source)
        assert isinstance(result, Program)
        # Find at least one NullLibAnnotation in the AST
        has_annotation = False
        for stmt in result.statements:
            if isinstance(stmt, SetCommand):
                if isinstance(stmt.value, NullLibAnnotation):
                    has_annotation = True
                    break
        assert has_annotation
    
    def test_complete_program_fixture(self):
        with open('fixtures/lang/complete_program.null', 'r') as f:
            source = f.read()
        result = parse(source)
        assert isinstance(result, Program)
        assert len(result.statements) > 5


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_nested_arrays(self):
        result = parse_statement('[[1, 2], [3, 4]]')
        assert isinstance(result, ArrayLiteral)
        assert isinstance(result.elements[0], ArrayLiteral)
    
    def test_nested_objects(self):
        result = parse_statement('{ outer: { inner: 42 } }')
        assert isinstance(result, ObjectLiteral)
    
    def test_complex_expression(self):
        result = parse_statement('(x PLUS y) TIMES (a MINUS b)')
        assert isinstance(result, BinaryExpression)
    
    def test_multiple_member_access(self):
        result = parse_statement('obj.prop1.prop2.prop3')
        assert isinstance(result, MemberAccess)
    
    def test_function_call_in_expression(self):
        result = parse_statement('SET x TO calculate(5) PLUS 10')
        assert isinstance(result, SetCommand)
        assert isinstance(result.value, BinaryExpression)
    
    def test_null_lib_in_set(self):
        result = parse_statement('SET data TO @http.get("url")')
        assert isinstance(result, SetCommand)
        assert isinstance(result.value, NullLibAnnotation)
