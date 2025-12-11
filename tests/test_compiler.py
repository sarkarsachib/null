"""Unit tests for the compiler module."""

import pytest

from src.null_system.compiler import NullCompiler, CompilationError
from src.null_system.compiler.optimization import DeduplicationPass, CompressionPass
from src.null_system.superbit.tokens import SuperBitOpCode


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
    
    def test_compile_invalid_syntax(self):
        """Test compilation with invalid syntax."""
        compiler = NullCompiler()
        
        with pytest.raises(CompilationError):
            compiler.compile("invalid syntax here")
    
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
        from src.null_system.superbit.tokens import SuperBitToken, SuperBitStream
        
        stream = SuperBitStream(tokens=[
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 5),
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 5),
            SuperBitToken(SuperBitOpCode.STORE_VAR, "x"),
        ])
        
        opt = DeduplicationPass()
        optimized = opt.optimize(stream)
        
        assert len(optimized.tokens) == 2
    
    def test_compression_pass_folds_constants(self):
        """Test constant folding in compression pass."""
        from src.null_system.superbit.tokens import SuperBitToken, SuperBitStream
        
        stream = SuperBitStream(tokens=[
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 5),
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 3),
            SuperBitToken(SuperBitOpCode.BINARY_ADD),
        ])
        
        opt = CompressionPass()
        optimized = opt.optimize(stream)
        
        assert len(optimized.tokens) == 1
        assert optimized.tokens[0].opcode == SuperBitOpCode.LOAD_CONST
        assert optimized.tokens[0].operand == 8
    
    def test_compression_pass_handles_division(self):
        """Test compression pass handles division."""
        from src.null_system.superbit.tokens import SuperBitToken, SuperBitStream
        
        stream = SuperBitStream(tokens=[
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 10),
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 2),
            SuperBitToken(SuperBitOpCode.BINARY_DIV),
        ])
        
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
