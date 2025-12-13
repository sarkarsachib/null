/**
 * AI Inference Example - Demonstrates super-bit tensor operations
 * Shows embedding allocation, dense layer inference, attention, and uncertainty reduction
 */

import { NullVM, OpCode, SuperBitTensor, EmbeddingRegistry } from '../src';

export function runAIInferenceExample() {
  console.log('=== NullVM AI Inference Example ===\n');

  const vm = new NullVM({ enableTracing: false });
  const registry = vm.getEmbeddingRegistry();

  console.log('Step 1: Creating and registering a token embedding');
  const tokenEmbedding = EmbeddingRegistry.createRandomDenseEmbedding('token_0', 16);
  registry.registerEmbedding('token_0', tokenEmbedding, 'dense', 'gpt-like-model');
  console.log(
    `  ✓ Registered embedding: dimension=${tokenEmbedding.getShape().dims[0]}, ` +
      `uncertainty=${tokenEmbedding.getMetadata().uncertainty}`
  );

  console.log('\nStep 2: Creating a simple token embedding query');
  const program1 = [
    {
      opcode: OpCode.AI_EMBED,
      args: ['token_embedding', 'token_0', 16],
    },
  ];

  vm.execute(program1);
  const tokenEmbedResult = vm.getState().memory.getTensorRegister('token_embedding');
  console.log(
    `  ✓ Token embedding loaded: shape=[${tokenEmbedResult?.getShape().dims}], ` +
      `uncertainty=${tokenEmbedResult?.getMetadata().uncertainty}`
  );

  console.log('\nStep 3: Creating a simple fully-connected layer (dense layer)');
  const program2 = [
    {
      opcode: OpCode.AI_EMBED,
      args: ['input', 'tok_embed', 8],
    },
    {
      opcode: OpCode.AI_LAYER,
      args: ['input', 'hidden_layer', '{"outputDim": 4}', 'relu'],
    },
  ];

  const vm2 = new NullVM();
  vm2.execute(program2);
  const hiddenResult = vm2.getState().memory.getTensorRegister('hidden_layer');
  console.log(
    `  ✓ Dense layer output: shape=[${hiddenResult?.getShape().dims}], ` +
      `activation=relu`
  );

  console.log('\nStep 4: Applying attention mechanism with uncertainty reduction');
  const program3 = [
    {
      opcode: OpCode.AI_EMBED,
      args: ['query_input', 'query_emb', 8],
    },
    {
      opcode: OpCode.AI_ATTEND,
      args: ['query_input', 'attention_output', '{"headCount": 2}'],
    },
  ];

  const vm3 = new NullVM();
  vm3.execute(program3);

  const queryInput = vm3.getState().memory.getTensorRegister('query_input');
  const attentionOutput = vm3.getState().memory.getTensorRegister('attention_output');

  const inputUncertainty = queryInput?.getMetadata().uncertainty || 0;
  const outputUncertainty = attentionOutput?.getMetadata().uncertainty || 0;
  const uncertaintyReduction = inputUncertainty - outputUncertainty;

  console.log(`  ✓ Input uncertainty: ${inputUncertainty.toFixed(4)}`);
  console.log(`  ✓ Output uncertainty: ${outputUncertainty.toFixed(4)}`);
  console.log(
    `  ✓ Uncertainty reduced by: ${uncertaintyReduction.toFixed(4)} (${(
      (uncertaintyReduction / inputUncertainty) *
      100
    ).toFixed(1)}%)`
  );

  console.log('\nStep 5: Complete inference pipeline (EMBED → LAYER → ATTEND)');
  const program4 = [
    {
      opcode: OpCode.AI_EMBED,
      args: ['x', 'emb_input_token', 12],
    },
    {
      opcode: OpCode.AI_LAYER,
      args: ['x', 'h1', '{"outputDim": 8}', 'relu'],
    },
    {
      opcode: OpCode.AI_LAYER,
      args: ['h1', 'h2', '{"outputDim": 4}', 'linear'],
    },
    {
      opcode: OpCode.AI_ATTEND,
      args: ['h2', 'logits', '{"headCount": 2}'],
    },
  ];

  const vm4 = new NullVM();
  vm4.execute(program4);

  const logits = vm4.getState().memory.getTensorRegister('logits');
  console.log(`  ✓ Final output shape: [${logits?.getShape().dims}]`);
  console.log(`  ✓ Final uncertainty: ${logits?.getMetadata().uncertainty.toFixed(4)}`);

  console.log('\nStep 6: Fuzzy logic uncertainty reduction');
  const program5 = [
    {
      opcode: OpCode.AI_EMBED,
      args: ['fuzzy_input', 'fuzzy_embed', 6],
    },
    {
      opcode: OpCode.AI_FUZZY,
      args: ['fuzzy_input', 'fuzzy_reduced', 0.25],
    },
  ];

  const vm5 = new NullVM();
  vm5.execute(program5);

  const fuzzyInput = vm5.getState().memory.getTensorRegister('fuzzy_input');
  const fuzzyReduced = vm5.getState().memory.getTensorRegister('fuzzy_reduced');

  console.log(
    `  ✓ Fuzzy operation: ${fuzzyInput?.getMetadata().uncertainty.toFixed(4)} → ` +
      `${fuzzyReduced?.getMetadata().uncertainty.toFixed(4)}`
  );

  console.log('\n=== Summary ===');
  console.log('✓ AI_EMBED: Allocates and loads embeddings into tensor registers');
  console.log('✓ AI_LAYER: Performs dense layer forward passes with activations');
  console.log('✓ AI_ATTEND: Applies self-attention with uncertainty reduction');
  console.log('✓ AI_FUZZY: Reduces uncertainty via probabilistic evaluation');
  console.log(
    '\n✓ All AI instructions work deterministically and maintain tensor state in NullVM'
  );
}

export function demonstrateEmbeddingManagement() {
  console.log('\n=== Embedding Management Demo ===\n');

  const vm = new NullVM();
  const registry = vm.getEmbeddingRegistry();

  console.log('Creating multiple embeddings with different types:');

  const denseEmbeds = [
    { id: 'dense_word_0', dim: 128, model: 'word2vec' },
    { id: 'dense_word_1', dim: 128, model: 'word2vec' },
    { id: 'dense_contextual', dim: 256, model: 'bert' },
  ];

  for (const { id, dim, model } of denseEmbeds) {
    const embed = EmbeddingRegistry.createRandomDenseEmbedding(id, dim);
    registry.registerEmbedding(id, embed, 'dense', model);
  }

  console.log(`  ✓ Registered ${denseEmbeds.length} dense embeddings`);

  const sparseEmbeds = [
    { id: 'sparse_one_hot_0', dim: 10000 },
    { id: 'sparse_one_hot_1', dim: 10000 },
  ];

  for (const { id, dim } of sparseEmbeds) {
    const embed = EmbeddingRegistry.createZeroEmbedding(dim);
    registry.registerEmbedding(id, embed, 'sparse');
  }

  console.log(`  ✓ Registered ${sparseEmbeds.length} sparse embeddings`);

  const denseList = registry.listByType('dense');
  const sparseList = registry.listByType('sparse');

  console.log(`\nEmbedding statistics:`);
  console.log(`  Dense embeddings: ${denseList.length}`);
  console.log(`  Sparse embeddings: ${sparseList.length}`);
  console.log(`  Total registered: ${registry.getCount()}`);

  console.log(`\nDense embeddings usage:`);
  for (const meta of denseList) {
    console.log(
      `  - ${meta.id} (dim=${meta.dimension}, model=${meta.sourceModel}, uses=${meta.useCount})`
    );
  }
}

export function demonstrateAttentionMechanism() {
  console.log('\n=== Attention Mechanism Demo ===\n');

  const vm = new NullVM();
  const attentionModule = vm.getAttentionModule();

  console.log('Multi-head attention with 4 heads:');
  attentionModule.setConfig({
    headCount: 4,
    temperatureScale: 1.0,
    uncertaintyReductionFactor: 0.4,
  });

  const sequence = new SuperBitTensor({ dims: [16] }, undefined, { uncertainty: 0.7 });
  console.log(`  Input: shape=[16], uncertainty=0.7`);

  const attended = attentionModule.selfAttention(sequence);
  console.log(`  Output: shape=[${attended.getShape().dims}], ` +
    `uncertainty=${attended.getMetadata().uncertainty.toFixed(4)}`);
  console.log(`  ✓ Uncertainty reduced by ${(0.7 - attended.getMetadata().uncertainty).toFixed(4)}`);
}

if (require.main === module) {
  runAIInferenceExample();
  demonstrateEmbeddingManagement();
  demonstrateAttentionMechanism();
}
