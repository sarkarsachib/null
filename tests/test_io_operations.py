"""Tests for I/O operations in Null-Lang."""

import os
import tempfile
import pytest

from null_system.lang.parser import NullLangParser
from null_system.lang.compiler import NullLangCompiler
from null_system.vm.vm import NullVM
from null_system.superbit.ir import SuperBitOpCode


class TestIOOperations:
    """Test I/O operations parsing, compilation, and execution."""

    def test_input_command_parsing(self):
        """Test parsing INPUT command."""
        parser = NullLangParser()
        source = "INPUT name"
        ast = parser.parse(source)

        assert len(ast.statements) == 1
        assert ast.statements[0].variable == "name"

    def test_input_with_prompt_parsing(self):
        """Test parsing INPUT with prompt."""
        parser = NullLangParser()
        source = 'INPUT name("Enter name: ")'
        ast = parser.parse(source)

        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert stmt.variable == "name"
        assert stmt.prompt is not None

    def test_read_file_command_parsing(self):
        """Test parsing READ_FILE command."""
        parser = NullLangParser()
        source = 'SET content TO READ_FILE "test.txt"'
        ast = parser.parse(source)

        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert stmt.target == "content"

    def test_write_file_command_parsing(self):
        """Test parsing WRITE_FILE command."""
        parser = NullLangParser()
        source = 'WRITE_FILE "test.txt" WITH "Hello, World!"'
        ast = parser.parse(source)

        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert stmt.path.value == "test.txt"
        assert stmt.content.value == "Hello, World!"

    def test_file_exists_command_parsing(self):
        """Test parsing FILE_EXISTS command."""
        parser = NullLangParser()
        source = 'SET exists TO FILE_EXISTS "test.txt"'
        ast = parser.parse(source)

        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert stmt.target == "exists"
        assert stmt.path.value == "test.txt"

    def test_list_files_command_parsing(self):
        """Test parsing LIST_FILES command."""
        parser = NullLangParser()
        source = 'SET files TO LIST_FILES "/tmp"'
        ast = parser.parse(source)

        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert stmt.target == "files"
        assert stmt.path.value == "/tmp"

    def test_input_compilation(self):
        """Test INPUT command compilation."""
        parser = NullLangParser()
        compiler = NullLangCompiler()

        source = "INPUT name"
        ast = parser.parse(source)
        stream = compiler.compile(ast)

        opcodes = [token.opcode for token in stream.tokens]
        assert SuperBitOpCode.INPUT in opcodes
        assert SuperBitOpCode.STORE_VAR in opcodes

    def test_input_with_prompt_compilation(self):
        """Test INPUT with prompt compilation."""
        parser = NullLangParser()
        compiler = NullLangCompiler()

        source = 'INPUT name("Enter your name: ")'
        ast = parser.parse(source)
        stream = compiler.compile(ast)

        opcodes = [token.opcode for token in stream.tokens]
        assert SuperBitOpCode.LOAD_CONST in opcodes
        assert SuperBitOpCode.PRINT in opcodes
        assert SuperBitOpCode.INPUT in opcodes
        assert SuperBitOpCode.STORE_VAR in opcodes

    def test_read_file_compilation(self):
        """Test READ_FILE compilation."""
        parser = NullLangParser()
        compiler = NullLangCompiler()

        source = 'SET content TO READ_FILE "test.txt"'
        ast = parser.parse(source)
        stream = compiler.compile(ast)

        opcodes = [token.opcode for token in stream.tokens]
        assert SuperBitOpCode.FILE_READ in opcodes
        assert SuperBitOpCode.STORE_VAR in opcodes

    def test_write_file_compilation(self):
        """Test WRITE_FILE compilation."""
        parser = NullLangParser()
        compiler = NullLangCompiler()

        source = 'WRITE_FILE "test.txt" WITH "Hello"'
        ast = parser.parse(source)
        stream = compiler.compile(ast)

        opcodes = [token.opcode for token in stream.tokens]
        assert SuperBitOpCode.FILE_WRITE in opcodes

    def test_file_exists_compilation(self):
        """Test FILE_EXISTS compilation."""
        parser = NullLangParser()
        compiler = NullLangCompiler()

        source = 'SET exists TO FILE_EXISTS "test.txt"'
        ast = parser.parse(source)
        stream = compiler.compile(ast)

        opcodes = [token.opcode for token in stream.tokens]
        assert SuperBitOpCode.FILE_EXISTS in opcodes
        assert SuperBitOpCode.STORE_VAR in opcodes

    def test_list_files_compilation(self):
        """Test LIST_FILES compilation."""
        parser = NullLangParser()
        compiler = NullLangCompiler()

        source = 'SET files TO LIST_FILES "/tmp"'
        ast = parser.parse(source)
        stream = compiler.compile(ast)

        opcodes = [token.opcode for token in stream.tokens]
        assert SuperBitOpCode.LIST_FILES in opcodes
        assert SuperBitOpCode.STORE_VAR in opcodes


class TestIOExecution:
    """Test I/O operation execution with VM."""

    def test_write_and_read_file(self):
        """Test writing and reading a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.txt")

            parser = NullLangParser()
            compiler = NullLangCompiler()
            vm = NullVM()

            source = f'WRITE_FILE "{filepath}" WITH "Hello, Null!"'
            ast = parser.parse(source)
            stream = compiler.compile(ast)
            result = vm.execute(stream)

            assert result.success

            source2 = f'SET content TO READ_FILE "{filepath}"'
            ast2 = parser.parse(source2)
            stream2 = compiler.compile(ast2)
            result2 = vm.execute(stream2)

            assert result2.success
            assert "content" in result2.final_state
            assert result2.final_state["content"] == "Hello, Null!"

    def test_file_exists_true(self):
        """Test FILE_EXISTS on existing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            filepath = f.name
            f.write("test content")

        try:
            parser = NullLangParser()
            compiler = NullLangCompiler()
            vm = NullVM()

            source = f'SET exists TO FILE_EXISTS "{filepath}"'
            ast = parser.parse(source)
            stream = compiler.compile(ast)
            result = vm.execute(stream)

            assert result.success
            assert "exists" in result.final_state
            assert result.final_state["exists"] is True
        finally:
            os.unlink(filepath)

    def test_file_exists_false(self):
        """Test FILE_EXISTS on non-existent file."""
        parser = NullLangParser()
        compiler = NullLangCompiler()
        vm = NullVM()

        source = 'SET exists TO FILE_EXISTS "/nonexistent/file.txt"'
        ast = parser.parse(source)
        stream = compiler.compile(ast)
        result = vm.execute(stream)

        assert result.success
        assert "exists" in result.final_state
        assert result.final_state["exists"] is False

    def test_list_files(self):
        """Test LIST_FILES command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            testfile = os.path.join(tmpdir, "test.txt")
            with open(testfile, 'w') as f:
                f.write("test")

            parser = NullLangParser()
            compiler = NullLangCompiler()
            vm = NullVM()

            source = f'SET files TO LIST_FILES "{tmpdir}"'
            ast = parser.parse(source)
            stream = compiler.compile(ast)
            result = vm.execute(stream)

            assert result.success
            assert "files" in result.final_state
            files = result.final_state["files"]
            assert isinstance(files, list)
            assert "test.txt" in files

    def test_io_pipeline(self):
        """Test complete I/O pipeline: write, read, check exists, list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "data.txt")

            parser = NullLangParser()
            compiler = NullLangCompiler()
            vm = NullVM()

            source = f'''
SET content TO "Hello, Null!"
WRITE_FILE "{filepath}" WITH content
SET read_content TO READ_FILE "{filepath}"
SET exists TO FILE_EXISTS "{filepath}"
SET files TO LIST_FILES "{tmpdir}"
'''

            ast = parser.parse(source)
            stream = compiler.compile(ast)
            result = vm.execute(stream)

            assert result.success
            assert result.final_state["read_content"] == "Hello, Null!"
            assert result.final_state["exists"] is True
            assert isinstance(result.final_state["files"], list)
            assert "data.txt" in result.final_state["files"]

    def test_write_empty_file(self):
        """Test writing an empty file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "empty.txt")

            parser = NullLangParser()
            compiler = NullLangCompiler()
            vm = NullVM()

            source = f'WRITE_FILE "{filepath}" WITH ""'
            ast = parser.parse(source)
            stream = compiler.compile(ast)
            result = vm.execute(stream)

            assert result.success

            source2 = f'SET content TO READ_FILE "{filepath}"'
            ast2 = parser.parse(source2)
            stream2 = compiler.compile(ast2)
            result2 = vm.execute(stream2)

            assert result2.success
            assert result2.final_state["content"] == ""

    def test_write_multiline_content(self):
        """Test writing multiline content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "multiline.txt")

            parser = NullLangParser()
            compiler = NullLangCompiler()
            vm = NullVM()

            source = f'WRITE_FILE "{filepath}" WITH "Line 1\\nLine 2\\nLine 3"'
            ast = parser.parse(source)
            stream = compiler.compile(ast)
            result = vm.execute(stream)

            assert result.success

            source2 = f'SET content TO READ_FILE "{filepath}"'
            ast2 = parser.parse(source2)
            stream2 = compiler.compile(ast2)
            result2 = vm.execute(stream2)

            assert result2.success
            assert result2.final_state["content"] == "Line 1\\nLine 2\\nLine 3"

    def test_read_nonexistent_file(self):
        """Test reading a non-existent file."""
        parser = NullLangParser()
        compiler = NullLangCompiler()
        vm = NullVM()

        source = 'SET content TO READ_FILE "/nonexistent/file.txt"'
        ast = parser.parse(source)
        stream = compiler.compile(ast)
        result = vm.execute(stream)

        assert not result.success
        assert "Failed to read file" in result.error

    def test_list_nonexistent_directory(self):
        """Test listing files in non-existent directory."""
        parser = NullLangParser()
        compiler = NullLangCompiler()
        vm = NullVM()

        source = 'SET files TO LIST_FILES "/nonexistent/directory"'
        ast = parser.parse(source)
        stream = compiler.compile(ast)
        result = vm.execute(stream)

        assert not result.success
        assert "Failed to list directory" in result.error

    def test_io_with_annotations(self):
        """Test I/O commands with layer annotations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "annotated.txt")

            parser = NullLangParser()
            compiler = NullLangCompiler()
            vm = NullVM()

            source = f'''
@layer(binary)
WRITE_FILE "{filepath}" WITH "Annotated"
@layer(binary)
SET content TO READ_FILE "{filepath}"
'''

            ast = parser.parse(source)
            stream = compiler.compile(ast)
            result = vm.execute(stream)

            assert result.success
            assert result.final_state["content"] == "Annotated"
