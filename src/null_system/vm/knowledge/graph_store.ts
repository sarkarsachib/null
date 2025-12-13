/**
 * Graph store for knowledge graph management
 * Stores entities, relationships, and properties in super-bit encoded format
 */

import { SuperBitTensor } from '../nlp/embedder';

export interface Entity {
  id: string;
  label: string;
  type: string;
  properties: Record<string, unknown>;
  embedding?: SuperBitTensor;
}

export interface Relationship {
  id: string;
  source: string;
  target: string;
  type: string;
  weight?: number;
  properties: Record<string, unknown>;
}

export interface Triple {
  subject: string;
  predicate: string;
  object: string;
}

export class GraphStore {
  private entities: Map<string, Entity> = new Map();
  private relationships: Map<string, Relationship> = new Map();
  private relationshipIndex: Map<string, Set<string>> = new Map(); // source -> set of relationship IDs
  private typeIndex: Map<string, Set<string>> = new Map(); // type -> set of entity IDs
  private nextRelationshipId: number = 0;

  /**
   * Add entity to graph
   */
  addEntity(entity: Entity): void {
    this.entities.set(entity.id, entity);

    if (!this.typeIndex.has(entity.type)) {
      this.typeIndex.set(entity.type, new Set());
    }
    this.typeIndex.get(entity.type)!.add(entity.id);
  }

  /**
   * Get entity by ID
   */
  getEntity(id: string): Entity | undefined {
    return this.entities.get(id);
  }

  /**
   * Get all entities of a type
   */
  getEntitiesByType(type: string): Entity[] {
    const ids = this.typeIndex.get(type);
    if (!ids) return [];
    return Array.from(ids).map(id => this.entities.get(id)!).filter(e => e !== undefined);
  }

  /**
   * Add relationship
   */
  addRelationship(source: string, target: string, type: string, properties: Record<string, unknown> = {}): string {
    if (!this.entities.has(source) || !this.entities.has(target)) {
      throw new Error(`Invalid relationship: source or target entity not found`);
    }

    const id = `rel_${this.nextRelationshipId++}`;
    const relationship: Relationship = {
      id,
      source,
      target,
      type,
      weight: 1.0,
      properties,
    };

    this.relationships.set(id, relationship);

    if (!this.relationshipIndex.has(source)) {
      this.relationshipIndex.set(source, new Set());
    }
    this.relationshipIndex.get(source)!.add(id);

    return id;
  }

  /**
   * Get relationship
   */
  getRelationship(id: string): Relationship | undefined {
    return this.relationships.get(id);
  }

  /**
   * Get relationships from entity
   */
  getOutgoingRelationships(entityId: string, type?: string): Relationship[] {
    const relIds = this.relationshipIndex.get(entityId);
    if (!relIds) return [];

    return Array.from(relIds)
      .map(id => this.relationships.get(id)!)
      .filter(rel => (type ? rel.type === type : true));
  }

  /**
   * Get incoming relationships to entity
   */
  getIncomingRelationships(entityId: string, type?: string): Relationship[] {
    const incoming: Relationship[] = [];

    for (const rel of this.relationships.values()) {
      if (rel.target === entityId && (type ? rel.type === type : true)) {
        incoming.push(rel);
      }
    }

    return incoming;
  }

  /**
   * Get all neighbors of an entity
   */
  getNeighbors(entityId: string): Entity[] {
    const neighbors = new Set<Entity>();

    const outgoing = this.getOutgoingRelationships(entityId);
    for (const rel of outgoing) {
      const entity = this.getEntity(rel.target);
      if (entity) neighbors.add(entity);
    }

    const incoming = this.getIncomingRelationships(entityId);
    for (const rel of incoming) {
      const entity = this.getEntity(rel.source);
      if (entity) neighbors.add(entity);
    }

    return Array.from(neighbors);
  }

  /**
   * Find path between two entities
   */
  findPath(sourceId: string, targetId: string, maxDepth: number = 5): Relationship[] | null {
    if (sourceId === targetId) return [];

    const visited = new Set<string>();
    const queue: Array<{ id: string; path: Relationship[] }> = [{ id: sourceId, path: [] }];

    while (queue.length > 0) {
      const { id, path } = queue.shift()!;

      if (visited.has(id) || path.length > maxDepth) {
        continue;
      }

      visited.add(id);

      const outgoing = this.getOutgoingRelationships(id);
      for (const rel of outgoing) {
        if (rel.target === targetId) {
          return [...path, rel];
        }

        queue.push({ id: rel.target, path: [...path, rel] });
      }
    }

    return null;
  }

  /**
   * Convert to RDF triples
   */
  toTriples(): Triple[] {
    const triples: Triple[] = [];

    for (const entity of this.entities.values()) {
      for (const [key, value] of Object.entries(entity.properties)) {
        if (value !== null && value !== undefined) {
          triples.push({
            subject: entity.id,
            predicate: key,
            object: String(value),
          });
        }
      }
    }

    for (const rel of this.relationships.values()) {
      triples.push({
        subject: rel.source,
        predicate: rel.type,
        object: rel.target,
      });

      for (const [key, value] of Object.entries(rel.properties)) {
        if (value !== null && value !== undefined) {
          triples.push({
            subject: rel.id,
            predicate: key,
            object: String(value),
          });
        }
      }
    }

    return triples;
  }

  /**
   * Get graph statistics
   */
  getStats(): Record<string, unknown> {
    return {
      entityCount: this.entities.size,
      relationshipCount: this.relationships.size,
      typeCount: this.typeIndex.size,
      averageDegree: this.relationships.size / Math.max(1, this.entities.size),
      types: Array.from(this.typeIndex.keys()),
    };
  }

  /**
   * Clear all data
   */
  clear(): void {
    this.entities.clear();
    this.relationships.clear();
    this.relationshipIndex.clear();
    this.typeIndex.clear();
    this.nextRelationshipId = 0;
  }
}
