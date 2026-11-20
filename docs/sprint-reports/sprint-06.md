# Sprint 06 Report: Proof, load test, CI and main documentation

Time window: 2026-11-20 | Owner: Antigravity | Branch: `overnight-sprints-4-7` | Status: **PASS**

## 1. Objective

Provide deterministic scenario evidence across disruption modes, empirical API load benchmark results with resource telemetry, hardened CI, and complete documentation aligned with implementation.

## 2. Deliverables and what now exists

- **Scenario runner (`scripts/scenario_runner.py`):** CLI supporting `--scenario baseline|spike|route|combined`, `--policy none|naive|heuristic`, `--ticks N`, and `--all`. Declarative disruption scenarios in `scenarios/*.yaml`. Evaluates all 12 scenario-policy configurations twice (24 total runs) to prove determinism. Output captured in `docs/results/scenario-summary.md` and `docs/results/scenario-summary.csv`.
- **Three-condition k6 load benchmark:** Read-only k6 workload (`loadtest/k6.js`) executed under three operational states:
  1. Normal operation: 68,907 requests, 320.5 req/s, avg 159.0 ms, p50 72.6 ms, p95 549.6 ms, 0.0% error rate.
  2. Simulator latency fault (3500ms delay): 66,588 requests, 309.7 req/s, avg 164.6 ms, p50 100.8 ms, p95 523.9 ms, 0.0% error rate.
  3. Predictor stopped: 70,233 requests, 326.6 req/s, avg 156.0 ms, p50 99.9 ms, p95 477.8 ms, 0.0% error rate.
- **Resource consumption telemetry:** `scripts/collect_stats.sh` captured Docker container CPU/memory throughout the runs (`docs/results/docker-stats-latency.csv`, `docs/results/docker-stats-nopredictor.csv`). API CPU peaked at 62.9% under 100 VUs; memory remained stable at 61.4 MiB. PostgreSQL CPU peaked at 42.4%, memory 62.7 MiB.
- **CI hardening:** `.github/workflows/ci.yml` validated with `actionlint` (clean exit 0). Added scenario runner smoke check to Compose workflow; pinned actions, dependency caching, health waiting loop, and failure artifact upload.
- **Clean checkout quickstart check:** `scripts/check_readme.sh` passes cleanly (Vite build, 141 Python + 6 frontend tests, Docker Compose image build, all 8 containers healthy, health/frontend endpoints reachable).
- **Architecture decisions:** Added ADR-031 (k6 installation), ADR-032 (pure local mode), ADR-033 (scenario runner & determinism), ADR-034 (three-condition load benchmark).

## 3. Decisions and constraints

- In simulation mode, allocations are submitted exclusively within `scripts/scenario_runner.py` after an explicit `/admin/reset` and `/admin/pause`. Production operator workflows remain strictly protected by mandatory human approval (AGENTS.md rule 6).
- The API reads solely from PostgreSQL on read paths, insulating operator queries from simulator latency faults and predictor outages.
- k6 raw per-request jsonl logs were excluded from source control to avoid repository bloat; summaries and rendered reports are committed.

## 4. Key files

- `scripts/scenario_runner.py`
- `scenarios/baseline.yaml`, `scenarios/spike.yaml`, `scenarios/route.yaml`, `scenarios/combined.yaml`
- `tests/unit/test_scenario_runner.py`
- `loadtest/k6.js`, `scripts/loadtest_report.py`, `scripts/collect_stats.sh`
- `docs/results/k6-normal-summary.json`, `docs/results/loadtest-normal.md`
- `docs/results/k6-latency-summary.json`, `docs/results/loadtest-latency.md`, `docs/results/docker-stats-latency.csv`
- `docs/results/k6-nopredictor-summary.json`, `docs/results/loadtest-nopredictor.md`, `docs/results/docker-stats-nopredictor.csv`
- `docs/results/scenario-summary.md`, `docs/results/scenario-summary.csv`, `docs/results/scenario-results.json`
- `.github/workflows/ci.yml`
- `docs/loadtest.md`, `docs/testing-and-ci.md`, `docs/decisions.md`

## 5. Verification

| Check | Actual result | Status |
|---|---|---|
| Python unit & integration tests | 141 passed in 1.67s | PASS |
| Frontend component tests | 6 passed (Vitest) | PASS |
| Lint & formatting | Ruff check/format clean; TypeScript typecheck & Vite build clean | PASS |
| Actionlint CI validation | `.github/workflows/ci.yml` clean exit 0 | PASS |
| Scenario runner determinism | 24 runs across 4 scenarios × 3 policies × 2 runs; delta 0.0000 on every pair | PASS |
| Load test runs (3 conditions) | Normal, latency fault, and predictor stopped all completed with 0% error rate | PASS |
| Concurrency knee analysis | p95 latency crosses 500 ms at 100 VUs; median latency stays under 100 ms | PASS |
| README quickstart check (`scripts/check_readme.sh`) | All 8 containers healthy, test suite passes, endpoints return HTTP 200 | PASS |
| Mechanical sprint gate (`scripts/sprint_gate_public.sh 6`) | All checks pass | PASS |

## 6. Acceptance checklist

- [x] A table shows the heuristic policy beats do-nothing and naive on service_level, with determinism proof (`docs/results/scenario-summary.md`).
- [x] `docs/loadtest.md` has workload and numbers from three runs (normal, latency fault, predictor stopped) with knee analysis.
- [x] README quickstart independently verified via `scripts/check_readme.sh`.
- [x] CI hardened with pinned action versions, Compose scenario smoke step, and actionlint passing.
- [x] Documentation updated across architecture, testing, loadtest, decisions, and README.

## 7. Five-minute update

1. **Problem:** Verify that the platform's intelligence decisions outperform trivial policies deterministically under disruptions, and measure API read scalability under operational faults.
2. **Change:** Declarative disruption scenario runner (`scripts/scenario_runner.py`), 24-run determinism verification matrix, 3-condition k6 load testing with resource telemetry, and CI hardening.
3. **Demo:** Run `python scripts/scenario_runner.py --scenario spike --policy heuristic --ticks 20` to demonstrate the autonomous simulation cycle; inspect `docs/results/scenario-summary.md` and `docs/loadtest.md`.
4. **Evidence:** [Scenario summary](docs/results/scenario-summary.md), [Load test documentation](docs/loadtest.md), and [CI workflow](.github/workflows/ci.yml).
5. **Remaining:** Sprint 7 freeze, cold-start timing validation, chaos round, and final documentation audit.
