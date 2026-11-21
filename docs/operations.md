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
