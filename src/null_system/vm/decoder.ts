/**
 * Decoder for super-bit programs - translates to intermediate instruction set
 */

import { Instruction, OpCode, isValidOpCode } from './instructions';
import { createError, ErrorType } from './errors';

export interface SuperBitProgram {
  instructions: unknown[];
}

export class Decoder {
  /**
   * Decode a super-bit program into intermediate instructions
   */
  decode(program: SuperBitProgram | unknown[]): Instruction[] {
    const instructions = Array.isArray(program) ? program : program.instructions;

    if (!Array.isArray(instructions)) {
      throw createError(ErrorType.InvalidProgram, 'Program must be an array of instructions', {
        received: typeof instructions,
      });
    }

    return instructions.map((instr, lineno) => this.decodeInstruction(instr, lineno));
  }

  /**
   * Decode a single instruction
   */
  private decodeInstruction(instr: unknown, lineno: number): Instruction {
    if (!instr || typeof instr !== 'object' || Array.isArray(instr)) {
      throw createError(ErrorType.InvalidInstruction, 'Instruction must be an object', {
        lineno,
        received: typeof instr,
      });
    }

    const obj = instr as Record<string, unknown>;
    const opcode = obj.opcode;

    if (typeof opcode !== 'string' || !isValidOpCode(opcode)) {
      throw createError(ErrorType.InvalidInstruction, `Invalid opcode: ${opcode}`, {
        lineno,
        opcode,
      });
    }

    const args = Array.isArray(obj.args) ? obj.args : [];

    // Validate instruction based on opcode
    this.validateInstruction(opcode, args, lineno);

    return {
      opcode,
      args,
      lineno,
    } as Instruction;
  }

  /**
   * Validate instruction arguments
   */
  private validateInstruction(opcode: string, args: unknown[], lineno: number): void {
    switch (opcode) {
      case OpCode.SET:
        if (args.length < 2 || typeof args[0] !== 'string' || typeof args[1] !== 'number') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SET requires two arguments: register (string) and value (number)',
            { lineno, args }
          );
        }
        break;

      case OpCode.ADD:
        if (
          args.length < 2 ||
          typeof args[0] !== 'string' ||
          (typeof args[1] !== 'number' && typeof args[1] !== 'string')
        ) {
          throw createError(
            ErrorType.InvalidInstruction,
            'ADD requires two arguments: register (string) and value (number or string)',
            { lineno, args }
          );
        }
        break;

      case OpCode.SHOW:
        if (args.length < 1 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SHOW requires one argument: register (string)',
            { lineno, args }
          );
        }
        break;

      case OpCode.IF:
        if (
          args.length < 3 ||
          typeof args[0] !== 'string' ||
          typeof args[1] !== 'string' ||
          !Array.isArray(args[2])
        ) {
          throw createError(
            ErrorType.InvalidInstruction,
            'IF requires three arguments: register (string), operator (string), and instructions (array)',
            { lineno, args }
          );
        }
        break;

      case OpCode.REPEAT:
        if (args.length < 2 || typeof args[0] !== 'string' || !Array.isArray(args[1])) {
          throw createError(
            ErrorType.InvalidInstruction,
            'REPEAT requires two arguments: count_register (string) and instructions (array)',
            { lineno, args }
          );
        }
        break;

      case OpCode.DEFINE:
        if (args.length < 2 || typeof args[0] !== 'string' || !Array.isArray(args[1])) {
          throw createError(
            ErrorType.InvalidInstruction,
            'DEFINE requires two arguments: function_name (string) and instructions (array)',
            { lineno, args }
          );
        }
        break;

      case OpCode.CALL:
        if (args.length < 1 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'CALL requires one argument: function_name (string)',
            { lineno, args }
          );
        }
        break;

      case OpCode.RETURN:
      case OpCode.NOP:
        // No arguments required
        break;

      case OpCode.JMP:
        if (args.length < 1 || typeof args[0] !== 'number') {
          throw createError(
            ErrorType.InvalidInstruction,
            'JMP requires one argument: target_address (number)',
            { lineno, args }
          );
        }
        break;

      case OpCode.SECURE_ENC:
      case OpCode.SECURE_DEC:
        if (args.length < 2 || typeof args[0] !== 'string' || typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SECURE_ENC/SECURE_DEC requires two arguments: register (string) and key_id (string)',
            { lineno, args }
          );
        }
        break;

      case OpCode.SECURE_EVAL:
        if (
          args.length < 3 ||
          typeof args[0] !== 'string' ||
          typeof args[1] !== 'string' ||
          typeof args[2] !== 'string'
        ) {
          throw createError(
            ErrorType.InvalidInstruction,
            'SECURE_EVAL requires three arguments: operation (string), source_register (string), dest_register (string)',
            { lineno, args }
          );
        }
        break;

      case OpCode.ZK_PROVE:
        if (args.length < 1 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'ZK_PROVE requires one argument: trace_id (string)',
            { lineno, args }
          );
        }
        break;

      case OpCode.ZK_VERIFY:
        if (args.length < 2 || typeof args[0] !== 'string' || typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'ZK_VERIFY requires two arguments: proof_id (string) and digest_id (string)',
            { lineno, args }
          );
        }
        break;

      case OpCode.SMPC_SHARE:
        if (args.length < 2 || typeof args[0] !== 'string' || typeof args[1] !== 'number') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SMPC_SHARE requires two arguments: secret_id (string) and threshold (number)',
            { lineno, args }
          );
        }
        break;

      case OpCode.SMPC_COMBINE:
        if (args.length < 2 || typeof args[0] !== 'string' || !Array.isArray(args[1])) {
          throw createError(
            ErrorType.InvalidInstruction,
            'SMPC_COMBINE requires two arguments: secret_id (string) and share_ids (array)',
            { lineno, args }
          );
        }
        break;

      case OpCode.AI_EMBED:
        if (
          args.length < 3 ||
          typeof args[0] !== 'string' ||
          typeof args[1] !== 'string' ||
          typeof args[2] !== 'number'
        ) {
          throw createError(
            ErrorType.InvalidInstruction,
            'AI_EMBED requires three arguments: output_register (string), embedding_id (string), dimension (number)',
            { lineno, args }
          );
        }
        break;

      case OpCode.AI_LAYER:
        if (
          args.length < 4 ||
          typeof args[0] !== 'string' ||
          typeof args[1] !== 'string' ||
          typeof args[2] !== 'string' ||
          typeof args[3] !== 'string'
        ) {
          throw createError(
            ErrorType.InvalidInstruction,
            'AI_LAYER requires four arguments: input_register (string), output_register (string), layer_config (string), activation (string)',
            { lineno, args }
          );
        }
        break;

      case OpCode.AI_ATTEND:
        if (
          args.length < 3 ||
          typeof args[0] !== 'string' ||
          typeof args[1] !== 'string' ||
          typeof args[2] !== 'string'
        ) {
          throw createError(
            ErrorType.InvalidInstruction,
            'AI_ATTEND requires three arguments: input_register (string), output_register (string), attention_config (string)',
            { lineno, args }
          );
        }
        break;

      case OpCode.AI_FUZZY:
        if (
          args.length < 3 ||
          typeof args[0] !== 'string' ||
          typeof args[1] !== 'string' ||
          typeof args[2] !== 'number'
        ) {
          throw createError(
            ErrorType.InvalidInstruction,
            'AI_FUZZY requires three arguments: input_register (string), output_register (string), uncertainty_reduction (number)',
            { lineno, args }
          );
        }
        break;

      case OpCode.SPAWN_VM:
        if (args.length < 2 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SPAWN_VM requires at least two arguments: vm_id (string) and config (object)',
            { lineno, args }
          );
        }
        break;

      case OpCode.SEND_MSG:
        if (args.length < 3 || typeof args[0] !== 'string' || typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SEND_MSG requires at least three arguments: target_vm_id (string), message_type (string), payload',
            { lineno, args }
          );
        }
        break;

      case OpCode.RECV_MSG:
        if (args.length < 2 || typeof args[0] !== 'string' || typeof args[1] !== 'number') {
          throw createError(
            ErrorType.InvalidInstruction,
            'RECV_MSG requires two arguments: output_register (string), timeout_ms (number)',
            { lineno, args }
          );
        }
        break;

      case OpCode.SYNC_BARRIER:
        if (args.length < 2 || typeof args[0] !== 'string' || typeof args[1] !== 'number') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SYNC_BARRIER requires two arguments: barrier_id (string), timeout_ms (number)',
            { lineno, args }
          );
        }
        break;

      default:
        throw createError(ErrorType.InvalidInstruction, `Unknown opcode: ${opcode}`, {
          lineno,
          opcode,
        });
    }
  }
}
