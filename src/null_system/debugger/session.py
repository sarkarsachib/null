"""Debugger session for interactive debugging of Null-Lang programs."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..compiler.compiler import NullCompiler, CompilationArtifact
from ..vm.vm import NullVM, VMState
from ..superbit.tokens import SuperBitStream
from ..parser.lexer import Lexer
from ..parser.parser import Parser
from .breakpoint import Breakpoint


@dataclass
class DebuggerState:
    """Complete debugger state including VM state and breakpoints."""
    
    vm_state: VMState
    current_token_index: int
    current_line: Optional[int]
    current_file: Optional[str]
    breakpoints_hit: List[Breakpoint]
    is_paused: bool
    is_finished: bool


class NullDebuggerSession:
    """Interactive debugger session for Null-Lang programs.
    
    Provides capabilities to:
    - Compile source code with debug info
    - Set/remove breakpoints by file:line
    - Run/continue/step/step-over/step-out
    - Evaluate watch expressions
    - View multi-layer state (source, super-bit, binary, variables)
    """
    
    def __init__(self, source: str, source_file: str = "<input>"):
        self.source = source
        self.source_file = source_file
        self.source_lines = source.splitlines()
        
        self.compiler = NullCompiler()
        self.artifact: Optional[CompilationArtifact] = None
        self.vm = NullVM()
        
        self.breakpoints: List[Breakpoint] = []
        self.call_stack_depth = 0
        
        self.is_paused = False
        self.is_finished = False
        
        self._compile()
    
    def _compile(self):
        """Compile the source code with debug information."""
        self.artifact = self.compiler.compile(self.source)
        
        if not self.artifact.is_valid():
            raise ValueError(f"Compilation errors: {self.artifact.validation_errors}")
        
        self.vm.load_program(self.artifact.superbit_stream)
    
    def set_breakpoint(self, filename: str, line: int) -> Breakpoint:
        """Set a breakpoint at the given file and line.
        
        Args:
            filename: Source file (can be relative or '<input>')
            line: Line number (1-indexed)
            
        Returns:
            The created breakpoint
        """
        instruction_index = self._map_line_to_instruction(filename, line)
        
        bp = Breakpoint(
            filename=filename,
            line=line,
            instruction_index=instruction_index
        )
        self.breakpoints.append(bp)
        return bp
    
    def remove_breakpoint(self, filename: str, line: int) -> bool:
        """Remove breakpoint at the given location.
        
        Returns:
            True if a breakpoint was removed
        """
        for i, bp in enumerate(self.breakpoints):
            if bp.filename == filename and bp.line == line:
                self.breakpoints.pop(i)
                return True
        return False
    
    def list_breakpoints(self) -> List[Breakpoint]:
        """List all breakpoints."""
        return self.breakpoints.copy()
    
    def _map_line_to_instruction(self, filename: str, line: int) -> Optional[int]:
        """Map a source line to a super-bit instruction index."""
        if not self.artifact:
            return None
        
        for idx, token in enumerate(self.artifact.superbit_stream.tokens):
            if token.source_span:
                if token.source_span.line == line:
                    return idx
        
        return None
    
    def _check_breakpoints(self) -> List[Breakpoint]:
        """Check if any breakpoints are hit at current PC."""
        hit = []
        for bp in self.breakpoints:
            if bp.enabled and bp.instruction_index == self.vm.pc:
                if bp.hit():
                    hit.append(bp)
        return hit
    
    def run(self) -> DebuggerState:
        """Run the program until a breakpoint or end."""
        self.is_paused = False
        
        breakpoints_hit = self._check_breakpoints()
        if breakpoints_hit:
            self.is_paused = True
            return self._get_state(breakpoints_hit)
        
        while self.vm.step():
            breakpoints_hit = self._check_breakpoints()
            if breakpoints_hit:
                self.is_paused = True
                return self._get_state(breakpoints_hit)
        
        self.is_finished = True
        return self._get_state([])
    
    def continue_execution(self) -> DebuggerState:
        """Continue execution from current position."""
        if self.is_finished:
            return self._get_state([])
        
        self.is_paused = False
        
        if not self.vm.step():
            self.is_finished = True
            return self._get_state([])
        
        return self.run()
    
    def step(self) -> DebuggerState:
        """Execute a single instruction."""
        if self.is_finished:
            return self._get_state([])
        
        if not self.vm.step():
            self.is_finished = True
        
        self.is_paused = True
        return self._get_state([])
    
    def step_over(self) -> DebuggerState:
        """Step over function calls (not implemented for simple VM)."""
        return self.step()
    
    def step_out(self) -> DebuggerState:
        """Step out of current function (not implemented for simple VM)."""
        return self.run()
    
    def evaluate_watch(self, expression: str) -> Any:
        """Evaluate a watch expression in the current context.
        
        Args:
            expression: Expression to evaluate (e.g., variable name)
            
        Returns:
            The evaluated value
        """
        expression = expression.strip()
        
        if expression in self.vm.variables:
            return self.vm.variables[expression]
        
        try:
            lexer = Lexer(expression)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            
            emitter = self.compiler.emitter
            emitter.tokens = []
            for stmt in ast.statements:
                emitter._visit(stmt)
            
            temp_stream = SuperBitStream(tokens=emitter.tokens)
            temp_vm = NullVM()
            temp_vm.variables = self.vm.variables.copy()
            temp_vm.load_program(temp_stream)
            
            while temp_vm.step():
                pass
            
            if temp_vm.stack:
                return temp_vm.stack[-1]
            
            return None
        except Exception as e:
            return f"<error: {e}>"
    
    def get_current_line(self) -> Optional[int]:
        """Get the current source line number."""
        if not self.artifact or self.vm.pc >= len(self.artifact.superbit_stream.tokens):
            return None
        
        token = self.artifact.superbit_stream.tokens[self.vm.pc]
        if token.source_span:
            return token.source_span.line
        
        return None
    
    def get_current_token(self):
        """Get the current super-bit token."""
        if not self.artifact or self.vm.pc >= len(self.artifact.superbit_stream.tokens):
            return None
        
        return self.artifact.superbit_stream.tokens[self.vm.pc]
    
    def get_binary_offset(self) -> Optional[int]:
        """Get the current binary frame offset."""
        if not self.artifact:
            return None
        
        offset = 0
        for i in range(min(self.vm.pc, len(self.artifact.superbit_stream.tokens))):
            token = self.artifact.superbit_stream.tokens[i]
            offset += len(token.to_bytes())
        
        return offset
    
    def _get_state(self, breakpoints_hit: Optional[List[Breakpoint]] = None) -> DebuggerState:
        """Get current debugger state."""
        return DebuggerState(
            vm_state=self.vm.get_state(),
            current_token_index=self.vm.pc,
            current_line=self.get_current_line(),
            current_file=self.source_file,
            breakpoints_hit=breakpoints_hit or [],
            is_paused=self.is_paused,
            is_finished=self.is_finished
        )
    
    def get_source_context(self, lines_before: int = 2, lines_after: int = 2) -> List[tuple[int, str, bool]]:
        """Get source code context around current line.
        
        Returns:
            List of (line_number, line_text, is_current) tuples
        """
        current_line = self.get_current_line()
        if current_line is None:
            return []
        
        start = max(1, current_line - lines_before)
        end = min(len(self.source_lines), current_line + lines_after)
        
        result = []
        for line_num in range(start, end + 1):
            if 1 <= line_num <= len(self.source_lines):
                result.append((
                    line_num,
                    self.source_lines[line_num - 1],
                    line_num == current_line
                ))
        
        return result
