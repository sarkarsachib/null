from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Iterator


@dataclass(frozen=True)
class TracingConfig:
    enabled: bool
    service_name: str
    endpoint: str | None = None

    @classmethod
    def from_env(cls, *, enabled: bool, service_name: str) -> "TracingConfig":
        endpoint = os.getenv("NULL_OTEL_EXPORTER_OTLP_ENDPOINT") or os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT"
        )
        return cls(enabled=enabled, service_name=service_name, endpoint=endpoint)


class Tracing:
    def __init__(self, *, enabled: bool):
        self.enabled = enabled
        self._tracer = None

    @contextmanager
    def span(self, name: str, *, attributes: Dict[str, Any] | None = None) -> Iterator[Any]:
        yield None


class _OtelTracing(Tracing):
    def __init__(self, *, service_name: str, endpoint: str | None):
        super().__init__(enabled=True)

        from opentelemetry import trace  # type: ignore
        from opentelemetry.sdk.resources import Resource  # type: ignore
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)

        exporter = None
        if endpoint:
            exporter = _create_otlp_exporter(endpoint)

        if exporter:
            provider.add_span_processor(BatchSpanProcessor(exporter))

        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer(service_name)

    @contextmanager
    def span(self, name: str, *, attributes: Dict[str, Any] | None = None) -> Iterator[Any]:
        assert self._tracer is not None
        with self._tracer.start_as_current_span(name, attributes=attributes or {}) as span:
            yield span


def _create_otlp_exporter(endpoint: str):
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  # type: ignore

        return OTLPSpanExporter(endpoint=endpoint)
    except Exception:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (  # type: ignore
                OTLPSpanExporter,
            )

            return OTLPSpanExporter(endpoint=endpoint)
        except Exception:
            return None


def create_tracing(config: TracingConfig) -> Tracing:
    if not config.enabled:
        return Tracing(enabled=False)

    try:
        import opentelemetry  # noqa: F401
    except Exception:
        return Tracing(enabled=False)

    try:
        return _OtelTracing(service_name=config.service_name, endpoint=config.endpoint)
    except Exception:
        return Tracing(enabled=False)
