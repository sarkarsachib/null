"""Tests for module loader functionality."""

import os
import tempfile
import pytest

from null_system.lang.module_loader import (
    ModuleLoader,
    ModuleNotFoundError,
    CircularImportError,
    ModuleLoadSyntaxError,
)
from null_system.lang.parser import NullLangParser
from null_system.lang.compiler import NullLangCompiler
from null_system.superbit.ir import SuperBitStream


class TestModuleLoader:
    """Test basic module loader functionality."""

    def test_initialization(self):
        """Test module loader initialization."""
        loader = ModuleLoader()
        assert loader.parser is not None
        assert len(loader.search_paths) > 0

    def test_custom_search_paths(self):
        """Test module loader with custom search paths."""
        custom_paths = ("/tmp", "/home")
        loader = ModuleLoader(search_paths=custom_paths)
        assert loader.search_paths == custom_paths

    def test_add_search_path(self):
        """Test adding a search path."""
        loader = ModuleLoader(search_paths=("/tmp",))
        loader.add_search_path("/home")
        assert "/home" in loader.search_paths

    def test_add_invalid_search_path(self):
        """Test adding an invalid search path."""
        loader = ModuleLoader()
        with pytest.raises(ValueError):
            loader.add_search_path("/nonexistent/path/that/does/not/exist")


class TestModuleResolution:
    """Test module name to path resolution."""

    def test_resolve_existing_module(self):
        """Test resolving an existing module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test module file
            module_path = os.path.join(tmpdir, "test.null")
            with open(module_path, 'w') as f:
                f.write('SET x TO 42')

            loader = ModuleLoader(search_paths=(tmpdir,))
            name, path = loader._resolve_module_path("test")

            assert name == "test"
            assert path == module_path

    def test_resolve_nested_module(self):
        """Test resolving a nested module (std::strings)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested directory structure
            std_dir = os.path.join(tmpdir, "std")
            os.makedirs(std_dir)

            module_path = os.path.join(std_dir, "strings.null")
            with open(module_path, 'w') as f:
                f.write('SET x TO "hello"')

            loader = ModuleLoader(search_paths=(tmpdir,))
            name, path = loader._resolve_module_path("std::strings")

            assert name == "std.strings"
            assert path == module_path

    def test_resolve_with_dot_separator(self):
        """Test resolving module with dot separator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = os.path.join(tmpdir, "test.null")
            with open(module_path, 'w') as f:
                f.write('SET x TO 42')

            loader = ModuleLoader(search_paths=(tmpdir,))
            name, path = loader._resolve_module_path("test.module")

            assert name == "test.module"
            # Should try test.module.null or test/module.null
            assert "test" in path

    def test_resolve_nonexistent_module(self):
        """Test resolving a non-existent module."""
        loader = ModuleLoader(search_paths=("/nonexistent",))
        with pytest.raises(ModuleNotFoundError) as exc_info:
            loader._resolve_module_path("nonexistent_module")

        assert "nonexistent_module" in str(exc_info.value)


class TestModuleLoading:
    """Test loading and parsing modules."""

    def test_load_simple_module(self):
        """Test loading a simple module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = os.path.join(tmpdir, "simple.null")
            with open(module_path, 'w') as f:
                f.write('SET x TO 42\nSHOW x')

            loader = ModuleLoader(search_paths=(tmpdir,))
            program = loader.load("simple")

            assert program is not None
            assert len(program.statements) == 2

    def test_load_module_with_imports(self):
        """Test loading a module that imports other modules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create base module
            base_path = os.path.join(tmpdir, "base.null")
            with open(base_path, 'w') as f:
                f.write('SET x TO 10')

            # Create dependent module
            dep_path = os.path.join(tmpdir, "dependent.null")
            with open(dep_path, 'w') as f:
                f.write('import base\nSET y TO base.x\nSHOW y')

            loader = ModuleLoader(search_paths=(tmpdir,))
            program = loader.load("dependent")

            assert program is not None
            assert len(program.imports) == 1
            assert program.imports[0].module_name.full_name == "base"

    def test_module_caching(self):
        """Test that modules are cached after first load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = os.path.join(tmpdir, "cached.null")
            with open(module_path, 'w') as f:
                f.write('SET x TO 42')

            loader = ModuleLoader(search_paths=(tmpdir,))

            # Load module twice
            program1 = loader.load("cached")
            program2 = loader.load("cached")

            # Should be the same object (cached)
            assert program1 is program2

            # Check cache
            assert loader.is_loaded("cached")

    def test_clear_cache(self):
        """Test clearing module cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = os.path.join(tmpdir, "test.null")
            with open(module_path, 'w') as f:
                f.write('SET x TO 42')

            loader = ModuleLoader(search_paths=(tmpdir,))
            loader.load("test")

            assert loader.is_loaded("test")

            loader.clear_cache()

            assert not loader.is_loaded("test")


class TestCircularImportDetection:
    """Test circular import detection."""

    def test_circular_import_two_modules(self):
        """Test detecting circular import between two modules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Module A imports B
            a_path = os.path.join(tmpdir, "a.null")
            with open(a_path, 'w') as f:
                f.write('import b')

            # Module B imports A
            b_path = os.path.join(tmpdir, "b.null")
            with open(b_path, 'w') as f:
                f.write('import a')

            loader = ModuleLoader(search_paths=(tmpdir,))

            with pytest.raises(CircularImportError) as exc_info:
                loader.load("a")

            assert "circular import" in str(exc_info.value).lower()

    def test_circular_import_three_modules(self):
        """Test detecting circular import with three modules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Module A imports B
            a_path = os.path.join(tmpdir, "a.null")
            with open(a_path, 'w') as f:
                f.write('import b')

            # Module B imports C
            b_path = os.path.join(tmpdir, "b.null")
            with open(b_path, 'w') as f:
                f.write('import c')

            # Module C imports A (cycle!)
            c_path = os.path.join(tmpdir, "c.null")
            with open(c_path, 'w') as f:
                f.write('import a')

            loader = ModuleLoader(search_paths=(tmpdir,))

            with pytest.raises(CircularImportError) as exc_info:
                loader.load("a")

            cycle = exc_info.value.cycle
            assert len(cycle) > 0


class TestModuleLoadAndCompile:
    """Test loading and compiling modules."""

    def test_load_and_compile_module(self):
        """Test loading and compiling a module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = os.path.join(tmpdir, "compile_test.null")
            with open(module_path, 'w') as f:
                f.write('SET x TO 42\nSHOW x')

            loader = ModuleLoader(search_paths=(tmpdir,))
            compiler = NullLangCompiler()

            stream = loader.load_and_compile("compile_test", compiler)

            assert isinstance(stream, SuperBitStream)
            assert len(stream.tokens) > 0


class TestDependencyDetection:
    """Test automatic dependency detection."""

    def test_detect_no_dependencies(self):
        """Test detecting module with no imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = os.path.join(tmpdir, "no_deps.null")
            with open(module_path, 'w') as f:
                f.write('SET x TO 42')

            loader = ModuleLoader(search_paths=(tmpdir,))
            program = loader.load("no_deps")

            deps = loader._detect_dependencies(program)
            assert len(deps) == 0

    def test_detect_single_import(self):
        """Test detecting single import."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dep_path = os.path.join(tmpdir, "dep.null")
            with open(dep_path, 'w') as f:
                f.write('SET x TO 10')

            module_path = os.path.join(tmpdir, "main.null")
            with open(module_path, 'w') as f:
                f.write('import dep')

            loader = ModuleLoader(search_paths=(tmpdir,))
            program = loader.load("main")

            deps = loader._detect_dependencies(program)
            assert "dep" in deps
            assert len(deps) == 1

    def test_detect_multiple_imports(self):
        """Test detecting multiple imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dependency modules
            for name in ["dep1", "dep2", "dep3"]:
                dep_path = os.path.join(tmpdir, f"{name}.null")
                with open(dep_path, 'w') as f:
                    f.write('SET x TO 10')

            # Create main module
            module_path = os.path.join(tmpdir, "main.null")
            with open(module_path, 'w') as f:
                f.write('import dep1\nimport dep2\nimport dep3')

            loader = ModuleLoader(search_paths=(tmpdir,))
            program = loader.load("main")

            deps = loader._detect_dependencies(program)
            assert "dep1" in deps
            assert "dep2" in deps
            assert "dep3" in deps
            assert len(deps) == 3
