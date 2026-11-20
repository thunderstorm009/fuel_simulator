# Project progress

Last updated: 2026-11-20. Resume point for the shared repository worktree.

## Current status

- Branch: `overnight-sprints-4-7`, based on `b1fc38b`. The pre-run tree is preserved in commit `ee830cc`; Sprint 4 is tagged at `3fe2353` as `sprint-4`. No pushes have been made.
- Sprint 1–3: historical reports record those sprint gates as passed. Their implementation remains preserved.
- Sprint 4: **PASS**. One project-owner-authorized recommendation was approved at tick 134, submitted by the worker, reached `ARRIVED` at tick 137, and one exact body/key replay returned the same allocation ID. The simulator is PAUSED at tick 138; only one allocation and one decision exist. Details: [Sprint 4 live evidence](evidence/sprint-04-overnight.md). The measured ETA discrepancy and the review's P2 projection-offset finding are corrected and regression-tested. Independent R3 review found no P0/P1; public and local mechanical gates passed after final changes. Tag: `sprint-4`.
- Sprint 5: API/worker/predictor metrics, health aggregation, remote predictor with baseline fallback, token-protected chaos switch, Grafana/Prometheus provisioning, and fault demo are present. Local unit/integration tests and builds passed earlier; live fault/recovery evidence is still required.
- Sprint 6: k6 workload, stats collector, report renderer, docs/quickstart checks and CI changes are present. Deterministic scenario runner, three measured load runs, and local CI validation remain.
- Sprint 7: cold-start and chaos scripts, final demo notes, Q&A, assumptions, AI-use and known-issues docs are present. Cold-start, chaos round, docs audit, final documentation audit and readiness report remain.
- Public local-instruction check: private development instructions and sprint prompts are intentionally absent from clean clones. `scripts/sprint_gate_public.sh` reports absent local-only inputs as SKIP. The legacy `scripts/sprint_gate.sh` path is ignored by existing repository rules and will not be force-added or made trackable by changing those rules.

## Verification in this work package

- Focused ETA regression initially failed on the old calculation, then passed after correcting the estimate to current simulator tick plus route transit.
- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make lint`: Ruff and formatting passed; TypeScript typecheck and Vite production build passed.
- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make test`: 130 Python tests and 6 frontend tests passed.
- `FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 docker compose config -q`: passed.
- `git diff --check`: passed.
- One replay through worker `SimClient` returned allocation ID 1, `ARRIVED`, same key and `stale=false`; read-only final verification found one matching allocation, one decision, and PAUSED tick 138.

## Current work package and exact next action

Sprint 5 first task: inspect its complete requirements/report/evidence and current Compose health, then run the latency fault scene with recovery while keeping simulator PAUSED and preserving allocation ID 1. Do not add another live operator-app approval or simulator allocation.

## Workspace constraints

Do not edit `.env`, stage ignored local instructions, expose secrets, reset state outside authorized scenario/cold-start runs, or push. Preserve current Compose volumes and simulator state except for user-authorized simulation scenarios after evidence and commits. Keep public documentation self-sufficient without private development files.

## Sprint log

| Sprint | Status | Report |
|---|---|---|
| 1 | Passed historically; local verification only | [sprint-01.md](sprint-reports/sprint-01.md) |
| 2 | Passed historically with runtime evidence | [sprint-02.md](sprint-reports/sprint-02.md) |
| 3 | Passed historically with revised simulator semantics | [sprint-03.md](sprint-reports/sprint-03.md) |
| 4 | PASS; live workflow, R3 review, and mechanical gates passed; tag `sprint-4` | [sprint-04.md](sprint-reports/sprint-04.md) |
| 5 | Implementation present; runtime fault gate open | [sprint-05.md](sprint-reports/sprint-05.md) |
| 6 | Tooling partial; scenarios and measurements open | [sprint-06.md](sprint-reports/sprint-06.md) |
| 7 | Readiness artifacts partial; final verification open | [sprint-07.md](sprint-reports/sprint-07.md) |

## Five-minute status update

1. **Problem:** Operators need current simulated fuel state, shortage risk, feasible explained allocations, mandatory human approval, and recovery visibility.
2. **Change:** Sprint 4's single authorized live workflow is complete. It exposed and corrected a one-tick recommendation ETA error; approval identity/body, health, and snapshot freshness safeguards are in place.
3. **Demo:** Open the frontend at `http://localhost:5174`; inspect health, inventories, risks and the allocation decision history. The simulator is PAUSED at tick 138 with the accepted 6,000 L allocation ARRIVED. Do not issue another live allocation.
4. **Evidence:** `docs/evidence/sprint-04-overnight.md` contains the owner authorization record, request body, constraint checks, tick-by-tick progression, exact replay and duplicate check. The current local test run passed 130 Python and 6 frontend tests, plus lint/build and Compose config.
5. **Remaining:** Commit/tag Sprint 4 and proceed to Sprint 5 live fault/recovery tests, then Sprint 6 load proof and Sprint 7 freeze checks. Hosted GitHub CI remains unavailable here.
