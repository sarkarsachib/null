/**
 * Security module - cryptographic primitives for privacy-preserving computation
 */

export {
  HomomorphicEngine,
  type EncryptedValue,
  type EncryptionKeyPair,
  type TensorData,
} from './homomorphic_engine';
export {
  SecureChannel,
  type KeyExchangeMessage,
  type AuthenticatedMessage,
  type ChannelConfig,
} from './secure_channel';
export { ZKProofSystem, type ExecutionTrace, type StatementRecord, type ZKProof } from './zkp';
export {
  SMPCOrchestrator,
  type SecretShare,
  type SharedSecret,
  type SMPCConfig,
} from './smpc_orchestrator';
