from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple


@dataclass(frozen=True)
class MetricSpec:
    name: str
    kind: str
    documentation: str
    labelnames: tuple[str, ...] = ()


METRIC_SPECS: tuple[MetricSpec, ...] = (
    MetricSpec(
        name="null_compilation_duration_seconds",
        kind="histogram",
        documentation="Total time spent compiling a program.",
        labelnames=("status",),
    ),
    MetricSpec(
        name="null_compilation_stage_duration_seconds",
        kind="histogram",
        documentation="Time spent in each compilation stage.",
        labelnames=("stage", "status"),
    ),
    MetricSpec(
        name="null_vm_execution_duration_seconds",
        kind="histogram",
        documentation="Total time spent executing a program in the VM.",
        labelnames=("status",),
    ),
    MetricSpec(
        name="null_vm_instructions_total",
        kind="counter",
        documentation="Total number of VM instructions executed.",
        labelnames=("opcode",),
    ),
    MetricSpec(
        name="null_vm_instruction_throughput",
        kind="gauge",
        documentation="Instruction throughput for the last VM execution (instructions/second).",
    ),
    MetricSpec(
        name="null_vm_stack_depth",
        kind="gauge",
        documentation="Current VM stack depth.",
    ),
    MetricSpec(
        name="null_vm_variable_count",
        kind="gauge",
        documentation="Current VM variable count.",
    ),
    MetricSpec(
        name="null_process_max_rss_bytes",
        kind="gauge",
        documentation="Process max resident set size (best-effort; platform dependent).",
    ),
    MetricSpec(
        name="null_errors_total",
        kind="counter",
        documentation="Total number of errors.",
        labelnames=("component", "error_type"),
    ),
)


class Metrics:
    def __init__(self, *, enabled: bool):
        self.enabled = enabled

        self._registry: Any | None = None
        self._compilation_duration = None
        self._compilation_stage_duration = None
        self._vm_execution_duration = None
        self._vm_instructions_total = None
        self._vm_instruction_throughput = None
        self._vm_stack_depth = None
        self._vm_variable_count = None
        self._process_max_rss_bytes = None
        self._errors_total = None

        if not enabled:
            return

        try:
            from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram  # type: ignore
        except Exception:
            self.enabled = False
            return

        self._registry = CollectorRegistry(auto_describe=True)

        self._compilation_duration = Histogram(
            "null_compilation_duration_seconds",
            "Total time spent compiling a program.",
            labelnames=["status"],
            registry=self._registry,
        )
        self._compilation_stage_duration = Histogram(
            "null_compilation_stage_duration_seconds",
            "Time spent in each compilation stage.",
            labelnames=["stage", "status"],
            registry=self._registry,
        )
        self._vm_execution_duration = Histogram(
            "null_vm_execution_duration_seconds",
            "Total time spent executing a program in the VM.",
            labelnames=["status"],
            registry=self._registry,
        )
        self._vm_instructions_total = Counter(
            "null_vm_instructions_total",
            "Total number of VM instructions executed.",
            labelnames=["opcode"],
            registry=self._registry,
        )
        self._vm_instruction_throughput = Gauge(
            "null_vm_instruction_throughput",
            "Instruction throughput for the last VM execution (instructions/second).",
            registry=self._registry,
        )
        self._vm_stack_depth = Gauge(
            "null_vm_stack_depth",
            "Current VM stack depth.",
            registry=self._registry,
        )
        self._vm_variable_count = Gauge(
            "null_vm_variable_count",
            "Current VM variable count.",
            registry=self._registry,
        )
        self._process_max_rss_bytes = Gauge(
            "null_process_max_rss_bytes",
            "Process max resident set size (best-effort; platform dependent).",
            registry=self._registry,
        )
        self._errors_total = Counter(
            "null_errors_total",
            "Total number of errors.",
            labelnames=["component", "error_type"],
            registry=self._registry,
        )

    def observe_compilation(self, *, duration_s: float, status: str) -> None:
        if self.enabled and self._compilation_duration is not None:
            self._compilation_duration.labels(status=status).observe(duration_s)

    def observe_compilation_stage(self, *, stage: str, duration_s: float, status: str) -> None:
        if self.enabled and self._compilation_stage_duration is not None:
            self._compilation_stage_duration.labels(stage=stage, status=status).observe(duration_s)

    def observe_vm_execution(self, *, duration_s: float, status: str) -> None:
        if self.enabled and self._vm_execution_duration is not None:
            self._vm_execution_duration.labels(status=status).observe(duration_s)

    def inc_vm_instruction(self, *, opcode: str) -> None:
        if self.enabled and self._vm_instructions_total is not None:
            self._vm_instructions_total.labels(opcode=opcode).inc()

    def set_vm_instruction_throughput(self, value: float) -> None:
        if self.enabled and self._vm_instruction_throughput is not None:
            self._vm_instruction_throughput.set(value)

    def set_vm_stack_depth(self, value: int) -> None:
        if self.enabled and self._vm_stack_depth is not None:
            self._vm_stack_depth.set(value)

    def set_vm_variable_count(self, value: int) -> None:
        if self.enabled and self._vm_variable_count is not None:
            self._vm_variable_count.set(value)

    def set_process_max_rss_bytes(self, value: int) -> None:
        if self.enabled and self._process_max_rss_bytes is not None:
            self._process_max_rss_bytes.set(value)

    def inc_error(self, *, component: str, error_type: str) -> None:
        if self.enabled and self._errors_total is not None:
            self._errors_total.labels(component=component, error_type=error_type).inc()

    def render(self) -> Tuple[bytes, str]:
        if not self.enabled or self._registry is None:
            return b"", "text/plain"

        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest  # type: ignore

        return generate_latest(self._registry), CONTENT_TYPE_LATEST


def create_metrics(*, enabled: bool) -> Metrics:
    return Metrics(enabled=enabled)
