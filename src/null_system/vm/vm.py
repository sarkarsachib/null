"""NullVM - Virtual machine for executing super-bit code."""

import resource
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ..observability import get_observability
from ..superbit.ir import SuperBitIRToken as SuperBitToken, SuperBitOpCode, SuperBitStream

if TYPE_CHECKING:
    from ..config import FeatureConfig


@dataclass
class ExecutionResult:
    """Result of VM execution."""
    success: bool
    output: List[str] = field(default_factory=list)
    error: str = ""
    final_state: Dict[str, Any] = field(default_factory=dict)


class NullVM:
    """Virtual machine for executing super-bit code."""
    
    def __init__(self, feature_config: Optional["FeatureConfig"] = None):
        self.stack: List[Any] = []
        self.variables: Dict[str, Any] = {}
        self.module_namespaces: Dict[str, Dict[str, Any]] = {"__main__": {}}
        self.current_module: str = "__main__"
        self.output: List[str] = []
        self.pc = 0
        self.feature_config = feature_config
    
    def execute(self, superbit_stream: SuperBitStream) -> ExecutionResult:
        """Execute a super-bit stream."""
        obs = get_observability()

        self.stack = []
        self.variables = {}
        self.module_namespaces = {"__main__": {}}
        self.current_module = "__main__"
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
    
    def _resolve_variable_name(self, name: str, token: SuperBitToken) -> tuple[str, str]:
        """Resolve variable name to (module, local_name).
        
        Handles qualified names like 'math::add' and module metadata.
        """
        if "::" in name:
            parts = name.split("::")
            module = "::".join(parts[:-1])
            local_name = parts[-1]
            return (module, local_name)
        
        module = token.metadata.get("module", self.current_module) if hasattr(token, 'metadata') else self.current_module
        return (module, name)
    
    def _execute_token(self, token: SuperBitToken):
        """Execute a single super-bit token."""
        if hasattr(token, 'metadata') and token.metadata.get("module"):
            exec_module = token.metadata["module"]
            if exec_module not in self.module_namespaces:
                self.module_namespaces[exec_module] = {}
        
        if token.opcode == SuperBitOpCode.LOAD_CONST:
            self.stack.append(token.operand)
        
        elif token.opcode == SuperBitOpCode.LOAD_VAR:
            module, local_name = self._resolve_variable_name(token.operand, token)
            
            if module in self.module_namespaces and local_name in self.module_namespaces[module]:
                self.stack.append(self.module_namespaces[module][local_name])
            elif token.operand in self.variables:
                self.stack.append(self.variables[token.operand])
            else:
                raise RuntimeError(f"Undefined variable: {token.operand}")
        
        elif token.opcode == SuperBitOpCode.STORE_VAR:
            if not self.stack:
                raise RuntimeError("Stack underflow")
            value = self.stack.pop()
            
            module, local_name = self._resolve_variable_name(token.operand, token)
            
            if module not in self.module_namespaces:
                self.module_namespaces[module] = {}
            self.module_namespaces[module][local_name] = value
            
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

        elif token.opcode == SuperBitOpCode.INPUT:
            import sys
            line = sys.stdin.readline()
            self.stack.append(line.rstrip('\n'))

        elif token.opcode == SuperBitOpCode.FILE_READ:
            if not self.stack:
                raise RuntimeError("Stack underflow for FILE_READ")
            path = self.stack.pop()
            try:
                with open(str(path), 'r') as f:
                    content = f.read()
                self.stack.append(content)
            except Exception as e:
                raise RuntimeError(f"Failed to read file '{path}': {e}")

        elif token.opcode == SuperBitOpCode.FILE_WRITE:
            if len(self.stack) < 2:
                raise RuntimeError("Stack underflow for FILE_WRITE")
            content = self.stack.pop()
            path = self.stack.pop()
            try:
                with open(str(path), 'w') as f:
                    f.write(str(content))
                self.stack.append(True)
            except Exception as e:
                raise RuntimeError(f"Failed to write file '{path}': {e}")

        elif token.opcode == SuperBitOpCode.FILE_EXISTS:
            if not self.stack:
                raise RuntimeError("Stack underflow for FILE_EXISTS")
            path = self.stack.pop()
            import os
            self.stack.append(os.path.exists(str(path)))

        elif token.opcode == SuperBitOpCode.LIST_FILES:
            if not self.stack:
                raise RuntimeError("Stack underflow for LIST_FILES")
            path = self.stack.pop()
            import os
            try:
                files = os.listdir(str(path))
                self.stack.append(files)
            except Exception as e:
                raise RuntimeError(f"Failed to list directory '{path}': {e}")

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
