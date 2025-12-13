"""Integration tests for the Null compiler system."""

import pytest

from null_system.compiler import NullCompiler, CompilationError
from null_system.compiler.optimization import DeduplicationPass, CompressionPass
from null_system.superbit.ir import SuperBitOpCode


class TestIntegration:
    """Integration tests that exercise the full compilation pipeline."""
    
    def test_simple_assignment(self):
        """Test simple variable assignment."""
        source = "set x to 5"
        
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        assert artifact.is_valid()
        assert len(artifact.ast.statements) == 1
        assert len(artifact.superbit_stream.tokens) == 2
        
        tokens = artifact.superbit_stream.tokens
        assert tokens[0].opcode == SuperBitOpCode.LOAD_CONST
        assert tokens[0].operand == 5
        assert tokens[1].opcode == SuperBitOpCode.STORE_VAR
        assert tokens[1].operand == "x"
    
    def test_simple_arithmetic(self):
        """Test basic arithmetic operation."""
        source = """
set x to 5
set y to 3
add x and y
"""
        
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        assert artifact.is_valid()
        assert len(artifact.ast.statements) == 3
        
        result = compiler.compile_and_run(source)
        assert result.success
        assert result.final_state["x"] == 5
        assert result.final_state["y"] == 3
    
    def test_print_statement(self):
        """Test print statement execution."""
        source = """
set x to 42
print x
"""
        
        compiler = NullCompiler()
        result = compiler.compile_and_run(source)
        
        assert result.success
        assert len(result.output) == 1
        assert result.output[0] == "42"
    
    def test_complex_expression(self):
        """Test complex expression with multiple operations."""
        source = """
set a to 10
set b to 5
add a and b
set c to 3
multiply c and 2
"""
        
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        assert artifact.is_valid()
        assert len(artifact.ast.statements) == 5
        assert len(artifact.superbit_stream.tokens) > 0
        
        result = compiler.compile_and_run(source)
        assert result.success
        assert result.final_state["a"] == 10
        assert result.final_state["b"] == 5
        assert result.final_state["c"] == 3
    
    def test_conditional_statement(self):
        """Test if-then-else conditional."""
        source = """
set x to 15
if x is greater than 10 then print 'big' else print 'small'
"""
        
        compiler = NullCompiler()
        result = compiler.compile_and_run(source)
        
        assert result.success
        assert len(result.output) == 1
        assert result.output[0] == "big"
    
    def test_conditional_else_branch(self):
        """Test else branch execution."""
        source = """
set x to 5
if x is greater than 10 then print 'big' else print 'small'
"""
        
        compiler = NullCompiler()
        result = compiler.compile_and_run(source)
        
        assert result.success
        assert len(result.output) == 1
        assert result.output[0] == "small"
    
    def test_string_literal(self):
        """Test string literal printing."""
        source = "print 'Hello World'"
        
        compiler = NullCompiler()
        result = compiler.compile_and_run(source)
        
        assert result.success
        assert len(result.output) == 1
        assert result.output[0] == "Hello World"
    
    def test_optimization_passes(self):
        """Test that optimization passes are applied."""
        source = """
set x to 5
set y to 3
"""
        
        compiler_no_opt = NullCompiler(optimization_passes=[])
        artifact_no_opt = compiler_no_opt.compile(source)
        
        compiler_opt = NullCompiler(optimization_passes=[
            DeduplicationPass(),
            CompressionPass()
        ])
        artifact_opt = compiler_opt.compile(source)
        
        assert artifact_no_opt.is_valid()
        assert artifact_opt.is_valid()
    
    def test_constant_folding(self):
        """Test constant folding optimization."""
        source = "add 5 and 3"
        
        compiler = NullCompiler(optimization_passes=[CompressionPass()])
        artifact = compiler.compile(source)
        
        assert artifact.is_valid()
        tokens = artifact.superbit_stream.tokens
        assert tokens[0].opcode == SuperBitOpCode.LOAD_CONST
        assert tokens[0].operand == 8
    
    def test_binary_frame_generation(self):
        """Test binary frame generation."""
        source = "set x to 5"
        
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        assert artifact.is_valid()
        assert len(artifact.binary_frames) > 0
        assert len(artifact.binary_frames[0].to_bytes()) > 0
    
    def test_undefined_variable_error(self):
        """Test that undefined variables are caught."""
        source = "print undefined_var"
        
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        assert not artifact.is_valid()
        assert len(artifact.validation_errors) > 0
    
    def test_multiple_operations(self):
        """Test multiple operations in sequence."""
        source = """
set x to 10
set y to 20
add x and y
set result to 30
print result
"""
        
        compiler = NullCompiler()
        result = compiler.compile_and_run(source)
        
        assert result.success
        assert len(result.output) == 1
        assert result.output[0] == "30"
    
    def test_comparison_operators(self):
        """Test all comparison operators."""
        sources = [
            ("set x to 10\nif x is greater than 5 then print 'yes' else print 'no'", "yes"),
            ("set x to 3\nif x is less than 5 then print 'yes' else print 'no'", "yes"),
            ("set x to 5\nif x is equals 5 then print 'yes' else print 'no'", "yes"),
        ]
        
        compiler = NullCompiler()
        for source, expected in sources:
            result = compiler.compile_and_run(source)
            assert result.success
            assert result.output[0] == expected
    
    def test_ast_validation(self):
        """Test AST validation detects errors."""
        source = "print x"
        
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        assert not artifact.is_valid()
        assert any("Undefined variable" in err for err in artifact.validation_errors)
    
    def test_consistent_artifacts(self):
        """Test that AST, super-bit, and VM execution are consistent."""
        source = """
set x to 5
set y to 10
add x and y
"""
        
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        assert artifact.is_valid()
        assert len(artifact.ast.statements) == 3
        
        result = compiler.compile_and_run(source)
        assert result.success
        
        tokens = artifact.superbit_stream.tokens
        load_const_count = sum(1 for t in tokens if t.opcode == SuperBitOpCode.LOAD_CONST)
        store_var_count = sum(1 for t in tokens if t.opcode == SuperBitOpCode.STORE_VAR)
        
        assert load_const_count >= 2
        assert store_var_count >= 2
    
    def test_empty_program(self):
        """Test compilation of empty program."""
        source = ""
        
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        assert artifact.is_valid()
        assert len(artifact.ast.statements) == 0
    
    def test_comments(self):
        """Test that comments are ignored."""
        source = """
# This is a comment
set x to 5
# Another comment
print x
"""
        
        compiler = NullCompiler()
        result = compiler.compile_and_run(source)
        
        assert result.success
        assert len(result.output) == 1
        assert result.output[0] == "5"
