# Resilience and fault verification

All exercises below use the simulated BUP Fuel Supply Simulator. The live fault demo does not reset state or submit allocation writes. It requires a paused simulator, no pre-existing active faults, Docker Compose, and a Python environment with project test dependencies.

Run it with:

```sh
PYTHON_BIN=.venv/bin/python bash scripts/fault_demo.sh
```

`PYTHON_BIN` may point at another environment that has the repository test dependencies installed. The script rejects a running simulator or pre-existing active fault, clears the fault it injects, restarts only worker/predictor containers that it stopped, and checks at exit that faults are clear, events are resolved, and the simulator is PAUSED. It does not reset the simulator.

## Live result — 2026-11-20

Evidence: [complete controlled fault demo](evidence/sprint-05-fault-demo-accepted.txt). The run began at tick 150 and ended PAUSED at tick 152. No allocation was created. The same stack remained healthy after recovery.

| Fault | Detection and degraded behavior | Recovery evidence | Result |
|---|---|---|---|
| `unavailable` | Simulator returned HTTP 503; retries and breaker-open metric increased; cached snapshot became DEGRADED | Fault cleared; accepted non-stale snapshot returned HEALTHY | PASS |
| `error_rate` | Injected HTTP 503; retry/failure counters and open breaker observed; cached snapshot became DEGRADED | Fault cleared; snapshot returned HEALTHY | PASS |
| `latency` | 3500 ms simulator delay; client probe took about 3.51 s; cached snapshot aged beyond 15 s and became DEGRADED | Fault cleared; fresh snapshot returned HEALTHY | PASS |
| `stale_data` | HTTP 200 included `X-Simulator-Stale: true`; API data health showed `stale=true`, `DEGRADED` | Fault cleared; fresh non-stale snapshot returned HEALTHY | PASS |
| `stream_disconnect` | Stream endpoint returned HTTP 503 with nested fault code; REST ingestion stayed HEALTHY; reconnect metric increased | After clear, worker logged `simulator_stream_connected` without a subsequent worker restart | PASS |
| Malformed simulator response | Controlled test fixture returned malformed content; last-known-good behavior and rejection path tested | `1 passed, 4 deselected` | PASS (test fixture; no live simulator mutation) |
| Predictor stopped | `/api/health` reported OFFLINE; fallback counter increased; tick 151 persisted 12 `baseline` forecasts, all review-required, confidence at most 0.4; fallback incident visible | Predictor restarted; `/api/health` HEALTHY; tick 152 persisted 12 `remote` forecasts | PASS |
| Worker stopped | API and frontend stayed reachable; health DEGRADED and snapshot age grew past 19 s | Worker restarted; ingestion returned HEALTHY | PASS |

Prometheus had three active targets and all were `up`. Grafana `/api/health` returned database `ok`, version 11.6.0. A controlled one-tick `demand_spike` changed the provisioned `hours_to_stockout{station="station-coxsbazar",fuel="DIESEL"}` query from 19.5 to 19.25, and the event resolved at tick 145. Evidence: [Grafana event and panel query](evidence/sprint-05-grafana-event.txt).

## Recovery and limits

- REST polling is authoritative. SSE disconnects trigger reconnect and refetch; stream availability is not required for REST health.
- Predictor fallback is persisted with low confidence and `needs_review`; recovery replaces same-key forecast rows with their remote `source` value. A regression test covers this upsert behavior.
- Grafana freshness alerting uses `worker_last_ingest_timestamp_seconds`, which ages while ingest is failing and alerts if the worker metric disappears. A successful poll alone is not enough to refresh the alert timestamp. A stopped-worker exercise observed Prometheus `up{job="worker"}=0` and the Grafana snapshot-age alert active; see [worker alert check](evidence/sprint-05-worker-alert-check.txt).
- The local `.env` contains values that differ from the public Compose defaults. It was left untouched. The safe configuration check passes with `.env.example` and reports the local mismatch by variable name only, without printing values. Run `python3 scripts/check_compose_env.py --env-file .env.example` to check clean-clone defaults.
- Grafana dashboards and alert rules are provisioned and evaluate locally. Email delivery is not configured (Grafana logs report SMTP is unconfigured), so notification delivery is not verified.
- Fault durations are bounded and the script does not clear unrelated/pre-existing faults; it refuses to start if any are active.

## Running simulator resilience & speed adaptation (Sprint 8)

When the simulator runs in continuous `RUNNING` mode (rather than paused and stepped), ticks advance at real-time speeds:
1. **Adaptive Freshness:** `GET /api/state` reports dynamic `ticks_per_second` and `snapshot_age_ticks`.
2. **Speed Warning Banner:** When observed tick velocity exceeds 0.5 ticks/s, a high-priority warning banner is displayed to the operator warning that recommendations may expire before manual approval.
3. **Pre-Submission Re-validation:** The executor re-reads fresh authoritative non-stale REST state from the simulator and re-validates all 5 constraint rules immediately prior to issuing `POST /v1/allocations`. If simulator ticks advanced and made the allocation infeasible, or if the snapshot is marked stale, the submission is rejected locally and marked failed without corrupting simulator state.
4. **Idempotency Stability:** Recommendation IDs and idempotency keys are permanent UUIDs stored in PostgreSQL and never reused across different allocation bodies.

## Empirical recovery matrix & failure boundaries (Sprint 10)

Evidence file: [docs/evidence/sprint-10-resilience-matrix.txt](evidence/sprint-10-resilience-matrix.txt).

### Per-service kill -9 recovery times

> [!NOTE]
> The figures below represent **container process restart times** under Compose restart policies. Application query readiness following container restart takes **~1.2s**, and container healthcheck polling (`Health=healthy`) reports in **5.18s** (governed by Compose `interval: 5s`).

| Service | Action | Container Restart Policy | Measured Process Restart Time (s) | Query Ready / Healthcheck | Post-Recovery Status |
|---|---|---|---|---|---|
| `api` | `kill -9` | Compose `unless-stopped` | 0.11 s | ~1.2 s / 5.18 s | HEALTHY |
| `worker` | `kill -9` | Compose `unless-stopped` | 0.17 s | Ingest resumes in ~1.2 s | HEALTHY |
| `predictor` | `kill -9` | Compose `unless-stopped` | 0.23 s | Health probe in ~1.2 s | HEALTHY |
| `frontend` | `kill -9` | Compose `unless-stopped` | 0.10 s | Instant / N/A | HEALTHY |
| `prometheus` | `kill -9` | Compose `unless-stopped` | 0.11 s | Scrape resumes ~1.5 s | HEALTHY |
| `grafana` | `kill -9` | Compose `unless-stopped` | 0.11 s | Web UI ready ~1.8 s | HEALTHY |

### Database outage & traffic surge

- **Database Stop:** When PostgreSQL is stopped, API gracefully returns degraded status / 503, UI displays OFFLINE banner, and the worker holds in-memory polling without crash. Upon `docker compose start postgres`, container restart was 0.16s, database query readiness was ~1.2s, and the API immediately resumed healthy queries.
- **Instantaneous Concurrency Burst:** 250 requests fired at 25 concurrent workers against `/api/state`: 100% success rate, latency p50 = 77.17 ms, p95 = 143.33 ms, p99 = 161.18 ms. Bounded asyncpg connection pool prevented socket exhaustion.

### Failure boundary analysis

Evidence and charts: [docs/results/failure-boundary.md](results/failure-boundary.md) and [failure boundary plot](results/failure-boundary.png).

1. **Physical Failure Boundaries vs Dispatch Capacity:** Total network demand across all 4 stations (`station-mirpur`, `station-tongi`, `station-karnaphuli`, `station-coxsbazar`) is **91,400 L/day** across all fuels (`core/world.py`). At 15-minute ticks (96 ticks/day), average demand is **~952 L/tick** (and **~508 L/tick** at 8-minute ticks). Peak demand with maximum hour factors reaches ~1,500 L/tick, and even an extreme 1.8x global surge consumes <2,700 L/tick. The two supply depots have a combined dispatch capacity of **23,000 L/tick** (Gazipur 12,000 + Patiya 11,000 L/tick), which is >24x average demand. Therefore, depot dispatch capacity is **not** the binding constraint.
2. **Empirically Measured Failure Boundaries (192 Ticks / 2 Days):**
   Across comprehensive stress sweeps on the live simulator, the crossover thresholds were measured as:
   - **99% SLA Threshold:** Heuristic sustains 99% service level up to **2.43x** demand surge (99.91% at 2.2x), whereas Naive degrades below 99% at **1.96x** (97.48% at 2.2x) and None fails immediately (**1.0x**).
   - **95% Critical Threshold:** Heuristic holds 95% service level up to **2.80x** demand surge (98.30% at 2.6x), whereas Naive drops below 95% at **2.55x** (94.66% at 2.6x).
   - **90% Collapse Boundary:** Heuristic maintains **>90%** service level across the entire test spectrum up to **>3.0x** (91.66% at 3.0x), whereas Naive breaches 90% at **2.95x** (89.28% at 3.0x).
3. **Actual Binding Constraints Identified from Measurements:**
   - **Route Max Shipment Limits:** Each route has a strict shipment cap of 5,000 to 7,000 L per allocation batch. Under demand surges >2.2x, route shipment capacity becomes the primary binding constraint.
   - **Depot Inventory & Resupply:** Initial combined depot stock is 252,000 L (Gazipur 131,000 L + Patiya 121,000 L), providing approximately 2.76 days of baseline cover without resupply. When supply shortfall factor drops to <=0.4 (<=40% planned resupply), depot stock depletion becomes binding.
   - **Corridor Transit Delay & Isolation:** Deliveries require 1 to 4 transit ticks; an allocation cannot arrive instantly to avert an immediate stockout. Disruption of >=3 routes isolates stations, dropping service level to ~79% regardless of policy.
   - **Station Tank Headroom (Ullage):** Allocations exceeding current station tank ullage are strictly prohibited by physical validation rules.
4. **Graceful Degradation at Boundary:** Rather than crashing or oversubscribing depots, the heuristic policy enters Pass 1 emergency triage (allocating 12h survival fuel first) and tags partial allocations with `is_partial=True` and clear unserved reason codes. Operator UI surfaces bottleneck alerts (`bottleneck` detections) and degraded service warnings.
