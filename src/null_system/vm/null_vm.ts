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
import { EmbeddingRegistry, NeuralEngine, AttentionModule, DenseLayer } from './ai';
import { HybridExecutionManager, HybridExecutionConfig, VMCapabilities } from './hybrid_runtime';

export interface NullVMConfig {
  maxCycles?: number;
  enableTracing?: boolean;
  fuzzyBitConfig?: FuzzyBitConfig;
  vmId?: string;
  hybridRuntime?: {
    enabled: boolean;
    manager?: HybridExecutionManager;
    capabilities?: Partial<VMCapabilities>;
    config?: HybridExecutionConfig;
  };
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
  private embeddingRegistry: EmbeddingRegistry;
  private neuralEngine: NeuralEngine;
  private attentionModule: AttentionModule;
  private vmId: string = '';
  private hybridRuntimeManager?: HybridExecutionManager;
  private childVMs: Map<string, NullVM> = new Map();
  private messageQueue: Array<{ messageType: string; payload: unknown; timestamp: number }> = [];

  constructor(config: NullVMConfig = {}) {
    this.maxCycles = config.maxCycles || 10000;
    this.enableTracing = config.enableTracing || false;
    this.vmId = config.vmId || `vm-${Date.now()}-${Math.random().toString(36).substring(7)}`;

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

    this.embeddingRegistry = new EmbeddingRegistry();
    this.neuralEngine = new NeuralEngine();
    this.attentionModule = new AttentionModule();

    if (this.enableTracing) {
      this.context.addTraceHook((event, data) => {
        console.log(`[TRACE] ${event}:`, data);
      });
    }

    if (config.hybridRuntime?.enabled && config.hybridRuntime.manager) {
      this.hybridRuntimeManager = config.hybridRuntime.manager;

      const vmCapabilities: VMCapabilities = {
        vmId: this.vmId,
        maxConcurrentTasks: config.hybridRuntime.capabilities?.maxConcurrentTasks || 10,
        supportedMessageTypes: config.hybridRuntime.capabilities?.supportedMessageTypes || [
          'WORK_ASSIGNMENT',
          'DATA',
          'CONTROL',
        ],
        customMetadata: config.hybridRuntime.capabilities?.customMetadata,
      };

      this.hybridRuntimeManager.registerVM(this.vmId, vmCapabilities).catch((err: unknown) => {
        console.error(`Failed to register VM ${this.vmId}:`, err);
      });

      this.hybridRuntimeManager.registerLogHook((message: string, data: unknown) => {
        this.binaryBridge.emitControlFlow(
          `HYBRID_LOG: ${message}`,
          data as Record<string, unknown>
        );
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

      case OpCode.AI_EMBED:
        this.executeAI_EMBED(instruction);
        break;

      case OpCode.AI_LAYER:
        this.executeAI_LAYER(instruction);
        break;

      case OpCode.AI_ATTEND:
        this.executeAI_ATTEND(instruction);
        break;

      case OpCode.AI_FUZZY:
        this.executeAI_FUZZY(instruction);
        break;

      case OpCode.SPAWN_VM:
      case OpCode.SEND_MSG:
      case OpCode.RECV_MSG:
      case OpCode.SYNC_BARRIER:
        throw createError(
          ErrorType.ExecutionError,
          `${instruction.opcode} requires hybrid runtime - not implemented in standalone VM`
        );

      default:
        throw createError(ErrorType.InvalidInstruction, `Unknown opcode: ${instruction.opcode}`);
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
      unknown[],
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
      throw createError(ErrorType.UndefinedFunction, `Function '${functionName}' is not defined`, {
        functionName,
      });
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

    while (this.context.getCurrentInstruction() !== null && this.executionCycle < this.maxCycles) {
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
      throw createError(ErrorType.SMPCError, `Failed to combine shares: ${String(error)}`, {
        secretId,
      });
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
      vmId: this.vmId,
      childVMCount: this.childVMs.size,
      messageQueueSize: this.messageQueue.length,
    };
  }

  /**
   * Get VM ID
   */
  getVMId(): string {
    return this.vmId;
  }

  /**
   * Spawn a child VM programmatically
   */
  async spawnChildVM(vmId: string, config?: Partial<VMCapabilities>): Promise<NullVM> {
    if (!this.hybridRuntimeManager) {
      throw createError(
        ErrorType.ExecutionError,
        'Hybrid runtime not enabled - cannot spawn child VM'
      );
    }

    const childVM = new NullVM({
      vmId,
      maxCycles: this.maxCycles,
      enableTracing: this.enableTracing,
      hybridRuntime: {
        enabled: true,
        manager: this.hybridRuntimeManager,
        capabilities: config,
      },
    });

    this.childVMs.set(vmId, childVM);
    return childVM;
  }

  /**
   * Send message to another VM
   */
  async sendMessageToVM(targetVmId: string, messageType: string, payload: unknown): Promise<void> {
    if (!this.hybridRuntimeManager) {
      throw createError(
        ErrorType.ExecutionError,
        'Hybrid runtime not enabled - cannot send message'
      );
    }

    await this.hybridRuntimeManager.sendMessage(this.vmId, targetVmId, messageType, payload);
  }

  /**
   * Queue incoming message
   */
  queueMessage(messageType: string, payload: unknown): void {
    this.messageQueue.push({
      messageType,
      payload,
      timestamp: Date.now(),
    });
  }

  /**
   * Join synchronization barrier
   */
  async joinBarrier(barrierId: string, _timeoutMs?: number): Promise<void> {
    if (!this.hybridRuntimeManager) {
      throw createError(
        ErrorType.ExecutionError,
        'Hybrid runtime not enabled - cannot join barrier'
      );
    }

    await this.hybridRuntimeManager.arriveAtBarrier(barrierId, this.vmId);
  }

  /**
   * Submit work to hybrid runtime
   */
  async submitWork(payload: unknown, priority = 0): Promise<string> {
    if (!this.hybridRuntimeManager) {
      throw createError(
        ErrorType.ExecutionError,
        'Hybrid runtime not enabled - cannot submit work'
      );
    }

    return await this.hybridRuntimeManager.submitWork(this.vmId, payload, priority);
  }

  /**
   * Get child VMs
   */
  getChildVMs(): Map<string, NullVM> {
    return this.childVMs;
  }

  /**
   * Get hybrid runtime manager
   */
  getHybridRuntimeManager(): HybridExecutionManager | undefined {
    return this.hybridRuntimeManager;
  }

  /**
   * Execute AI_EMBED instruction: AI_EMBED <output_register> <embedding_id> <dimension>
   */
  private executeAI_EMBED(instruction: Instruction): void {
    const [outputRegister, embeddingId, dimension] = instruction.args as [string, string, number];

    let embedding = this.embeddingRegistry.getEmbedding(embeddingId);
    if (!embedding) {
      embedding = EmbeddingRegistry.createRandomDenseEmbedding(embeddingId, dimension);
      this.embeddingRegistry.registerEmbedding(embeddingId, embedding, 'dense', 'ai_instruction');
    }

    this.memory.setTensorRegister(outputRegister, embedding);
    this.binaryBridge.emitControlFlow('AI_EMBED', {
      outputRegister,
      embeddingId,
      dimension,
      shape: embedding.getShape().dims,
    });
  }

  /**
   * Execute AI_LAYER instruction: AI_LAYER <input_register> <output_register> <layer_config> <activation>
   */
  private executeAI_LAYER(instruction: Instruction): void {
    const [inputRegister, outputRegister, layerConfigStr, activation] = instruction.args as [
      string,
      string,
      string,
      string,
    ];

    const inputTensor = this.memory.getTensorRegister(inputRegister);
    if (!inputTensor) {
      throw createError(
        ErrorType.ExecutionError,
        `Input tensor register not found: ${inputRegister}`
      );
    }

    const inputDim = inputTensor.getShape().dims[inputTensor.getShape().dims.length - 1] || 1;

    try {
      const layerConfig = JSON.parse(layerConfigStr) as { outputDim?: number };
      const outputDim = layerConfig.outputDim || inputDim;

      const layer = new DenseLayer(
        {
          inputDim,
          outputDim,
          activation: (activation as 'relu' | 'sigmoid' | 'tanh' | 'linear') || 'linear',
          usesBias: true,
        },
        undefined,
        undefined
      );

      const outputTensor = layer.forward(inputTensor);
      this.memory.setTensorRegister(outputRegister, outputTensor);

      this.binaryBridge.emitControlFlow('AI_LAYER', {
        inputRegister,
        outputRegister,
        inputShape: inputTensor.getShape().dims,
        outputShape: outputTensor.getShape().dims,
        activation,
      });
    } catch (error) {
      throw createError(
        ErrorType.ExecutionError,
        `AI_LAYER execution failed: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Execute AI_ATTEND instruction: AI_ATTEND <input_register> <output_register> <attention_config>
   */
  private executeAI_ATTEND(instruction: Instruction): void {
    const [inputRegister, outputRegister, attentionConfigStr] = instruction.args as [
      string,
      string,
      string,
    ];

    const inputTensor = this.memory.getTensorRegister(inputRegister);
    if (!inputTensor) {
      throw createError(
        ErrorType.ExecutionError,
        `Input tensor register not found: ${inputRegister}`
      );
    }

    try {
      const attentionConfig = JSON.parse(attentionConfigStr) as Record<string, unknown>;
      if (attentionConfig.headCount !== undefined) {
        this.attentionModule.setConfig({
          headCount: attentionConfig.headCount as number,
        });
      }
      if (attentionConfig.temperatureScale !== undefined) {
        this.attentionModule.setConfig({
          temperatureScale: attentionConfig.temperatureScale as number,
        });
      }

      const outputTensor = this.attentionModule.selfAttention(inputTensor);
      this.memory.setTensorRegister(outputRegister, outputTensor);

      const inputMeta = inputTensor.getMetadata();
      const outputMeta = outputTensor.getMetadata();

      this.binaryBridge.emitControlFlow('AI_ATTEND', {
        inputRegister,
        outputRegister,
        inputUncertainty: inputMeta.uncertainty,
        outputUncertainty: outputMeta.uncertainty,
        uncertaintyReduced: inputMeta.uncertainty - outputMeta.uncertainty,
      });
    } catch (error) {
      throw createError(
        ErrorType.ExecutionError,
        `AI_ATTEND execution failed: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Execute AI_FUZZY instruction: AI_FUZZY <input_register> <output_register> <uncertainty_reduction>
   */
  private executeAI_FUZZY(instruction: Instruction): void {
    const [inputRegister, outputRegister, uncertaintyReduction] = instruction.args as [
      string,
      string,
      number,
    ];

    const inputTensor = this.memory.getTensorRegister(inputRegister);
    if (!inputTensor) {
      throw createError(
        ErrorType.ExecutionError,
        `Input tensor register not found: ${inputRegister}`
      );
    }

    const outputTensor = inputTensor.clone();
    const inputUncertainty = outputTensor.getMetadata().uncertainty;
    outputTensor.reduceUncertainty(uncertaintyReduction);
    const outputUncertainty = outputTensor.getMetadata().uncertainty;

    this.memory.setTensorRegister(outputRegister, outputTensor);

    this.binaryBridge.emitControlFlow('AI_FUZZY', {
      inputRegister,
      outputRegister,
      inputUncertainty,
      outputUncertainty,
      reduction: uncertaintyReduction,
    });
  }

  /**
   * Get embedding registry (for external access)
   */
  getEmbeddingRegistry(): EmbeddingRegistry {
    return this.embeddingRegistry;
  }

  /**
   * Get neural engine (for external access)
   */
  getNeuralEngine(): NeuralEngine {
    return this.neuralEngine;
  }

  /**
   * Get attention module (for external access)
   */
  getAttentionModule(): AttentionModule {
    return this.attentionModule;
  }
}
