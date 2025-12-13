"""Context management for Null-Lang NLP engine."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from .embeddings import EmbeddingModel


@dataclass
class ContextFrame:
    """Represents a context frame for tracking conversation state."""
    variables: Dict[str, Any] = field(default_factory=dict)
    functions: Dict[str, str] = field(default_factory=dict)
    imports: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (f"ContextFrame(vars={len(self.variables)}, "
                f"funcs={len(self.functions)}, "
                f"imports={len(self.imports)})")


class ContextManager:
    """Manages context and state for multi-turn NLP interactions."""

    def __init__(self, max_history: int = 50):
        """
        Initialize the context manager.

        Args:
            max_history: Maximum number of history entries to keep
        """
        self.max_history = max_history
        self.frames: List[ContextFrame] = [ContextFrame()]
        self.history: List[str] = []
        self.embedding_model = EmbeddingModel()

    def push_frame(self) -> None:
        """Push a new context frame onto the stack."""
        new_frame = ContextFrame()
        # Inherit variables and functions from current frame
        if self.frames:
            current = self.frames[-1]
            new_frame.variables = dict(current.variables)
            new_frame.functions = dict(current.functions)
            new_frame.imports = list(current.imports)

        self.frames.append(new_frame)

    def pop_frame(self) -> Optional[ContextFrame]:
        """Pop the current context frame from the stack."""
        if len(self.frames) > 1:
            return self.frames.pop()
        return None

    def current_frame(self) -> ContextFrame:
        """Get the current context frame."""
        return self.frames[-1] if self.frames else ContextFrame()

    def set_variable(self, name: str, value: Any) -> None:
        """
        Set a variable in the current context.

        Args:
            name: Variable name
            value: Variable value
        """
        self.current_frame().variables[name] = value

    def get_variable(self, name: str) -> Optional[Any]:
        """
        Get a variable from the current context.

        Args:
            name: Variable name

        Returns:
            Variable value or None if not found
        """
        # Search from current frame backwards through history
        for frame in reversed(self.frames):
            if name in frame.variables:
                return frame.variables[name]
        return None

    def has_variable(self, name: str) -> bool:
        """
        Check if a variable exists in the current context.

        Args:
            name: Variable name

        Returns:
            True if variable exists
        """
        for frame in reversed(self.frames):
            if name in frame.variables:
                return True
        return False

    def add_function(self, name: str, definition: str) -> None:
        """
        Register a function in the current context.

        Args:
            name: Function name
            definition: Function definition code
        """
        self.current_frame().functions[name] = definition

    def get_function(self, name: str) -> Optional[str]:
        """
        Get a function definition from context.

        Args:
            name: Function name

        Returns:
            Function definition or None if not found
        """
        for frame in reversed(self.frames):
            if name in frame.functions:
                return frame.functions[name]
        return None

    def add_import(self, module: str) -> None:
        """
        Add an import to the current context.

        Args:
            module: Module name
        """
        frame = self.current_frame()
        if module not in frame.imports:
            frame.imports.append(module)

    def get_imports(self) -> List[str]:
        """Get all imports in the current context."""
        return self.current_frame().imports.copy()

    def add_to_history(self, entry: str) -> None:
        """
        Add an entry to the conversation history.

        Args:
            entry: History entry (code, command, or user input)
        """
        self.history.append(entry)
        # Keep history size in check
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_history(self, limit: Optional[int] = None) -> List[str]:
        """
        Get conversation history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of history entries
        """
        if limit is None:
            return self.history.copy()
        return self.history[-limit:] if self.history else []

    def get_similar_entries(self, query: str, top_k: int = 5) -> List[tuple[str, float]]:
        """
        Find similar history entries using embeddings.

        Args:
            query: Query text
            top_k: Number of top entries to return

        Returns:
            List of (entry, similarity_score) tuples
        """
        if not self.history:
            return []

        query_emb = self.embedding_model.embed(query)
        scores = []

        for entry in self.history:
            entry_emb = self.embedding_model.embed(entry)
            similarity = self.embedding_model.cosine_similarity(query_emb, entry_emb)
            scores.append((entry, (similarity + 1.0) / 2.0))  # Normalize to [0, 1]

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def get_context_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current context.

        Returns:
            Dictionary with context information
        """
        frame = self.current_frame()
        return {
            "variables": list(frame.variables.keys()),
            "functions": list(frame.functions.keys()),
            "imports": frame.imports,
            "history_length": len(self.history),
            "frame_depth": len(self.frames),
        }

    def clear_context(self) -> None:
        """Clear the entire context."""
        self.frames = [ContextFrame()]
        self.history = []
        self.embedding_model.clear_cache()

    def export_context(self) -> Dict[str, Any]:
        """
        Export the current context state.

        Returns:
            Dictionary representing the context
        """
        frame = self.current_frame()
        return {
            "variables": dict(frame.variables),
            "functions": dict(frame.functions),
            "imports": frame.imports,
            "metadata": dict(frame.metadata),
            "history": self.history.copy(),
        }

    def import_context(self, context_dict: Dict[str, Any]) -> None:
        """
        Import context state.

        Args:
            context_dict: Dictionary to import from
        """
        frame = self.current_frame()
        if "variables" in context_dict:
            frame.variables.update(context_dict["variables"])
        if "functions" in context_dict:
            frame.functions.update(context_dict["functions"])
        if "imports" in context_dict:
            frame.imports.extend(context_dict["imports"])
        if "history" in context_dict:
            self.history.extend(context_dict["history"])
