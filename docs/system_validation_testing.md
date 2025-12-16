# System Validation Testing

This document describes the comprehensive system validation test suite for Null-Lang, designed to ensure stability and correctness across the entire compilation and execution pipeline.

## Overview

The system validation tests go beyond unit and integration tests to verify:
- End-to-end compilation from English → super-bits → VM output
- Cross-module cooperation (ML/NLP operations)
- Hybrid execution with accelerator offloading
- Distributed consistency across multiple VM instances
- Fault injection and recovery scenarios
- Load and stress testing at scale

## Test Structure

### 1. End-to-End Compilation Tests (`TestEndToEndCompilation`)

Located in `tests/test_system_validation.py`, these tests exercise the full compilation pipeline using real example programs from `examples/*.null`:

- **hello.null** - Basic print statement validation
- **arithmetic.null** - Mathematical operations with optimizations
- **conditional.null** - Control flow verification
- **comprehensive.null** - Complex program with multiple features

**Key Validations:**
- AST generation correctness
- SuperBit stream consistency
- Binary frame generation
- Deterministic compilation (same input → same output)

### 2. Cross-Module Integration Tests (`TestCrossModuleIntegration`)

Tests that combine operations from multiple library modules:

- Math + Text operations
- Multiple conditionals with calculations
- Library registry integration
- Complex calculation chains

**Purpose:** Ensure that different subsystems work together correctly and maintain consistent state.

### 3. Hybrid Execution Tests (`TestHybridExecution`)

Uses `tests/fixtures/hybrid_executor.py` to simulate offloading work to specialized accelerators:

**Accelerator Types:**
- CPU (default execution)
- GPU (parallel computation)
- ML_ENGINE (machine learning inference)
- NLP_ENGINE (natural language processing)

**Offload Strategy:**
The hybrid executor supports custom strategies that examine token metadata (e.g., `@layer(ml)` annotations) and route work to appropriate accelerators.

**Key Tests:**
- CPU baseline execution
- GPU offload for large workloads
- ML/NLP layer routing via metadata
- State consistency after hybrid execution

### 4. Distributed Consistency Tests (`TestDistributedConsistency`)

Validates that multiple VM instances execute the same program identically:

- Spawn 3-10 VM instances
- Execute identical programs
- Compare final states (must be identical)
- Verify snapshot consistency

**Critical for:** Distributed execution scenarios and parallel workload processing.

### 5. Fault Injection Tests (`TestFaultInjection`)

Systematically inject failures at various pipeline stages:

**Failure Scenarios:**
- Parser errors (syntax errors)
- Optimizer crashes (simulated internal errors)
- VM execution errors (undefined variables)
- Division by zero
- Stack underflow
- Runtime exceptions during execution

**Key Validations:**
- Graceful error reporting
- Error messages contain diagnostic information
- VM can recover after errors
- State remains valid after partial execution

### 6. Consistency Validation Tests (`TestConsistencyValidation`)

Verify that different pipeline stages remain consistent:

- AST statement count ↔ SuperBit token count
- Optimization preserves semantics (no-opt vs. optimized)
- Binary frames match SuperBit stream

## Load & Stress Tests

Located in `tests/perf/test_load.py` and marked with `@pytest.mark.load`.

### Running Load Tests

```bash
# Run all load tests
pytest tests/perf/test_load.py -v -m load

# Run specific load test
pytest tests/perf/test_load.py::TestLoadScenarios::test_compile_1000_simple_programs -v -m load

# Skip load tests (default behavior)
pytest tests/ -v -m "not load"
```

### Load Test Scenarios

#### TestLoadScenarios

1. **test_compile_1000_simple_programs**
   - Compile 1,000 simple programs sequentially
   - Measures throughput (programs/second)
   - Validates all compilations succeed

2. **test_execute_1000_programs**
   - Compile and execute 1,000 programs
   - End-to-end throughput measurement
   - Validates consistent execution

3. **test_concurrent_compilation_threads**
   - 1,000 programs compiled across 100 worker threads
   - Tests thread safety of compiler
   - Validates no race conditions

4. **test_concurrent_execution_threads**
   - 1,000 programs executed across 100 worker threads
   - Tests VM isolation and thread safety
   - Validates independent execution contexts

5. **test_vm_state_isolation_under_load**
   - 1,000 VMs with different initial states
   - Concurrent execution
   - Validates perfect state isolation (no cross-contamination)

6. **test_memory_stability_under_load**
   - 1,000 iterations of same program
   - Detects memory leaks and state corruption
   - Validates consistent results

7. **test_optimizer_performance_under_load**
   - Compare optimized vs. unoptimized throughput
   - Measure optimization overhead
   - Validate optimization correctness at scale

8. **test_race_condition_detection**
   - Shared state with concurrent modifications
   - Validates locking mechanisms
   - Detects race conditions

9. **test_compilation_consistency_under_concurrent_load**
   - 100 concurrent compilations of same program
   - Validates deterministic output
   - Ensures no non-deterministic behavior

#### TestStressScenarios

1. **test_large_program_compilation**
   - Compile program with 10,000 statements
   - Tests scalability of compiler
   - Validates handling of large ASTs

2. **test_deep_variable_dependencies**
   - 1,000 sequential variable assignments
   - Tests state management at scale
   - Validates deep execution stacks

3. **test_burst_compilation_load**
   - 10 bursts of 500 compilations each
   - Tests sustained high-load performance
   - Validates no performance degradation over time

## Interpreting Test Results

### Success Criteria

All tests (except load tests) should pass within CI time budgets:
- System validation tests: < 1 second
- Integration tests: < 1 second
- Load tests (opt-in): < 60 seconds per test

### Performance Metrics

Load tests output performance metrics:
```
Compiled 1000 programs in 0.50s (2000 programs/s)
Executed 1000 programs concurrently in 0.30s with 100 threads
```

**Expected Throughput:**
- Compilation: > 100 programs/second
- Execution: > 50 programs/second
- Concurrent (100 threads): > 1000 programs in < 1 second

### Common Failures

1. **Inconsistent State** - Usually indicates non-deterministic behavior or race conditions
2. **Performance Regression** - Throughput drops below expected thresholds
3. **Memory Leaks** - Memory usage grows unbounded during iterations
4. **Race Conditions** - Intermittent failures in concurrent tests

## Adding New Tests

### System Validation Test

```python
class TestMyFeature:
    def test_my_scenario(self):
        source = "set x to 42"
        compiler = NullCompiler()
        result = compiler.compile_and_run(source)
        
        assert result.success
        assert result.final_state["x"] == 42
```

### Load Test

```python
@pytest.mark.load
class TestMyLoadScenario:
    def test_my_load_case(self):
        # Perform load test
        pass
```

## CI Integration

The test suite integrates with CI as follows:

```yaml
# Run standard tests (excludes load)
pytest tests/ -v -m "not load"

# Run load tests (separate job, optional)
pytest tests/perf/ -v -m load
```

## Best Practices

1. **Determinism** - All tests should be deterministic and repeatable
2. **Isolation** - Each test should be independent
3. **Speed** - Non-load tests should complete in < 1 second
4. **Coverage** - Test both success and failure paths
5. **Documentation** - Include docstrings explaining what each test validates

## Maintenance

When modifying the compiler or VM:

1. Run system validation tests: `pytest tests/test_system_validation.py -v`
2. Check consistency tests pass
3. Run load tests locally before merging: `pytest tests/perf/ -v -m load`
4. Update tests if behavior changes are intentional
5. Add new tests for new features

## References

- [IMPLEMENTATION.md](../IMPLEMENTATION.md) - Compiler architecture
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [pyproject.toml](../pyproject.toml) - Test configuration and markers
