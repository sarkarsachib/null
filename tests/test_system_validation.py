"""System validation tests for end-to-end compilation and execution."""

import os
import pytest
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from null_system.compiler import NullCompiler, CompilationError
from null_system.compiler.optimization import DeduplicationPass, CompressionPass
from null_system.superbit.ir import SuperBitOpCode, SuperBitIRToken, SuperBitStream
from null_system.vm.vm import NullVM, ExecutionResult
from null_system.lib.registry import default_registry
from tests.fixtures.hybrid_executor import HybridExecutor, simple_offload_strategy, AcceleratorType


class TestEndToEndCompilation:
    """End-to-end tests using example .null files."""
    
    @pytest.fixture
    def examples_dir(self):
        return Path(__file__).parent.parent / "examples"
    
    def test_hello_world_e2e(self, examples_dir):
        source_file = examples_dir / "hello.null"
        with open(source_file) as f:
            source = f.read()
        
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        assert artifact.is_valid()
        assert len(artifact.ast.statements) > 0
        assert len(artifact.superbit_stream.tokens) > 0
        assert len(artifact.binary_frames) > 0
        
        result = compiler.compile_and_run(source)
        assert result.success
        assert "Hello, World!" in result.output
    
    def test_arithmetic_e2e(self, examples_dir):
        source_file = examples_dir / "arithmetic.null"
        with open(source_file) as f:
            source = f.read()
        
        compiler = NullCompiler(optimization_passes=[
            DeduplicationPass(),
            CompressionPass()
        ])
        artifact = compiler.compile(source)
        
        assert artifact.is_valid()
        assert len(artifact.superbit_stream.tokens) > 0
        
        result = compiler.compile_and_run(source)
        assert result.success
        assert len(result.output) > 0
    
    def test_conditional_e2e(self, examples_dir):
        source_file = examples_dir / "conditional.null"
        with open(source_file) as f:
            source = f.read()
        
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        assert artifact.is_valid()
        
        result = compiler.compile_and_run(source)
        assert result.success
        assert "adult" in result.output
    
    def test_comprehensive_e2e(self, examples_dir):
        source_file = examples_dir / "comprehensive.null"
        with open(source_file) as f:
            source = f.read()
        
        compiler = NullCompiler(optimization_passes=[CompressionPass()])
        artifact = compiler.compile(source)
        
        assert artifact.is_valid()
        assert len(artifact.ast.statements) > 10
        
        result = compiler.compile_and_run(source)
        assert result.success
        assert len(result.output) > 5
        assert "Calculation complete!" in result.output
    
    def test_superbit_stream_consistency(self, examples_dir):
        source_file = examples_dir / "arithmetic.null"
        with open(source_file) as f:
            source = f.read()
        
        compiler = NullCompiler()
        artifact1 = compiler.compile(source)
        artifact2 = compiler.compile(source)
        
        assert len(artifact1.superbit_stream.tokens) == len(artifact2.superbit_stream.tokens)
        
        for t1, t2 in zip(artifact1.superbit_stream.tokens, artifact2.superbit_stream.tokens):
            assert t1.opcode == t2.opcode
            assert t1.operand == t2.operand
    
    def test_binary_frame_consistency(self, examples_dir):
        source_file = examples_dir / "hello.null"
        with open(source_file) as f:
            source = f.read()
        
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        assert len(artifact.binary_frames) > 0
        
        for frame in artifact.binary_frames:
            frame_bytes = frame.to_bytes()
            assert len(frame_bytes) > 0
            assert isinstance(frame_bytes, bytes)


class TestCrossModuleIntegration:
    """Tests that exercise multiple library modules together."""
    
    def test_math_and_text_ops_combined(self):
        source = """
set x to 10
set y to 5
add x and y
print 'Result is calculated'
print x
"""
        compiler = NullCompiler()
        result = compiler.compile_and_run(source)
        
        assert result.success
        assert "Result is calculated" in result.output
        assert "10" in result.output
        assert result.final_state["x"] == 10
        assert result.final_state["y"] == 5
    
    def test_multiple_conditionals_with_math(self):
        source = """
set value to 100
if value is greater than 50 then print 'high' else print 'low'
set threshold to 25
if threshold is less than value then print 'threshold exceeded' else print 'within threshold'
"""
        compiler = NullCompiler()
        result = compiler.compile_and_run(source)
        
        assert result.success
        assert "high" in result.output
        assert "threshold exceeded" in result.output
    
    def test_library_registry_integration(self):
        registry = default_registry()
        
        assert registry is not None
        
        available_functions = registry.available()
        assert len(available_functions) > 0
    
    def test_complex_calculation_chain(self):
        source = """
set a to 5
set b to 3
add a and b
set c to 2
multiply a and c
print a
"""
        compiler = NullCompiler()
        result = compiler.compile_and_run(source)
        
        assert result.success
        assert result.final_state["a"] == 5
        assert result.final_state["b"] == 3
        assert result.final_state["c"] == 2


class TestHybridExecution:
    """Tests for hybrid execution with mock accelerators."""
    
    @pytest.fixture
    def hybrid_executor(self):
        executor = HybridExecutor()
        executor.set_offload_strategy(simple_offload_strategy)
        return executor
    
    def test_cpu_execution(self, hybrid_executor):
        source = "set x to 5"
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        result = hybrid_executor.execute_hybrid(artifact.superbit_stream)
        
        assert result.success
        stats = hybrid_executor.get_stats()
        assert stats["total_tasks"] == 1
    
    def test_gpu_offload_simulation(self, hybrid_executor):
        source = """
set x to 1
set y to 2
add x and y
set z to 3
multiply z and 4
add x and z
subtract y and z
multiply x and y
"""
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        result = hybrid_executor.execute_hybrid(artifact.superbit_stream)
        
        assert result.success
    
    def test_ml_layer_offload(self, hybrid_executor):
        tokens = [
            SuperBitIRToken(
                opcode=SuperBitOpCode.LOAD_CONST,
                operand=42,
                metadata={"layer": "ml"}
            )
        ]
        stream = SuperBitStream(tokens=tokens)
        
        result = hybrid_executor.execute_hybrid(stream)
        
        assert result.success
        assert result.final_state.get("_ml_inference") is True
    
    def test_nlp_layer_offload(self, hybrid_executor):
        tokens = [
            SuperBitIRToken(
                opcode=SuperBitOpCode.LOAD_CONST,
                operand="test",
                metadata={"layer": "nlp"}
            )
        ]
        stream = SuperBitStream(tokens=tokens)
        
        result = hybrid_executor.execute_hybrid(stream)
        
        assert result.success
        assert result.final_state.get("_nlp_processed") is True
    
    def test_hybrid_state_consistency(self, hybrid_executor):
        source = "set counter to 0"
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        initial_state = {"counter": 0}
        result = hybrid_executor.execute_hybrid(artifact.superbit_stream, initial_state)
        
        assert result.success


class TestDistributedConsistency:
    """Tests for distributed execution consistency."""
    
    def test_multiple_vm_instances_same_program(self):
        source = """
set x to 10
set y to 20
add x and y
"""
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        vm1 = NullVM()
        vm2 = NullVM()
        vm3 = NullVM()
        
        result1 = vm1.execute(artifact.superbit_stream)
        result2 = vm2.execute(artifact.superbit_stream)
        result3 = vm3.execute(artifact.superbit_stream)
        
        assert result1.success and result2.success and result3.success
        assert result1.final_state == result2.final_state == result3.final_state
    
    def test_state_snapshot_consistency(self):
        source = """
set a to 5
set b to 10
set c to 15
"""
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        vms = [NullVM() for _ in range(5)]
        results = [vm.execute(artifact.superbit_stream) for vm in vms]
        
        assert all(r.success for r in results)
        
        first_state = results[0].final_state
        for result in results[1:]:
            assert result.final_state == first_state
    
    def test_synchronized_execution_consistency(self):
        source = "set value to 42"
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        snapshots = []
        for i in range(10):
            vm = NullVM()
            result = vm.execute(artifact.superbit_stream)
            snapshots.append(result.final_state.copy())
        
        for snapshot in snapshots:
            assert snapshot["value"] == 42


class TestFaultInjection:
    """Tests for fault injection and error recovery."""
    
    def test_parser_fault_recovery(self):
        invalid_source = "set x to y z"
        
        compiler = NullCompiler()
        with pytest.raises(CompilationError):
            compiler.compile(invalid_source)
    
    def test_optimizer_fault_simulation(self):
        source = "set x to 5"
        
        class FaultyOptimizationPass:
            def optimize(self, stream):
                raise RuntimeError("Simulated optimizer failure")
        
        compiler = NullCompiler(optimization_passes=[FaultyOptimizationPass()])
        
        with pytest.raises(CompilationError):
            compiler.compile(source)
    
    def test_vm_execution_fault_handling(self):
        source = "print undefined_variable"
        
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        assert not artifact.is_valid()
        assert len(artifact.validation_errors) > 0
    
    def test_division_by_zero_handling(self):
        tokens = [
            SuperBitIRToken(opcode=SuperBitOpCode.LOAD_CONST, operand=10),
            SuperBitIRToken(opcode=SuperBitOpCode.LOAD_CONST, operand=0),
            SuperBitIRToken(opcode=SuperBitOpCode.BINARY_DIV, operand=None)
        ]
        stream = SuperBitStream(tokens=tokens)
        
        vm = NullVM()
        result = vm.execute(stream)
        
        assert not result.success
        assert "Division by zero" in result.error
    
    def test_stack_underflow_handling(self):
        tokens = [
            SuperBitIRToken(opcode=SuperBitOpCode.BINARY_ADD, operand=None)
        ]
        stream = SuperBitStream(tokens=tokens)
        
        vm = NullVM()
        result = vm.execute(stream)
        
        assert not result.success
        assert ("underflow" in result.error.lower() or "pop from empty list" in result.error.lower())
    
    def test_graceful_error_reporting(self):
        source = "set x to 5"
        
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        vm = NullVM()
        
        with patch.object(vm, '_execute_token', side_effect=RuntimeError("Simulated error")):
            result = vm.execute(artifact.superbit_stream)
            
            assert not result.success
            assert len(result.error) > 0
    
    def test_recovery_after_error(self):
        tokens_error = [
            SuperBitIRToken(opcode=SuperBitOpCode.LOAD_CONST, operand=10),
            SuperBitIRToken(opcode=SuperBitOpCode.LOAD_CONST, operand=0),
            SuperBitIRToken(opcode=SuperBitOpCode.BINARY_DIV, operand=None)
        ]
        stream_error = SuperBitStream(tokens=tokens_error)
        
        vm = NullVM()
        result_error = vm.execute(stream_error)
        assert not result_error.success
        
        tokens_ok = [
            SuperBitIRToken(opcode=SuperBitOpCode.LOAD_CONST, operand=5),
            SuperBitIRToken(opcode=SuperBitOpCode.STORE_VAR, operand="x")
        ]
        stream_ok = SuperBitStream(tokens=tokens_ok)
        
        result_ok = vm.execute(stream_ok)
        assert result_ok.success
        assert result_ok.final_state["x"] == 5


class TestConsistencyValidation:
    """Tests to ensure consistency across the compilation pipeline."""
    
    def test_ast_to_superbit_token_count(self):
        source = """
set x to 10
set y to 20
add x and y
"""
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        assert len(artifact.ast.statements) == 3
        assert len(artifact.superbit_stream.tokens) >= 6
    
    def test_optimization_preserves_semantics(self):
        source = """
set x to 5
set y to 3
add x and y
"""
        compiler_no_opt = NullCompiler(optimization_passes=[])
        compiler_opt = NullCompiler(optimization_passes=[CompressionPass()])
        
        result_no_opt = compiler_no_opt.compile_and_run(source)
        result_opt = compiler_opt.compile_and_run(source)
        
        assert result_no_opt.success and result_opt.success
        assert result_no_opt.final_state["x"] == result_opt.final_state["x"]
    
    def test_binary_frames_match_superbit_stream(self):
        source = "set x to 42"
        
        compiler = NullCompiler()
        artifact = compiler.compile(source)
        
        assert len(artifact.binary_frames) > 0
        assert len(artifact.superbit_stream.tokens) > 0
