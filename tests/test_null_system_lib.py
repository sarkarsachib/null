import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from null_system.compiler import compile_program
from null_system.errors import NullLibNotFoundError, NullTypeError
from null_system.lib.registry import default_registry
from null_system.runtime import NullIO
from null_system.vm import VirtualMachine


class BufferIO(NullIO):
    def __init__(self, inputs=None):
        self._inputs = list(inputs or [])
        self.outputs = []

    def read_line(self) -> str:
        if not self._inputs:
            return ""
        return self._inputs.pop(0)

    def write(self, text: str) -> None:
        self.outputs.append(text)


class NullSystemLibTests(unittest.TestCase):
    def test_math_add_via_define_call_and_show(self):
        registry = default_registry()
        program = compile_program(
            """
            DEFINE add USE LIB math.ADD
            PUSH 2
            PUSH 3
            CALL add 2
            SHOW
            HALT
            """,
            registry=registry,
        )

        io = BufferIO()
        vm = VirtualMachine(registry=registry, io=io)
        vm.run(program)

        self.assertEqual(io.outputs, ["5"])

    def test_text_substr(self):
        registry = default_registry()
        program = compile_program(
            """
            PUSH "hello"
            PUSH 1
            PUSH 3
            LIBCALL text.SUBSTR 3
            SHOW
            HALT
            """,
            registry=registry,
        )

        io = BufferIO()
        vm = VirtualMachine(registry=registry, io=io)
        vm.run(program)

        self.assertEqual(io.outputs, ["ell"])

    def test_array_map_multiply_by_2(self):
        registry = default_registry()
        program = compile_program(
            """
            DEFINE mul USE LIB math.MUL
            PUSH [1, 2, 3]
            PUSH_REF mul
            PUSH 2
            LIBCALL array.MAP 3
            SHOW
            HALT
            """,
            registry=registry,
        )

        io = BufferIO()
        vm = VirtualMachine(registry=registry, io=io)
        vm.run(program)

        self.assertEqual(io.outputs, ["[2, 4, 6]"])

    def test_unknown_library_is_typed_and_descriptive(self):
        registry = default_registry()
        with self.assertRaises(NullLibNotFoundError) as ctx:
            compile_program(
                """
                DEFINE add USE LIB nope.ADD
                """,
                registry=registry,
            )
        self.assertIn("Unknown library 'nope'", str(ctx.exception))

    def test_type_error_from_lib_call(self):
        registry = default_registry()
        program = compile_program(
            """
            PUSH "a"
            PUSH 2
            LIBCALL math.ADD 2
            HALT
            """,
            registry=registry,
        )

        vm = VirtualMachine(registry=registry, io=BufferIO())
        with self.assertRaises(NullTypeError):
            vm.run(program)


if __name__ == "__main__":
    unittest.main()
