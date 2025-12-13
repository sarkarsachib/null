# NLP & Knowledge Graph System

## Overview

The NLP & Knowledge Graph system is an integrated subsystem of the Null-Lang VM that enables sophisticated semantic processing, knowledge representation, and probabilistic reasoning. It consists of two main components:

1. **NLP Module** - Natural Language Processing with multilingual support
2. **Knowledge Graph Module** - Semantic data structures and inference engines

Both components operate on `SuperBitTensor` abstractions for efficient vector representation and seamless integration with the VM's super-bit encoding layer.

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Null-Lang VM                            │
├─────────────────────────────────────────────────┤
│  NLP_TOKENIZE │ NLP_EMBED │ NLP_TRANSLATE       │
├─────────────────────────────────────────────────┤
│  KG_LOAD │ KG_QUERY │ KG_REASON                 │
├─────────────────────────────────────────────────┤
│ NLP Module          │ Knowledge Graph Module    │
│ ├─ Tokenizer        │ ├─ GraphStore            │
│ ├─ Embedder         │ ├─ OntologyManager       │
│ └─ CodegenAdapter   │ ├─ InferenceEngine       │
│                     │ └─ RDFLoader             │
└─────────────────────────────────────────────────┘
```

## NLP Module

### Tokenizer

Performs multilingual text tokenization with optional preprocessing.

#### Features
- **Multilingual Support**: English, Spanish, French, German, Chinese, Japanese, Korean, Arabic, Russian
- **Language Detection**: Automatic detection from text patterns
- **Stopword Removal**: Language-aware stopword filtering
- **Stemming**: Simple suffix-based word stemming
- **Language Statistics**: Analyze token distribution across languages

#### Usage

```typescript
import { Tokenizer } from './nlp/tokenizer';

const tokenizer = new Tokenizer();

// Basic tokenization
const tokens = tokenizer.tokenize('Hello world from NullVM');
// [{ text: 'hello', language: 'en' }, { text: 'world', language: 'en' }, ...]

// With options
const processedTokens = tokenizer.tokenize('The quick brown fox', {
  language: 'en',
  lowercase: true,
  removeStopwords: true,
  stemming: true,
});

// Language detection
const detectedLang = tokenizer.detectLanguage('你好世界');
// Returns: 'zh'

// Statistics
const stats = tokenizer.getLanguageStats(tokens);
// { totalTokens: 5, uniqueLanguages: 1, languageDistribution: { en: 5 } }
```

#### API

```typescript
interface TokenizeOptions {
  language?: string;        // Default: auto-detected
  lowercase?: boolean;      // Default: true
  removeStopwords?: boolean; // Default: false
  stemming?: boolean;       // Default: false
}

tokenize(text: string, options?: TokenizeOptions): Token[]
detectLanguage(text: string): string
getLanguageStats(tokens: Token[]): Record<string, unknown>
```

### Embedder

Generates semantic embeddings using super-bit tensor representation with translation support.

#### Features
- **Deterministic Embeddings**: Hash-based embeddings for reproducibility
- **Multilingual Translation**: Word/phrase translation across languages
- **Similarity Computation**: Cosine-like similarity between embeddings
- **Batch Operations**: Process multiple texts efficiently
- **Tensor Arithmetic**: Add and combine embeddings

#### Usage

```typescript
import { Embedder, SuperBitTensor } from './nlp/embedder';

const embedder = new Embedder(128);

// Generate embedding
const result = embedder.embed('hello world', 'en');
// {
//   tensor: { dimensions: 128, bits: Uint8Array(128), metadata: {...} },
//   confidence: 0.95,
//   language: 'en',
//   originalText: 'hello world'
// }

// Compute similarity
const emb1 = embedder.embed('hello', 'en').tensor;
const emb2 = embedder.embed('world', 'en').tensor;
const similarity = embedder.similarity(emb1, emb2);
// Returns: 0.0 to 1.0

// Translate text
const translated = embedder.translate('hello', 'en', 'es');
// { translatedText: 'hola', targetLanguage: 'es', confidence: 0.99 }

// Batch embed
const texts = ['hello', 'world', 'foo'];
const embeddings = embedder.batchEmbed(texts, 'en');

// Combine embeddings
const combined = embedder.add(emb1, emb2);
```

#### API

```typescript
interface SuperBitTensor {
  dimensions: number;
  bits: Uint8Array;
  metadata?: Record<string, unknown>;
}

interface EmbeddingResult {
  tensor: SuperBitTensor;
  confidence: number;
  language: string;
  originalText?: string;
}

embed(text: string, language?: string): EmbeddingResult
translate(text: string, sourceLanguage: string, targetLanguage: string): TranslationResult
similarity(embedding1: SuperBitTensor, embedding2: SuperBitTensor): number
batchEmbed(texts: string[], language?: string): EmbeddingResult[]
add(tensor1: SuperBitTensor, tensor2: SuperBitTensor): SuperBitTensor
zeroEmbedding(dimension?: number): SuperBitTensor
```

### CodegenAdapter

Generates executable code from embeddings and knowledge graph rules.

#### Features
- **Multi-Language Output**: TypeScript, Python, SQL code generation
- **Inference Function Generation**: Create executable rule engines
- **Code Transpilation**: Convert between programming languages

#### Usage

```typescript
import { CodegenAdapter } from './nlp/codegen_adapter';

const adapter = new CodegenAdapter();

// Generate code from embeddings
const embeddings = [
  embedder.embed('process', 'en').tensor,
  embedder.embed('query', 'en').tensor,
];

const result = adapter.generateCode({
  embeddings,
  targetLanguage: 'typescript',
});

console.log(result.code);
// const result = {
//   embedding_0: [128, 45, ...],
//   embedding_1: [200, 60, ...],
// };

// Generate inference function
const rules = [
  { condition: 'facts.animal', conclusion: 'facts.mammal' },
  { condition: 'facts.mammal', conclusion: 'facts.vertebrate' },
];

const inferenceCode = adapter.generateInferenceFunction(rules, 'typescript');

// Transpile code
const pythonCode = adapter.transpile(tsCode, 'typescript', 'python');
```

#### API

```typescript
interface CodeGenerationRequest {
  embeddings: SuperBitTensor[];
  targetLanguage?: string;
  context?: Record<string, unknown>;
}

generateCode(request: CodeGenerationRequest): GeneratedCode
generateInferenceFunction(rules: Rule[], language?: string): GeneratedCode
transpile(code: string, fromLanguage: string, toLanguage: string): GeneratedCode
```

## Knowledge Graph Module

### GraphStore

Manages knowledge graph entities, relationships, and semantic connections.

#### Features
- **Entity Management**: Add, retrieve, and index entities by type
- **Relationship Tracking**: Directed relationships with properties
- **Path Finding**: Breadth-first search for semantic paths
- **RDF Conversion**: Export to RDF triple format
- **Graph Statistics**: Analyze graph structure and properties

#### Usage

```typescript
import { GraphStore, Entity } from './knowledge/graph_store';

const graph = new GraphStore();

// Add entities
graph.addEntity({
  id: 'person_alice',
  label: 'Alice',
  type: 'Person',
  properties: { age: 30, city: 'NYC' },
});

graph.addEntity({
  id: 'person_bob',
  label: 'Bob',
  type: 'Person',
  properties: { age: 25, city: 'LA' },
});

// Add relationships
const relId = graph.addRelationship('person_alice', 'person_bob', 'knows', {
  since: 2020,
});

// Query entities
const alice = graph.getEntity('person_alice');
const people = graph.getEntitiesByType('Person');

// Find relationships
const knows = graph.getOutgoingRelationships('person_alice');
const knownBy = graph.getIncomingRelationships('person_bob');

// Get neighbors
const aliceNeighbors = graph.getNeighbors('person_alice');

// Find paths
const path = graph.findPath('person_alice', 'person_bob', 3);

// Export as RDF
const triples = graph.toTriples();
// [
//   { subject: 'person_alice', predicate: 'age', object: '30' },
//   { subject: 'person_alice', predicate: 'knows', object: 'person_bob' },
//   ...
// ]

// Statistics
const stats = graph.getStats();
// { entityCount: 2, relationshipCount: 1, typeCount: 1, ... }
```

#### API

```typescript
interface Entity {
  id: string;
  label: string;
  type: string;
  properties: Record<string, unknown>;
  embedding?: SuperBitTensor;
}

interface Relationship {
  id: string;
  source: string;
  target: string;
  type: string;
  weight?: number;
  properties: Record<string, unknown>;
}

addEntity(entity: Entity): void
getEntity(id: string): Entity | undefined
getEntitiesByType(type: string): Entity[]
addRelationship(source: string, target: string, type: string, properties?: Record<string, unknown>): string
getRelationship(id: string): Relationship | undefined
getOutgoingRelationships(entityId: string, type?: string): Relationship[]
getIncomingRelationships(entityId: string, type?: string): Relationship[]
getNeighbors(entityId: string): Entity[]
findPath(sourceId: string, targetId: string, maxDepth?: number): Relationship[] | null
toTriples(): Triple[]
getStats(): Record<string, unknown>
clear(): void
```

### OntologyManager

Manages entity types, relationship types, and schema constraints.

#### Features
- **Schema Definition**: Define entity and relationship types
- **Validation**: Validate data against schema
- **Type Hierarchy**: Support parent-child type relationships
- **Constraints**: Define domain, range, and cardinality constraints
- **JSON-LD Export**: Export ontology as semantic web standard

#### Usage

```typescript
import { OntologyManager } from './knowledge/ontology_manager';

const onto = new OntologyManager();

// Define entity type
onto.defineEntityType({
  name: 'Person',
  properties: {
    name: { type: 'string', required: true },
    age: { type: 'number' },
    email: { type: 'string' },
  },
  description: 'A human person',
});

// Define relationship type
onto.defineRelationshipType({
  name: 'knows',
  sourceType: 'Person',
  targetType: 'Person',
  description: 'Acquaintance relationship',
});

// Validate entity
const validation = onto.validateEntity('Person', { name: 'Alice', age: 30 });
if (!validation.valid) {
  console.error('Validation errors:', validation.errors);
}

// Type hierarchy
onto.defineEntityType({
  name: 'Student',
  parent: 'Person',
  properties: {
    schoolId: { type: 'string' },
  },
});

const hierarchy = onto.getHierarchy('Student');
// Returns: [Student, Person]

// Export ontology
const jsonLd = onto.exportAsJsonLd();
```

#### API

```typescript
interface EntityType {
  name: string;
  parent?: string;
  properties: Record<string, PropertyDefinition>;
  description?: string;
}

interface PropertyDefinition {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  required?: boolean;
  description?: string;
  default?: unknown;
}

defineEntityType(entityType: EntityType): void
getEntityType(name: string): EntityType | undefined
hasEntityType(name: string): boolean
defineRelationshipType(relType: RelationshipType): void
getRelationshipType(name: string): RelationshipType | undefined
hasRelationshipType(name: string): boolean
validateEntity(entityType: string, properties: Record<string, unknown>): ValidationResult
getHierarchy(entityType: string): EntityType[]
getSubtypes(entityType: string): EntityType[]
exportAsJsonLd(): Record<string, unknown>
```

### InferenceEngine

Executes forward chaining, backward chaining, and rule-based inference over knowledge graphs.

#### Features
- **Forward Chaining**: Data-driven inference
- **Backward Chaining**: Goal-driven inference
- **Rule Management**: Add and track inference rules
- **Confidence Tracking**: Track inference confidence scores
- **History**: Maintain complete inference history

#### Usage

```typescript
import { InferenceEngine } from './knowledge/inference_engine';

const engine = new InferenceEngine();

// Define rules
const ruleId = engine.addRule({
  name: 'all_animals_are_living',
  condition: [
    { type: 'entity', entityType: 'Animal' }
  ],
  conclusion: {
    type: 'set_property',
    property: 'isLiving',
    value: true,
  },
  weight: 0.95,
});

// Forward chaining (data-driven)
const forwardResults = engine.forwardChain(graph, 10);
// Iteratively applies rules until no new facts are inferred

// Backward chaining (goal-driven)
const backwardResults = engine.backwardChain(graph, {
  entityType: 'Living',
});

// Get inference history
const history = engine.getInferenceHistory();
```

#### API

```typescript
interface Rule {
  id: string;
  name: string;
  condition: RuleCondition[];
  conclusion: RuleConclusion;
  weight?: number;
}

interface RuleCondition {
  type: 'entity' | 'relationship' | 'property';
  entityType?: string;
  relationshipType?: string;
  property?: string;
  value?: unknown;
  operator?: string;
}

interface RuleConclusion {
  type: 'assert_entity' | 'assert_relationship' | 'set_property';
  entityType?: string;
  relationshipType?: string;
  property?: string;
  value?: unknown;
}

addRule(rule: Omit<Rule, 'id'>): string
getRule(id: string): Rule | undefined
getAllRules(): Rule[]
forwardChain(graph: GraphStore, iterations?: number): InferenceResult[]
backwardChain(graph: GraphStore, goal: QueryGoal): InferenceResult[]
getInferenceHistory(): InferenceResult[]
clear(): void
```

### RDFLoader

Loads and exports knowledge graphs in RDF and JSON-LD formats.

#### Features
- **RDF Triple Loading**: Import from RDF format
- **JSON-LD Support**: Load and export JSON-LD documents
- **RDF Object Parsing**: Parse RDF/XML-style objects
- **Format Conversion**: Convert between RDF and JSON-LD
- **Embedding Generation**: Create embeddings from graph entities

#### Usage

```typescript
import { RDFLoader } from './knowledge/rdf_loader';

const loader = new RDFLoader();
const graph = new GraphStore();

// Load RDF triples
const triples = [
  { subject: 'http://example.com/alice', predicate: 'http://schema.org/name', object: 'Alice' },
  { subject: 'http://example.com/alice', predicate: 'http://schema.org/age', object: '30' },
  { subject: 'http://example.com/bob', predicate: 'http://schema.org/name', object: 'Bob' },
];
loader.loadTriples(triples, graph);

// Load JSON-LD
const jsonLd = {
  '@context': { '@vocab': 'http://schema.org/' },
  '@graph': [
    {
      '@id': 'http://example.com/person1',
      '@type': 'Person',
      name: 'Alice',
      age: 30,
    },
  ],
};
loader.loadJsonLd(jsonLd, graph);

// Export to RDF
const exportedTriples = loader.exportAsTriples(graph);

// Export to JSON-LD
const exportedJsonLd = loader.exportAsJsonLd(graph);

// Create embeddings from graph
const embeddings = loader.createEmbeddingsFromGraph(graph, 128);
```

#### API

```typescript
interface RDFTripleFormat {
  subject: string;
  predicate: string;
  object: string;
}

interface JsonLdDocument {
  '@context'?: Record<string, unknown> | string[];
  '@graph'?: Array<Record<string, unknown>>;
  [key: string]: unknown;
}

loadTriples(triples: RDFTripleFormat[], graph: GraphStore): void
loadJsonLd(doc: JsonLdDocument, graph: GraphStore): void
loadRdfObject(rdfObj: Record<string, unknown>, graph: GraphStore): void
exportAsTriples(graph: GraphStore): Triple[]
exportAsJsonLd(graph: GraphStore): JsonLdDocument
createEmbeddingsFromGraph(graph: GraphStore, dimension?: number): Map<string, SuperBitTensor>
```

## VM Opcodes

### NLP Operations

#### NLP_TOKENIZE
Tokenizes text in a register and stores token count.

```
NLP_TOKENIZE input_register output_register
```

- **Args**: 
  - `input_register`: Register containing input value
  - `output_register`: Register to store token count
- **Effects**: Stores token count in output register
- **Example**:
  ```
  SET text 100
  NLP_TOKENIZE text tokens
  SHOW tokens
  ```

#### NLP_EMBED
Generates embeddings for text and stores result flag.

```
NLP_EMBED input_register output_register
```

- **Args**:
  - `input_register`: Register containing input value
  - `output_register`: Register to store success flag (1)
- **Effects**: Creates super-bit tensor in memory, stores success flag
- **Example**:
  ```
  SET text 42
  NLP_EMBED text result
  ```

#### NLP_TRANSLATE
Translates text to target language.

```
NLP_TRANSLATE input_register target_language output_register
```

- **Args**:
  - `input_register`: Register containing input value
  - `target_language`: Target language code (es, fr, de, zh, etc.)
  - `output_register`: Register to store translated value
- **Effects**: Stores language-encoded value in output register
- **Example**:
  ```
  SET hello 10
  NLP_TRANSLATE hello es translated
  SHOW translated
  ```

### Knowledge Graph Operations

#### KG_LOAD
Loads a knowledge graph from data.

```
KG_LOAD graph_data graph_id_register
```

- **Args**:
  - `graph_data`: Graph data (entities, relationships)
  - `graph_id_register`: Register to store graph ID (success flag: 1)
- **Effects**: Stores graph in memory, returns success flag
- **Example**:
  ```
  KG_LOAD { entities: [], relationships: [] } kg_id
  ```

#### KG_QUERY
Queries a knowledge graph.

```
KG_QUERY graph_id_register query_register result_register
```

- **Args**:
  - `graph_id_register`: Register containing graph ID
  - `query_register`: Register containing query value
  - `result_register`: Register to store query result
- **Effects**: Executes query, stores result value
- **Example**:
  ```
  SET kg_id 5
  SET query 10
  KG_QUERY kg_id query result
  SHOW result
  ```

#### KG_REASON
Performs rule-based inference over a knowledge graph.

```
KG_REASON graph_id_register rule_data_register result_register
```

- **Args**:
  - `graph_id_register`: Register containing graph ID
  - `rule_data_register`: Register containing rule data
  - `result_register`: Register to store inference result
- **Effects**: Executes inference, stores result value
- **Example**:
  ```
  SET kg_id 5
  SET rules 3
  KG_REASON kg_id rules inferred
  SHOW inferred
  ```

## Integration Examples

### Complete Multilingual Pipeline

```typescript
const program: Instruction[] = [
  // Input text
  { opcode: OpCode.SET, args: ['input', 50] },
  
  // Tokenize
  { opcode: OpCode.NLP_TOKENIZE, args: ['input', 'tokens'] },
  
  // Embed
  { opcode: OpCode.NLP_EMBED, args: ['input', 'embedding'] },
  
  // Translate to Spanish
  { opcode: OpCode.NLP_TRANSLATE, args: ['input', 'es', 'spanish'] },
  
  // Load knowledge graph
  { opcode: OpCode.KG_LOAD, args: [graphData, 'kg'] },
  
  // Query knowledge graph
  { opcode: OpCode.KG_QUERY, args: ['kg', 'tokens', 'answer'] },
  
  // Perform inference
  { opcode: OpCode.KG_REASON, args: ['kg', 'embedding', 'conclusion'] },
  
  // Output results
  { opcode: OpCode.SHOW, args: ['answer'] },
  { opcode: OpCode.SHOW, args: ['conclusion'] },
];

const vm = new NullVM();
vm.execute(program);
```

### Knowledge Graph Construction and Reasoning

```typescript
const graph = new GraphStore();
const onto = new OntologyManager();
const engine = new InferenceEngine();

// Define schema
onto.defineEntityType({
  name: 'Concept',
  properties: { label: { type: 'string' } },
});

onto.defineRelationshipType({
  name: 'relatedTo',
  sourceType: 'Concept',
  targetType: 'Concept',
});

// Build graph
graph.addEntity({ id: 'nlp', label: 'NLP', type: 'Concept', properties: {} });
graph.addEntity({ id: 'kg', label: 'KG', type: 'Concept', properties: {} });
graph.addRelationship('nlp', 'kg', 'relatedTo');

// Define inference rules
engine.addRule({
  name: 'related_implies_connected',
  condition: [{ type: 'relationship', relationshipType: 'relatedTo' }],
  conclusion: {
    type: 'set_property',
    property: 'connected',
    value: true,
  },
});

// Execute inference
const results = engine.forwardChain(graph, 5);
```

## Performance Considerations

1. **Embedding Dimensions**: Larger dimensions provide better representation but slower computation
2. **Graph Size**: PathFinding is O(V + E) where V is vertices and E is edges
3. **Inference Iterations**: More iterations increase inference time but improve completeness
4. **Tokenization**: Language-aware tokenization is more accurate but slightly slower

## Best Practices

1. **Schema First**: Define ontology before building knowledge graphs
2. **Validation**: Always validate entities before adding to graph
3. **Incremental Inference**: Use limited iterations for real-time applications
4. **Embedding Caching**: Store computed embeddings to avoid recomputation
5. **Graph Size Management**: Clean up unused entities and relationships periodically
6. **Language Settings**: Specify language explicitly for better accuracy

## Limitations and Future Work

- Current embedding is hash-based; replace with ML model for production
- Translation uses basic dictionary; support sophisticated translation models
- Inference limited to rule-based; add probabilistic reasoning
- Graph storage in memory; add persistence layer for large graphs
- RDF support is basic; expand to full semantic web standards

## See Also

- [Architecture Documentation](./architecture.md)
- [README](../README.md)
- [Hybrid Runtime Guide](./hybrid_runtime.md)
