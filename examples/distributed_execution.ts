import { NullVM } from '../src/null_system/vm/null_vm';
import { HybridExecutionManager } from '../src/null_system/vm/hybrid_runtime/hybrid_execution_manager';
import { BaseTransportAdapter, VMCapabilities, SuperBitMessage } from '../src/null_system/vm/hybrid_runtime/transport_adapter';
import { OpCode } from '../src/null_system/vm/instructions';

class InProcessTransportAdapter extends BaseTransportAdapter {
  readonly adapterId = 'in-process';
  private capabilities: VMCapabilities[] = [];

  async initialize(): Promise<void> {
    return Promise.resolve();
  }

  async sendMessage(message: SuperBitMessage): Promise<void> {
    setTimeout(() => this.emitMessage(message), 0);
    return Promise.resolve();
  }

  async advertiseCapabilities(capabilities: VMCapabilities): Promise<void> {
    this.capabilities.push(capabilities);
    this.emitHealth({
      vmId: capabilities.vmId,
      status: 'healthy',
      timestamp: Date.now(),
    });
    return Promise.resolve();
  }

  async discoverVMs(): Promise<VMCapabilities[]> {
    return Promise.resolve([...this.capabilities]);
  }

  async close(): Promise<void> {
    this.capabilities = [];
    return Promise.resolve();
  }
}

async function runDistributedExample() {
  console.log('=== Distributed Execution Example ===\n');

  const adapter = new InProcessTransportAdapter();
  const manager = new HybridExecutionManager(adapter, {
    loadBalancingStrategy: 'round-robin',
    maxTasksPerWorker: 10,
    enableAutoRestart: true,
    healthCheckIntervalMs: 5000,
  });

  await manager.initialize();

  manager.registerLogHook((message, data) => {
    console.log(`[HybridRuntime] ${message}`, data || '');
  });

  console.log('Creating 3 worker VMs...\n');

  const workers: NullVM[] = [];
  for (let i = 0; i < 3; i++) {
    const vm = new NullVM({
      vmId: `worker-${i}`,
      enableTracing: false,
      hybridRuntime: {
        enabled: true,
        manager,
        capabilities: {
          maxConcurrentTasks: 10,
          supportedMessageTypes: ['WORK_ASSIGNMENT', 'DATA', 'CONTROL'],
          customMetadata: { workerId: i },
        },
      },
    });
    workers.push(vm);
    console.log(`  ✓ Worker ${i} created (VM ID: ${vm.getVMId()})`);
  }

  await new Promise(resolve => setTimeout(resolve, 100));

  console.log('\n--- Example 1: Distributed REPEAT Workload ---\n');

  const repeatProgram = [
    { opcode: OpCode.SET, args: ['counter', 0] },
    { opcode: OpCode.SET, args: ['iterations', 5] },
    {
      opcode: OpCode.REPEAT,
      args: [
        'iterations',
        [
          { opcode: OpCode.ADD, args: ['counter', 2] },
        ],
      ],
    },
    { opcode: OpCode.SHOW, args: ['counter'] },
  ];

  workers.forEach((worker, idx) => {
    console.log(`  Executing on Worker ${idx}...`);
    worker.execute(repeatProgram);
    const result = worker.getMemory().getRegister('counter');
    console.log(`  → Worker ${idx} result: ${result}`);
  });

  console.log('\n--- Example 2: Conditional Distributed Workload ---\n');

  const conditionalProgram = [
    { opcode: OpCode.SET, args: ['value', 10] },
    { opcode: OpCode.SET, args: ['threshold', 5] },
    {
      opcode: OpCode.IF,
      args: [
        'value',
        '>',
        [
          { opcode: OpCode.ADD, args: ['value', 10] },
          { opcode: OpCode.SHOW, args: ['value'] },
        ],
      ],
    },
  ];

  workers.forEach((worker, idx) => {
    console.log(`  Executing conditional on Worker ${idx}...`);
    worker.execute(conditionalProgram);
    const result = worker.getMemory().getRegister('value');
    console.log(`  → Worker ${idx} result: ${result}`);
  });

  console.log('\n--- Example 3: Message Passing Between VMs ---\n');

  const sender = workers[0];
  const receiver = workers[1];

  console.log(`  Sending message from ${sender.getVMId()} to ${receiver.getVMId()}...`);

  await sender.sendMessageToVM(receiver.getVMId(), 'DATA', { value: 42, operation: 'compute' });
  
  receiver.queueMessage('DATA', 42);

  const receiveProgram = [
    { opcode: OpCode.RECV_MSG, args: ['msg_data', 1000] },
    { opcode: OpCode.SHOW, args: ['msg_data'] },
  ];

  receiver.execute(receiveProgram);
  const receivedValue = receiver.getMemory().getRegister('msg_data');
  console.log(`  → Receiver got message with value: ${receivedValue}`);

  console.log('\n--- Example 4: Barrier Synchronization ---\n');

  await manager.createBarrier('example-barrier', 3, 5000);
  console.log('  Barrier created for 3 participants');

  const barrierPromises = workers.map(async (worker, idx) => {
    console.log(`  → Worker ${idx} approaching barrier...`);
    await worker.joinBarrier('example-barrier');
    console.log(`  → Worker ${idx} passed barrier!`);
  });

  await Promise.all(barrierPromises);
  console.log('  ✓ All workers synchronized at barrier');

  console.log('\n--- Example 5: Child VM Spawning ---\n');

  const parent = workers[0];
  console.log(`  Parent VM: ${parent.getVMId()}`);

  const spawnProgram = [
    { opcode: OpCode.SPAWN_VM, args: ['child-1', { maxConcurrentTasks: 5 }] },
    { opcode: OpCode.SPAWN_VM, args: ['child-2', { maxConcurrentTasks: 5 }] },
  ];

  parent.execute(spawnProgram);
  console.log(`  ✓ Spawned ${parent.getChildVMs().size} child VMs`);
  parent.getChildVMs().forEach((child, id) => {
    console.log(`    - Child VM ID: ${id}`);
  });

  console.log('\n--- Example 6: Simulated Worker Failure & Recovery ---\n');

  console.log('  Simulating failure scenario...');
  const failingWorker = workers[2];
  
  try {
    await manager.sendMessage(failingWorker.getVMId(), 'non-existent-vm', 'DATA', {});
  } catch (error) {
    console.log(`  ✗ Expected error caught: ${(error as Error).message}`);
  }

  console.log('  System continues operating normally');

  console.log('\n--- Runtime Statistics ---\n');

  const stats = manager.getStats();
  console.log('  Manager Stats:', JSON.stringify(stats, null, 2));

  workers.forEach((worker, idx) => {
    const state = worker.getState();
    console.log(`\n  Worker ${idx} State:`, JSON.stringify(state, null, 2));
  });

  console.log('\n--- Cleanup ---\n');

  await manager.shutdown();
  console.log('  ✓ Hybrid runtime manager shut down');
  
  console.log('\n=== Example Complete ===\n');
}

if (require.main === module) {
  runDistributedExample().catch((error) => {
    console.error('Error running distributed example:', error);
    process.exit(1);
  });
}

export { runDistributedExample };
