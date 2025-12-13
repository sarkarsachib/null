"""NullVM - Virtual machine for executing super-bit code."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..superbit.ir import SuperBitIRToken as SuperBitToken, SuperBitStream, SuperBitOpCode


@dataclass
class ExecutionResult:
    """Result of VM execution."""
    success: bool
    output: List[str] = field(default_factory=list)
    error: str = ""
    final_state: Dict[str, Any] = field(default_factory=dict)


class NullVM:
    """Virtual machine for executing super-bit code."""
    
    def __init__(self):
        self.stack: List[Any] = []
        self.variables: Dict[str, Any] = {}
        self.output: List[str] = []
        self.pc = 0
    
    def execute(self, superbit_stream: SuperBitGroup) -> ExecutionResult:
        """Execute a super-bit stream."""
        self.stack = []
        self.variables = {}
        self.output = []
        self.pc = 0
        
        try:
            while self.pc < len(superbit_stream.tokens):
                token = superbit_stream.tokens[self.pc]
                self._execute_token(token)
                self.pc += 1
            
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
                self.pc = token.operand - 1
        
        elif token.opcode == SuperBitOpCode.JUMP:
            self.pc = token.operand - 1
        
        elif token.opcode == SuperBitOpCode.NOP:
            pass
