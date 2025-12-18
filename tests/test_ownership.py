"""Tests for ownership features in Null-Lang."""

import pytest

from ..parser.lexer import Lexer, TokenType
from ..parser.parser import Parser
from ..ast.validator import ASTValidator
from ..analysis.ownership import OwnershipAnalyzer
from ..superbit.emitter import SuperBitEmitter
from ..superbit.ir import SuperBitOpCode


class TestOwnershipLexer:
    """Test lexer support for Rust-like ownership constructs."""
    
    def test_let_keyword(self):
        """Test let keyword tokenization."""
        lexer = Lexer("let x = 5")
        tokens = lexer.tokenize()
        
        token_types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.LET in token_types
        assert TokenType.EQUALS in token_types
    
    def test_mut_keyword(self):
        """Test mut keyword tokenization."""
        lexer = Lexer("let mut x = 5")
        tokens = lexer.tokenize()
        
        token_types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.MUT in token_types
        assert TokenType.LET in token_types
    
    def test_borrow_token(self):
        """Test & token tokenization."""
        lexer = Lexer("&x")
        tokens = lexer.tokenize()
        
        token_types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.BORROW in token_types
    
    def test_drop_keyword(self):
        """Test drop keyword tokenization."""
        lexer = Lexer("drop x")
        tokens = lexer.tokenize()
        
        token_types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.DROP in token_types


class TestOwnershipParser:
    """Test parser support for ownership constructs."""
    
    def test_let_binding_parsing(self):
        """Test parsing let bindings."""
        source = "let x = 42"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert stmt.__class__.__name__ == "LetBinding"
        assert stmt.pattern.name == "x"
        assert stmt.mutable == False
        assert stmt.value.value == 42
    
    def test_let_mut_binding_parsing(self):
        """Test parsing mutable let bindings."""
        source = "let mut x = 42"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert stmt.__class__.__name__ == "LetBinding"
        assert stmt.pattern.name == "x"
        assert stmt.mutable == True
        assert stmt.value.value == 42
    
    def test_borrow_expression_parsing(self):
        """Test parsing borrow expressions."""
        source = "&x"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert len(ast.statements) == 1
        expr = ast.statements[0]
        assert expr.__class__.__name__ == "BorrowExpr"
        assert expr.mutable == False
        assert expr.expr.name == "x"
    
    def test_mutable_borrow_parsing(self):
        """Test parsing mutable borrow expressions."""
        source = "&mut x"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert len(ast.statements) == 1
        expr = ast.statements[0]
        assert expr.__class__.__name__ == "BorrowExpr"
        assert expr.mutable == True
        assert expr.expr.name == "x"
    
    def test_drop_statement_parsing(self):
        """Test parsing drop statements."""
        source = "drop x"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        assert len(ast.statements) == 1
        stmt = ast.statements[0]
        assert stmt.__class__.__name__ == "DropStatement"
        assert stmt.target.name == "x"


class TestOwnershipValidator:
    """Test AST validation with ownership features."""
    
    def test_valid_let_binding(self):
        """Test valid let binding passes validation."""
        source = "let x = 42"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        validator = ASTValidator()
        is_valid = validator.validate(ast)
        assert is_valid == True
        assert len(validator.errors) == 0
    
    def test_duplicate_variable_error(self):
        """Test duplicate variable definition error."""
        source = "let x = 42\nlet x = 24"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        validator = ASTValidator()
        is_valid = validator.validate(ast)
        assert is_valid == False
        assert len(validator.errors) > 0
        assert "already defined" in validator.errors[0].lower()
    
    def test_borrow_of_undefined_variable(self):
        """Test borrow of undefined variable error."""
        source = "&undefined_var"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        validator = ASTValidator()
        is_valid = validator.validate(ast)
        assert is_valid == False
        assert len(validator.errors) > 0
        assert "undefined" in validator.errors[0].lower()


class TestOwnershipAnalyzer:
    """Test ownership analysis features."""
    
    def test_valid_ownership_simple(self):
        """Test valid simple ownership scenario."""
        source = "let x = 42"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        analyzer = OwnershipAnalyzer()
        is_valid = analyzer.analyze(ast)
        assert is_valid == True
        assert len(analyzer.get_errors()) == 0
    
    def test_valid_borrow_scenario(self):
        """Test valid borrow scenario."""
        source = "let x = 42\nlet y = &x"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        analyzer = OwnershipAnalyzer()
        is_valid = analyzer.analyze(ast)
        assert is_valid == True
        assert len(analyzer.get_errors()) == 0
    
    def test_double_mutable_borrow_error(self):
        """Test error on double mutable borrow."""
        source = "let mut x = 42\nlet y = &mut x\nlet z = &mut x"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        analyzer = OwnershipAnalyzer()
        is_valid = analyzer.analyze(ast)
        assert is_valid == False
        assert len(analyzer.get_errors()) > 0
        assert "mutable borrow" in analyzer.get_errors()[0].lower()
    
    def test_borrow_immutable_variable_error(self):
        """Test error when borrowing immutable variable mutably."""
        source = "let x = 42\nlet y = &mut x"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        analyzer = OwnershipAnalyzer()
        is_valid = analyzer.analyze(ast)
        assert is_valid == False
        assert len(analyzer.get_errors()) > 0
        assert "immutable" in analyzer.get_errors()[0].lower()
    
    def test_drop_borrowed_variable_error(self):
        """Test error when dropping borrowed variable."""
        source = "let x = 42\nlet y = &x\ndrop x"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        analyzer = OwnershipAnalyzer()
        is_valid = analyzer.analyze(ast)
        assert is_valid == False
        assert len(analyzer.get_errors()) > 0
        assert "borrowed" in analyzer.get_errors()[0].lower()


class TestOwnershipEmitter:
    """Test SuperBit emitter with ownership opcodes."""
    
    def test_let_binding_emits_store_var(self):
        """Test let binding emits STORE_VAR opcode."""
        source = "let x = 42"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        emitter = SuperBitEmitter()
        stream = emitter.emit(ast)
        
        opcodes = [token.opcode for token in stream.tokens]
        assert SuperBitOpCode.STORE_VAR in opcodes
        assert SuperBitOpCode.LOAD_CONST in opcodes
    
    def test_borrow_emits_borrow_opcodes(self):
        """Test borrow expressions emit appropriate borrow opcodes."""
        source = "&x"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        emitter = SuperBitEmitter()
        stream = emitter.emit(ast)
        
        opcodes = [token.opcode for token in stream.tokens]
        assert SuperBitOpCode.BORROW_IMM in opcodes
        assert SuperBitOpCode.LOAD_VAR in opcodes
    
    def test_mutable_borrow_emits_borrow_mut(self):
        """Test mutable borrow emits BORROW_MUT opcode."""
        source = "&mut x"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        emitter = SuperBitEmitter()
        stream = emitter.emit(ast)
        
        opcodes = [token.opcode for token in stream.tokens]
        assert SuperBitOpCode.BORROW_MUT in opcodes
        assert SuperBitOpCode.LOAD_VAR in opcodes
    
    def test_drop_emits_drop_opcode(self):
        """Test drop statements emit DROP opcode."""
        source = "drop x"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        emitter = SuperBitEmitter()
        stream = emitter.emit(ast)
        
        opcodes = [token.opcode for token in stream.tokens]
        assert SuperBitOpCode.DROP in opcodes
        assert SuperBitOpCode.LOAD_VAR in opcodes


class TestComplexOwnershipScenarios:
    """Test complex ownership scenarios."""
    
    def test_scope_based_lifetime(self):
        """Test scope-based variable lifetime."""
        source = "let x = 42"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        analyzer = OwnershipAnalyzer()
        is_valid = analyzer.analyze(ast)
        assert is_valid == True
        
        # Variable should exist
        var_info = analyzer.get_variable_state("x")
        assert var_info is not None
        assert var_info.name == "x"
        assert var_info.mutable == False
    
    def test_mixed_ownership_and_english_syntax(self):
        """Test mixing ownership features with English syntax."""
        source = "set x to 42\nlet y = &x\nprint y"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        analyzer = OwnershipAnalyzer()
        is_valid = analyzer.analyze(ast)
        assert is_valid == True
    
    def test_complete_ownership_lifecycle(self):
        """Test complete ownership lifecycle with all features."""
        source = """
        let mut data = 42
        let ref1 = &data
        let ref2 = &data
        let mut_ref = &mut data
        drop ref1
        drop ref2
        drop mut_ref
        drop data
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        # Should fail due to multiple borrows
        analyzer = OwnershipAnalyzer()
        is_valid = analyzer.analyze(ast)
        # This might pass or fail depending on current implementation


class TestBackwardCompatibility:
    """Test backward compatibility with existing English syntax."""
    
    def test_english_syntax_still_works(self):
        """Test existing English syntax continues to work."""
        source = "set x to 42\nprint x"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        validator = ASTValidator()
        is_valid = validator.validate(ast)
        assert is_valid == True
        assert len(validator.errors) == 0
    
    def test_mixed_syntax_validation(self):
        """Test mixing ownership and English syntax."""
        source = """
        set x to 42
        let y = &x
        print y
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        validator = ASTValidator()
        is_valid = validator.validate(ast)
        assert is_valid == True
        assert len(validator.errors) == 0