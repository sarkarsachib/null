# Null NLP Engine Documentation

The Null NLP Engine provides comprehensive natural language processing capabilities for the Null-Lang programming language. It enables users to write programs using natural language, which is then automatically converted to executable Null code.

## Architecture Overview

The NLP engine consists of several interconnected components:

```
┌─────────────────────────────────────────────────────────┐
│                    NLP Pipeline                          │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────┐  ┌────────────┐  ┌──────────┐             │
│  │Tokenizer │─→│Intent Detect│─→│Entities  │             │
│  └──────────┘  └────────────┘  └──────────┘             │
│                                        │                 │
│                ┌───────────────────────┘                 │
│                │                                         │
│        ┌───────▼──────────┐  ┌──────────────┐            │
│        │ Code Generator   │◄─│Translation   │            │
│        └────────┬─────────┘  └──────────────┘            │
│                 │                                        │
│        ┌────────▼──────────┐                             │
│        │Context Manager    │                             │
│        └───────────────────┘                             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Tokenizer

Multilingual tokenization with support for English, Chinese, and Spanish.

```python
from null_system.nlp import Tokenizer

tokenizer = Tokenizer(language="en")
tokens = tokenizer.tokenize("set x to 5")

for token in tokens:
    print(f"{token.text}: {token.token_type.value}")
```

**Features:**
- Unicode normalization (NFC)
- CJK character handling
- Language auto-detection
- Token type classification
- Vocabulary extraction

**Performance:** <10ms for typical sentences

### 2. Intent Detector

Identifies the user's intent from natural language input.

```python
from null_system.nlp import IntentDetector

detector = IntentDetector()
intent = detector.get_primary_intent("set x to 5")

print(f"Intent: {intent.name}")
print(f"Confidence: {intent.confidence:.2%}")
```

**Supported Intents:**
- `SET_VARIABLE`: Variable assignment
- `CALCULATE`: Arithmetic operations
- `DISPLAY`: Output/display operations
- `LOOP`: Repetition/iteration
- `CONDITION`: Conditional logic
- `DEFINE_FUNCTION`: Function definitions
- `CALL_FUNCTION`: Function invocation
- `CODE_GENERATION`: Code generation requests

**Performance:** <10ms per detection

### 3. Entity Extractor

Identifies and classifies entities in the text.

```python
from null_system.nlp import EntityExtractor, EntityType

extractor = EntityExtractor()
entities = extractor.extract("set x to 42")

for entity in entities:
    print(f"{entity.text}: {entity.entity_type.value}")
```

**Entity Types:**
- `VARIABLE`: Variable names
- `NUMBER`: Numeric literals
- `STRING`: String literals
- `OPERATOR`: Operators
- `KEYWORD`: Language keywords
- `IDENTIFIER`: Generic identifiers

**Performance:** <10ms per extraction

### 4. Embeddings Model

Super-Bit compatible semantic embeddings for similarity calculations.

```python
from null_system.nlp import EmbeddingModel

embeddings = EmbeddingModel(dimension=128)
emb1 = embeddings.embed("set variable")
emb2 = embeddings.embed("assign value")

similarity = embeddings.semantic_similarity("set", "assign")
print(f"Similarity: {similarity:.2%}")
```

### 5. Translator

Multilingual translation between English, Spanish, and Chinese.

```python
from null_system.nlp import Translator

translator = Translator()
result = translator.translate("set", "en", "es")

print(f"Translation: {result.target_text}")
print(f"Confidence: {result.confidence:.2%}")
```

**Supported Language Pairs:**
- English ↔ Spanish (es)
- English ↔ Chinese (zh)

**Performance:** <5ms per word

### 6. Code Generator

Converts natural language to executable Null code.

```python
from null_system.nlp import CodeGenerator

codegen = CodeGenerator()
result = codegen.generate("set x to 5", target_language="null")

print(result.generated_code)
print(f"Intent: {result.intent.name}")
print(f"Confidence: {result.confidence:.2%}")
```

**Supported Target Languages:**
- `null`: Null-Lang code
- `python`: Python code

**Performance:** <20ms per generation

### 7. Context Manager

Maintains state and history across multiple NLP interactions.

```python
from null_system.nlp import ContextManager

context = ContextManager()
context.set_variable("x", 5)
context.add_function("my_func", "def my_func(): pass")

# Retrieve values
x_val = context.get_variable("x")
```

**Features:**
- Variable tracking
- Function registration
- Import management
- Conversation history
- Embedding-based history search
- Context frames for scoping

### 8. NLP Pipeline

Complete end-to-end pipeline coordinating all components.

```python
from null_system.nlp import NLPPipeline

pipeline = NLPPipeline(language="auto", enable_translation=True)
result = pipeline.process("set x to 5")

print(f"Generated code: {result.generated_code.generated_code}")
print(f"Total latency: {result.metrics.total_time_ms:.2f} ms")
```

## CLI Usage

### Tokenization

```bash
nullc nlp tokenize "set x to 5"
nullc nlp tokenize "set x to 5" --language en
```

### Translation

```bash
nullc nlp translate "set" --target es
nullc nlp translate "你好" --target en
```

### Code Generation

```bash
nullc nlp codegen "set x to 5"
nullc nlp codegen "set x to 5" --language python
nullc nlp codegen "set x to 5" --details
```

## Library Functions

The NLP engine exposes five main functions through the Null library registry:

### nlp.TOKENIZE

```null
TOKENIZE "set x to 5"
```

Returns an array of tokens.

### nlp.INTENT

```null
INTENT "set x to 5"
```

Returns an object with intent name and confidence.

### nlp.ENTITIES

```null
ENTITIES "set x to 5"
```

Returns an array of extracted entities.

### nlp.TRANSLATE

```null
TRANSLATE "set" "es"
```

Translates text to the target language.

### nlp.CODEGEN

```null
CODEGEN "set x to 5" "null"
```

Generates code from natural language.

## Performance Characteristics

### Latency Targets

| Operation | Target | Typical |
|-----------|--------|---------|
| Tokenization | <10ms | 2-5ms |
| Intent Detection | <10ms | 3-7ms |
| Entity Extraction | <10ms | 3-8ms |
| Translation | <5ms per word | 1-3ms |
| Code Generation | <20ms | 5-15ms |
| Full Pipeline | <50ms | 15-30ms |

### Accuracy Metrics

| Component | Threshold | Target |
|-----------|-----------|--------|
| Intent Detection | 0.5+ confidence | >80% |
| Entity Extraction | Matched position | >85% |
| Code Generation | Valid Null syntax | 100% |
| Translation | Vocabulary coverage | >70% |

## Example Use Cases

### 1. Interactive Shell

```python
from null_system.nlp import NLPPipeline

pipeline = NLPPipeline(language="auto")

while True:
    user_input = input("null> ")
    result = pipeline.process(user_input)
    
    if result.success:
        print(f"Code: {result.generated_code.generated_code}")
        print(f"Latency: {result.metrics.total_time_ms:.2f} ms")
    else:
        print(f"Error: {result.error}")
```

### 2. Batch Code Generation

```python
from null_system.nlp import NLPPipeline

pipeline = NLPPipeline()
descriptions = [
    "set x to 5",
    "show x",
    "add x and 10"
]

results = pipeline.batch_process(descriptions)
report = pipeline.get_performance_report(results)

print(f"Success rate: {report['success_rate']:.2%}")
print(f"Avg latency: {report['avg_latency_ms']:.2f} ms")
```

### 3. Multilingual Support

```python
from null_system.nlp import CodeGenerator

# Spanish
codegen_es = CodeGenerator(language="es")
result = codegen_es.generate("establecer x a 5")
print(result.generated_code)

# Chinese
codegen_zh = CodeGenerator(language="zh")
result = codegen_zh.generate("设置 x 为 5")
print(result.generated_code)
```

### 4. Intent-Driven Routing

```python
from null_system.nlp import IntentDetector

detector = IntentDetector()
intent = detector.get_primary_intent(user_input)

if intent.name == "CALCULATE":
    # Handle calculation
    pass
elif intent.name == "DISPLAY":
    # Handle display
    pass
elif intent.name == "SET_VARIABLE":
    # Handle assignment
    pass
```

## Error Handling

### Common Issues

**1. Language Detection Failure**
```python
# Explicitly specify language
tokenizer = Tokenizer(language="zh")  # Don't use "auto"
```

**2. Low Confidence Scores**
```python
result = pipeline.process(text)
if result.generated_code.confidence < 0.5:
    # Request clarification or manual input
```

**3. Unsupported Translation Pair**
```python
if not translator.can_translate("en", "ja"):
    # Fall back to English
```

## Configuration

### Pipeline Configuration

```python
from null_system.nlp import NLPPipeline

pipeline = NLPPipeline(
    language="auto",           # Input language
    enable_translation=True     # Enable translation
)
```

### Embedding Model Configuration

```python
from null_system.nlp import EmbeddingModel

embeddings = EmbeddingModel(
    dimension=128,            # Embedding dimension
    seed=42                   # Random seed
)
```

### Context Manager Configuration

```python
from null_system.nlp import ContextManager

context = ContextManager(
    max_history=50           # Maximum history entries
)
```

## Cross-Domain Integration

### With Compiler

```python
from null_system.nlp import NLPPipeline
from null_system.compiler import NullCompiler

pipeline = NLPPipeline()
compiler = NullCompiler()

# Generate code from natural language
result = pipeline.process("set x to 5 show x")

# Compile generated code
artifact = compiler.compile(result.generated_code.generated_code)
```

### With Optimizer

```python
from null_system.nlp import NLPPipeline
from null_system.compiler.optimization import DeduplicationPass

pipeline = NLPPipeline()

result = pipeline.process("set x to 5")
generated_code = result.generated_code.generated_code

# Pass to optimizer
optimizer = DeduplicationPass()
# ... optimization pipeline
```

## Benchmarking

Run performance benchmarks:

```bash
python tests/nlp/benchmark_nlp.py
```

Expected output:
```
Tokenizer:         ~5ms
Intent Detection:  ~7ms
Entity Extraction: ~8ms
Translation:       ~2ms
Code Generation:  ~15ms
────────────────────
Total Pipeline:   ~37ms
```

## Advanced Features

### Custom Intent Templates

```python
detector = IntentDetector()
detector.add_intent_template("CUSTOM", ["custom", "action"])
```

### Custom Entity Mappings

```python
extractor = EntityExtractor()
extractor.add_custom_entity("myvar", EntityType.VARIABLE)
```

### Custom Translation Pairs

```python
translator = Translator()
translator.add_translation_pair("en", "es", "myword", "mipalabra")
```

### Context-Aware Generation

```python
codegen = CodeGenerator()
context = {"x": "5", "y": "10"}
result = codegen.generate_with_context("show x plus y", context)
```

## Limitations and Future Improvements

### Current Limitations

1. **Translation Coverage**: Limited to vocabulary in translation tables
2. **Complex Expressions**: May not handle deeply nested expressions
3. **Semantic Understanding**: Limited semantic analysis beyond keywords
4. **Multi-line Handling**: Single-sentence focus

### Planned Improvements

1. Integration with transformer-based models for better semantics
2. Improved parsing for complex natural language
3. Multi-sentence and multi-turn conversation support
4. Extended language support
5. Custom domain-specific vocabulary training

## Contributing

To extend the NLP engine:

1. Add new intent templates in `IntentDetector.intent_templates`
2. Add new entity types in `EntityType` enum
3. Add translation pairs to translator tables
4. Add code generation patterns in `CodeGenerator`

## References

- [Null-Lang Grammar](../src/null_system/lang/grammar.lark)
- [Null-Lang Parser](../src/null_system/lang/parser.py)
- [Compiler Documentation](architecture.md)
