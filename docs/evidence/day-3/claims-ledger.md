# Day 3 Claims Ledger: Empirical Derivation of Numbers

Every numerical claim in `docs/DAY-3-UPDATE.md` and `README.md` is mapped to its command, execution time, and raw output artifact generated today (2026-11-21).

| Metric / Claim | Exact Value | Source Command / Script | Raw Output Artifact / Evidence File |
|---|---|---|---|
| **Python Unit & Integration Tests** | 182 passed, 0 failed, 1 warning | `pytest tests/` | `task-2235.log` / `tests/` |
| **Frontend Component Tests** | 11 passed (App: 6, NewViews: 5) | `npm --prefix web run test` | `task-2235.log` / `web/tests/` |
| **Python Files Formatted** | 88 files checked, 0 errors | `ruff format --check . && ruff check .` | `task-2235.log` |
| **Frontend Production Modules** | 508 modules transformed | `npm --prefix web run build` | `task-2235.log` / `web/dist/` |
| **Clean-Clone Gate Result** | Code 0 (PASS) | `scripts/verify_clean_clone.sh` | `docs/evidence/clean-clone-check.txt` |
| **Total Scenario Benchmark Runs** | 54 runs (9 scenarios × 3 policies × 2 runs) | `scripts/scenario_runner.py --all --ticks 20` | `task-2350.log` / `docs/results/scenario-summary.csv` |
| **Scenario Determinism Delta** | 0.0000 across all paired runs | `scripts/scenario_runner.py` | `docs/results/scenario-results.json` |
| **Historical Demand Evaluated** | 2,000 ticks across 4 stations, 3 fuels | `scripts/backtest.py` | `docs/results/data/demand_history_96ticks.json` |
| **Backtest 1h Horizon MAPE** | 3.07% (Bias: +0.01%, Coverage: 91.49%) | `scripts/backtest.py` | `docs/results/backtest-summary.md` |
| **Backtest 6h Horizon MAPE** | 2.19% (Bias: -0.13%, Coverage: 65.57%) | `scripts/backtest.py` | `docs/results/backtest-summary.md` |
| **Backtest 12h Horizon MAPE** | 2.10% (Bias: -0.31%, Coverage: 49.86%) | `scripts/backtest.py` | `docs/results/backtest-summary.md` |
| **Backtest 24h Horizon MAPE** | 2.11% (Bias: -0.42%, Coverage: 36.08%) | `scripts/backtest.py` | `docs/results/backtest-summary.md` |
| **k6 Decision Load Requests** | 8,540 requests (131.3 req/s) | `k6 run loadtest/k6.js` | `loadtest/summary.json` / `task-2359.log` |
| **k6 Checks Passed** | 10,675 passed, 0 failed (100.0%) | `k6 run loadtest/k6.js` | `loadtest/summary.json` |
| **k6 Error Rate** | 0.00% across all endpoints | `k6 run loadtest/k6.js` | `loadtest/summary.json` |
| **k6 What-If Median Latency** | 150.1 ms (p90: 628.7 ms, p95: 920.6 ms) | `k6 run loadtest/k6.js` | `loadtest/summary.json` |
| **k6 Overall Median Latency** | 245.5 ms (p90: 955.3 ms, p95: 1279.3 ms) | `k6 run loadtest/k6.js` | `loadtest/summary.json` |
| **PostgreSQL Process Start Time** | 0.10s – 0.16s | `scripts/measure_resilience_boundaries.py` | `docs/evidence/sprint-10-resilience-matrix.txt` |
| **PostgreSQL Docker Healthcheck** | 5.18s (`pg_isready` interval: 5s) | `task-2391` empirical probe | `docs/evidence/day-3/verification.md` |
| **Database Query Readiness Time** | ~1.2s – 1.5s post container start | `task-2391` empirical probe | `docs/evidence/day-3/verification.md` |
| **Traffic Surge Concurrency** | 250 requests @ 25 concurrent workers | `scripts/measure_resilience_boundaries.py` | `docs/evidence/sprint-10-resilience-matrix.txt` |
| **Traffic Surge Latency** | p50: 77.2ms, p95: 143.3ms, p99: 161.2ms | `scripts/measure_resilience_boundaries.py` | `docs/evidence/sprint-10-resilience-matrix.txt` |
| **Total Depot Dispatch Ceiling** | 23,000 L/tick (Gazipur: 12k, Patiya: 11k) | `GET /api/state` network topology | `backend/shared/core/depot_risk.py` |
| **Gitleaks Leaks Detected** | 0 leaks across 20 commits (2.97 MB) | `gitleaks detect --config=.gitleaks.toml` | Step 2379 terminal output |
| **npm audit Vulnerabilities** | 0 vulnerabilities | `npm audit --prefix web` | Step 2376 terminal output |
| **Trivy Container Scan** | 0 CRITICAL, 3 HIGH (Starlette 0.46.2) | `docker run ... aquasec/trivy:latest image fuel_simulator-api:latest` | `task-2387.log` |
| **pip-audit Vulnerabilities** | 16 advisories (Starlette 0.46.2, Pytest 8.3.5) | `pip-audit` via uv `.venv` scan | `task-2383.log` |
| **Decision Rate Limit** | 60 requests per minute | `backend/api/routes/recommendations.py` | `tests/unit/test_token_and_rate_limit.py` |
| **Captured Screenshots** | 17 PNG files (all < 440 KB, total 4.3 MB) | Headless Chrome via Puppeteer in `/tmp` | `docs/evidence/day-3/screens/MANIFEST.md` |
| **Brief Compliance Coverage** | 100% (MET or OPTIONAL-SKIPPED, Sec 4–26) | Independent audit of `docs/BRIEF-COMPLIANCE.md` | `docs/BRIEF-COMPLIANCE.md` |
