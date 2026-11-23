# Project progress

Last updated: 2026-11-23. Resume point for the shared repository worktree.

## Current status

- Branch: `sprints-11-13`, based on `origin/main` (`10554f0`). Tags: `sprint-0`, `sprint-4`, `sprint-5`, `sprint-6`, `sprint-7`, `sprint-8`, `sprint-9`, `sprint-10`.
- Sprints 1–10: All gates passed and tagged.
- Sprint 11: In progress. WP11.0 (Truth pass on Day 3 and related docs) COMPLETE.
- Next: WP11.1 Measured failure boundary (P0).

## Verification in this work package

- Truth-pass grep: `git grep -n -i "refinery\|pipeline capacity\|corridor throughput\|chittagong\|conservation law\|reverse proxy\|vehicle quota\|price spike\|redis\|cryptograph" -- . ':!prompts' ':!reference'`: all hits verified as true (ADRs, historical audits, or Day 3 corrections).
- Brief compliance matrix re-enumerated from brief text: 109 requirements (107 MET, 1 OPTIONAL-SKIPPED, 1 PARTIAL).
- Derived physical limits replaced with exact demand arithmetic from `core/world.py`: 91,400 L/day across 4 stations, ~952 L/tick (15-min) average, depot dispatch capacity (23k L/tick) is >24x demand and not binding; binding limits are depot stock, resupply arrivals, route shipment caps (5-7k L), tank ullage, and transit delay.
- What-If latency accurately stated (<50ms unloaded, ~834ms under 100 VU load).
- Container process restart times (0.10s-0.23s) distinguished from full query recovery (~1.2s).
- `.venv/bin/ruff format --check . && .venv/bin/ruff check .`: passed.
- `.venv/bin/pytest tests/`: 182 passed.
- `npm --prefix web run typecheck && npm --prefix web run test`: passed (11 Vitest tests).
- `git diff --check`: passed.

## Current work package and exact next action

Sprint 11 WP11.0 complete.
Next action: WP11.1 Measured failure boundary (P0) — parameter sweeps across 192+ ticks for demand spikes, supply shortfalls, disrupted routes, station outages, and combined crisis scenarios.


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

## Five-minute status update

1. **Problem:** Final delivery required production-grade delivery automation, empirical measurement of system failure boundaries, full 4-layer observability with alerting as code, decision-path load testing, 100% brief compliance, and a judging day presentation pack.
2. **Change:** Added versioning API (`/api/version`) and UI footer, constant-time token verification with rate limiting, container release workflow (`release.yml`), automated rollback scripts (`deploy.sh`, `rollback.sh`), empirical resilience benchmarks (per-service kill recovery in 0.10s-0.23s, database outage in 0.16s), decision load test in k6 (9.5k reqs @ 100 VUs, median 122ms, 0% errors), surprise rehearsal drill (`surprise_drill.sh`), and judging guide (`docs/JUDGING-DAY.md`).
3. **Demo:** Open `http://localhost:5173`: Follow the 10-minute presentation script in `docs/JUDGING-DAY.md`. Rehearse surprise fault injects with `scripts/surprise_drill.sh`.
4. **Evidence:** 182 Python tests + 11 Vitest tests passing; rollback drill verified in `docs/evidence/sprint-10-rollback-drill.txt`; decision trace in `docs/evidence/sprint-10-decision-trace.txt`; 100% brief compliance in `docs/BRIEF-COMPLIANCE.md`; mechanical gate `bash scripts/sprint_gate.sh 10` passed.
5. **Remaining:** All 10 sprints complete. Ready for final project-owner review and push.
