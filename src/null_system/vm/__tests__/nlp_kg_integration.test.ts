/**
 * Integration tests for NLP and Knowledge Graph systems
 */

import { NullVM } from '../null_vm';
import { OpCode, Instruction } from '../instructions';
import { Tokenizer } from '../nlp/tokenizer';
import { Embedder } from '../nlp/embedder';
import { CodegenAdapter } from '../nlp/codegen_adapter';
import { GraphStore, Entity } from '../knowledge/graph_store';
import { OntologyManager } from '../knowledge/ontology_manager';
import { InferenceEngine } from '../knowledge/inference_engine';
import { RDFLoader } from '../knowledge/rdf_loader';

describe('NLP and Knowledge Graph Integration', () => {
  let vm: NullVM;

  beforeEach(() => {
    vm = new NullVM();
  });

  describe('Tokenizer', () => {
    it('should tokenize English text', () => {
      const tokenizer = new Tokenizer();
      const tokens = tokenizer.tokenize('hello world from NullVM');

      expect(tokens.length).toBe(4);
      expect(tokens[0].text).toBe('hello');
      expect(tokens[1].text).toBe('world');
    });

    it('should detect language', () => {
      const tokenizer = new Tokenizer();

      expect(tokenizer.detectLanguage('hello world')).toBe('en');
      expect(tokenizer.detectLanguage('你好世界')).toBe('zh');
      expect(tokenizer.detectLanguage('مرحبا')).toBe('ar');
    });

    it('should remove stopwords', () => {
      const tokenizer = new Tokenizer();
      const tokens = tokenizer.tokenize('the quick brown fox is in the forest', {
        removeStopwords: true,
        lowercase: true,
      });

      const texts = tokens.map(t => t.text);
      expect(texts).toContain('quick');
      expect(texts).not.toContain('the');
      expect(texts).not.toContain('is');
    });

    it('should apply stemming', () => {
      const tokenizer = new Tokenizer();
      const tokens = tokenizer.tokenize('running runner run', { stemming: true, lowercase: true });

      const texts = tokens.map(t => t.text);
      expect(texts).toEqual(['runn', 'runner', 'run']);
    });

    it('should collect language statistics', () => {
      const tokenizer = new Tokenizer();
      const tokens = tokenizer.tokenize('hello world', { language: 'en' });
      const stats = tokenizer.getLanguageStats(tokens);

      expect(stats.totalTokens).toBe(2);
      expect(stats.uniqueLanguages).toBe(1);
    });
  });

  describe('Embedder', () => {
    it('should generate embeddings from text', () => {
      const embedder = new Embedder(64);
      const result = embedder.embed('hello world', 'en');

      expect(result.tensor.dimensions).toBe(64);
      expect(result.tensor.bits.length).toBe(64);
      expect(result.confidence).toBeGreaterThan(0);
      expect(result.language).toBe('en');
    });

    it('should be deterministic', () => {
      const embedder = new Embedder(64);
      const result1 = embedder.embed('hello', 'en');
      const result2 = embedder.embed('hello', 'en');

      const bits1 = Array.from(result1.tensor.bits);
      const bits2 = Array.from(result2.tensor.bits);

      expect(bits1).toEqual(bits2);
    });

    it('should compute similarity between embeddings', () => {
      const embedder = new Embedder(64);
      const emb1 = embedder.embed('hello', 'en').tensor;
      const emb2 = embedder.embed('hello', 'en').tensor;
      const emb3 = embedder.embed('world', 'en').tensor;

      const similarity12 = embedder.similarity(emb1, emb2);
      const similarity13 = embedder.similarity(emb1, emb3);

      expect(similarity12).toBe(1); // Same embedding
      expect(similarity13).toBeLessThan(1);
    });

    it('should translate text between languages', () => {
      const embedder = new Embedder();
      const result = embedder.translate('hello', 'en', 'es');

      expect(result.translatedText).toBe('hola');
      expect(result.targetLanguage).toBe('es');
      expect(result.confidence).toBeGreaterThan(0);
    });

    it('should batch embed texts', () => {
      const embedder = new Embedder(64);
      const texts = ['hello', 'world', 'foo'];
      const results = embedder.batchEmbed(texts, 'en');

      expect(results.length).toBe(3);
      expect(results[0].originalText).toBe('hello');
      expect(results[2].originalText).toBe('foo');
    });

    it('should add embeddings', () => {
      const embedder = new Embedder(64);
      const emb1 = embedder.embed('hello', 'en').tensor;
      const emb2 = embedder.embed('world', 'en').tensor;
      const sum = embedder.add(emb1, emb2);

      expect(sum.dimensions).toBe(64);
      expect(sum.bits.length).toBe(64);
    });
  });

  describe('Codegen Adapter', () => {
    it('should generate TypeScript code from embeddings', () => {
      const embedder = new Embedder(128);
      const embeddings = [
        embedder.embed('hello', 'en').tensor,
        embedder.embed('world', 'en').tensor,
      ];

      const adapter = new CodegenAdapter();
      const result = adapter.generateCode({
        embeddings,
        targetLanguage: 'typescript',
      });

      expect(result.language).toBe('typescript');
      expect(result.code).toContain('result');
      expect(result.code).toContain('embedding_0');
      expect(result.code).toContain('embedding_1');
    });

    it('should generate Python code from embeddings', () => {
      const embedder = new Embedder(64);
      const embeddings = [embedder.embed('test', 'en').tensor];

      const adapter = new CodegenAdapter();
      const result = adapter.generateCode({
        embeddings,
        targetLanguage: 'python',
      });

      expect(result.language).toBe('python');
      expect(result.code).toContain('result');
      expect(result.code).toContain('=');
    });

    it('should generate inference functions', () => {
      const adapter = new CodegenAdapter();
      const rules = [
        { condition: 'facts.animal', conclusion: 'facts.mammal' },
        { condition: 'facts.mammal', conclusion: 'facts.vertebrate' },
      ];

      const result = adapter.generateInferenceFunction(rules, 'typescript');

      expect(result.code).toContain('infer');
      expect(result.code).toContain('animal');
      expect(result.code).toContain('mammal');
    });

    it('should transpile TypeScript to Python', () => {
      const adapter = new CodegenAdapter();
      const tsCode = 'const x: number = 5; interface Foo { bar: string; }';

      const result = adapter.transpile(tsCode, 'typescript', 'python');

      expect(result.language).toBe('python');
      expect(result.code).toContain('#');
    });
  });

  describe('Graph Store', () => {
    it('should add and retrieve entities', () => {
      const graph = new GraphStore();
      const entity: Entity = {
        id: 'e1',
        label: 'Alice',
        type: 'Person',
        properties: { age: 30, city: 'NYC' },
      };

      graph.addEntity(entity);

      const retrieved = graph.getEntity('e1');
      expect(retrieved).toEqual(entity);
    });

    it('should add and retrieve relationships', () => {
      const graph = new GraphStore();

      const e1: Entity = { id: 'e1', label: 'Alice', type: 'Person', properties: {} };
      const e2: Entity = { id: 'e2', label: 'Bob', type: 'Person', properties: {} };

      graph.addEntity(e1);
      graph.addEntity(e2);

      const relId = graph.addRelationship('e1', 'e2', 'knows', { since: 2020 });

      const rel = graph.getRelationship(relId);
      expect(rel).toBeDefined();
      expect(rel?.type).toBe('knows');
      expect(rel?.source).toBe('e1');
      expect(rel?.target).toBe('e2');
    });

    it('should get entities by type', () => {
      const graph = new GraphStore();

      graph.addEntity({ id: 'p1', label: 'Alice', type: 'Person', properties: {} });
      graph.addEntity({ id: 'p2', label: 'Bob', type: 'Person', properties: {} });
      graph.addEntity({ id: 'c1', label: 'NYC', type: 'City', properties: {} });

      const people = graph.getEntitiesByType('Person');
      expect(people.length).toBe(2);

      const cities = graph.getEntitiesByType('City');
      expect(cities.length).toBe(1);
    });

    it('should find paths between entities', () => {
      const graph = new GraphStore();

      graph.addEntity({ id: 'a', label: 'A', type: 'Node', properties: {} });
      graph.addEntity({ id: 'b', label: 'B', type: 'Node', properties: {} });
      graph.addEntity({ id: 'c', label: 'C', type: 'Node', properties: {} });

      graph.addRelationship('a', 'b', 'connected');
      graph.addRelationship('b', 'c', 'connected');

      const path = graph.findPath('a', 'c');
      expect(path).not.toBeNull();
      expect(path?.length).toBe(2);
    });

    it('should convert to RDF triples', () => {
      const graph = new GraphStore();

      graph.addEntity({
        id: 'person1',
        label: 'Alice',
        type: 'Person',
        properties: { name: 'Alice', age: 30 },
      });

      const triples = graph.toTriples();
      expect(triples.length).toBeGreaterThan(0);

      const nameTriple = triples.find(t => t.predicate === 'name');
      expect(nameTriple?.object).toBe('Alice');
    });
  });

  describe('Ontology Manager', () => {
    it('should define and retrieve entity types', () => {
      const onto = new OntologyManager();

      onto.defineEntityType({
        name: 'Person',
        properties: {
          name: { type: 'string', required: true },
          age: { type: 'number' },
        },
      });

      const personType = onto.getEntityType('Person');
      expect(personType).toBeDefined();
      expect(personType?.properties.name.required).toBe(true);
    });

    it('should define and retrieve relationship types', () => {
      const onto = new OntologyManager();

      onto.defineRelationshipType({
        name: 'knows',
        sourceType: 'Person',
        targetType: 'Person',
      });

      const knowsType = onto.getRelationshipType('knows');
      expect(knowsType).toBeDefined();
      expect(knowsType?.sourceType).toBe('Person');
    });

    it('should validate entities against types', () => {
      const onto = new OntologyManager();

      onto.defineEntityType({
        name: 'Person',
        properties: {
          name: { type: 'string', required: true },
          age: { type: 'number' },
        },
      });

      const validEntity = { name: 'Alice', age: 30 };
      const result1 = onto.validateEntity('Person', validEntity);
      expect(result1.valid).toBe(true);

      const invalidEntity = { age: 25 };
      const result2 = onto.validateEntity('Person', invalidEntity);
      expect(result2.valid).toBe(false);
      expect(result2.errors.length).toBeGreaterThan(0);
    });

    it('should export ontology as JSON-LD', () => {
      const onto = new OntologyManager();

      onto.defineEntityType({
        name: 'Person',
        properties: { name: { type: 'string' } },
      });

      const jsonLd = onto.exportAsJsonLd();
      expect(jsonLd['@context']).toBeDefined();
      expect(jsonLd['@graph']).toBeDefined();
    });
  });

  describe('Inference Engine', () => {
    it('should add and retrieve rules', () => {
      const engine = new InferenceEngine();

      const ruleId = engine.addRule({
        name: 'animal_to_mammal',
        condition: [{ type: 'property', property: 'isAnimal', value: true, operator: '=' }],
        conclusion: {
          type: 'set_property',
          property: 'isMammal',
          value: true,
        },
      });

      const rule = engine.getRule(ruleId);
      expect(rule).toBeDefined();
      expect(rule?.name).toBe('animal_to_mammal');
    });

    it('should perform forward chaining inference', () => {
      const engine = new InferenceEngine();
      const graph = new GraphStore();

      graph.addEntity({
        id: 'animal1',
        label: 'Dog',
        type: 'Animal',
        properties: { hasWings: false },
      });

      engine.addRule({
        name: 'has_fur_implies_mammal',
        condition: [{ type: 'entity', entityType: 'Animal' }],
        conclusion: {
          type: 'set_property',
          property: 'isMammal',
          value: true,
        },
      });

      const results = engine.forwardChain(graph, 5);
      expect(results.length).toBeGreaterThan(0);
    });

    it('should perform backward chaining inference', () => {
      const engine = new InferenceEngine();
      const graph = new GraphStore();

      graph.addEntity({
        id: 'test1',
        label: 'Test',
        type: 'TestType',
        properties: {},
      });

      engine.addRule({
        name: 'test_rule',
        condition: [{ type: 'entity', entityType: 'TestType' }],
        conclusion: { type: 'set_property', property: 'tested', value: true },
      });

      const results = engine.backwardChain(graph, { entityType: 'TestType' });
      expect(results).toBeDefined();
    });

    it('should track inference history', () => {
      const engine = new InferenceEngine();
      const graph = new GraphStore();

      graph.addEntity({
        id: 'e1',
        label: 'Entity1',
        type: 'Type1',
        properties: {},
      });

      engine.addRule({
        name: 'rule1',
        condition: [{ type: 'entity', entityType: 'Type1' }],
        conclusion: { type: 'set_property', property: 'inferred', value: true },
      });

      engine.forwardChain(graph);
      const history = engine.getInferenceHistory();

      expect(history.length).toBeGreaterThan(0);
    });
  });

  describe('RDF Loader', () => {
    it('should load RDF triples into graph', () => {
      const loader = new RDFLoader();
      const graph = new GraphStore();

      const triples = [
        { subject: 'http://example.com/alice', predicate: 'http://schema.org/name', object: 'Alice' },
        { subject: 'http://example.com/bob', predicate: 'http://schema.org/name', object: 'Bob' },
      ];

      loader.loadTriples(triples, graph);

      const stats = graph.getStats();
      expect((stats.entityCount as number)).toBeGreaterThan(0);
    });

    it('should load JSON-LD documents', () => {
      const loader = new RDFLoader();
      const graph = new GraphStore();

      const jsonLd = {
        '@context': { '@vocab': 'http://schema.org/' },
        '@graph': [
          {
            '@id': 'http://example.com/person1',
            '@type': 'Person',
            name: 'Alice',
            age: 30,
          },
          {
            '@id': 'http://example.com/person2',
            '@type': 'Person',
            name: 'Bob',
            age: 25,
          },
        ],
      };

      loader.loadJsonLd(jsonLd, graph);
      const stats = graph.getStats();
      expect((stats.entityCount as number)).toBeGreaterThan(0);
    });

    it('should export graph as RDF triples', () => {
      const loader = new RDFLoader();
      const graph = new GraphStore();

      graph.addEntity({
        id: 'person1',
        label: 'Alice',
        type: 'Person',
        properties: { name: 'Alice', age: 30 },
      });

      const triples = loader.exportAsTriples(graph);
      expect(triples.length).toBeGreaterThan(0);

      const nameTriple = triples.find(t => t.predicate === 'name');
      expect(nameTriple).toBeDefined();
    });

    it('should export graph as JSON-LD', () => {
      const loader = new RDFLoader();
      const graph = new GraphStore();

      graph.addEntity({
        id: 'person1',
        label: 'Alice',
        type: 'Person',
        properties: { name: 'Alice' },
      });

      const jsonLd = loader.exportAsJsonLd(graph);
      expect(jsonLd['@context']).toBeDefined();
      expect(jsonLd['@graph']).toBeDefined();
    });
  });

  describe('VM NLP/KG Operations', () => {
    it('should execute NLP_TOKENIZE instruction', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['input', 100] },
        { opcode: OpCode.NLP_TOKENIZE, args: ['input', 'tokens'] },
      ];

      vm.execute(program);

      const tokenCount = vm.getMemory().getRegister('tokens');
      expect(tokenCount).toBeGreaterThan(0);
    });

    it('should execute NLP_EMBED instruction', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['text', 42] },
        { opcode: OpCode.NLP_EMBED, args: ['text', 'embedding'] },
      ];

      vm.execute(program);

      const result = vm.getMemory().getRegister('embedding');
      expect(result).toBe(1);
    });

    it('should execute NLP_TRANSLATE instruction', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['input', 50] },
        { opcode: OpCode.NLP_TRANSLATE, args: ['input', 'es', 'output'] },
      ];

      vm.execute(program);

      const result = vm.getMemory().getRegister('output');
      expect(typeof result).toBe('number');
    });

    it('should execute KG_LOAD instruction', () => {
      const program: Instruction[] = [
        {
          opcode: OpCode.KG_LOAD,
          args: [{ entities: [], relationships: [] }, 'graph_id'],
        },
      ];

      vm.execute(program);

      const result = vm.getMemory().getRegister('graph_id');
      expect(result).toBe(1);
    });

    it('should execute KG_QUERY instruction', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['g_id', 5] },
        { opcode: OpCode.SET, args: ['query', 10] },
        { opcode: OpCode.KG_QUERY, args: ['g_id', 'query', 'result'] },
      ];

      vm.execute(program);

      const result = vm.getMemory().getRegister('result');
      expect(typeof result).toBe('number');
    });

    it('should execute KG_REASON instruction', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['g_id', 5] },
        { opcode: OpCode.SET, args: ['rule', 3] },
        { opcode: OpCode.KG_REASON, args: ['g_id', 'rule', 'result'] },
      ];

      vm.execute(program);

      const result = vm.getMemory().getRegister('result');
      expect(typeof result).toBe('number');
    });

    it('should chain NLP and KG operations', () => {
      const program: Instruction[] = [
        { opcode: OpCode.SET, args: ['text', 50] },
        { opcode: OpCode.NLP_EMBED, args: ['text', 'emb'] },
        {
          opcode: OpCode.KG_LOAD,
          args: [{ data: 'knowledge' }, 'kg'],
        },
        { opcode: OpCode.KG_QUERY, args: ['kg', 'emb', 'answer'] },
      ];

      vm.execute(program);

      const answer = vm.getMemory().getRegister('answer');
      expect(answer).toBeDefined();
    });
  });

  describe('Full Multilingual Integration', () => {
    it('should process multilingual text pipeline', () => {
      const tokenizer = new Tokenizer();
      const embedder = new Embedder();

      const texts = {
        en: 'Hello world from knowledge graph',
        es: 'Hola mundo desde gráfico de conocimiento',
        zh: '来自知识图的你好世界',
      };

      for (const [lang, text] of Object.entries(texts)) {
        const tokens = tokenizer.tokenize(text, { language: lang });
        expect(tokens.length).toBeGreaterThan(0);

        const embedding = embedder.embed(tokens[0].text, lang);
        expect(embedding.tensor.dimensions).toBeGreaterThan(0);
      }
    });

    it('should build and query knowledge graph', () => {
      const graph = new GraphStore();
      const onto = new OntologyManager();
      const loader = new RDFLoader();

      onto.defineEntityType({
        name: 'Concept',
        properties: { label: { type: 'string' }, description: { type: 'string' } },
      });

      const rdfData = {
        '@context': { '@vocab': 'http://schema.org/' },
        '@graph': [
          {
            '@id': 'http://example.com/nlp',
            '@type': 'Concept',
            label: 'Natural Language Processing',
          },
          {
            '@id': 'http://example.com/kg',
            '@type': 'Concept',
            label: 'Knowledge Graph',
          },
        ],
      };

      loader.loadJsonLd(rdfData, graph);

      const concepts = graph.getEntitiesByType('Concept');
      expect(concepts.length).toBeGreaterThanOrEqual(2);
    });

    it('should apply inference over semantic data', () => {
      const graph = new GraphStore();
      const engine = new InferenceEngine();

      graph.addEntity({
        id: 'socrates',
        label: 'Socrates',
        type: 'Person',
        properties: { isPhilosopher: true },
      });

      graph.addEntity({
        id: 'human',
        label: 'Humans',
        type: 'Category',
        properties: { areMortal: true },
      });

      graph.addRelationship('socrates', 'human', 'isInstanceOf');

      engine.addRule({
        name: 'mortal_rule',
        condition: [
          { type: 'relationship', relationshipType: 'isInstanceOf' },
        ],
        conclusion: {
          type: 'set_property',
          property: 'isMortal',
          value: true,
        },
      });

      const results = engine.forwardChain(graph);
      expect(results.length).toBeGreaterThan(0);
    });
  });
});
