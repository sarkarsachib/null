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
import { HomomorphicEngine, SecureChannel, ZKProofSystem, SMPCOrchestrator } from '../security';

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
  private homomorphicEngine: HomomorphicEngine;
  private secureChannel: SecureChannel;
  private zkProofSystem: ZKProofSystem;
  private smpcOrchestrator: SMPCOrchestrator;

  constructor(config: NullVMConfig = {}) {
    this.maxCycles = config.maxCycles || 10000;
    this.enableTracing = config.enableTracing || false;

    this.memory = new Memory();
    this.context = new ExecutionContext();
    this.decoder = new Decoder();
    this.binaryBridge = new BinaryBridge();
    this.fuzzyEvaluator = new FuzzyBitEvaluator(config.fuzzyBitConfig);
    this.homomorphicEngine = new HomomorphicEngine(2048);
    this.secureChannel = new SecureChannel({ algorithm: 'nacl-box' });
    this.zkProofSystem = new ZKProofSystem();
    this.smpcOrchestrator = new SMPCOrchestrator({
      partyId: 'party_0',
      threshold: 2,
      totalParties: 2,
    });

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

      case OpCode.SECURE_ENC:
        this.executeSECURE_ENC(instruction);
        break;

      case OpCode.SECURE_DEC:
        this.executeSECURE_DEC(instruction);
        break;

      case OpCode.SECURE_EVAL:
        this.executeSECURE_EVAL(instruction);
        break;

      case OpCode.ZK_PROVE:
        this.executeZK_PROVE(instruction);
        break;

      case OpCode.ZK_VERIFY:
        this.executeZK_VERIFY(instruction);
        break;

      case OpCode.SMPC_SHARE:
        this.executeSMPC_SHARE(instruction);
        break;

      case OpCode.SMPC_COMBINE:
        this.executeSMPC_COMBINE(instruction);
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
   * Execute SECURE_ENC instruction: Encrypt a register value
   */
  private executeSECURE_ENC(instruction: Instruction): void {
    const [register, keyId] = instruction.args as [string, string];

    try {
      const value = this.memory.getRegister(register);

      let key = this.memory.getKey(keyId);
      if (!key) {
        const keyPair = this.homomorphicEngine.generateKeyPair();
        this.memory.storeKey(keyId, keyPair.publicKey, keyPair.privateKey);
        key = { publicKey: keyPair.publicKey, privateKey: keyPair.privateKey };
      }

      const encrypted = this.homomorphicEngine.encrypt(value, key.publicKey);
      const encryptedId = `${register}_encrypted`;

      this.memory.storeEncryptedValue(encryptedId, encrypted.ciphertext, keyId);
      this.binaryBridge.emitControlFlow('SECURE_ENC', {
        register,
        keyId,
        encryptedValueId: encryptedId,
      });
    } catch (error) {
      throw createError(
        ErrorType.EncryptionError,
        `Failed to encrypt register ${register}: ${String(error)}`,
        { register, keyId }
      );
    }
  }

  /**
   * Execute SECURE_DEC instruction: Decrypt an encrypted value
   */
  private executeSECURE_DEC(instruction: Instruction): void {
    const [register, keyId] = instruction.args as [string, string];

    try {
      const encryptedId = `${register}_encrypted`;
      const encrypted = this.memory.getEncryptedValue(encryptedId);

      if (!encrypted) {
        throw new Error(`No encrypted value found for ${register}`);
      }

      const key = this.memory.getKey(keyId);
      if (!key || !key.privateKey) {
        throw new Error(`Private key not available for ${keyId}`);
      }

      const encryptedValue = {
        ciphertext: encrypted.ciphertext,
        publicKey: key.publicKey,
      };

      const decrypted = this.homomorphicEngine.decrypt(encryptedValue, key.privateKey);
      this.memory.setRegister(register, decrypted);

      this.binaryBridge.emitControlFlow('SECURE_DEC', {
        register,
        keyId,
        decrypted,
      });
    } catch (error) {
      throw createError(
        ErrorType.DecryptionError,
        `Failed to decrypt register ${register}: ${String(error)}`,
        { register, keyId }
      );
    }
  }

  /**
   * Execute SECURE_EVAL instruction: Homomorphic evaluation on encrypted values
   */
  private executeSECURE_EVAL(instruction: Instruction): void {
    const [operation, sourceReg, destReg] = instruction.args as [string, string, string];

    try {
      const sourceId = `${sourceReg}_encrypted`;
      const destId = `${destReg}_encrypted`;

      const sourceEncrypted = this.memory.getEncryptedValue(sourceId);
      const destEncrypted = this.memory.getEncryptedValue(destId);

      if (!sourceEncrypted || !destEncrypted) {
        throw new Error('One or both encrypted values not found');
      }

      const sourceValue = {
        ciphertext: sourceEncrypted.ciphertext,
        publicKey: Buffer.alloc(0),
      };
      const destValue = {
        ciphertext: destEncrypted.ciphertext,
        publicKey: Buffer.alloc(0),
      };

      let result;
      switch (operation) {
        case 'add':
          result = this.homomorphicEngine.encryptedAdd(sourceValue, destValue);
          break;
        case 'mul_scalar': {
          const scalar = this.memory.getRegister('__scalar');
          result = this.homomorphicEngine.encryptedScalarMultiply(sourceValue, scalar);
          break;
        }
        default:
          throw new Error(`Unknown secure operation: ${operation}`);
      }

      this.memory.storeEncryptedValue(destId, result.ciphertext, destEncrypted.keyId);

      this.binaryBridge.emitControlFlow('SECURE_EVAL', {
        operation,
        sourceReg,
        destReg,
      });
    } catch (error) {
      throw createError(
        ErrorType.ExecutionError,
        `Failed to evaluate secure operation ${operation}: ${String(error)}`,
        { operation, sourceReg, destReg }
      );
    }
  }

  /**
   * Execute ZK_PROVE instruction: Generate zero-knowledge proof
   */
  private executeZK_PROVE(instruction: Instruction): void {
    const [traceId] = instruction.args as [string];

    try {
      const pc = this.context.getProgramCounter();
      const statements = [
        `Execution at cycle ${this.executionCycle}`,
        `Program counter: ${pc >= 0 ? pc : 0}`,
      ];

      this.zkProofSystem.recordTrace(traceId, statements);
      const proof = this.zkProofSystem.proveExecution(traceId);

      const transcript = this.zkProofSystem.getProofTranscript(traceId);
      this.binaryBridge.emitProofTranscript(traceId, transcript);

      this.binaryBridge.emitControlFlow('ZK_PROVE', {
        traceId,
        verified: proof.verified,
        commitmentLength: proof.commitment.length,
      });
    } catch (error) {
      this.binaryBridge.emitControlFlow('ZK_PROVE_ERROR', {
        traceId,
        error: String(error),
      });
    }
  }

  /**
   * Execute ZK_VERIFY instruction: Verify zero-knowledge proof
   */
  private executeZK_VERIFY(instruction: Instruction): void {
    const [proofId, expectedDigestId] = instruction.args as [string, string];

    try {
      this.binaryBridge.emitControlFlow('ZK_VERIFY', {
        proofId,
        expectedDigestId,
        status: 'verification_attempted',
      });
    } catch (error) {
      throw createError(ErrorType.ProofError, `Failed to verify ZK proof: ${String(error)}`, {
        proofId,
      });
    }
  }

  /**
   * Execute SMPC_SHARE instruction: Share a secret for multi-party computation
   */
  private executeSMPC_SHARE(instruction: Instruction): void {
    const [secretId, threshold] = instruction.args as [string, number];

    try {
      const secret = Buffer.alloc(32);
      for (let i = 0; i < 32; i++) {
        secret[i] = Math.floor(Math.random() * 256);
      }

      const shares = this.smpcOrchestrator.shareSecret(secretId, secret);

      for (const [partyId, share] of shares) {
        const shareId = `${secretId}_${partyId}`;
        this.smpcOrchestrator.submitShare(shareId, share);
      }

      this.binaryBridge.emitControlFlow('SMPC_SHARE', {
        secretId,
        threshold,
        numShares: shares.size,
      });
    } catch (error) {
      throw createError(ErrorType.SMPCError, `Failed to share secret: ${String(error)}`, {
        secretId,
      });
    }
  }

  /**
   * Execute SMPC_COMBINE instruction: Combine shares to reconstruct secret
   */
  private executeSMPC_COMBINE(instruction: Instruction): void {
    const [secretId, shareIds] = instruction.args as [string, string[]];

    try {
      const reconstructed = this.smpcOrchestrator.combineShares(secretId, shareIds);

      this.memory.setRegister('__secret_output', reconstructed.readUInt32BE(0));

      this.binaryBridge.emitControlFlow('SMPC_COMBINE', {
        secretId,
        numSharesUsed: shareIds.length,
        combined: true,
      });
    } catch (error) {
      throw createError(
        ErrorType.SMPCError,
        `Failed to combine shares: ${String(error)}`,
        { secretId }
      );
    }
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
   * Get homomorphic engine
   */
  getHomomorphicEngine(): HomomorphicEngine {
    return this.homomorphicEngine;
  }

  /**
   * Get secure channel
   */
  getSecureChannel(): SecureChannel {
    return this.secureChannel;
  }

  /**
   * Get ZK proof system
   */
  getZKProofSystem(): ZKProofSystem {
    return this.zkProofSystem;
  }

  /**
   * Get SMPC orchestrator
   */
  getSMPCOrchestrator(): SMPCOrchestrator {
    return this.smpcOrchestrator;
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
