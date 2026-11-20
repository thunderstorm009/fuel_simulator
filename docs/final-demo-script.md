# Final demo script (8-10 minutes)

All data and actions shown are **SIMULATED**.
This demo follows the operator decision loop: **Observe -> Detect -> Predict -> Decide -> Approve -> Act -> Monitor -> Recover**.

## Prerequisites
- Docker Compose running: `make up` (or `FRONTEND_HOST_PORT=5174 make up` if 5173 is taken)
- Browser open at operator dashboard: `http://localhost:${FRONTEND_HOST_PORT:-5174}`
- Grafana open at: `http://localhost:3000` (provisioned dashboards under "Fuel Supply Platform")
- Terminal open at project root with project virtual environment active

---

## Step-by-step walkthrough

| Time | Step & Command | Expected Visual | Recovery Line |
|---|---|---|---|
| **0:00–1:00** | **System status & health**<br/>`curl -s http://localhost:8101/api/health \| python3 -m json.tool` | Dashboard header displays `SIMULATED` badge, overall status `HEALTHY`, all 6 components healthy, data freshness < 5s. | If health shows `DEGRADED`, explain that the simulator was just paused; step 2 ticks with `/admin/step` to refresh. |
| **1:00–2:30** | **Observe state & shortage risk**<br/>Click **Overview**, then **Stockout Risk** | Station cards show current fuel inventory (DIESEL, PETROL, OCTANE). Risk matrix highlights at-risk stations with hours-to-stockout and 24h probability. Trajectory charts display P10/P50/P90 Monte Carlo fan. | Refresh browser. If trajectories are loading, explain they are cached in PostgreSQL and refreshed each tick. |
| **2:30–4:00** | **Decide & human approval**<br/>Click **Allocations** drawer; inspect a PROPOSED recommendation | Recommendation card shows source depot, target station, fuel, quantity, ETA, and constraint validation. An explanation drawer details stockout drivers and rejected alternatives. | Emphasize: **No auto-submission**. The operator token is held only in browser memory. Submissions require explicit human approval. |
| **4:00–5:30** | **Simulate disruptions & resilience**<br/>`python3 scripts/fault_demo.sh` (or show pre-recorded scene) | Injects simulator faults (unavailable, latency, stale data, stream disconnect). Component health marks degraded without crashing; cached state remains visible. On clear, SSE refetches and restores `HEALTHY`. | `scripts/fault_demo.sh` automatically clears faults on exit. Verify with `curl http://localhost:8000/v1/faults`. |
| **5:30–6:30** | **Predictor fallback & recovery**<br/>`docker compose stop predictor`<br/>Wait 5s, check UI, then `docker compose start predictor` | Predictor marks `OFFLINE`; worker falls back to baseline model with confidence capped at 0.4 and `needs_review=true`. On restart, predictor recovers to `source=remote`. | Restart container immediately with `docker compose start predictor`; health auto-recovers within 5s. |
| **6:30–8:00** | **Load & scenario proof**<br/>Show `docs/results/scenario-summary.md` and `docs/loadtest.md` | Table of 24 scenario runs proving 100% determinism (delta 0.0000). Load test graphs showing 320 req/s, 0% error rate across 205k requests, and the 100 VU performance knee. | Reference raw summaries in `docs/results/k6-*-summary.json` and Docker resource telemetry CSVs. |
| **8:00–9:00** | **Auditing & telemetry**<br/>Open Grafana (`http://localhost:3000`) | Live dashboards: accepted snapshot age, stockout risk gauge, policy fallback counts, worker request rates. Decision log shows immutable operator audit trail. | If Grafana container is slow to load, show Prometheus targets directly at `http://localhost:9090/targets`. |
| **9:00–10:00** | **Q&A & wrap-up** | Conclude with architecture principles: pure domain logic, worker-owned I/O, strict validation, zero unauthorized writes. | Refer to `docs/qa.md` for detailed technical answers. |

---

## Emergency reset command
If the simulator gets into an unexpected state during live presentation:
```sh
curl -s -X POST http://localhost:8000/admin/reset
curl -s -X POST http://localhost:8000/admin/pause
curl -s -X POST http://localhost:8000/admin/faults/clear
for _ in $(seq 1 5); do curl -s -X POST http://localhost:8000/admin/step; done
```
Restores clean tick-5 baseline in 2 seconds.
