"""Module loader for Null-Lang.

Handles loading .null files from the filesystem with support for:
- Module path resolution (std::strings → stdlib/strings.null)
- Circular import detection
- Module caching
- Error reporting
"""

import os
from typing import Dict, Optional, Set, Tuple
from dataclasses import dataclass

from .parser import NullLangParser, Program
from ..superbit.ir import SuperBitStream


@dataclass
class ModuleInfo:
    """Information about a loaded module."""
    name: str
    path: str
    program: Program
    dependencies: Set[str]
    being_loaded: bool = False


class ModuleLoadError(Exception):
    """Raised when a module cannot be loaded."""
    def __init__(self, message: str, module_name: str, path: Optional[str] = None):
        self.message = message
        self.module_name = module_name
        self.path = path
        super().__init__(self.message)


class CircularImportError(ModuleLoadError):
    """Raised when a circular import is detected."""
    def __init__(self, module_name: str, cycle: Tuple[str, ...]):
        cycle_str = " -> ".join(cycle) + f" -> {module_name}"
        message = f"Circular import detected: {cycle_str}"
        super().__init__(message, module_name, None)
        self.cycle = cycle


class ModuleNotFoundError(ModuleLoadError):
    """Raised when a module file cannot be found."""
    def __init__(self, module_name: str, search_paths: Tuple[str, ...]):
        paths_str = ", ".join(f"'{p}'" for p in search_paths)
        message = f"Module '{module_name}' not found. Searched: {paths_str}"
        super().__init__(message, module_name, None)
        self.search_paths = search_paths


class ModuleLoadSyntaxError(ModuleLoadError):
    """Raised when a module has syntax errors."""
    def __init__(self, module_name: str, path: str, original_error: Exception):
        message = f"Syntax error in module '{module_name}' ({path}): {original_error}"
        super().__init__(message, module_name, path)
        self.original_error = original_error


class ModuleLoader:
    """Loads and caches Null-Lang modules from the filesystem."""

    def __init__(
        self,
        parser: Optional[NullLangParser] = None,
        search_paths: Optional[Tuple[str, ...]] = None,
    ):
        """Initialize the module loader.

        Args:
            parser: The parser to use for parsing module source files
            search_paths: Directories to search for modules
        """
        self.parser = parser or NullLangParser()
        self.search_paths = search_paths or self._default_search_paths()
        self._cache: Dict[str, ModuleInfo] = {}
        self._load_stack: Set[str] = set()

    def _default_search_paths(self) -> Tuple[str, ...]:
        """Get default module search paths."""
        paths = []

        # Add src/null_system/stdlib if it exists
        stdlib_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "stdlib"
        )
        if os.path.exists(stdlib_path):
            paths.append(stdlib_path)

        # Add current working directory
        paths.append(os.getcwd())

        # Add directory relative to project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        paths.append(project_root)

        return tuple(paths)

    def _resolve_module_path(self, module_name: str) -> Tuple[str, str]:
        """Resolve a module name to a filesystem path.

        Args:
            module_name: Module name in dot/colon notation (e.g., "std::strings" or "std.strings")

        Returns:
            Tuple of (normalized_name, filesystem_path)

        Raises:
            ModuleNotFoundError: If module cannot be found
        """
        # Normalize module name (both :: and . separators supported)
        normalized_name = module_name.replace("::", ".").replace("/", ".")

        # Convert to filesystem path
        # std::strings -> strings.null or std/strings.null
        relative_paths = [
            f"{normalized_name}.null",
            normalized_name.replace(".", "/") + ".null",
        ]

        for search_path in self.search_paths:
            for relative_path in relative_paths:
                full_path = os.path.join(search_path, relative_path)
                if os.path.isfile(full_path):
                    return (normalized_name, full_path)

        raise ModuleNotFoundError(module_name, self.search_paths)

    def _detect_dependencies(self, program: Program) -> Set[str]:
        """Extract module dependencies from a parsed program.

        Args:
            program: The parsed program

        Returns:
            Set of module names that this program imports
        """
        dependencies = set()

        for imp in program.imports or []:
            if imp.module_name:
                module_str = imp.module_name.full_name if hasattr(imp.module_name, 'full_name') else str(imp.module_name)
                dependencies.add(module_str.replace("::", "."))

        return dependencies

    def load(self, module_name: str) -> Program:
        """Load a module and all its dependencies.

        Args:
            module_name: Name of the module to load

        Returns:
            The parsed program

        Raises:
            ModuleNotFoundError: If module cannot be found
            CircularImportError: If circular import is detected
            ModuleLoadSyntaxError: If module has syntax errors
        """
        # Normalize module name
        normalized_name = module_name.replace("::", ".").replace("/", ".")

        # Check cache
        if normalized_name in self._cache:
            return self._cache[normalized_name].program

        # Check for circular import
        if normalized_name in self._load_stack:
            cycle = tuple(self._load_stack)
            raise CircularImportError(normalized_name, cycle)

        # Resolve path
        _, module_path = self._resolve_module_path(normalized_name)

        # Read source file
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except IOError as e:
            raise ModuleLoadError(f"Failed to read module file: {e}", normalized_name, module_path)

        # Parse module
        self._load_stack.add(normalized_name)
        try:
            program = self.parser.parse(source)
        except Exception as e:
            raise ModuleLoadSyntaxError(normalized_name, module_path, e)
        finally:
            self._load_stack.remove(normalized_name)

        # Detect and load dependencies
        dependencies = self._detect_dependencies(program)
        for dep_name in dependencies:
            self.load(dep_name)  # Recursively load dependencies

        # Cache module
        module_info = ModuleInfo(
            name=normalized_name,
            path=module_path,
            program=program,
            dependencies=dependencies,
        )
        self._cache[normalized_name] = module_info

        return program

    def load_and_compile(self, module_name: str, compiler) -> SuperBitStream:
        """Load a module and compile it to SuperBit IR.

        Args:
            module_name: Name of the module to load
            compiler: The compiler to use for compiling the module

        Returns:
            Compiled SuperBit stream

        Raises:
            ModuleNotFoundError: If module cannot be found
            CircularImportError: If circular import is detected
            ModuleLoadSyntaxError: If module has syntax errors
        """
        program = self.load(module_name)
        return compiler.compile(program)

    def get_loaded_modules(self) -> Dict[str, ModuleInfo]:
        """Get all loaded modules.

        Returns:
            Dictionary mapping module names to their info
        """
        return self._cache.copy()

    def is_loaded(self, module_name: str) -> bool:
        """Check if a module is already loaded.

        Args:
            module_name: Name of the module to check

        Returns:
            True if module is in cache, False otherwise
        """
        normalized_name = module_name.replace("::", ".").replace("/", ".")
        return normalized_name in self._cache

    def clear_cache(self):
        """Clear the module cache."""
        self._cache.clear()
        self._load_stack.clear()

    def add_search_path(self, path: str):
        """Add a directory to the module search paths.

        Args:
            path: Directory path to add
        """
        if os.path.isdir(path):
            self.search_paths = self.search_paths + (path,)
        else:
            raise ValueError(f"Search path does not exist or is not a directory: {path}")
