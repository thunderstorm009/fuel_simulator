# Project progress

Last updated: 2026-11-21. Resume point for the shared repository worktree.

## Current status

- Branch: `sprints-8-10`, based on `dc7f60f`. Tags: `sprint-0`, `sprint-4`, `sprint-5`, `sprint-6`, `sprint-7`, `sprint-8`, `sprint-9`.
- Sprints 1–9: All gates passed and tagged.
- Sprint 9: COMPLETE. WP9.1 (Backtesting, calibration, versioning, experiments), WP9.2 (What-if simulator), WP9.3 (Operator view gaps: regional demand, incoming supply, alert center, network view, evaluation page), WP9.4 (Uncertainty buffer & LP optimizer), WP9.5 (Generative incident explanations) all verified. 177 Python tests, 11 frontend tests.
- Next: Sprint 10 (prompts/SPRINT-10.md: security hardening, decision load testing, cold start resilience, compliance pass, demo day runbook).

## Verification in this work package

- `.venv/bin/ruff format --check . && .venv/bin/ruff check .`: passed; 85 files checked, 0 errors.
- `.venv/bin/pytest tests/`: 177 Python tests passed in 1.74s.
- `npm --prefix web test -- --run && npm --prefix web run build`: 11 Vitest tests passed; Vite production build passed cleanly.
- `docker compose config -q`: passed.
- `git diff --check`: passed.
- `bash scripts/sprint_gate.sh 9`: passed.
- Backtesting: 2,000 ticks replayed across 1h, 6h, 12h, 24h horizons. MAPE 2.11%-3.07%.
- What-If Simulator: pure candidate simulation with zero DB/simulator writes (<50ms).
- Operator Views: Regional demand, incoming supply, alert center, network view, evaluation scorecard.
- Generative Explanations: deterministic template default with bounded LLM wrapper (3s timeout, safe fallback).

## Current work package and exact next action

Sprint 9 is COMPLETE and gated.
Next action: Proceed to Sprint 10 work packages (WP10.1 Security hardening & zero-vulnerability audit).

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
| 9 | PASS; backtest calibration, what-if simulator, 5 operator views, LP optimizer & buffer, incident summarizer; tag `sprint-9` | [sprint-09.md](sprint-reports/sprint-09.md) |

## Five-minute status update

1. **Problem:** Operators required verified forecast accuracy and calibration bounds, interactive what-if simulation to test candidate allocations before approving, comprehensive operational views (regional demand, incoming supply, alert center, network topology, offline evaluation scorecard), uncertainty safety buffers, and plain-language incident explanations.
2. **Change:** Implemented pure backtesting and calibration engine (`backtest.py`), pure what-if simulator (`what_if.py` and `POST /api/whatif`), 5 operator views in React, P90 uncertainty safety buffer, linear flow optimizer (`policies/optimizer.py`), and deterministic template summarizer with bounded LLM fallback (`summarize.py` and `GET /api/incidents/{id}/summary`).
3. **Demo:** Open `http://localhost:5174`: Navigate between Allocations (What-If drawer with quantity slider), Network View (topology status), Regional Demand, Incoming Supply, and Alert Center (click "Explain Incident" for plain-language summary with disclaimer badge).
4. **Evidence:** 177 Python tests + 11 Vitest tests passing; backtest summary across 2,000 ticks in `docs/results/backtest-summary.md`; what-if tested with zero DB/simulator writes (<50ms); mechanical gate `bash scripts/sprint_gate.sh 9` passed.
5. **Remaining:** Proceed automatically to Sprint 10 (security hardening, decision load testing, cold-start resilience audit, judging runbook).
