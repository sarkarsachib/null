"""Intent detection for Null-Lang NLP engine."""

from dataclasses import dataclass
from typing import List, Dict, Optional
from .embeddings import EmbeddingModel
from .tokenizer import Tokenizer


@dataclass
class Intent:
    """Represents a detected intent."""
    name: str
    confidence: float
    tokens: List[str]

    def __repr__(self) -> str:
        return f"Intent({self.name}, confidence={self.confidence:.3f})"


class IntentDetector:
    """Detects user intent from natural language input."""

    def __init__(self, language: str = "en"):
        """
        Initialize the intent detector.

        Args:
            language: Language code ('en', 'zh', 'es')
        """
        self.language = language
        self.tokenizer = Tokenizer(language=language)
        self.embedding_model = EmbeddingModel()

        # Intent templates for different domains
        self._intent_templates: Dict[str, List[str]] = {
            "SET_VARIABLE": [
                "set", "assign", "define", "initialize", "put",
                "store", "save", "declare"
            ],
            "CALCULATE": [
                "add", "subtract", "multiply", "divide", "compute",
                "calculate", "sum", "total", "minus", "times"
            ],
            "DISPLAY": [
                "show", "print", "display", "output", "show me",
                "tell", "reveal", "exhibit"
            ],
            "LOOP": [
                "repeat", "loop", "for", "while", "iterate",
                "cycle", "go through", "foreach"
            ],
            "CONDITION": [
                "if", "unless", "when", "check", "verify",
                "condition", "case", "switch"
            ],
            "DEFINE_FUNCTION": [
                "define", "function", "create", "make",
                "procedure", "subroutine", "method"
            ],
            "CALL_FUNCTION": [
                "call", "invoke", "execute", "run", "apply",
                "use", "trigger"
            ],
            "QUERY": [
                "what", "where", "which", "how", "who",
                "when", "why", "help", "explain"
            ],
            "CODE_GENERATION": [
                "generate", "create code", "write code", "produce",
                "compile", "translate", "convert"
            ]
        }

    def detect(self, text: str, top_k: int = 1) -> List[Intent]:
        """
        Detect intent(s) from input text.

        Args:
            text: Input text
            top_k: Number of top intents to return

        Returns:
            List of detected intents (sorted by confidence)
        """
        if not text:
            return []

        # Tokenize
        tokens_list = self.tokenizer.tokenize(text)
        token_texts = [t.text.lower() for t in tokens_list]

        # Calculate intent scores
        intent_scores: Dict[str, float] = {}

        for intent_name, template_words in self._intent_templates.items():
            score = 0.0
            matched_words = []

            for token in token_texts:
                # Direct match
                if token in template_words:
                    score += 1.0
                    matched_words.append(token)
                else:
                    # Semantic similarity
                    best_match, similarity = self.embedding_model.find_most_similar(
                        token, template_words
                    )
                    if similarity > 0.6:
                        score += similarity
                        matched_words.append(token)

            # Normalize score
            if token_texts:
                intent_scores[intent_name] = score / len(token_texts)
            else:
                intent_scores[intent_name] = 0.0

        # Sort by score and return top-k
        sorted_intents = sorted(
            intent_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        results = []
        for intent_name, confidence in sorted_intents[:top_k]:
            if confidence > 0:
                results.append(Intent(
                    name=intent_name,
                    confidence=min(1.0, confidence),
                    tokens=token_texts
                ))

        # If no intent found, return QUERY as default
        if not results:
            results.append(Intent(
                name="QUERY",
                confidence=0.1,
                tokens=token_texts
            ))

        return results

    def get_primary_intent(self, text: str) -> Optional[Intent]:
        """
        Get the primary (highest confidence) intent.

        Args:
            text: Input text

        Returns:
            The primary intent, or None if no intent detected
        """
        intents = self.detect(text, top_k=1)
        return intents[0] if intents else None

    def match_intent(self, text: str, intent_name: str, threshold: float = 0.5) -> bool:
        """
        Check if text matches a specific intent.

        Args:
            text: Input text
            intent_name: Intent name to match
            threshold: Confidence threshold

        Returns:
            True if text matches the intent above threshold
        """
        intents = self.detect(text, top_k=1)
        if not intents:
            return False

        primary = intents[0]
        return (primary.name == intent_name and 
                primary.confidence >= threshold)

    def add_intent_template(self, intent_name: str, keywords: List[str]) -> None:
        """
        Add or update an intent template.

        Args:
            intent_name: Name of the intent
            keywords: List of keywords for this intent
        """
        self._intent_templates[intent_name] = keywords

    def get_intent_templates(self) -> Dict[str, List[str]]:
        """
        Get all intent templates.

        Returns:
            Dictionary mapping intent names to keyword lists
        """
        return dict(self._intent_templates)
