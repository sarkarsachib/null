"""Diagnostic collection and reporting for Null-Lang LSP."""

from typing import List, Dict
from .document_state import DocumentState


class DiagnosticsCollector:
    """Collects and manages diagnostics for documents."""
    
    @staticmethod
    def get_diagnostics(doc_state: DocumentState) -> List[Dict]:
        """Get all diagnostics for a document."""
        return doc_state.diagnostics
    
    @staticmethod
    def clear_diagnostics(doc_state: DocumentState) -> None:
        """Clear all diagnostics for a document."""
        doc_state.diagnostics = []
