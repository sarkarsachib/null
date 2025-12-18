"""
Transpiler API for Null-Lang.

High-level API for automatic translation between English, modern_rust, and modern_python syntaxes
with learning-path suggestions and explanatory comments.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from .english_printer import EnglishPrinter
from .rust_printer import RustPrinter
from .python_printer import PythonPrinter
from .learning_comments import LearningLevel, LearningCommentGenerator
from ..lang.parser_factory import ParserFactory, SyntaxMode
from ..lang.compiler import NullLangCompiler
from ..lang.ast_nodes import Program, ASTNode


class OutputFormat(Enum):
    """Output formats for transpiled code."""
    STRING = "string"
    FILE = "file"
    PREVIEW = "preview"


@dataclass
class TranspileOptions:
    """Options for transpilation."""
    from_mode: SyntaxMode
    to_mode: SyntaxMode
    learning_level: LearningLevel = LearningLevel.NOVICE
    add_comments: bool = True
    output_file: Optional[Path] = None
    preview_mode: bool = False
    
    def __post_init__(self):
        """Validate transpile options."""
        if self.from_mode == self.to_mode:
            raise ValueError("Source and target syntax modes cannot be the same")


def transpile(source: str, from_mode: SyntaxMode, to_mode: SyntaxMode, 
              learning_level: LearningLevel = LearningLevel.NOVICE,
              add_comments: bool = True) -> str:
    """Transpile source code from one syntax to another.
    
    Args:
        source: Source code to transpile
        from_mode: Source syntax mode
        to_mode: Target syntax mode
        learning_level: Level of learning comments to include
        add_comments: Whether to add explanatory comments
        
    Returns:
        Transpiled source code as a string
        
    Raises:
        ValueError: If from_mode == to_mode
        SyntaxError: If parsing fails
        RuntimeError: If compilation fails
    """
    if from_mode == to_mode:
        raise ValueError("Source and target syntax modes cannot be the same")
    
    # Parse source code
    parser_factory = ParserFactory()
    try:
        ast = parser_factory.parse(source, from_mode)
    except Exception as e:
        raise SyntaxError(f"Failed to parse {from_mode.value} source: {e}") from e
    
    # Compile to ensure semantic validity
    compiler = NullCompiler()
    try:
        compiler.visit(ast)
    except Exception as e:
        raise RuntimeError(f"Compilation failed: {e}") from e
    
    # Select appropriate printer
    printer = _get_printer(to_mode)
    
    # Generate transpiled code
    transpiled_code = printer.print_program(ast)
    
    # Add learning comments if requested
    if add_comments and learning_level != LearningLevel.ADVANCED:
        comment_generator = LearningCommentGenerator(learning_level)
        header_comment = comment_generator.get_file_header_comment(from_mode.value, to_mode.value)
        
        if header_comment:
            transpiled_code = f"{header_comment}\n\n{transpiled_code}"
    
    return transpiled_code


def transpile_file(input_file: Path, output_file: Path, from_mode: SyntaxMode, 
                   to_mode: SyntaxMode, learning_level: LearningLevel = LearningLevel.NOVICE,
                   add_comments: bool = True) -> bool:
    """Transpile a file from one syntax to another.
    
    Args:
        input_file: Path to input file
        output_file: Path to output file
        from_mode: Source syntax mode
        to_mode: Target syntax mode
        learning_level: Level of learning comments to include
        add_comments: Whether to add explanatory comments
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Read source file
        source = input_file.read_text(encoding='utf-8')
        
        # Transpile
        transpiled_code = transpile(source, from_mode, to_mode, learning_level, add_comments)
        
        # Write output file
        output_file.write_text(transpiled_code, encoding='utf-8')
        
        return True
        
    except Exception as e:
        print(f"Error transpiling file: {e}", file=sys.stderr)
        return False


def _get_printer(to_mode: SyntaxMode):
    """Get the appropriate printer for the target syntax mode."""
    if to_mode == SyntaxMode.english:
        return EnglishPrinter()
    elif to_mode in [SyntaxMode.modern, SyntaxMode.rust]:
        return RustPrinter()
    elif to_mode == SyntaxMode.python:
        return PythonPrinter()
    else:
        raise ValueError(f"Unsupported target syntax mode: {to_mode}")


def get_syntax_modes() -> Dict[str, SyntaxMode]:
    """Get all available syntax modes."""
    return {
        "english": SyntaxMode.english,
        "modern": SyntaxMode.modern,
        "rust": SyntaxMode.rust,
        "python": SyntaxMode.python,
        "auto": SyntaxMode.auto,
        "hybrid": SyntaxMode.hybrid,
    }


def validate_syntax_mode(mode: str) -> bool:
    """Validate if a syntax mode is supported."""
    supported_modes = {"english", "modern", "rust", "python"}
    return mode.lower() in supported_modes


def get_translation_examples(from_mode: SyntaxMode, to_mode: SyntaxMode) -> Dict[str, str]:
    """Get example translations for demonstration.
    
    Args:
        from_mode: Source syntax mode
        to_mode: Target syntax mode
        
    Returns:
        Dictionary mapping example names to translated code
    """
    examples = {}
    
    # Load example files if they exist
    examples_dir = Path(__file__).parent.parent.parent / "examples" / "dual_syntax"
    
    if from_mode == SyntaxMode.english:
        if to_mode in [SyntaxMode.modern, SyntaxMode.rust]:
            # English to Rust examples
            rust_files = ["counter_rust.null", "fibonacci_rust.null", "async_rust.null"]
            for filename in rust_files:
                file_path = examples_dir / filename
                if file_path.exists():
                    examples[filename.replace(".null", "")] = file_path.read_text()
        elif to_mode == SyntaxMode.python:
            # English to Python examples  
            python_files = ["counter_python.null", "fibonacci_python.null", "async_python.null"]
            for filename in python_files:
                file_path = examples_dir / filename
                if file_path.exists():
                    examples[filename.replace(".null", "")] = file_path.read_text()
    
    elif to_mode == SyntaxMode.english:
        if from_mode in [SyntaxMode.modern, SyntaxMode.rust]:
            # Rust to English examples
            rust_files = ["counter_rust.null", "fibonacci_rust.null", "async_rust.null"]
            for filename in rust_files:
                file_path = examples_dir / filename
                if file_path.exists():
                    # Read and convert to English
                    source = file_path.read_text()
                    try:
                        english_version = transpile(source, from_mode, to_mode)
                        examples[f"{filename.replace('.null', '')}_to_english"] = english_version
                    except Exception:
                        pass  # Skip if transpilation fails
        elif from_mode == SyntaxMode.python:
            # Python to English examples
            python_files = ["counter_python.null", "fibonacci_python.null", "async_python.null"]
            for filename in python_files:
                file_path = examples_dir / filename
                if file_path.exists():
                    # Read and convert to English
                    source = file_path.read_text()
                    try:
                        english_version = transpile(source, from_mode, to_mode)
                        examples[f"{filename.replace('.null', '')}_to_english"] = english_version
                    except Exception:
                        pass  # Skip if transpilation fails
    
    return examples