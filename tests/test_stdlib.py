"""Tests for standard library functions."""

import pytest

from null_system.lang.parser import NullLangParser
from null_system.lang.compiler import NullLangCompiler
from null_system.vm.vm import NullVM
from null_system.lib.registry import default_registry


class TestMathStdlib:
    """Test math module standard library functions."""

    def test_add(self):
        """Test math.ADD function."""
        registry = default_registry()
        fn = registry.resolve("math.ADD")
        assert fn.arity == 2

    def test_sqrt(self):
        """Test math.SQRT function."""
        registry = default_registry()
        fn = registry.resolve("math.SQRT")
        assert fn.arity == 1

    def test_pow(self):
        """Test math.POW function."""
        registry = default_registry()
        fn = registry.resolve("math.POW")
        assert fn.arity == 2

    def test_comparison_functions_exist(self):
        """Test that all comparison functions are registered."""
        registry = default_registry()
        for fn_name in ["math.GT", "math.LT", "math.GTE", "math.LTE", "math.EQ", "math.NEQ"]:
            fn = registry.resolve(fn_name)
            assert fn.arity == 2

    def test_rounding_functions_exist(self):
        """Test that all rounding functions are registered."""
        registry = default_registry()
        for fn_name in ["math.FLOOR", "math.CEIL", "math.ROUND"]:
            fn = registry.resolve(fn_name)
            assert fn.arity == 1


class TestTextStdlib:
    """Test text module standard library functions."""

    def test_concat(self):
        """Test text.CONCAT function."""
        registry = default_registry()
        fn = registry.resolve("text.CONCAT")
        assert fn.arity == 2

    def test_uppercase(self):
        """Test text.UPPERCASE function."""
        registry = default_registry()
        fn = registry.resolve("text.UPPERCASE")
        assert fn.arity == 1

    def test_lowercase(self):
        """Test text.LOWERCASE function."""
        registry = default_registry()
        fn = registry.resolve("text.LOWERCASE")
        assert fn.arity == 1

    def test_trim(self):
        """Test text.TRIM function."""
        registry = default_registry()
        fn = registry.resolve("text.TRIM")
        assert fn.arity == 1

    def test_length(self):
        """Test text.LENGTH function."""
        registry = default_registry()
        fn = registry.resolve("text.LENGTH")
        assert fn.arity == 1

    def test_contains(self):
        """Test text.CONTAINS function."""
        registry = default_registry()
        fn = registry.resolve("text.CONTAINS")
        assert fn.arity == 2

    def test_starts_with(self):
        """Test text.STARTS_WITH function."""
        registry = default_registry()
        fn = registry.resolve("text.STARTS_WITH")
        assert fn.arity == 2

    def test_ends_with(self):
        """Test text.ENDS_WITH function."""
        registry = default_registry()
        fn = registry.resolve("text.ENDS_WITH")
        assert fn.arity == 2

    def test_split(self):
        """Test text.SPLIT function."""
        registry = default_registry()
        fn = registry.resolve("text.SPLIT")
        assert fn.arity == 2

    def test_join(self):
        """Test text.JOIN function."""
        registry = default_registry()
        fn = registry.resolve("text.JOIN")
        assert fn.arity == 2

    def test_replace(self):
        """Test text.REPLACE function."""
        registry = default_registry()
        fn = registry.resolve("text.REPLACE")
        assert fn.arity == 3


class TestArrayStdlib:
    """Test array module standard library functions."""

    def test_push(self):
        """Test array.PUSH function."""
        registry = default_registry()
        fn = registry.resolve("array.PUSH")
        assert fn.arity == 2

    def test_pop(self):
        """Test array.POP function."""
        registry = default_registry()
        fn = registry.resolve("array.POP")
        assert fn.arity == 1

    def test_length(self):
        """Test array.LENGTH function."""
        registry = default_registry()
        fn = registry.resolve("array.LENGTH")
        assert fn.arity == 1

    def test_sort(self):
        """Test array.SORT function."""
        registry = default_registry()
        fn = registry.resolve("array.SORT")
        assert fn.arity == 1

    def test_reverse(self):
        """Test array.REVERSE function."""
        registry = default_registry()
        fn = registry.resolve("array.REVERSE")
        assert fn.arity == 1

    def test_map(self):
        """Test array.MAP function."""
        registry = default_registry()
        fn = registry.resolve("array.MAP")
        assert fn.arity == 3

    def test_filter(self):
        """Test array.FILTER function."""
        registry = default_registry()
        fn = registry.resolve("array.FILTER")
        assert fn.arity == 3

    def test_reduce(self):
        """Test array.REDUCE function."""
        registry = default_registry()
        fn = registry.resolve("array.REDUCE")
        assert fn.arity == 3

    def test_for_each(self):
        """Test array.FOR_EACH function."""
        registry = default_registry()
        fn = registry.resolve("array.FOR_EACH")
        assert fn.arity == 3


class TestIOStdlib:
    """Test I/O module standard library functions."""

    def test_show(self):
        """Test io.SHOW function."""
        registry = default_registry()
        fn = registry.resolve("io.SHOW")
        assert fn.arity == 1

    def test_read(self):
        """Test io.READ function."""
        registry = default_registry()
        fn = registry.resolve("io.READ")
        assert fn.arity == 0


class TestStdlibCompleteness:
    """Test that all expected stdlib functions are available."""

    def test_math_functions_available(self):
        """Test that all expected math functions are available."""
        registry = default_registry()
        expected = [
            "math.ADD", "math.SUB", "math.MUL", "math.DIV",
            "math.ABS", "math.MIN", "math.MAX", "math.SQRT",
            "math.POW", "math.SIN", "math.COS",
            "math.FLOOR", "math.CEIL", "math.ROUND",
            "math.GT", "math.LT", "math.GTE", "math.LTE",
            "math.EQ", "math.NEQ",
        ]
        for fn_name in expected:
            assert fn_name in registry.available()

    def test_text_functions_available(self):
        """Test that all expected text functions are available."""
        registry = default_registry()
        expected = [
            "text.CONCAT", "text.SUBSTR", "text.UPPERCASE",
            "text.LOWERCASE", "text.TRIM", "text.LENGTH",
            "text.CONTAINS", "text.STARTS_WITH", "text.ENDS_WITH",
            "text.SPLIT", "text.JOIN", "text.REPLACE",
            "text.REPEAT", "text.SLICE", "text.GET_CHAR",
        ]
        for fn_name in expected:
            assert fn_name in registry.available()

    def test_array_functions_available(self):
        """Test that all expected array functions are available."""
        registry = default_registry()
        expected = [
            "array.PUSH", "array.POP", "array.LENGTH",
            "array.SORT", "array.REVERSE", "array.MAP",
            "array.FILTER", "array.REDUCE", "array.FOR_EACH",
            "array.SLICE",
        ]
        for fn_name in expected:
            assert fn_name in registry.available()

    def test_io_functions_available(self):
        """Test that all expected I/O functions are available."""
        registry = default_registry()
        expected = ["io.SHOW", "io.READ"]
        for fn_name in expected:
            assert fn_name in registry.available()

    def test_total_stdlib_functions_count(self):
        """Verify we have a comprehensive stdlib."""
        registry = default_registry()
        available = registry.available()
        # Should have math, text, array, io, object, option, result functions
        assert len(available) > 50
