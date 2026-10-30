# Non-functional requirements

### NFR-004 Order lookup latency
Status: live (since 1.0.0)
Acceptance (EARS):
- AC-004.1 The API shall answer getOrder within 300 ms at p95 under 50 requests/s.
Errors: -
Tests: T-004.1 [system]  (test-cases/nfr.yaml)
Traces: UJ-01; FR-002

## Observability

Log fields on every line: `timestamp`, `level`, `request_id`, `operation`, `error_code`.
No customer email or name is ever logged.

| Metric | Error code | Alert threshold |
|---|---|---|
| orders_import_duplicates_total | IMPORT_DUPLICATE | none; counted only |
| orders_import_empty_total | IMPORT_EMPTY | any increase in 1 hour pages the owner |
| orders_not_found_total | ORDER_NOT_FOUND | more than 50 in 5 minutes |
| orders_forbidden_total | FORBIDDEN | more than 20 in 5 minutes |
| geocoder_timeouts_total | GEOCODER_TIMEOUT | more than 5 in 10 minutes |
