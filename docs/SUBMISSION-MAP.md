# Submission map

| # | Deliverable | Current location | Evidence/status |
|---|---|---|---|
| 1 | Working application | `docker-compose.yml`, `README.md` | All 8 containers healthy; cold-start measured in 36s (`docs/evidence/day-6/cold-start.txt`, pre-built images) |
| 2 | Source repository | This repository (`main` / `final-audit`) | Git commit history; tags `sprint-0` through `sprint-16`, `v1.0.0`; 240 Python + 12 Vitest + 12 Playwright tests (264 total) |
| 3 | Simulator integration | `backend/shared/core/sim_client.py`, `backend/worker/` | Typed client, SSE ingestion, permanent idempotency keys; live verification in `docs/evidence/` |
| 4 | Intelligence component | `backend/shared/core/forecast.py`, `risk.py`, `backtest.py`, `policies/` | Deterministic models; 3,152-tick backtest (2.10% 24h outside-event MAPE, 2.71% overall 24h MAPE) in `docs/results/backtest-summary.md`; 54 scenario runs in `docs/results/scenario-summary.md` (delta 0.0000); 60-scenario sweep (`97.93%` SLA, `+0.79% [0.41%, 1.27%]`); event-aware calibration (Brier 0.1558) |
| 5 | Operator interface | `web/` | React 19 + TypeScript + Vite + Tailwind dashboard; What-If simulator, Regional Demand, Supply Timeline, Alert Center; 12/12 Playwright e2e tests pass; 0 Critical / 0 Serious automated axe-core violations |
| 6 | Architecture diagram | `docs/architecture.md`, `README.md` | Complete Mermaid component topology and 6 sequence diagrams; 54 documented ADRs in `docs/decisions.md` |
| 7 | Deployment | `docker-compose.yml`, `docs/operations.md`, `scripts/deploy.sh`, `scripts/rollback.sh` | Release workflow (`.github/workflows/release.yml`), automated rollback drill, clean clone check in `scripts/verify_clean_clone.sh` |
| 8 | Observability | `observability/prometheus/`, `observability/grafana/`, `docs/observability.md` | 4 layers (application, system, intelligence, logs); alert rules with Alertmanager routing; Grafana dashboards provisioned (bound to `127.0.0.1`) |
| 9 | Resilience demonstration | `docs/resilience.md`, `scripts/fault_demo.sh` | All 8 fault scenarios verified; circuit breakers with half-open concurrency guard; baseline heuristic fallback; `psql` restore RTO 2.93s |
| 10 | Load-test evidence | `loadtest/k6.js`, `docs/loadtest.md` | Sprint 12 sweep: `615.3 req/s` (`338.3ms` read p95) @ 100 VUs, `625.8 req/s` (`622.5ms` read p95) @ 200 VUs; clean-clone `loadtest/k6.js` (100 VUs): `374.57 req/s`, read p95 `378.84ms`, What-If p95 `514.49ms` (0% errors); unloaded What-If `p50=14.67ms`, `p95=18.87ms` |
| 11 | Final demo & judging pack | `docs/JUDGING-DAY.md`, `docs/presentation/`, `scripts/demo_director.py`, `scripts/preflight_judging.sh`, `docs/qa.md` | Preflight script (`make preflight`), interactive storyline runner, 3 automated dry runs, offline backup pack (`docs/DEMO-BACKUP.md`, `docs/presentation/BACKUP-PLAN.md`) |
