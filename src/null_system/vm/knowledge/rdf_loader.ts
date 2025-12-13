/**
 * RDF/JSON-LD loader for importing knowledge graphs
 */

import { GraphStore, Entity, Triple } from './graph_store';
import { SuperBitTensor } from '../nlp/embedder';

export interface RDFTripleFormat {
  subject: string;
  predicate: string;
  object: string;
}

export interface JsonLdDocument {
  '@context'?: Record<string, unknown> | string[];
  '@graph'?: Array<Record<string, unknown>>;
  [key: string]: unknown;
}

export class RDFLoader {
  /**
   * Load triples into graph store
   */
  loadTriples(triples: RDFTripleFormat[] | Triple[], graph: GraphStore): void {
    const entityMap = new Map<string, Partial<Entity>>();

    // First pass: collect all entities
    for (const triple of triples) {
      const subject = triple.subject;
      const object = triple.object;

      if (!entityMap.has(subject)) {
        entityMap.set(subject, {
          id: subject,
          label: this.extractLabel(subject),
          type: 'Resource',
          properties: {},
        });
      }

      // Object might also be an entity if it looks like an IRI
      if (this.isEntityReference(object)) {
        if (!entityMap.has(object)) {
          entityMap.set(object, {
            id: object,
            label: this.extractLabel(object),
            type: 'Resource',
            properties: {},
          });
        }
      }
    }

    // Add entities to graph
    for (const entity of entityMap.values()) {
      if (entity.id && entity.label && entity.type) {
        graph.addEntity(entity as Entity);
      }
    }

    // Second pass: add relationships and properties
    for (const triple of triples) {
      const predicate = triple.predicate;

      if (this.isEntityReference(triple.object)) {
        // Relationship
        graph.addRelationship(triple.subject, triple.object, predicate, {
          from: triple.subject,
          to: triple.object,
        });
      } else {
        // Property
        const entity = graph.getEntity(triple.subject);
        if (entity) {
          entity.properties[predicate] = triple.object;
        }
      }
    }
  }

  /**
   * Load JSON-LD document
   */
  loadJsonLd(doc: JsonLdDocument, graph: GraphStore): void {
    const triples: Triple[] = [];

    if (doc['@graph'] && Array.isArray(doc['@graph'])) {
      for (const node of doc['@graph']) {
        this.extractTriplesFromNode(node, triples);
      }
    } else {
      this.extractTriplesFromNode(doc, triples);
    }

    this.loadTriples(triples, graph);
  }

  /**
   * Load RDF/XML-style object (minimal)
   */
  loadRdfObject(rdfObj: Record<string, unknown>, graph: GraphStore): void {
    const triples: Triple[] = [];

    for (const [key, value] of Object.entries(rdfObj)) {
      if (key === '@id' || key === '@context') continue;

      const subject = rdfObj['@id'] as string;
      if (!subject) continue;

      if (typeof value === 'string') {
        triples.push({
          subject,
          predicate: key,
          object: value,
        });
      } else if (typeof value === 'object' && value !== null && '@id' in value) {
        triples.push({
          subject,
          predicate: key,
          object: (value as Record<string, unknown>)['@id'] as string,
        });
      }
    }

    this.loadTriples(triples, graph);
  }

  /**
   * Export graph as RDF triples
   */
  exportAsTriples(graph: GraphStore): Triple[] {
    return graph.toTriples();
  }

  /**
   * Export graph as JSON-LD
   */
  exportAsJsonLd(graph: GraphStore): JsonLdDocument {
    const triples = graph.toTriples();
    const nodeMap = new Map<string, Record<string, unknown>>();

    for (const triple of triples) {
      if (!nodeMap.has(triple.subject)) {
        nodeMap.set(triple.subject, { '@id': triple.subject });
      }

      const node = nodeMap.get(triple.subject)!;
      if (Array.isArray(node[triple.predicate])) {
        (node[triple.predicate] as unknown[]).push(triple.object);
      } else if (triple.predicate in node) {
        node[triple.predicate] = [node[triple.predicate], triple.object];
      } else {
        node[triple.predicate] = triple.object;
      }
    }

    return {
      '@context': { '@vocab': 'http://schema.org/' },
      '@graph': Array.from(nodeMap.values()),
    };
  }

  /**
   * Extract triples from JSON-LD node
   */
  private extractTriplesFromNode(node: Record<string, unknown>, triples: Triple[]): void {
    const subject = node['@id'] as string;
    if (!subject) return;

    for (const [key, value] of Object.entries(node)) {
      if (key === '@id' || key === '@type' || key === '@context') continue;

      if (Array.isArray(value)) {
        for (const item of value) {
          this.addTripleFromValue(subject, key, item, triples);
        }
      } else {
        this.addTripleFromValue(subject, key, value, triples);
      }
    }
  }

  /**
   * Add triple from value
   */
  private addTripleFromValue(subject: string, predicate: string, value: unknown, triples: Triple[]): void {
    if (value === null || value === undefined) return;

    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      triples.push({
        subject,
        predicate,
        object: String(value),
      });
    } else if (typeof value === 'object' && '@id' in (value as Record<string, unknown>)) {
      triples.push({
        subject,
        predicate,
        object: (value as Record<string, unknown>)['@id'] as string,
      });
    }
  }

  /**
   * Extract label from entity ID
   */
  private extractLabel(id: string): string {
    const parts = id.split(/[#/]/);
    return parts[parts.length - 1];
  }

  /**
   * Check if value looks like an entity reference (IRI or ID)
   */
  private isEntityReference(value: string): boolean {
    return value.startsWith('http') || value.includes(':') || value.startsWith('#');
  }

  /**
   * Create embeddings from knowledge graph using simple hashing
   */
  createEmbeddingsFromGraph(graph: GraphStore, dimension: number = 128): Map<string, SuperBitTensor> {
    const embeddings = new Map<string, SuperBitTensor>();

    for (const entity of graph.getStats() as any) {
      // This is a simplified version - in real implementation would be more sophisticated
      const bits = this.hashToEmbedding(entity.id, dimension);
      embeddings.set(entity.id, {
        dimensions: dimension,
        bits,
        metadata: {
          entityId: entity.id,
          type: 'knowledge_graph_embedding',
        },
      });
    }

    return embeddings;
  }

  /**
   * Hash text to embedding
   */
  private hashToEmbedding(text: string, dimension: number): Uint8Array {
    const bits = new Uint8Array(dimension);

    for (let i = 0; i < dimension; i++) {
      let hash = 0;
      for (let j = 0; j < text.length; j++) {
        const char = text.charCodeAt(j);
        hash = ((hash << 5) - hash) + char + i;
        hash |= 0;
      }
      bits[i] = Math.abs(hash) % 256;
    }

    return bits;
  }
}
