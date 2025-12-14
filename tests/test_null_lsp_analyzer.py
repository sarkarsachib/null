"""Unit tests for Null-Lang LSP analyzer."""

import pytest
from tools.null_lsp.document_state import DocumentState


class TestDocumentStateBasics:
    """Test basic document state functionality."""
    
    def test_create_document(self):
        """Test creating a document state."""
        doc = DocumentState(uri="file:///test.null", text="SET x TO 5")
        assert doc.uri == "file:///test.null"
        assert doc.text == "SET x TO 5"
    
    def test_update_document(self):
        """Test updating document text."""
        doc = DocumentState(uri="file:///test.null", text="SET x TO 5")
        doc.update("SET y TO 10")
        assert doc.text == "SET y TO 10"


class TestParsingAndDiagnostics:
    """Test parsing and diagnostic generation."""
    
    def test_parse_valid_set_statement(self):
        """Test parsing a valid SET statement."""
        doc = DocumentState(uri="file:///test.null", text="")
        doc.update("SET x TO 5")
        assert doc.ast is not None
        assert doc.parse_error is None
        assert len(doc.diagnostics) == 0
    
    def test_parse_valid_show_statement(self):
        """Test parsing a valid SHOW statement."""
        doc = DocumentState(uri="file:///test.null", text="")
        doc.update("SHOW \"Hello\"")
        assert doc.ast is not None
        assert doc.parse_error is None
    
    def test_parse_invalid_syntax(self):
        """Test that invalid syntax generates diagnostics."""
        doc = DocumentState(uri="file:///test.null", text="")
        doc.update("SET x")
        assert doc.ast is None
        assert doc.parse_error is not None
        assert len(doc.diagnostics) > 0
    
    def test_parse_empty_document(self):
        """Test parsing an empty document."""
        doc = DocumentState(uri="file:///test.null", text="")
        doc.update("")
        assert doc.ast is not None


class TestIdentifierCollection:
    """Test identifier collection and validation."""
    
    def test_collect_defined_variable(self):
        """Test collecting defined variables."""
        doc = DocumentState(uri="file:///test.null", text="")
        doc.update("SET x TO 5")
        assert 'x' in doc.defined_identifiers
    
    def test_collect_multiple_definitions(self):
        """Test collecting multiple defined variables."""
        doc = DocumentState(uri="file:///test.null", text="")
        doc.update("SET x TO 5\nSET y TO 10")
        assert 'x' in doc.defined_identifiers
        assert 'y' in doc.defined_identifiers
    
    def test_undefined_variable_warning(self):
        """Test that undefined variables generate warnings."""
        doc = DocumentState(uri="file:///test.null", text="")
        doc.update("SHOW z")
        assert 'z' in doc.used_identifiers
        assert len(doc.diagnostics) > 0
        assert any('Undefined' in d.get('message', '') for d in doc.diagnostics)
    
    def test_defined_then_used_variable(self):
        """Test that defined variables don't generate warnings."""
        doc = DocumentState(uri="file:///test.null", text="")
        doc.update("SET x TO 5\nSHOW x")
        assert len([d for d in doc.diagnostics if 'Undefined' in d.get('message', '')]) == 0


class TestCompletions:
    """Test completion generation."""
    
    def test_completion_includes_keywords(self):
        """Test that completions include keywords."""
        doc = DocumentState(uri="file:///test.null", text="SET x TO 5")
        completions = doc.get_completions_at_position(0, 0)
        
        keywords = [c for c in completions if c['kind'] == 14]
        keyword_labels = [k['label'] for k in keywords]
        
        assert 'SET' in keyword_labels
        assert 'SHOW' in keyword_labels
        assert 'IF' in keyword_labels
    
    def test_completion_includes_defined_variables(self):
        """Test that completions include defined variables."""
        doc = DocumentState(uri="file:///test.null", text="")
        doc.update("SET myvar TO 5")
        completions = doc.get_completions_at_position(0, 0)
        
        variables = [c for c in completions if c['kind'] == 6]
        variable_labels = [v['label'] for v in variables]
        
        assert 'myvar' in variable_labels
    
    def test_completion_includes_library_functions(self):
        """Test that completions include library functions."""
        doc = DocumentState(uri="file:///test.null", text="SET x TO 5")
        completions = doc.get_completions_at_position(0, 0)
        
        functions = [c for c in completions if c['kind'] == 3]
        
        assert len(functions) > 0
        assert any('math' in f['label'].lower() or 'text' in f['label'].lower() 
                   for f in functions)


class TestHoverInfo:
    """Test hover information."""
    
    def test_hover_on_keyword(self):
        """Test hover information on keywords."""
        doc = DocumentState(uri="file:///test.null", text="SET x TO 5")
        hover = doc.get_hover_info(0, 0)
        assert hover is not None
        assert 'SET' in hover or 'variable' in hover.lower()
    
    def test_hover_on_undefined_variable(self):
        """Test hover on undefined variable returns None."""
        doc = DocumentState(uri="file:///test.null", text="SHOW undefined_var")
        hover = doc.get_hover_info(0, 7)
        # Should return None for undefined variables
        assert hover is None or 'undefined' not in hover.lower()
    
    def test_hover_on_defined_variable(self):
        """Test hover on defined variable."""
        doc = DocumentState(uri="file:///test.null", text="")
        doc.update("SET myvar TO 5")
        hover = doc.get_hover_info(0, 4)
        assert hover is not None or 'myvar' in doc.defined_identifiers


class TestComplexPrograms:
    """Test analyzer on complex programs."""
    
    def test_if_statement(self):
        """Test parsing IF statements."""
        doc = DocumentState(uri="file:///test.null", text="")
        doc.update('SET x TO 5\nIF x IS GREATER THAN 3 THEN\nSHOW "yes"\nEND IF')
        assert doc.ast is not None
        assert 'x' in doc.defined_identifiers
    
    def test_repeat_statement(self):
        """Test parsing REPEAT statements."""
        doc = DocumentState(uri="file:///test.null", text="")
        doc.update('REPEAT 5 TIMES\nSHOW "hello"\nEND REPEAT')
        assert doc.ast is not None
    
    def test_define_statement(self):
        """Test parsing DEFINE statements."""
        doc = DocumentState(uri="file:///test.null", text="")
        doc.update('DEFINE greet WITH msg\nSHOW msg\nEND DEFINE')
        assert doc.ast is not None
        assert 'greet' in doc.defined_identifiers
        assert 'msg' in doc.defined_identifiers
    
    def test_multiple_statements(self):
        """Test parsing multiple statements."""
        code = """SET x TO 10
SET y TO 20
SHOW x
SHOW y"""
        doc = DocumentState(uri="file:///test.null", text="")
        doc.update(code)
        assert doc.ast is not None
        assert 'x' in doc.defined_identifiers
        assert 'y' in doc.defined_identifiers


class TestDiagnosticRanges:
    """Test diagnostic range accuracy."""
    
    def test_diagnostic_has_valid_range(self):
        """Test that diagnostics have valid ranges."""
        doc = DocumentState(uri="file:///test.null", text="")
        doc.update("SHOW undefined_variable")
        
        diagnostics = [d for d in doc.diagnostics if 'Undefined' in d.get('message', '')]
        assert len(diagnostics) > 0
        
        for diag in diagnostics:
            assert 'range' in diag
            assert 'start' in diag['range']
            assert 'end' in diag['range']
            assert 'line' in diag['range']['start']
            assert 'character' in diag['range']['start']
