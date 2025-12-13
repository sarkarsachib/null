#!/usr/bin/env ts-node
/**
 * NullVM CLI - Hybrid executor entry point
 */

import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import pino from 'pino';
import { NullVM } from '../null_system/vm';
import { DistributedExecutor } from '../null_system/vm/distributed';
import { Instruction, OpCode } from '../null_system/vm';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  transport: {
    target: 'pino-pretty',
    options: {
      colorize: true,
    },
  },
});

interface RunArgs {
  file?: string;
  program?: string;
  vmId?: string;
  tracing?: boolean;
  maxCycles?: number;
}

interface BenchmarkArgs {
  workers: number;
  taskCount: number;
  taskSize: number;
  duration?: number;
  output?: string;
}

interface ServerArgs {
  port: number;
  nodeId?: string;
  listenAddr?: string;
  peers?: string;
  workers?: number;
}

async function runProgram(args: RunArgs): Promise<void> {
  logger.info('Starting NullVM execution...');

  const config = {
    enableTracing: args.tracing || false,
    maxCycles: args.maxCycles || 10000,
    vmId: args.vmId || `vm-cli-${Date.now()}`,
  };

  const vm = new NullVM(config);

  let program: Instruction[] = [];

  if (args.program) {
    // Parse inline program (simple format: "SET x 10; ADD x 5; SHOW x")
    const parts = args.program.split(';').map((p) => p.trim());
    program = parts.map((part) => {
      const tokens = part.split(/\s+/);
      const opcode = tokens[0] as OpCode;
      const args = tokens.slice(1);
      return { opcode, args };
    });
  } else {
    // For now, create a simple test program
    program = [
      { opcode: OpCode.SET, args: ['x', '42'] },
      { opcode: OpCode.SHOW, args: ['x'] },
    ];
  }

  try {
    vm.execute(program);
    const state = vm.getState();
    logger.info({ state }, 'Execution completed');
  } catch (error) {
    logger.error({ error }, 'Execution failed');
    process.exit(1);
  }
}

async function benchmark(args: BenchmarkArgs): Promise<void> {
  logger.info(
    {
      workers: args.workers,
      taskCount: args.taskCount,
      taskSize: args.taskSize,
    },
    'Starting benchmark...'
  );

  const executor = new DistributedExecutor({
    nodeId: `bench-node-${Date.now()}`,
    listenAddr: 'localhost',
    listenPort: 50051,
    maxWorkers: args.workers,
    enableCheckpointing: true,
    checkpointInterval: 5000,
    heartbeatInterval: 2000,
  });

  await executor.initialize();

  // Register VMs as workers
  for (let i = 0; i < args.workers; i++) {
    const vm = new NullVM({ vmId: `worker-${i}` });
    executor.registerVM(`worker-${i}`, vm);
  }

  const startTime = Date.now();
  const results: any[] = [];

  // Create tasks
  for (let i = 0; i < args.taskCount; i++) {
    const instructions: Instruction[] = [];
    for (let j = 0; j < args.taskSize; j++) {
      instructions.push({ opcode: OpCode.SET, args: [`r${j}`, String(j)] });
      instructions.push({
        opcode: OpCode.ADD,
        args: [`r${j}`, String(j + 1)],
      });
    }

    const vmId = `worker-${i % args.workers}`;
    const result = await executor.executeOnVM(
      vmId,
      instructions,
      Math.floor(Math.random() * 10)
    );
    results.push(result);

    if ((i + 1) % 100 === 0) {
      logger.info(`Completed ${i + 1}/${args.taskCount} tasks`);
    }
  }

  const totalDuration = Date.now() - startTime;
  const successCount = results.filter((r) => r.status === 'success').length;
  const failureCount = results.length - successCount;
  const avgLatency = totalDuration / results.length;
  const throughput = (results.length / totalDuration) * 1000;

  const metrics = executor.getMetrics();

  logger.info(
    {
      totalDuration,
      tasksCompleted: results.length,
      successCount,
      failureCount,
      avgLatency: `${avgLatency.toFixed(2)}ms`,
      throughput: `${throughput.toFixed(2)} tasks/sec`,
      metrics,
    },
    'Benchmark completed'
  );

  // Write results to file if specified
  if (args.output) {
    const fs = require('fs');
    fs.writeFileSync(
      args.output,
      JSON.stringify(
        {
          benchmark: {
            workers: args.workers,
            taskCount: args.taskCount,
            taskSize: args.taskSize,
            totalDuration,
            successCount,
            failureCount,
            avgLatency,
            throughput,
            metrics,
          },
          results,
        },
        null,
        2
      )
    );
    logger.info(`Results written to ${args.output}`);
  }

  await executor.shutdown();
}

async function startServer(args: ServerArgs): Promise<void> {
  logger.info(
    {
      port: args.port,
      nodeId: args.nodeId,
      listenAddr: args.listenAddr,
      workers: args.workers,
    },
    'Starting NullVM hybrid executor server...'
  );

  const executor = new DistributedExecutor({
    nodeId: args.nodeId || `node-${Date.now()}`,
    listenAddr: args.listenAddr || 'localhost',
    listenPort: args.port,
    maxWorkers: args.workers || 10,
    enableCheckpointing: true,
    checkpointInterval: 5000,
    heartbeatInterval: 2000,
  });

  if (args.peers) {
    const peers = args.peers.split(',').map((p) => {
      const [addr, port] = p.split(':');
      return { addr, port: parseInt(port, 10) };
    });
    logger.info({ peers }, 'Connecting to peers');
  }

  await executor.initialize();

  // Register worker VMs
  for (let i = 0; i < (args.workers || 10); i++) {
    const vm = new NullVM({ vmId: `worker-${i}` });
    executor.registerVM(`worker-${i}`, vm);
  }

  logger.info('Executor ready to receive work');

  // Keep server running
  process.on('SIGINT', async () => {
    logger.info('Shutting down...');
    await executor.shutdown();
    process.exit(0);
  });
}

yargs(hideBin(process.argv))
  .command(
    'run',
    'Execute a NullVM program',
    (builder) =>
      builder
        .option('file', { describe: 'Program file to execute' })
        .option('program', { describe: 'Inline program string' })
        .option('vmId', { describe: 'VM ID' })
        .option('tracing', { describe: 'Enable tracing', type: 'boolean' })
        .option('maxCycles', { describe: 'Maximum execution cycles', type: 'number' }),
    (args) => runProgram(args as RunArgs)
  )
  .command(
    'benchmark',
    'Run hybrid executor benchmark',
    (builder) =>
      builder
        .option('workers', {
          describe: 'Number of workers',
          type: 'number',
          default: 10,
        })
        .option('taskCount', {
          describe: 'Number of tasks',
          type: 'number',
          default: 1000,
        })
        .option('taskSize', {
          describe: 'Instructions per task',
          type: 'number',
          default: 100,
        })
        .option('duration', { describe: 'Benchmark duration (seconds)', type: 'number' })
        .option('output', { describe: 'Output file for results' }),
    (args) => benchmark(args as BenchmarkArgs)
  )
  .command(
    'server',
    'Start hybrid executor server',
    (builder) =>
      builder
        .option('port', {
          describe: 'Server port',
          type: 'number',
          default: 50051,
        })
        .option('nodeId', { describe: 'Node ID' })
        .option('listenAddr', {
          describe: 'Listen address',
          default: 'localhost',
        })
        .option('peers', { describe: 'Peer addresses (comma-separated)' })
        .option('workers', { describe: 'Number of workers', type: 'number' }),
    (args) => startServer(args as ServerArgs)
  )
  .help()
  .alias('help', 'h')
  .alias('version', 'v')
  .demandCommand()
  .strict()
  .parse();
