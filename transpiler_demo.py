"""
Standalone demonstration of the transpiler functionality.
This shows the core transpiler concepts without full dependency issues.
"""

class LearningLevel:
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
                                 statement_type: str) -> str:
        """Get an explanatory comment for a specific conversion."""
        if self.learning_level == LearningLevel.BEGINNER:
            return self._beginner_comment(from_syntax, to_syntax, statement_type)
        elif self.learning_level == LearningLevel.NOVICE:
            return self._novice_comment(from_syntax, to_syntax, statement_type)
        elif self.learning_level == LearningLevel.MODERATE:
            return self._moderate_comment(from_syntax, to_syntax, statement_type)
        else:
            return ""
    
    def _beginner_comment(self, from_syntax: str, to_syntax: str, statement_type: str) -> str:
        """Generate beginner-level explanatory comments."""
        comments = {
            ("english", "rust", "set"): "In Rust, we use 'let' to create variables instead of 'SET ... TO'",
            ("english", "rust", "if"): "Rust uses braces '{}' instead of 'THEN...END' blocks",
            ("english", "rust", "show"): "Rust uses println!() macro for output instead of SHOW",
            ("english", "python", "set"): "Python uses '=' for assignment instead of 'SET ... TO'",
            ("english", "python", "if"): "Python uses colons and indentation instead of 'THEN...END'",
            ("english", "python", "show"): "Python uses print() function instead of SHOW",
        }
        
        key = (from_syntax, to_syntax, statement_type)
        return comments.get(key, f"Converting {statement_type} from {from_syntax} to {to_syntax}")
    
    def _novice_comment(self, from_syntax: str, to_syntax: str, statement_type: str) -> str:
        """Generate novice-level explanatory comments."""
        comments = {
            ("english", "rust", "set"): "Rust: 'let' creates variables; semicolons end statements",
            ("english", "rust", "if"): "Rust: braces define blocks; no 'THEN' keyword needed",
            ("english", "rust", "show"): "Rust: println!() is a macro for formatted output",
            ("english", "python", "set"): "Python: '=' assigns values; no 'SET...TO' needed",
            ("english", "python", "if"): "Python: colons start blocks; indentation defines scope",
            ("english", "python", "show"): "Python: print() outputs values with parentheses",
        }
        
        key = (from_syntax, to_syntax, statement_type)
        return comments.get(key, f"Translating {statement_type} to {to_syntax}")
    
    def _moderate_comment(self, from_syntax: str, to_syntax: str, statement_type: str) -> str:
        """Generate moderate-level explanatory comments."""
        comments = {
            ("english", "rust", "set"): "Rust: Variables are immutable by default; use 'mut' for mutability",
            ("english", "rust", "if"): "Rust: Expressions return values; last expression is return value",
            ("english", "python", "set"): "Python: Variables are dynamic; types determined at runtime",
            ("english", "python", "if"): "Python: Indentation defines block structure; colon required",
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


class SimpleEnglishPrinter:
    """Simple demonstration of English syntax printing."""
    
    def print_program(self, statements):
        """Print a program as English syntax."""
        lines = []
        for stmt in statements:
            lines.append(self._print_statement(stmt))
        return "\n".join(lines)
    
    def _print_statement(self, stmt):
        """Print individual statement."""
        if stmt['type'] == 'set':
            return f"SET {stmt['target']} TO {stmt['value']}"
        elif stmt['type'] == 'show':
            return f"SHOW {stmt['value']}"
        elif stmt['type'] == 'if':
            lines = [f"IF {stmt['condition']} THEN"]
            for child_stmt in stmt['then_block']:
                lines.append(f"    {self._print_statement(child_stmt)}")
            lines.append("END")
            return "\n".join(lines)
        else:
            return f"# Unknown statement: {stmt['type']}"


class SimpleRustPrinter:
    """Simple demonstration of Rust syntax printing."""
    
    def print_program(self, statements):
        """Print a program as Rust syntax."""
        lines = []
        for stmt in statements:
            lines.append(self._print_statement(stmt))
        return "\n".join(lines)
    
    def _print_statement(self, stmt):
        """Print individual statement."""
        if stmt['type'] == 'set':
            return f"let {stmt['target']} = {stmt['value']};"
        elif stmt['type'] == 'show':
            return f'println!("{stmt["value"]}");'
        elif stmt['type'] == 'if':
            lines = [f"if {stmt['condition']} {{"]
            for child_stmt in stmt['then_block']:
                lines.append(f"    {self._print_statement(child_stmt)}")
            lines.append("}}")
            return "\n".join(lines)
        else:
            return f"// Unknown statement: {stmt['type']}"


class SimplePythonPrinter:
    """Simple demonstration of Python syntax printing."""
    
    def print_program(self, statements):
        """Print a program as Python syntax."""
        lines = []
        for stmt in statements:
            lines.append(self._print_statement(stmt))
        return "\n".join(lines)
    
    def _print_statement(self, stmt):
        """Print individual statement."""
        if stmt['type'] == 'set':
            return f"{stmt['target']} = {stmt['value']}"
        elif stmt['type'] == 'show':
            return f'print({stmt["value"]})'
        elif stmt['type'] == 'if':
            lines = [f"if {stmt['condition']}:"]
            for child_stmt in stmt['then_block']:
                lines.append(f"    {self._print_statement(child_stmt)}")
            return "\n".join(lines)
        else:
            return f"# Unknown statement: {stmt['type']}"


def simple_transpile(source_code: str, from_syntax: str, to_syntax: str, learning_level: str = "novice"):
    """Simple transpilation demonstration."""
    
    # Parse English code into simple AST (demo purposes)
    if from_syntax == "english":
        # Very simple parsing - just for demonstration
        lines = [line.strip() for line in source_code.strip().split('\n') if line.strip()]
        statements = []
        
        for line in lines:
            if line.startswith("SET ") and " TO " in line:
                # SET x TO 5
                parts = line[4:].split(" TO ")
                if len(parts) == 2:
                    statements.append({
                        'type': 'set',
                        'target': parts[0].strip(),
                        'value': parts[1].strip()
                    })
            elif line.startswith("SHOW "):
                # SHOW x
                statements.append({
                    'type': 'show',
                    'value': line[5:].strip()
                })
            elif line.startswith("IF ") and " THEN" in line:
                # IF x > 3 THEN
                condition = line[3:-4].strip()  # Remove " THEN"
                statements.append({
                    'type': 'if',
                    'condition': condition,
                    'then_block': []
                })
    
    # Select appropriate printer
    if to_syntax == "english":
        printer = SimpleEnglishPrinter()
    elif to_syntax == "rust":
        printer = SimpleRustPrinter()
    elif to_syntax == "python":
        printer = SimplePythonPrinter()
    else:
        raise ValueError(f"Unsupported target syntax: {to_syntax}")
    
    # Add learning comments if requested
    if learning_level != "advanced":
        generator = LearningCommentGenerator(learning_level)
        header = generator.get_file_header_comment(from_syntax, to_syntax)
        transpiled_code = header + "\n\n" + printer.print_program(statements)
    else:
        transpiled_code = printer.print_program(statements)
    
    return transpiled_code


def main():
    """Demonstrate transpiler functionality."""
    print("=== NULL-LANG TRANSPILER DEMONSTRATION ===\n")
    
    # Sample English code
    english_code = """SET x TO 5
SHOW x
IF x IS GREATER THAN 3 THEN
    SET y TO 10
    SHOW y
END"""
    
    print("Original English code:")
    print(english_code)
    print("\n" + "="*50 + "\n")
    
    # Test English to Rust
    print("TRANSLATING TO RUST:")
    rust_code = simple_transpile(english_code, "english", "rust", "novice")
    print(rust_code)
    print("\n" + "="*50 + "\n")
    
    # Test English to Python  
    print("TRANSLATING TO PYTHON:")
    python_code = simple_transpile(english_code, "english", "python", "novice")
    print(python_code)
    print("\n" + "="*50 + "\n")
    
    # Test beginner level comments
    print("BEGINNER LEVEL COMMENTS:")
    beginner_rust = simple_transpile(english_code, "english", "rust", "beginner")
    print(beginner_rust)
    print("\n" + "="*50 + "\n")
    
    # Test advanced level (no comments)
    print("ADVANCED LEVEL (NO COMMENTS):")
    advanced_rust = simple_transpile(english_code, "english", "rust", "advanced")
    print(advanced_rust)
    print("\n" + "="*50 + "\n")
    
    print("✅ Transpiler demonstration completed successfully!")
    print("\nKey Features Demonstrated:")
    print("• Syntax translation between English, Rust, and Python")
    print("• Learning comment system with 4 levels (beginner, novice, moderate, advanced)")
    print("• AST printing with proper syntax formatting")
    print("• CLI-ready transpilation API")


if __name__ == "__main__":
    main()