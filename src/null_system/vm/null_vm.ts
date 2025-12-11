/**
 * NullVM - Virtual machine for executing super-bit programs
 */

import { Instruction, OpCode } from './instructions';
import { Memory } from './memory';
import { ExecutionContext } from './execution_context';
import { Decoder, SuperBitProgram } from './decoder';
import { BinaryBridge } from './binary_bridge';
import { FuzzyBitEvaluator, FuzzyBitConfig } from './fuzzy_bits';
import { createError, ErrorType, VMError } from './errors';

export interface NullVMConfig {
  maxCycles?: number;
  enableTracing?: boolean;
  fuzzyBitConfig?: FuzzyBitConfig;
}

export class NullVM {
  private memory: Memory;
  private context: ExecutionContext;
  private decoder: Decoder;
  private binaryBridge: BinaryBridge;
  private fuzzyEvaluator: FuzzyBitEvaluator;
  private maxCycles: number;
  private enableTracing: boolean;
  private executionCycle: number = 0;

  constructor(config: NullVMConfig = {}) {
    this.maxCycles = config.maxCycles || 10000;
    this.enableTracing = config.enableTracing || false;

    this.memory = new Memory();
    this.context = new ExecutionContext();
    this.decoder = new Decoder();
    this.binaryBridge = new BinaryBridge();
    this.fuzzyEvaluator = new FuzzyBitEvaluator(config.fuzzyBitConfig);

    if (this.enableTracing) {
      this.context.addTraceHook((event, data) => {
        console.log(`[TRACE] ${event}:`, data);
      });
    }
  }

  /**
   * Execute a super-bit program
   */
  execute(program: SuperBitProgram | unknown[]): void {
    try {
      // Decode program
      const instructions = this.decoder.decode(program);

      // Set program in context
      this.context.setProgram(instructions);
      this.context.setRunning(true);
      this.executionCycle = 0;

      // Execute instructions
      while (
        this.context.getCurrentInstruction() !== null &&
        this.executionCycle < this.maxCycles
      ) {
        this.executeInstruction();
        this.executionCycle++;
      }

      if (this.executionCycle >= this.maxCycles) {
        throw createError(
          ErrorType.ExecutionError,
          `Execution exceeded maximum cycles (${this.maxCycles})`
        );
      }

      this.context.setRunning(false);
    } catch (error) {
      this.context.setRunning(false);
      if (error instanceof VMError) {
        this.context.emitTrace('error', {
          type: error.type,
          message: error.message,
          context: error.context,
        });
        throw error;
      }
      throw error;
    }
  }

  /**
   * Execute a single instruction
   */
  private executeInstruction(): void {
    const instruction = this.context.getCurrentInstruction();
    if (!instruction) {
      return;
    }

    this.context.emitTrace('instruction', {
      opcode: instruction.opcode,
      args: instruction.args,
      pc: this.context.getProgramCounter(),
    });

    switch (instruction.opcode) {
      case OpCode.SET:
        this.executeSET(instruction);
        break;

      case OpCode.ADD:
        this.executeADD(instruction);
        break;

      case OpCode.SHOW:
        this.executeSHOW(instruction);
        break;

      case OpCode.IF:
        this.executeIF(instruction);
        break;

      case OpCode.REPEAT:
        this.executeREPEAT(instruction);
        break;

      case OpCode.DEFINE:
        this.executeDEFINE(instruction);
        break;

      case OpCode.CALL:
        this.executeCALL(instruction);
        break;

      case OpCode.RETURN:
        this.executeRETURN(instruction);
        break;

      case OpCode.JMP:
        this.executeJMP(instruction);
        return;

      case OpCode.NOP:
        break;

      default:
        throw createError(
          ErrorType.InvalidInstruction,
          `Unknown opcode: ${instruction.opcode}`
        );
    }

    this.context.advanceProgramCounter();
  }

  /**
   * Execute SET instruction: SET <register> <value>
   */
  private executeSET(instruction: Instruction): void {
    const [register, value] = instruction.args as [string, number];
    this.memory.setRegister(register, value);
    this.binaryBridge.emitRegisterState(register, value);
  }

  /**
   * Execute ADD instruction: ADD <register> <value_or_register>
   */
  private executeADD(instruction: Instruction): void {
    const [register, operand] = instruction.args as [string, number | string];
    const currentValue = this.memory.getRegister(register);
    const addValue =
      typeof operand === 'number' ? operand : this.memory.getRegister(operand as string);
    const newValue = currentValue + addValue;
    this.memory.setRegister(register, newValue);
    this.binaryBridge.emitRegisterState(register, newValue);
  }

  /**
   * Execute SHOW instruction: SHOW <register>
   */
  private executeSHOW(instruction: Instruction): void {
    const [register] = instruction.args as [string];
    const value = this.memory.getRegister(register);
    this.binaryBridge.emitOutput(register, value);
  }

  /**
   * Execute IF instruction: IF <condition_register> <operator> <instructions>
   */
  private executeIF(instruction: Instruction): void {
    const [conditionRegister, operator, instructions] = instruction.args as [
      string,
      string,
      unknown[]
    ];

    const value = this.memory.getRegister(conditionRegister);
    const condition = this.fuzzyEvaluator.evaluateCondition(operator, value);

    if (condition) {
      this.executeBlock(instructions);
    }
  }

  /**
   * Execute REPEAT instruction: REPEAT <count_register> <instructions>
   */
  private executeREPEAT(instruction: Instruction): void {
    const [countRegister, instructions] = instruction.args as [string, unknown[]];
    const count = this.memory.getRegister(countRegister);

    for (let i = 0; i < count; i++) {
      if (this.executionCycle >= this.maxCycles) {
        throw createError(
          ErrorType.ExecutionError,
          `Execution exceeded maximum cycles during REPEAT loop`
        );
      }
      this.executeBlock(instructions);
    }
  }

  /**
   * Execute DEFINE instruction: DEFINE <function_name> <instructions>
   */
  private executeDEFINE(instruction: Instruction): void {
    const [functionName, instructions] = instruction.args as [string, unknown[]];

    // Decode the block instructions
    const decodedInstructions = this.decoder.decode(instructions);

    // Store function definition
    this.context.defineFunction(functionName, decodedInstructions);
  }

  /**
   * Execute CALL instruction: CALL <function_name>
   */
  private executeCALL(instruction: Instruction): void {
    const [functionName] = instruction.args as [string];

    if (!this.context.isFunctionDefined(functionName)) {
      throw createError(
        ErrorType.UndefinedFunction,
        `Function '${functionName}' is not defined`,
        { functionName }
      );
    }

    const functionInstructions = this.context.getFunction(functionName)!;

    // Push call frame
    const returnAddress = this.context.getProgramCounter();
    const savedStackPointer = this.memory.getStackPointer();
    this.context.pushCallFrame(functionName, returnAddress, savedStackPointer);

    // Execute function body
    this.executeBlock(functionInstructions);

    // Pop call frame
    const frame = this.context.popCallFrame();
    this.memory.setStackPointer(frame.savedStackPointer);
  }

  /**
   * Execute RETURN instruction: RETURN
   */
  private executeRETURN(_instruction: Instruction): void {
    const frame = this.context.popCallFrame();
    this.context.setProgramCounter(frame.returnAddress);
    this.memory.setStackPointer(frame.savedStackPointer);
  }

  /**
   * Execute JMP instruction: JMP <address>
   */
  private executeJMP(instruction: Instruction): void {
    const [address] = instruction.args as [number];
    this.context.setProgramCounter(address - 1); // -1 because advanceProgramCounter will increment
  }

  /**
   * Execute a block of instructions (used for IF, REPEAT, etc.)
   */
  private executeBlock(instructions: unknown[]): void {
    const savedPC = this.context.getProgramCounter();
    const decodedInstructions = this.decoder.decode(instructions);

    // Save current program
    const savedProgram = this.context.program;

    // Execute block
    this.context.program = decodedInstructions;
    this.context.setProgramCounter(0);

    while (
      this.context.getCurrentInstruction() !== null &&
      this.executionCycle < this.maxCycles
    ) {
      this.executeInstruction();
      this.executionCycle++;
    }

    // Restore original program and PC
    this.context.program = savedProgram;
    // Directly set PC without validation since we're restoring
    const ctx = this.context as unknown as { programCounter: number };
    ctx.programCounter = savedPC;
  }

  /**
   * Get memory
   */
  getMemory(): Memory {
    return this.memory;
  }

  /**
   * Get binary bridge
   */
  getBinaryBridge(): BinaryBridge {
    return this.binaryBridge;
  }

  /**
   * Get execution context
   */
  getContext(): ExecutionContext {
    return this.context;
  }

  /**
   * Get fuzzy bit evaluator
   */
  getFuzzyBitEvaluator(): FuzzyBitEvaluator {
    return this.fuzzyEvaluator;
  }

  /**
   * Reset VM state
   */
  reset(): void {
    this.memory.reset();
    this.context.reset();
    this.binaryBridge.clearFrames();
    this.executionCycle = 0;
  }

  /**
   * Get execution cycle count
   */
  getExecutionCycle(): number {
    return this.executionCycle;
  }

  /**
   * Get VM state snapshot
   */
  getState() {
    return {
      memory: this.memory.getSnapshot(),
      context: this.context.getSnapshot(),
      executionCycle: this.executionCycle,
      binaryFrameCount: this.binaryBridge.getFrameCount(),
    };
  }
}
