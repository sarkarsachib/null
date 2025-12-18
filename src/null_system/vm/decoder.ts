/**
 * Decoder for super-bit programs - translates to intermediate instruction set
 */

import { Instruction, InstructionMetadata, OpCode, isValidOpCode } from './instructions';
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

    const rawArgs = Array.isArray(obj.args) ? obj.args : [];
    const metadata = this.decodeMetadata(obj, lineno);

    const args = this.normalizeArgs(opcode, rawArgs, lineno);

    const instruction: Instruction = {
      opcode,
      args,
      lineno,
      metadata,
    } as Instruction;
  }

  private decodeMetadata(obj: Record<string, unknown>, lineno: number): InstructionMetadata | undefined {
    const raw = obj.metadata ?? obj.meta;
    if (raw === undefined || raw === null) {
      return undefined;
    }

    if (typeof raw !== 'object' || Array.isArray(raw)) {
      throw createError(ErrorType.InvalidInstruction, 'metadata must be an object', {
        lineno,
        metadataType: typeof raw,
      });
    }

    return raw as InstructionMetadata;
  }

  private parseNumber(value: unknown, lineno: number, label: string): number {
    if (typeof value === 'number' && Number.isFinite(value)) {
      return value;
    }

    if (typeof value === 'string' && value.trim() !== '') {
      const parsed = Number(value);
      if (Number.isFinite(parsed)) {
        return parsed;
      }
    }

    throw createError(ErrorType.InvalidInstruction, `${label} must be a number`, {
      lineno,
      received: value,
    });
  }

  private normalizeArgs(opcode: OpCode, args: unknown[], lineno: number): unknown[] {
    switch (opcode) {
      case OpCode.SET: {
        if (args.length < 2 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SET requires two arguments: register (string) and value (number)',
            { lineno, args }
          );
        }
        const value = this.parseNumber(args[1], lineno, 'SET value');
        return [args[0], value];
      }

      case OpCode.ADD: {
        if (args.length < 2 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'ADD requires two arguments: register (string) and value (number or string)',
            { lineno, args }
          );
        }

        const operand = args[1];
        if (typeof operand === 'number') {
          return [args[0], operand];
        }

        if (typeof operand === 'string') {
          const parsed = Number(operand);
          if (operand.trim() !== '' && Number.isFinite(parsed)) {
            return [args[0], parsed];
          }
          return [args[0], operand];
        }

        throw createError(
          ErrorType.InvalidInstruction,
          'ADD requires two arguments: register (string) and value (number or string)',
          { lineno, args }
        );
      }

      case OpCode.SHOW: {
        if (args.length < 1 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SHOW requires one argument: register (string)',
            { lineno, args }
          );
        }
        return [args[0]];
      }

      case OpCode.IF: {
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
        return [args[0], args[1], args[2]];
      }

      case OpCode.REPEAT: {
        if (args.length < 2 || typeof args[0] !== 'string' || !Array.isArray(args[1])) {
          throw createError(
            ErrorType.InvalidInstruction,
            'REPEAT requires two arguments: count_register (string) and instructions (array)',
            { lineno, args }
          );
        }
        return [args[0], args[1]];
      }

      case OpCode.DEFINE: {
        if (args.length < 2 || typeof args[0] !== 'string' || !Array.isArray(args[1])) {
          throw createError(
            ErrorType.InvalidInstruction,
            'DEFINE requires two arguments: function_name (string) and instructions (array)',
            { lineno, args }
          );
        }
        return [args[0], args[1]];
      }

      case OpCode.CALL: {
        if (args.length < 1 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'CALL requires one argument: function_name (string)',
            { lineno, args }
          );
        }
        return [args[0]];
      }

      case OpCode.RETURN:
      case OpCode.NOP:
      case OpCode.UNWRAP_UNION:
        return [];

      case OpCode.JMP: {
        if (args.length < 1) {
          throw createError(ErrorType.InvalidInstruction, 'JMP requires one argument: target_address', {
            lineno,
            args,
          });
        }
        const address = this.parseNumber(args[0], lineno, 'JMP target_address');
        return [address];
      }

      case OpCode.SECURE_ENC:
      case OpCode.SECURE_DEC: {
        if (args.length < 2 || typeof args[0] !== 'string' || typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SECURE_ENC/SECURE_DEC requires two arguments: register (string) and key_id (string)',
            { lineno, args }
          );
        }
        return [args[0], args[1]];
      }

      case OpCode.SECURE_EVAL: {
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
        return [args[0], args[1], args[2]];
      }

      case OpCode.ZK_PROVE: {
        if (args.length < 1 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'ZK_PROVE requires one argument: trace_id (string)',
            { lineno, args }
          );
        }
        return [args[0]];
      }

      case OpCode.ZK_VERIFY: {
        if (args.length < 2 || typeof args[0] !== 'string' || typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'ZK_VERIFY requires two arguments: proof_id (string) and expectedDigestId (string)',
            { lineno, args }
          );
        }
        return [args[0], args[1]];
      }

      case OpCode.SMPC_SHARE: {
        if (args.length < 2 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SMPC_SHARE requires two arguments: secret_id (string) and threshold (number)',
            { lineno, args }
          );
        }
        const threshold = this.parseNumber(args[1], lineno, 'SMPC_SHARE threshold');
        return [args[0], threshold];
      }

      case OpCode.SMPC_COMBINE: {
        if (args.length < 2 || typeof args[0] !== 'string' || !Array.isArray(args[1])) {
          throw createError(
            ErrorType.InvalidInstruction,
            'SMPC_COMBINE requires two arguments: secret_id (string) and share_ids (array)',
            { lineno, args }
          );
        }
        return [args[0], args[1]];
      }

      case OpCode.AI_EMBED: {
        if (args.length < 3 || typeof args[0] !== 'string' || typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'AI_EMBED requires three arguments: output_register (string), embedding_id (string), dimension (number)',
            { lineno, args }
          );
        }
        const dimension = this.parseNumber(args[2], lineno, 'AI_EMBED dimension');
        return [args[0], args[1], dimension];
      }

      case OpCode.AI_LAYER: {
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
        return [args[0], args[1], args[2], args[3]];
      }

      case OpCode.AI_ATTEND: {
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
        return [args[0], args[1], args[2]];
      }

      case OpCode.AI_FUZZY: {
        if (args.length < 3 || typeof args[0] !== 'string' || typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'AI_FUZZY requires three arguments: input_register (string), output_register (string), uncertainty_reduction (number)',
            { lineno, args }
          );
        }
        const uncertaintyReduction = this.parseNumber(args[2], lineno, 'AI_FUZZY uncertainty_reduction');
        return [args[0], args[1], uncertaintyReduction];
      }

      case OpCode.MATCH_TAG: {
        if (args.length < 1 || typeof args[0] !== 'string') {
          throw createError(ErrorType.InvalidInstruction, 'MATCH_TAG requires one argument: tag (string)', {
            lineno,
            args,
          });
        }
        return [args[0]];
      }

      case OpCode.MATCH_PATTERN: {
        if (args.length < 1 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'MATCH_PATTERN requires one argument: pattern_tag (string)',
            { lineno, args }
          );
        }
        return [args[0]];
      }

      case OpCode.SPAWN_VM: {
        if (args.length < 2 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SPAWN_VM requires at least two arguments: vm_id (string) and config (object)',
            { lineno, args }
          );
        }
        return args;
      }

      case OpCode.SEND_MSG: {
        if (args.length < 3 || typeof args[0] !== 'string' || typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SEND_MSG requires at least three arguments: target_vm_id (string), message_type (string), payload',
            { lineno, args }
          );
        }
        return args;
      }

      case OpCode.RECV_MSG: {
        if (args.length < 2 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'RECV_MSG requires two arguments: output_register (string), timeout_ms (number)',
            { lineno, args }
          );
        }
        const timeoutMs = this.parseNumber(args[1], lineno, 'RECV_MSG timeout_ms');
        return [args[0], timeoutMs];
      }

      case OpCode.SYNC_BARRIER: {
        if (args.length < 2 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SYNC_BARRIER requires two arguments: barrier_id (string), timeout_ms (number)',
            { lineno, args }
          );
        }
        const timeoutMs = this.parseNumber(args[1], lineno, 'SYNC_BARRIER timeout_ms');
        return [args[0], timeoutMs];
      }

      case OpCode.Q_ALLOC: {
        if (args.length < 1 || typeof args[0] !== 'string') {
          throw createError(ErrorType.InvalidInstruction, 'Q_ALLOC requires one argument: target_reg (string)', {
            lineno,
            args,
          });
        }
        return [args[0]];
      }

      case OpCode.Q_SUPERPOSE: {
        if (args.length < 1 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'Q_SUPERPOSE requires one argument: qubit_reg (string)',
            { lineno, args }
          );
        }
        return [args[0]];
      }

      case OpCode.Q_ENTANGLE: {
        if (args.length < 2 || typeof args[0] !== 'string' || typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'Q_ENTANGLE requires two arguments: control_reg (string), target_reg (string)',
            { lineno, args }
          );
        }
        return [args[0], args[1]];
      }

      case OpCode.Q_APPLY: {
        if (args.length < 2 || typeof args[0] !== 'string' || !Array.isArray(args[1])) {
          throw createError(
            ErrorType.InvalidInstruction,
            'Q_APPLY requires two arguments: gate_name (string), qubit_regs (string[])',
            { lineno, args }
          );
        }
        return [args[0], args[1]];
      }

      case OpCode.Q_MEASURE: {
        if (args.length < 2 || typeof args[0] !== 'string' || typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'Q_MEASURE requires two arguments: qubit_reg (string), dest_reg (string)',
            { lineno, args }
          );
        }
        return [args[0], args[1]];
      }

      case OpCode.DISTRIBUTED_ALLOC: {
        if (args.length < 1 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'DISTRIBUTED_ALLOC requires at least one argument: register (string)',
            { lineno, args }
          );
        }
        if (args.length >= 2 && args[1] !== undefined && typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'DISTRIBUTED_ALLOC second argument must be kind (string) if provided',
            { lineno, args }
          );
        }
        if (args.length >= 3 && args[2] !== undefined && (typeof args[2] !== 'object' || Array.isArray(args[2]))) {
          throw createError(
            ErrorType.InvalidInstruction,
            'DISTRIBUTED_ALLOC third argument must be options (object) if provided',
            { lineno, args }
          );
        }
        return args;
      }

      case OpCode.CONSENSUS_WAIT: {
        if (args.length < 2 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'CONSENSUS_WAIT requires at least two arguments: register (string) and quorum (number)',
            { lineno, args }
          );
        }
        const quorum = this.parseNumber(args[1], lineno, 'CONSENSUS_WAIT quorum');
        const timeoutMs = args.length >= 3 ? this.parseNumber(args[2], lineno, 'CONSENSUS_WAIT timeout_ms') : 0;
        return [args[0], quorum, timeoutMs];
      }

      case OpCode.PARTIAL_RESUME: {
        if (args.length < 1 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'PARTIAL_RESUME requires at least one argument: register (string)',
            { lineno, args }
          );
        }
        if (args.length >= 2 && args[1] !== undefined && typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'PARTIAL_RESUME second argument must be mode (string) if provided',
            { lineno, args }
          );
        }
        return args;
      }

      case OpCode.OBSERVE_VALUE: {
        if (args.length < 1 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'OBSERVE_VALUE requires at least one argument: register (string)',
            { lineno, args }
          );
        }
        if (args.length >= 2 && args[1] !== undefined && typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'OBSERVE_VALUE second argument must be label (string) if provided',
            { lineno, args }
          );
        }
        return args;
      }

      case OpCode.TRACE_REPLAY: {
        if (args.length >= 1 && args[0] !== undefined && typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'TRACE_REPLAY first argument must be trace_id (string) if provided',
            { lineno, args }
          );
        }
        return args;
      }

      case OpCode.SET_INTENT: {
        if (args.length < 1 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SET_INTENT requires one argument: intent (string)',
            { lineno, args }
          );
        }
        return [args[0]];
      }

      case OpCode.APPLY_CONSTRAINT: {
        if (args.length < 3 || typeof args[0] !== 'string' || typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'APPLY_CONSTRAINT requires three arguments: register (string), operator (string), value (number)',
            { lineno, args }
          );
        }
        const value = this.parseNumber(args[2], lineno, 'APPLY_CONSTRAINT value');
        return [args[0], args[1], value];
      }

      case OpCode.SET_DEADLINE: {
        if (args.length < 1) {
          throw createError(
            ErrorType.InvalidInstruction,
            'SET_DEADLINE requires one argument: deadline_ms (number)',
            { lineno, args }
          );
        }
        const deadlineMs = this.parseNumber(args[0], lineno, 'SET_DEADLINE deadline_ms');
        return [deadlineMs];
      }

      case OpCode.TIME_HINT: {
        if (args.length < 1) {
          throw createError(
            ErrorType.InvalidInstruction,
            'TIME_HINT requires one argument: time_hint_ms (number)',
            { lineno, args }
          );
        }
        const timeHintMs = this.parseNumber(args[0], lineno, 'TIME_HINT time_hint_ms');
        return [timeHintMs];
      }

      // V10 Runtime - Coroutines, channels, and structured concurrency
      case OpCode.SPAWN_TASK: {
        if (args.length < 2 || typeof args[0] !== 'string' || typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SPAWN_TASK requires two arguments: task_name (string) and function_name (string)',
            { lineno, args }
          );
        }
        return [args[0], args[1]];
      }

      case OpCode.AWAIT: {
        if (args.length < 1 || typeof args[0] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'AWAIT requires one argument: task_id (string)',
            { lineno, args }
          );
        }
        return [args[0]];
      }

      case OpCode.CHANNEL_NEW: {
        if (args.length < 2 || typeof args[0] !== 'string' || typeof args[1] !== 'number') {
          throw createError(
            ErrorType.InvalidInstruction,
            'CHANNEL_NEW requires two arguments: channel_id (string) and capacity (number)',
            { lineno, args }
          );
        }
        const capacity = this.parseNumber(args[1], lineno, 'CHANNEL_NEW capacity');
        return [args[0], capacity];
      }

      case OpCode.CHANNEL_SEND: {
        if (args.length < 2 || typeof args[0] !== 'string' || typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'CHANNEL_SEND requires two arguments: channel_id (string) and value (string)',
            { lineno, args }
          );
        }
        return [args[0], args[1]];
      }

      case OpCode.CHANNEL_RECV: {
        if (args.length < 2 || typeof args[0] !== 'string' || typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'CHANNEL_RECV requires two arguments: channel_id (string) and result_var (string)',
            { lineno, args }
          );
        }
        return [args[0], args[1]];
      }

      case OpCode.SELECT: {
        if (args.length < 2 || !Array.isArray(args[0]) || typeof args[1] !== 'string') {
          throw createError(
            ErrorType.InvalidInstruction,
            'SELECT requires at least two arguments: operation_ids (array) and result_var (string)',
            { lineno, args }
          );
        }
        const operationIds = args[0];
        const resultVar = args[1];
        const timeoutMs = args[2] !== undefined ? this.parseNumber(args[2], lineno, 'SELECT timeout_ms') : undefined;
        return [operationIds, resultVar, timeoutMs].filter(x => x !== undefined) as unknown[];
      }

      default:
        throw createError(ErrorType.InvalidInstruction, `Unknown opcode: ${opcode}`, {
          lineno,
          opcode,
        });
    }
  }
}
