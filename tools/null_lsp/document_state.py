"""Document state management for Null-Lang LSP."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from lark.exceptions import UnexpectedInput, UnexpectedCharacters

from src.null_system.lang import NullLangParser, Program
from src.null_system.lib.registry import default_registry


@dataclass
class DocumentState:
    """Maintains AST, diagnostics, and metadata for a document."""
    
    uri: str
    text: str
    ast: Optional[Program] = None
    parse_error: Optional[str] = None
    diagnostics: List[Dict] = field(default_factory=list)
    defined_identifiers: Set[str] = field(default_factory=set)
    used_identifiers: Set[str] = field(default_factory=set)
    library_functions: Set[str] = field(default_factory=set)
    
    def update(self, text: str) -> None:
        """Update document text and reparse."""
        self.text = text
        self.diagnostics = []
        self.parse_error = None
        self.defined_identifiers = set()
        self.used_identifiers = set()
        self._parse_and_analyze()
    
    def _parse_and_analyze(self) -> None:
        """Parse document and collect identifiers and errors."""
        try:
            parser = NullLangParser()
            self.ast = parser.parse(self.text)
            self._collect_identifiers(self.ast)
            self._validate_identifiers()
        except (UnexpectedInput, UnexpectedCharacters) as e:
            self.ast = None
            self.parse_error = str(e)
            self._add_parse_diagnostic(e)
        except Exception as e:
            self.ast = None
            self.parse_error = str(e)
            self._add_error_diagnostic(str(e), e)
    
    def _add_parse_diagnostic(self, error: Exception) -> None:
        """Convert parser error to LSP diagnostic."""
        line = getattr(error, 'line', 1) - 1
        column = getattr(error, 'column', 0) - 1
        
        diagnostic = {
            'range': {
                'start': {'line': max(0, line), 'character': max(0, column)},
                'end': {'line': max(0, line), 'character': max(0, column + 1)},
            },
            'severity': 1,  # Error
            'message': str(error),
            'source': 'null-lsp-parser',
        }
        self.diagnostics.append(diagnostic)
    
    def _add_error_diagnostic(self, message: str, error: Exception) -> None:
        """Add a generic error diagnostic."""
        line = getattr(error, 'line', 1) - 1
        column = getattr(error, 'column', 0) - 1
        
        diagnostic = {
            'range': {
                'start': {'line': max(0, line), 'character': max(0, column)},
                'end': {'line': max(0, line), 'character': max(0, column + 10)},
            },
            'severity': 1,  # Error
            'message': message,
            'source': 'null-lsp',
        }
        self.diagnostics.append(diagnostic)
    
    def _collect_identifiers(self, node) -> None:
        """Recursively collect defined and used identifiers from AST."""
        if node is None:
            return
        
        node_type = type(node).__name__
        
        if node_type == 'SetCommand':
            if hasattr(node.target, 'name'):
                self.defined_identifiers.add(node.target.name)
            if node.value:
                self._collect_identifiers(node.value)
        elif node_type == 'DefineCommand':
            self.defined_identifiers.add(node.name)
            for param in node.parameters:
                self.defined_identifiers.add(param)
            for stmt in node.body:
                self._collect_identifiers(stmt)
        elif node_type == 'Identifier':
            self.used_identifiers.add(node.name)
        elif node_type == 'FunctionCall':
            self.used_identifiers.add(node.name)
            for arg in node.arguments:
                self._collect_identifiers(arg)
        elif node_type == 'NullLibAnnotation':
            lib_path = f"{node.lib_name}.{node.function}"
            self.library_functions.add(lib_path)
            for arg in node.arguments:
                self._collect_identifiers(arg)
        elif node_type == 'Program':
            for stmt in node.statements:
                self._collect_identifiers(stmt)
        elif node_type in ['IfCommand', 'RepeatCommand']:
            if hasattr(node, 'condition'):
                self._collect_identifiers(node.condition)
            if hasattr(node, 'body'):
                for stmt in node.body:
                    self._collect_identifiers(stmt)
            if hasattr(node, 'then_block'):
                for stmt in node.then_block:
                    self._collect_identifiers(stmt)
            if hasattr(node, 'else_block') and node.else_block:
                for stmt in node.else_block:
                    self._collect_identifiers(stmt)
        elif node_type == 'SetCommand':
            if node.value:
                self._collect_identifiers(node.value)
        elif node_type in ['ShowCommand', 'AddCommand', 'BinaryExpression', 'UnaryExpression']:
            if hasattr(node, 'value'):
                self._collect_identifiers(node.value)
            if hasattr(node, 'operands'):
                for op in node.operands:
                    self._collect_identifiers(op)
            if hasattr(node, 'left'):
                self._collect_identifiers(node.left)
            if hasattr(node, 'right'):
                self._collect_identifiers(node.right)
            if hasattr(node, 'operand'):
                self._collect_identifiers(node.operand)
        elif hasattr(node, '__dict__'):
            for attr in node.__dict__.values():
                if isinstance(attr, list):
                    for item in attr:
                        self._collect_identifiers(item)
                elif hasattr(attr, '__dict__'):
                    self._collect_identifiers(attr)
    
    def _validate_identifiers(self) -> None:
        """Check for undefined variable references."""
        builtins = {
            'TRUE', 'FALSE', 'ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE',
            'SET', 'SHOW', 'IF', 'THEN', 'ELSE', 'REPEAT', 'DEFINE', 'TIMES',
            'AND', 'OR', 'NOT', 'IS', 'EQUALS', 'GREATER', 'LESS', 'THAN'
        }
        
        registry = default_registry()
        available_libs = set(registry.available())
        
        undefined = self.used_identifiers - self.defined_identifiers - builtins
        
        for var in undefined:
            if not var.startswith('print') and var.lower() not in [f.lower() for f in builtins]:
                self._add_undefined_diagnostic(var)
    
    def _add_undefined_diagnostic(self, identifier: str) -> None:
        """Add diagnostic for undefined identifier."""
        lines = self.text.split('\n')
        for line_num, line in enumerate(lines):
            if identifier in line:
                col = line.find(identifier)
                diagnostic = {
                    'range': {
                        'start': {'line': line_num, 'character': col},
                        'end': {'line': line_num, 'character': col + len(identifier)},
                    },
                    'severity': 2,  # Warning
                    'message': f"Undefined identifier: {identifier}",
                    'source': 'null-lsp-analyzer',
                }
                self.diagnostics.append(diagnostic)
                break
    
    def get_completions_at_position(self, line: int, character: int) -> List[Dict]:
        """Get completion items for a position."""
        registry = default_registry()
        available_libs = registry.available()
        
        keywords = [
            'SET', 'TO', 'ADD', 'AND', 'SUBTRACT', 'MULTIPLY', 'DIVIDE',
            'SHOW', 'IF', 'THEN', 'ELSE', 'REPEAT', 'TIMES',
            'DEFINE', 'TRUE', 'FALSE',
            'IS', 'EQUALS', 'GREATER', 'LESS', 'THAN', 'OR', 'NOT'
        ]
        
        completions = []
        
        for keyword in keywords:
            completions.append({
                'label': keyword,
                'kind': 14,  # Keyword
                'detail': f"Null-Lang keyword",
            })
        
        for identifier in sorted(self.defined_identifiers):
            completions.append({
                'label': identifier,
                'kind': 6,  # Variable
                'detail': "Defined variable",
            })
        
        for lib_func in sorted(available_libs):
            completions.append({
                'label': lib_func,
                'kind': 3,  # Function
                'detail': f"Library function from {lib_func.split('.')[0]}",
            })
        
        return completions
    
    def get_hover_info(self, line: int, character: int) -> Optional[str]:
        """Get hover information for a position."""
        registry = default_registry()
        available_libs = set(registry.available())
        
        lines = self.text.split('\n')
        if line >= len(lines):
            return None
        
        line_text = lines[line]
        if character >= len(line_text):
            return None
        
        word_start = character
        while word_start > 0 and line_text[word_start - 1].isalnum() or line_text[word_start - 1] == '_':
            word_start -= 1
        
        word_end = character
        while word_end < len(line_text) and (line_text[word_end].isalnum() or line_text[word_end] == '_' or line_text[word_end] == '.'):
            word_end += 1
        
        word = line_text[word_start:word_end]
        
        keywords_info = {
            'SET': 'SET <var> TO <value> - Assign a value to a variable',
            'SHOW': 'SHOW <expr> - Display output',
            'ADD': 'ADD <expr> AND <expr> - Add two values',
            'IF': 'IF <condition> THEN <stmt> [ELSE <stmt>] - Conditional execution',
            'REPEAT': 'REPEAT <count> TIMES <stmt> - Loop execution',
            'DEFINE': 'DEFINE <name> WITH <params> DOES <body> - Define a function',
            'TRUE': 'Boolean true value',
            'FALSE': 'Boolean false value',
        }
        
        if word.upper() in keywords_info:
            return keywords_info[word.upper()]
        
        if word in self.defined_identifiers:
            return f"Variable: {word}"
        
        if word in available_libs:
            lib, func = word.split('.')
            return f"Library function: {func} from {lib}"
        
        return None
