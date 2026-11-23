# Day 4 Claims Ledger

**Document Mapped:** `docs/DAY-4-UPDATE.md`  
**Audit Principle:** Every number, metric, benchmark, and claim is traced to a verifiable command output or generated artifact in this repository. Zero fabricated numbers.

---

## Metric & Claim Verification Index

| # | Metric / Claim | Value in Report | Command / Source File | Verification Output / Location |
|---|---|---|---|---|
| 1 | Day 4 Commit Count | 31 commits | `git rev-list --count sprint-10..HEAD` | Output: `31` |
| 2 | Code Churn | 177 files changed, +13,122 / -1,692 | `git diff sprint-10..HEAD --shortstat` | Output: `177 files changed, 13122 insertions(+), 1692 deletions(-)` |
| 3 | Baseline Tag | `0a871e6` | `git rev-parse --short sprint-10` | Output: `0a871e6` |
| 4 | Final Head Commit | `cd9cf4b` | `git rev-parse --short HEAD` | Output: `cd9cf4b` |
| 5 | Scenario Sweep Runs | 240 live simulation runs (46,080 ticks / 480 days) | `python3 scripts/scenario_sweep.py` | `docs/results/scenario-sweep-summary.json` (`total_runs: 240`) |
| 6 | Crisis Scenarios | 60 scenarios (50 tuning, 10 hold-out, seed=42) | `scripts/scenario_sweep.py` | `docs/results/scenario-sweep-summary.md` |
| 7 | Heuristic Policy SLA | 97.93% average SLA (15 W / 44 T / 1 L) | `scripts/scenario_sweep.py` | `docs/results/scenario-sweep-summary.json` (`mean_service_level: 0.9793`) |
| 8 | Bootstrap 95% CI | +0.79% [0.41%, 1.27%] | `scripts/scenario_sweep.py` | `docs/results/scenario-sweep-summary.json` (`bootstrap_ci: [0.0041, 0.0127]`) |
| 9 | Single Loss Disclosure | `holdout_08` (99.86% vs 99.95%, -0.08% delta) | `scripts/scenario_sweep.py` | `docs/results/scenario-sweep-summary.json` (`losses: [...]`) |
| 10 | Spike Adaptation Lag | 0-tick lag (instantaneous) | `tests/unit/test_forecast_event_aware.py` | `test_event_aware_spike_immediate_adaptation` passed |
| 11 | 24h Baseline MAPE | 2.11% outside events | `scripts/backtest.py` | `docs/results/backtest-summary.json` (`mape_24h: 0.0211`) |
| 12 | Brier Calibration Score | 0.1558 | `scripts/backtest.py` | `docs/results/backtest-summary.json` (`brier_score: 0.1558`) |
| 13 | Query Latency Reduction | 15.3ms down to 0.103ms (149× speedup) | `EXPLAIN ANALYZE` on indexed tables | `docs/loadtest.md`, `docs/decisions.md` (ADR-044) |
| 14 | API Throughput | 625.8 req/s at 200 VUs | `k6 run loadtest/k6.js` | `docs/loadtest.md`, `loadtest/summary.json` (`http_reqs_per_sec: 625.8`) |
| 15 | Read P95 Latency | 338.3 ms | `k6 run loadtest/k6.js` | `loadtest/summary.json` (`http_req_duration.p95: 338.3`) |
| 16 | What-If P95 Latency | 288.3 ms | `k6 run loadtest/k6.js` | `loadtest/summary.json` (`whatif_duration_ms.p95: 288.3`) |
| 17 | Database CPU Reduction | 309.8% down to 34.1% | Docker stats during k6 run | `docs/loadtest.md`, `docs/results/docker-stats-scaled.csv` |
| 18 | Read Polling Reduction | 95% reduction via SSE | SSE `GET /api/stream` invalidation | `docs/loadtest.md`, `tests/integration/test_sse.py` |
| 19 | Database Restore RTO | 2.93 seconds | `python3 scripts/drill_backup_restore.py` | `docs/evidence/day-4/drill_backup_restore.log` (`RTO: 2.93s`) |
| 20 | Chaos Soak Drift | API +14.4 MiB, Worker +2.4 MiB (90 mins) | `scripts/run_soak_test.py` | `docs/results/soak-test-summary.json` |
| 21 | Python Tests | 237 passed | `pytest tests/` | Output: `237 passed, 2 warnings in 3.22s` |
| 22 | Frontend Tests | 11 passed | `npm --prefix web run test` | Output: `11 passed (11) in 1.11s` |
| 23 | Browser E2E Tests | 12 passed in 28.9s | `npm --prefix web run test:e2e` | `docs/evidence/day-4/playwright.log`, `docs/results/playwright-results.json` |
| 24 | Accessibility Score | 0 critical violations; 90/100 subpages | `node scripts/audit_accessibility.js` | `docs/evidence/day-4/accessibility-audit.md` |
| 25 | Hackathon Requirements | 109 requirements (100% MET/OPTIONAL) | `docs/BRIEF-COMPLIANCE.md` | 109 discrete requirements audited |
| 26 | System Average Demand | 952 L/tick (91,400 L/day ÷ 96 ticks) | `scripts/measure_failure_boundaries.py` | 91,400 L/day across 4 retail stations |
| 27 | Depot Combined Dispatch | 23,000 L/tick (24.1× average demand) | `backend/shared/core/models.py`, `scripts/measure_failure_boundaries.py` | Gazipur (12,000) + Patiya (11,000) |
| 28 | Truck Capacity Bounds | 5,000 to 7,000 L per route | `backend/shared/core/models.py` | Route truck shipment limits |
| 29 | Starvation Resupply Ratio | 0.40 resupply factor | `scripts/measure_failure_boundaries.py` | Boundary sweep inflection point |
