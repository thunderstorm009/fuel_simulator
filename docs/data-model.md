# Data model (planned; adjust to the real schema in api/db.sql)

- snapshots: id, tick, sim_time, raw_json, fetched_at, stale (bool), data_status. Prune old rows.
- forecasts: id, snapshot_id/tick, station_id, fuel, hours_to_stockout, p10, p50, p90, stockout_prob_24h, confidence, risk_level, needs_review, source (local, remote, baseline).
- recommendations: id, status, policy_used, fallback_used, depot_id, station_id, route_id, fuel, quantity, idempotency_key (unique), explanation_json, created_tick, expires_tick, correlation_id, sim_allocation_id.
- decisions: id, recommendation_id, actor, action (approve, reject), reason, at.
- incidents: id, type, severity, detected_at, resolved_at, detail.
- integration_events: id, kind (retry, breaker_state, validation_failure, stale_data, sse_reconnect), detail, at.
- heartbeats: component, last_seen, detail.
The database stores history and our decisions. The simulator stays the source of truth for current state.
