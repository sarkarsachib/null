/**
 * Example: Multilingual NLP and Knowledge Graph Reasoning
 * Demonstrates tokenization, embedding, translation, and semantic queries
 */

import { NullVM } from '../src/null_system/vm/null_vm';
import { OpCode, Instruction } from '../src/null_system/vm/instructions';
import { Tokenizer } from '../src/null_system/vm/nlp/tokenizer';
import { Embedder } from '../src/null_system/vm/nlp/embedder';
import { CodegenAdapter } from '../src/null_system/vm/nlp/codegen_adapter';
import { GraphStore, Entity } from '../src/null_system/vm/knowledge/graph_store';
import { OntologyManager } from '../src/null_system/vm/knowledge/ontology_manager';
import { InferenceEngine } from '../src/null_system/vm/knowledge/inference_engine';
import { RDFLoader } from '../src/null_system/vm/knowledge/rdf_loader';

async function main() {
  console.log('=== NLP & Knowledge Graph Integration Example ===\n');

  // Part 1: Tokenization and Embeddings
  console.log('1. Multilingual Tokenization and Embeddings');
  console.log('----------------------------------------');

  const tokenizer = new Tokenizer();
  const embedder = new Embedder(128);

  const texts = {
    en: 'Knowledge graphs enable semantic reasoning',
    es: 'Los gráficos de conocimiento permiten razonamiento semántico',
    fr: 'Les graphes de connaissance permettent le raisonnement sémantique',
    de: 'Wissensgraphen ermöglichen semantisches Denken',
  };

  for (const [lang, text] of Object.entries(texts)) {
    const tokens = tokenizer.tokenize(text, {
      language: lang,
      lowercase: true,
      removeStopwords: false,
    });

    console.log(`\n${lang.toUpperCase()}: "${text}"`);
    console.log(`  Tokens: ${tokens.length}`);
    console.log(`  First 3 tokens: ${tokens
      .slice(0, 3)
      .map(t => t.text)
      .join(', ')}`);

    // Generate embedding for first token
    if (tokens.length > 0) {
      const embedding = embedder.embed(tokens[0].text, lang);
      console.log(
        `  Embedding dimension: ${embedding.tensor.dimensions}, confidence: ${embedding.confidence}`
      );
    }
  }

  // Part 2: Translation Pipeline
  console.log('\n\n2. Translation Pipeline');
  console.log('---------------------');

  const sourceTexts = ['hello', 'knowledge', 'graph', 'reason'];
  const targetLanguages = ['es', 'fr', 'de'];

  for (const text of sourceTexts) {
    console.log(`\n"${text}" (en):`);
    for (const lang of targetLanguages) {
      const translated = embedder.translate(text, 'en', lang);
      console.log(`  → ${lang}: "${translated.translatedText}" (confidence: ${translated.confidence})`);
    }
  }

  // Part 3: Code Generation from Embeddings
  console.log('\n\n3. Code Generation from Embeddings');
  console.log('----------------------------------');

  const codegenTexts = ['process', 'query', 'analyze'];
  const codegenEmbeddings = codegenTexts.map(t => embedder.embed(t, 'en').tensor);

  const codegen = new CodegenAdapter();

  for (const lang of ['typescript', 'python']) {
    const generated = codegen.generateCode({
      embeddings: codegenEmbeddings,
      targetLanguage: lang,
    });

    console.log(`\n${lang.toUpperCase()} Code:`);
    console.log(generated.code.split('\n').slice(0, 5).join('\n'));
    console.log('  ...');
  }

  // Part 4: Knowledge Graph Construction
  console.log('\n\n4. Knowledge Graph Construction');
  console.log('------------------------------');

  const graph = new GraphStore();
  const onto = new OntologyManager();

  onto.defineEntityType({
    name: 'Concept',
    properties: {
      label: { type: 'string', required: true },
      description: { type: 'string' },
    },
  });

  onto.defineEntityType({
    name: 'Person',
    parent: 'Concept',
    properties: {
      name: { type: 'string' },
      expertise: { type: 'string' },
    },
  });

  onto.defineRelationshipType({
    name: 'understands',
    sourceType: 'Person',
    targetType: 'Concept',
  });

  onto.defineRelationshipType({
    name: 'relatedTo',
    sourceType: 'Concept',
    targetType: 'Concept',
  });

  // Add entities
  const concepts = [
    { id: 'nlp', label: 'Natural Language Processing', description: 'Processing human language' },
    { id: 'kg', label: 'Knowledge Graph', description: 'Semantic data structure' },
    { id: 'reasoning', label: 'Semantic Reasoning', description: 'Inference over knowledge' },
    { id: 'embedding', label: 'Embeddings', description: 'Vector representations' },
  ];

  for (const concept of concepts) {
    graph.addEntity({
      id: concept.id,
      label: concept.label,
      type: 'Concept',
      properties: concept,
    });
  }

  // Add relationships
  graph.addRelationship('nlp', 'embedding', 'relatedTo', { weight: 0.9 });
  graph.addRelationship('kg', 'reasoning', 'relatedTo', { weight: 0.95 });
  graph.addRelationship('nlp', 'kg', 'relatedTo', { weight: 0.8 });
  graph.addRelationship('embedding', 'reasoning', 'relatedTo', { weight: 0.85 });

  console.log(`\nGraph Statistics:`);
  const stats = graph.getStats();
  console.log(`  Entities: ${stats.entityCount}`);
  console.log(`  Relationships: ${stats.relationshipCount}`);
  console.log(`  Entity Types: ${stats.typeCount}`);

  // Find paths
  const path = graph.findPath('nlp', 'reasoning');
  if (path) {
    console.log(`\nPath from NLP to Reasoning:`);
    for (const rel of path) {
      const source = graph.getEntity(rel.source);
      const target = graph.getEntity(rel.target);
      console.log(`  ${source?.label} --${rel.type}--> ${target?.label}`);
    }
  }

  // Part 5: Inference Engine
  console.log('\n\n5. Rule-Based Inference');
  console.log('---------------------');

  const engine = new InferenceEngine();

  engine.addRule({
    name: 'concept_related_implies_similar',
    condition: [
      { type: 'relationship', relationshipType: 'relatedTo' },
    ],
    conclusion: {
      type: 'set_property',
      property: 'isSimilar',
      value: true,
    },
  });

  engine.addRule({
    name: 'multiple_relations_implies_core',
    condition: [
      { type: 'entity', entityType: 'Concept' },
    ],
    conclusion: {
      type: 'set_property',
      property: 'isConcept',
      value: true,
    },
  });

  console.log(`\nRules defined: ${engine.getAllRules().length}`);

  const inferenceResults = engine.forwardChain(graph, 5);
  console.log(`Inference results: ${inferenceResults.length}`);

  for (const result of inferenceResults.slice(0, 3)) {
    console.log(`  Rule: ${result.ruleId}, Confidence: ${(result.confidence * 100).toFixed(0)}%`);
  }

  // Part 6: RDF/JSON-LD Import/Export
  console.log('\n\n6. RDF/JSON-LD Operations');
  console.log('-----------------------');

  const loader = new RDFLoader();

  const jsonLdData = {
    '@context': {
      '@vocab': 'http://schema.org/',
      'schema': 'http://schema.org/',
    },
    '@graph': [
      {
        '@id': 'http://example.com/ai',
        '@type': 'Concept',
        'schema:name': 'Artificial Intelligence',
        'schema:description': 'Machine learning and automation',
      },
      {
        '@id': 'http://example.com/ml',
        '@type': 'Concept',
        'schema:name': 'Machine Learning',
        'schema:description': 'Learning from data',
      },
    ],
  };

  const importedGraph = new GraphStore();
  loader.loadJsonLd(jsonLdData, importedGraph);

  console.log(`\nImported graph statistics:`);
  const importedStats = importedGraph.getStats();
  console.log(`  Entities: ${importedStats.entityCount}`);
  console.log(`  Relationships: ${importedStats.relationshipCount}`);

  const exportedJsonLd = loader.exportAsJsonLd(graph);
  console.log(`\nExported graph to JSON-LD`);
  console.log(`  Nodes: ${(exportedJsonLd['@graph'] as unknown[])?.length || 0}`);

  // Part 7: VM Execution
  console.log('\n\n7. VM Execution with NLP/KG Operations');
  console.log('------------------------------------');

  const vm = new NullVM({ enableTracing: false });

  const program: Instruction[] = [
    // Tokenization
    { opcode: OpCode.SET, args: ['text_input', 42] },
    { opcode: OpCode.NLP_TOKENIZE, args: ['text_input', 'token_count'] },

    // Embedding
    { opcode: OpCode.NLP_EMBED, args: ['text_input', 'embedding_result'] },

    // Translation
    { opcode: OpCode.NLP_TRANSLATE, args: ['text_input', 'es', 'translated'] },

    // Knowledge Graph Load
    {
      opcode: OpCode.KG_LOAD,
      args: [{ entities: concepts, relationships: [] }, 'graph_id'],
    },

    // Query Knowledge Graph
    { opcode: OpCode.KG_QUERY, args: ['graph_id', 'token_count', 'query_result'] },

    // Inference
    { opcode: OpCode.KG_REASON, args: ['graph_id', 'embedding_result', 'reasoning_result'] },

    // Output results
    { opcode: OpCode.SHOW, args: ['token_count'] },
    { opcode: OpCode.SHOW, args: ['query_result'] },
    { opcode: OpCode.SHOW, args: ['reasoning_result'] },
  ];

  try {
    vm.execute(program);

    console.log('VM Execution Results:');
    console.log(`  Token Count: ${vm.getMemory().getRegister('token_count')}`);
    console.log(`  Query Result: ${vm.getMemory().getRegister('query_result')}`);
    console.log(`  Reasoning Result: ${vm.getMemory().getRegister('reasoning_result')}`);

    const frames = vm.getBinaryBridge().getFrames();
    console.log(`  Output Frames: ${frames.length}`);
  } catch (error) {
    console.error('VM Execution Error:', error);
  }

  // Summary
  console.log('\n\n=== Summary ===');
  console.log('✓ Multilingual tokenization and embeddings');
  console.log('✓ Text translation across languages');
  console.log('✓ Code generation from embeddings');
  console.log('✓ Knowledge graph construction and querying');
  console.log('✓ Rule-based semantic reasoning');
  console.log('✓ RDF/JSON-LD import/export');
  console.log('✓ VM integration with NLP/KG opcodes');
  console.log('\nAll examples completed successfully!');
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
