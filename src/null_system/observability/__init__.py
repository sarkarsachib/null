from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from .logging import LoggingConfig, StructuredLogger, configure_logging, get_structured_logger
from .metrics import Metrics, create_metrics
from .tracing import Tracing, TracingConfig, create_tracing


@dataclass
class Observability:
    enabled: bool
    logger: StructuredLogger
    metrics: Metrics
    tracing: Tracing

    def capture_exception(self, exc: BaseException, **context: Any) -> None:
        dsn = os.getenv("NULL_SENTRY_DSN")
        if not dsn:
            return
        try:
            import sentry_sdk  # type: ignore
        except Exception:
            return

        try:
            sentry_sdk.set_context("null", context)
            sentry_sdk.capture_exception(exc)
        except Exception:
            return


_OBSERVABILITY: Observability | None = None
_HTTP_SERVER_STARTED = False


def get_observability() -> Observability:
    global _OBSERVABILITY
    if _OBSERVABILITY is None:
        _OBSERVABILITY = init_observability(enabled=None)
    return _OBSERVABILITY


def init_observability(
    *,
    enabled: bool | None = None,
    service_name: str = "null-lang",
    environment: str | None = None,
    logging_config: LoggingConfig | None = None,
    tracing_config: TracingConfig | None = None,
    metrics_enabled: bool | None = None,
) -> Observability:
    global _OBSERVABILITY

    if enabled is None:
        enabled = os.getenv("NULL_OBSERVABILITY_ENABLED", "0") in {"1", "true", "True"}

    if environment is None:
        environment = os.getenv("NULL_ENV") or os.getenv("ENV")

    if metrics_enabled is None:
        metrics_enabled = enabled

    if logging_config is None:
        logging_config = LoggingConfig.from_env(enabled=enabled)

    if tracing_config is None:
        tracing_config = TracingConfig.from_env(enabled=enabled, service_name=service_name)

    logger = configure_logging(logging_config)
    tracing = create_tracing(tracing_config)
    metrics = create_metrics(enabled=metrics_enabled)

    _OBSERVABILITY = Observability(
        enabled=enabled,
        logger=logger,
        metrics=metrics,
        tracing=tracing,
    )

    dsn = os.getenv("NULL_SENTRY_DSN")
    if enabled and dsn:
        try:
            import sentry_sdk  # type: ignore

            sentry_sdk.init(
                dsn=dsn,
                environment=environment,
                traces_sample_rate=float(os.getenv("NULL_SENTRY_TRACES_SAMPLE_RATE", "0")),
                send_default_pii=False,
            )
        except Exception:
            pass

    if enabled:
        port = os.getenv("NULL_OBSERVABILITY_HTTP_PORT")
        if port:
            start_observability_http_server(host=os.getenv("NULL_OBSERVABILITY_HTTP_HOST", "0.0.0.0"), port=int(port))

    return _OBSERVABILITY


def get_logger(name: str | None = None) -> StructuredLogger:
    return get_structured_logger(name)


def create_observability_app(observability: Observability | None = None):
    if observability is None:
        observability = get_observability()

    from .health import HealthState, create_health_router

    try:
        from fastapi import FastAPI
        from fastapi.responses import Response
    except Exception as e:  # pragma: no cover
        raise RuntimeError("FastAPI is required for the observability app") from e

    state = HealthState()
    app = FastAPI(title="Null-Lang Observability")
    app.include_router(create_health_router(state))

    @app.get("/metrics")
    def metrics() -> Response:
        payload, content_type = observability.metrics.render()
        return Response(content=payload, media_type=content_type)

    return app


def start_observability_http_server(*, host: str = "0.0.0.0", port: int = 8000) -> None:
    global _HTTP_SERVER_STARTED

    if _HTTP_SERVER_STARTED:
        return

    try:
        import threading

        import uvicorn
    except Exception:
        return

    obs = get_observability()
    app = create_observability_app(obs)

    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, name="null-observability", daemon=True)
    thread.start()
    _HTTP_SERVER_STARTED = True
