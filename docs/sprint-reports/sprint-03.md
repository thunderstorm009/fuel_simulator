# Sprint 03 Report: Forecast and stockout risk

**Path note:** The key paths below reflect the repository layout at Sprint 3. They were later moved into `backend/`, `intel/predictor/`, `web/`, and `observability/`; see `docs/DAY-1-UPDATE.md` for the current tree. The referenced Sprint 3 prompt is retained in the local-only development workspace.

Time window: 2026-11-19 resume session | Owner(s): Codex | Branch and tag: `main`, last tag `sprint-0` | Status: **Passed locally with documented simulator semantics**

## 1. Objective

Give operators a 24-hour, uncertainty-aware hours-to-stockout forecast for every station/fuel pair, with explanations and a UI matrix/drill-down, while keeping simulator I/O in the worker and API reads in PostgreSQL.

## 2. What now exists

- Pure hourly demand, EWMA calibration, station inventory projection and known station-allocation arrival timing in `core/world.py` and `core/forecast.py`.
- Seeded, vectorized 300-path Monte Carlo risk, inventory bands, risk classification and stale/history/stability confidence in `core/risk.py`.
- A worker forecast job computes and persists all 12 pairs after distinct snapshots, records forecast error, and opens/updates/resolves stockout-risk incidents.
- DB-only `GET /api/risks` and trajectory endpoint return stored forecasts, bands, drivers and freshness metadata.
- The existing overview remains; a SIMULATED risk matrix, alerts, review state, and lazy Recharts trajectory drawer are available.
- No policy, recommendation, approval, or execution behavior was added.

## 3. Decisions and rejected alternatives

- ADR-018 uses Recharts for the required projection band.
- ADR-019 includes only known station allocation arrivals in station inventory projections. It does not infer future station shipments from depot supply schedules.
- ADR-020 distinguishes demand forecast recovery from inventory recovery after a demand event.
- No inventory restoration or future dispatch behavior was invented.

## 4. Key files

- `core/world.py`, `core/forecast.py`, `core/risk.py`: pure profile demand, calibration, projection and uncertainty.
- `worker/forecast_job.py`, `worker/ingest.py`, `worker/store.py`, `worker/main.py`: post-snapshot calculation, persistence, metrics and incident lifecycle.
- `api/db.sql`, `api/database.py`, `api/routes/read.py`: forecast fields/migrations and read routes.
- `frontend/src/App.tsx`, `frontend/src/TrajectoryDrawer.tsx`, `frontend/src/api.ts`, `frontend/src/index.css`: risk matrix and chart.
- `tests/test_forecast.py`, `tests/test_risk.py`, `tests/test_forecast_job.py`, `tests/test_risk_api.py`, and ingestion callback regression coverage.
- Sprint 3 acceptance prompt: revised event criteria distinguish elevated demand, EWMA convergence, persistent stock depletion, and depot ETA changes (the prompt is local-only).
- `docs/intelligence.md`, `docs/data-model.md`, `docs/api.md`, `docs/architecture.md`, `docs/decisions.md`.

## 5. API added

| Method and path | Behavior |
|---|---|
| `GET /api/risks` | Latest persisted forecast for each station/fuel with stockout hours, P10/P50/P90, 24h probability, confidence, risk, review flag, drivers and freshness. |
| `GET /api/risks/{station_id}/{fuel_type}/trajectory` | Persisted projected inventory mean/P10/P90 trajectory and freshness. |

Both endpoints are database-only; missing snapshot returns 503 and unknown pair returns 404. Worker `/metrics` exposes `forecast_error_liters{station_id,fuel_type}`.

## 6. Tests and verification

| Command or scenario | Actual result | Status |
|---|---|---|
| `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make test` | `72 passed in 1.18s` | PASS |
| `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make lint` | Ruff passed; 34 files formatted; TypeScript/Vite production build passed | PASS |
| `docker compose config -q` | Exit 0 | PASS |
| Port override Compose config | Exit 0 with port 5174 and matching CORS origin | PASS |
| `git diff --check` | Exit 0 | PASS |
| `SMOKE_SKIP_BUILD=1 FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 make smoke` | Exit 0; simulator paused at tick 114; API, worker and predictor health checks returned ok | PASS |
| Browser UI | 4 overview stations, SIMULATED label, 12 risk cells, Recharts chart rendered | PASS |
| Forecast metric | Worker `/metrics` exposed all station/fuel gauges; forecast job failure counter 0 | PASS |
| Live demand spike | At tick 104, x1.8 lowered Mirpur DIESEL 2.5h→1.0h and Tongi OCTANE 11.5h→6.5h; multiplier returned to 1.0 after resolution | PASS; stockout hours stayed lower because inventory remained consumed |
| Demand forecast convergence | Fixture test verifies elevated event demand, normal multiplier after resolution, EWMA-adjusted demand moving toward baseline with normal observations, and persistent depletion | PASS |
| Live shipment delay | `supply-202` moved tick 132→137; DB `GET /api/state` at tick 114 exposed delayed ETA; no dependent allocation existed and Mirpur risk remained 0h/critical | PASS |
| Unrelated depot delay regression | Fixture test compares station risk before/after an ETA-only change with no allocation; forecasts remain equal | PASS |

## 7. Evidence

`docs/evidence/sprint-03-runtime.md` contains runtime, API, UI, event, metric and command results. Event interpretation is recorded in ADR-019 and ADR-020 and in `docs/intelligence.md`.

## 8. Problems and fixes

The first full lint run found import sorting, modernization, unused import and line-length issues among saved Sprint 3 code. Ruff auto-fixes and formatting resolved them; `make lint` passed. Live scenarios confirmed that demand events consume inventory without restoring it, while shipment delays alter depot arrival times only. Acceptance wording was revised with the user's authorization. The forecast follows official simulator semantics and does not fabricate inventory or future dispatches.

## 9. Not done or limitations

- Forecast demand may retain a temporarily elevated EWMA after resolution; it converges with subsequent normal demand observations. Inventory remains depleted, so risk need not return to its pre-event level.
- A depot delay alone cannot change station risk without a dependent station allocation or projected station coverage. The system does not synthesize future dispatches.
- The simulator was left PAUSED at tick 114; all injected events are RESOLVED.
- No commit or tag was created; existing worktree changes and simulator samples were preserved.

## 10. Risks and dependencies

The risk model intentionally forecasts on-hand station stock plus known pending/in-transit station allocations. Scheduled depot supply affects feasible future decisions but is not assumed to become a station delivery. The simulator was left PAUSED at tick 114 and all injected events are RESOLVED. The unrelated host port conflict still requires port 5174 in this environment.

## 11. Acceptance checklist

- [x] During the event, x1.8 demand lowers forecast hours for Mirpur and Tongi within one snapshot cycle.
- [x] After resolution, the multiplier returns to normal and tests show forecast rates moving toward baseline as EWMA calibration converges.
- [x] Consumed inventory remains depleted and risk is recalculated using remaining inventory and normal demand; risk is not expected to return automatically to its original value.
- [x] Live shipment delay updates depot ETA (tick 132→137 for `supply-202`) and DB-backed state returns that ETA.
- [x] With no dependent allocation, shipment delay does not artificially change station risk; regression test confirms unchanged forecast.
- [x] If station allocations exist, projected coverage uses their verified expected arrival ticks; depot supply is never counted as station on-hand inventory.
- [x] Forecast error metric is exposed on worker `/metrics` for all station/fuel pairs.
- [x] Hand-calculated/property tests pass; full suite has 72 passing tests.
- [x] Lint, format check and frontend production build pass.
- [x] Compose configuration, smoke, browser UI and `git diff --check` pass.
- [x] Sprint docs, evidence, report and progress are updated.
- [x] Sprint gate passed after user-authorized acceptance revision; no unsupported shipment behavior added.

## 12. Five-minute update

1. Problem solved: operators can inspect per-station/fuel 24-hour stockout risk and projected inventory uncertainty.
2. What we built: pure demand and inventory projections, seeded Monte Carlo bands, a worker forecast/persistence path, DB-only risk APIs, forecast metrics, and the dashboard matrix/drill-down.
3. Live demonstration: bring up Compose on port 5174, open Stockout risk, select any of 12 pairs, and inspect the trajectory; worker metrics show per-pair forecast error.
4. Evidence: 72 tests pass; lint/build, both Compose config checks, smoke, browser rendering, live risk API, demand spike and depot ETA outcomes are in `docs/evidence/sprint-03-runtime.md`.
5. Remaining gap and next dependency: EWMA calibration may need subsequent normal observations to settle after a spike; Sprint 4 starts from this documented behavior.

## Gate decision

Decision: **passed locally**. Revised acceptance criteria pass against fixture tests and live simulator/API evidence. Local Sprint 3 quality gates passed. No commit or tag created.
