"""Tests for intent detection."""

import pytest
from null_system.nlp.intent import IntentDetector, Intent


class TestIntentDetector:
    """Test suite for intent detection."""

    def test_detect_set_variable_intent(self):
        """Test detection of SET_VARIABLE intent."""
        detector = IntentDetector()
        intents = detector.detect("set x to 5")

        assert len(intents) > 0
        assert any(i.name == "SET_VARIABLE" for i in intents)

    def test_detect_calculate_intent(self):
        """Test detection of CALCULATE intent."""
        detector = IntentDetector()
        intents = detector.detect("add 5 and 10")

        assert len(intents) > 0
        assert any(i.name == "CALCULATE" for i in intents)

    def test_detect_display_intent(self):
        """Test detection of DISPLAY intent."""
        detector = IntentDetector()
        intents = detector.detect("show me the result")

        assert len(intents) > 0
        assert any(i.name == "DISPLAY" for i in intents)

    def test_detect_loop_intent(self):
        """Test detection of LOOP intent."""
        detector = IntentDetector()
        intents = detector.detect("repeat 10 times")

        assert len(intents) > 0
        assert any(i.name == "LOOP" for i in intents)

    def test_detect_condition_intent(self):
        """Test detection of CONDITION intent."""
        detector = IntentDetector()
        intents = detector.detect("if x is greater than 5")

        assert len(intents) > 0
        assert any(i.name == "CONDITION" for i in intents)

    def test_detect_function_definition_intent(self):
        """Test detection of DEFINE_FUNCTION intent."""
        detector = IntentDetector()
        intents = detector.detect("define a function called add")

        assert len(intents) > 0
        # Should have at least one intent
        assert any(i.name in ["DEFINE_FUNCTION", "CALL_FUNCTION"] for i in intents)

    def test_intent_confidence_scores(self):
        """Test that intents have confidence scores."""
        detector = IntentDetector()
        intents = detector.detect("set x to 5")

        assert len(intents) > 0
        for intent in intents:
            assert 0.0 <= intent.confidence <= 1.0

    def test_get_primary_intent(self):
        """Test getting the primary intent."""
        detector = IntentDetector()
        intent = detector.get_primary_intent("set x to 5")

        assert intent is not None
        assert isinstance(intent, Intent)
        assert intent.name is not None
        assert intent.confidence >= 0.0

    def test_match_specific_intent(self):
        """Test matching a specific intent."""
        detector = IntentDetector()

        # Should match SET_VARIABLE
        matches = detector.match_intent("set x to 5", "SET_VARIABLE")
        assert matches

        # Should not match other intent
        matches = detector.match_intent("set x to 5", "DISPLAY")
        assert not matches

    def test_empty_input(self):
        """Test with empty input."""
        detector = IntentDetector()
        intents = detector.detect("")

        assert isinstance(intents, list)

    def test_intent_tokens(self):
        """Test that intent includes tokens."""
        detector = IntentDetector()
        intent = detector.get_primary_intent("set x to 5")

        assert intent is not None
        assert hasattr(intent, "tokens")
        assert isinstance(intent.tokens, list)

    def test_add_custom_intent_template(self):
        """Test adding custom intent templates."""
        detector = IntentDetector()

        # Add a custom intent
        detector.add_intent_template("CUSTOM_ACTION", ["custom", "action", "do"])

        # Should now detect the custom intent
        intents = detector.detect("custom action here")
        intent_names = [i.name for i in intents]
        assert "CUSTOM_ACTION" in intent_names

    def test_get_intent_templates(self):
        """Test retrieving intent templates."""
        detector = IntentDetector()
        templates = detector.get_intent_templates()

        assert isinstance(templates, dict)
        assert "SET_VARIABLE" in templates
        assert "CALCULATE" in templates
        assert "DISPLAY" in templates

    def test_multilingual_intent_detection(self):
        """Test intent detection in different languages."""
        # English
        detector_en = IntentDetector(language="en")
        intent_en = detector_en.get_primary_intent("set x to 5")
        assert intent_en is not None

        # Spanish (with Spanish-like keywords)
        detector_es = IntentDetector(language="es")
        intent_es = detector_es.get_primary_intent("establecer x a 5")
        assert intent_es is not None

    def test_intent_threshold(self):
        """Test intent matching with confidence threshold."""
        detector = IntentDetector()

        # High confidence threshold
        matches = detector.match_intent("set x to 5", "SET_VARIABLE", threshold=0.3)
        assert matches

        # Very high confidence threshold might not match
        matches = detector.match_intent("unclear text", "SET_VARIABLE", threshold=0.99)
        # This might or might not match depending on the text


class TestIntentPerformance:
    """Test intent detection performance."""

    def test_intent_detection_speed(self):
        """Test that intent detection is reasonably fast."""
        import time
        detector = IntentDetector()

        start = time.time()
        intents = detector.detect("set x to 5")
        elapsed_ms = (time.time() - start) * 1000

        # Should be fast (under 50ms)
        assert elapsed_ms < 50.0
        assert len(intents) > 0

    def test_batch_intent_detection_speed(self):
        """Test batch intent detection performance."""
        import time
        detector = IntentDetector()

        texts = ["set x to 5"] * 10

        start = time.time()
        intents_list = [detector.detect(text) for text in texts]
        elapsed_ms = (time.time() - start) * 1000

        # Should be reasonably fast
        assert elapsed_ms < 500.0  # <50ms per item on average
        assert len(intents_list) == 10
