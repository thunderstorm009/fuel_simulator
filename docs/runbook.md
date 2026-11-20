# Operations runbook

## First checks

```sh
docker compose ps
curl -fsS http://localhost:8101/api/health
curl -fsS http://localhost:8101/api/data-health
docker compose logs --tail=100 api worker predictor
```

## Recovery by symptom

| Symptom | Check | Recovery |
|---|---|---|
| Simulator degraded or stale | `/api/data-health`, worker logs, simulator `/v1/health` | Restore simulator access, clear any demo fault, wait for a successful REST poll. Never submit from stale state. |
| Predictor fallback active | Worker metrics/logs and predictor health | Restore predictor; wait for a new snapshot/forecast cycle. Fallback confidence stays capped and needs review. |
| Worker unavailable | Compose health and worker logs | Restore worker and verify heartbeat/data age. API can only serve persisted state while it is stopped. |
| API unavailable | Compose health and API logs | Restore API/database dependencies; frontend may retain cached query data with an error state. |
| Database unavailable | Postgres health/logs and configured URL | Preserve volumes while diagnosing. Ensure `DATABASE_URL` credentials match initialized database credentials. |
| Prometheus/Grafana unavailable | Compose health, Prometheus targets, Grafana provisioning logs | Restore services; configuration files are under `observability/`. Do not claim dashboard runtime from config alone. |
| Approved recommendation does not progress | Recommendation/decision history, worker log, data freshness | Investigate stored request/key and failure reason. Do not edit the key/body or create a replacement to work around an ambiguous POST. |

## Fault cleanup

`scripts/fault_demo.sh` clears active simulator faults on exit. The random chaos runner also attempts a final clear. After interruption, inspect `GET /admin/faults` on the dedicated simulator and clear any remaining fault before resuming normal operation.

## Destructive reset

`scripts/cold_start_check.sh --confirm-volume-destroy` runs `docker compose down -v`; it irreversibly removes local PostgreSQL and Grafana state. Confirm the target volumes are disposable before invoking it. This command was not run in the current session.
