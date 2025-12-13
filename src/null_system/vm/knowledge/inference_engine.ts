/**
 * Inference engine for rule-based reasoning over knowledge graphs
 * Supports forward chaining, backward chaining, and probabilistic inference
 */

import { GraphStore, Entity, Relationship } from './graph_store';

export interface Rule {
  id: string;
  name: string;
  condition: RuleCondition[];
  conclusion: RuleConclusion;
  weight?: number; // Confidence weight [0, 1]
}

export interface RuleCondition {
  type: 'entity' | 'relationship' | 'property';
  entityType?: string;
  relationshipType?: string;
  property?: string;
  value?: unknown;
  operator?: string; // '=', '!=', '>', '<', 'contains', etc.
}

export interface RuleConclusion {
  type: 'assert_entity' | 'assert_relationship' | 'set_property';
  entityType?: string;
  relationshipType?: string;
  property?: string;
  value?: unknown;
}

export interface InferenceResult {
  ruleId: string;
  confidence: number;
  newFacts: Array<{ type: string; data: unknown }>;
  timestamp: number;
}

export class InferenceEngine {
  private rules: Map<string, Rule> = new Map();
  private nextRuleId: number = 0;
  private inferenceResults: InferenceResult[] = [];

  /**
   * Add inference rule
   */
  addRule(rule: Omit<Rule, 'id'>): string {
    const id = `rule_${this.nextRuleId++}`;
    const fullRule: Rule = { ...rule, id, weight: rule.weight || 0.9 };
    this.rules.set(id, fullRule);
    return id;
  }

  /**
   * Get rule by ID
   */
  getRule(id: string): Rule | undefined {
    return this.rules.get(id);
  }

  /**
   * Get all rules
   */
  getAllRules(): Rule[] {
    return Array.from(this.rules.values());
  }

  /**
   * Execute forward chaining inference
   */
  forwardChain(graph: GraphStore, iterations: number = 10): InferenceResult[] {
    const results: InferenceResult[] = [];
    let round = 0;

    while (round < iterations) {
      const roundResults: InferenceResult[] = [];
      let newFactsAdded = false;

      for (const rule of this.rules.values()) {
        const matches = this.findMatches(graph, rule);

        for (const matchSet of matches) {
          const result = this.applyRule(graph, rule, matchSet);
          if (result.newFacts.length > 0) {
            newFactsAdded = true;
            roundResults.push(result);
          }
        }
      }

      if (!newFactsAdded) {
        break;
      }

      results.push(...roundResults);
      round++;
    }

    this.inferenceResults.push(...results);
    return results;
  }

  /**
   * Execute backward chaining inference
   */
  backwardChain(graph: GraphStore, goal: { entityType?: string; relationshipType?: string }): InferenceResult[] {
    const results: InferenceResult[] = [];
    const visited = new Set<string>();

    const chain = (
      currentGoal: { entityType?: string; relationshipType?: string },
      depth: number
    ): InferenceResult[] => {
      if (depth > 10) return [];

      const key = `${currentGoal.entityType || ''}_${currentGoal.relationshipType || ''}`;
      if (visited.has(key)) return [];
      visited.add(key);

      const results: InferenceResult[] = [];

      for (const rule of this.rules.values()) {
        const matches = this.findMatches(graph, rule);

        for (const matchSet of matches) {
          const result = this.applyRule(graph, rule, matchSet);
          if (result.newFacts.length > 0) {
            results.push(result);

            // Recursively apply rules
            for (const newFact of result.newFacts) {
              if (newFact.type === 'entity' && typeof newFact.data === 'object') {
                const fact = newFact.data as { entityType?: string };
                if (fact.entityType) {
                  results.push(...chain({ entityType: fact.entityType }, depth + 1));
                }
              }
            }
          }
        }
      }

      return results;
    };

    return chain(goal, 0);
  }

  /**
   * Find entities matching conditions
   */
  private findMatches(graph: GraphStore, rule: Rule): Array<Map<string, unknown>> {
    const matches: Array<Map<string, unknown>> = [];

    // Simple matching: find entities that satisfy conditions
    const conditions = rule.condition;
    if (conditions.length === 0) {
      matches.push(new Map());
      return matches;
    }

    const firstCondition = conditions[0];

    if (firstCondition.type === 'entity' && firstCondition.entityType) {
      const candidates = graph.getEntitiesByType(firstCondition.entityType);

      for (const entity of candidates) {
        const bindingMap = new Map<string, unknown>([['entity', entity]]);

        // Check remaining conditions
        let allMatch = true;
        for (let i = 1; i < conditions.length; i++) {
          const condition = conditions[i];
          if (!this.matchesCondition(graph, entity, condition)) {
            allMatch = false;
            break;
          }
        }

        if (allMatch) {
          matches.push(bindingMap);
        }
      }
    }

    return matches;
  }

  /**
   * Check if entity matches condition
   */
  private matchesCondition(graph: GraphStore, entity: Entity, condition: RuleCondition): boolean {
    if (condition.type === 'property' && condition.property) {
      const value = entity.properties[condition.property];
      if (condition.operator === '=') {
        return value === condition.value;
      } else if (condition.operator === '!=') {
        return value !== condition.value;
      } else if (condition.operator === '>') {
        return (value as number) > (condition.value as number);
      } else if (condition.operator === '<') {
        return (value as number) < (condition.value as number);
      } else if (condition.operator === 'contains') {
        return String(value).includes(String(condition.value));
      }
    } else if (condition.type === 'relationship' && condition.relationshipType) {
      const rels = graph.getOutgoingRelationships(entity.id, condition.relationshipType);
      return rels.length > 0;
    }

    return true;
  }

  /**
   * Apply rule to generate new facts
   */
  private applyRule(graph: GraphStore, rule: Rule, bindings: Map<string, unknown>): InferenceResult {
    const newFacts: Array<{ type: string; data: unknown }> = [];
    const conclusion = rule.conclusion;

    try {
      if (conclusion.type === 'assert_entity' && conclusion.entityType && conclusion.value) {
        const value = conclusion.value as Record<string, unknown>;
        const entity: Entity = {
          id: `inferred_${Date.now()}_${Math.random().toString(36).substring(7)}`,
          label: String(value.label || conclusion.entityType),
          type: conclusion.entityType,
          properties: { ...value },
        };

        graph.addEntity(entity);
        newFacts.push({ type: 'entity', data: entity });
      } else if (
        conclusion.type === 'assert_relationship' &&
        conclusion.relationshipType &&
        conclusion.value
      ) {
        const value = conclusion.value as { source: string; target: string };
        graph.addRelationship(value.source, value.target, conclusion.relationshipType);
        newFacts.push({ type: 'relationship', data: value });
      } else if (conclusion.type === 'set_property' && conclusion.property) {
        const entity = bindings.get('entity') as Entity | undefined;
        if (entity) {
          entity.properties[conclusion.property] = conclusion.value;
          newFacts.push({ type: 'property', data: { property: conclusion.property, value: conclusion.value } });
        }
      }
    } catch (error) {
      // Ignore errors in inference
    }

    return {
      ruleId: rule.id,
      confidence: rule.weight || 0.9,
      newFacts,
      timestamp: Date.now(),
    };
  }

  /**
   * Get inference history
   */
  getInferenceHistory(): InferenceResult[] {
    return [...this.inferenceResults];
  }

  /**
   * Clear all rules and history
   */
  clear(): void {
    this.rules.clear();
    this.inferenceResults = [];
    this.nextRuleId = 0;
  }
}
