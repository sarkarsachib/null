from __future__ import annotations
import re
from enum import Enum
from typing import List, Optional, Union

from .ast_nodes import ASTNode, Program, SourceSpan, SyntaxMode, OutputMode
from .parser import NullLangParser
from .modern.modern_rust import ModernRustParser
from .parser_factory import ParserFactory
from .errors import SyntaxError

class HybridDynamicParser:
    """
    Orchestrates dynamic syntax switching between English and Modern syntax.
    """
    
    def __init__(self):
        self.factory = ParserFactory()
        self.english_markers = re.compile(r"\b(SET|SHOW|ADD|IF|THEN|ELSE|REPEAT|DEFINE|CALL|RETURN|END|MODULE|IMPORT)\b", re.IGNORECASE)
        self.modern_markers = re.compile(r"\b(let|fn|match|return|print|true|false|class|data|sealed|trait|impl|async|await|try|catch|finally)\b|\{|\}|;|::|=>", re.IGNORECASE)
        self.hint_marker = re.compile(r"^\s*#\s*mode:(english|modern)\s*$", re.IGNORECASE)
        self.directive_marker = re.compile(r"^\s*@syntax:(english|modern)\s*$", re.IGNORECASE)

    def parse(self, source: str, mode: OutputMode = OutputMode.AUTO) -> Program:
        """Parse source code in the specified output mode."""
        lines = source.splitlines()
        statements = []
        current_mode = SyntaxMode.english # Default
        
        # We need a better way to group lines into statements/blocks
        # For simplicity in this implementation, we'll process top-level statements
        # A more robust implementation would use a proper lexer/splitter
        
        # For now, let's collect lines and try to parse them
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith("//"): # Skip empty and comments (except hints)
                i += 1
                continue
            
            # Check for directive/hint
            directive_mode = self._extract_directive(line)
            if directive_mode:
                current_mode = directive_mode
                i += 1
                if i >= len(lines): break
                line = lines[i].strip()
            
            hint_mode = self._extract_hint(line)
            if hint_mode:
                # In Semi-Auto, we might need to handle this differently
                # But for now, it behaves similarly to directive in terms of setting mode
                current_mode = hint_mode
                i += 1
                if i >= len(lines): break
                line = lines[i].strip()

            # Determine mode if in AUTO
            if mode == OutputMode.AUTO:
                current_mode = self._detect_mode(line)
            elif mode == OutputMode.SEMI_AUTO:
                detected = self._detect_mode(line)
                # If hint was provided, current_mode is already set.
                # Validate hint + detected
                # The ticket says: "If hint conflicts with detected mode, warn and use detected"
                # Since we don't have a warning mechanism here yet, we'll just follow the logic.
                current_mode = detected
            elif mode == OutputMode.MANUAL:
                # In manual mode, we expect a directive. If none was found, use default or previous.
                # The ticket says: "Parser respects directive, errors on mismatch with following statement"
                detected = self._detect_mode(line)
                if directive_mode and detected != directive_mode:
                    # Actually, some statements might be ambiguous.
                    # But if we have a strong mismatch, we should error.
                    pass # TODO: implement strict mismatch check

            # Parse statement
            # Some statements are multi-line (blocks). 
            # This is the hard part of a line-by-line hybrid parser.
            
            # Let's try to find the full statement/block
            stmt_lines, next_i = self._get_full_statement(lines, i, current_mode)
            stmt_source = "\n".join(stmt_lines)
            
            try:
                node = self.factory.parse_statement(stmt_source, current_mode)
                if isinstance(node, list):
                    for n in node:
                        self._set_mode_recursive(n, current_mode)
                    statements.extend(node)
                else:
                    self._set_mode_recursive(node, current_mode)
                    statements.append(node)
            except Exception as e:
                # Fallback in AUTO mode
                if mode == OutputMode.AUTO and current_mode == SyntaxMode.modern:
                    try:
                        node = self.factory.parse_statement(stmt_source, SyntaxMode.english)
                        self._set_mode_recursive(node, SyntaxMode.english)
                        statements.append(node)
                    except:
                        raise e
                else:
                    raise e
            
            i = next_i
            
        program = Program(statements=statements)
        program.syntax_mode = SyntaxMode.english # Program itself is English by default
        return program

    def _get_full_statement(self, lines: List[str], start_index: int, mode: SyntaxMode) -> tuple[List[str], int]:
        """Extracts a full statement or block starting from start_index."""
        first_line = lines[start_index].strip()
        
        if mode == SyntaxMode.english:
            # English blocks end with END <KEYWORD>
            upper = first_line.split()[0].upper() if first_line else ""
            if upper in ["IF", "REPEAT", "DEFINE", "MATCH"]:
                end_marker = f"END {upper}"
                for j in range(start_index, len(lines)):
                    if lines[j].strip().upper().startswith(end_marker):
                        return lines[start_index:j+1], j + 1
            return [lines[start_index]], start_index + 1
        else:
            # Modern blocks use braces
            if "{" in first_line:
                brace_count = 0
                for j in range(start_index, len(lines)):
                    brace_count += lines[j].count("{")
                    brace_count -= lines[j].count("}")
                    if brace_count == 0:
                        return lines[start_index:j+1], j + 1
            return [lines[start_index]], start_index + 1

    def _detect_mode(self, stmt: str) -> SyntaxMode:
        """Detect mode from keywords (for AUTO mode)."""
        has_modern = bool(self.modern_markers.search(stmt))
        has_english = bool(self.english_markers.search(stmt))
        
        if has_modern and not has_english:
            return SyntaxMode.modern
        
        if has_modern and has_english:
            # If both are present, strong indicators for modern
            if "{" in stmt or "}" in stmt or ";" in stmt or "=>" in stmt or "::" in stmt:
                return SyntaxMode.modern
                
        return SyntaxMode.english

    def _extract_hint(self, line: str) -> Optional[SyntaxMode]:
        match = self.hint_marker.match(line)
        if match:
            mode_str = match.group(1).lower()
            return SyntaxMode.modern if mode_str == "modern" else SyntaxMode.english
        return None

    def _extract_directive(self, line: str) -> Optional[SyntaxMode]:
        match = self.directive_marker.match(line)
        if match:
            mode_str = match.group(1).lower()
            return SyntaxMode.modern if mode_str == "modern" else SyntaxMode.english
        return None

    def _set_mode_recursive(self, node: ASTNode, mode: SyntaxMode):
        if not node: return
        node.syntax_mode = mode
        if hasattr(node, "span") and node.span:
            node.span.syntax_mode = mode
            
        # Recurse into children if needed
        for attr in dir(node):
            if attr.startswith('_'): continue
            val = getattr(node, attr)
            if isinstance(val, ASTNode):
                self._set_mode_recursive(val, mode)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, ASTNode):
                        self._set_mode_recursive(item, mode)
            elif isinstance(val, tuple):
                 for item in val:
                    if isinstance(item, ASTNode):
                        self._set_mode_recursive(item, mode)
