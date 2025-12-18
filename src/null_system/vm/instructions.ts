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

  // Security
  SECURE_ENC = 'SECURE_ENC',
  SECURE_DEC = 'SECURE_DEC',
  SECURE_EVAL = 'SECURE_EVAL',
  ZK_PROVE = 'ZK_PROVE',
  ZK_VERIFY = 'ZK_VERIFY',
  SMPC_SHARE = 'SMPC_SHARE',
  SMPC_COMBINE = 'SMPC_COMBINE',

  // AI
  AI_EMBED = 'AI_EMBED',
  AI_LAYER = 'AI_LAYER',
  AI_ATTEND = 'AI_ATTEND',
  AI_FUZZY = 'AI_FUZZY',

  // Pattern matching
  MATCH_TAG = 'MATCH_TAG',
  UNWRAP_UNION = 'UNWRAP_UNION',
  MATCH_PATTERN = 'MATCH_PATTERN',

  // Hybrid runtime
  SPAWN_VM = 'SPAWN_VM',
  SEND_MSG = 'SEND_MSG',
  RECV_MSG = 'RECV_MSG',
  SYNC_BARRIER = 'SYNC_BARRIER',

  // Quantum
  Q_ALLOC = 'Q_ALLOC',
  Q_SUPERPOSE = 'Q_SUPERPOSE',
  Q_ENTANGLE = 'Q_ENTANGLE',
  Q_APPLY = 'Q_APPLY',
  Q_MEASURE = 'Q_MEASURE',

  // Distributed-first primitives
  DISTRIBUTED_ALLOC = 'DISTRIBUTED_ALLOC',
  CONSENSUS_WAIT = 'CONSENSUS_WAIT',
  PARTIAL_RESUME = 'PARTIAL_RESUME',

  // Observability
  OBSERVE_VALUE = 'OBSERVE_VALUE',
  TRACE_REPLAY = 'TRACE_REPLAY',

  // Intent / constraints
  SET_INTENT = 'SET_INTENT',
  APPLY_CONSTRAINT = 'APPLY_CONSTRAINT',
  SET_DEADLINE = 'SET_DEADLINE',
  TIME_HINT = 'TIME_HINT',

  // Ownership and memory safety
  BORROW_IMM = 'BORROW_IMM',
  BORROW_MUT = 'BORROW_MUT',
  DROP = 'DROP',
  INC_REF = 'INC_REF',
  DEC_REF = 'DEC_REF',
  CHECK_BORROW = 'CHECK_BORROW',
}

export interface InstructionMetadata {
  eventually?: boolean;
  local?: boolean;
  deadlineMs?: number;
  deadlineAt?: number;
  intent?: string;
  timeHintMs?: number;
  [key: string]: unknown;
}

export interface Instruction {
  opcode: OpCode;
  args: unknown[];
  lineno?: number;
  metadata?: InstructionMetadata;
}

export interface SetInstruction extends Instruction {
  opcode: OpCode.SET;
  args: [string, number];
}

export interface AddInstruction extends Instruction {
  opcode: OpCode.ADD;
  args: [string, string | number];
}

export interface ShowInstruction extends Instruction {
  opcode: OpCode.SHOW;
  args: [string];
}

export interface IfInstruction extends Instruction {
  opcode: OpCode.IF;
  args: [string, string, unknown[]];
}

export interface RepeatInstruction extends Instruction {
  opcode: OpCode.REPEAT;
  args: [string, unknown[]];
}

export interface DefineInstruction extends Instruction {
  opcode: OpCode.DEFINE;
  args: [string, unknown[]];
}

export interface CallInstruction extends Instruction {
  opcode: OpCode.CALL;
  args: [string];
}

export interface ReturnInstruction extends Instruction {
  opcode: OpCode.RETURN;
  args: [];
}

export interface JmpInstruction extends Instruction {
  opcode: OpCode.JMP;
  args: [number];
}

export interface SecureEncInstruction extends Instruction {
  opcode: OpCode.SECURE_ENC;
  args: [string, string];
}

export interface SecureDecInstruction extends Instruction {
  opcode: OpCode.SECURE_DEC;
  args: [string, string];
}

export interface SecureEvalInstruction extends Instruction {
  opcode: OpCode.SECURE_EVAL;
  args: [string, string, string];
}

export interface ZKProveInstruction extends Instruction {
  opcode: OpCode.ZK_PROVE;
  args: [string];
}

export interface ZKVerifyInstruction extends Instruction {
  opcode: OpCode.ZK_VERIFY;
  args: [string, string];
}

export interface SMPCShareInstruction extends Instruction {
  opcode: OpCode.SMPC_SHARE;
  args: [string, number];
}

export interface SMPCCombineInstruction extends Instruction {
  opcode: OpCode.SMPC_COMBINE;
  args: [string, string[]];
}

export interface AIEmbedInstruction extends Instruction {
  opcode: OpCode.AI_EMBED;
  args: [string, string, number];
}

export interface AILayerInstruction extends Instruction {
  opcode: OpCode.AI_LAYER;
  args: [string, string, string, string];
}

export interface AIAttendInstruction extends Instruction {
  opcode: OpCode.AI_ATTEND;
  args: [string, string, string];
}

export interface AIFuzzyInstruction extends Instruction {
  opcode: OpCode.AI_FUZZY;
  args: [string, string, number];
}

export interface MatchTagInstruction extends Instruction {
  opcode: OpCode.MATCH_TAG;
  args: [string];
}

export interface UnwrapUnionInstruction extends Instruction {
  opcode: OpCode.UNWRAP_UNION;
  args: [];
}

export interface MatchPatternInstruction extends Instruction {
  opcode: OpCode.MATCH_PATTERN;
  args: [string];
}

export function isValidOpCode(code: string): code is OpCode {
  return Object.values(OpCode).includes(code as OpCode);
}
