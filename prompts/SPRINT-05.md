# Sprint 5 (hours 16-20): Observability and resilience

SAME REPOSITORY. Starting state: tag sprint-4 (approval and execution working). Extend. Do not rewrite the decision logic.

Skills: observability-metrics, resilience-testing, systematic-debugging, verification-before-completion.

## Objective
You can see what the system is doing, and every failure has a demonstrated, visible response.

## Work packages

### WP5.1 Metrics
TASK: Instrument api, worker and predictor with prometheus-client. Names: http_requests_total, http_request_duration_seconds, sim_client_requests_total{endpoint,outcome}, sim_client_retries_total, sim_breaker_state, snapshot_age_seconds, snapshot_rejected_total{reason}, forecast_mape, hours_to_stockout{station,fuel}, stockout_probability{station,fuel}, recommendations_total{status}, policy_fallback_total{reason}, alerts_active{severity}, sim_service_level. No ids as labels. JSON logs with timestamp, level, service, event, tick, correlation_id.
TESTS: scrape /metrics and assert the names exist.

### WP5.2 Prometheus and Grafana as code
TASK: infra/prometheus.yml (scrape api, worker, predictor) and Grafana provisioning (datasource plus a committed dashboard JSON). Panels: API rate, errors, p95; simulator-client success, retries, breaker state; data age; risk gauges per station and fuel; fallback count; recommendations by status; service level. Alert rules: data age over 30s, breaker open, 5xx rate high, fallback active.
ACCEPT: after docker compose up the dashboard loads with no manual clicks.

### WP5.3 Health aggregation
TASK: GET /api/health returning per-component status (backend, database, simulator via worker heartbeat, predictor ping, decision engine last-run age) with last-check time, plus p95 latency and error rate from the in-process histogram. Overall HEALTHY, DEGRADED or OFFLINE using the data-status rules. Frontend Health page and a global banner.
TESTS: each component down gives the expected overall status.

### WP5.4 Predictor service, fallback, chaos switch
TASK: predictor/main.py: POST /predict takes a snapshot slice and returns forecasts via core. worker RemoteForecaster (timeout 1.5s, own breaker) then BaselineForecaster (static profile, no calibration, confidence capped at 0.4, needs_review true). Each fallback increments policy_fallback_total and opens an incident. Add POST /api/chaos/forecast-fail {enabled} (operator token) so the predictor fails on demand for demos.
TESTS: remote ok, remote timeout gives baseline, remote 500 gives baseline, recovery returns to remote.

### WP5.5 Fault demo and resilience evidence
TASK: scripts/fault_demo.sh with one scene per fault (unavailable, error_rate, latency, stale_data, stream_disconnect) plus malformed data and predictor down. Each scene: inject through /admin/faults, print the expected UI change, wait, clear. tests/integration/test_resilience.py simulates each fault shape against ingest and executor. Fill docs/resilience.md as a table: scenario, expected, observed (real evidence paths).

## Docs to update
docs/observability.md, docs/resilience.md (with evidence), docs/decisions.md, docs/PROGRESS.md.

## Acceptance checklist (real output required, nothing restarted by hand)
- [ ] each of the 5 simulator faults shows detection, degraded behavior and recovery
- [ ] docker stop predictor: fallback, a visible metric, recommendations still produced
- [ ] docker stop worker: dashboard still loads and shows data age
- [ ] Grafana panels move when events are injected
- [ ] tests and lint green

## Finish
Run prompts/SPRINT-GATE.md with N=5. Do not start Sprint 6.
