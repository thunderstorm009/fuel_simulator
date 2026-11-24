# Submission map

| # | Deliverable | Current location | Evidence/status |
|---|---|---|---|
| 1 | Working application | `docker-compose.yml`, `README.md` | All 8 containers healthy; cold-start measured in 36s (`docs/evidence/day-6/cold-start.txt`) |
| 2 | Source repository | This repository (`day-6-7`) | Git commit history on branch `day-6-7`; tags `sprint-0` through `sprint-14`; 239 Python + 11 Vitest + 12 Playwright tests |
| 3 | Simulator integration | `backend/shared/core/sim_client.py`, `backend/worker/` | Typed client, SSE ingestion, permanent idempotency keys; live verification in `docs/evidence/` |
| 4 | Intelligence component | `backend/shared/core/forecast.py`, `risk.py`, `backtest.py`, `policies/` | Deterministic models; 2,000 tick backtest (2.11% MAPE over 24h) in `docs/results/backtest-summary.md`; 54 scenario runs in `docs/results/scenario-summary.md` (delta 0.0000); event-aware calibration (Brier 0.1558) |
| 5 | Operator interface | `web/` | React 19 + TypeScript + Vite + Tailwind dashboard; What-If simulator, Regional Demand, Supply Timeline, Alert Center; 12/12 Playwright e2e tests pass; axe-core 0 critical a11y violations |
| 6 | Architecture diagram | `docs/architecture.md`, `README.md` | Complete Mermaid component topology and 5 sequence diagrams; 52 documented ADRs in `docs/decisions.md` |
| 7 | Deployment | `docker-compose.yml`, `docs/operations.md`, `scripts/deploy.sh`, `scripts/rollback.sh` | Release workflow (`.github/workflows/release.yml`), automated rollback drill, clean clone check in `scripts/verify_clean_clone.sh` |
| 8 | Observability | `observability/prometheus/`, `observability/grafana/`, `docs/observability.md` | 4 layers (application, system, intelligence, logs); alert rules with Alertmanager routing; Grafana dashboards provisioned |
| 9 | Resilience demonstration | `docs/resilience.md`, `scripts/fault_demo.sh` | All 8 fault scenarios verified; circuit breakers with half-open concurrency guard; baseline heuristic fallback; RTO 2.93s |
| 10 | Load-test evidence | `loadtest/k6.js`, `docs/loadtest.md` | 625.8 req/s throughput (3.1x target), p95 18.2ms; Decision path What-If (9.5k requests @ 100 VUs, median 122ms, 0% errors) |
| 11 | Final demo & judging pack | `docs/JUDGING-DAY.md`, `scripts/demo_director.py`, `scripts/preflight_judging.sh`, `docs/qa.md` | Preflight script (`make preflight`), interactive storyline runner, 3 live rehearsals, emergency static backup pack (`docs/DEMO-BACKUP.md`) |
