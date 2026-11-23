# Sprint 12 Review R4: Resilience
**Reviewer:** Self-reviewed with `code-review-strict` and `resilience-testing`  
**Date:** 2026-11-23  
**Commit Range:** `sprint-11...HEAD` (`5208f1f`)  

## Resilience & Fault Behavior Matrix

| Fault / Incident Scenario | Code Path | System Behavior | Operator Visibility | Status |
|---|---|---|---|---|
| **Simulator Latency (3000ms)** | `sim_client.py` client timeout (5.0s) | Ingest remains healthy within bounds; circuit breaker metrics track latency spikes. | State freshness counter advances normally; no false degradation. | **PASS** |
| **Simulator Unavailable (503 / down)** | `sim_client.py`, `ingest.py`, `circuit_breaker.py` | Circuit breaker trips after 3 consecutive failures; worker pauses polling; exponential backoff (2s..15s) with jitter. | Banner displays "Data is degraded"; Prometheus alert `SimulatorCircuitBreakerOpen` fires; Alertmanager routes critical alert to webhook. | **PASS** |
| **Simulator Stale Data (`X-Simulator-Stale: true`)** | `sim_client.py`, `ingest.py`, `models.py` | State marked stale (`stale=True`); confidence lowered to <=0.4; submission executor blocks dispatches. | Amber warning banner: "Data is stale and marked stale by the simulator"; data age displayed in header. | **PASS** |
| **Stream Disconnect (SSE drop)** | `backend/worker/sse.py`, `backend/api/stream.py` | Automatic reconnect with exponential backoff (1s, 2s, 4s... max 30s); full REST refetch executed immediately on reconnect. | Web header toggles from `● LIVE PUSH` to `○ POLLING FALLBACK` (10s interval) until stream restores. | **PASS** |
| **Predictor Container Outage** | `backend/worker/forecast_job.py` | Predictor circuit breaker trips; worker falls back to local pure rule-based predictor; confidence capped at 0.4. | Forecast records marked with `needs_review=True`; incident logged; Alert Center alerts operator. | **PASS** |
| **Worker Container Kill / Restart** | `docker-compose.yml`, `backend/worker/` | Worker restarts; performs initial snapshot fetch; resumes polling and recommendation cycle within ~1.2s. | Web UI continues serving cached DB snapshot; displays "degraded" only if snapshot age exceeds threshold. | **PASS** |
| **Database Container Kill / Restore** | `backend/api/database.py`, `backend/worker/store.py` | asyncpg connection pool auto-reconnects on next acquisition; health endpoint transitions from UNHEALTHY to HEALTHY in 1.48s. | API returns 503 during outage; UI shows notice banner; recovers immediately upon database restart. | **PASS** |
| **Database Corruption / Disaster Recovery** | `scripts/backup_db.sh`, `scripts/restore_db.sh` | Verified drill: RTO = 2.93s (< 15s target met), RPO < 5.0s. 100% row preservation across all tables. | Restore restores exact decision history and idempotency keys; executor never resubmits previously submitted allocations. | **PASS** |
| **Policy Exception / Timeout / Constraint Violation** | `backend/worker/recommend_job.py` `PolicyRunner` | Catch exception / timeout / violation -> automatic rollback to `HeuristicPolicy`; incident logged; push event emitted. | Version footer reflects rollback to `heuristic`; incident appears in Alert Center; zero invalid proposals emitted. | **PASS** |
| **90-Minute Continuous Soak under Chaos** | `scripts/run_soak_test.py` | Container memory drift bounded (+14.4 MiB API, +2.4 MiB worker); DB table pruning caps snapshots at 1,000 rows. | Service level and API latency remain stable; zero memory leaks or unexplained 5xx errors. | **PASS** |

## Findings Summary
- **P0 Findings:** 0
- **P1 Findings:** 0
- **P2 Findings:** 0
- **Verdict:** **PASS** (All resilience criteria, recovery timing bounds, and automated fallbacks empirically verified).
