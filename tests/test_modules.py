"""Tests for the module system."""

import pytest
from src.null_system.lang.parser import NullLangParser
from src.null_system.lang.compiler import NullLangCompiler
from src.null_system.lang.ast_nodes import (
    Program, ModuleDeclaration, ImportStatement, QualifiedIdentifier,
    SetCommand, Identifier
)
from src.null_system.ast.validator import ASTValidator
from src.null_system.vm.vm import NullVM


class TestModuleDeclaration:
    """Tests for module declarations."""
    
    def test_parse_simple_module_declaration(self):
        parser = NullLangParser()
        source = """
        module math
        
        SET x TO 42
        """
        program = parser.parse(source)
        
        assert isinstance(program, Program)
        assert program.module_declaration is not None
        assert isinstance(program.module_declaration, ModuleDeclaration)
        assert program.module_declaration.name.full_name == "math"
    
    def test_parse_qualified_module_name(self):
        parser = NullLangParser()
        source = """
        module std::math::algebra
        
        SET x TO 42
        """
        program = parser.parse(source)
        
        assert isinstance(program, Program)
        assert program.module_declaration is not None
        assert program.module_declaration.name.full_name == "std::math::algebra"
        assert program.module_declaration.name.module_path == ["std", "math"]
        assert program.module_declaration.name.name == "algebra"
    
    def test_program_without_module_declaration(self):
        parser = NullLangParser()
        source = """
        SET x TO 42
        """
        program = parser.parse(source)
        
        assert isinstance(program, Program)
        assert program.module_declaration is None
        assert len(program.statements) > 0


class TestImportStatement:
    """Tests for import statements."""
    
    def test_parse_simple_import(self):
        parser = NullLangParser()
        source = """
        import math
        
        SET x TO 42
        """
        program = parser.parse(source)
        
        assert isinstance(program, Program)
        assert len(program.imports) == 1
        assert isinstance(program.imports[0], ImportStatement)
        assert program.imports[0].module_name.full_name == "math"
        assert program.imports[0].alias is None
    
    def test_parse_import_with_alias(self):
        parser = NullLangParser()
        source = """
        import std::math as math
        
        SET x TO 42
        """
        program = parser.parse(source)
        
        assert isinstance(program, Program)
        assert len(program.imports) == 1
        assert program.imports[0].module_name.full_name == "std::math"
        assert program.imports[0].alias == "math"
    
    def test_parse_multiple_imports(self):
        parser = NullLangParser()
        source = """
        import math
        import std::io as io
        import collections
        
        SET x TO 42
        """
        program = parser.parse(source)
        
        assert isinstance(program, Program)
        assert len(program.imports) == 3
        assert program.imports[0].module_name.full_name == "math"
        assert program.imports[1].module_name.full_name == "std::io"
        assert program.imports[1].alias == "io"
        assert program.imports[2].module_name.full_name == "collections"


class TestQualifiedIdentifiers:
    """Tests for qualified identifiers (qualified names)."""
    
    def test_parse_qualified_identifier_in_expression(self):
        parser = NullLangParser()
        source = """
        SET x TO math::pi
        """
        program = parser.parse(source)
        
        assert isinstance(program, Program)
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, SetCommand)
        assert isinstance(stmt.value, QualifiedIdentifier)
        assert stmt.value.full_name == "math::pi"
    
    def test_qualified_identifier_properties(self):
        qid = QualifiedIdentifier(parts=["std", "math", "sqrt"])
        
        assert qid.full_name == "std::math::sqrt"
        assert qid.module_path == ["std", "math"]
        assert qid.name == "sqrt"
    
    def test_single_part_qualified_identifier(self):
        qid = QualifiedIdentifier(parts=["x"])
        
        assert qid.full_name == "x"
        assert qid.module_path == []
        assert qid.name == "x"


class TestModuleValidation:
    """Tests for module system validation."""
    
    def test_validator_handles_module_declaration(self):
        parser = NullLangParser()
        source = """
        module mymodule
        
        SET x TO 42
        """
        program = parser.parse(source)
        
        validator = ASTValidator()
        result = validator.validate(program)
        
        assert result is True
        assert validator.current_module == "mymodule"
        assert "mymodule" in validator.module_symbols
    
    def test_validator_handles_imports(self):
        parser = NullLangParser()
        source = """
        module mymodule
        import math
        import std::io as io
        
        SET x TO 42
        """
        program = parser.parse(source)
        
        validator = ASTValidator()
        result = validator.validate(program)
        
        assert result is True
        assert "math" in validator.imported_modules
        assert "std::io" in validator.imported_modules
        assert validator.module_aliases["io"] == "std::io"
    
    def test_validator_tracks_module_symbols(self):
        parser = NullLangParser()
        source = """
        module mymodule
        
        SET x TO 42
        SET y TO 10
        """
        program = parser.parse(source)
        
        validator = ASTValidator()
        result = validator.validate(program)
        
        assert result is True
        assert "x" in validator.module_symbols["mymodule"]
        assert "y" in validator.module_symbols["mymodule"]
    
    def test_validator_default_module_for_no_declaration(self):
        parser = NullLangParser()
        source = """
        SET x TO 42
        """
        program = parser.parse(source)
        
        validator = ASTValidator()
        result = validator.validate(program)
        
        assert result is True
        assert validator.current_module == "__main__"
        assert "__main__" in validator.module_symbols


class TestModuleEmitter:
    """Tests for module metadata in emitter."""
    
    def test_emitter_preserves_module_metadata(self):
        parser = NullLangParser()
        source = """
        module mymodule
        
        SET x TO 42
        """
        program = parser.parse(source)
        
        emitter = NullLangCompiler()
        ir = emitter.compile(program)
        
        assert emitter.current_module == "mymodule"
        for token in ir.tokens:
            if hasattr(token, 'metadata') and token.metadata:
                if "module" in token.metadata:
                    assert token.metadata["module"] == "mymodule"
    
    def test_emitter_tracks_imported_modules(self):
        parser = NullLangParser()
        source = """
        module mymodule
        import math
        import std::io as io
        
        SET x TO 42
        """
        program = parser.parse(source)
        
        emitter = NullLangCompiler()
        ir = emitter.compile(program)
        
        assert "math" in emitter.imported_modules
        assert "io" in emitter.imported_modules
        assert emitter.imported_modules["io"] == "std::io"
    
    def test_emitter_default_module_no_declaration(self):
        parser = NullLangParser()
        source = """
        SET x TO 42
        """
        program = parser.parse(source)
        
        emitter = NullLangCompiler()
        ir = emitter.compile(program)
        
        assert emitter.current_module == "__main__"


class TestModuleVM:
    """Tests for module execution in VM."""
    
    def test_vm_executes_module_program(self):
        parser = NullLangParser()
        source = """
        module mymodule
        
        SET x TO 42
        SET y TO 10
        """
        program = parser.parse(source)
        
        emitter = NullLangCompiler()
        ir = emitter.compile(program)
        
        vm = NullVM()
        result = vm.execute(ir)
        
        assert result.success is True
        assert "mymodule" in vm.module_namespaces
        assert "x" in vm.module_namespaces["mymodule"]
        assert vm.module_namespaces["mymodule"]["x"] == 42
    
    def test_vm_handles_default_module(self):
        parser = NullLangParser()
        source = """
        SET x TO 42
        """
        program = parser.parse(source)
        
        emitter = NullLangCompiler()
        ir = emitter.compile(program)
        
        vm = NullVM()
        result = vm.execute(ir)
        
        assert result.success is True
        assert "x" in vm.variables
        assert vm.variables["x"] == 42


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing programs."""
    
    def test_legacy_program_still_works(self):
        parser = NullLangParser()
        source = """
        SET x TO 42
        SET y TO x PLUS 10
        SHOW y
        """
        program = parser.parse(source)
        
        emitter = NullLangCompiler()
        ir = emitter.compile(program)
        
        vm = NullVM()
        result = vm.execute(ir)
        
        assert result.success is True
        assert "52" in result.output or "52.0" in result.output
    
    def test_if_statement_backward_compatibility(self):
        parser = NullLangParser()
        source = """
        SET x TO 10
        IF x IS GREATER THAN 5 THEN
            SET y TO 100
        ELSE
            SET y TO 50
        END IF
        SHOW y
        """
        program = parser.parse(source)
        
        emitter = NullLangCompiler()
        ir = emitter.compile(program)
        
        vm = NullVM()
        result = vm.execute(ir)
        
        assert result.success is True
        assert "100" in result.output or "100.0" in result.output
    
    def test_repeat_statement_backward_compatibility(self):
        parser = NullLangParser()
        source = """
        SET count TO 0
        REPEAT 3 TIMES
            SET count TO count PLUS 1
        END REPEAT
        SHOW count
        """
        program = parser.parse(source)
        
        emitter = NullLangCompiler()
        ir = emitter.compile(program)
        
        vm = NullVM()
        result = vm.execute(ir)
        
        assert result.success is True
        assert "3" in result.output or "3.0" in result.output


class TestIntegrationScenarios:
    """Integration tests for complete module scenarios."""
    
    def test_complete_module_with_imports(self):
        parser = NullLangParser()
        source = """
        module myapp
        import math
        import utils
        
        SET pi TO 3.14159
        SET radius TO 10
        SET area TO pi TIMES radius TIMES radius
        SHOW area
        """
        program = parser.parse(source)
        
        validator = ASTValidator()
        assert validator.validate(program) is True
        
        emitter = NullLangCompiler()
        ir = emitter.compile(program)
        
        vm = NullVM()
        result = vm.execute(ir)
        
        assert result.success is True
        assert len(result.output) > 0
    
    def test_nested_module_declaration(self):
        parser = NullLangParser()
        source = """
        module company::product::feature
        
        SET version TO 1
        SET name TO "feature"
        SHOW name
        """
        program = parser.parse(source)
        
        assert program.module_declaration.name.full_name == "company::product::feature"
        
        validator = ASTValidator()
        assert validator.validate(program) is True
        
        emitter = NullLangCompiler()
        ir = emitter.compile(program)
        
        vm = NullVM()
        result = vm.execute(ir)
        
        assert result.success is True
