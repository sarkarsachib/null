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

export interface SpawnVMInstruction extends Instruction {
  opcode: OpCode.SPAWN_VM;
  args: [string, unknown]; // [vm_id, config]
}

export interface SendMsgInstruction extends Instruction {
  opcode: OpCode.SEND_MSG;
  args: [string, string, unknown]; // [target_vm_id, message_type, payload]
}

export interface RecvMsgInstruction extends Instruction {
  opcode: OpCode.RECV_MSG;
  args: [string, number?]; // [result_register, timeout_ms?]
}

export interface SyncBarrierInstruction extends Instruction {
  opcode: OpCode.SYNC_BARRIER;
  args: [string, number?]; // [barrier_id, timeout_ms?]
}

export function isValidOpCode(code: string): code is OpCode {
  return Object.values(OpCode).includes(code as OpCode);
}
