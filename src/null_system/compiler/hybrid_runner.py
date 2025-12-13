"""
Hybrid executor runner for NullCompiler
Provides gRPC client interface for distributed execution
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Instruction:
    """Represents a NullVM instruction"""
    opcode: str
    args: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {"opcode": self.opcode, "args": self.args}


@dataclass
class ExecutionResult:
    """Result of program execution"""
    task_id: str
    vm_id: str
    status: str
    registers: Dict[str, int]
    execution_cycles: int
    duration: float
    error: Optional[str] = None
    checkpoint_id: Optional[str] = None


class HybridExecutorClient:
    """Client for distributed NullVM execution"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 50051,
        enable_checkpointing: bool = True,
    ):
        """Initialize the hybrid executor client

        Args:
            host: Server host address
            port: Server port
            enable_checkpointing: Enable automatic checkpointing
        """
        self.host = host
        self.port = port
        self.enable_checkpointing = enable_checkpointing
        self.channel = None
        self.stub = None
        self.pending_tasks: Dict[str, ExecutionResult] = {}

    async def connect(self) -> None:
        """Establish connection to the hybrid executor server"""
        try:
            # Note: Full gRPC implementation would go here
            # For now, this is a stub that demonstrates the API
            logger.info(f"Connecting to hybrid executor at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to executor: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to the executor"""
        if self.channel:
            await self.channel.close()

    async def execute_program(
        self,
        instructions: List[Instruction],
        vm_id: Optional[str] = None,
        priority: int = 0,
    ) -> str:
        """Submit a program for execution

        Args:
            instructions: List of NullVM instructions
            vm_id: Target VM ID (optional)
            priority: Task priority

        Returns:
            Task ID for tracking execution
        """
        request = {
            "vmId": vm_id or f"vm-{id(instructions)}",
            "instructions": [i.to_dict() for i in instructions],
            "priority": priority,
        }

        try:
            # In a full implementation, this would send a gRPC request
            task_id = f"task-{id(request)}"
            logger.info(f"Submitted task {task_id} with {len(instructions)} instructions")
            return task_id
        except Exception as e:
            logger.error(f"Failed to execute program: {e}")
            raise

    async def get_task_status(self, task_id: str) -> ExecutionStatus:
        """Get the status of a submitted task

        Args:
            task_id: Task ID from execute_program

        Returns:
            Current execution status
        """
        try:
            # In a full implementation, this would query gRPC
            if task_id in self.pending_tasks:
                return ExecutionStatus(self.pending_tasks[task_id].status)
            return ExecutionStatus.PENDING
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            raise

    async def get_result(self, task_id: str, timeout: float = 30.0) -> ExecutionResult:
        """Wait for and retrieve execution result

        Args:
            task_id: Task ID from execute_program
            timeout: Maximum time to wait (seconds)

        Returns:
            ExecutionResult with registers and status
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            if task_id in self.pending_tasks:
                result = self.pending_tasks[task_id]
                if result.status in ["completed", "failed"]:
                    return result

            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")

            await asyncio.sleep(0.1)

    async def batch_execute(
        self, task_configs: List[Dict[str, Any]]
    ) -> List[ExecutionResult]:
        """Execute multiple tasks in parallel

        Args:
            task_configs: List of task configurations

        Returns:
            List of execution results
        """
        tasks = []
        for config in task_configs:
            instructions = [Instruction(**i) for i in config.get("instructions", [])]
            task_id = await self.execute_program(
                instructions,
                vm_id=config.get("vmId"),
                priority=config.get("priority", 0),
            )
            tasks.append(self.get_result(task_id))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, ExecutionResult)]

    async def get_metrics(self) -> Dict[str, Any]:
        """Get executor metrics

        Returns:
            Metrics dictionary with throughput, latency, etc.
        """
        try:
            # In a full implementation, this would query gRPC
            return {
                "totalTasksScheduled": len(self.pending_tasks),
                "totalTasksCompleted": sum(
                    1 for r in self.pending_tasks.values() if r.status == "completed"
                ),
                "totalTasksFailed": sum(
                    1 for r in self.pending_tasks.values() if r.status == "failed"
                ),
                "averageLatency": 0.0,
                "throughput": 0.0,
            }
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            raise

    async def create_checkpoint(self, vm_id: str) -> str:
        """Create a checkpoint for a VM

        Args:
            vm_id: VM ID

        Returns:
            Checkpoint ID
        """
        try:
            checkpoint_id = f"checkpoint-{vm_id}-{id(vm_id)}"
            logger.info(f"Created checkpoint {checkpoint_id} for VM {vm_id}")
            return checkpoint_id
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            raise

    async def recover_from_checkpoint(
        self, vm_id: str, checkpoint_id: str
    ) -> bool:
        """Recover a VM from a checkpoint

        Args:
            vm_id: VM ID
            checkpoint_id: Checkpoint ID

        Returns:
            True if recovery succeeded
        """
        try:
            logger.info(f"Recovering VM {vm_id} from checkpoint {checkpoint_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to recover from checkpoint: {e}")
            return False


class HybridCompilerBridge:
    """Bridge between NullCompiler and hybrid executor"""

    def __init__(self, executor_host: str = "localhost", executor_port: int = 50051):
        """Initialize the compiler bridge

        Args:
            executor_host: Hybrid executor server host
            executor_port: Hybrid executor server port
        """
        self.client = HybridExecutorClient(executor_host, executor_port)
        self.compiled_programs: Dict[str, List[Instruction]] = {}

    async def initialize(self) -> None:
        """Initialize the bridge and connect to executor"""
        await self.client.connect()

    async def shutdown(self) -> None:
        """Shutdown and disconnect from executor"""
        await self.client.disconnect()

    async def submit_compiled_program(
        self,
        program_id: str,
        instructions: List[Instruction],
        vm_id: Optional[str] = None,
        priority: int = 0,
    ) -> str:
        """Submit a compiled program for distributed execution

        Args:
            program_id: Unique program identifier
            instructions: Compiled instructions
            vm_id: Target VM ID (optional)
            priority: Execution priority

        Returns:
            Task ID for tracking
        """
        self.compiled_programs[program_id] = instructions
        return await self.client.execute_program(instructions, vm_id, priority)

    async def get_execution_result(
        self, task_id: str, timeout: float = 30.0
    ) -> ExecutionResult:
        """Get result of execution

        Args:
            task_id: Task ID from submit_compiled_program
            timeout: Maximum wait time

        Returns:
            ExecutionResult
        """
        return await self.client.get_result(task_id, timeout)

    async def monitor_execution(
        self, task_id: str, poll_interval: float = 0.1
    ) -> ExecutionResult:
        """Monitor execution with periodic polling

        Args:
            task_id: Task ID
            poll_interval: Polling interval in seconds

        Returns:
            Final ExecutionResult
        """
        while True:
            status = await self.client.get_task_status(task_id)

            if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]:
                return await self.client.get_result(task_id)

            await asyncio.sleep(poll_interval)

    async def get_executor_health(self) -> Dict[str, Any]:
        """Get executor health and metrics

        Returns:
            Health metrics
        """
        metrics = await self.client.get_metrics()
        return {
            "healthy": metrics["totalTasksFailed"] == 0,
            "metrics": metrics,
        }

    def parse_program_string(self, program_str: str) -> List[Instruction]:
        """Parse a program string into instructions

        Args:
            program_str: Program string (semicolon-separated instructions)

        Returns:
            List of Instruction objects
        """
        instructions = []
        for line in program_str.split(";"):
            line = line.strip()
            if not line:
                continue

            tokens = line.split()
            opcode = tokens[0]
            args = tokens[1:]
            instructions.append(Instruction(opcode, args))

        return instructions


# Example usage
async def main():
    """Example of using the hybrid executor bridge"""
    bridge = HybridCompilerBridge()
    await bridge.initialize()

    # Parse and submit a program
    program_str = "SET x 10; ADD x 5; SHOW x"
    instructions = bridge.parse_program_string(program_str)

    task_id = await bridge.submit_compiled_program(
        "example-program",
        instructions,
        priority=5,
    )

    # Monitor execution
    result = await bridge.monitor_execution(task_id)
    print(f"Execution result: {result}")

    await bridge.shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
