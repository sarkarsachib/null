/**
 * Tokenizer for multilingual text processing
 * Supports basic tokenization and language-aware processing
 */

export interface TokenizeOptions {
  language?: string;
  lowercase?: boolean;
  removeStopwords?: boolean;
  stemming?: boolean;
}

export interface Token {
  text: string;
  language?: string;
  pos?: string;
  confidence?: number;
}

const STOPWORDS: Record<string, Set<string>> = {
  en: new Set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'be']),
  es: new Set(['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no', 'haber', 'por', 'con', 'su']),
  fr: new Set(['le', 'la', 'de', 'et', 'à', 'en', 'un', 'être', 'se', 'ne', 'avoir', 'par', 'pour', 'que', 'ou']),
  de: new Set(['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf', 'für', 'ist', 'im']),
  zh: new Set(['的', '一', '是', '在', '不', '了', '有', '和', '人', '这', '中', '大', '为', '上', '个']),
};

const SIMPLE_STEMMER: Record<string, (word: string) => string> = {
  en: (word: string) => {
    if (word.endsWith('ing')) return word.slice(0, -3);
    if (word.endsWith('ed')) return word.slice(0, -2);
    if (word.endsWith('s')) return word.slice(0, -1);
    return word;
  },
};

export class Tokenizer {
  tokenize(text: string, options: TokenizeOptions = {}): Token[] {
    const language = options.language || 'en';
    let tokens = this.splitTokens(text, language);

    if (options.lowercase !== false) {
      tokens = tokens.map(t => ({ ...t, text: t.text.toLowerCase() }));
    }

    if (options.removeStopwords) {
      tokens = tokens.filter(t => !this.isStopword(t.text, language));
    }

    if (options.stemming) {
      tokens = tokens.map(t => ({ ...t, text: this.stem(t.text, language) }));
    }

    return tokens;
  }

  private splitTokens(text: string, language: string): Token[] {
    let separator = /\s+/;

    if (language === 'zh' || language === 'ja' || language === 'ko') {
      separator = /(?:)/;
    }

    const tokenTexts = text
      .split(separator)
      .map(t => t.trim())
      .filter(t => t.length > 0);

    return tokenTexts.map(text => ({
      text,
      language,
    }));
  }

  private isStopword(word: string, language: string): boolean {
    const stopwords = STOPWORDS[language];
    if (!stopwords) return false;
    return stopwords.has(word.toLowerCase());
  }

  private stem(word: string, language: string): string {
    const stemmer = SIMPLE_STEMMER[language];
    if (!stemmer) return word;
    return stemmer(word);
  }

  detectLanguage(text: string): string {
    if (/[\u4E00-\u9FFF]/.test(text)) return 'zh';
    if (/[\u3040-\u309F]/.test(text)) return 'ja';
    if (/[\uAC00-\uD7AF]/.test(text)) return 'ko';
    if (/[\u0600-\u06FF]/.test(text)) return 'ar';
    if (/[\u0400-\u04FF]/.test(text)) return 'ru';

    return 'en';
  }

  getLanguageStats(tokens: Token[]): Record<string, unknown> {
    const languages = new Map<string, number>();
    for (const token of tokens) {
      const lang = token.language || 'en';
      languages.set(lang, (languages.get(lang) || 0) + 1);
    }

    return {
      totalTokens: tokens.length,
      uniqueLanguages: languages.size,
      languageDistribution: Object.fromEntries(languages),
    };
  }
}
