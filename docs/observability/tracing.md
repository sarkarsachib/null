# OpenTelemetry tracing

Null-Lang uses OpenTelemetry (OTLP exporter) when installed via the `observability` extra.

## OTLP endpoint

The runtime honors these env vars:

- `NULL_OTEL_EXPORTER_OTLP_ENDPOINT`
- `OTEL_EXPORTER_OTLP_ENDPOINT`

Example with the OpenTelemetry Collector:

```bash
export NULL_OBSERVABILITY_ENABLED=1
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

## Collector example

Example `otelcol` config snippet:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
      http:
exporters:
  logging:
    loglevel: info
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [logging]
```

## Span names

- `null.compiler.compile`
  - `null.compiler.lex`
  - `null.compiler.parse`
  - `null.compiler.validate`
  - `null.compiler.emit`
  - `null.compiler.optimize`
  - `null.compiler.binary`
- `null.vm.execute`
- `null.security.key_manager.create_key`
- `null.security.key_manager.load_key`
- `null.security.encrypt_stream`
- `null.security.decrypt_stream`
