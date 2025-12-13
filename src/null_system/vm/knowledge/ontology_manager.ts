/**
 * Ontology manager for managing entity types, relationships types, and constraints
 */

export interface EntityType {
  name: string;
  parent?: string;
  properties: Record<string, PropertyDefinition>;
  description?: string;
}

export interface PropertyDefinition {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  required?: boolean;
  description?: string;
  default?: unknown;
}

export interface RelationshipType {
  name: string;
  sourceType: string;
  targetType: string;
  inverseOf?: string;
  description?: string;
}

export interface OntologyConstraint {
  id: string;
  type: 'cardinality' | 'domain' | 'range' | 'functional' | 'inverse';
  definition: Record<string, unknown>;
}

export class OntologyManager {
  private entityTypes: Map<string, EntityType> = new Map();
  private relationshipTypes: Map<string, RelationshipType> = new Map();
  private constraints: Map<string, OntologyConstraint> = new Map();
  private nextConstraintId: number = 0;

  /**
   * Define entity type
   */
  defineEntityType(entityType: EntityType): void {
    this.entityTypes.set(entityType.name, entityType);
  }

  /**
   * Get entity type
   */
  getEntityType(name: string): EntityType | undefined {
    return this.entityTypes.get(name);
  }

  /**
   * Check if entity type exists
   */
  hasEntityType(name: string): boolean {
    return this.entityTypes.has(name);
  }

  /**
   * Define relationship type
   */
  defineRelationshipType(relType: RelationshipType): void {
    this.relationshipTypes.set(relType.name, relType);
  }

  /**
   * Get relationship type
   */
  getRelationshipType(name: string): RelationshipType | undefined {
    return this.relationshipTypes.get(name);
  }

  /**
   * Check if relationship type exists
   */
  hasRelationshipType(name: string): boolean {
    return this.relationshipTypes.has(name);
  }

  /**
   * Add constraint
   */
  addConstraint(constraint: OntologyConstraint): string {
    const id = constraint.id || `constraint_${this.nextConstraintId++}`;
    this.constraints.set(id, { ...constraint, id });
    return id;
  }

  /**
   * Get constraints
   */
  getConstraints(type?: string): OntologyConstraint[] {
    const all = Array.from(this.constraints.values());
    return type ? all.filter(c => c.type === type) : all;
  }

  /**
   * Validate entity against type
   */
  validateEntity(entityType: string, properties: Record<string, unknown>): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    const type = this.getEntityType(entityType);
    if (!type) {
      return { valid: false, errors: [`Entity type '${entityType}' not defined`] };
    }

    for (const [propName, propDef] of Object.entries(type.properties)) {
      if (propDef.required && !(propName in properties)) {
        errors.push(`Required property '${propName}' missing from ${entityType}`);
      }

      if (propName in properties) {
        const value = properties[propName];
        if (typeof value !== propDef.type) {
          errors.push(`Property '${propName}' has wrong type: expected ${propDef.type}, got ${typeof value}`);
        }
      }
    }

    return { valid: errors.length === 0, errors };
  }

  /**
   * Get ontology hierarchy
   */
  getHierarchy(entityType: string): EntityType[] {
    const hierarchy: EntityType[] = [];
    let current: EntityType | undefined = this.getEntityType(entityType);

    while (current) {
      hierarchy.push(current);
      current = current.parent ? this.getEntityType(current.parent) : undefined;
    }

    return hierarchy;
  }

  /**
   * Get all subtypes of an entity type
   */
  getSubtypes(entityType: string): EntityType[] {
    const subtypes: EntityType[] = [];

    for (const type of this.entityTypes.values()) {
      if (type.parent === entityType) {
        subtypes.push(type);
        subtypes.push(...this.getSubtypes(type.name));
      }
    }

    return subtypes;
  }

  /**
   * Export ontology as JSON-LD
   */
  exportAsJsonLd(): Record<string, unknown> {
    const context: Record<string, unknown> = {
      '@context': {
        '@vocab': 'http://schema.org/',
      },
      '@graph': [],
    };

    const graph: Array<Record<string, unknown>> = [];

    for (const [name, type] of this.entityTypes.entries()) {
      graph.push({
        '@id': `#${name}`,
        '@type': 'rdfs:Class',
        'rdfs:label': name,
        'rdfs:comment': type.description || '',
      });
    }

    for (const [name, relType] of this.relationshipTypes.entries()) {
      graph.push({
        '@id': `#${name}`,
        '@type': 'rdf:Property',
        'rdfs:label': name,
        'rdfs:domain': relType.sourceType,
        'rdfs:range': relType.targetType,
      });
    }

    return { ...context, '@graph': graph };
  }

  /**
   * Clear ontology
   */
  clear(): void {
    this.entityTypes.clear();
    this.relationshipTypes.clear();
    this.constraints.clear();
    this.nextConstraintId = 0;
  }
}
