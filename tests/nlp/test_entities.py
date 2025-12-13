"""Tests for entity extraction."""

import pytest
from null_system.nlp.entity_extraction import (
    EntityExtractor, Entity, EntityType
)


class TestEntityExtractor:
    """Test suite for entity extraction."""

    def test_extract_identifiers(self):
        """Test extraction of identifiers."""
        extractor = EntityExtractor()
        text = "set variable x to 5"
        entities = extractor.extract(text)

        identifiers = [e for e in entities if e.entity_type == EntityType.IDENTIFIER]
        assert len(identifiers) > 0
        assert any(e.text == "x" for e in identifiers)

    def test_extract_numbers(self):
        """Test extraction of numbers."""
        extractor = EntityExtractor()
        text = "set x to 42"
        entities = extractor.extract(text)

        numbers = [e for e in entities if e.entity_type == EntityType.NUMBER]
        assert len(numbers) > 0
        assert any(e.text == "42" for e in numbers)

    def test_extract_strings(self):
        """Test extraction of string literals."""
        extractor = EntityExtractor()
        text = 'show "hello world"'
        entities = extractor.extract(text)

        strings = [e for e in entities if e.entity_type == EntityType.STRING]
        assert len(strings) > 0

    def test_extract_keywords(self):
        """Test extraction of keywords."""
        extractor = EntityExtractor()
        text = "if x is equal to 5 then show value"
        entities = extractor.extract(text)

        keywords = [e for e in entities if e.entity_type == EntityType.KEYWORD]
        assert len(keywords) > 0
        assert any(e.text.lower() in ["if", "is", "equal", "then", "show"] for e in keywords)

    def test_extract_operators(self):
        """Test extraction of operators."""
        extractor = EntityExtractor()
        text = "x + y - z"
        entities = extractor.extract(text)

        operators = [e for e in entities if e.entity_type == EntityType.OPERATOR]
        assert len(operators) > 0
        assert any(e.text in ["+", "-"] for e in operators)

    def test_extract_by_type(self):
        """Test extracting entities of a specific type."""
        extractor = EntityExtractor()
        text = "set x to 42"
        entities = extractor.extract_by_type(text, EntityType.NUMBER)

        assert len(entities) > 0
        assert all(e.entity_type == EntityType.NUMBER for e in entities)

    def test_entity_position(self):
        """Test that entity positions are correct."""
        extractor = EntityExtractor()
        text = "set x to 42"
        entities = extractor.extract(text)

        for entity in entities:
            assert entity.start_position >= 0
            assert entity.end_position > entity.start_position

    def test_overlapping_entities(self):
        """Test that overlapping entities are resolved."""
        extractor = EntityExtractor()
        text = "123 + 456"
        entities = extractor.extract(text)

        # Check that entities don't overlap
        for i, e1 in enumerate(entities):
            for e2 in entities[i + 1:]:
                # No overlap
                assert not (e1.start_position < e2.end_position and 
                           e1.end_position > e2.start_position)

    def test_empty_input(self):
        """Test with empty input."""
        extractor = EntityExtractor()
        entities = extractor.extract("")

        assert len(entities) == 0

    def test_add_custom_entity(self):
        """Test adding custom entity mappings."""
        extractor = EntityExtractor()
        extractor.add_custom_entity("myvar", EntityType.VARIABLE)

        text = "set myvar to 5"
        entities = extractor.extract(text)

        # Should recognize myvar as VARIABLE
        variables = [e for e in entities if e.entity_type == EntityType.VARIABLE]
        assert any(e.text.lower() == "myvar" for e in variables)

    def test_get_entity_text_by_type(self):
        """Test getting entity text by type."""
        extractor = EntityExtractor()
        text = "set x to 42 and y to 10"
        texts = extractor.get_entity_text_by_type(text, EntityType.NUMBER)

        assert len(texts) > 0
        assert "42" in texts
        assert "10" in texts

    def test_float_extraction(self):
        """Test extraction of floating point numbers."""
        extractor = EntityExtractor()
        text = "set x to 3.14"
        entities = extractor.extract(text)

        numbers = [e for e in entities if e.entity_type == EntityType.NUMBER]
        assert any("3.14" in e.text for e in numbers)

    def test_complex_expression(self):
        """Test extraction from complex expressions."""
        extractor = EntityExtractor()
        text = "if x > 5 then add x and y else set z to 0"
        entities = extractor.extract(text)

        # Should extract multiple entities
        assert len(entities) > 3

    def test_entity_confidence(self):
        """Test that entities have confidence scores."""
        extractor = EntityExtractor()
        text = "set x to 5"
        entities = extractor.extract(text)

        for entity in entities:
            assert hasattr(entity, "confidence")
            assert 0.0 <= entity.confidence <= 1.0

    def test_python_keywords(self):
        """Test recognition of Python keywords."""
        extractor = EntityExtractor()
        text = "def my_function return True"
        entities = extractor.extract(text)

        keywords = [e for e in entities if e.entity_type == EntityType.KEYWORD]
        keyword_texts = [k.text.lower() for k in keywords]
        
        # Should recognize some keywords
        assert len(keywords) > 0


class TestEntityExtractionPerformance:
    """Test entity extraction performance."""

    def test_extraction_speed(self):
        """Test that extraction is reasonably fast."""
        import time
        extractor = EntityExtractor()

        text = "set x to 42 add y to 100 set z to x and y"

        start = time.time()
        entities = extractor.extract(text)
        elapsed_ms = (time.time() - start) * 1000

        # Should be fast (under 50ms)
        assert elapsed_ms < 50.0
        assert len(entities) > 0

    def test_batch_extraction_speed(self):
        """Test batch extraction performance."""
        import time
        extractor = EntityExtractor()

        texts = ["set x to 42"] * 10

        start = time.time()
        entities_list = [extractor.extract(text) for text in texts]
        elapsed_ms = (time.time() - start) * 1000

        # Should be reasonably fast
        assert elapsed_ms < 500.0  # <50ms per item on average
        assert len(entities_list) == 10
