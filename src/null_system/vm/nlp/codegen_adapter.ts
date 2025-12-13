/**
 * Code generation adapter for translating embeddings and knowledge graphs to executable code
 */

import { SuperBitTensor } from './embedder';

export interface CodeGenerationRequest {
  embeddings: SuperBitTensor[];
  targetLanguage?: string;
  context?: Record<string, unknown>;
}

export interface GeneratedCode {
  language: string;
  code: string;
  confidence: number;
  explanation: string;
}

export class CodegenAdapter {
  /**
   * Generate code from embeddings
   */
  generateCode(request: CodeGenerationRequest): GeneratedCode {
    const targetLanguage = request.targetLanguage || 'typescript';

    const code = this.buildCode(request.embeddings, targetLanguage, request.context);

    return {
      language: targetLanguage,
      code,
      confidence: 0.85,
      explanation: `Generated ${targetLanguage} code from ${request.embeddings.length} embeddings`,
    };
  }

  /**
   * Build code based on embeddings
   */
  private buildCode(
    embeddings: SuperBitTensor[],
    targetLanguage: string,
    context?: Record<string, unknown>
  ): string {
    if (embeddings.length === 0) {
      return this.getEmptyTemplate(targetLanguage);
    }

    const lines: string[] = [];

    if (targetLanguage === 'typescript' || targetLanguage === 'javascript') {
      lines.push('// Generated from embeddings');
      lines.push('const result = {');

      for (let i = 0; i < embeddings.length; i++) {
        const emb = embeddings[i];
        const name = `embedding_${i}`;
        const value = this.embeddingToValue(emb);
        lines.push(`  ${name}: ${value},`);
      }

      lines.push('};');
      lines.push('export default result;');
    } else if (targetLanguage === 'python') {
      lines.push('# Generated from embeddings');
      lines.push('result = {');

      for (let i = 0; i < embeddings.length; i++) {
        const emb = embeddings[i];
        const name = `embedding_${i}`;
        const value = this.embeddingToValue(emb);
        lines.push(`    "${name}": ${value},`);
      }

      lines.push('}');
    } else if (targetLanguage === 'sql') {
      lines.push('-- Generated from embeddings');
      lines.push('CREATE TABLE embeddings (');
      lines.push('  id INT PRIMARY KEY,');
      lines.push('  dimension INT,');
      lines.push('  data BLOB');
      lines.push(');');

      for (let i = 0; i < embeddings.length; i++) {
        const emb = embeddings[i];
        const hexData = Buffer.from(emb.bits).toString('hex');
        lines.push(`INSERT INTO embeddings VALUES (${i}, ${emb.dimensions}, X'${hexData}');`);
      }
    }

    return lines.join('\n');
  }

  /**
   * Convert embedding to a code value representation
   */
  private embeddingToValue(embedding: SuperBitTensor): string {
    const firstBytes = Array.from(embedding.bits.slice(0, 8)).join(', ');
    return `[${firstBytes}...] /* ${embedding.dimensions} dims */`;
  }

  /**
   * Get empty template for target language
   */
  private getEmptyTemplate(targetLanguage: string): string {
    if (targetLanguage === 'typescript' || targetLanguage === 'javascript') {
      return 'export const result = {};';
    } else if (targetLanguage === 'python') {
      return 'result = {}';
    } else if (targetLanguage === 'sql') {
      return 'SELECT 1 AS empty;';
    }
    return '';
  }

  /**
   * Generate inference function from knowledge graph
   */
  generateInferenceFunction(rules: Array<{ condition: string; conclusion: string }>, language: string = 'typescript'): GeneratedCode {
    const lines: string[] = [];

    if (language === 'typescript' || language === 'javascript') {
      lines.push('function infer(facts: Record<string, boolean>): Record<string, boolean> {');
      lines.push('  const result = { ...facts };');
      lines.push('  let changed = true;');
      lines.push('  while (changed) {');
      lines.push('    changed = false;');

      for (const rule of rules) {
        lines.push(`    // Rule: ${rule.condition} -> ${rule.conclusion}`);
        lines.push(`    if (${rule.condition} && !${rule.conclusion}) {`);
        lines.push(`      result.${rule.conclusion} = true;`);
        lines.push('      changed = true;');
        lines.push('    }');
      }

      lines.push('  }');
      lines.push('  return result;');
      lines.push('}');
    }

    return {
      language,
      code: lines.join('\n'),
      confidence: 0.9,
      explanation: `Generated inference function with ${rules.length} rules`,
    };
  }

  /**
   * Transpile generated code to another language
   */
  transpile(code: string, fromLanguage: string, toLanguage: string): GeneratedCode {
    // Simple transpilation strategy: preserve structure, adapt syntax
    let transpiledCode = code;

    if (fromLanguage === 'typescript' && toLanguage === 'python') {
      transpiledCode = this.transpileTypescriptToPython(code);
    } else if (fromLanguage === 'python' && toLanguage === 'typescript') {
      transpiledCode = this.transpilepythonToTypescript(code);
    }

    return {
      language: toLanguage,
      code: transpiledCode,
      confidence: 0.8,
      explanation: `Transpiled from ${fromLanguage} to ${toLanguage}`,
    };
  }

  /**
   * Transpile TypeScript to Python
   */
  private transpileTypescriptToPython(code: string): string {
    let result = code
      .replace(/\/\//g, '#')
      .replace(/interface\s+\w+\s*\{[^}]*\}/g, '# interface removed')
      .replace(/const\s+/g, '')
      .replace(/:\s*\w+/g, '')
      .replace(/;\s*$/gm, '')
      .replace(/\{\s*\}/g, '{}')
      .replace(/\[\s*\]/g, '[]');

    return result;
  }

  /**
   * Transpile Python to TypeScript
   */
  private transpilepythonToTypescript(code: string): string {
    let result = code
      .replace(/#/g, '//')
      .replace(/^([^=]+)=/gm, 'const $1 =')
      .replace(/def\s+(\w+)/g, 'function $1')
      .replace(/\n\s{4}/g, '\n  ')
      .replace(/import\s+/g, 'import ')
      .replace(/from\s+(\S+)\s+import/g, 'import');

    return result;
  }
}
