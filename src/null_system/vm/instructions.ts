/**
 * Instruction set for NullVM
 */

export enum OpCode {
  SET = 'SET',
  ADD = 'ADD',
  SHOW = 'SHOW',
  IF = 'IF',
  REPEAT = 'REPEAT',
  DEFINE = 'DEFINE',
  CALL = 'CALL',
  RETURN = 'RETURN',
  JMP = 'JMP',
  NOP = 'NOP',
  SECURE_ENC = 'SECURE_ENC',
  SECURE_DEC = 'SECURE_DEC',
  SECURE_EVAL = 'SECURE_EVAL',
  ZK_PROVE = 'ZK_PROVE',
  ZK_VERIFY = 'ZK_VERIFY',
  SMPC_SHARE = 'SMPC_SHARE',
  SMPC_COMBINE = 'SMPC_COMBINE',
  AI_EMBED = 'AI_EMBED',
  AI_LAYER = 'AI_LAYER',
  AI_ATTEND = 'AI_ATTEND',
  AI_FUZZY = 'AI_FUZZY',
  MATCH_TAG = 'MATCH_TAG',
  UNWRAP_UNION = 'UNWRAP_UNION',
  MATCH_PATTERN = 'MATCH_PATTERN',
  SPAWN_VM = 'SPAWN_VM',
  SEND_MSG = 'SEND_MSG',
  RECV_MSG = 'RECV_MSG',
  SYNC_BARRIER = 'SYNC_BARRIER',
}

export interface Instruction {
  opcode: OpCode;
  args: unknown[];
  lineno?: number;
}

export interface SetInstruction extends Instruction {
  opcode: OpCode.SET;
  args: [string, number]; // [register, value]
}

export interface AddInstruction extends Instruction {
  opcode: OpCode.ADD;
  args: [string, string | number]; // [register, register_or_value]
}

export interface ShowInstruction extends Instruction {
  opcode: OpCode.SHOW;
  args: [string]; // [register]
}

export interface IfInstruction extends Instruction {
  opcode: OpCode.IF;
  args: [string, string, unknown[]]; // [condition_register, operator, instructions]
}

export interface RepeatInstruction extends Instruction {
  opcode: OpCode.REPEAT;
  args: [string, unknown[]]; // [count_register, instructions]
}

export interface DefineInstruction extends Instruction {
  opcode: OpCode.DEFINE;
  args: [string, unknown[]]; // [function_name, instructions]
}

export interface CallInstruction extends Instruction {
  opcode: OpCode.CALL;
  args: [string]; // [function_name]
}

export interface ReturnInstruction extends Instruction {
  opcode: OpCode.RETURN;
  args: [];
}

export interface JmpInstruction extends Instruction {
  opcode: OpCode.JMP;
  args: [number]; // [target_address]
}

export interface SecureEncInstruction extends Instruction {
  opcode: OpCode.SECURE_ENC;
  args: [string, string]; // [register, keyId]
}

export interface SecureDecInstruction extends Instruction {
  opcode: OpCode.SECURE_DEC;
  args: [string, string]; // [register, keyId]
}

export interface SecureEvalInstruction extends Instruction {
  opcode: OpCode.SECURE_EVAL;
  args: [string, string, string]; // [operation, sourceReg, destReg]
}

export interface ZKProveInstruction extends Instruction {
  opcode: OpCode.ZK_PROVE;
  args: [string]; // [traceId]
}

export interface ZKVerifyInstruction extends Instruction {
  opcode: OpCode.ZK_VERIFY;
  args: [string, string]; // [proofId, expectedDigestId]
}

export interface SMPCShareInstruction extends Instruction {
  opcode: OpCode.SMPC_SHARE;
  args: [string, number]; // [secretId, threshold]
}

export interface SMPCCombineInstruction extends Instruction {
  opcode: OpCode.SMPC_COMBINE;
  args: [string, string[]]; // [secretId, shareIds]
}

export interface AIEmbedInstruction extends Instruction {
  opcode: OpCode.AI_EMBED;
  args: [string, string, number]; // [outputRegister, embeddingId, dimension]
}

export interface AILayerInstruction extends Instruction {
  opcode: OpCode.AI_LAYER;
  args: [string, string, string, string]; // [inputRegister, outputRegister, layerConfig, activation]
}

export interface AIAttendInstruction extends Instruction {
  opcode: OpCode.AI_ATTEND;
  args: [string, string, string]; // [inputRegister, outputRegister, attentionConfig]
}

export interface AIFuzzyInstruction extends Instruction {
  opcode: OpCode.AI_FUZZY;
  args: [string, string, number]; // [inputRegister, outputRegister, uncertaintyReduction]
}

export interface MatchTagInstruction extends Instruction {
  opcode: OpCode.MATCH_TAG;
  args: [string]; // [tag]
}

export interface UnwrapUnionInstruction extends Instruction {
  opcode: OpCode.UNWRAP_UNION;
  args: [];
}

export interface MatchPatternInstruction extends Instruction {
  opcode: OpCode.MATCH_PATTERN;
  args: [string]; // [pattern_tag]
}

export function isValidOpCode(code: string): code is OpCode {
  return Object.values(OpCode).includes(code as OpCode);
}
