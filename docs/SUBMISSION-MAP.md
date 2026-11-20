# Submission map

| # | Deliverable | Current location | Evidence/status |
|---|---|---|---|
| 1 | Working application | `docker-compose.yml`, `README.md` | All 8 containers healthy; cold-start measured in 34s (`docs/evidence/sprint-07-cold-start.txt`) |
| 2 | Source repository | This repository (`overnight-sprints-4-7`) | Git commit history on branch `overnight-sprints-4-7`; tags `sprint-4`, `sprint-5`, `sprint-6`, `sprint-7` |
| 3 | Simulator integration | `backend/shared/core/sim_client.py`, `backend/worker/` | Typed client, SSE ingestion, idempotency; Sprint 4 live verification in `docs/evidence/sprint-04-overnight.md` |
| 4 | Intelligence component | `backend/shared/core/forecast.py`, `risk.py`, `policies/` | Deterministic models; 24-run scenario proof (delta 0.0000) in `docs/results/scenario-summary.md` and `docs/results/scenario-results.json` |
| 5 | Operator interface | `web/` | React 19 + TypeScript + Vite + Tailwind dashboard; live approval UX, 6/6 frontend vitest tests pass |
| 6 | Architecture diagram | `docs/architecture.md`, `docs/DAY-1-UPDATE.md` | Complete Mermaid loop (Observe-Detect-Predict-Decide-Simulate-Approve-Act-Monitor-Recover) |
| 7 | Deployment | `docker-compose.yml`, `docs/operations.md`, `.github/workflows/ci.yml` | Hardened CI (actionlint clean); clean-clone test passes in `docs/evidence/clean-clone-check.txt` |
| 8 | Observability | `observability/prometheus/`, `observability/grafana/`, `docs/observability.md` | Prometheus metrics on all services; Grafana alert verified live in `docs/evidence/sprint-05-worker-alert-check.txt` |
| 9 | Resilience demonstration | `docs/resilience.md`, `scripts/fault_demo.sh`, `scripts/chaos_random.py` | 5 simulator faults + crashes verified in `docs/evidence/sprint-05-fault-demo-accepted.txt` and `docs/evidence/sprint-07-chaos.json` |
| 10 | Load-test evidence | `loadtest/k6.js`, `docs/loadtest.md` | 3 measured runs (normal, latency, predictor down); 205k requests, 0% errors, knee at 100 VUs in `docs/results/` |
| 11 | Final demo | `docs/final-demo-script.md`, `docs/qa.md` | Rehearsal-ready demo script; answers to 15 judge questions; limitations in `docs/assumptions-and-limitations.md` |
