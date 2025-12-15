"""NullVM - Virtual machine for executing super-bit code."""

import resource
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..observability import get_observability
from ..superbit.ir import SuperBitIRToken as SuperBitToken, SuperBitOpCode, SuperBitStream


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
    
    def execute(self, superbit_stream: SuperBitStream) -> ExecutionResult:
        """Execute a super-bit stream."""
        obs = get_observability()

        self.stack = []
        self.variables = {}
        self.output = []
        self.pc = 0

        started = time.perf_counter()
        executed = 0

        with obs.tracing.span(
            "null.vm.execute",
            attributes={"token_count": len(superbit_stream.tokens)},
        ):
            try:
                while self.pc < len(superbit_stream.tokens):
                    token = superbit_stream.tokens[self.pc]
                    obs.metrics.inc_vm_instruction(opcode=token.opcode.name)
                    self._execute_token(token)

                    executed += 1
                    obs.metrics.set_vm_stack_depth(len(self.stack))
                    obs.metrics.set_vm_variable_count(len(self.variables))

                    self.pc += 1

                duration_s = time.perf_counter() - started
                obs.metrics.observe_vm_execution(duration_s=duration_s, status="ok")
                obs.metrics.set_process_max_rss_bytes(
                    int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
                )
                if duration_s > 0:
                    obs.metrics.set_vm_instruction_throughput(executed / duration_s)
                obs.logger.info(
                    "vm.execute",
                    status="ok",
                    duration_s=duration_s,
                    instructions=executed,
                )

                return ExecutionResult(
                    success=True,
                    output=self.output,
                    final_state=self.variables.copy(),
                )
            except Exception as e:
                duration_s = time.perf_counter() - started
                obs.metrics.observe_vm_execution(duration_s=duration_s, status="error")
                obs.metrics.set_process_max_rss_bytes(
                    int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
                )
                obs.metrics.inc_error(component="vm", error_type=type(e).__name__)
                obs.logger.exception(
                    "vm.execute",
                    status="error",
                    duration_s=duration_s,
                    instructions=executed,
                    error_type=type(e).__name__,
                )
                obs.capture_exception(e, component="vm", error_type=type(e).__name__)

                return ExecutionResult(
                    success=False,
                    output=self.output,
                    error=str(e),
                    final_state=self.variables.copy(),
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
        
        elif token.opcode == SuperBitOpCode.MATCH_TAG:
            if not self.stack:
                raise RuntimeError("Stack underflow for MATCH_TAG")
            value = self.stack.pop()
            if hasattr(value, 'tag') and value.tag == token.operand:
                self.stack.append(True)
            else:
                self.stack.append(False)

        elif token.opcode == SuperBitOpCode.UNWRAP_UNION:
            if not self.stack:
                raise RuntimeError("Stack underflow for UNWRAP_UNION")
            value = self.stack.pop()
            if hasattr(value, 'value'):
                self.stack.append(value.value)
            else:
                raise RuntimeError(f"Cannot unwrap non-union value: {value}")

        elif token.opcode == SuperBitOpCode.MATCH_PATTERN:
            if not self.stack:
                raise RuntimeError("Stack underflow for MATCH_PATTERN")
            value = self.stack.pop()
            pattern_tag = token.operand
            if hasattr(value, 'tag') and value.tag == pattern_tag:
                self.stack.append(True)
            else:
                self.stack.append(False)

        elif token.opcode == SuperBitOpCode.NOP:
            pass
