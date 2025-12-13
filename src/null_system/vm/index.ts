/**
 * NullVM module exports
 */

export { NullVM, NullVMConfig, ExecutionHook } from './null_vm';
export { Memory } from './memory';
export { ExecutionContext, StackFrame, TraceHook } from './execution_context';
export { Decoder, SuperBitProgram } from './decoder';
export { BinaryBridge, BinaryFrame } from './binary_bridge';
export { FuzzyBitEvaluator, FuzzyBitConfig } from './fuzzy_bits';
export {
  Instruction,
  OpCode,
  SetInstruction,
  AddInstruction,
  ShowInstruction,
  IfInstruction,
  RepeatInstruction,
  DefineInstruction,
  CallInstruction,
  ReturnInstruction,
  JmpInstruction,
  NLPTokenizeInstruction,
  NLPEmbedInstruction,
  NLPTranslateInstruction,
  KGLoadInstruction,
  KGQueryInstruction,
  KGReasonInstruction,
  isValidOpCode,
} from './instructions';
export { VMError, ErrorType, createError } from './errors';

// NLP Module
export { Tokenizer, Token, TokenizeOptions } from './nlp/tokenizer';
export { Embedder, SuperBitTensor, EmbeddingResult, TranslationResult } from './nlp/embedder';
export { CodegenAdapter, CodeGenerationRequest, GeneratedCode } from './nlp/codegen_adapter';

// Knowledge Graph Module
export { GraphStore, Entity, Relationship, Triple } from './knowledge/graph_store';
export { OntologyManager, EntityType, RelationshipType, PropertyDefinition, OntologyConstraint } from './knowledge/ontology_manager';
export { InferenceEngine, Rule, RuleCondition, RuleConclusion, InferenceResult } from './knowledge/inference_engine';
export { RDFLoader, RDFTripleFormat, JsonLdDocument } from './knowledge/rdf_loader';

export {
  HybridExecutionManager,
  HybridExecutionConfig,
  WorkScheduler,
  WorkItem,
  LoadBalancingStrategy,
  SuperBitMessageBus,
  MessageBusConfig,
  TransportAdapter,
  BaseTransportAdapter,
  SuperBitMessage,
  VMCapabilities,
  HealthStatus,
  MessageHandler,
  HealthCallback,
  FaultCallback,
  WorkerThreadAdapter,
} from './hybrid_runtime';
export {
  StateSnapshot,
  ReplayLog,
  FaultToleranceManager,
  VMSnapshot,
  ReplayLogEntry,
  CheckpointData,
} from './fault_tolerance';
export { WorkStealingScheduler, ScheduledTask, WorkerMetrics, SchedulerMetrics } from './scheduler';
export { DistributedExecutor, DistributedExecutorConfig, ExecutionResult } from './distributed';
