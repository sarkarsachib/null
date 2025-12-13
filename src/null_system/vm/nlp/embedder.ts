/**
 * Embedder for generating and translating multilingual embeddings
 * Works with SuperBitTensor abstractions for efficient vector representation
 */

export interface SuperBitTensor {
  dimensions: number;
  bits: Uint8Array;
  metadata?: Record<string, unknown>;
}

export interface EmbeddingResult {
  tensor: SuperBitTensor;
  confidence: number;
  language: string;
  originalText?: string;
}

export interface TranslationResult {
  targetLanguage: string;
  translatedText: string;
  confidence: number;
}

// Simple hash-based embedding generator for deterministic results
class SimpleEmbedder {
  private dimension: number;

  constructor(dimension: number = 128) {
    this.dimension = dimension;
  }

  /**
   * Generate deterministic embedding from text using hash-based approach
   */
  generateEmbedding(text: string, language: string = 'en'): Uint8Array {
    const bits = new Uint8Array(this.dimension);

    for (let i = 0; i < this.dimension; i++) {
      let hash = 0;
      for (let j = 0; j < text.length; j++) {
        const char = text.charCodeAt(j);
        hash = ((hash << 5) - hash) + char + i;
        hash |= 0; // Convert to 32-bit integer
      }

      // Deterministic bit based on hash
      const byte = Math.abs(hash) % 256;
      bits[i] = byte & 0xff;
    }

    return bits;
  }

  /**
   * Compute similarity between two embeddings (cosine-like)
   */
  similarity(bits1: Uint8Array, bits2: Uint8Array): number {
    let dotProduct = 0;
    let norm1 = 0;
    let norm2 = 0;

    for (let i = 0; i < Math.min(bits1.length, bits2.length); i++) {
      const v1 = bits1[i];
      const v2 = bits2[i];
      dotProduct += v1 * v2;
      norm1 += v1 * v1;
      norm2 += v2 * v2;
    }

    const denominator = Math.sqrt(norm1) * Math.sqrt(norm2);
    if (denominator === 0) return 0;

    return dotProduct / denominator;
  }
}

const TRANSLATION_PAIRS: Record<string, Record<string, string>> = {
  'hello_en': {
    es: 'hola',
    fr: 'bonjour',
    de: 'hallo',
    zh: '你好',
    ru: 'привет',
  },
  'world_en': {
    es: 'mundo',
    fr: 'monde',
    de: 'welt',
    zh: '世界',
    ru: 'мир',
  },
  'knowledge_en': {
    es: 'conocimiento',
    fr: 'connaissance',
    de: 'wissen',
    zh: '知识',
    ru: 'знание',
  },
  'graph_en': {
    es: 'gráfico',
    fr: 'graphique',
    de: 'grafik',
    zh: '图表',
    ru: 'график',
  },
  'reason_en': {
    es: 'razón',
    fr: 'raison',
    de: 'grund',
    zh: '原因',
    ru: 'причина',
  },
};

export class Embedder {
  private simpleEmbedder: SimpleEmbedder;

  constructor(dimension: number = 128) {
    this.simpleEmbedder = new SimpleEmbedder(dimension);
  }

  /**
   * Generate embedding for text
   */
  embed(text: string, language: string = 'en'): EmbeddingResult {
    const bits = this.simpleEmbedder.generateEmbedding(text, language);

    return {
      tensor: {
        dimensions: bits.length,
        bits,
        metadata: {
          text,
          language,
          createdAt: Date.now(),
        },
      },
      confidence: 0.95,
      language,
      originalText: text,
    };
  }

  /**
   * Translate text between languages with embedding consistency
   */
  translate(text: string, sourceLanguage: string, targetLanguage: string): TranslationResult {
    const lowerText = text.toLowerCase();
    const key = `${lowerText}_${sourceLanguage}`;

    if (TRANSLATION_PAIRS[key] && TRANSLATION_PAIRS[key][targetLanguage]) {
      return {
        targetLanguage,
        translatedText: TRANSLATION_PAIRS[key][targetLanguage],
        confidence: 0.99,
      };
    }

    // Fallback: transliterate or approximate
    return {
      targetLanguage,
      translatedText: this.approximate(text, targetLanguage),
      confidence: 0.6,
    };
  }

  /**
   * Get approximate translation
   */
  private approximate(text: string, targetLanguage: string): string {
    // Simple strategy: return text with language marker
    return `[${targetLanguage}:${text}]`;
  }

  /**
   * Compute semantic similarity between embeddings
   */
  similarity(embedding1: SuperBitTensor, embedding2: SuperBitTensor): number {
    return this.simpleEmbedder.similarity(embedding1.bits, embedding2.bits);
  }

  /**
   * Batch embed texts
   */
  batchEmbed(texts: string[], language: string = 'en'): EmbeddingResult[] {
    return texts.map(text => this.embed(text, language));
  }

  /**
   * Create zero embedding
   */
  zeroEmbedding(dimension: number = 128): SuperBitTensor {
    return {
      dimensions: dimension,
      bits: new Uint8Array(dimension),
      metadata: {
        type: 'zero',
        createdAt: Date.now(),
      },
    };
  }

  /**
   * Add two embeddings (element-wise addition with normalization)
   */
  add(tensor1: SuperBitTensor, tensor2: SuperBitTensor): SuperBitTensor {
    const dimension = Math.min(tensor1.dimensions, tensor2.dimensions);
    const result = new Uint8Array(dimension);

    for (let i = 0; i < dimension; i++) {
      const sum = (tensor1.bits[i] + tensor2.bits[i]) / 2; // Average to keep in range
      result[i] = Math.floor(sum) & 0xff;
    }

    return {
      dimensions: dimension,
      bits: result,
      metadata: {
        type: 'sum',
        operands: 2,
        createdAt: Date.now(),
      },
    };
  }
}
