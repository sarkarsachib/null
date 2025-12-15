import io
import json
import logging

from null_system.compiler import NullCompiler
from null_system.observability import create_observability_app, init_observability
from null_system.observability.logging import LoggingConfig, configure_logging
from null_system.observability.metrics import METRIC_SPECS
from null_system.observability.tracing import TracingConfig


def test_json_logging_output_shape():
    stream = io.StringIO()

    base_logger = logging.getLogger("null_system")
    old_handlers = list(base_logger.handlers)
    old_level = base_logger.level
    old_propagate = base_logger.propagate

    try:
        base_logger.handlers.clear()
        logger = configure_logging(LoggingConfig(enabled=True, stream=stream))
        logger.info("test.event", foo="bar", count=2)
    finally:
        base_logger.handlers.clear()
        base_logger.handlers.extend(old_handlers)
        base_logger.setLevel(old_level)
        base_logger.propagate = old_propagate

    payload = json.loads(stream.getvalue().strip())
    assert payload["event"] == "test.event"
    assert payload["level"] == "info"
    assert "timestamp" in payload
    assert payload["foo"] == "bar"
    assert payload["count"] == 2


def test_metric_specs_have_expected_labels():
    spec_by_name = {s.name: s for s in METRIC_SPECS}

    assert spec_by_name["null_compilation_duration_seconds"].labelnames == ("status",)
    assert spec_by_name["null_compilation_stage_duration_seconds"].labelnames == (
        "stage",
        "status",
    )
    assert spec_by_name["null_vm_execution_duration_seconds"].labelnames == ("status",)
    assert spec_by_name["null_errors_total"].labelnames == ("component", "error_type")


def test_observability_can_be_enabled_without_optional_deps():
    init_observability(
        enabled=True,
        logging_config=LoggingConfig(enabled=False),
        tracing_config=TracingConfig(enabled=False, service_name="null-lang"),
        metrics_enabled=False,
    )

    compiler = NullCompiler()
    result = compiler.compile_and_run("set x to 5")
    assert result.success


def test_observability_app_has_expected_routes():
    init_observability(
        enabled=True,
        logging_config=LoggingConfig(enabled=False),
        tracing_config=TracingConfig(enabled=False, service_name="null-lang"),
        metrics_enabled=False,
    )

    app = create_observability_app()
    paths = {route.path for route in app.routes}

    assert "/metrics" in paths
    assert "/healthz" in paths
    assert "/readyz" in paths
