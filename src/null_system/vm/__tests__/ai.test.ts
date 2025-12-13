/**
 * AI Module Tests - Super-bit tensors, embeddings, neural layers, and attention
 */

import {
  SuperBitTensor,
  EmbeddingRegistry,
  NeuralEngine,
  DenseLayer,
  AttentionModule,
  NullVM,
  OpCode,
} from '../index';

describe('SuperBitTensor', () => {
  it('should create a tensor with specified shape', () => {
    const tensor = new SuperBitTensor({ dims: [3, 4] });
    expect(tensor.getSize()).toBe(12);
    expect(tensor.getShape().dims).toEqual([3, 4]);
  });

  it('should set and get tensor values', () => {
    const data = new Float32Array([1, 2, 3, 4, 5, 6]);
    const tensor = new SuperBitTensor({ dims: [2, 3] }, data);

    expect(tensor.getAt([0, 0])).toBe(1);
    expect(tensor.getAt([1, 2])).toBe(6);

    tensor.setAt([0, 1], 99);
    expect(tensor.getAt([0, 1])).toBe(99);
  });

  it('should handle tensor metadata (uncertainty, precision)', () => {
    const tensor = new SuperBitTensor({ dims: [5] }, undefined, {
      uncertainty: 0.5,
      precision: 0.8,
      superbitEncoded: true,
    });

    const meta = tensor.getMetadata();
    expect(meta.uncertainty).toBe(0.5);
    expect(meta.precision).toBe(0.8);
    expect(meta.superbitEncoded).toBe(true);
  });

  it('should reduce uncertainty', () => {
    const tensor = new SuperBitTensor({ dims: [3] }, undefined, { uncertainty: 0.8 });

    tensor.reduceUncertainty(0.3);
    expect(tensor.getMetadata().uncertainty).toBe(0.5);

    tensor.reduceUncertainty(0.7);
    expect(tensor.getMetadata().uncertainty).toBe(0);
  });

  it('should clone tensors', () => {
    const data = new Float32Array([1, 2, 3]);
    const tensor = new SuperBitTensor({ dims: [3] }, data);

    const cloned = tensor.clone();
    expect(cloned.getSize()).toBe(tensor.getSize());
    expect(cloned.getData()).toEqual(tensor.getData());

    cloned.setAt([0], 99);
    expect(tensor.getAt([0])).toBe(1);
  });

  it('should serialize and deserialize tensors', () => {
    const data = new Float32Array([1.5, 2.5, 3.5, 4.5]);
    const original = new SuperBitTensor({ dims: [2, 2] }, data, {
      uncertainty: 0.6,
      precision: 0.9,
      superbitEncoded: true,
    });

    const buffer = original.toBuffer();
    const restored = SuperBitTensor.fromBuffer(buffer);

    expect(restored.getShape().dims).toEqual([2, 2]);
    expect(restored.getMetadata().uncertainty).toBeCloseTo(0.6);
    expect(restored.getMetadata().precision).toBeCloseTo(0.9);
  });
});

describe('EmbeddingRegistry', () => {
  let registry: EmbeddingRegistry;

  beforeEach(() => {
    registry = new EmbeddingRegistry();
  });

  it('should register and retrieve embeddings', () => {
    const tensor = new SuperBitTensor({ dims: [128] });
    registry.registerEmbedding('test_embed', tensor, 'dense', 'gpt-2');

    const retrieved = registry.getEmbedding('test_embed');
    expect(retrieved).not.toBeNull();
    expect(retrieved!.getShape().dims[0]).toBe(128);
  });

  it('should track embedding metadata', () => {
    const tensor = new SuperBitTensor({ dims: [64] });
    registry.registerEmbedding('emb1', tensor, 'sparse', 'bert');

    const meta = registry.getEmbeddingMetadata('emb1');
    expect(meta).not.toBeNull();
    expect(meta!.dimension).toBe(64);
    expect(meta!.type).toBe('sparse');
    expect(meta!.sourceModel).toBe('bert');
  });

  it('should list embeddings by type', () => {
    registry.registerEmbedding('dense1', new SuperBitTensor({ dims: [128] }), 'dense');
    registry.registerEmbedding('dense2', new SuperBitTensor({ dims: [256] }), 'dense');
    registry.registerEmbedding('sparse1', new SuperBitTensor({ dims: [512] }), 'sparse');

    const denseEmbeds = registry.listByType('dense');
    expect(denseEmbeds.length).toBe(2);
    expect(denseEmbeds.every((e) => e.type === 'dense')).toBe(true);

    const sparseEmbeds = registry.listByType('sparse');
    expect(sparseEmbeds.length).toBe(1);
  });

  it('should increment use count on retrieval', () => {
    const tensor = new SuperBitTensor({ dims: [100] });
    registry.registerEmbedding('freq_embed', tensor, 'dense');

    let meta = registry.getEmbeddingMetadata('freq_embed');
    expect(meta!.useCount).toBe(0);

    registry.getEmbedding('freq_embed');
    meta = registry.getEmbeddingMetadata('freq_embed');
    expect(meta!.useCount).toBe(1);

    registry.getEmbedding('freq_embed');
    meta = registry.getEmbeddingMetadata('freq_embed');
    expect(meta!.useCount).toBe(2);
  });

  it('should create random embeddings', () => {
    const embed = EmbeddingRegistry.createRandomDenseEmbedding('random_embed', 128);
    expect(embed.getShape().dims[0]).toBe(128);
    expect(embed.getMetadata().uncertainty).toBe(0.5);
  });

  it('should create zero embeddings', () => {
    const embed = EmbeddingRegistry.createZeroEmbedding(64);
    expect(embed.getShape().dims[0]).toBe(64);

    const data = embed.getData();
    for (let i = 0; i < data.length; i++) {
      expect(data[i]).toBe(0);
    }
  });

  it('should delete embeddings', () => {
    registry.registerEmbedding('to_delete', new SuperBitTensor({ dims: [50] }), 'dense');
    expect(registry.hasEmbedding('to_delete')).toBe(true);

    registry.deleteEmbedding('to_delete');
    expect(registry.hasEmbedding('to_delete')).toBe(false);
  });
});

describe('DenseLayer', () => {
  it('should create layer with correct dimensions', () => {
    const layer = new DenseLayer({ inputDim: 10, outputDim: 5 });
    const weights = layer.getWeights();
    expect(weights.getShape().dims).toEqual([10, 5]);
  });

  it('should execute forward pass', () => {
    const input = new SuperBitTensor({ dims: [3] }, new Float32Array([1, 2, 3]));
    const layer = new DenseLayer({ inputDim: 3, outputDim: 2, activation: 'linear' });

    const output = layer.forward(input);
    expect(output.getShape().dims[0]).toBe(2);
  });

  it('should apply ReLU activation', () => {
    const input = new SuperBitTensor({ dims: [2] }, new Float32Array([-5, 5]));
    const weights = new SuperBitTensor({ dims: [2, 3] }, new Float32Array(Array(6).fill(0.1)));
    const layer = new DenseLayer({ inputDim: 2, outputDim: 3, activation: 'relu' }, weights);

    const output = layer.forward(input);
    const data = output.getData();

    for (let i = 0; i < data.length; i++) {
      expect(data[i]).toBeGreaterThanOrEqual(0);
    }
  });

  it('should apply Sigmoid activation', () => {
    const input = new SuperBitTensor({ dims: [2] }, new Float32Array([0, 10]));
    const weights = new SuperBitTensor({ dims: [2, 1] }, new Float32Array([1, 1]));
    const layer = new DenseLayer({ inputDim: 2, outputDim: 1, activation: 'sigmoid' }, weights);

    const output = layer.forward(input);
    const value = output.getAt([0]);

    expect(value).toBeGreaterThan(0);
    expect(value).toBeLessThan(1);
  });

  it('should propagate uncertainty through layer', () => {
    const input = new SuperBitTensor({ dims: [5] }, undefined, { uncertainty: 0.6 });

    const layer = new DenseLayer({ inputDim: 5, outputDim: 3 });
    const output = layer.forward(input);

    expect(output.getMetadata().uncertainty).toBeGreaterThan(0);
  });
});

describe('NeuralEngine', () => {
  let engine: NeuralEngine;

  beforeEach(() => {
    engine = new NeuralEngine();
  });

  it('should add layers to network', () => {
    engine.addLayer({ inputDim: 10, outputDim: 5 });
    engine.addLayer({ inputDim: 5, outputDim: 2 });

    expect(engine.getLayerCount()).toBe(2);
  });

  it('should execute forward pass through multiple layers', () => {
    engine.addLayer({ inputDim: 10, outputDim: 5, activation: 'relu' });
    engine.addLayer({ inputDim: 5, outputDim: 2, activation: 'linear' });

    const input = new SuperBitTensor({ dims: [10] });
    const output = engine.forward(input);

    expect(output.getShape().dims[0]).toBe(2);
  });

  it('should clone neural engine', () => {
    engine.addLayer({ inputDim: 8, outputDim: 4 });
    const cloned = engine.clone();

    expect(cloned.getLayerCount()).toBe(1);
  });
});

describe('AttentionModule', () => {
  let attention: AttentionModule;

  beforeEach(() => {
    attention = new AttentionModule({ headCount: 2 });
  });

  it('should perform scaled dot-product attention', () => {
    const query = new SuperBitTensor({ dims: [4] }, new Float32Array([1, 2, 3, 4]));
    const key = new SuperBitTensor({ dims: [4] }, new Float32Array([1, 1, 1, 1]));
    const value = new SuperBitTensor({ dims: [4] }, new Float32Array([1, 0, 1, 0]));

    const output = attention.scaledDotProductAttention(query, key, value);
    expect(output.getShape().dims[0]).toBe(4);
  });

  it('should perform multi-head attention', () => {
    const input = new SuperBitTensor({ dims: [8] });
    const output = attention.multiHeadAttention(input, input, input);

    expect(output.getShape().dims[0]).toBe(8);
  });

  it('should perform self-attention', () => {
    const input = new SuperBitTensor({ dims: [6] });
    const output = attention.selfAttention(input);

    expect(output.getShape().dims[0]).toBe(6);
  });

  it('should reduce uncertainty through attention', () => {
    const input = new SuperBitTensor({ dims: [4] }, undefined, { uncertainty: 0.8 });

    const output = attention.reduceUncertaintyWithAttention(input);
    expect(output.getMetadata().uncertainty).toBeLessThan(0.8);
  });

  it('should configure attention module', () => {
    attention.setConfig({ temperatureScale: 2.0, uncertaintyReductionFactor: 0.5 });
    const config = attention.getConfig();

    expect(config.temperatureScale).toBe(2.0);
    expect(config.uncertaintyReductionFactor).toBe(0.5);
  });
});

describe('AI Instructions in NullVM', () => {
  let vm: NullVM;

  beforeEach(() => {
    vm = new NullVM();
  });

  it('should execute AI_EMBED instruction', () => {
    const program = [
      {
        opcode: OpCode.AI_EMBED,
        args: ['embed_out', 'embed_001', 128],
      },
      {
        opcode: OpCode.SHOW,
        args: ['embed_out'],
      },
    ];

    expect(() => vm.execute(program)).not.toThrow();
    const tensor = vm.getMemory().getTensorRegister('embed_out');
    expect(tensor).not.toBeNull();
    expect(tensor!.getShape().dims[0]).toBe(128);
  });

  it('should execute AI_LAYER instruction', () => {
    const program = [
      {
        opcode: OpCode.AI_EMBED,
        args: ['input_tensor', 'embed_test', 10],
      },
      {
        opcode: OpCode.AI_LAYER,
        args: ['input_tensor', 'layer_output', '{"outputDim": 5}', 'linear'],
      },
    ];

    expect(() => vm.execute(program)).not.toThrow();
    const output = vm.getMemory().getTensorRegister('layer_output');
    expect(output).not.toBeNull();
    expect(output!.getShape().dims[0]).toBe(5);
  });

  it('should execute AI_ATTEND instruction with uncertainty reduction', () => {
    const program = [
      {
        opcode: OpCode.AI_EMBED,
        args: ['attn_input', 'emb_attn', 8],
      },
      {
        opcode: OpCode.AI_ATTEND,
        args: ['attn_input', 'attn_output', '{"headCount": 2}'],
      },
    ];

    expect(() => vm.execute(program)).not.toThrow();
    const input = vm.getMemory().getTensorRegister('attn_input');
    const output = vm.getMemory().getTensorRegister('attn_output');

    expect(output).not.toBeNull();
    expect(output!.getMetadata().uncertainty).toBeLessThanOrEqual(input!.getMetadata().uncertainty);
  });

  it('should execute AI_FUZZY instruction', () => {
    const program = [
      {
        opcode: OpCode.AI_EMBED,
        args: ['fuzzy_input', 'emb_fuzzy', 5],
      },
      {
        opcode: OpCode.AI_FUZZY,
        args: ['fuzzy_input', 'fuzzy_output', 0.2],
      },
    ];

    expect(() => vm.execute(program)).not.toThrow();
    const input = vm.getMemory().getTensorRegister('fuzzy_input');
    const output = vm.getMemory().getTensorRegister('fuzzy_output');

    expect(output).not.toBeNull();
    expect(output!.getMetadata().uncertainty).toBeLessThan(input!.getMetadata().uncertainty);
  });

  it('should execute full AI pipeline: EMBED -> LAYER -> ATTEND -> SHOW', () => {
    const program = [
      {
        opcode: OpCode.AI_EMBED,
        args: ['x', 'token_embedding_001', 16],
      },
      {
        opcode: OpCode.AI_LAYER,
        args: ['x', 'h1', '{"outputDim": 8}', 'relu'],
      },
      {
        opcode: OpCode.AI_ATTEND,
        args: ['h1', 'attn_out', '{"headCount": 2}'],
      },
      {
        opcode: OpCode.SHOW,
        args: ['attn_out'],
      },
    ];

    expect(() => vm.execute(program)).not.toThrow();

    const result = vm.getMemory().getTensorRegister('attn_out');
    expect(result).not.toBeNull();
    expect(result!.getShape().dims[0]).toBe(8);
  });

  it('should fail on invalid tensor register access', () => {
    const program = [
      {
        opcode: OpCode.AI_LAYER,
        args: ['nonexistent_input', 'output', '{"outputDim": 5}', 'linear'],
      },
    ];

    expect(() => vm.execute(program)).toThrow();
  });

  it('should access embedding registry from VM', () => {
    const program = [
      {
        opcode: OpCode.AI_EMBED,
        args: ['out', 'test_emb_access', 32],
      },
    ];

    vm.execute(program);
    const registry = vm.getEmbeddingRegistry();
    expect(registry.hasEmbedding('test_emb_access')).toBe(true);
    expect(registry.getCount()).toBeGreaterThan(0);
  });

  it('should access neural engine and attention module from VM', () => {
    const engine = vm.getNeuralEngine();
    const attention = vm.getAttentionModule();

    expect(engine).not.toBeUndefined();
    expect(attention).not.toBeUndefined();
  });
});

describe('AI Integration - Complex Scenarios', () => {
  let vm: NullVM;

  beforeEach(() => {
    vm = new NullVM();
  });

  it('should handle multiple sequential AI operations', () => {
    const program = [
      {
        opcode: OpCode.AI_EMBED,
        args: ['seq1', 'emb1', 10],
      },
      {
        opcode: OpCode.AI_EMBED,
        args: ['seq2', 'emb2', 10],
      },
      {
        opcode: OpCode.AI_ATTEND,
        args: ['seq1', 'attended1', '{}'],
      },
      {
        opcode: OpCode.AI_ATTEND,
        args: ['seq2', 'attended2', '{}'],
      },
    ];

    expect(() => vm.execute(program)).not.toThrow();

    expect(vm.getMemory().getTensorRegister('attended1')).not.toBeNull();
    expect(vm.getMemory().getTensorRegister('attended2')).not.toBeNull();
  });

  it('should maintain tensor state in memory across instructions', () => {
    const program = [
      {
        opcode: OpCode.AI_EMBED,
        args: ['persistent', 'long_term_embed', 20],
      },
      {
        opcode: OpCode.SET,
        args: ['counter', 1],
      },
      {
        opcode: OpCode.ADD,
        args: ['counter', 5],
      },
      {
        opcode: OpCode.SHOW,
        args: ['counter'],
      },
    ];

    vm.execute(program);

    const tensorState = vm.getMemory().getTensorRegister('persistent');
    expect(tensorState).not.toBeNull();
    expect(tensorState!.getShape().dims[0]).toBe(20);
  });

  it('should measure uncertainty reduction through attention', () => {
    const program = [
      {
        opcode: OpCode.AI_EMBED,
        args: ['input', 'uncertainty_test', 8],
      },
      {
        opcode: OpCode.AI_ATTEND,
        args: ['input', 'output', '{}'],
      },
    ];

    vm.execute(program);

    const input = vm.getMemory().getTensorRegister('input');
    const output = vm.getMemory().getTensorRegister('output');

    const inputUncertainty = input!.getMetadata().uncertainty;
    const outputUncertainty = output!.getMetadata().uncertainty;

    expect(outputUncertainty).toBeLessThan(inputUncertainty);
  });
});
