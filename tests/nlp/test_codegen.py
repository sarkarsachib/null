"""Tests for code generation."""

import pytest
from null_system.nlp.codegen import CodeGenerator, GeneratedCode


class TestCodeGenerator:
    """Test suite for code generation."""

    def test_generate_set_variable(self):
        """Test generation of SET variable code."""
        codegen = CodeGenerator()
        result = codegen.generate("set x to 5")

        assert result.generated_code
        assert "set" in result.generated_code.lower()

    def test_generate_calculation(self):
        """Test generation of calculation code."""
        codegen = CodeGenerator()
        result = codegen.generate("add 5 and 10")

        assert result.generated_code
        assert "add" in result.generated_code.lower()

    def test_generate_display(self):
        """Test generation of display code."""
        codegen = CodeGenerator()
        result = codegen.generate("show x")

        assert result.generated_code
        assert "show" in result.generated_code.lower()

    def test_generate_loop(self):
        """Test generation of loop code."""
        codegen = CodeGenerator()
        result = codegen.generate("repeat 10 times")

        assert result.generated_code
        assert "repeat" in result.generated_code.lower()

    def test_generate_condition(self):
        """Test generation of conditional code."""
        codegen = CodeGenerator()
        result = codegen.generate("if x is 5 then show true")

        assert result.generated_code
        assert "if" in result.generated_code.lower()

    def test_generate_function_definition(self):
        """Test generation of function definition."""
        codegen = CodeGenerator()
        result = codegen.generate("define a function called add_numbers")

        assert result.generated_code
        assert "define" in result.generated_code.lower()

    def test_generated_code_has_intent(self):
        """Test that generated code includes intent."""
        codegen = CodeGenerator()
        result = codegen.generate("set x to 5")

        assert result.intent is not None
        assert result.intent.name is not None

    def test_generated_code_has_entities(self):
        """Test that generated code includes entities."""
        codegen = CodeGenerator()
        result = codegen.generate("set x to 5")

        assert result.entities is not None
        assert isinstance(result.entities, list)

    def test_generated_code_confidence(self):
        """Test that generated code has confidence score."""
        codegen = CodeGenerator()
        result = codegen.generate("set x to 5")

        assert result.confidence >= 0.0
        assert result.confidence <= 1.0

    def test_empty_input(self):
        """Test with empty input."""
        codegen = CodeGenerator()
        result = codegen.generate("")

        assert isinstance(result, GeneratedCode)
        assert result.generated_code == ""

    def test_batch_generation(self):
        """Test batch code generation."""
        codegen = CodeGenerator()
        texts = [
            "set x to 5",
            "show x",
            "repeat 10 times"
        ]

        results = codegen.batch_generate(texts)

        assert len(results) == 3
        assert all(isinstance(r, GeneratedCode) for r in results)

    def test_target_language_null(self):
        """Test code generation for Null language."""
        codegen = CodeGenerator()
        result = codegen.generate("set x to 5", target_language="null")

        assert result.generated_code
        assert result.language == "null"

    def test_target_language_python(self):
        """Test code generation for Python language."""
        codegen = CodeGenerator()
        result = codegen.generate("set x to 5", target_language="python")

        assert result.generated_code
        assert result.language == "python"

    def test_multilingual_codegen(self):
        """Test code generation from different languages."""
        # English
        codegen_en = CodeGenerator(language="en")
        result_en = codegen_en.generate("set x to 5")
        assert result_en.generated_code

        # Spanish
        codegen_es = CodeGenerator(language="es")
        result_es = codegen_es.generate("establecer x a 5")
        assert result_es.generated_code

    def test_parse_natural_language_code(self):
        """Test parsing multi-line natural language code."""
        codegen = CodeGenerator()
        description = """set x to 5
        show x
        set y to 10"""

        statements = codegen.parse_natural_language_code(description)

        assert len(statements) > 0
        assert all(isinstance(s, str) for s in statements)

    def test_generation_with_context(self):
        """Test code generation with context."""
        codegen = CodeGenerator()
        context = {"x": "5"}

        result = codegen.generate_with_context("show x", context=context)

        assert isinstance(result, GeneratedCode)
        assert result.generated_code

    def test_complex_expression_generation(self):
        """Test generation from complex expressions."""
        codegen = CodeGenerator()
        result = codegen.generate("if x is greater than 5 then add x and y")

        assert result.generated_code
        assert len(result.generated_code) > 0

    def test_function_call_generation(self):
        """Test generation of function calls."""
        codegen = CodeGenerator()
        result = codegen.generate("call my_function with arg1 and arg2")

        assert result.generated_code
        assert "call" in result.generated_code.lower()


class TestCodeGenPerformance:
    """Test code generation performance."""

    def test_generation_speed(self):
        """Test that code generation is reasonably fast."""
        import time
        codegen = CodeGenerator()

        start = time.time()
        result = codegen.generate("set x to 5 show x repeat 10 times add x and y")
        elapsed_ms = (time.time() - start) * 1000

        # Should be fast (under 50ms)
        assert elapsed_ms < 50.0
        assert result.generated_code

    def test_batch_generation_speed(self):
        """Test batch generation performance."""
        import time
        codegen = CodeGenerator()

        texts = ["set x to 5"] * 10

        start = time.time()
        results = codegen.batch_generate(texts)
        elapsed_ms = (time.time() - start) * 1000

        # Should be reasonably fast
        assert elapsed_ms < 500.0  # <50ms per item on average
        assert len(results) == 10


class TestCodeGenIntegration:
    """Integration tests for code generation."""

    def test_generated_null_code_structure(self):
        """Test that generated Null code has proper structure."""
        codegen = CodeGenerator()
        result = codegen.generate("set x to 42")

        # Should be valid Null syntax
        code = result.generated_code
        assert isinstance(code, str)
        assert len(code) > 0

    def test_variable_extraction(self):
        """Test that variables are properly extracted."""
        codegen = CodeGenerator()
        result = codegen.generate("set my_var to 100")

        # Should have extracted the variable name
        assert len(result.entities) > 0

    def test_intent_driven_generation(self):
        """Test that intent properly drives code generation."""
        codegen = CodeGenerator()

        set_result = codegen.generate("set x to 5")
        assert "set" in set_result.generated_code.lower()

        show_result = codegen.generate("show the value")
        assert "show" in show_result.generated_code.lower()

        # Different intents should produce different code patterns
        assert set_result.generated_code != show_result.generated_code
