# Sprint 11 Report: Truth, Measured Limits, Robust Policy Evaluation, Forecast Quality, Security Debt, and Tick Compatibility

Time window: 2026-11-23 | Owner: Engineering Agent (Autonomous run) | Branch: `sprints-11-13` | Status: **PASS**

---

## 1. Objective

Make every claim in the public platform documentation true and proven, replace derived guesses with empirical measurements, prove the heuristic allocation policy is robust across randomized scenarios with bootstrap confidence intervals, eliminate forecast calibration lag under demand shocks, resolve all dependency security vulnerabilities, and verify tick-length compatibility across 8-minute and 15-minute intervals.

---

## 2. What Now Exists

### WP11.0: Truth Pass on Day 3 & Documentation Audit (P0)
- Audited `docs/DAY-3-UPDATE.md`, `README.md`, `docs/resilience.md`, `docs/JUDGING-DAY.md`, `docs/qa.md`, and `docs/BRIEF-COMPLIANCE.md`.
- Removed unsubstantiated terminology (`refinery`, `pipeline capacity`, `corridor throughput`, `Chittagong`, `mathematical conservation laws`, `reverse proxy`).
- Replaced the derived "23k L/tick ceiling vs 30k demand" with exact profile arithmetic from `backend/shared/core/world.py`: network baseline demand across 4 stations and 3 fuels is exactly 91,400 L/day (~952 L per 15-min tick); depot dispatch capacity (23k L/tick) is >24x baseline demand and not binding.
- Re-enumerated and recounted the official brief compliance matrix directly from extracted brief text: 109 requirements (107 MET, 1 OPTIONAL-SKIPPED, 1 PARTIAL).
- Added Section 16 "Corrections to Day 3 Claims" in `docs/DAY-3-UPDATE.md`. Recorded ADR-042.

### WP11.1: Measured Failure Boundaries (P0)
- Implemented pure domain module `backend/shared/core/failure_boundary.py` (`compute_theoretical_days_of_cover`, `identify_binding_constraint`, `find_service_level_thresholds`).
- Added 11 unit tests in `tests/unit/test_failure_boundary.py` (all passed).
- Executed comprehensive 192-tick empirical sweep on live simulator (`scripts/measure_failure_boundaries.py`) across demand surge (1.0x–3.0x), supply shortfall (1.0x–0.2x), route disruption (0–4 routes), station outages (0–2 stations), and compound stress.
- Measured exact empirical crossover points:
  - 99% SLA: Heuristic 2.43x demand surge vs Naive 1.96x vs None 1.0x.
  - 95% SLA: Heuristic 2.80x demand surge vs Naive 2.55x vs None 1.0x.
  - 90% SLA: Heuristic >3.0x (91.66% at 3.0x) vs Naive 2.95x vs None 1.0x.
- Identified physical binding constraints from measurements: route single-shipment ceilings (5k–7k L) bind under demand surge >2.2x; depot inventory exhaustion binds under supply shortfall factor <0.4; network partition isolates stations when $\ge 3$ routes close.
- Generated `docs/results/failure-boundary.md`, `docs/results/failure-boundary-summary.csv`, and `docs/results/failure-boundary.png`. Recorded ADR-043 (`matplotlib` dev dependency).

### WP11.2: Robust Policy Evaluation (P0)
- Implemented pure domain module `backend/shared/core/scenario_sweep.py` (fixed RNG seed=42, 60 randomized crisis scenarios with 10 holdout compound disasters, win/tie/loss tracking, bootstrap 95% confidence intervals, and loss diagnosis).
- Added 6 unit tests in `tests/unit/test_scenario_sweep.py` (all passed).
- Executed 240 simulation runs (60 scenarios × 4 policies × 192 ticks = 46,080 ticks) on live simulator (`scripts/scenario_sweep.py`).
- Empirical results:
  - `heuristic`: Mean SLA **97.93%** (Median: 100.0%, P10: 92.54%, Worst: 86.27%, Mean unmet: 4,798 L).
  - `naive`: Mean SLA **97.14%** (Median: 100.0%, P10: 90.20%, Worst: 86.27%, Mean unmet: 7,324 L).
  - `none`: Mean SLA **40.40%** (Median: 45.58%, Worst: 22.76%, Mean unmet: 137,340 L).
  - Head-to-head record vs Naive: **15 Wins / 44 Ties / 1 Loss**.
  - Bootstrap 95% Confidence Interval for Improvement vs Naive: **+0.79% [0.41%, 1.27%]** SLA, cutting unmet demand by **35%** (4,798 L vs 7,324 L).
  - Holdout disaster family performance: Heuristic **96.26% Mean SLA** vs Naive **92.57% Mean SLA** (9 Wins, 0 Ties, 1 Loss).
  - Honest loss disclosure: Exactly 1 loss out of 60 scenarios (`holdout_08` at 99.86% vs 99.95%, -0.08% delta) due to compound transit bottleneck timing.
- Generated `docs/results/scenario-sweep.csv`, `docs/results/scenario-sweep.md`, and updated `README.md` and `GET /api/evaluation/summary`.

### WP11.3: Forecast Quality: Event-Aware Calibration & Honest Accuracy (P1)
- Resolved the 4–6 tick calibration lag root cause: legacy model computed historical baseline with hardcoded `multiplier=1.0`, forcing the EWMA ratio to absorb demand surges over 4–6 ticks and leading to double-counting.
- Implemented pure evaluation helpers in `backend/shared/core/backtest.py`: `compute_brier_score`, `evaluate_probability_reliability`, and `measure_spike_convergence_ticks`.
- Built event-aware calibration in `backend/shared/core/risk.py` (`get_station_multiplier_at_tick`) active when `MODEL_VERSION >= "1.2.0"`. Bumped `MODEL_VERSION = "1.2.0"` in `core/version.py`.
- Added 4 unit tests in `tests/unit/test_forecast_event_aware.py`.
- Measured spike convergence:
  - 2.0x surge: Legacy v1.1.0 lag (7 ticks, ~105 min) -> Event-Aware v1.2.0 lag (**0 ticks**, instantaneous adaptation).
  - 2.5x surge: Legacy v1.1.0 lag (19 ticks, ~285 min) -> Event-Aware v1.2.0 lag (**0 ticks**, instantaneous adaptation).
- Evaluated probabilistic calibration across 240 simulation runs: Brier score **0.1558** (high sharpness), 5-bin reliability table generated.
- Generated `docs/results/backtest-summary.md`, `docs/results/calibration-summary.md`, and `docs/results/event-calibration.md` with explicit Truth Rule disclaimer.

### WP11.4: Dependency & Security Debt (P0)
- Upgraded Python dependencies: FastAPI `0.165.0`, Starlette `1.10.0`, Pytest `9.2.0`, Pytest-Asyncio `1.5.0`, annotated-doc `0.0.7`, opentelemetry-api `1.45.2`.
- Pinned exact versions in `requirements.txt` and `requirements-dev.txt`.
- Ran `.venv/bin/pip-audit`: **0 known vulnerabilities** (all 16 Starlette/pytest advisories cleared).
- Ran `npm --prefix web audit`: **0 vulnerabilities found**.
- Executed Gitleaks via Docker (`zricethezav/gitleaks:latest`): **no leaks found** (247 MB scanned).
- Executed Trivy via Docker (`aquasec/trivy:latest`): **0 High/Critical vulnerabilities** across `requirements.txt` and `web/package-lock.json`.
- Added `.github/dependabot.yml` covering pip, npm, github-actions, and docker with weekly schedule.
- Updated `.github/workflows/ci.yml` removing fallback tolerance from `pip-audit`.
- Documented complete security posture and audit results in `docs/security-and-guardrails.md`.

### WP11.5: Tick-Length & Speed Compatibility (P0)
- Codebase audit: zero hardcoded tick length assumptions in platform calculations; all temporal scaling dynamically derives from `instance.tick_minutes`.
- Built parametrized test suite `tests/unit/test_tick_compatibility.py` (12 tests) verifying:
  - Demand integration invariance (<0.001% variance).
  - Dynamic trajectory scaling (96 rates for 15m, 180 rates for 8m).
  - Proportional scaling of `hours_to_stockout`, Monte Carlo stochastic horizons, and policy lookahead (`ticks_12h = round(12*60/tick_minutes)`).
- Recreated simulator container under `TICK_MINUTES=8` and ran live simulation scenarios:
  - Baseline (45 ticks = 6h): 100.0% service level, 0 stockouts, 0 allocation failures, 100% deterministic across runs.
  - Demand spike (45 ticks = 6h): 100.0% service level, 0 stockouts, 0 allocation failures, 100% deterministic across runs.
- Recreated simulator container under `TICK_MINUTES=15` and confirmed identical performance (24 ticks = 6h, 100.0% SLA, 0 stockouts).
- Restored simulator container to default `TICK_MINUTES=15`, status `PAUSED`, zero faults.
- Generated `docs/results/tick-compatibility.md` with complete comparative table and code audit justification.

---

## 3. Decisions Recorded

- **ADR-042**: Documentation Truth Pass and Brief Compliance Recount Methodology.
- **ADR-043**: Addition of Matplotlib as Development Dependency for Failure Boundary Curve Rendering.

---

## 4. Independent Review Verification

- **R1 (Architecture & Boundaries)**: `docs/reviews/sprint-11-r1.md` — PASS (0 P0, 0 P1, 0 P2 violations). Pure domain core preserved; zero simulator I/O in API; REST truth and SSE refetch semantics verified.
- **R7 (Brief Compliance)**: `docs/reviews/sprint-11-r7.md` — PASS (107 MET, 1 OPTIONAL-SKIPPED, 1 PARTIAL). All cited to exact brief sections.
- **R3 (Allocation Safety)**: `docs/reviews/sprint-11-r3.md` — PASS (0 P0, 0 P1 findings). Constraint validation order, permanent idempotency keys, and human approval gates confirmed.

---

## 5. Verification Evidence & Quality Gates

- `ruff check . && ruff format --check .`: Clean across 96 files, 0 errors.
- `pytest tests/`: **215 tests passing** in 1.66s (unit, integration, scenario).
- `vitest run`: **11 tests passing** in 1.04s.
- `tsc -b && vite build`: Frontend production build clean.
- `make smoke`: Full Docker Compose stack built and verified healthy.
- `git diff --check`: Clean, zero whitespace errors.
- `pip-audit`: 0 known vulnerabilities.
- `npm audit`: 0 vulnerabilities.
- `zricethezav/gitleaks:latest`: 0 leaks found.
- `aquasec/trivy:latest`: 0 vulnerabilities found.
- Simulator container: Verified `PAUSED` at tick 0 with 0 active faults and default speed/tick length.
- Mechanical gate: `bash scripts/sprint_gate.sh 11` PASSED.
