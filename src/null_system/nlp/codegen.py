"""Code generation from natural language for Null-Lang."""

from dataclasses import dataclass
from typing import List, Optional, Dict
from .intent import IntentDetector, Intent
from .entity_extraction import EntityExtractor, Entity, EntityType
from .tokenizer import Tokenizer, Token


@dataclass
class GeneratedCode:
    """Represents generated code from NLP."""
    source_text: str
    generated_code: str
    intent: Optional[Intent]
    entities: List[Entity]
    confidence: float
    language: str = "null"

    def __repr__(self) -> str:
        return f"GeneratedCode(lang={self.language}, conf={self.confidence:.3f})"


class CodeGenerator:
    """Generates Null-Lang code from natural language."""

    def __init__(self, language: str = "en"):
        """
        Initialize the code generator.

        Args:
            language: Language code ('en', 'es', 'zh')
        """
        self.language = language
        self.intent_detector = IntentDetector(language=language)
        self.entity_extractor = EntityExtractor()
        self.tokenizer = Tokenizer(language=language)

    def generate(self, text: str, target_language: str = "null") -> GeneratedCode:
        """
        Generate code from natural language.

        Args:
            text: Natural language description
            target_language: Target language ('null', 'python')

        Returns:
            GeneratedCode object
        """
        if not text:
            return GeneratedCode(
                source_text=text,
                generated_code="",
                intent=None,
                entities=[],
                confidence=0.0,
                language=target_language
            )

        # Detect intent
        intent = self.intent_detector.get_primary_intent(text)

        # Extract entities
        entities = self.entity_extractor.extract(text)

        # Generate code based on intent
        if intent and intent.name == "SET_VARIABLE":
            code = self._generate_set_variable(text, entities)
        elif intent and intent.name == "CALCULATE":
            code = self._generate_calculation(text, entities)
        elif intent and intent.name == "DISPLAY":
            code = self._generate_display(text, entities)
        elif intent and intent.name == "LOOP":
            code = self._generate_loop(text, entities)
        elif intent and intent.name == "CONDITION":
            code = self._generate_condition(text, entities)
        elif intent and intent.name == "DEFINE_FUNCTION":
            code = self._generate_function_definition(text, entities)
        elif intent and intent.name == "CALL_FUNCTION":
            code = self._generate_function_call(text, entities)
        else:
            code = self._generate_generic(text, entities)

        confidence = (intent.confidence if intent else 0.5) * 0.8 + 0.2

        return GeneratedCode(
            source_text=text,
            generated_code=code,
            intent=intent,
            entities=entities,
            confidence=confidence,
            language=target_language
        )

    def _get_identifiers(self, entities: List[Entity]) -> List[str]:
        """Extract identifier names from entities."""
        identifiers = []
        for entity in entities:
            if entity.entity_type == EntityType.IDENTIFIER:
                identifiers.append(entity.text)
        return identifiers

    def _get_numbers(self, entities: List[Entity]) -> List[str]:
        """Extract numbers from entities."""
        numbers = []
        for entity in entities:
            if entity.entity_type == EntityType.NUMBER:
                numbers.append(entity.text)
        return numbers

    def _get_strings(self, entities: List[Entity]) -> List[str]:
        """Extract strings from entities."""
        strings = []
        for entity in entities:
            if entity.entity_type == EntityType.STRING:
                strings.append(entity.text)
        return strings

    def _generate_set_variable(self, text: str, entities: List[Entity]) -> str:
        """Generate SET variable code."""
        identifiers = self._get_identifiers(entities)
        numbers = self._get_numbers(entities)

        if identifiers and numbers:
            var_name = identifiers[0]
            value = numbers[0]
            return f"set {var_name} to {value}"
        elif identifiers:
            if len(identifiers) >= 2:
                return f"set {identifiers[0]} to {identifiers[1]}"
            else:
                return f"set {identifiers[0]} to 0"
        else:
            return "set variable to value"

    def _generate_calculation(self, text: str, entities: List[Entity]) -> str:
        """Generate calculation code."""
        identifiers = self._get_identifiers(entities)
        numbers = self._get_numbers(entities)

        # Try to determine operator from text
        text_lower = text.lower()
        operator = "and"

        if "multiply" in text_lower or "times" in text_lower:
            operator = "times"
        elif "divide" in text_lower:
            return "divide"  # Special syntax needed
        elif "subtract" in text_lower or "minus" in text_lower:
            return "subtract"  # Special syntax needed

        if len(identifiers) >= 2:
            return f"add {identifiers[0]} {operator} {identifiers[1]}"
        elif len(identifiers) == 1 and numbers:
            return f"add {identifiers[0]} {operator} {numbers[0]}"
        elif len(numbers) >= 2:
            return f"add {numbers[0]} {operator} {numbers[1]}"
        else:
            return "add value and value"

    def _generate_display(self, text: str, entities: List[Entity]) -> str:
        """Generate SHOW/PRINT code."""
        identifiers = self._get_identifiers(entities)
        strings = self._get_strings(entities)

        if identifiers:
            return f"show {identifiers[0]}"
        elif strings:
            return f'show {strings[0]}'
        else:
            return "show value"

    def _generate_loop(self, text: str, entities: List[Entity]) -> str:
        """Generate REPEAT/LOOP code."""
        numbers = self._get_numbers(entities)
        identifiers = self._get_identifiers(entities)

        count = numbers[0] if numbers else "10"

        # Parse for loop body (simplified)
        return f"repeat {count} times\n  show value"

    def _generate_condition(self, text: str, entities: List[Entity]) -> str:
        """Generate IF condition code."""
        identifiers = self._get_identifiers(entities)
        numbers = self._get_numbers(entities)

        if identifiers:
            condition = f"{identifiers[0]} is equal to value"
        elif numbers:
            condition = f"value is equal to {numbers[0]}"
        else:
            condition = "value is true"

        return f"if {condition}\n  show true\nelse\n  show false"

    def _generate_function_definition(self, text: str, entities: List[Entity]) -> str:
        """Generate DEFINE function code."""
        identifiers = self._get_identifiers(entities)

        func_name = identifiers[0] if identifiers else "my_function"
        params = " ".join(identifiers[1:3]) if len(identifiers) > 1 else ""

        if params:
            return f"define {func_name} taking {params}\n  show value"
        else:
            return f"define {func_name}\n  show value"

    def _generate_function_call(self, text: str, entities: List[Entity]) -> str:
        """Generate function call code."""
        identifiers = self._get_identifiers(entities)

        if identifiers:
            func_name = identifiers[0]
            args = " and ".join(identifiers[1:]) if len(identifiers) > 1 else ""
            if args:
                return f"call {func_name} with {args}"
            else:
                return f"call {func_name}"
        else:
            return "call function"

    def _generate_generic(self, text: str, entities: List[Entity]) -> str:
        """Generate generic code when intent is unclear."""
        identifiers = self._get_identifiers(entities)

        # Default: try to generate variable assignment
        if identifiers:
            if len(identifiers) >= 2:
                return f"set {identifiers[0]} to {identifiers[1]}"
            else:
                return f"set {identifiers[0]} to 0"
        else:
            return "# Generated code: " + text

    def batch_generate(self, texts: List[str], 
                      target_language: str = "null") -> List[GeneratedCode]:
        """
        Generate code for multiple inputs.

        Args:
            texts: List of natural language descriptions
            target_language: Target language

        Returns:
            List of GeneratedCode objects
        """
        return [self.generate(text, target_language) for text in texts]

    def generate_with_context(self, text: str, context: Dict[str, str],
                             target_language: str = "null") -> GeneratedCode:
        """
        Generate code with additional context.

        Args:
            text: Natural language description
            context: Dictionary with context variables
            target_language: Target language

        Returns:
            GeneratedCode object
        """
        # For now, just use regular generation
        # In a real implementation, context could influence code generation
        return self.generate(text, target_language)

    def parse_natural_language_code(self, description: str) -> List[str]:
        """
        Parse a multi-line natural language description into code statements.

        Args:
            description: Multi-line natural language description

        Returns:
            List of generated code statements
        """
        statements = []
        for line in description.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                result = self.generate(line)
                if result.generated_code:
                    statements.append(result.generated_code)

        return statements
