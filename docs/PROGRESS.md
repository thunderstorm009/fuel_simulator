# Project progress

Last updated: 2026-11-21. Resume point for the shared repository worktree.

## Current status

- Branch: `sprints-8-10`, based on `dc7f60f`. Tags: `sprint-0`, `sprint-4`, `sprint-5`, `sprint-6`, `sprint-7`, `sprint-8`.
- Sprints 1–8: All gates passed and tagged.
- Sprint 8: COMPLETE. WP8.0 (Truth pass), WP8.1 (Brief compliance matrix), WP8.2 (Full event coverage and two-pass constrained triage), WP8.3 (Pure detection engine), WP8.4 (Depot supply risk & 24h cover), WP8.5 (Running-simulator robustness) all verified. 158 Python tests, 6 frontend tests, 54 scenario runs with 100% determinism.
- Next: Sprint 9 (prompts/SPRINT-09.md: continuous backtesting, what-if simulator, regional supply views, LP/MIP optimization, LLM incident explainer).

## Verification in this work package

- `.venv/bin/ruff check . && .venv/bin/ruff format --check .`: passed; 73 files formatted, 0 errors.
- `.venv/bin/pytest tests/`: 158 Python tests passed in 1.61s.
- `npm --prefix web test -- --run && npm --prefix web run build`: 6 Vitest tests passed; Vite production build passed.
- `FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 docker compose config -q`: passed.
- `git diff --check`: passed.
- `bash scripts/smoke.sh`: passed; all 8 containers healthy.
- Live demand-spike detection & auto-resolution: verified on running stack (`docs/evidence/sprint-08-demand-spike-detection.txt`).
- Simulator speed matrix: measured speeds 1, 4, 8 (`docs/evidence/sprint-08-speed-matrix.txt`).
- Mutation testing: 3 intentional mutations verified and caught by test suite.
- Scenario determinism: 54 benchmark runs (9 scenarios × 3 policies × 2 runs), delta 0.0000.

## Current work package and exact next action

Sprint 8 is COMPLETE and gated.
Next action: Proceed to Sprint 9 work packages (WP9.1 continuous backtesting & calibration).

## Workspace constraints

Do not edit `.env`, stage ignored local instructions, expose secrets, reset state outside authorized scenario/cold-start runs, or push. Preserve current Compose volumes and simulator state. Keep public documentation self-sufficient without private development files.

## Sprint log

| Sprint | Status | Report |
|---|---|---|
| 1 | Passed historically; local verification only | [sprint-01.md](sprint-reports/sprint-01.md) |
| 2 | Passed historically with runtime evidence | [sprint-02.md](sprint-reports/sprint-02.md) |
| 3 | Passed historically with revised simulator semantics | [sprint-03.md](sprint-reports/sprint-03.md) |
| 4 | PASS; live workflow, R3 review, and mechanical gates passed; tag `sprint-4` | [sprint-04.md](sprint-reports/sprint-04.md) |
| 5 | PASS; live fault/recovery matrix, Prometheus/Grafana, R4 review and mechanical gates passed; tag `sprint-5` | [sprint-05.md](sprint-reports/sprint-05.md) |
| 6 | PASS; deterministic scenario runner (24 runs), 3-profile k6 load benchmarks, CI hardening, and mechanical gates passed; tag `sprint-6` | [sprint-06.md](sprint-reports/sprint-06.md) |
| 7 | PASS; cold start (34s), clean clone proof, random chaos, demo script & QA, doc audit; tag `sprint-7` | [sprint-07.md](sprint-reports/sprint-07.md) |
| 8 | PASS; truth pass, brief compliance (4-26), 6 crisis types, 2-pass triage, pure detectors, depot risk, speed adaptation; tag `sprint-8` | [sprint-08.md](sprint-reports/sprint-08.md) |

## Five-minute status update

1. **Problem:** Operators required complete compliance with the 26-section Hackathon brief, zero false/unsubstantiated claims, explicit handling of all six crisis events, automated anomaly detection, forward depot supply risk visibility, and robustness when the simulator runs continuous ticks without manual pausing.
2. **Change:** Implemented a pure deterministic two-pass triage heuristic, 5 crisis scenarios, a pure detection engine (`detect.py`) with 5 detectors and auto-resolution, forward depot cover modeling (`depot_risk.py`) with dashboard panel, dynamic tick freshness monitoring (`ticks_per_second`) with operator speed warning banners, and controllable demo clock stepping (`demo_clock.py`). Remediated all `/admin` routes in app code.
3. **Demo:** Run `./scripts/demo_clock.py --rate 0.5`. Open dashboard at `http://localhost:5174`: inspect live depot risk cover panel, events/incidents panel, and speed telemetry.
4. **Evidence:** 158 Python tests + 6 frontend tests passing cleanly. Live demand-spike auto-resolution documented in `docs/evidence/sprint-08-demand-spike-detection.txt`; speed matrix in `docs/evidence/sprint-08-speed-matrix.txt`; 54 scenario runs with 100% determinism in `docs/results/scenario-summary.md`.
5. **Remaining:** Proceed automatically to Sprint 9 (backtesting, what-if simulation, regional corridor views, LP optimization, LLM explainer).
