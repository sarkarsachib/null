/**
 * NullVM module exports
 */

export { NullVM, NullVMConfig } from './null_vm';
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
  AIEmbedInstruction,
  AILayerInstruction,
  AIAttendInstruction,
  AIFuzzyInstruction,
  isValidOpCode,
} from './instructions';
export { VMError, ErrorType, createError } from './errors';
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
  SuperBitTensor,
  TensorShape,
  TensorMetadata,
  EmbeddingRegistry,
  EmbeddingEntry,
  EmbeddingMetadata,
  NeuralEngine,
  DenseLayer,
  LayerConfig,
  AttentionModule,
  AttentionConfig,
} from './ai';
