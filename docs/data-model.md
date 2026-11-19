# Data model

`backend/api/db.sql` initializes the schema on a fresh database volume. Simulator snapshots are stored as the validated raw aggregate in `snapshots.raw_json`; the current simulator response remains the source of truth. Later features extend this schema through idempotent worker startup migrations.

- `snapshots`: id, tick, sim_time, raw_json, fetched_at, stale, data_status. Fetched time and tick are indexed. Repeated ticks are allowed after simulator reset; ingestion skips a tick only when it matches the newest stored snapshot.
- `forecasts`: snapshot/tick, station/fuel, deterministic stockout hours, Monte Carlo hours quantiles and probability, confidence, risk level, review flag, source, JSON trajectory and JSON drivers. A unique snapshot/station/fuel index prevents duplicate forecasts; station/fuel/tick supports latest-pair reads.
- `recommendations`: lifecycle status, selected route and quantity, unique permanent idempotency key, exact request body, explanation, expiry and simulator allocation reference. Status/tick is indexed.
- `decisions`: recommendation, actor, approve/reject action, optional reason, timestamp. Recommendation/time is indexed.
- `incidents`: type, severity, detection/resolution timestamps, JSON detail. Open incidents are indexed.
- `integration_events`: kind, JSON detail, timestamp. Kind/time is indexed.
- `heartbeats`: component primary key, last seen, JSON detail.

The worker persists validated snapshots, forecasts, incidents, integration events, and heartbeats. PostgreSQL initializes the schema from the mounted SQL file on a fresh volume. On startup, the worker applies idempotent migrations for reset-aware snapshot ticks and forecast trajectory/driver fields and indexes; API access remains read-only. Forecast rows refer to the snapshot used to compute them, and trajectory points contain tick offset and mean/P10/P90 projected inventory.
The database stores history and our decisions. The simulator stays the source of truth for current state.
