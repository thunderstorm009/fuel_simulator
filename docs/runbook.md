# Operations runbook

## First checks

```sh
docker compose ps
curl -fsS http://localhost:8101/api/health
curl -fsS http://localhost:8101/api/data-health
docker compose logs --tail=100 api worker predictor
```

## Alertmanager routing and silencing

Alertmanager runs under the optional Docker Compose profile `alerts` (not started in default stack):
```sh
# Start Alertmanager and the local Webhook Receiver
docker compose --profile alerts up -d alertmanager webhook-receiver

# Check Alertmanager health and UI
curl -fsS http://localhost:9093/-/healthy
# Web UI is available at http://localhost:9093

# Check Webhook Receiver logs
docker compose logs -f webhook-receiver
curl -fsS http://localhost:5001/alerts
```

### Silencing alerts

During scheduled maintenance, chaos drills, or simulator resets, alerts can be silenced via Alertmanager API or web UI:
1. **Via Alertmanager Web UI (`http://localhost:9093/#/silences`):**
   - Click "New Silence".
   - Specify matcher (e.g., `alertname = SimulatorCircuitBreakerOpen` or `severity = warning`).
   - Set duration (e.g. 1h) and comment with operator identity and reason.
2. **Via Alertmanager REST API (`curl`):**
   ```sh
   curl -X POST http://localhost:9093/api/v2/silences \
     -H "Content-Type: application/json" \
     -d '{
       "matchers": [{"name": "alertname", "value": "SnapshotDataStale", "isRegex": false, "isEqual": true}],
       "startsAt": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'",
       "endsAt": "'"$(date -u -v+1H +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '+1 hour' +%Y-%m-%dT%H:%M:%SZ)"'",
       "createdBy": "operator",
       "comment": "Scheduled maintenance drill"
     }'
   ```
3. **Via `amtool` (inside container):**
   ```sh
   docker compose exec alertmanager amtool silence add alertname="SimulatorCircuitBreakerOpen" --duration=30m --comment="drill"
   ```

---

## Alert procedures & runbook anchors

<a id="circuit-breaker"></a>
### Circuit Breaker (`#circuit-breaker`)
- **Alert:** `SimulatorCircuitBreakerOpen` (Severity: `critical`)
- **Condition:** `sim_breaker_state == 1` for 15s.
- **Cause:** Ingestion worker experienced 5 consecutive failures contacting simulator REST endpoints (HTTP 503, timeouts, or connection resets).
- **Impact:** State ingestion is paused; snapshots are not advancing.
- **Immediate action:**
  1. Inspect simulator health: `curl -I http://localhost:8000/v1/health`.
  2. Inspect active faults: `curl http://localhost:8000/admin/faults`.
  3. If an injected fault is present, clear it: `curl -X POST http://localhost:8000/admin/faults/clear`.
  4. Once simulator recovers, worker circuit breaker resets automatically after reset cooldown (`SIM_BREAKER_RESET_S=10s`). Verify `sim_breaker_state` drops to 0.

<a id="stale-data"></a>
### Stale Data (`#stale-data`)
- **Alerts:** `SnapshotDataStale` (Severity: `warning`), `SimulatorStaleDataFlag` (Severity: `warning`)
- **Condition:** `snapshot_age_seconds > 60` or `snapshot_stale == 1` for 15s.
- **Cause:** Simulator returned `X-Simulator-Stale: true` header or stopped advancing simulation ticks, or worker ingestion stalled.
- **Impact:** System status degrades to `DEGRADED`; confidence drops; operator recommendations are blocked from submission (AGENTS.md rule 6 & 10).
- **Immediate action:**
  1. Check data age: `curl http://localhost:8101/api/data-health`.
  2. Inspect simulator tick status: `curl http://localhost:8000/v1/instance`.
  3. Clear simulator faults: `curl -X POST http://localhost:8000/admin/faults/clear`.
  4. If simulator was paused, resume or step: `curl -X POST http://localhost:8000/admin/run`.

<a id="stockout-risk"></a>
### Stockout Risk (`#stockout-risk`)
- **Alert:** `CriticalStockoutRisk` (Severity: `critical`)
- **Condition:** `min(hours_to_stockout) < 4` for 1m.
- **Cause:** Projected demand exceeds remaining tank inventory plus in-transit fuel within 4 hours.
- **Impact:** Immediate risk of unserved fuel demand and station outage.
- **Immediate action:**
  1. Review recommendations in web UI (`http://localhost:5173`) or `GET /api/recommendations`.
  2. Review candidate allocations and verify depot source inventory cover (`/api/depots/risk`).
  3. Enter `OPERATOR_TOKEN` and approve recommendation via `POST /api/recommendations/{id}/approve`.
  4. Worker submits allocation to simulator; verify status transitions to `SUBMITTED` -> `IN_TRANSIT`.

<a id="predictor-fallback"></a>
### Predictor Fallback (`#predictor-fallback`)
- **Alert:** `PredictorFallbackActive` (Severity: `warning`)
- **Condition:** `sum(rate(policy_fallback_total[5m])) > 0` for 1m.
- **Cause:** Worker failed to reach predictor service (`http://predictor:8103`) due to crash, timeout, or circuit breaker trip.
- **Impact:** Worker uses pure heuristic profile fallback. Forecasts have capped confidence (0.4) and are flagged `needs_review=True`.
- **Immediate action:**
  1. Check predictor service: `docker compose ps predictor` and `curl http://localhost:8103/health`.
  2. Review predictor logs: `docker compose logs --tail=50 predictor`.
  3. If predictor was stopped or faulted via demo endpoint, restart or reset: `docker compose restart predictor`.

<a id="calibration-drift"></a>
### Calibration Drift (`#calibration-drift`)
- **Alert:** `CalibrationDriftDetected` (Severity: `warning`)
- **Condition:** `increase(forecast_drift_total[5m]) > 0` for 1m.
- **Cause:** Rolling 24-hour demand ratio (actual / predicted) drifted outside tolerance envelope `[0.80, 1.25]`.
- **Impact:** Forecasts consistently under-predicting or over-predicting demand, degrading allocation safety buffers.
- **Immediate action:**
  1. Check open drift incidents: `curl "http://localhost:8101/api/incidents?status=open"`.
  2. Inspect regional demand: `curl http://localhost:8101/api/regional-demand`.
  3. Verify whether an unannounced simulator demand spike event is active (`GET /v1/events`).

---

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
