from .legacy_compiler import compile_program, Instruction, CompiledProgram
from .legacy_vm import VirtualMachine
from .lib.registry import default_registry, LibraryRegistry

__all__ = [
    "compile_program",
    "Instruction",
    "CompiledProgram",
    "VirtualMachine",
    "default_registry",
    "LibraryRegistry",
]
