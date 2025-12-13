"""Entity extraction for Null-Lang NLP engine."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional


class EntityType(Enum):
    """Types of entities that can be extracted."""
    VARIABLE = "VARIABLE"
    NUMBER = "NUMBER"
    STRING = "STRING"
    OPERATOR = "OPERATOR"
    KEYWORD = "KEYWORD"
    FUNCTION_NAME = "FUNCTION_NAME"
    IDENTIFIER = "IDENTIFIER"
    TYPE = "TYPE"
    UNKNOWN = "UNKNOWN"


@dataclass
class Entity:
    """Represents an extracted entity."""
    text: str
    entity_type: EntityType
    start_position: int
    end_position: int
    confidence: float = 1.0

    def __repr__(self) -> str:
        return f"Entity({self.text!r}, {self.entity_type.value}, pos={self.start_position})"


class EntityExtractor:
    """Extracts named entities from text for code generation."""

    # Keywords and operators in various languages
    NULL_KEYWORDS = {
        "set", "to", "add", "and", "show", "repeat", "times",
        "if", "then", "else", "define", "function", "return",
        "true", "false", "not", "or", "is", "greater", "than",
        "less", "equal", "while", "do", "for", "in", "call"
    }

    PYTHON_KEYWORDS = {
        "def", "class", "if", "else", "elif", "for", "while",
        "return", "import", "from", "as", "try", "except", "finally",
        "with", "lambda", "yield", "assert", "raise", "pass", "break",
        "continue", "global", "nonlocal", "and", "or", "not", "in", "is"
    }

    OPERATORS = {
        "+", "-", "*", "/", "%", "//", "**",
        "==", "!=", "<", ">", "<=", ">=",
        "=", "+=", "-=", "*=", "/=",
        "&", "|", "^", "~", "<<", ">>",
        "and", "or", "not"
    }

    def __init__(self):
        """Initialize the entity extractor."""
        self._custom_entities: dict[str, EntityType] = {}

    def extract(self, text: str) -> List[Entity]:
        """
        Extract entities from text.

        Args:
            text: Input text

        Returns:
            List of extracted entities
        """
        entities = []

        # Extract numbers
        entities.extend(self._extract_numbers(text))

        # Extract strings
        entities.extend(self._extract_strings(text))

        # Extract operators
        entities.extend(self._extract_operators(text))

        # Extract keywords
        entities.extend(self._extract_keywords(text))

        # Extract identifiers (variables, functions)
        entities.extend(self._extract_identifiers(text))

        # Remove overlapping entities (keep longer ones)
        entities = self._resolve_overlaps(entities)

        # Sort by position
        entities.sort(key=lambda e: e.start_position)

        return entities

    def _extract_numbers(self, text: str) -> List[Entity]:
        """Extract numeric entities."""
        entities = []
        # Match integers and floats
        pattern = r'\b\d+\.?\d*\b'
        for match in re.finditer(pattern, text):
            entities.append(Entity(
                text=match.group(),
                entity_type=EntityType.NUMBER,
                start_position=match.start(),
                end_position=match.end()
            ))
        return entities

    def _extract_strings(self, text: str) -> List[Entity]:
        """Extract string literal entities."""
        entities = []
        # Match quoted strings (single or double quotes)
        pattern = r'(["\'])(?:(?=(\\?))\2.)*?\1'
        for match in re.finditer(pattern, text):
            entities.append(Entity(
                text=match.group(),
                entity_type=EntityType.STRING,
                start_position=match.start(),
                end_position=match.end()
            ))
        return entities

    def _extract_operators(self, text: str) -> List[Entity]:
        """Extract operator entities."""
        entities = []
        # Sort by length to match longer operators first
        sorted_ops = sorted(self.OPERATORS, key=len, reverse=True)
        pattern = '|'.join(re.escape(op) for op in sorted_ops)

        for match in re.finditer(f'\\b({pattern})\\b|{pattern}', text):
            op_text = match.group()
            if op_text in self.OPERATORS:
                entities.append(Entity(
                    text=op_text,
                    entity_type=EntityType.OPERATOR,
                    start_position=match.start(),
                    end_position=match.end()
                ))
        return entities

    def _extract_keywords(self, text: str) -> List[Entity]:
        """Extract keyword entities."""
        entities = []
        all_keywords = self.NULL_KEYWORDS | self.PYTHON_KEYWORDS

        pattern = '|'.join(f'\\b{kw}\\b' for kw in all_keywords)
        for match in re.finditer(pattern, text, re.IGNORECASE):
            keyword = match.group().lower()
            if keyword in all_keywords:
                entities.append(Entity(
                    text=match.group(),
                    entity_type=EntityType.KEYWORD,
                    start_position=match.start(),
                    end_position=match.end()
                ))
        return entities

    def _extract_identifiers(self, text: str) -> List[Entity]:
        """Extract identifier entities (variables, function names)."""
        entities = []
        # Match identifiers: start with letter/underscore, followed by letters/digits/underscores
        pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'

        for match in re.finditer(pattern, text):
            identifier = match.group()
            # Skip if it's a keyword
            if identifier.lower() in self.NULL_KEYWORDS | self.PYTHON_KEYWORDS:
                continue

            # Check custom entities first
            entity_type = self._custom_entities.get(
                identifier.lower(),
                EntityType.IDENTIFIER
            )

            entities.append(Entity(
                text=identifier,
                entity_type=entity_type,
                start_position=match.start(),
                end_position=match.end()
            ))
        return entities

    def _resolve_overlaps(self, entities: List[Entity]) -> List[Entity]:
        """Remove overlapping entities, keeping longer ones."""
        if not entities:
            return []

        # Sort by position and length
        entities.sort(key=lambda e: (e.start_position, -(e.end_position - e.start_position)))

        result = []
        for entity in entities:
            # Check if overlaps with any already-added entity
            overlaps = False
            for existing in result:
                if (entity.start_position < existing.end_position and 
                    entity.end_position > existing.start_position):
                    overlaps = True
                    break

            if not overlaps:
                result.append(entity)

        return result

    def extract_by_type(self, text: str, entity_type: EntityType) -> List[Entity]:
        """
        Extract entities of a specific type.

        Args:
            text: Input text
            entity_type: Type of entities to extract

        Returns:
            List of entities of the specified type
        """
        entities = self.extract(text)
        return [e for e in entities if e.entity_type == entity_type]

    def add_custom_entity(self, text: str, entity_type: EntityType) -> None:
        """
        Register a custom entity mapping.

        Args:
            text: The entity text (case-insensitive)
            entity_type: The entity type
        """
        self._custom_entities[text.lower()] = entity_type

    def extract_variables(self, text: str) -> List[Entity]:
        """Extract variable names from text."""
        return self.extract_by_type(text, EntityType.VARIABLE)

    def extract_functions(self, text: str) -> List[Entity]:
        """Extract function names from text."""
        return self.extract_by_type(text, EntityType.FUNCTION_NAME)

    def get_entity_text_by_type(self, text: str, entity_type: EntityType) -> List[str]:
        """
        Get text of entities of a specific type.

        Args:
            text: Input text
            entity_type: Type of entities to extract

        Returns:
            List of entity texts
        """
        entities = self.extract_by_type(text, entity_type)
        return [e.text for e in entities]
