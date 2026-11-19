---
name: observability-metrics
description: Use when adding metrics, logs, Grafana dashboards, alerts or health endpoints.
---
# Observability
- Metrics: http_requests_total, http_request_duration_seconds, sim_client_requests_total{endpoint,outcome}, sim_client_retries_total, sim_breaker_state, snapshot_age_seconds, snapshot_rejected_total{reason}, forecast_mape, hours_to_stockout{station,fuel}, stockout_probability{station,fuel}, recommendations_total{status}, policy_fallback_total{reason}, alerts_active{severity}, sim_service_level.
- Labels are low cardinality: no ids, no free text.
- Logs are JSON: timestamp, level, service, event, tick, correlation_id. One correlation id follows a decision from forecast to simulator allocation.
- Dashboards and alert rules are committed under infra/ and provisioned automatically.
- Health page shows components, last check time, p95 latency and error rate, and the overall HEALTHY, DEGRADED or OFFLINE status.
