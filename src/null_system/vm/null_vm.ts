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
import {
  HybridExecutionManager,
  HybridExecutionConfig,
  VMCapabilities,
} from './hybrid_runtime';

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
  private vmId: string;
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
        supportedMessageTypes: config.hybridRuntime.capabilities?.supportedMessageTypes || ['WORK_ASSIGNMENT', 'DATA', 'CONTROL'],
        customMetadata: config.hybridRuntime.capabilities?.customMetadata,
      };
      
      this.hybridRuntimeManager.registerVM(this.vmId, vmCapabilities).catch((err) => {
        console.error(`Failed to register VM ${this.vmId}:`, err);
      });

      this.hybridRuntimeManager.registerLogHook((message, data) => {
        this.binaryBridge.emitControlFlow(`HYBRID_LOG: ${message}`, data as Record<string, unknown>);
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

      case OpCode.SPAWN_VM:
        this.executeSPAWN_VM(instruction);
        break;

      case OpCode.SEND_MSG:
        this.executeSEND_MSG(instruction);
        break;

      case OpCode.RECV_MSG:
        this.executeRECV_MSG(instruction);
        break;

      case OpCode.SYNC_BARRIER:
        this.executeSYNC_BARRIER(instruction);
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
   * Execute SPAWN_VM instruction: SPAWN_VM <vm_id> <config>
   */
  private executeSPAWN_VM(instruction: Instruction): void {
    const [vmId, config] = instruction.args as [string, unknown];

    if (!this.hybridRuntimeManager) {
      throw createError(
        ErrorType.ExecutionError,
        'Hybrid runtime not enabled - cannot spawn VM'
      );
    }

    const childVM = new NullVM({
      vmId,
      maxCycles: this.maxCycles,
      enableTracing: this.enableTracing,
      hybridRuntime: {
        enabled: true,
        manager: this.hybridRuntimeManager,
        capabilities: config as Partial<VMCapabilities>,
      },
    });

    this.childVMs.set(vmId, childVM);
    this.binaryBridge.emitControlFlow('SPAWN_VM', { vmId, parentVm: this.vmId });
  }

  /**
   * Execute SEND_MSG instruction: SEND_MSG <target_vm_id> <message_type> <payload>
   */
  private executeSEND_MSG(instruction: Instruction): void {
    const [targetVmId, messageType, payload] = instruction.args as [string, string, unknown];

    if (!this.hybridRuntimeManager) {
      throw createError(
        ErrorType.ExecutionError,
        'Hybrid runtime not enabled - cannot send message'
      );
    }

    this.hybridRuntimeManager
      .sendMessage(this.vmId, targetVmId, messageType, payload)
      .catch((error) => {
        throw createError(
          ErrorType.ExecutionError,
          `Failed to send message: ${error.message}`,
          { targetVmId, messageType }
        );
      });

    this.binaryBridge.emitControlFlow('SEND_MSG', {
      sourceVm: this.vmId,
      targetVm: targetVmId,
      messageType,
    });
  }

  /**
   * Execute RECV_MSG instruction: RECV_MSG <result_register> [timeout_ms]
   */
  private executeRECV_MSG(instruction: Instruction): void {
    const [resultRegister, timeoutMs] = instruction.args as [string, number | undefined];

    if (this.messageQueue.length === 0) {
      if (timeoutMs) {
        const startTime = Date.now();
        while (this.messageQueue.length === 0 && Date.now() - startTime < timeoutMs) {
          // Busy wait (in real implementation would use async/await)
        }
      }

      if (this.messageQueue.length === 0) {
        this.memory.setRegister(resultRegister, 0);
        return;
      }
    }

    const message = this.messageQueue.shift()!;
    const messageData = typeof message.payload === 'number' ? message.payload : 1;
    this.memory.setRegister(resultRegister, messageData);

    this.binaryBridge.emitControlFlow('RECV_MSG', {
      vmId: this.vmId,
      messageType: message.messageType,
    });
  }

  /**
   * Execute SYNC_BARRIER instruction: SYNC_BARRIER <barrier_id> [timeout_ms]
   */
  private executeSYNC_BARRIER(instruction: Instruction): void {
    const [barrierId, timeoutMs] = instruction.args as [string, number | undefined];

    if (!this.hybridRuntimeManager) {
      throw createError(
        ErrorType.ExecutionError,
        'Hybrid runtime not enabled - cannot sync barrier'
      );
    }

    this.hybridRuntimeManager
      .arriveAtBarrier(barrierId, this.vmId)
      .catch((error) => {
        throw createError(
          ErrorType.ExecutionError,
          `Barrier sync failed: ${error.message}`,
          { barrierId }
        );
      });

    this.binaryBridge.emitControlFlow('SYNC_BARRIER', {
      vmId: this.vmId,
      barrierId,
    });
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
  async sendMessageToVM(
    targetVmId: string,
    messageType: string,
    payload: unknown
  ): Promise<void> {
    if (!this.hybridRuntimeManager) {
      throw createError(
        ErrorType.ExecutionError,
        'Hybrid runtime not enabled - cannot send message'
      );
    }

    await this.hybridRuntimeManager.sendMessage(
      this.vmId,
      targetVmId,
      messageType,
      payload
    );
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
  async joinBarrier(barrierId: string, timeoutMs?: number): Promise<void> {
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
}
