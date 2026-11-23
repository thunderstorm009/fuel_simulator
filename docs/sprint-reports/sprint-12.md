# Sprint 12 Report: Performance, Scale, Reliability, and Operations

Time window: 2026-11-23 | Owner: Engineering Agent (Autonomous run) | Branch: `sprints-11-13` | Status: **PASS**

---

## 1. Objective

Make the API fast and stable under traffic surges, reduce polling load via Server-Sent Events push updates, prove long-run continuous stability under active chaos, demonstrate end-to-end alert routing with Alertmanager, drill and measure database backup and restore, document service-by-service recovery times, and implement runtime recommendation policy switching with automatic fail-safe rollback.

---

## 2. What Now Exists

### WP12.1: API Performance & Load Test Optimization (P0)
- **Baseline Sweep (10–400 VUs):** Profiled unchanged API under k6 sweep. Max throughput saturated at ~201 req/s; read p95 latency degraded to 1,210.6 ms at 100 VUs and 4,991.1 ms at 400 VUs. Postgres CPU saturated at 309.8% due to full-table sequential scans on `forecasts` and `depot_risks` executing `DISTINCT ON` quicksorts taking 15.342 ms and 3.815 ms per query. Single-core Uvicorn saturated at ~140% CPU.
- **Root Cause Fixes:**
  1. Scaled Uvicorn to 4 worker processes (`--workers ${API_WORKERS:-4}`) behind published port 8101.
  2. Enlarged asyncpg connection pool to `min_size=2, max_size=20` (max 80 pool connections across 4 workers).
  3. Added composite indexes in `backend/api/db.sql`:
     - `snapshots_fetched_id_idx ON snapshots (fetched_at DESC, id DESC)`
     - `forecasts_pair_snapshot_idx ON forecasts (station_id, fuel_type, snapshot_id DESC)`
     - `depot_risks_depot_snapshot_idx ON depot_risks (depot_id, fuel_type, snapshot_id DESC)`
     Subquery filtering on latest snapshot ID reduced query execution time from 15.342 ms to 0.103 ms (149x speedup).
  4. Implemented in-memory pre-serialized UTF-8 byte cache keyed by `(endpoint, snapshot_id)`. Added HTTP 304 Not Modified support via `ETag: W/"snap-{id}"` and `If-None-Match`. Caches are invalidated immediately upon new snapshot arrival.
  5. Cached parsed `Snapshot` Pydantic model in memory, eliminating redundant 60+ KB JSON parsing on `POST /api/whatif`.
  6. Scaled rate limiter dynamically per worker (`max(5, limit // workers)`).
- **Post-Optimization Empirical Results:**
  - Throughput tripled to **615.3–625.8 req/s** at 100–200 VUs.
  - Read p50 dropped by 78% (**88.2 ms** vs 393.2 ms at 100 VUs).
  - Read p95 dropped by 72% (**338.3 ms** vs 1,210.6 ms at 100 VUs; knee at ~300 VUs).
  - What-If p95 dropped to **288.3 ms** (<500 ms target met).
  - Postgres CPU under 400 VUs dropped from 309.8% to **34.1%** (89% reduction).
  - **0.0% error rate** across all concurrency levels up to 400 VUs.
- Documented complete comparative matrix and pyinstrument profile evidence in `docs/loadtest.md`. Recorded ADR-044.

### WP12.2: Push Updates over SSE with Polling Fallback (P1)
- Implemented `EventBroadcaster` in `backend/api/stream.py` backed by PostgreSQL `LISTEN/NOTIFY` on the `platform_events` channel.
- Added `GET /api/stream` endpoint delivering push hints (`{"type": "snapshot", "tick": 42}`). Heartbeat comments (`: ping\n\n`) emitted every 15s.
- Guardrails: Bounded per-client queues (`maxsize=100`, drops oldest on overflow without blocking broadcaster); connection limit per worker process (`SSE_MAX_CLIENTS=50`, HTTP 429 when saturated).
- Wired worker persistence to emit notifications on snapshot, forecasts, recommendations, and incidents; API emits on operator decisions.
- Created React hook `useEventStream` in `web/src/features/stream/useEventStream.ts`: invalidates TanStack queries on events, disables interval polling when live, and falls back to 10-second polling if stream drops.
- Added stream status indicator (`● LIVE PUSH` / `○ POLLING FALLBACK`) to web application header.
- Added 7 unit tests in `tests/unit/test_sse_stream.py`.
- Measured request-rate reduction: drops from 120 req/min/tab (polling) to 6 req/min/tab (push hints), an empirical **95% reduction** in read request volume. Recorded ADR-045 and updated `docs/architecture.md` and `docs/api.md`.

### WP12.3: 90-Minute Continuous Soak Test (P0)
- Built automated soak testing harness `scripts/soak_test.sh` and `scripts/run_soak_test.py`.
- Ran live stack with simulator continuously `RUNNING` at `SIMULATION_SPEED=2` (tick_minutes=15) while executing randomized chaos injection (latency, unavailable, error_rate, demand_spikes).
- Sampled metrics every 60 seconds: container CPU/memory, database size, snapshot counts, API p95 latency, and incident states.
- Empirical Findings:
  - API container memory drift: **+14.4 MiB** (STABLE < 25 MiB ceiling).
  - Worker container memory drift: **+2.4 MiB** (STABLE < 15 MiB ceiling).
  - Database size: bounded between **33.1 MiB and 35.7 MiB** due to automatic snapshot pruning (retaining latest 1,000 snapshots).
  - API read p95 latency: 8.7–12.5 ms during standard operation.
  - Zero unexplained 5xx errors across the entire execution window.
- Simulator returned to `PAUSED` at tick 153 with zero faults. Generated `docs/results/soak-test-timeseries.csv` and `docs/results/soak-test-summary.md`.

### WP12.4: Alert Routing End to End (P1)
- Added Alertmanager (`prom/alertmanager:v0.28.0`) and custom Python Webhook Receiver (`observability/webhook_receiver/`) isolated under `profiles: ["alerts"]` in `docker-compose.yml`.
- Standard developer stack (`docker compose up`) starts only the standard 8 services; verified via integration test `tests/integration/test_compose_config.py`.
- Added `promtool check rules` step to CI (`.github/workflows/ci.yml`), passing rule validation with 6 rules.
- Implemented and executed automated drill `scripts/demonstrate_alert_routing.py`:
  - Injected simulator `unavailable` fault at `2026-11-23T07:28:18.625Z`.
  - FIRING alert `SimulatorCircuitBreakerOpen` (severity: `critical`, runbook: `docs/runbook.md#circuit-breaker`) received by webhook at `2026-11-23T07:28:46.347Z`.
  - Cleared fault at `2026-11-23T07:28:46.788Z`.
  - RESOLVED alert `SimulatorCircuitBreakerOpen` received by webhook at `2026-11-23T07:29:01.351Z` (resolution duration: 15.0s).
- Evidence captured in `docs/evidence/day-4/alert-routing-evidence.json` and `.txt`.
- Updated `docs/runbook.md` with silencing commands (`amtool`, API, UI) and runbook anchors, and recorded ADR-046.

### WP12.5: Backup, Restore & Measured Recovery (P0)
- Implemented `scripts/backup_db.sh` and `scripts/restore_db.sh` targeting the project's PostgreSQL container.
- Wrote TDD unit test `tests/unit/test_backup_restore_idempotency.py` verifying idempotency key immutability and executor non-resubmission rules.
- Automated drill `scripts/drill_backup_restore.py` verified:
  - RTO: **2.93s** (target < 15s MET). Complete 77.6 MB schema and data restoration.
  - RPO: **< 5.0s** (continuous PostgreSQL WAL durability).
  - 100% row preservation across snapshots (419), forecasts (5,004), recommendations (158), decisions (1), depot_risks (1,572), incidents (387).
  - Zero duplicate submissions or regressions. Report: `docs/results/backup-restore-drill.json`.
- Measured recovery times across all 7 services (`scripts/measure_recovery_times.py`) using 3 distinct phases (running, healthy, fresh data visible):
  - `api`: Running 0.16s, Healthy 0.19s, Fresh Data 0.20s.
  - `worker`: Running 0.14s, Healthy 0.17s, Fresh Data 1.18s.
  - `predictor`: Running 0.14s, Healthy 0.17s, Fresh Data 0.19s.
  - `postgres`: Running 0.14s, Healthy 1.48s, Fresh Data 1.49s.
  - `web`: Running 0.13s, Healthy 0.16s, Fresh Data 0.18s.
  - `prometheus`: Running 0.14s, Healthy 0.17s, Fresh Data 0.19s.
  - `grafana`: Running 0.14s, Healthy 0.17s, Fresh Data 0.18s.
  - `full_stack_restart`: Running 0.38s, Healthy 1.58s, Fresh Data 1.82s.
- Replaced outdated process-start numbers in `docs/resilience.md`.

### WP12.6: Runtime Policy Switch with Automatic Rollback (P2)
- Added `policy_changes` table schema in `backend/api/db.sql`, `backend/api/database.py`, and `backend/worker/store.py` with full audit fields (`id`, `policy`, `previous_policy`, `actor`, `reason`, `changed_at`).
- Added Prometheus metrics: `active_policy` Gauge and `policy_changes_total{policy, actor}` Counter.
- Implemented `POST /api/policy` and `GET /api/policy` in `backend/api/routes/policy.py` with operator token authentication, rate limiting, and database auditing.
- Updated `GET /api/version` to expose `active_policy`.
- Updated web frontend: `Footer` displays live active policy (`Policy v2.1.0 (<policy>)`) updated via TanStack query.
- Hardened `PolicyRunner` in `backend/worker/recommend_job.py`:
  - Validates every candidate proposal against pure domain constraints via `core.validator.validate`.
  - Automatically rolls back to `HeuristicPolicy` if active policy throws an exception, times out (0.5s), or emits any candidate violating validator constraints.
  - Records rollback in `policy_changes` with actor `system:rollback` and logs warning.
  - Creates `policy_rollback` incident in database and broadcasts push event via PostgreSQL `LISTEN/NOTIFY`.
  - Discards invalid candidate plans and guarantees validator violations are never emitted.
- Unit tested in `tests/unit/test_policy_switch_and_rollback.py` (6 tests passing).
- Recorded ADR-047 in `docs/decisions.md` and updated `docs/api.md`.

---

## 3. Decisions Recorded

- **ADR-044**: API Performance Scaling via Multi-Worker Uvicorn, Connection Pool Enlargement, Composite Indexing, and Byte-Level Caching.
- **ADR-045**: Push Invalidation Over SSE with PostgreSQL LISTEN/NOTIFY and Polling Fallback.
- **ADR-046**: Alertmanager Routing and Local Webhook Receiver under Compose Profile 'alerts'.
- **ADR-047**: Runtime Policy Switch with Automatic Rollback and Constraint Validation.

---

## 4. Independent Review Verification

- **R4 (Resilience)**: `docs/reviews/sprint-12-r4.md` — PASS (0 P0, 0 P1 findings). Evaluated simulator faults, container kill, network partition, and soak test.
- **R5 (Performance & Load Test)**: `docs/reviews/sprint-12-r5.md` — PASS (0 P0, 0 P1 findings). Full VU sweep (10–400 VUs) audited for honesty; 3.1x throughput improvement and 89% DB CPU drop verified.

---

## 5. Verification Evidence & Quality Gates

- `make lint`: PASS (ruff check, ruff format, web typecheck, web build clean).
- `make test`: PASS (234 pytest unit & integration tests, 11 frontend Vitest tests).
- `docker compose config -q`: PASS (profile separation verified).
- `git diff --check`: PASS (zero whitespace errors or conflict markers).
- Simulator state: PAUSED at tick 153, default speed, faults cleared.
