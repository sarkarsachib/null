"""
Learning Comment Generator for Null-Lang Transpiler.

Adds explanatory comments when converting between syntaxes to help
users understand the differences and learn the target syntax.
"""

from typing import Dict, Optional
from enum import Enum


class LearningLevel(Enum):
    """Learning levels for transpilation."""
    BEGINNER = "beginner"
    NOVICE = "novice" 
    MODERATE = "moderate"
    ADVANCED = "advanced"


class LearningCommentGenerator:
    """Generates educational comments for syntax translations."""
    
    def __init__(self, learning_level: LearningLevel = LearningLevel.NOVICE):
        self.learning_level = learning_level
        
    def get_comment_for_conversion(self, from_syntax: str, to_syntax: str, 
                                 statement_type: str) -> Optional[str]:
        """Get an explanatory comment for a specific conversion."""
        if self.learning_level == LearningLevel.BEGINNER:
            return self._beginner_comment(from_syntax, to_syntax, statement_type)
        elif self.learning_level == LearningLevel.NOVICE:
            return self._novice_comment(from_syntax, to_syntax, statement_type)
        elif self.learning_level == LearningLevel.MODERATE:
            return self._moderate_comment(from_syntax, to_syntax, statement_type)
        else:
            return None
    
    def _beginner_comment(self, from_syntax: str, to_syntax: str, statement_type: str) -> str:
        """Generate beginner-level explanatory comments."""
        comments = {
            ("english", "rust", "set"): "In Rust, we use 'let' to create variables instead of 'SET ... TO'",
            ("english", "rust", "if"): "Rust uses braces '{}' instead of 'THEN...END' blocks",
            ("english", "rust", "show"): "Rust uses println!() macro for output instead of SHOW",
            ("english", "rust", "for"): "Rust uses for loops with 'in' keyword and range syntax '..'",
            ("english", "rust", "define"): "Functions in Rust start with 'fn' keyword",
            ("english", "rust", "repeat"): "Rust converts loops to for loops with range syntax",
            
            ("english", "python", "set"): "Python uses '=' for assignment instead of 'SET ... TO'",
            ("english", "python", "if"): "Python uses colons and indentation instead of 'THEN...END'",
            ("english", "python", "show"): "Python uses print() function instead of SHOW",
            ("english", "python", "for"): "Python uses for loops with range() function",
            ("english", "python", "define"): "Functions in Python start with 'def' keyword",
            ("english", "python", "repeat"): "Python converts loops to for loops with range()",
            
            ("rust", "english", "let"): "English uses natural language 'SET ... TO' instead of 'let'",
            ("rust", "english", "if"): "English uses 'IF...THEN...END' instead of braces",
            ("rust", "english", "println"): "English uses 'SHOW' instead of println!()",
            ("rust", "english", "for"): "English uses 'FOR...FROM...TO' instead of range syntax",
            ("rust", "english", "fn"): "English uses 'DEFINE...WITH...END' instead of 'fn'",
            
            ("python", "english", "assignment"): "English uses 'SET ... TO' instead of '='",
            ("python", "english", "if"): "English uses 'IF...THEN...END' instead of colons",
            ("python", "english", "print"): "English uses 'SHOW' instead of print()",
            ("python", "english", "for"): "English uses 'FOR...FROM...TO' instead of range()",
            ("python", "english", "def"): "English uses 'DEFINE...WITH...END' instead of 'def'",
        }
        
        key = (from_syntax, to_syntax, statement_type)
        return comments.get(key, f"Converting {statement_type} from {from_syntax} to {to_syntax}")
    
    def _novice_comment(self, from_syntax: str, to_syntax: str, statement_type: str) -> str:
        """Generate novice-level explanatory comments."""
        comments = {
            ("english", "rust", "set"): "Rust: 'let' creates variables; semicolons end statements",
            ("english", "rust", "if"): "Rust: braces define blocks; no 'THEN' keyword needed",
            ("english", "rust", "show"): "Rust: println!() is a macro for formatted output",
            ("english", "rust", "for"): "Rust: for loops use 'in' with ranges (start..end)",
            ("english", "rust", "define"): "Rust: 'fn' defines functions with braces for body",
            
            ("english", "python", "set"): "Python: '=' assigns values; no 'SET...TO' needed",
            ("english", "python", "if"): "Python: colons start blocks; indentation defines scope",
            ("english", "python", "show"): "Python: print() outputs values with parentheses",
            ("english", "python", "for"): "Python: range() generates sequences for iteration",
            ("english", "python", "define"): "Python: 'def' defines functions with colon and indent",
            
            ("rust", "english", "let"): "English: Natural language commands use SET...TO",
            ("rust", "english", "if"): "English: IF...THEN...END blocks use explicit keywords",
            ("rust", "english", "println"): "English: SHOW is the standard output command",
            ("rust", "english", "for"): "English: FOR...FROM...TO loop syntax",
            ("rust", "english", "fn"): "English: DEFINE...WITH...END function syntax",
            
            ("python", "english", "assignment"): "English: Natural language SET...TO assignment",
            ("python", "english", "if"): "English: Explicit IF...THEN...END keywords",
            ("python", "english", "print"): "English: SHOW command for output",
            ("python", "english", "for"): "English: FOR...FROM...TO iteration syntax",
            ("python", "english", "def"): "English: DEFINE...WITH...END function definition",
        }
        
        key = (from_syntax, to_syntax, statement_type)
        return comments.get(key, f"Translating {statement_type} to {to_syntax}")
    
    def _moderate_comment(self, from_syntax: str, to_syntax: str, statement_type: str) -> str:
        """Generate moderate-level explanatory comments."""
        comments = {
            ("english", "rust", "set"): "Rust: Variables are immutable by default; use 'mut' for mutability",
            ("english", "rust", "if"): "Rust: Expressions return values; last expression is return value",
            ("english", "rust", "show"): "Rust: println! uses format strings and interpolation",
            ("english", "rust", "for"): "Rust: Range operators '..' and '..=' for inclusive ranges",
            ("english", "rust", "define"): "Rust: Type annotations can be added to parameters and returns",
            
            ("english", "python", "set"): "Python: Variables are dynamic; types determined at runtime",
            ("english", "python", "if"): "Python: Indentation defines block structure; colon required",
            ("english", "python", "show"): "Python: print() supports multiple arguments and formatting",
            ("english", "python", "for"): "Python: range() is lazy-evaluated; supports step parameter",
            ("english", "python", "define"): "Python: Type hints optional; *args and **kwargs supported",
            
            ("rust", "english", "let"): "English: Natural language approach for beginners",
            ("rust", "english", "if"): "English: Explicit block structure aids readability",
            ("rust", "english", "println"): "English: Simple output without complex formatting",
            ("rust", "english", "for"): "English: Numeric range specification",
            ("rust", "english", "fn"): "English: Function definition with parameter names",
        }
        
        key = (from_syntax, to_syntax, statement_type)
        return comments.get(key, f"Modern {to_syntax} equivalent")
    
    def get_file_header_comment(self, from_syntax: str, to_syntax: str) -> str:
        """Get a header comment explaining the conversion."""
        if self.learning_level == LearningLevel.BEGINNER:
            return f"# This code was automatically translated from {from_syntax} to {to_syntax}"
        elif self.learning_level == LearningLevel.NOVICE:
            return f"# Translation: {from_syntax} → {to_syntax} (with learning annotations)"
        elif self.learning_level == LearningLevel.MODERATE:
            return f"# Transpiled from {from_syntax} to {to_syntax}"
        else:
            return ""