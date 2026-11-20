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
