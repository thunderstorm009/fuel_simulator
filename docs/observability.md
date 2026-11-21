# Observability

## Current topology

Prometheus scrapes the API (`api:8101`), worker (`worker:8102`), and independent predictor (`predictor:8103`) at a 15-second interval. Configuration is in `observability/prometheus/prometheus.yml`. Grafana has a provisioned Prometheus data source, dashboard, and alert rules under `observability/grafana/provisioning/`; it is available at port 3000.

Each Python service exposes `/health` and `/metrics`. API request metrics are low-cardinality by method, route template, and status class. Simulator request metrics use endpoint and outcome labels; rejection metrics use simulator error code. Station/fuel labels appear only on forecast error metrics, where they are useful for domain diagnosis.

## Metrics implemented

Metric definitions are in `backend/shared/core/metrics.py`; route and job instrumentation is in `backend/api/` and `backend/worker/`.

| Metric family | Purpose |
|---|---|
| `http_requests_total`, `http_request_duration_seconds` | API request volume and duration by method/route/status class |
| `service_health_checks_total` | Health endpoint requests by service |
| `sim_client_requests_total`, `sim_client_retries_total`, `sim_client_failures_total` | Worker simulator request outcome, retries, and failures |
| `sim_breaker_state` | Simulator circuit breaker state |
| `worker_ingest_success_total`, `worker_ingest_failures_total`, `snapshot_rejected_total`, `snapshot_age_seconds`, `worker_last_ingest_timestamp_seconds` | Ingestion and accepted-data freshness; the timestamp advances only after successful persistence |
| `forecasts_computed_total`, `forecast_job_failures_total`, `forecast_error_liters` | Forecast work, failures, and observed demand forecast error |
| `recommendations_created_total`, `recommendation_fallbacks_total`, `recommendation_job_failures_total` | Recommendation job outcomes |
| `allocation_executor_failures_total`, `simulator_allocation_rejections_total` | Approved-allocation executor and simulator rejections |
| `worker_sse_events_total`, `worker_sse_reconnects_total` | SSE hints and reconnect activity |
| `policy_fallback_total{reason}`, `forecast_mape{station,fuel}`, `hours_to_stockout{station,fuel}`, `stockout_probability{station,fuel}` | Predictor fallback and forecast quality/risk |
| `recommendations_total{status}`, `sim_service_level`, `alerts_active{severity}` | Recommendation lifecycle, service level, and active alert gauges |
| `detections_total{type}` | Automated anomaly and incident detections by type (`demand_anomaly`, `regional_surge`, `abnormal_inventory`, `bottleneck`, `emerging_regional_disruption`) |


Prometheus counters are process-local and reset when a service restarts. No metrics should include recommendation IDs, operator tokens, raw URLs, or other unbounded values.

## Logs and health

Python services log operational errors and job events using JSON records for relevant worker paths. `GET /api/health` reports backend, database, simulator heartbeat/data age, predictor ping, and decision-engine age, plus API histogram p95 and observed 5xx fraction. `/health` remains a liveness endpoint. The API does not call the simulator for health information.

## Verification and gaps

Live verification on 2026-11-20 found API, worker, and predictor Prometheus targets all `up`; Grafana `/api/health` returned database `ok` on version 11.6.0. The provisioned dashboard was found by UID `fuel-supply-platform`. During a one-tick simulated demand-spike event, the Grafana-backed `hours_to_stockout{station="station-coxsbazar",fuel="DIESEL"}` query changed from 19.5 to 19.25; the event later resolved. See [Grafana event evidence](evidence/sprint-05-grafana-event.txt) and [fault/recovery evidence](evidence/sprint-05-fault-demo-accepted.txt).

Alert rules are provisioned and evaluating, but outbound notification delivery is not configured: Grafana logs report SMTP is unconfigured. No email notification delivery is claimed. Metric values are process-local and may reset after a service restart.
