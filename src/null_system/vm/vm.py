"""NullVM - Virtual machine for executing super-bit code."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable

from ..superbit.tokens import EnhancedSuperBitToken as SuperBitToken, SuperBitStream, SuperBitOpCode


@dataclass
class ExecutionResult:
    """Result of VM execution."""
    success: bool
    output: List[str] = field(default_factory=list)
    error: str = ""
    final_state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VMState:
    """Snapshot of VM state at a point in execution."""
    pc: int
    stack: List[Any]
    variables: Dict[str, Any]
    output: List[str]


class NullVM:
    """Virtual machine for executing super-bit code."""
    
    def __init__(self):
        self.stack: List[Any] = []
        self.variables: Dict[str, Any] = {}
        self.output: List[str] = []
        self.pc = 0
        self.program: Optional[SuperBitStream] = None
        self.halted: bool = False
        self.pc_moved_callback: Optional[Callable[[int, int], None]] = None
    
    def load_program(self, superbit_stream: SuperBitStream):
        """Load a program for execution or debugging."""
        self.stack = []
        self.variables = {}
        self.output = []
        self.pc = 0
        self.program = superbit_stream
        self.halted = False
    
    def execute(self, superbit_stream: SuperBitStream) -> ExecutionResult:
        """Execute a super-bit stream."""
        self.load_program(superbit_stream)
        
        try:
            while self.pc < len(self.program.tokens) and not self.halted:
                self.step()
            
            return ExecutionResult(
                success=True,
                output=self.output,
                final_state=self.variables.copy()
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output=self.output,
                error=str(e),
                final_state=self.variables.copy()
            )
    
    def step(self) -> bool:
        """Execute a single instruction and return True if execution should continue.
        
        Returns:
            False if the program has halted or reached the end, True otherwise.
        """
        if self.program is None:
            raise RuntimeError("No program loaded")
        
        if self.halted or self.pc >= len(self.program.tokens):
            return False
        
        old_pc = self.pc
        token = self.program.tokens[self.pc]
        self._execute_token(token)
        
        if token.opcode not in [SuperBitOpCode.JUMP, SuperBitOpCode.JUMP_IF_FALSE]:
            self.pc += 1
        
        if self.pc_moved_callback:
            self.pc_moved_callback(old_pc, self.pc)
        
        return not self.halted and self.pc < len(self.program.tokens)
    
    def get_state(self) -> VMState:
        """Get a snapshot of the current VM state."""
        return VMState(
            pc=self.pc,
            stack=self.stack.copy(),
            variables=self.variables.copy(),
            output=self.output.copy()
        )
    
    def set_pc_moved_callback(self, callback: Callable[[int, int], None]):
        """Set a callback that is called when the program counter moves."""
        self.pc_moved_callback = callback
    
    def _execute_token(self, token: SuperBitToken):
        """Execute a single super-bit token."""
        if token.opcode == SuperBitOpCode.LOAD_CONST:
            self.stack.append(token.operand)
        
        elif token.opcode == SuperBitOpCode.LOAD_VAR:
            if token.operand not in self.variables:
                raise RuntimeError(f"Undefined variable: {token.operand}")
            self.stack.append(self.variables[token.operand])
        
        elif token.opcode == SuperBitOpCode.STORE_VAR:
            if not self.stack:
                raise RuntimeError("Stack underflow")
            value = self.stack.pop()
            self.variables[token.operand] = value
        
        elif token.opcode == SuperBitOpCode.BINARY_ADD:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left + right)
        
        elif token.opcode == SuperBitOpCode.BINARY_SUB:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left - right)
        
        elif token.opcode == SuperBitOpCode.BINARY_MUL:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left * right)
        
        elif token.opcode == SuperBitOpCode.BINARY_DIV:
            right = self.stack.pop()
            left = self.stack.pop()
            if right == 0:
                raise RuntimeError("Division by zero")
            self.stack.append(left / right)
        
        elif token.opcode == SuperBitOpCode.COMPARE_GT:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left > right)
        
        elif token.opcode == SuperBitOpCode.COMPARE_LT:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left < right)
        
        elif token.opcode == SuperBitOpCode.COMPARE_EQ:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left == right)
        
        elif token.opcode == SuperBitOpCode.PRINT:
            value = self.stack.pop()
            output_str = str(value)
            self.output.append(output_str)
        
        elif token.opcode == SuperBitOpCode.JUMP_IF_FALSE:
            condition = self.stack.pop()
            if not condition:
                self.pc = token.operand
            else:
                self.pc += 1
        
        elif token.opcode == SuperBitOpCode.JUMP:
            self.pc = token.operand
        
        elif token.opcode == SuperBitOpCode.HALT:
            self.halted = True
        
        elif token.opcode == SuperBitOpCode.NOP:
            pass
