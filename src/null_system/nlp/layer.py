"""NLP/knowledge layer for Null source code.

Implements the Phase 1-4 deliverables from ``docs/blocked_subsystems.md``:

* Phase 1 - semantic understanding of code and comments
* Phase 2 - knowledge graph construction with query support
* Phase 3 - cross-reference linking between definitions and uses
* Phase 4 - semantic search over a codebase using embeddings

The layer composes the existing :mod:`null_system.nlp` components (tokenizer,
intent detection, entity extraction, embeddings) with the knowledge graph store.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from ..knowledge.graph_store import GraphStore, InMemoryBackend
from .embeddings import EmbeddingModel
from .entity_extraction import EntityExtractor
from .intent import IntentDetector

KEYWORDS = (
    "SET",
    "SHOW",
    "ADD",
    "IF",
    "THEN",
    "ELSE",
    "END",
    "REPEAT",
    "TIMES",
    "DEFINE",
    "WITH",
    "CALL",
    "RETURN",
    "MATCH",
    "CASE",
    "WHEN",
    "LET",
)
_IDENTIFIER_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")


@dataclass
class SemanticAnalysis:
    """Result of analysing code and its comments."""

    identifiers: List[str] = field(default_factory=list)
    keywords: Dict[str, int] = field(default_factory=dict)
    intents: List[Dict[str, Any]] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    complexity: Dict[str, int] = field(default_factory=dict)

    @property
    def cyclomatic_complexity(self) -> int:
        return self.complexity.get("cyclomatic", 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identifiers": list(self.identifiers),
            "keywords": dict(self.keywords),
            "intents": list(self.intents),
            "entities": list(self.entities),
            "summary": self.summary,
            "complexity": dict(self.complexity),
        }


@dataclass
class CodeMatch:
    """A semantic search hit."""

    path: str
    line: int
    score: float
    snippet: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "line": self.line,
            "score": round(self.score, 6),
            "snippet": self.snippet,
        }


class NLPLayer:
    """Natural language + knowledge graph layer for Null code."""

    def __init__(
        self,
        *,
        language: str = "en",
        embedding_model: Optional[EmbeddingModel] = None,
        graph: Optional[GraphStore] = None,
    ) -> None:
        self.language = language
        self.embedding_model = embedding_model or EmbeddingModel()
        self.intent_detector = IntentDetector(language=language)
        self.entity_extractor = EntityExtractor()
        self.graph = graph or GraphStore(InMemoryBackend())

    # ------------------------------------------------------------------
    # Phase 1: semantic understanding
    # ------------------------------------------------------------------
    def analyze_semantic_meaning(self, code: str, comments: str = "") -> SemanticAnalysis:
        """Analyse ``code`` and ``comments`` for meaning, intent and entities."""
        if not isinstance(code, str):
            raise TypeError("code must be a string")
        comments = comments or ""

        identifiers: List[str] = []
        for match in _IDENTIFIER_RE.finditer(code):
            name = match.group(0)
            if name.upper() in KEYWORDS:
                continue
            if name not in identifiers:
                identifiers.append(name)

        keyword_counts: Dict[str, int] = {}
        for match in _IDENTIFIER_RE.finditer(code):
            upper = match.group(0).upper()
            if upper in KEYWORDS:
                keyword_counts[upper] = keyword_counts.get(upper, 0) + 1

        analysis_text = comments.strip() or self._strip_code_noise(code)
        intents = []
        try:
            for intent in self.intent_detector.detect(analysis_text, top_k=3):
                intents.append(
                    {
                        "name": getattr(intent, "name", getattr(intent, "intent", "unknown")),
                        "confidence": float(getattr(intent, "confidence", 0.0)),
                    }
                )
        except Exception:  # noqa: BLE001 - NLP is best effort
            intents = []

        entities = []
        try:
            for entity in self.entity_extractor.extract(analysis_text):
                entities.append(
                    {
                        "text": getattr(entity, "text", ""),
                        "type": str(getattr(entity, "type", "unknown")),
                    }
                )
        except Exception:  # noqa: BLE001 - NLP is best effort
            entities = []

        branches = keyword_counts.get("IF", 0) + keyword_counts.get("CASE", 0)
        loops = keyword_counts.get("REPEAT", 0)
        functions = keyword_counts.get("DEFINE", 0)
        complexity = {
            "lines": len(code.splitlines()),
            "statements": max(1, keyword_counts.get("SET", 0) + keyword_counts.get("SHOW", 0)),
            "branches": branches,
            "loops": loops,
            "functions": functions,
            "cyclomatic": 1 + branches + loops,
        }

        summary = self._summarise(identifiers, keyword_counts, complexity)
        return SemanticAnalysis(
            identifiers=identifiers,
            keywords=keyword_counts,
            intents=intents,
            entities=entities,
            summary=summary,
            complexity=complexity,
        )

    @staticmethod
    def _strip_code_noise(code: str) -> str:
        text = re.sub(r"#[^\n]*", " ", code)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _summarise(
        identifiers: Sequence[str], keywords: Dict[str, int], complexity: Dict[str, int]
    ) -> str:
        parts = [f"{complexity['lines']} line(s)"]
        if keywords.get("DEFINE"):
            parts.append(f"{keywords['DEFINE']} function definition(s)")
        if keywords.get("IF"):
            parts.append(f"{keywords['IF']} conditional(s)")
        if keywords.get("REPEAT"):
            parts.append(f"{keywords['REPEAT']} loop(s)")
        if identifiers:
            preview = ", ".join(identifiers[:5])
            parts.append(f"identifiers: {preview}")
        return "; ".join(parts)

    # ------------------------------------------------------------------
    # Phase 2: knowledge graph
    # ------------------------------------------------------------------
    def build_knowledge_graph(self, ast: Any, *, name: str = "__program__") -> GraphStore:
        """Build a knowledge graph from a parsed program.

        Every statement becomes a ``statement`` entity linked to the program via
        ``contains``; definitions create ``variable``/``function`` entities with
        ``defines`` edges and calls add ``calls`` edges.
        """
        program_entity = self.graph.upsert_entity(
            "program", {"name": name, "statements": len(getattr(ast, "statements", []))}
        )

        statements = getattr(ast, "statements", None) or []
        for index, statement in enumerate(statements):
            kind = statement.__class__.__name__
            statement_entity = self.graph.upsert_entity(
                "statement", {"index": index, "kind": kind}
            )
            self.graph.create_relationship(
                program_entity.id, statement_entity.id, "contains"
            )

            for symbol, symbol_kind in self._symbols_in(statement):
                entity = self.graph.upsert_entity(
                    symbol_kind, {"name": symbol}
                )
                relationship = "defines" if symbol_kind in {"variable", "function"} else "uses"
                self.graph.create_relationship(
                    statement_entity.id, entity.id, relationship
                )

        return self.graph

    def _symbols_in(self, statement: Any) -> List[Tuple[str, str]]:
        """Extract (symbol, kind) pairs from a statement node."""
        found: List[Tuple[str, str]] = []
        kind = statement.__class__.__name__

        def name_of(value: Any) -> Optional[str]:
            if isinstance(value, str):
                return value
            return getattr(value, "name", None) if value is not None else None

        if kind in {"SetCommand", "LetBindingExpression", "InputCommand"}:
            target = name_of(
                getattr(statement, "target", None) or getattr(statement, "name", None)
            )
            if target:
                found.append((target, "variable"))
        elif kind == "DefineCommand":
            target = name_of(getattr(statement, "name", None))
            if target:
                found.append((target, "function"))
        elif kind in {"FunctionCall"}:
            target = name_of(getattr(statement, "name", None))
            if target:
                found.append((target, "call"))

        for field_name in ("value", "condition", "count", "expr"):
            value = getattr(statement, field_name, None)
            if value is not None:
                for symbol in self._identifiers_in_node(value):
                    found.append((symbol, "use"))
        return found

    def _identifiers_in_node(self, node: Any, depth: int = 0) -> List[str]:
        if depth > 6 or node is None:
            return []
        if node.__class__.__name__ == "Identifier":
            name = getattr(node, "name", None)
            return [name] if isinstance(name, str) else []
        results: List[str] = []
        for attribute in ("left", "right", "operand", "value"):
            results.extend(self._identifiers_in_node(getattr(node, attribute, None), depth + 1))
        return results

    def query_knowledge_graph(self, query: str) -> List[Any]:
        """Query the knowledge graph.

        Supports ``type:<entity type>`` filters, ``name:<substring>`` filters and
        free-text search across entity types and properties.
        """
        if not query or not query.strip():
            return []

        query = query.strip()
        entity_type: Optional[str] = None
        substring: Optional[str] = None

        if query.lower().startswith("type:"):
            entity_type = query.split(":", 1)[1].strip()
        elif query.lower().startswith("name:"):
            substring = query.split(":", 1)[1].strip().lower()
        else:
            substring = query.lower()

        results = []
        for entity in self.graph.list_entities(entity_type):
            if substring is None:
                results.append(entity)
                continue
            haystack = f"{entity.type} {entity.properties}".lower()
            if substring in haystack:
                results.append(entity)
        return results

    # ------------------------------------------------------------------
    # Phase 3: cross references
    # ------------------------------------------------------------------
    def cross_references(self, code: str) -> Dict[str, List[int]]:
        """Map each defined symbol to the lines where it is referenced."""
        definitions: Dict[str, int] = {}
        for number, line in enumerate(code.splitlines(), start=1):
            match = re.match(r"\s*(?:DEFINE|LET)\s+([A-Za-z_][A-Za-z0-9_]*)", line, re.IGNORECASE)
            if match:
                definitions[match.group(1)] = number
                continue
            match = re.match(r"\s*SET\s+([A-Za-z_][A-Za-z0-9_]*)", line, re.IGNORECASE)
            if match:
                definitions.setdefault(match.group(1), number)

        references: Dict[str, List[int]] = {name: [] for name in definitions}
        for number, line in enumerate(code.splitlines(), start=1):
            for name, definition_line in definitions.items():
                if number == definition_line:
                    continue
                if re.search(rf"\b{re.escape(name)}\b", line):
                    references[name].append(number)
        return references

    # ------------------------------------------------------------------
    # Phase 4: semantic search
    # ------------------------------------------------------------------
    def semantic_search(
        self,
        query: str,
        codebase: Union[Dict[str, str], Iterable[Tuple[str, str]]],
        *,
        limit: int = 5,
        window: int = 4,
        min_score: float = 0.0,
    ) -> List[CodeMatch]:
        """Search a codebase for semantically similar snippets."""
        if not query:
            raise ValueError("query must not be empty")
        if limit <= 0:
            raise ValueError("limit must be positive")

        items: Iterable[Tuple[str, str]]
        if isinstance(codebase, dict):
            items = codebase.items()
        else:
            items = codebase

        query_embedding = self.embedding_model.embed(query)
        matches: List[CodeMatch] = []

        for path, source in items:
            lines = str(source).splitlines()
            if not lines:
                continue
            for start in range(0, len(lines), window):
                snippet_lines = lines[start : start + window]
                snippet = "\n".join(snippet_lines).strip()
                if not snippet:
                    continue
                score = self.embedding_model.cosine_similarity(
                    query_embedding, self.embedding_model.embed(snippet)
                )
                if score >= min_score:
                    matches.append(
                        CodeMatch(
                            path=str(path),
                            line=start + 1,
                            score=score,
                            snippet=snippet,
                        )
                    )

        matches.sort(key=lambda match: match.score, reverse=True)
        return matches[:limit]

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def build_graph_from_source(self, source: str, *, name: str = "__program__") -> GraphStore:
        """Parse ``source`` with the Null parser and build its knowledge graph."""
        from ..lang.parser import parse

        ast = parse(source)
        return self.build_knowledge_graph(ast, name=name)
