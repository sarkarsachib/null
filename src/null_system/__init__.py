from .compiler import compile_program
from .vm import VirtualMachine
from .lib.registry import default_registry, LibraryRegistry

__all__ = [
    "compile_program",
    "VirtualMachine",
    "default_registry",
    "LibraryRegistry",
]
