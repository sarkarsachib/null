/**
 * Knowledge Graph module index - exports all KG components
 */

export { GraphStore, Entity, Relationship, Triple } from './graph_store';
export { OntologyManager, EntityType, RelationshipType, PropertyDefinition, OntologyConstraint } from './ontology_manager';
export { InferenceEngine, Rule, RuleCondition, RuleConclusion, InferenceResult } from './inference_engine';
export { RDFLoader, RDFTripleFormat, JsonLdDocument } from './rdf_loader';
