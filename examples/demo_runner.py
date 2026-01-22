#!/usr/bin/env python3
import os
import sys

# Add src to sys.path to allow importing null_system
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from null_system.lang.parser import NullLangParser
    from null_system.analysis.type_inference import TypeInference
    from null_system.lang.compiler import NullLangCompiler
except ImportError as e:
    print(f"Error importing Null-Lang components: {e}")
    print("Make sure you are running this from the project root.")
    sys.exit(1)

def run_demo(file_path):
    print(f"Program: {os.path.basename(file_path)}")
    
    with open(file_path, 'r') as f:
        source = f.read()
    
    # Step 1: Parse
    try:
        parser = NullLangParser()
        ast = parser.parse(source)
        print(f"✓ Parse: Success ({len(ast.statements)} statements)")
    except Exception as e:
        print(f"✗ Parse: Failed\n  Error: {e}")
        return False
    
    # Step 2: Type Inference
    try:
        inference = TypeInference()
        inference.infer(ast)
        if inference.errors:
            print(f"✗ Type Inference: Failed with {len(inference.errors)} errors")
            for err in inference.errors:
                print(f"  - {err}")
        else:
            print(f"✓ Type Inference: Success")
            # Print inferred types for some variables if it's type_inference.null
            if "type_inference.null" in file_path:
                for var, type_info in inference.context.variables.items():
                    print(f"  {var}: {type_info.nullable_name}")
    except Exception as e:
        print(f"✗ Type Inference: Failed with unexpected error\n  Error: {e}")
        return False
    
    # Step 3: Compilation
    try:
        compiler = NullLangCompiler()
        ir_stream = compiler.compile(ast)
        print(f"✓ Compilation: Success ({len(ir_stream.tokens)} IR tokens)")
    except Exception as e:
        print(f"✗ Compilation: Failed\n  Error: {e}")
        return False
    
    print("")
    return True

def main():
    print("=== Null-Lang Demo Runner ===\n")
    
    examples_dir = "examples"
    demo_files = [
        "basic_arithmetic.null",
        "type_inference.null",
        "null_safety.null",
        "control_flow.null",
        "modules_demo.null",
        "function_composition.null"
    ]
    
    success_count = 0
    total_count = len(demo_files)
    
    for demo_file in demo_files:
        file_path = os.path.join(examples_dir, demo_file)
        if os.path.exists(file_path):
            if run_demo(file_path):
                success_count += 1
        else:
            print(f"Skipping {demo_file}: File not found\n")
            total_count -= 1
            
    print(f"--- [{success_count}/{total_count} programs successful] ---")
    
    if success_count < total_count:
        sys.exit(1)

if __name__ == "__main__":
    main()
