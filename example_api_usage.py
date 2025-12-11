#!/usr/bin/env python3
"""Example demonstrating the Null compiler API usage."""

from src.null_system.compiler import NullCompiler
from src.null_system.compiler.optimization import DeduplicationPass, CompressionPass


def main():
    """Demonstrate compiler API usage."""
    
    # Create compiler with optimization passes
    compiler = NullCompiler(optimization_passes=[
        DeduplicationPass(),
        CompressionPass()
    ])
    
    # Example 1: Simple compilation
    print("=" * 60)
    print("Example 1: Simple Compilation")
    print("=" * 60)
    
    source1 = """
    set x to 10
    set y to 5
    add x and y
    """
    
    artifact = compiler.compile(source1)
    
    if artifact.is_valid():
        print(f"✓ Compilation successful!")
        print(f"  - Statements: {len(artifact.ast.statements)}")
        print(f"  - Super-bit tokens: {len(artifact.superbit_stream.tokens)}")
        print(f"  - Binary size: {sum(len(f) for f in artifact.binary_frames)} bytes")
    else:
        print(f"✗ Compilation failed:")
        for error in artifact.validation_errors:
            print(f"  - {error}")
    
    # Example 2: Compile and run
    print("\n" + "=" * 60)
    print("Example 2: Compile and Run")
    print("=" * 60)
    
    source2 = """
    set message to 'Hello from Null-Lang!'
    print message
    
    set x to 15
    if x is greater than 10 then print 'Big number' else print 'Small number'
    """
    
    result = compiler.compile_and_run(source2)
    
    if result.success:
        print("✓ Execution successful!")
        print("\nProgram output:")
        for line in result.output:
            print(f"  > {line}")
        
        print("\nFinal state:")
        for var, val in result.final_state.items():
            print(f"  {var} = {val}")
    else:
        print(f"✗ Execution failed: {result.error}")
    
    # Example 3: Show optimization effect
    print("\n" + "=" * 60)
    print("Example 3: Optimization Effect")
    print("=" * 60)
    
    source3 = "add 5 and 3"
    
    # Compile without optimization
    compiler_no_opt = NullCompiler(optimization_passes=[])
    artifact_no_opt = compiler_no_opt.compile(source3)
    
    # Compile with optimization
    compiler_opt = NullCompiler(optimization_passes=[CompressionPass()])
    artifact_opt = compiler_opt.compile(source3)
    
    print(f"Without optimization: {len(artifact_no_opt.superbit_stream.tokens)} tokens")
    print(f"With optimization:    {len(artifact_opt.superbit_stream.tokens)} tokens")
    print(f"Reduction:            {len(artifact_no_opt.superbit_stream.tokens) - len(artifact_opt.superbit_stream.tokens)} tokens")
    
    print("\nOptimized super-bit stream:")
    print(artifact_opt.superbit_stream)
    
    # Example 4: Error handling
    print("\n" + "=" * 60)
    print("Example 4: Error Handling")
    print("=" * 60)
    
    source4 = "print undefined_variable"
    
    artifact = compiler.compile(source4)
    
    if not artifact.is_valid():
        print("✓ Validation correctly caught errors:")
        for error in artifact.validation_errors:
            print(f"  - {error}")
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
