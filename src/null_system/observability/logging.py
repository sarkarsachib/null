from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, MutableMapping


class TraceContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        trace_id: str | None = None
        span_id: str | None = None

        try:
            from opentelemetry import trace  # type: ignore

            span = trace.get_current_span()
            ctx = span.get_span_context()
            if ctx and ctx.is_valid:
                trace_id = f"{ctx.trace_id:032x}"
                span_id = f"{ctx.span_id:016x}"
        except Exception:
            pass

        setattr(record, "trace_id", trace_id)
        setattr(record, "span_id", span_id)
        return True


_STANDARD_LOG_RECORD_KEYS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
}


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()

        payload: MutableMapping[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname.lower(),
            "event": record.getMessage(),
            "logger": record.name,
        }

        if getattr(record, "trace_id", None):
            payload["trace_id"] = record.trace_id
        if getattr(record, "span_id", None):
            payload["span_id"] = record.span_id

        for key, value in record.__dict__.items():
            if key in _STANDARD_LOG_RECORD_KEYS or key.startswith("_"):
                continue
            if key in payload:
                continue
            payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


@dataclass(frozen=True)
class LoggingConfig:
    enabled: bool
    level: str = "INFO"
    json: bool = True
    stream: Any = sys.stderr

    @classmethod
    def from_env(cls, *, enabled: bool) -> "LoggingConfig":
        level = os.getenv("NULL_LOG_LEVEL", "INFO")
        json_format = os.getenv("NULL_LOG_FORMAT", "json").lower() == "json"
        return cls(enabled=enabled, level=level, json=json_format)


class StructuredLogger:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    @property
    def raw(self) -> logging.Logger:
        return self._logger

    def debug(self, event: str, **fields: Any) -> None:
        self._logger.debug(event, extra=fields)

    def info(self, event: str, **fields: Any) -> None:
        self._logger.info(event, extra=fields)

    def warning(self, event: str, **fields: Any) -> None:
        self._logger.warning(event, extra=fields)

    def error(self, event: str, **fields: Any) -> None:
        self._logger.error(event, extra=fields)

    def exception(self, event: str, **fields: Any) -> None:
        self._logger.exception(event, extra=fields)


def configure_logging(config: LoggingConfig) -> StructuredLogger:
    logger = logging.getLogger("null_system")
    logger.setLevel(config.level.upper())

    if not config.enabled:
        return StructuredLogger(logger)

    handler = logging.StreamHandler(config.stream)
    if config.json:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))

    handler.addFilter(TraceContextFilter())

    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False

    return StructuredLogger(logger)


def get_structured_logger(name: str | None = None) -> StructuredLogger:
    return StructuredLogger(logging.getLogger(name or "null_system"))
