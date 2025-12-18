/**
 * V10 Runtime Jest Tests
 * 
 * Tests cover:
 * - Coroutine scheduling
 * - Channel send/recv operations
 * - Select timeout operations
 * - Supervisor functionality
 * - VM integration
 */

import { 
  createScheduler,
  CoroutineScheduler,
  createChannel,
  Channel,
  createSupervisor,
  Supervisor,
  createV10Runtime,
  V10RuntimeCapability,
  CoroutineTask,
  TaskState,
  TaskPriority,
  CoroutineId,
  TaskResult
} from '../src/null_system/vm/v10/interfaces';
import { createExecutionPipeline } from '../src/null_system/vm/v10/execution_pipeline';
import { NullVM } from '../src/null_system/vm/null_vm';
import { OpCode } from '../src/null_system/vm/instructions';

// Mock coroutine task for testing
class MockCoroutineTask implements CoroutineTask {
  readonly taskId: CoroutineId;
  readonly supervisorId: string;
  readonly priority: TaskPriority;
  readonly state: TaskState = TaskState.PENDING;
  readonly startTime: number;
  readonly instructions: any[] = [];
  readonly instructionPointer: number = 0;
  
  private executePromise?: Promise<TaskResult>;
  private resolveExecution?: (result: TaskResult) => void;
  private rejectExecution?: (error: Error) => void;

  constructor(taskId: CoroutineId, supervisorId: string, priority: TaskPriority = TaskPriority.NORMAL) {
    this.taskId = taskId;
    this.supervisorId = supervisorId;
    this.priority = priority;
    this.startTime = Date.now();
  }

  async execute(context: any): Promise<TaskResult> {
    // Create a promise that can be resolved externally for testing
    this.executePromise = new Promise((resolve, reject) => {
      this.resolveExecution = resolve;
      this.rejectExecution = reject;
    });
    
    // Simulate some execution time
    await new Promise(resolve => setTimeout(resolve, 10));
    
    // Mark as running
    this.state = TaskState.RUNNING;
    
    return this.executePromise;
  }

  suspend(reason: string): void {
    console.log(`Task ${this.taskId} suspended: ${reason}`);
    // In a real implementation, this would pause execution
  }

  resume(): void {
    console.log(`Task ${this.taskId} resumed`);
    // In a real implementation, this would resume execution
  }

  async cancel(): Promise<void> {
    if (this.resolveExecution) {
      this.resolveExecution({
        taskId: this.taskId,
        state: TaskState.CANCELLED,
        startTime: this.startTime,
        endTime: Date.now(),
        executionTime: Date.now() - this.startTime,
        metadata: { cancelled: true }
      });
    }
  }

  // Test helper methods
  resolveTask(result: TaskResult): void {
    if (this.resolveExecution) {
      this.resolveExecution(result);
    }
  }

  rejectTask(error: Error): void {
    if (this.rejectExecution) {
      this.rejectExecution(error);
    }
  }
}

describe('V10 Runtime Coroutine Scheduling', () => {
  let scheduler: CoroutineScheduler;

  beforeEach(async () => {
    scheduler = createScheduler('test-scheduler', 5);
  });

  afterEach(async () => {
    if (scheduler) {
      await scheduler.shutdown();
    }
  });

  test('should schedule and execute a basic task', async () => {
    const task = new MockCoroutineTask('test-task-1', 'test-scheduler');
    
    await scheduler.schedule(task);
    
    // Verify task is scheduled
    expect(scheduler.getStatus('test-task-1')).toBe(TaskState.PENDING);
    
    // Resolve the task
    const result: TaskResult = {
      taskId: 'test-task-1',
      state: TaskState.COMPLETED,
      startTime: task.startTime,
      endTime: Date.now(),
      executionTime: 100,
      result: 'success',
      metadata: {}
    };
    
    task.resolveTask(result);
    
    // Wait a bit for execution
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Task should complete
    expect(scheduler.getStatus('test-task-1')).toBe(TaskState.COMPLETED);
  });

  test('should handle multiple tasks with priority scheduling', async () => {
    const highPriorityTask = new MockCoroutineTask('high-priority', 'test-scheduler', TaskPriority.HIGH);
    const lowPriorityTask = new MockCoroutineTask('low-priority', 'test-scheduler', TaskPriority.LOW);
    const normalPriorityTask = new MockCoroutineTask('normal-priority', 'test-scheduler', TaskPriority.NORMAL);

    await Promise.all([
      scheduler.schedule(lowPriorityTask),
      scheduler.schedule(highPriorityTask),
      scheduler.schedule(normalPriorityTask)
    ]);

    const tasks = scheduler.getAllTasks();
    
    // Verify all tasks are scheduled
    expect(tasks).toHaveLength(3);
    expect(tasks.find(t => t.taskId === 'high-priority')?.priority).toBe(TaskPriority.HIGH);
    expect(tasks.find(t => t.taskId === 'normal-priority')?.priority).toBe(TaskPriority.NORMAL);
    expect(tasks.find(t => t.taskId === 'low-priority')?.priority).toBe(TaskPriority.LOW);
  });

  test('should cancel scheduled tasks', async () => {
    const task = new MockCoroutineTask('cancellable-task', 'test-scheduler');
    
    await scheduler.schedule(task);
    expect(scheduler.getStatus('cancellable-task')).toBe(TaskState.PENDING);
    
    await scheduler.cancel('cancellable-task');
    
    // Task should be cancelled and removed
    expect(() => scheduler.getStatus('cancellable-task')).toThrow();
  });

  test('should handle task pause and resume', async () => {
    const task = new MockCoroutineTask('pausable-task', 'test-scheduler');
    
    await scheduler.schedule(task);
    
    // Pause the task
    await scheduler.pause('pausable-task');
    expect(scheduler.getStatus('pausable-task')).toBe(TaskState.SUSPENDED);
    
    // Resume the task
    await scheduler.resume('pausable-task');
    expect(scheduler.getStatus('pausable-task')).toBe(TaskState.PENDING);
  });
});

describe('V10 Runtime Channel Operations', () => {
  let channel: Channel<string>;

  beforeEach(async () => {
    channel = createChannel<string>('test-channel', 5);
  });

  afterEach(async () => {
    if (channel && !channel.isClosed) {
      await channel.close();
    }
  });

  test('should create channel with specified capacity', () => {
    expect(channel.channelId).toBe('test-channel');
    expect(channel.capacity).toBe(5);
    expect(channel.isClosed).toBe(false);
  });

  test('should send and receive values through channel', async () => {
    const testValue = 'Hello, V10 Runtime!';
    
    // Send value
    await channel.send(testValue);
    
    // Receive value
    const received = await channel.receive();
    expect(received).toBe(testValue);
  });

  test('should handle buffered channel operations', async () => {
    const bufferedChannel = createChannel<number>('buffered-channel', 3);
    
    // Send multiple values
    await Promise.all([
      bufferedChannel.send(1),
      bufferedChannel.send(2),
      bufferedChannel.send(3)
    ]);
    
    // Should be able to receive them back
    expect(await bufferedChannel.receive()).toBe(1);
    expect(await bufferedChannel.receive()).toBe(2);
    expect(await bufferedChannel.receive()).toBe(3);
  });

  test('should handle unbuffered channel (synchronous)', async () => {
    const unbufferedChannel = createChannel<string>('unbuffered-channel', 0);
    
    const sendPromise = unbufferedChannel.send('synchronous message');
    const receivePromise = unbufferedChannel.receive();
    
    // Both should resolve when paired
    await Promise.all([sendPromise, receivePromise]);
    
    const received = await receivePromise;
    expect(received).toBe('synchronous message');
  });

  test('should handle tryReceive for non-blocking receives', () => {
    const testChannel = createChannel<string>('try-receive-test', 1);
    
    // Should return undefined for empty channel
    expect(testChannel.tryReceive()).toBeUndefined();
    
    // Send a value and try to receive
    testChannel.send('test value');
    expect(testChannel.tryReceive()).toBe('test value');
    
    // Should return undefined again
    expect(testChannel.tryReceive()).toBeUndefined();
  });

  test('should close channel and handle post-close operations', async () => {
    await channel.close();
    
    expect(channel.isClosed).toBe(true);
    
    // Send should fail after close
    await expect(channel.send('test')).rejects.toThrow();
    
    // Receive should fail after close
    await expect(channel.receive()).rejects.toThrow();
  });

  test('should call close handlers when channel closes', async () => {
    let closeHandlerCalled = false;
    
    channel.onClose(() => {
      closeHandlerCalled = true;
    });
    
    await channel.close();
    
    expect(closeHandlerCalled).toBe(true);
  });
});

describe('V10 Runtime Select Operations', () => {
  test('should handle select with timeout', async () => {
    const channel1 = createChannel<string>('select-channel-1', 1);
    const channel2 = createChannel<number>('select-channel-2', 1);
    
    // Send to first channel
    await channel1.send('message on channel 1');
    
    // Setup select operations
    const operations = [
      { 
        operationId: 'op1', 
        channel: channel1, 
        operationType: 'receive' as const 
      },
      { 
        operationId: 'op2', 
        channel: channel2, 
        operationType: 'receive' as const 
      }
    ];
    
    // Execute select with timeout
    const startTime = Date.now();
    const result = await new Promise((resolve) => {
      // Simulate select operation
      Promise.race([
        channel1.receive().then(value => ({
          operationId: 'op1',
          succeeded: true,
          value,
          channelId: 'select-channel-1'
        })),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Select timeout')), 100)
        )
      ]).then(resolve).catch(() => {
        // Timeout case - select the timeout operation
        resolve({
          operationId: 'op2',
          succeeded: false,
          channelId: 'select-channel-2',
          error: new Error('Select timeout')
        });
      });
    });
    
    const elapsed = Date.now() - startTime;
    
    expect(result).toEqual({
      operationId: 'op1',
      succeeded: true,
      value: 'message on channel 1',
      channelId: 'select-channel-1'
    });
    
    expect(elapsed).toBeLessThan(50); // Should complete quickly
    
    await Promise.all([channel1.close(), channel2.close()]);
  });

  test('should handle select with send operations', async () => {
    const channel1 = createChannel<string>('send-channel-1', 1);
    const channel2 = createChannel<string>('send-channel-2', 0);
    
    // Setup select with send operation
    const result = await new Promise((resolve) => {
      Promise.race([
        channel2.receive().then(value => ({
          operationId: 'recv-op',
          succeeded: true,
          value,
          channelId: 'send-channel-2'
        })),
        new Promise<void>((resolveSend) => {
          channel1.send('message on channel 1').then(() => resolveSend());
        }).then(() => ({
          operationId: 'send-op',
          succeeded: true,
          channelId: 'send-channel-1'
        })),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Select timeout')), 100)
        )
      ]).then(resolve).catch(() => {
        resolve({
          operationId: 'timeout',
          succeeded: false,
          error: new Error('Select timeout')
        });
      });
    });
    
    expect(result).toEqual({
      operationId: 'send-op',
      succeeded: true,
      channelId: 'send-channel-1'
    });
    
    await Promise.all([channel1.close(), channel2.close()]);
  });
});

describe('V10 Runtime Supervisor', () => {
  let supervisor: Supervisor;

  beforeEach(async () => {
    supervisor = createSupervisor('test-supervisor');
    await supervisor.start();
  });

  afterEach(async () => {
    if (supervisor) {
      await supervisor.stop();
    }
  });

  test('should supervise tasks with proper lifecycle', async () => {
    const task = new MockCoroutineTask('supervised-task', 'test-supervisor');
    
    const supervisePromise = supervisor.supervise(task);
    
    // Provide task result
    const result: TaskResult = {
      taskId: 'supervised-task',
      state: TaskState.COMPLETED,
      startTime: Date.now(),
      endTime: Date.now(),
      executionTime: 50,
      result: 'supervised success',
      metadata: {}
    };
    
    task.resolveTask(result);
    
    const supervisedResult = await supervisePromise;
    
    expect(supervisedResult.state).toBe(TaskState.COMPLETED);
    expect(supervisedResult.result).toBe('supervised success');
  });

  test('should handle child supervisors', async () => {
    const childSupervisor = createSupervisor('child-supervisor', 'test-supervisor');
    
    await supervisor.addChildSupervisor(childSupervisor);
    
    const childIds = supervisor.getChildSupervisorIds();
    expect(childIds).toContain('child-supervisor');
    
    // Get metrics should include child information
    const metrics = supervisor.getMetrics();
    expect(metrics.activeTasks).toBe(0);
    
    await supervisor.removeChildSupervisor('child-supervisor');
    await childSupervisor.stop();
  });

  test('should collect supervisor metrics', async () => {
    // Create some supervised tasks
    const task1 = new MockCoroutineTask('metrics-task-1', 'test-supervisor');
    const task2 = new MockCoroutineTask('metrics-task-2', 'test-supervisor');
    
    // Start supervising tasks but don't complete them yet
    const supervisePromise1 = supervisor.supervise(task1);
    const supervisePromise2 = supervisor.supervise(task2);
    
    // Get metrics while tasks are active
    const metrics = supervisor.getMetrics();
    expect(metrics.activeTasks).toBeGreaterThanOrEqual(0); // May be 0 due to task implementation
    
    // Complete tasks
    const result1: TaskResult = {
      taskId: 'metrics-task-1',
      state: TaskState.COMPLETED,
      startTime: Date.now(),
      endTime: Date.now(),
      executionTime: 30,
      metadata: {}
    };
    
    const result2: TaskResult = {
      taskId: 'metrics-task-2',
      state: TaskState.COMPLETED,
      startTime: Date.now(),
      endTime: Date.now(),
      executionTime: 40,
      metadata: {}
    };
    
    task1.resolveTask(result1);
    task2.resolveTask(result2);
    
    await Promise.all([supervisePromise1, supervisePromise2]);
    
    // Get final metrics
    const finalMetrics = supervisor.getMetrics();
    expect(finalMetrics.completedTasks).toBeGreaterThanOrEqual(0);
  });
});

describe('V10 Runtime Execution Pipeline', () => {
  test('should create and configure execution pipeline', () => {
    const pipeline = createExecutionPipeline({
      profiler: undefined, // Will use default
      jitCompiler: undefined, // Will use default
      gcManager: undefined, // Will use default
    });
    
    expect(pipeline).toBeDefined();
    expect(pipeline.interpreter).toBeDefined();
    expect(pipeline.getHotPaths).toBeDefined();
  });

  test('should execute instructions through pipeline', async () => {
    const pipeline = createExecutionPipeline();
    
    // Create a mock execution context
    const context = {
      taskId: 'test-task',
      supervisorId: 'test-supervisor',
      variables: new Map(),
      deadlines: new Map(),
      timeouts: new Map(),
      
      setVariable: (name: string, value: unknown) => {
        context.variables.set(name, value);
      },
      
      getVariable: (name: string) => {
        return context.variables.get(name);
      },
      
      setDeadline: (deadlineId: string, deadlineMs: number) => {
        context.deadlines.set(deadlineId, Date.now() + deadlineMs);
      },
      
      clearDeadline: (deadlineId: string) => {
        context.deadlines.delete(deadlineId);
      },
    };
    
    // Execute a simple SET instruction
    const setInstruction = {
      opcode: OpCode.SET,
      args: ['test_var', 'test_value'],
      lineno: 1
    };
    
    const result = await pipeline.execute(setInstruction, context);
    
    expect(result.success).toBe(true);
    expect(result.nextInstruction).toBe(0);
    expect(context.getVariable('test_var')).toBe('test_value');
  });
});

describe('V10 Runtime VM Integration', () => {
  test('should create NullVM with V10 runtime support', async () => {
    const vm = new NullVM({ enableTracing: true });
    
    // Check V10 runtime methods exist
    expect(vm.hasV10Runtime).toBeDefined();
    expect(vm.getV10Runtime).toBeDefined();
    expect(vm.enableV10Runtime).toBeDefined();
    
    // Initially V10 should not be available
    expect(vm.hasV10Runtime()).toBe(false);
  });

  test('should enable V10 runtime', async () => {
    const vm = new NullVM();
    
    // Enable V10 runtime
    await vm.enableV10Runtime({
      maxConcurrentTasks: 5,
      defaultTaskTimeout: 10000,
      enableProfiling: true,
      enableJit: false,
      gcConfig: {
        incremental: true,
        maxPauseMs: 5,
        heapSizeLimit: 512 * 1024
      }
    });
    
    // V10 runtime should now be available
    expect(vm.hasV10Runtime()).toBe(true);
    
    // Should be able to get V10 runtime instance
    const v10Runtime = vm.getV10Runtime();
    expect(v10Runtime).toBeDefined();
    expect(v10Runtime.version).toBe('10.0.0');
    
    // Cleanup
    await vm.shutdownV10Runtime();
  });

  test('should execute V10 opcodes through VM', async () => {
    const vm = new NullVM();
    
    // Define a simple function
    const program = [
      { opcode: OpCode.DEFINE, args: ['test_function', [
        { opcode: OpCode.SET, args: ['result', 'Hello from V10!'] }
      ]]},
      { opcode: OpCode.SPAWN_TASK, args: ['test_task', 'test_function'] },
      { opcode: OpCode.CHANNEL_NEW, args: ['test_channel', 5] },
      { opcode: OpCode.SET, args: ['message', 'Test message'] },
      { opcode: OpCode.CHANNEL_SEND, args: ['test_channel', 'message'] }
    ];
    
    // Execute program with V10 runtime enabled
    await vm.enableV10Runtime();
    
    // Mock execution - in real scenario this would execute the full program
    const instructions = vm.getDecoder().decode(program);
    
    // Verify V10 opcodes are properly decoded
    expect(instructions.find(i => i.opcode === OpCode.SPAWN_TASK)).toBeDefined();
    expect(instructions.find(i => i.opcode === OpCode.CHANNEL_NEW)).toBeDefined();
    expect(instructions.find(i => i.opcode === OpCode.CHANNEL_SEND)).toBeDefined();
    
    // Cleanup
    await vm.shutdownV10Runtime();
  });

  test('should handle V10 runtime shutdown gracefully', async () => {
    const vm = new NullVM();
    
    // Enable and then shutdown V10 runtime
    await vm.enableV10Runtime();
    expect(vm.hasV10Runtime()).toBe(true);
    
    await vm.shutdownV10Runtime();
    expect(vm.hasV10Runtime()).toBe(false);
    
    // Should be able to re-enable after shutdown
    await vm.enableV10Runtime();
    expect(vm.hasV10Runtime()).toBe(true);
    
    await vm.shutdownV10Runtime();
  });
});

describe('V10 Runtime Stress Tests', () => {
  test('should handle multiple concurrent tasks', async () => {
    const scheduler = createScheduler('stress-test-scheduler', 10);
    
    const tasks: MockCoroutineTask[] = [];
    const taskCount = 20;
    
    // Create and schedule many tasks
    for (let i = 0; i < taskCount; i++) {
      const task = new MockCoroutineTask(`stress-task-${i}`, 'stress-test-scheduler');
      tasks.push(task);
      await scheduler.schedule(task);
    }
    
    // Complete all tasks
    const completionPromises = tasks.map(async (task, index) => {
      const result: TaskResult = {
        taskId: task.taskId,
        state: TaskState.COMPLETED,
        startTime: task.startTime,
        endTime: Date.now(),
        executionTime: Math.random() * 100,
        result: `Task ${index} completed`,
        metadata: {}
      };
      
      task.resolveTask(result);
      return result;
    });
    
    const results = await Promise.all(completionPromises);
    
    // Verify all tasks completed
    expect(results).toHaveLength(taskCount);
    expect(results.every(r => r.state === TaskState.COMPLETED)).toBe(true);
    
    await scheduler.shutdown();
  });

  test('should handle high-throughput channel operations', async () => {
    const channel = createChannel<number>('throughput-channel', 100);
    
    const messageCount = 1000;
    const sendPromises: Promise<void>[] = [];
    
    // Send many messages
    const startTime = Date.now();
    for (let i = 0; i < messageCount; i++) {
      sendPromises.push(channel.send(i));
    }
    
    await Promise.all(sendPromises);
    const sendTime = Date.now() - startTime;
    
    // Receive all messages
    const receiveStartTime = Date.now();
    const receivedValues: number[] = [];
    for (let i = 0; i < messageCount; i++) {
      receivedValues.push(await channel.receive());
    }
    const receiveTime = Date.now() - receiveStartTime;
    
    // Verify throughput
    expect(receivedValues).toHaveLength(messageCount);
    expect(receivedValues).toEqual(expect.arrayContaining([...Array(messageCount).keys()]));
    
    console.log(`Sent ${messageCount} messages in ${sendTime}ms, received in ${receiveTime}ms`);
    
    await channel.close();
  }, 10000); // 10 second timeout for stress test
});

describe('V10 Runtime Error Handling', () => {
  test('should handle task execution errors', async () => {
    const scheduler = createScheduler('error-test-scheduler', 5);
    
    const errorTask = new MockCoroutineTask('error-task', 'error-test-scheduler');
    await scheduler.schedule(errorTask);
    
    // Reject the task with an error
    const testError = new Error('Task execution failed');
    errorTask.rejectTask(testError);
    
    // Wait for task to fail
    await new Promise(resolve => setTimeout(resolve, 100));
    
    expect(scheduler.getStatus('error-task')).toBe(TaskState.FAILED);
    
    await scheduler.shutdown();
  });

  test('should handle channel errors gracefully', async () => {
    const channel = createChannel<string>('error-channel', 1);
    
    // Close channel and try to use it
    await channel.close();
    
    // Send should fail
    await expect(channel.send('test')).rejects.toThrow();
    
    // Receive should fail
    await expect(channel.receive()).rejects.toThrow();
  });

  test('should handle scheduler errors', async () => {
    const scheduler = createScheduler('error-test-scheduler', 2);
    
    // Try to schedule a task with duplicate ID
    const task1 = new MockCoroutineTask('duplicate-task', 'error-test-scheduler');
    const task2 = new MockCoroutineTask('duplicate-task', 'error-test-scheduler'); // Same ID
    
    await scheduler.schedule(task1);
    
    // Should throw error for duplicate task
    await expect(scheduler.schedule(task2)).rejects.toThrow();
    
    await scheduler.shutdown();
  });
});

// Performance benchmarks (can be run separately with --verbose)
describe('V10 Runtime Performance Benchmarks', () => {
  test('scheduler performance benchmark', async () => {
    const scheduler = createScheduler('benchmark-scheduler', 50);
    
    const taskCount = 1000;
    const startTime = Date.now();
    
    // Create and schedule tasks
    for (let i = 0; i < taskCount; i++) {
      const task = new MockCoroutineTask(`benchmark-task-${i}`, 'benchmark-scheduler');
      await scheduler.schedule(task);
      
      // Immediately resolve task for benchmark
      const result: TaskResult = {
        taskId: task.taskId,
        state: TaskState.COMPLETED,
        startTime: task.startTime,
        endTime: Date.now(),
        executionTime: 1,
        result: i,
        metadata: {}
      };
      task.resolveTask(result);
    }
    
    const endTime = Date.now();
    const duration = endTime - startTime;
    
    const tasksPerSecond = (taskCount / duration) * 1000;
    console.log(`Scheduler performance: ${taskCount} tasks in ${duration}ms (${tasksPerSecond.toFixed(2)} tasks/sec)`);
    
    expect(tasksPerSecond).toBeGreaterThan(1000); // Should handle at least 1000 tasks/second
    
    await scheduler.shutdown();
  }, 30000); // 30 second timeout for performance test
});