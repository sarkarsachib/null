"""Code completion for Null-Lang LSP."""

from typing import List, Dict, Optional
from lsprotocol.types import CompletionItem, CompletionItemKind
from .document_state import DocumentState


class CompletionProvider:
    """Provides code completions for Null-Lang."""
    
    @staticmethod
    def get_completions(
        doc_state: DocumentState,
        line: int,
        character: int
    ) -> List[Dict]:
        """Get completion items for a position."""
        return doc_state.get_completions_at_position(line, character)
