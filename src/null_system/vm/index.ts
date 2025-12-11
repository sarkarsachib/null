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
  isValidOpCode,
} from './instructions';
export { VMError, ErrorType, createError } from './errors';
