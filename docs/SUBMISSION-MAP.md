# Submission map

| # | Deliverable | Current location | Evidence/status |
|---|---|---|---|
| 1 | Working application | `docker-compose.yml`, `README.md` | All 8 containers healthy; cold-start measured in 34s (`docs/evidence/sprint-07-cold-start.txt`) |
| 2 | Source repository | This repository (`sprints-8-10`) | Git commit history on branch `sprints-8-10`; tags `sprint-0` through `sprint-10` |
| 3 | Simulator integration | `backend/shared/core/sim_client.py`, `backend/worker/` | Typed client, SSE ingestion, permanent idempotency keys; live verification in `docs/evidence/` |
| 4 | Intelligence component | `backend/shared/core/forecast.py`, `risk.py`, `backtest.py`, `policies/` | Deterministic models; 2,000 tick backtest (2.11% MAPE over 24h) in `docs/results/backtest-summary.md`; 54 scenario runs in `docs/results/scenario-summary.md` |
| 5 | Operator interface | `web/` | React 19 + TypeScript + Vite + Tailwind dashboard; What-If simulator, Regional Demand, Supply Timeline, Alert Center; 11/11 Vitest tests pass |
| 6 | Architecture diagram | `docs/architecture.md`, `README.md` | Complete Mermaid loop (Observe-Detect-Predict-Decide-Simulate-Approve-Act-Monitor-Recover) |
| 7 | Deployment | `docker-compose.yml`, `docs/operations.md`, `scripts/deploy.sh`, `scripts/rollback.sh` | Release workflow (`.github/workflows/release.yml`), automated rollback drill in `docs/evidence/sprint-10-rollback-drill.txt` |
| 8 | Observability | `observability/prometheus/`, `observability/grafana/`, `docs/observability.md` | 4 layers (application, system, intelligence, logs); alert rules with runbook links; end-to-end decision trace in `docs/evidence/sprint-10-decision-trace.txt` |
| 9 | Resilience demonstration | `docs/resilience.md`, `scripts/measure_resilience_boundaries.py` | 5 simulator faults + per-service kill -9 recovery (0.10s-0.23s) in `docs/evidence/sprint-10-resilience-matrix.txt` |
| 10 | Load-test evidence | `loadtest/k6.js`, `docs/loadtest.md` | Read path (205k requests, 0% errors) + Decision path What-If (9.5k requests @ 100 VUs, median 122ms, 0% errors) |
| 11 | Final demo & judging pack | `docs/JUDGING-DAY.md`, `scripts/surprise_drill.sh`, `docs/qa.md` | Judging runbook with 10-minute demo script, surprise drill rehearsal, and contingency protocols |
