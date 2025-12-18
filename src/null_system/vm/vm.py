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


@dataclass
class ReferenceCountedValue:
    """A value with reference counting for ownership tracking."""
    value: Any
    ref_count: int = 1
    
    def increment_ref(self):
        """Increment reference count."""
        self.ref_count += 1
    
    def decrement_ref(self):
        """Decrement reference count."""
        self.ref_count -= 1
        return self.ref_count == 0


class NullVM:
    """Virtual machine for executing super-bit code."""
    
    def __init__(self):
        self.stack: List[Any] = []
        self.variables: Dict[str, Any] = {}
        self.output: List[str] = []
        self.pc = 0
        # Ownership tracking
        self.reference_counts: Dict[str, ReferenceCountedValue] = {}
        self.borrows: Dict[str, int] = {}  # Track active borrows per variable
        self.scopes: List[Dict[str, List[str]]] = []  # Variable scopes
        self._enter_scope()  # Start with global scope
    
    def _enter_scope(self):
        """Enter a new scope (for RAII)."""
        self.scopes.append({})
    
    def _exit_scope(self):
        """Exit current scope and clean up variables."""
        if len(self.scopes) > 1:  # Don't remove global scope
            scope = self.scopes.pop()
            for var_name in scope:
                if var_name in self.reference_counts:
                    ref_value = self.reference_counts[var_name]
                    if ref_value.decrement_ref():
                        del self.reference_counts[var_name]
                if var_name in self.variables:
                    del self.variables[var_name]
    
    def _add_to_scope(self, var_name: str):
        """Add variable to current scope."""
        if self.scopes:
            current_scope = self.scopes[-1]
            if var_name not in current_scope:
                current_scope[var_name] = []
    
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
        
        # Ownership and memory safety opcodes
        elif token.opcode == SuperBitOpCode.BORROW_IMM:
            if not self.stack:
                raise RuntimeError("Stack underflow for BORROW_IMM")
            value = self.stack.pop()
            # For immutable borrow, just push a reference
            self.stack.append(("borrow", value, False))  # False = immutable
        
        elif token.opcode == SuperBitOpCode.BORROW_MUT:
            if not self.stack:
                raise RuntimeError("Stack underflow for BORROW_MUT")
            value = self.stack.pop()
            # For mutable borrow, push a mutable reference
            self.stack.append(("borrow", value, True))  # True = mutable
        
        elif token.opcode == SuperBitOpCode.DROP:
            if not self.stack:
                raise RuntimeError("Stack underflow for DROP")
            value = self.stack.pop()
            # For explicit drop, decrement reference count
            if isinstance(value, str) and value in self.reference_counts:
                ref_value = self.reference_counts[value]
                if ref_value.decrement_ref():
                    # Reference count reached zero, actually drop the value
                    del self.reference_counts[value]
                    if value in self.variables:
                        del self.variables[value]
        
        elif token.opcode == SuperBitOpCode.INC_REF:
            # Increment reference count for a value
            pass  # Implementation depends on specific memory management strategy
        
        elif token.opcode == SuperBitOpCode.DEC_REF:
            # Decrement reference count for a value
            pass  # Implementation depends on specific memory management strategy
        
        elif token.opcode == SuperBitOpCode.CHECK_BORROW:
            # Check if a borrow is still valid
            if not self.stack:
                raise RuntimeError("Stack underflow for CHECK_BORROW")
            borrow_info = self.stack.pop()
            if isinstance(borrow_info, tuple) and borrow_info[0] == "borrow":
                # Validate that the borrowed value still exists
                original_value = borrow_info[1]
                if isinstance(original_value, str) and original_value not in self.variables:
                    raise RuntimeError("Dangling reference detected")
        
        else:
            raise RuntimeError(f"Unknown opcode: {token.opcode}")
