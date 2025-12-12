# Hybrid Runtime Layer

The Hybrid Runtime Layer enables concurrent and distributed execution across multiple NullVM instances, allowing them to cooperate and share workloads efficiently.

## Architecture

The hybrid runtime consists of several key components:

1. **HybridExecutionManager**: Orchestrates multiple VM instances
2. **WorkScheduler**: Distributes work across VMs using various strategies
3. **SuperBitMessageBus**: Handles message passing with retry and timeout logic
4. **TransportAdapter**: Abstraction for communication (worker threads, WebSocket, IPC)
5. **WorkerThreadAdapter**: Implementation for in-process worker threads

## Configuration

### NullVMConfig Extensions

```typescript
interface NullVMConfig {
  vmId?: string;
  hybridRuntime?: {
    enabled: boolean;
    manager?: HybridExecutionManager;
    capabilities?: Partial<VMCapabilities>;
    config?: HybridExecutionConfig;
  };
}
```

### HybridExecutionConfig

```typescript
interface HybridExecutionConfig {
  loadBalancingStrategy?: 'round-robin' | 'work-stealing' | 'least-loaded';
  maxTasksPerWorker?: number;
  enableAutoRestart?: boolean;
  healthCheckIntervalMs?: number;
  maxRetries?: number;
}
```

### VMCapabilities

```typescript
interface VMCapabilities {
  vmId: string;
  maxConcurrentTasks: number;
  supportedMessageTypes: string[];
  customMetadata?: Record<string, unknown>;
}
```

## New Opcodes

### SPAWN_VM

Spawns a new child VM instance.

```typescript
{ opcode: OpCode.SPAWN_VM, args: ['vm-id', configObject] }
```

**Arguments:**
- `vm-id` (string): Unique identifier for the new VM
- `configObject` (object): VM capabilities configuration

**Example:**
```typescript
const program = [
  { opcode: OpCode.SPAWN_VM, args: ['worker-1', { maxConcurrentTasks: 10 }] },
];
```

### SEND_MSG

Sends a message to another VM.

```typescript
{ opcode: OpCode.SEND_MSG, args: ['target-vm-id', 'message-type', payload] }
```

**Arguments:**
- `target-vm-id` (string): Destination VM identifier
- `message-type` (string): Type of message (e.g., 'DATA', 'CONTROL')
- `payload` (any): Message payload

**Example:**
```typescript
const program = [
  { opcode: OpCode.SEND_MSG, args: ['worker-2', 'DATA', { value: 42 }] },
];
```

### RECV_MSG

Receives a message from the queue.

```typescript
{ opcode: OpCode.RECV_MSG, args: ['result-register', timeoutMs] }
```

**Arguments:**
- `result-register` (string): Register to store the received value
- `timeoutMs` (number, optional): Timeout in milliseconds

**Example:**
```typescript
const program = [
  { opcode: OpCode.RECV_MSG, args: ['msg', 5000] },
  { opcode: OpCode.SHOW, args: ['msg'] },
];
```

### SYNC_BARRIER

Synchronizes multiple VMs at a barrier point.

```typescript
{ opcode: OpCode.SYNC_BARRIER, args: ['barrier-id', timeoutMs] }
```

**Arguments:**
- `barrier-id` (string): Unique barrier identifier
- `timeoutMs` (number, optional): Timeout in milliseconds

**Example:**
```typescript
const program = [
  { opcode: OpCode.SET, args: ['x', 10] },
  { opcode: OpCode.SYNC_BARRIER, args: ['checkpoint-1', 5000] },
  { opcode: OpCode.ADD, args: ['x', 5] },
];
```

## Usage Examples

### Basic Multi-VM Setup

```typescript
import { NullVM } from './null_vm';
import { HybridExecutionManager } from './hybrid_runtime';
import { WorkerThreadAdapter } from './hybrid_runtime/worker_adapter';

// Create transport adapter
const adapter = new WorkerThreadAdapter();

// Create manager
const manager = new HybridExecutionManager(adapter, {
  loadBalancingStrategy: 'round-robin',
  maxTasksPerWorker: 10,
  enableAutoRestart: true,
});

await manager.initialize();

// Create VMs
const vm1 = new NullVM({
  vmId: 'worker-1',
  hybridRuntime: {
    enabled: true,
    manager,
    capabilities: {
      maxConcurrentTasks: 10,
      supportedMessageTypes: ['WORK', 'DATA'],
    },
  },
});

const vm2 = new NullVM({
  vmId: 'worker-2',
  hybridRuntime: {
    enabled: true,
    manager,
  },
});
```

### Message Passing

```typescript
// VM1 sends message to VM2
await vm1.sendMessageToVM('worker-2', 'DATA', { value: 42 });

// VM2 receives the message
vm2.queueMessage('DATA', 42);

const program = [
  { opcode: OpCode.RECV_MSG, args: ['result', 1000] },
  { opcode: OpCode.SHOW, args: ['result'] },
];

vm2.execute(program);
```

### Barrier Synchronization

```typescript
// Create barrier for 2 participants
await manager.createBarrier('sync-point', 2);

// Both VMs arrive at barrier
await Promise.all([
  vm1.joinBarrier('sync-point'),
  vm2.joinBarrier('sync-point'),
]);

console.log('Both VMs synchronized!');
```

### Spawning Child VMs

```typescript
// Programmatically spawn child VM
const child = await vm1.spawnChildVM('child-1', {
  maxConcurrentTasks: 5,
  supportedMessageTypes: ['DATA'],
});

// Or use opcode
const program = [
  { opcode: OpCode.SPAWN_VM, args: ['child-2', {}] },
];

vm1.execute(program);
```

## Load Balancing Strategies

### Round-Robin

Distributes work evenly across all available VMs in a circular fashion.

```typescript
const manager = new HybridExecutionManager(adapter, {
  loadBalancingStrategy: 'round-robin',
});
```

### Work-Stealing

Assigns work to the least loaded VM. If load imbalance exceeds threshold, work is "stolen" from heavily loaded VMs.

```typescript
const manager = new HybridExecutionManager(adapter, {
  loadBalancingStrategy: 'work-stealing',
});
```

### Least-Loaded

Always assigns work to the VM with the lowest current workload.

```typescript
const manager = new HybridExecutionManager(adapter, {
  loadBalancingStrategy: 'least-loaded',
});
```

## Fault Recovery

The hybrid runtime includes automatic fault recovery:

1. **Health Monitoring**: VMs report health status periodically
2. **Auto-Restart**: Failed workers are automatically restarted (if enabled)
3. **Message Replay**: In-flight messages are replayed after restart
4. **Graceful Degradation**: System continues operating with remaining healthy VMs

```typescript
const manager = new HybridExecutionManager(adapter, {
  enableAutoRestart: true,
  healthCheckIntervalMs: 5000,
  maxRetries: 3,
});

// Register fault callback
adapter.registerFaultCallback((vmId, error) => {
  console.error(`VM ${vmId} failed:`, error);
});
```

## Backpressure

The system automatically applies backpressure when:
- Message queue exceeds maximum size
- VM workload exceeds 80% of capacity
- Transport buffer is full

```typescript
// Check if backpressure is active
const stats = manager.getStats();
console.log('Backpressure:', stats.scheduler.backpressureActive);

// Message bus will throw error if queue is full
try {
  await manager.sendMessage('vm-1', 'vm-2', 'DATA', payload);
} catch (error) {
  if (error.message.includes('backpressure')) {
    // Handle backpressure
    await delay(100);
    // Retry
  }
}
```

## Logging and Monitoring

### Register Log Hooks

```typescript
manager.registerLogHook((message, data) => {
  console.log(`[HybridRuntime] ${message}`, data);
});
```

### Access Statistics

```typescript
const stats = manager.getStats();
/*
{
  registeredVMs: 3,
  healthyVMs: 3,
  scheduler: {
    queueLength: 5,
    availableVMs: 3,
    totalWorkload: 12,
    vmWorkloads: { 'vm-1': 4, 'vm-2': 4, 'vm-3': 4 },
    backpressureActive: false
  },
  pendingMessages: 2,
  activeBarriers: 1
}
*/
```

### VM State Inspection

```typescript
const state = vm.getState();
/*
{
  memory: {...},
  context: {...},
  executionCycle: 42,
  binaryFrameCount: 10,
  vmId: 'worker-1',
  childVMCount: 2,
  messageQueueSize: 1
}
*/
```

## Transport Adapters

### WorkerThreadAdapter (Built-in)

Uses Node.js worker_threads for in-process parallelism.

```typescript
import { WorkerThreadAdapter } from './hybrid_runtime/worker_adapter';

const adapter = new WorkerThreadAdapter();
await adapter.initialize();
```

### Custom Transport Adapter

Implement the `TransportAdapter` interface for remote execution:

```typescript
import { BaseTransportAdapter, SuperBitMessage } from './hybrid_runtime';

class WebSocketAdapter extends BaseTransportAdapter {
  readonly adapterId = 'websocket';

  async initialize(): Promise<void> {
    // Setup WebSocket connections
  }

  async sendMessage(message: SuperBitMessage): Promise<void> {
    // Send via WebSocket
  }

  async advertiseCapabilities(capabilities: VMCapabilities): Promise<void> {
    // Broadcast capabilities
  }

  async discoverVMs(): Promise<VMCapabilities[]> {
    // Query available VMs
  }

  async close(): Promise<void> {
    // Cleanup connections
  }
}
```

## Super-Bit Message Format

Messages are serialized using the super-bit encoding format:

```
[message_id (uuid)] [source_vm_id] [target_vm_id] [message_type] [payload (Buffer)] [timestamp]
```

The payload is serialized to JSON and then converted to Buffer for transport.

## Configuration Knobs Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `loadBalancingStrategy` | string | 'round-robin' | Work distribution strategy |
| `maxTasksPerWorker` | number | 10 | Maximum concurrent tasks per VM |
| `enableAutoRestart` | boolean | true | Automatically restart failed workers |
| `healthCheckIntervalMs` | number | undefined | Health check interval (disabled if not set) |
| `maxRetries` | number | 3 | Maximum message retry attempts |
| `retryDelayMs` | number | 1000 | Delay between retries |
| `messageTimeoutMs` | number | 30000 | Message timeout duration |

## Best Practices

1. **VM IDs**: Use descriptive, unique IDs for VMs
2. **Capabilities**: Accurately advertise VM capabilities
3. **Message Types**: Use consistent message type naming
4. **Barriers**: Always specify timeouts for barriers
5. **Error Handling**: Handle message failures and timeouts gracefully
6. **Monitoring**: Register log hooks for production deployments
7. **Cleanup**: Always call `manager.shutdown()` when done

## Performance Considerations

- Worker thread overhead is minimal for CPU-intensive tasks
- Message passing has serialization overhead
- Barrier synchronization can block all participants
- Consider work granularity when distributing tasks
- Monitor backpressure and adjust `maxTasksPerWorker` accordingly

## Limitations

- Current implementation focuses on worker threads
- Remote transport adapters are stubs (WebSocket/IPC implementations needed)
- Message serialization limited to JSON-serializable payloads
- No built-in priority-based message routing
- Barrier timeout handling is basic

## Future Enhancements

- Advanced remote transport implementations (WebSocket, gRPC, IPC)
- Priority-based message queuing
- Dynamic load rebalancing
- Distributed barrier algorithms
- Enhanced fault tolerance with checkpointing
- Custom serialization formats beyond JSON
