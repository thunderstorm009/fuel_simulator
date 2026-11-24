# Day 7 Master Claims Ledger

**Generated:** 2026-11-24
**Audit Standard:** Truth Rule (zero fabricated numbers, zero phantom metrics, every claim backed by executable code or verifiable artifact).
**Repository Branch:** `day-6-7`

---

## Metric & Claim Verification Index

| # | Metric / Claim | Exact Reported Value | Verification Command / Source File | Real Output / Artifact Location |
|:---:|---|---|---|---|
| **1** | Automated Tests (Python) | **239 passed** | `pytest tests/` | `239 passed, 2 warnings in 3.15s` (`tests/`) |
| **2** | Automated Tests (Frontend Unit) | **11 passed** | `npm --prefix web run test` | `11 passed (11) in 0.98s` (`web/tests/`) |
| **3** | Automated Tests (Browser E2E) | **12 passed** | `npm --prefix web run test:e2e` / `make test-e2e` | `12 passed in 28.9s` (`tests/e2e/platform.spec.ts`) |
| **4** | Total Automated Test Suite | **262 tests passing** | `make test && make test-e2e` | Sum: 239 + 11 + 12 = 262 tests |
| **5** | Cold Start Recovery Time | **36 seconds** | `bash scripts/cold_start_check.sh --confirm-volume-destroy` | `docs/evidence/day-6/cold-start.txt` (`cold_start_elapsed_seconds=36`) |
| **6** | Architectural Decisions | **52 ADRs** (ADR-001 to ADR-052) | `docs/decisions.md` | Indexed in `docs/decisions.md` and `docs/README.md` |
| **7** | Real Browser Screenshots | **22 screenshots** | `scripts/capture_day7_evidence.js` | `docs/evidence/day-7/screens/` with `MANIFEST.md` |
| **8** | Accessibility Compliance | **0 Critical violations**, 87.5/100 avg | `node scripts/capture_day7_evidence.js` / Axe-Core | `docs/evidence/day-7/browser-audit.md` |
| **9** | Fault Scene 1 (unavailable) | **0.87s recovery** | `scripts/fault_demo.sh` | Task log 656: `Recovery verified: data_age_seconds: 0.87s` |
| **10** | Fault Scene 2 (error_rate) | **0.21s recovery** | `scripts/fault_demo.sh` | Task log 656: `Recovery verified: data_age_seconds: 0.21s` |
| **11** | Fault Scene 3 (latency) | **0.24s recovery** | `scripts/fault_demo.sh` | Task log 656: `Recovery verified: data_age_seconds: 0.24s` |
| **12** | Fault Scene 4 (stale_data) | **0.65s recovery** | `scripts/fault_demo.sh` | Task log 656: `Recovery verified: stale: false` |
| **13** | Fault Scene 5 (stream_disconnect)| **1.79s recovery** | `scripts/fault_demo.sh` | Task log 656: `Recovery verified: SSE reconnected` |
| **14** | Fault Scene 7 (predictor outage) | **1 tick fallback (8s)** | `scripts/fault_demo.sh` | Task log 656: `tick=1 source=baseline; tick=2 source=remote` |
| **15** | Fault Scene 8 (worker outage) | **0.82s recovery** | `scripts/fault_demo.sh` | Task log 656: `Frontend HTTP 200; Recovery verified: 0.82s` |
| **16** | Deterministic Scenario Sweep | **54 runs, delta 0.0000** | `python3 scripts/scenario_runner.py` | `docs/results/scenario-summary.csv` |
| **17** | 60-Scenario Evaluation SLA | **97.93% average SLA** | `scripts/scenario_sweep.py` | `docs/results/scenario-sweep-summary.json` |
| **18** | Bootstrap 95% Confidence Interval| **+0.79% [0.41%, 1.27%]** | `scripts/scenario_sweep.py` | `docs/results/scenario-sweep-summary.json` |
| **19** | Single Loss Disclosure | **1 loss on holdout_08** (-0.08%) | `scripts/scenario_sweep.py` | `docs/results/scenario-sweep-summary.json` |
| **20** | Demand Baseline MAPE (24h) | **2.11% error** outside events | `scripts/backtest.py` | `docs/results/backtest-summary.json` (`mape_24h: 0.0211`) |
| **21** | Event Probability Calibration | **Brier score 0.1558** | `scripts/backtest.py` | `docs/results/backtest-summary.json` (`brier_score: 0.1558`) |
| **22** | API Throughput Benchmark | **625.8 req/s at 200 VUs** | `k6 run loadtest/k6.js` | `docs/loadtest.md`, `loadtest/summary.json` |
| **23** | Read Path P95 Latency | **338.3 ms** | `k6 run loadtest/k6.js` | `loadtest/summary.json` |
| **24** | What-If Simulation P95 Latency | **288.3 ms** | `k6 run loadtest/k6.js` | `loadtest/summary.json` |
| **25** | Database Restore RTO | **2.93 seconds** | `python3 scripts/drill_backup_restore.py` | `docs/results/backup-restore-drill.json` |
| **26** | Code Vulnerabilities (Python) | **0 vulnerabilities** | `pip-audit` | 0 known CVEs across all pinned requirements |
| **27** | Code Vulnerabilities (Frontend)| **0 vulnerabilities** | `npm audit --prefix web` | 0 vulnerabilities found |
| **28** | Container Vulnerabilities | **0 High/Critical findings** | `trivy fs .` | 0 High or Critical vulnerabilities |
| **29** | Secret Leaks Across History | **0 leaks** | `gitleaks git --verbose` | 65 commits scanned; 0 secrets leaked |
| **30** | Brief Requirements Met | **109 requirements (100% MET)**| `docs/BRIEF-COMPLIANCE.md` | All 109 requirements verified against spec |
| **31** | Network Aggregate Demand | **91,400 L/day (952 L/tick)** | `backend/shared/core/world.py` | Sum of Mirpur, Uttara, Dhanmondi, Gulshan |
| **32** | Depot Maximum Dispatch Limit | **23,000 L/tick (24.1x demand)** | `backend/shared/core/models.py` | Gazipur (12,000) + Patiya (11,000) L/tick |
| **33** | Frontend Bundle Size | **278 kB main chunk** | `npm --prefix web run build` | `dist/assets/index-*.js 278.23 kB` |
| **34** | Live Judging Rehearsals | **3 consecutive passes** | `scripts/demo_director.py` | `docs/evidence/day-7/rehearsal.md` |
