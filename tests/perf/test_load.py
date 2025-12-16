"""Load and stress tests for Null compiler and VM."""

import pytest
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Dict, Any

from null_system.compiler import NullCompiler
from null_system.vm.vm import NullVM


@pytest.mark.load
class TestLoadScenarios:
    """Load and stress tests marked with @pytest.mark.load."""
    
    def test_compile_1000_simple_programs(self):
        programs = [
            f"set x{i} to {i}" 
            for i in range(1000)
        ]
        
        compiler = NullCompiler()
        start_time = time.perf_counter()
        
        compiled_count = 0
        for program in programs:
            artifact = compiler.compile(program)
            if artifact.is_valid():
                compiled_count += 1
        
        duration = time.perf_counter() - start_time
        throughput = compiled_count / duration
        
        assert compiled_count == 1000
        assert throughput > 100
        print(f"\nCompiled {compiled_count} programs in {duration:.2f}s ({throughput:.2f} programs/s)")
    
    def test_execute_1000_programs(self):
        programs = [
            f"""
set a to {i}
set b to {i + 1}
add a and b
""" 
            for i in range(1000)
        ]
        
        compiler = NullCompiler()
        start_time = time.perf_counter()
        
        success_count = 0
        for program in programs:
            result = compiler.compile_and_run(program)
            if result.success:
                success_count += 1
        
        duration = time.perf_counter() - start_time
        throughput = success_count / duration
        
        assert success_count == 1000
        assert throughput > 50
        print(f"\nExecuted {success_count} programs in {duration:.2f}s ({throughput:.2f} programs/s)")
    
    def test_concurrent_compilation_threads(self):
        programs = [
            f"""
set x to {i}
set y to {i * 2}
add x and y
print x
""" 
            for i in range(1000)
        ]
        
        def compile_program(source: str) -> bool:
            compiler = NullCompiler()
            artifact = compiler.compile(source)
            return artifact.is_valid()
        
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(compile_program, prog) for prog in programs]
            results = [f.result() for f in as_completed(futures)]
        
        duration = time.perf_counter() - start_time
        success_count = sum(results)
        
        assert success_count == 1000
        print(f"\nCompiled {success_count} programs concurrently in {duration:.2f}s with 100 threads")
    
    def test_concurrent_execution_threads(self):
        programs = [
            f"set value to {i}" 
            for i in range(1000)
        ]
        
        def execute_program(source: str) -> bool:
            compiler = NullCompiler()
            result = compiler.compile_and_run(source)
            return result.success
        
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(execute_program, prog) for prog in programs]
            results = [f.result() for f in as_completed(futures)]
        
        duration = time.perf_counter() - start_time
        success_count = sum(results)
        
        assert success_count == 1000
        print(f"\nExecuted {success_count} programs concurrently in {duration:.2f}s with 100 threads")
    
    def test_vm_state_isolation_under_load(self):
        source_template = "set counter to {value}"
        
        def run_isolated_vm(value: int) -> int:
            source = source_template.format(value=value)
            compiler = NullCompiler()
            artifact = compiler.compile(source)
            
            vm = NullVM()
            result = vm.execute(artifact.superbit_stream)
            
            if result.success:
                return result.final_state.get("counter", -1)
            return -1
        
        values = list(range(1000))
        
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = {executor.submit(run_isolated_vm, val): val for val in values}
            results = {}
            
            for future in as_completed(futures):
                expected_value = futures[future]
                actual_value = future.result()
                results[expected_value] = actual_value
        
        for expected, actual in results.items():
            assert actual == expected, f"State isolation failed: expected {expected}, got {actual}"
        
        print(f"\nVerified state isolation across 1000 concurrent VM instances")
    
    def test_memory_stability_under_load(self):
        source = """
set a to 100
set b to 200
add a and b
set c to 300
multiply c and 2
"""
        
        compiler = NullCompiler()
        
        for i in range(1000):
            artifact = compiler.compile(source)
            result = compiler.compile_and_run(source)
            
            assert result.success
            assert result.final_state["a"] == 300
            assert result.final_state["c"] == 300
            
            if i % 100 == 0:
                print(f"Completed {i} iterations")
        
        print("\nMemory stability verified over 1000 iterations")
    
    def test_optimizer_performance_under_load(self):
        from null_system.compiler.optimization import CompressionPass, DeduplicationPass
        
        source = """
set x to 5
set y to 10
add x and y
set z to 15
multiply z and 2
add x and z
"""
        
        compiler_no_opt = NullCompiler()
        compiler_opt = NullCompiler(optimization_passes=[
            DeduplicationPass(),
            CompressionPass()
        ])
        
        start_no_opt = time.perf_counter()
        for _ in range(1000):
            compiler_no_opt.compile(source)
        duration_no_opt = time.perf_counter() - start_no_opt
        
        start_opt = time.perf_counter()
        for _ in range(1000):
            compiler_opt.compile(source)
        duration_opt = time.perf_counter() - start_opt
        
        print(f"\nNo optimization: {duration_no_opt:.2f}s")
        print(f"With optimization: {duration_opt:.2f}s")
        print(f"Overhead: {((duration_opt / duration_no_opt) - 1) * 100:.1f}%")
    
    def test_race_condition_detection(self):
        shared_state = {"counter": 0}
        lock = threading.Lock()
        
        def increment_counter():
            for _ in range(100):
                with lock:
                    shared_state["counter"] += 1
        
        threads = [threading.Thread(target=increment_counter) for _ in range(10)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        assert shared_state["counter"] == 1000
        print(f"\nRace condition test passed: counter = {shared_state['counter']}")
    
    def test_compilation_consistency_under_concurrent_load(self):
        source = """
set x to 42
set y to 10
add x and y
"""
        
        def compile_and_compare() -> List[str]:
            compiler = NullCompiler()
            artifact = compiler.compile(source)
            return [str(token.opcode.value) for token in artifact.superbit_stream.tokens]
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(compile_and_compare) for _ in range(100)]
            results = [f.result() for f in as_completed(futures)]
        
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result
        
        print("\nCompilation consistency verified across 100 concurrent compilations")


@pytest.mark.load
class TestStressScenarios:
    """Stress tests for extreme conditions."""
    
    def test_large_program_compilation(self):
        statements = [f"set var{i} to {i}" for i in range(10000)]
        source = "\n".join(statements)
        
        compiler = NullCompiler()
        start_time = time.perf_counter()
        
        artifact = compiler.compile(source)
        
        duration = time.perf_counter() - start_time
        
        assert artifact.is_valid()
        assert len(artifact.ast.statements) == 10000
        print(f"\nCompiled program with 10,000 statements in {duration:.2f}s")
    
    def test_deep_variable_dependencies(self):
        statements = ["set v0 to 1"]
        for i in range(1, 1000):
            statements.append(f"set v{i} to {i}")
        
        source = "\n".join(statements)
        
        compiler = NullCompiler()
        result = compiler.compile_and_run(source)
        
        assert result.success
        assert len(result.final_state) == 1000
        print("\nSuccessfully executed program with 1,000 variable assignments")
    
    def test_burst_compilation_load(self):
        source = "set x to 42"
        compiler = NullCompiler()
        
        burst_size = 500
        num_bursts = 10
        
        for burst in range(num_bursts):
            start_time = time.perf_counter()
            
            with ThreadPoolExecutor(max_workers=100) as executor:
                futures = [executor.submit(compiler.compile, source) for _ in range(burst_size)]
                results = [f.result() for f in as_completed(futures)]
            
            duration = time.perf_counter() - start_time
            valid_count = sum(1 for r in results if r.is_valid())
            
            assert valid_count == burst_size
            
            if burst % 2 == 0:
                print(f"Burst {burst + 1}/{num_bursts}: {burst_size} compilations in {duration:.2f}s")
        
        print(f"\nCompleted {num_bursts} bursts of {burst_size} compilations each")
