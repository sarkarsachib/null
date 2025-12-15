"""Unit tests for the compiler module."""

import pytest

from null_system.compiler import NullCompiler, CompilationError
from null_system.compiler.optimization import DeduplicationPass, CompressionPass
from null_system.superbit.ir import SuperBitOpCode
from null_system.lang.syntax_modes import SyntaxMode, SyntaxConfig


class TestNullCompiler:
    """Tests for NullCompiler class."""
    
    def test_compiler_initialization(self):
        """Test compiler initialization."""
        compiler = NullCompiler()
        assert compiler is not None
        assert len(compiler.optimization_passes) == 0
    
    def test_compiler_with_optimization_passes(self):
        """Test compiler with optimization passes."""
        passes = [DeduplicationPass(), CompressionPass()]
        compiler = NullCompiler(optimization_passes=passes)
        assert len(compiler.optimization_passes) == 2
    
    def test_compile_returns_artifact(self):
        """Test that compile returns a CompilationArtifact."""
        compiler = NullCompiler()
        artifact = compiler.compile("set x to 5")
        
        assert artifact is not None
        assert artifact.ast is not None
        assert artifact.superbit_stream is not None
        assert artifact.binary_frames is not None
        assert artifact.is_valid()
    
    def test_compile_with_syntax_config(self):
        """Test compilation with syntax configuration."""
        compiler = NullCompiler()
        syntax_config = SyntaxConfig(mode=SyntaxMode.MODERN)
        artifact = compiler.compile("set x to 5", syntax_config=syntax_config)
        
        assert artifact is not None
        assert artifact.syntax_config == syntax_config
        assert artifact.syntax_config.mode == SyntaxMode.MODERN
    
    def test_compile_with_default_syntax_config(self):
        """Test compilation with default syntax configuration."""
        compiler = NullCompiler()
        artifact = compiler.compile("set x to 5")  # No syntax config provided
        
        assert artifact is not None
        assert artifact.syntax_config is None  # Should be None when not provided
    
    def test_compile_and_run_with_syntax_config(self):
        """Test compile_and_run with syntax configuration."""
        compiler = NullCompiler()
        syntax_config = SyntaxConfig(mode=SyntaxMode.HYBRID, allow_hybrid=True)
        result = compiler.compile_and_run("set x to 5", syntax_config=syntax_config)
        
        assert result is not None
        assert result.success
        assert result.final_state["x"] == 5
    
    def test_compile_invalid_syntax(self):
        """Test compilation with invalid syntax."""
        compiler = NullCompiler()
        
        with pytest.raises(CompilationError):
            compiler.compile("invalid syntax here")
    
    def test_compile_and_run_invalid_syntax(self):
        """Test compile_and_run with invalid syntax."""
        compiler = NullCompiler()
        result = compiler.compile_and_run("invalid syntax here")
        
        assert not result.success
        assert "Parse error" in result.error
    
    def test_compile_and_run_returns_result(self):
        """Test compile_and_run returns ExecutionResult."""
        compiler = NullCompiler()
        result = compiler.compile_and_run("set x to 5")
        
        assert result is not None
        assert result.success
        assert result.final_state["x"] == 5
    
    def test_compile_and_run_with_validation_error(self):
        """Test compile_and_run with validation errors."""
        compiler = NullCompiler()
        result = compiler.compile_and_run("print undefined")
        
        assert not result.success
        assert "Validation errors" in result.error


class TestOptimizationPasses:
    """Tests for optimization passes."""
    
    def test_deduplication_pass(self):
        """Test deduplication optimization pass."""
        from null_system.superbit.ir import SuperBitIRToken, SuperBitStream

        stream = SuperBitStream(
            tokens=[
                SuperBitIRToken(SuperBitOpCode.LOAD_CONST, 5),
                SuperBitIRToken(SuperBitOpCode.LOAD_CONST, 5),
                SuperBitIRToken(SuperBitOpCode.STORE_VAR, "x"),
            ]
        )
        
        opt = DeduplicationPass()
        optimized = opt.optimize(stream)
        
        assert len(optimized.tokens) == 2
    
    def test_compression_pass_folds_constants(self):
        """Test constant folding in compression pass."""
        from null_system.superbit.ir import SuperBitIRToken, SuperBitStream

        stream = SuperBitStream(
            tokens=[
                SuperBitIRToken(SuperBitOpCode.LOAD_CONST, 5),
                SuperBitIRToken(SuperBitOpCode.LOAD_CONST, 3),
                SuperBitIRToken(SuperBitOpCode.BINARY_ADD),
            ]
        )
        
        opt = CompressionPass()
        optimized = opt.optimize(stream)
        
        assert len(optimized.tokens) == 1
        assert optimized.tokens[0].opcode == SuperBitOpCode.LOAD_CONST
        assert optimized.tokens[0].operand == 8
    
    def test_compression_pass_handles_division(self):
        """Test compression pass handles division."""
        from null_system.superbit.ir import SuperBitIRToken, SuperBitStream

        stream = SuperBitStream(
            tokens=[
                SuperBitIRToken(SuperBitOpCode.LOAD_CONST, 10),
                SuperBitIRToken(SuperBitOpCode.LOAD_CONST, 2),
                SuperBitIRToken(SuperBitOpCode.BINARY_DIV),
            ]
        )
        
        opt = CompressionPass()
        optimized = opt.optimize(stream)
        
        assert len(optimized.tokens) == 1
        assert optimized.tokens[0].operand == 5.0


class TestCompilationArtifact:
    """Tests for CompilationArtifact."""
    
    def test_is_valid_with_no_errors(self):
        """Test is_valid returns True when no errors."""
        compiler = NullCompiler()
        artifact = compiler.compile("set x to 5")
        
        assert artifact.is_valid()
        assert len(artifact.validation_errors) == 0
    
    def test_is_valid_with_errors(self):
        """Test is_valid returns False when errors exist."""
        compiler = NullCompiler()
        artifact = compiler.compile("print undefined")
        
        assert not artifact.is_valid()
        assert len(artifact.validation_errors) > 0
