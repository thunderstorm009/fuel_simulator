# Sprint 05 Report: Observability and resilience

Time window: 2026-11-20 | Owner: Codex | Branch: `main`, base `b1fc38b` | Status: **Blocked on live runtime acceptance**

## 1. Objective

Make service state and failure responses visible, add predictor fallback, and demonstrate fault detection and recovery.

## 2. What now exists

- Predictor `POST /predict` validates a snapshot slice and returns shared-core forecast output. Worker uses a bounded remote client and a single-probe circuit breaker; fallback uses profile demand only, caps confidence at 0.4, and sets `needs_review`.
- Predictor fallback creates/resolves an incident, emits a low-cardinality counter and structured log record, and continues to persist forecast results.
- `/api/health` aggregates database, worker/simulator heartbeat and age, predictor ping, decision engine age, request p95, and observed API 5xx ratio. Frontend health view/banner and Grafana dashboard/alerts are provisioned.
- Added integration coverage for unavailable/error-rate/latency-shaped ingestion failure, stale responses, malformed data, and a regression proving only one predictor half-open probe proceeds.
- Added `scripts/fault_demo.sh`; runtime scenes were not executed.

## 3. Decisions

- Kept forecast/risk computation in shared pure core code and used a separate predictor HTTP boundary. Remote failure does not affect the recommendation feasibility validator.
- Used a profile-only fallback with review required; no confidence higher than 0.4 is claimed for fallback forecasts.
- The live fault script clears simulator faults on exit. It does not approve or submit recommendations.

## 4. Key files

`backend/worker/forecaster.py`, `forecast_job.py`, `store.py`, `backend/api/routes/health.py`, `backend/api/routes/chaos.py`, `intel/predictor/app/main.py`, `web/src/features/system-health/`, `observability/grafana/provisioning/`, `scripts/fault_demo.sh`, and `tests/integration/test_resilience.py`.

## 5. APIs

- `POST /predict`: validated forecast request to independent predictor.
- `POST /api/chaos/forecast-fail`: token-protected predictor failure switch.
- `GET /api/health`: database-backed component health and API latency/error summary.

## 6. Verification

| Check | Actual result | Status |
|---|---|---|
| Full Python suite | 123 passed; frontend Vitest 3 passed | PASS |
| Frontend tests | 3 passed | PASS |
| `make lint` | Ruff and format checks passed; TypeScript passed; Vite production build passed (500 modules) | PASS |
| Compose config / `git diff --check` | Exit 0 | PASS |
| Fault injection and recovery, five simulator faults | Docker socket unavailable; not run | NOT-RUN |
| Predictor stop/fallback/recovery and worker stop | Docker socket unavailable; not run | NOT-RUN |
| Grafana panels move during event/fault | Docker socket unavailable; not run | NOT-RUN |

## 7. Evidence

Local test/build output is recorded in `docs/evidence/sprint-05-runtime.md`. No new live runtime capture was produced. Historical Sprint 2 fault evidence is in `docs/evidence/sprint-02-runtime.md` and does not verify this Sprint 5 runtime.

## 8. Problems and fixes

The first new half-open breaker test failed because concurrent calls could all pass after reset. Added an async-lock-protected single-probe guard; full verification was rerun. Docker daemon unavailability prevented live acceptance checks.

## 9. Not done / risks

The fault demo, predictor-stop and recovery, worker-stop behavior, dashboard movement, and five-fault recovery are not demonstrated in this environment. The frontend image was not rebuilt. No live runtime pass is claimed.

## 10. Next dependency

Restore Docker and run the live resilience matrix on a dedicated demo stack. Confirm `PREDICTOR_URL` configuration without exposing `.env` values.

## 11. Acceptance checklist

- [x] Predictor endpoint, fallback, health UI, and dashboards implemented.
- [x] Local resilience tests, lint, frontend tests/build, Compose config, and whitespace check passed.
- [ ] Five simulator faults detected and recovered live — NOT-RUN.
- [ ] Predictor stop/fallback/recovery and worker stop/data-age demonstrated — NOT-RUN.
- [ ] Grafana panels move under injected conditions — NOT-RUN.
- [ ] Sprint 5 gate passed — No; live runtime acceptance remains open.

## 12. Five-minute update

1. Problem: failures were not sufficiently visible and predictor failure needed a review-required path.
2. Change: remote predictor, bounded breaker/fallback, health aggregation, UI banner, Grafana provisioning, tests and fault demo.
3. Demo: not available while Docker daemon is offline; planned steps are in `docs/final-demo-script.md`.
4. Evidence: 123 Python and 3 frontend tests; lint/typecheck/build and Compose config pass.
5. Gap: current live fault, recovery, Grafana, and stop/restart evidence is absent.

## Gate decision

**Blocked.** Local checks pass. Live acceptance is NOT-RUN because Docker is unavailable.
