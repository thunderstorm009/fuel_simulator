# Observability (planned)
Metrics: http_requests_total, http_request_duration_seconds, sim_client_requests_total{endpoint,outcome}, sim_client_retries_total, sim_breaker_state, snapshot_age_seconds, snapshot_rejected_total{reason}, forecast_mape, hours_to_stockout{station,fuel}, stockout_probability{station,fuel}, recommendations_total{status}, policy_fallback_total{reason}, alerts_active{severity}, sim_service_level.
Logs: JSON with timestamp, level, service, event, tick, correlation_id.
Dashboards and alerts: committed in infra/; alerts for data age over 30s, breaker open, high 5xx rate, fallback active.
Health: /api/health with component status, p95 latency and error rate.
Final version: build the metrics catalog from the code (Sprint 6, prompt D3).
