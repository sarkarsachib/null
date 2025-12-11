from __future__ import annotations

from .compiler import CompiledProgram
from .errors import NullArityError, NullRuntimeError
from .lib.registry import LibraryRegistry
from .runtime import NullCallContext, NullIO
from .types import NULL, NullValue


class VirtualMachine:
    def __init__(self, *, registry: LibraryRegistry, io: NullIO | None = None) -> None:
        self.registry = registry
        self.io = io or NullIO()

    def run(self, program: CompiledProgram) -> list[NullValue]:
        ctx = NullCallContext(registry=self.registry, io=self.io)
        stack: list[NullValue] = []

        ip = 0
        instructions = program.instructions
        while ip < len(instructions):
            inst = instructions[ip]
            ip += 1

            if inst.op == "PUSH":
                (value,) = inst.args
                stack.append(value)  # type: ignore[arg-type]
                continue

            if inst.op == "LIBCALL":
                lib_path, argc = inst.args
                if not isinstance(argc, int):
                    raise NullArityError(
                        "Invalid arg count",
                        code="NULL_ARITY_ERROR",
                        argc=argc,
                    )
                if len(stack) < argc:
                    raise NullArityError(
                        f"Stack underflow: need {argc} args",
                        code="NULL_ARITY_ERROR",
                        argc=argc,
                        stack_size=len(stack),
                    )
                args = stack[-argc:]
                del stack[-argc:]
                result = self.registry.call(str(lib_path), ctx, args)
                stack.append(result)
                continue

            if inst.op == "SHOW":
                if not stack:
                    raise NullRuntimeError(
                        "SHOW requires a value on the stack",
                        code="NULL_STACK_UNDERFLOW",
                    )
                value = stack.pop()
                self.registry.call("io.SHOW", ctx, [value])
                stack.append(NULL)
                continue

            if inst.op == "READ":
                value = self.registry.call("io.READ", ctx, [])
                stack.append(value)
                continue

            if inst.op == "HALT":
                break

            raise NullRuntimeError(
                f"Unknown instruction '{inst.op}'",
                code="NULL_RUNTIME_ERROR",
                op=inst.op,
            )

        return stack
