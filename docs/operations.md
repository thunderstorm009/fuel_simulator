# Operations

## Local Compose stack

Use `make up` to start the application and `make down` to stop containers while preserving named volumes. `docker compose down -v` deletes local PostgreSQL and Grafana state and should only be used when that data is intentionally disposable.

The six platform services and default URLs are:

| Service | URL |
|---|---|
| Simulator | `http://localhost:8000` |
| API | `http://localhost:8101` |
| Worker | `http://localhost:8102` |
| Predictor | `http://localhost:8103` |
| Frontend | `http://localhost:${FRONTEND_HOST_PORT:-5173}` |
| Prometheus | `http://localhost:9090` |
| Grafana | `http://localhost:3000` |

PostgreSQL is an additional supporting container and is not published on a host port by default. Docker Compose waits for required dependencies' health checks.

## Configuration

Copy `.env.example` to `.env` and set local values. `DATABASE_URL` and `POSTGRES_PASSWORD` must match when the database volume is initialized. Set `OPERATOR_TOKEN` to enable operator decision routes. When choosing a non-default frontend port, set `CORS_ORIGIN` to the corresponding browser origin. Never commit `.env` or credentials; `.env.example` is safe to publish and documents variable names/defaults.

## Useful commands

```sh
docker compose config -q
make smoke
docker compose ps
docker compose logs --tail=100 api worker predictor frontend prometheus grafana
```

The simulator can be paused or reset only through its documented administrative controls. A reset changes simulator state; it is not part of ordinary startup or smoke verification. Do not approve a recommendation during routine health checks.

## Simulator running speeds and judging demonstration

The simulator can run in paused/stepped mode or continuous `RUNNING` mode at configurable speeds via `SIMULATION_SPEED`:

| SIMULATION_SPEED | Configured Rate | Observed Rate | Ingest Lag (Ticks) | Forecast Age (Ticks) | Recommendation Window | Warning Banner Triggered | Stale / Error Rejection |
|---|---|---|---|---|---|---|---|
| 1 (Project Default) | 1.0 tick/s | 0.99 ticks/s | 0.3 - 1.9 ticks | 1 - 2 ticks | 4 ticks (4.0s) | Yes (speed_warning: true) | Submissions revalidated against fresh tick |
| 4 | 4.0 ticks/s | 3.58 ticks/s | 2.5 - 13.6 ticks | 4 - 8 ticks | 4 ticks (1.1s) | Yes (speed_warning: true) | 409/422 handled; stale write blocked |
| 8 (Image Default) | 8.0 ticks/s | 5.97 ticks/s | 1.5 - 15.0 ticks | 6 - 12 ticks | 4 ticks (0.67s) | Yes (speed_warning: true) | Stale flag lowered; submission blocked |

### Recommended judging demo configuration

In the simulator image's default mode (`SIMULATION_SPEED=8`), ticks advance at ~6 ticks/second (~160ms per tick). At this rate, 1 simulated hour elapses every 670ms, which is too rapid for manual human review and approval.

For live judging and operator walkthroughs, use the controlled demo clock:
```sh
# Run simulator clock at 0.5 ticks per second (1 tick every 2 seconds; 8 seconds per simulated hour)
./scripts/demo_clock.py --rate 0.5
```
Pressing `Ctrl+C` halts the clock and guarantees the simulator is cleanly `PAUSED`.

### High-speed resilience safeguards

When running at elevated speeds:
1. `GET /api/state` reports `ticks_per_second` and `snapshot_age_ticks`.
2. When tick rate exceeds 0.5 ticks/s, a prominent warning banner alerts the operator: *"High simulation speed detected. Recommendations may expire before operator approval."*
3. The platform strictly enforces safety rule 6: recommendations must be `APPROVED` and re-validated against fresh non-stale snapshot data immediately before calling `POST /v1/allocations`. Expired or stale recommendations are blocked before submission.


## Backup and disaster recovery (Sprint 12 WP12.5)

The database backup and restore scripts target this project's PostgreSQL container (`fuel_simulator-postgres-1`) exclusively without affecting any external volumes.

### Operational commands

```sh
# 1. Take database backup
./scripts/backup_db.sh [optional_output_path.sql]

# 2. Restore database from backup
./scripts/restore_db.sh <backup_path.sql>

# 3. Execute automated backup and restore drill
python3 scripts/drill_backup_restore.py

# 4. Measure service and full-stack recovery times
python3 scripts/measure_recovery_times.py
```

### Recovery objectives & empirical metrics

- **RPO (Recovery Point Objective):** **< 5 seconds**. PostgreSQL write-ahead logging commits every tick transaction before worker ingestion finishes. Ingest interval is 5 seconds.
- **RTO (Recovery Time Objective):** **2.93 seconds** (measured cold SQL dump restoration of complete 77.6 MB schema and data).
- **Service Recovery Times (Running / Healthy / Data Visible):**
  - `postgres`: 0.38s / 5.53s / 0.38s
  - `api`: 0.70s / 6.03s / 2.26s
  - `worker`: 0.65s / 5.94s / 1.85s
  - `predictor`: 0.63s / 5.95s / 1.54s
  - `frontend`: 0.39s / 5.39s / 0.39s
  - `prometheus`: 0.39s / 5.41s / 0.39s
  - `grafana`: 0.40s / 5.35s / 0.99s
  - **Full stack restart:** 1.02s running, 6.87s healthy, 3.06s data visible.
- **Idempotency Guarantees:** Recommendation UUIDs and `idempotency_key` tokens survive backup and restore identically. The worker executor checks database recommendation statuses and simulator allocation IDs, preventing duplicate allocation submissions after recovery.

## Data retention and pruning policy

1. **Snapshots:** The worker retains recent tick snapshots for demand trend aggregation (last 24–48 hours). Older raw snapshots are pruned periodically to keep database size bounded within 250 MB.
2. **Forecasts & Depot Risks:** Linked via foreign key cascade (`ON DELETE CASCADE`) to snapshots. Pruning older snapshot IDs automatically reclaims forecast and risk storage.
3. **Decisions & Audit Trail:** Recommendations, human operator approval/rejection decisions, and incident logs are **permanent** and never pruned to preserve full audit traceability.

## Alertmanager and alert routing (Compose profile `alerts`)

Alert routing is isolated under the optional Compose profile `alerts` to keep the standard stack minimal and fast:
- **Alertmanager (`prom/alertmanager:v0.28.0`):** Listens on port 9093. Routes alerts to receivers based on severity (`critical` and `warning`) and debounces with `group_wait: 2s, group_interval: 5s`.
- **Webhook Receiver (`webhook-receiver`):** Lightweight Python HTTP receiver on port 5001. Logs firing and resolved alerts to stdout and records structured JSONL in `/logs/alerts.jsonl`.
- **Rule Validation:** Alert rules in `observability/prometheus/alert_rules.yml` are validated via `promtool` in CI and can be verified locally:
  ```sh
  docker run --rm --entrypoint promtool -v "$(pwd)/observability/prometheus":/etc/prometheus prom/prometheus:v3.3.0 check rules /etc/prometheus/alert_rules.yml
  ```
- **Automated Routing Demonstration:** `python3 scripts/demonstrate_alert_routing.py` starts the `alerts` profile, restarts Prometheus to discover Alertmanager, injects simulator `unavailable` fault, verifies webhook receipt of firing alert with severity and runbook link, clears the fault, verifies webhook receipt of resolution notification (15.0s resolution duration), and stops the `alerts` profile containers. Evidence recorded in `docs/evidence/day-4/alert-routing-evidence.json` and `.txt`.

## Recovery notes

- **Simulator unavailable:** inspect worker logs, simulator health, and `/api/data-health`; worker keeps the last accepted snapshot and marks it degraded.
- **Stale data:** inspect `snapshot_age_seconds`, worker ingestion logs, and the simulator stale header. The worker must refetch authoritative REST state before execution.
- **Worker unavailable:** inspect worker health/logs and database availability. API read routes continue to return stored state where available, but no new synchronization or execution occurs.
- **API unavailable:** frontend requests fail; cached data may remain visible with an API-unavailable status.
- **Database unavailable:** API/worker startup or requests may fail health/dependency checks. Preserve the named volume while diagnosing.
- **Frontend or registry build failure:** run `npm --prefix web run build` separately from `docker compose build frontend` to distinguish local bundle errors from image-registry or Docker metadata errors.
- **Recommendation backlog:** inspect worker logs and persisted recommendation/execution status. Only explicitly APPROVED recommendations are eligible for executor handling.

To restore normal operation after a simulator fault, clear the simulator fault using its supported admin endpoint and confirm a subsequent worker refresh restores healthy freshness. Do not treat SSE reconnection as data replay; REST polling/refetch remains the source of truth.

## Deployment limitations

This is a local hackathon/demo Compose deployment. Hosted CI has not been triggered, production secrets management and external deployment are not configured. Grafana dashboard and alert provisioning exists, but current runtime loading and panel movement have not been reverified. See `docs/PROGRESS.md` for environment-specific notes and open acceptance items.
