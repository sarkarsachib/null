"""Lightweight stub executor for hybrid execution testing."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from null_system.superbit.ir import SuperBitStream, SuperBitIRToken, SuperBitOpCode
from null_system.vm.vm import ExecutionResult


class AcceleratorType(Enum):
    CPU = "cpu"
    GPU = "gpu"
    ML_ENGINE = "ml_engine"
    NLP_ENGINE = "nlp_engine"


@dataclass
class AcceleratorTask:
    task_id: str
    accelerator: AcceleratorType
    tokens: List[SuperBitIRToken]
    state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AcceleratorResult:
    task_id: str
    success: bool
    state: Dict[str, Any] = field(default_factory=dict)
    output: List[str] = field(default_factory=list)
    error: str = ""


class MockAccelerator:
    def __init__(self, accelerator_type: AcceleratorType):
        self.accelerator_type = accelerator_type
        self.task_count = 0
        self.failed_tasks = 0
        
    def execute(self, task: AcceleratorTask) -> AcceleratorResult:
        self.task_count += 1
        
        if self.accelerator_type == AcceleratorType.GPU:
            return self._execute_gpu(task)
        elif self.accelerator_type == AcceleratorType.ML_ENGINE:
            return self._execute_ml(task)
        elif self.accelerator_type == AcceleratorType.NLP_ENGINE:
            return self._execute_nlp(task)
        else:
            return self._execute_cpu(task)
    
    def _execute_cpu(self, task: AcceleratorTask) -> AcceleratorResult:
        state = task.state.copy()
        output = []
        
        for token in task.tokens:
            if token.opcode == SuperBitOpCode.LOAD_CONST:
                state[f"_stack_{len(state)}"] = token.operand
            elif token.opcode == SuperBitOpCode.BINARY_ADD:
                if "_stack_0" in state and "_stack_1" in state:
                    result = state["_stack_0"] + state["_stack_1"]
                    state = {"_result": result}
        
        return AcceleratorResult(
            task_id=task.task_id,
            success=True,
            state=state,
            output=output
        )
    
    def _execute_gpu(self, task: AcceleratorTask) -> AcceleratorResult:
        state = task.state.copy()
        state["_accelerated"] = "gpu"
        state["_speedup"] = 2.5
        
        return AcceleratorResult(
            task_id=task.task_id,
            success=True,
            state=state,
            output=[f"GPU accelerated {len(task.tokens)} operations"]
        )
    
    def _execute_ml(self, task: AcceleratorTask) -> AcceleratorResult:
        state = task.state.copy()
        state["_ml_inference"] = True
        state["_model"] = "mock_model"
        
        return AcceleratorResult(
            task_id=task.task_id,
            success=True,
            state=state,
            output=["ML inference completed"]
        )
    
    def _execute_nlp(self, task: AcceleratorTask) -> AcceleratorResult:
        state = task.state.copy()
        state["_nlp_processed"] = True
        state["_tokens_processed"] = len(task.tokens)
        
        return AcceleratorResult(
            task_id=task.task_id,
            success=True,
            state=state,
            output=["NLP processing completed"]
        )


class HybridExecutor:
    def __init__(self):
        self.accelerators: Dict[AcceleratorType, MockAccelerator] = {
            AcceleratorType.CPU: MockAccelerator(AcceleratorType.CPU),
            AcceleratorType.GPU: MockAccelerator(AcceleratorType.GPU),
            AcceleratorType.ML_ENGINE: MockAccelerator(AcceleratorType.ML_ENGINE),
            AcceleratorType.NLP_ENGINE: MockAccelerator(AcceleratorType.NLP_ENGINE),
        }
        self.task_counter = 0
        self.offload_strategy: Optional[Callable[[List[SuperBitIRToken]], AcceleratorType]] = None
    
    def set_offload_strategy(self, strategy: Callable[[List[SuperBitIRToken]], AcceleratorType]):
        self.offload_strategy = strategy
    
    def execute_hybrid(self, superbit_stream: SuperBitStream, 
                      initial_state: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        if initial_state is None:
            initial_state = {}
        
        tokens = superbit_stream.tokens
        
        if not self.offload_strategy:
            accelerator_type = AcceleratorType.CPU
        else:
            accelerator_type = self.offload_strategy(tokens)
        
        task = AcceleratorTask(
            task_id=f"task_{self.task_counter}",
            accelerator=accelerator_type,
            tokens=tokens,
            state=initial_state
        )
        self.task_counter += 1
        
        accelerator = self.accelerators[accelerator_type]
        result = accelerator.execute(task)
        
        return ExecutionResult(
            success=result.success,
            output=result.output,
            error=result.error,
            final_state=result.state
        )
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_tasks": self.task_counter,
            "accelerator_usage": {
                acc_type.value: acc.task_count
                for acc_type, acc in self.accelerators.items()
            }
        }
    
    def reset(self):
        self.task_counter = 0
        for accelerator in self.accelerators.values():
            accelerator.task_count = 0
            accelerator.failed_tasks = 0


def simple_offload_strategy(tokens: List[SuperBitIRToken]) -> AcceleratorType:
    if any(token.metadata.get("layer") == "ml" for token in tokens):
        return AcceleratorType.ML_ENGINE
    elif any(token.metadata.get("layer") == "nlp" for token in tokens):
        return AcceleratorType.NLP_ENGINE
    elif len(tokens) > 10:
        return AcceleratorType.GPU
    else:
        return AcceleratorType.CPU
