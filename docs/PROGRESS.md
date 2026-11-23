# Project progress

Last updated: 2026-11-23. Resume point for the shared repository worktree.

## Current status

- Branch: `sprints-11-13`, based on `origin/main` (`10554f0`). Tags: `sprint-0`, `sprint-4`, `sprint-5`, `sprint-6`, `sprint-7`, `sprint-8`, `sprint-9`, `sprint-10`, `sprint-11`.
- Sprints 1–11: All gates passed and tagged.
- Sprint 12: In progress. WP12.1 (API Performance), WP12.5 (Backup, Restore & Measured Recovery), WP12.3 (Soak test), WP12.2 (Push updates over SSE), and WP12.4 (Alert routing end to end) COMPLETE.
- Next: WP12.6 Runtime policy switch with automatic rollback (P2).

## Verification in this work package

- WP12.4 Alert routing end to end complete:
  - Added `alertmanager` (`prom/alertmanager:v0.28.0`) and `webhook-receiver` (`observability/webhook_receiver/receiver.py`) under Docker Compose profile `alerts`. Default `docker compose up` starts only the standard 8 services.
  - Added unit test `tests/integration/test_compose_config.py` confirming profile isolation.
  - Added `promtool check rules` step to CI (`.github/workflows/ci.yml`), passing rule validation with 6 rules.
  - Created automated drill `scripts/demonstrate_alert_routing.py`:
    - Injected simulator fault `unavailable` at `2026-11-23T07:28:18.625Z`.
    - Firing alert `SimulatorCircuitBreakerOpen` (severity: `critical`, runbook: `docs/runbook.md#circuit-breaker`) received by webhook at `2026-11-23T07:28:46.347Z`.
    - Cleared fault at `2026-11-23T07:28:46.788Z`.
    - Resolved alert `SimulatorCircuitBreakerOpen` received by webhook at `2026-11-23T07:29:01.351Z` (resolution duration: 15.0s).
    - Saved structured evidence in `docs/evidence/day-4/alert-routing-evidence.json` and `.txt`.
  - Updated `docs/runbook.md` with silencing instructions (`amtool` and UI) and anchor tags (`#circuit-breaker`, `#stale-data`, `#stockout-risk`, `#predictor-fallback`, `#calibration-drift`), and `docs/operations.md` and `docs/decisions.md` (ADR-046).

- WP12.2 Push updates over SSE complete:
  - Implemented `EventBroadcaster` with PostgreSQL `LISTEN/NOTIFY` on `platform_events`, bounded queue (maxsize=100, drops oldest on overflow), connection limit per process (`SSE_MAX_CLIENTS=50`), and automated exponential backoff reconnection.
  - Added `GET /api/stream` endpoint with `: ping\n\n` keepalive heartbeats every 15s, `text/event-stream` headers, and HTTP 429 client limit protection.
  - Added metrics: `sse_clients_connected` (Gauge) and `sse_events_sent_total{event_type}` (Counter).
  - Wired worker persistence notifications on snapshot, forecasts, recommendations, and incidents, and API decision notification.
  - Implemented `useEventStream` React hook in `web/src/features/stream/useEventStream.ts`, invalidating specific TanStack queries on events and disabling interval polling when stream is live. Added 10-second polling fallback when stream disconnects.
  - Added stream status indicator (`● LIVE PUSH` / `○ POLLING FALLBACK`) to web header.
  - Added unit tests in `tests/unit/test_sse_stream.py` (7 tests passed).
  - Recorded empirical request-rate comparison matrix in `docs/loadtest.md` (95% reduction in API read volume during standard operation) and updated `docs/architecture.md`, `docs/api.md`, and `docs/decisions.md` (ADR-045).

- WP12.3 Soak test complete:
  - Implemented `scripts/soak_test.sh` and `scripts/run_soak_test.py` with automated container stats, DB metrics, API probes, and graceful cleanup.
  - Executed soak test with live simulator running at speed=2 under active randomized chaos injection.
  - Metrics verified: API memory drift +14.4 MiB (STABLE < 25 MiB), worker drift +2.4 MiB (STABLE < 15 MiB), database size bounded (33.1 to 35.7 MiB), snapshot pruning active, API read p95 8.7–12.5 ms, 0.0% unexplained errors.
  - Generated `docs/results/soak-test-timeseries.csv` and `docs/results/soak-test-summary.md`. Simulator left PAUSED at tick 153 with zero active faults.

- WP12.5 Backup, restore and measured recovery complete:
  - Created `scripts/backup_db.sh` and `scripts/restore_db.sh` targeting this project's PostgreSQL container.
  - Wrote TDD unit test `tests/unit/test_backup_restore_idempotency.py` (2 passed) verifying idempotency key immutability and executor non-resubmission rules.
  - Automated drill `scripts/drill_backup_restore.py` verified:
    - RTO: **2.93s** (target < 15s MET). Complete 77.6 MB schema and data restoration.
    - RPO: **< 5.0s** (continuous PostgreSQL WAL durability).
    - 100% row preservation across snapshots (419), forecasts (5,004), recommendations (158), decisions (1), depot_risks (1,572), incidents (387).
    - Zero duplicate submissions or regressions. Report: `docs/results/backup-restore-drill.json`.
  - Recovery timing measurement `scripts/measure_recovery_times.py` across all 7 services:
    - `postgres`: 0.38s running, 5.53s healthy, 0.38s data visible.
    - `api`: 0.70s running, 6.03s healthy, 2.26s data visible.
    - `worker`: 0.65s running, 5.94s healthy, 1.85s data visible.
    - `predictor`: 0.63s running, 5.95s healthy, 1.54s data visible.
    - `frontend`: 0.39s running, 5.39s healthy, 0.39s data visible.
    - `prometheus`: 0.39s running, 5.41s healthy, 0.39s data visible.
    - `grafana`: 0.40s running, 5.35s healthy, 0.99s data visible.
    - `full_stack`: 1.02s running, 6.87s healthy, 3.06s data visible in API & UI. Report: `docs/results/recovery-times.json`.
  - Updated `docs/resilience.md` and `docs/operations.md`.

- WP12.1 API performance complete:
  - Baseline k6 sweep (10 to 400 VUs) executed: throughput saturated at 201 req/s, read p95 1,210.6 ms at 100 VUs, Postgres CPU 309.8% at 400 VUs.
  - Profiled with EXPLAIN ANALYZE: identified Seq Scans and quicksorts on `forecasts` (15.342 ms) and `depot_risks` (3.815 ms).
  - Implemented 4 Uvicorn workers, pool size 20, 3 composite indexes (query time dropped to 0.103 ms, 149x speedup), in-memory pre-serialized UTF-8 byte cache, ETag / 304 Not Modified, cached Snapshot Pydantic model for what-if, and scaled rate limiter.
  - Optimized k6 sweep: throughput tripled to **615.3 req/s at 100 VUs** and **625.8 req/s at 200 VUs**; read p50 dropped by 78% (88.2 ms); read p95 dropped by 72% (338.3 ms); what-if p95 dropped by 67% (**288.3 ms**, target < 500 ms MET); Postgres CPU dropped to 34.1%; 0.0% errors.
  - Added ADR-044 and updated `docs/loadtest.md`.

- WP11.2 Robust policy evaluation:
  - Generated 60 randomized crisis scenarios from fixed RNG seed (seed=42) partitioned into 50 tuning scenarios and 10 hold-out scenarios never used for tuning.
  - Executed 240 simulation runs (192 ticks / 2 days each = 46,080 ticks) on live simulator across 4 policies: `none`, `naive`, `heuristic`, `heuristic_buffer`.
  - Headline Results:
    - Heuristic Mean SLA: **97.93%** (Median: 100.0%, P10: 92.54%, Worst: 86.27%, Mean unmet: 4,798 L).
    - Naive Mean SLA: **97.14%** (Median: 100.0%, P10: 90.20%, Worst: 86.27%, Mean unmet: 7,324 L).
    - Do Nothing Mean SLA: **40.40%** (Median: 45.58%, Worst: 22.76%, Mean unmet: 137,340 L).
    - Head-to-head vs Naive: **15 Wins / 44 Ties / 1 Loss**.
    - Bootstrap 95% Confidence Interval for Improvement vs Naive: **+0.79% [0.41%, 1.27%]** SLA.
    - Hold-Out Family Performance (10 compound disasters): Heuristic **96.26% SLA** vs Naive **92.57% SLA** (9 Wins / 0 Ties / 1 Loss).
    - Honest Loss Disclosure: Exactly 1 loss out of 60 scenarios (`holdout_08` at 99.86% vs 99.95%, a -0.08% delta due to compound multi-corridor transit bottleneck timing).
  - Pure module `core.scenario_sweep`: unit tests in `tests/unit/test_scenario_sweep.py` (6 passed in 0.02s).
  - Full suite: 199 Python tests passed, 11 Vitest tests passed, `make lint` clean, `git diff --check` clean.
  - Generated: `docs/results/scenario-sweep.csv`, `docs/results/scenario-sweep.md`, appended to `docs/results/experiments.csv`.
  - Updated `README.md` and `GET /api/evaluation/summary`. Simulator left PAUSED, faults cleared.

  - WP11.3 Forecast Quality & Event-Aware Calibration complete:
    - Root cause of calibration lag resolved: historical expected demand incorporates known event multipliers when `MODEL_VERSION >= "1.2.0"`.
    - Bumped `MODEL_VERSION = "1.2.0"` in `core/version.py`, updated UI footer and evaluation view.
    - Measured spike convergence: Legacy v1.1.0 lag (7 ticks on 2.0x, 19 ticks on 2.5x) -> Event-Aware v1.2.0 lag (0 ticks, instantaneous adaptation).
    - Segmented backtest: Outside events (1h MAPE 2.27%, 24h MAPE 2.10%) vs Inside events (1h MAPE 0.00%, 24h MAPE 3.88%).
    - Probabilistic calibration across 240 simulation runs: Brier score **0.1558**; 5-bin reliability table generated.
    - Pure evaluation helpers: `compute_brier_score`, `evaluate_probability_reliability`, `measure_spike_convergence_ticks` in `core.backtest`.
    - Unit tests: 4 tests in `tests/unit/test_forecast_event_aware.py` (203 Python tests, 11 Vitest tests all passing).
    - Generated `docs/results/backtest-summary.md`, `docs/results/calibration-summary.md`, and `docs/results/event-calibration.md`.

  - WP11.4 Dependency & Security Debt complete:
    - Upgraded dependencies: FastAPI 0.165.0, Starlette 1.10.0, Pytest 9.2.0, Pytest-Asyncio 1.5.0, annotated-doc 0.0.7, opentelemetry-api 1.45.2.
    - `pip-audit`: 0 known vulnerabilities (all 16 Starlette/pytest advisories cleared).
    - `npm audit`: 0 vulnerabilities found in frontend.
    - Trivy Docker container scan: 0 High/Critical findings.
    - Gitleaks Docker container scan: 0 leaks found across repository.
    - Added `.github/dependabot.yml` (weekly updates for pip, npm, github-actions, docker).
    - Enforced strict pip-audit in `.github/workflows/ci.yml`.
    - Updated `docs/security-and-guardrails.md`. Full suite and smoke passed.

  - WP11.5 Tick-Length & Speed Compatibility complete:
    - Codebase audit: zero hardcoded tick length assumptions in platform calculations; all temporal scaling dynamically derives from `instance.tick_minutes`.
    - Parametrized tests: `tests/unit/test_tick_compatibility.py` (12 tests) verifying demand integration invariance (<0.001%), dynamic trajectory scaling, proportional stockout hours, and policy lookahead scaling.
    - Empirical simulator runs: 6h simulated runs executed at both `TICK_MINUTES=8` (45 ticks) and `TICK_MINUTES=15` (24 ticks); both achieved 100.0% service level, 0 stockouts, 0 failures, 100% determinism.
    - Generated `docs/results/tick-compatibility.md`. Simulator container restored to default `TICK_MINUTES=15`, PAUSED, faults cleared.
    - Full suite passing: 215 Python tests, 11 Vitest tests.

## Current work package and exact next action

Sprint 11 P0 and P1 work packages complete (WP11.0, WP11.1, WP11.2, WP11.3, WP11.4, WP11.5).
Next action: Sprint 11 Gate, Reviews (R1, R7, R3), sprint report `docs/sprint-reports/sprint-11.md`, and tag `sprint-11`.


## Workspace constraints

Do not edit `.env`, stage ignored local instructions, expose secrets, reset state outside authorized scenario/cold-start runs, or push. Preserve current Compose volumes and simulator state. Keep public documentation self-sufficient without private development files.

## Sprint log

| Sprint | Status | Report |
|---|---|---|
| Sprint 1 | Passed historically; local verification only | [sprint-01.md](sprint-reports/sprint-01.md) |
| Sprint 2 | Passed historically with runtime evidence | [sprint-02.md](sprint-reports/sprint-02.md) |
| Sprint 3 | Passed historically with revised simulator semantics | [sprint-03.md](sprint-reports/sprint-03.md) |
| Sprint 4 | PASS; live workflow, R3 review, and mechanical gates passed; tag `sprint-4` | [sprint-04.md](sprint-reports/sprint-04.md) |
| Sprint 5 | PASS; live fault/recovery matrix, Prometheus/Grafana, R4 review and mechanical gates passed; tag `sprint-5` | [sprint-05.md](sprint-reports/sprint-05.md) |
| Sprint 6 | PASS; deterministic scenario runner (24 runs), 3-profile k6 load benchmarks, CI hardening, and mechanical gates passed; tag `sprint-6` | [sprint-06.md](sprint-reports/sprint-06.md) |
| Sprint 7 | PASS; cold start (34s), clean clone proof, random chaos, demo script & QA, doc audit; tag `sprint-7` | [sprint-07.md](sprint-reports/sprint-07.md) |
| Sprint 8 | PASS; truth pass, brief compliance (4-26), 6 crisis types, 2-pass triage, pure detectors, depot risk, speed adaptation; tag `sprint-8` | [sprint-08.md](sprint-reports/sprint-08.md) |
| Sprint 9 | PASS; backtest calibration, what-if simulator, 5 operator views, LP optimizer & buffer, incident summarizer; tag `sprint-9` | [sprint-09.md](sprint-reports/sprint-09.md) |
| Sprint 10 | PASS; delivery excellence, rollback drill, resilience limits, decision load test, judging runbook; tag `sprint-10` | [sprint-10.md](sprint-reports/sprint-10.md) |
| Sprint 11 | PASS; truth pass, measured failure boundaries, 60-scenario sweep (95% CI), event-aware calibration, 0 security findings, tick 8/15 compatibility; tag `sprint-11` | [sprint-11.md](sprint-reports/sprint-11.md) |

## Five-minute status update

1. **Problem:** Platform documentation contained unverified derived limits and terminology; policy robustness required proof across randomized scenarios with rigorous confidence intervals; demand forecasting suffered from a 4–6 tick calibration lag under shocks; 16 security advisories affected test/runtime dependencies; tick-length compatibility (8m vs 15m) required empirical verification.
2. **Change:** Conducted documentation truth pass removing fluff and aligning brief compliance (109 rows recounted); empirically swept failure boundaries across 192 ticks identifying binding physical constraints; executed 240 live simulation runs across 60 randomized crisis scenarios proving Heuristic SLA (97.93% vs 97.14% Naive, +0.79% [0.41%, 1.27%] 95% CI); resolved calibration lag by incorporating known event multipliers into historical baseline calculation (Model v1.2.0); cleared all 16 pip-audit advisories (FastAPI 0.165.0, Starlette 1.10.0, Pytest 9.2.0); verified 8m vs 15m tick duration invariance and dynamic scaling.
3. **Demo:** Inspect `docs/results/failure-boundary.png` and `docs/results/scenario-sweep.md`. Run `python3 scripts/backtest.py` to observe 0-tick convergence under demand shocks. Run `pytest tests/unit/test_tick_compatibility.py` to verify temporal scaling.
4. **Evidence:** 215 Python tests + 11 Vitest tests passing; pip-audit 0 vulnerabilities; npm audit 0 vulnerabilities; Gitleaks 0 leaks; Trivy 0 vulnerabilities; mechanical gate `bash scripts/sprint_gate.sh 11` passed.
5. **Remaining:** Sprint 11 complete. Proceeding to Sprint 12 (API performance, SSE push, soak test, alert routing, backup/restore, policy switch).
