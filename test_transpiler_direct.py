"""
Direct test of transpiler components without full null_system imports.
"""

import sys
sys.path.append('src')

# Test learning comments directly
import importlib.util
spec = importlib.util.spec_from_file_location("learning_comments", "/home/engine/project/src/null_system/transpiler/learning_comments.py")
learning_comments = importlib.util.module_from_spec(spec)
spec.loader.exec_module(learning_comments)

print("Testing LearningCommentGenerator...")
generator = learning_comments.LearningCommentGenerator(learning_comments.LearningLevel.NOVICE)
comment = generator.get_comment_for_conversion("english", "rust", "set")
print(f"Learning comment: {comment}")

# Test printers directly
spec = importlib.util.spec_from_file_location("english_printer", "/home/engine/project/src/null_system/transpiler/english_printer.py")
english_printer_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(english_printer_module)

spec = importlib.util.spec_from_file_location("rust_printer", "/home/engine/project/src/null_system/transpiler/rust_printer.py")
rust_printer_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rust_printer_module)

spec = importlib.util.spec_from_file_location("python_printer", "/home/engine/project/src/null_system/transpiler/python_printer.py")
python_printer_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(python_printer_module)

print("Testing printers...")
english_printer = english_printer_module.EnglishPrinter()
rust_printer = rust_printer_module.RustPrinter()
python_printer = python_printer_module.PythonPrinter()
print("All printers created successfully!")

# Test API structure
spec = importlib.util.spec_from_file_location("api", "/home/engine/project/src/null_system/transpiler/api.py")
api_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api_module)

print("API module structure looks good")

print("Direct transpiler component tests completed!")