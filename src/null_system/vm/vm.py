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
    # Innermost-first call frames for a runtime error, empty on success.
    trace: List[str] = field(default_factory=list)


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
        # Process arguments visible to a running program. The host VM has no
        # argv of its own in the bootstrap chain, so a caller sets this
        # explicitly; a native binary fills it from the real process argv.
        self.argv: List[str] = []
    
    def execute(self, superbit_stream: SuperBitStream) -> ExecutionResult:
        """Execute a super-bit stream."""
        obs = get_observability()

        self.stack = []
        self.variables = {}
        self.module_namespaces = {"__main__": {}}
        self.current_module = "__main__"
        self.output = []
        self.pc = 0
        self.frames: List[Any] = []
        self.call_sites: List[Dict[str, Any]] = []
        self.current_function = "main"
        self.token_count = len(superbit_stream.tokens)
        self.function_table = self._index_functions(superbit_stream.tokens)

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

                fault_line = None
                if 0 <= self.pc < self.token_count:
                    fault_line = superbit_stream.tokens[self.pc].source_line
                trace = self._format_trace(fault_line)
                message = str(e)
                if trace:
                    message += "\nstack trace (innermost first):\n" + "\n".join(trace)

                return ExecutionResult(
                    success=False,
                    output=self.output,
                    error=message,
                    final_state=self.variables.copy(),
                    trace=trace,
                )
    
    def _format_trace(self, fault_line: Optional[int]) -> List[str]:
        """Render the Null-level call stack, innermost frame first.

        `call_sites` records one entry per entered function: its name plus the
        line of the call that entered it. The innermost function is the one
        currently executing, which is not in `call_sites`.
        """
        where = f" at line {fault_line}" if fault_line else ""
        lines = [f"  in {self.current_function}{where}"]
        for index in range(len(self.call_sites) - 1, -1, -1):
            site = self.call_sites[index]
            caller = "main" if index == 0 else self.call_sites[index - 1]["name"]
            call_line = site.get("line")
            caller_where = f" at line {call_line}" if call_line else ""
            lines.append(f"  in {caller}{caller_where}")
        return lines

    def _index_functions(self, tokens) -> Dict[str, Any]:
        """Map user function name -> (body start, body end, parameters)."""
        table: Dict[str, Any] = {}
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.opcode == SuperBitOpCode.FUNCTION:
                end = i + 1
                while end < len(tokens):
                    probe = tokens[end]
                    if probe.opcode == SuperBitOpCode.NOP and probe.operand == "end_fn":
                        break
                    end += 1
                params = list(token.metadata.get("params", []) or [])
                table[str(token.operand)] = (i + 1, end, params)
            i += 1
        return table

    @staticmethod
    def _truthy(value: Any) -> bool:
        checker = getattr(value, "as_bool", None)
        if callable(checker):
            return bool(checker())
        return bool(value)

    @staticmethod
    def _format_value(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        if value is None:
            return "NOTHING"
        return str(value)

    def _call_builtin(self, name: str, args: List[Any]) -> Any:
        """Execute a standard-library call on plain Python values."""
        import os

        key = name.upper()
        if key in ("LEN", "LENGTH"):
            return float(len(args[0]))
        if key == "APPEND":
            return list(args[0]) + [args[1]]
        if key == "SPLIT":
            return str(args[0]).split(str(args[1]))
        if key == "JOIN":
            return str(args[1]).join(str(x) for x in args[0])
        if key == "CHAR_AT":
            return str(args[0])[int(args[1])]
        if key == "SUBSTR":
            start = int(args[1])
            end = int(args[2]) if len(args) > 2 else len(str(args[0]))
            return str(args[0])[start:end]
        if key == "SLICE":
            return args[0][int(args[1]):int(args[2])]
        if key == "TO_STRING":
            return self._format_value(args[0])
        if key == "TO_NUMBER":
            text = str(args[0])
            try:
                return float(text)
            except ValueError:
                return 0.0
        if key == "CONTAINS":
            return args[1] in args[0]
        if key == "ORD":
            return float(ord(str(args[0])[0]))
        if key == "CHR":
            return chr(int(args[0]))
        if key == "READ_FILE":
            with open(str(args[0]), "r", encoding="utf-8") as handle:
                return handle.read()
        if key == "WRITE_FILE":
            with open(str(args[0]), "w", encoding="utf-8") as handle:
                handle.write(str(args[1]))
            return None
        if key == "FILE_EXISTS":
            return os.path.exists(str(args[0]))
        if key == "ARGC":
            return float(len(self.argv))
        if key == "ARGV":
            index = int(args[0])
            if 0 <= index < len(self.argv):
                return self.argv[index]
            return ""
        if key == "SHELL":
            import subprocess

            return float(subprocess.call(str(args[0]), shell=True))
        if key == "LIST_FILES":
            return sorted(os.listdir(str(args[0])))
        if key == "RANGE":
            start, stop = int(args[0]), int(args[1])
            return [float(x) for x in range(start, stop)]
        raise RuntimeError(f"Unknown function '{name}'")

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
            
            # Locals of the active frame shadow module globals.
            if token.operand in self.variables:
                self.stack.append(self.variables[token.operand])
            elif module in self.module_namespaces and local_name in self.module_namespaces[module]:
                self.stack.append(self.module_namespaces[module][local_name])
            else:
                raise RuntimeError(f"Undefined variable: {token.operand}")
        
        elif token.opcode == SuperBitOpCode.STORE_VAR:
            if not self.stack:
                raise RuntimeError("Stack underflow")
            value = self.stack.pop()
            
            module, local_name = self._resolve_variable_name(token.operand, token)
            
            # Inside a function call `variables` holds the frame's locals; those
            # must not leak into the module namespace of the caller.
            if not self.frames:
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

        elif token.opcode == SuperBitOpCode.COMPARE_NE:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left != right)

        elif token.opcode == SuperBitOpCode.COMPARE_GE:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left >= right)

        elif token.opcode == SuperBitOpCode.COMPARE_LE:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left <= right)

        elif token.opcode == SuperBitOpCode.LOGICAL_AND:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(self._truthy(left) and self._truthy(right))

        elif token.opcode == SuperBitOpCode.LOGICAL_OR:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(self._truthy(left) or self._truthy(right))
        
        elif token.opcode == SuperBitOpCode.PRINT:
            value = self.stack.pop()
            self.output.append(self._format_value(value))

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

        elif token.opcode == SuperBitOpCode.FUNCTION:
            # Body is skipped by the compiler's jump; the pre-pass indexed it.
            pass

        elif token.opcode == SuperBitOpCode.CALL:
            argc = int(token.metadata.get("argc", token.metadata.get("arity", 0)) or 0)
            args = [self.stack.pop() for _ in range(argc)][::-1]
            name = str(token.operand)
            if name in self.function_table:
                start, _end, params = self.function_table[name]
                self.frames.append(
                    (self.pc + 1, self.variables, self.current_function)
                )
                # The implicit entry call to `main` is not a source-level frame.
                if not token.metadata.get("entry"):
                    self.call_sites.append({"name": name, "line": token.source_line})
                self.current_function = name
                self.variables = {
                    param: (args[i] if i < len(args) else None)
                    for i, param in enumerate(params)
                }
                self.pc = start - 1
            else:
                self.stack.append(self._call_builtin(name, args))

        elif token.opcode == SuperBitOpCode.RETURN:
            unit = bool(token.metadata.get("unit"))
            value = None if unit else (self.stack.pop() if self.stack else None)
            if self.frames:
                return_pc, saved_variables, caller = self.frames.pop()
                self.variables = saved_variables
                self.current_function = caller
                if self.call_sites:
                    self.call_sites.pop()
                if not unit:
                    self.stack.append(value)
                self.pc = return_pc - 1
            else:
                self.pc = self.token_count

        elif token.opcode == SuperBitOpCode.ARRAY:
            arity = int(token.metadata.get("arity", 0) or 0)
            items = [self.stack.pop() for _ in range(arity)][::-1] if arity else []
            self.stack.append(items)

        elif token.opcode == SuperBitOpCode.INDEX:
            index = self.stack.pop()
            container = self.stack.pop()
            try:
                self.stack.append(container[int(index)])
            except (IndexError, TypeError, ValueError) as exc:
                raise RuntimeError(f"Invalid index {index!r}: {exc}") from exc

        elif token.opcode == SuperBitOpCode.NOP:
            pass
