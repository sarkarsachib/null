# ELK / JSON log fields

When `NULL_OBSERVABILITY_ENABLED=1`, the runtime emits JSON logs.

## Base fields

- `timestamp` (RFC3339 UTC)
- `level` (lowercase string)
- `event` (human-readable event name)
- `logger` (logger name)

## Tracing correlation

When OpenTelemetry is enabled, these fields are included:

- `trace_id` (32-char hex)
- `span_id` (16-char hex)

## Common event fields

Compiler:
- `status`: `ok|error`
- `duration_s`
- `validation_error_count`

VM:
- `status`: `ok|error`
- `duration_s`
- `instructions`
- `error_type` (on errors)

Security:
- `key_id`
- `token_count`
- `plaintext_bytes`
- `ciphertext_bytes`
- `duration_s`

These fields are designed to work well with Elasticsearch indexing and Kibana dashboards.
