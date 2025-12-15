# Observability

Null-Lang can be instrumented with optional Prometheus metrics, JSON logs, OpenTelemetry traces, and Sentry error reporting.

## Installation

```bash
pip install -e ".[observability]"
```

## Quick start

### 1) Run the observability HTTP server

```bash
nullc observe --host 0.0.0.0 --port 8000
```

Endpoints:
- `GET /metrics` (Prometheus)
- `GET /healthz`
- `GET /readyz`

### 2) Enable instrumentation for compiler/VM runs

Instrumentation is opt-in and controlled via environment variables:

```bash
export NULL_OBSERVABILITY_ENABLED=1
# Optional: start an embedded HTTP server during compilation/execution
export NULL_OBSERVABILITY_HTTP_PORT=8000

nullc run examples/phase6/ml_inference.null
```

## Prometheus

Example scrape config:

```yaml
scrape_configs:
  - job_name: null-lang
    static_configs:
      - targets: ["localhost:8000"]
```

## Grafana

1. Add Prometheus as a data source.
2. Import the sample dashboard from `docs/observability/grafana-dashboard-null-lang.json`.

## Logs (ELK)

Logs are emitted as JSON (to stderr) when `NULL_OBSERVABILITY_ENABLED=1`. Suggested field mappings are documented in `docs/observability/elk-fields.md`.

## Tracing (OpenTelemetry)

Set an OTLP exporter endpoint (HTTP or gRPC):

```bash
export NULL_OBSERVABILITY_ENABLED=1
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

Spans:
- `null.compiler.compile`
- `null.vm.execute`
- `null.security.encrypt_stream`
- `null.security.decrypt_stream`

See `docs/observability/tracing.md` for exporter wiring examples.

## Sentry

Configure Sentry via env var:

```bash
export NULL_SENTRY_DSN=https://...@sentry.io/...
export NULL_OBSERVABILITY_ENABLED=1
```

When unset, Sentry integration is a no-op.
