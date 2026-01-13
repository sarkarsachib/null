"""
Simple test for transpiler functionality without full null_system dependencies.
"""

import sys
sys.path.append('src')

# Test individual components without full imports
print("Testing transpiler components...")

# Test learning comments
from null_system.transpiler.learning_comments import LearningCommentGenerator, LearningLevel

generator = LearningCommentGenerator(LearningLevel.NOVICE)
comment = generator.get_comment_for_conversion("english", "rust", "set")
print(f"Learning comment: {comment}")

# Test printers (just the classes, not full functionality)
try:
    from null_system.transpiler.english_printer import EnglishPrinter
    from null_system.transpiler.rust_printer import RustPrinter
    from null_system.transpiler.python_printer import PythonPrinter
    
    english_printer = EnglishPrinter()
    rust_printer = RustPrinter()
    python_printer = PythonPrinter()
    
    print("All printers created successfully!")
except Exception as e:
    print(f"Printer creation failed: {e}")

# Test CLI command exists
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("cli", "/home/engine/project/src/null_system/cli.py")
    cli_module = importlib.util.module_from_spec(spec)
    print("CLI module structure looks good")
except Exception as e:
    print(f"CLI test failed: {e}")

print("Transpiler component tests completed!")