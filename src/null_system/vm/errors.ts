/**
 * Error types for NullVM execution
 */

export enum ErrorType {
  InvalidInstruction = 'INVALID_INSTRUCTION',
  InvalidRegister = 'INVALID_REGISTER',
  StackUnderflow = 'STACK_UNDERFLOW',
  StackOverflow = 'STACK_OVERFLOW',
  HeapOutOfBounds = 'HEAP_OUT_OF_BOUNDS',
  DivisionByZero = 'DIVISION_BY_ZERO',
  UndefinedFunction = 'UNDEFINED_FUNCTION',
  InvalidProgram = 'INVALID_PROGRAM',
  ExecutionError = 'EXECUTION_ERROR',
  IllegalState = 'ILLEGAL_STATE',
  EncryptionError = 'ENCRYPTION_ERROR',
  DecryptionError = 'DECRYPTION_ERROR',
  KeyError = 'KEY_ERROR',
  ProofError = 'PROOF_ERROR',
  SMPCError = 'SMPC_ERROR',
  ChannelError = 'CHANNEL_ERROR',
}

export class VMError extends Error {
  constructor(
    public type: ErrorType,
    public message: string,
    public context?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'VMError';
  }

  toJSON() {
    return {
      name: this.name,
      type: this.type,
      message: this.message,
      context: this.context,
    };
  }
}

export function createError(
  type: ErrorType,
  message: string,
  context?: Record<string, unknown>
): VMError {
  return new VMError(type, message, context);
}
