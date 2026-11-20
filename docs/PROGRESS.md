# Project progress

Last updated: 2026-11-20. Resume point for the shared repository worktree.

## Current status

- Repository: `main`, base commit `b1fc38b` (`docs: organize project and publish day 1 engineering update`). Existing Sprint 5 edits were preserved and extended; no reset, commit, or tag was performed.
- Sprint 1–3: historical reports record local gates as passed.
- Sprint 4: code and local checks exist. Docker stack is now running with all eight services healthy. Six current proposals were generated at simulator tick 134; one fully validated candidate is presented in `docs/evidence/sprint-04-live-workflow.md`. Awaiting explicit human approval. No approval or simulator allocation POST was made; arrival and exact same-key/body replay remain **OPEN**.
- Sprint 4 reinspection fixes: recommendation `1cb05b67-3440-45e5-a6d8-398482678d8c` is correctly stored as 6,000 L with its matching request body and key; ~1,543.55 L belongs to sibling ID `dab6db72-4f94-4b09-a167-d1dea8c1f2fc` and a different key/body. The frontend omitted IDs and rounded liters, creating the ambiguity. UI now exposes ID, key, full precision and exact request body; UI and API both fail closed on mismatched stored fields/body. Health distinguishes worker availability from decision-pipeline freshness. Same-tick snapshot updates replace payload and simulator time together with freshness metadata. Regression tests and runtime checks passed; tick remains 134 PAUSED, with no decision, allocation, replay, reset or advancement. Sprint 4 live approval/arrival/replay remains OPEN.
- Sprint 5: predictor endpoint/fallback, health view, metric instrumentation, dashboard/alert provisioning, fault demo, and resilience tests are present. Local suite/lint/build pass. Live fault/recovery and runtime acceptance are **NOT-RUN**.
- Sprint 6: read-only k6 workload, summary renderer, Docker stats collector, README quickstart checker, and CI changes are present. Scenario comparison runner, measured load runs, knee analysis, and hosted CI result are **OPEN**.
- Sprint 7: guarded cold-start and fault-chaos scripts, final demo notes, Q&A, known-issues, AI-use and assumptions docs are present. Cold start, chaos round, demo repetitions, docs audit, and release tags are **OPEN**.

## Verification run in this session

- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make test`: **124 Python tests passed**; **3 frontend tests passed** after the SSE timeout regression fix.
- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make lint`: Ruff passed, 59 files formatted, TypeScript check passed, Vite production build passed (500 modules; main bundle 251.09 kB, trajectory chunk 426.04 kB).
- `python3 -m compileall -q backend intel scripts tests`: passed.
- `bash -n scripts/fault_demo.sh scripts/collect_stats.sh scripts/cold_start_check.sh scripts/check_readme.sh`: passed.
- `docker compose config -q` and `git diff --check`: passed.
- The first focused half-open-breaker test failed as intended: concurrent recovery request did not raise `breaker_open`. A single-probe guard was added; final full suite passed after the fix. Detailed local evidence: `docs/evidence/sprint-05-runtime.md`.
- Docker Compose startup/build passed on 2026-11-20; all eight services reported healthy, frontend HTTP 200, simulator/API reads succeeded, and Prometheus API/worker/predictor targets were up. Grafana API search returned 401 without credentials, so dashboard contents are unverified. Sprint 4 live proposal validation passed locally; approval/submission/arrival/replay await operator authorization.
- Live SSE check found a 3s stream timeout conflicting with the simulator's 15s keepalive. Worker rebuilt with separate 20s SSE timeout. Over 22s there were no disconnect logs and reconnect counter stayed at one. Regression test added; final Python suite 124 passed.
- Recommendation identity/health/freshness correction: final `make test` passed **129 Python + 6 frontend tests**; `make lint` passed Ruff, formatting (61 files), TypeScript and Vite build (500 modules); `docker compose config -q` and `git diff --check` passed. API, worker, and frontend images rebuilt; all eight Compose services healthy and frontend HTTP 200 on 5174. Fresh worker-side simulator read at tick 134 PAUSED returned all ten allocation checks true and `violations=[]`; API snapshot now also says PAUSED, data fresh/non-stale. Health reports worker/simulator/predictor healthy and decision engine/aggregate degraded. Candidate and sibling remain PROPOSED, decisions and allocations remain empty. Evidence: `docs/evidence/sprint-04-live-workflow.md`.
- Sprint 5 fault injections, predictor/worker stop-recovery, cold start, and CI-hosted execution remain **NOT-RUN**.
- `k6` is not installed (`k6-installed=False`); load runs and numeric performance claims are **NOT-RUN**.

## Exact remaining work and blockers

1. **Sprint 4 live operator gate:** candidate `1cb05b67-3440-45e5-a6d8-398482678d8c` is ready for review at `http://localhost:5174`. An operator must explicitly approve this candidate (or choose another fresh candidate) in the UI. Then verify worker submission, simulator `ARRIVED`, and exact stored body/key replay. Do not progress to Sprint 5 until the gate passes.
2. **Sprint 5 live gate:** restore Docker, confirm the simulator is in an appropriate demo state, then run the five fault scenes, malformed-data path, predictor stop/recovery, worker stop/data-age, Grafana movement, and recovery checks. Record real outputs in `docs/evidence/`.
3. **Sprint 6:** implement the scenario runner using a safe isolated simulation mode that does not bypass the operator approval requirement; run deterministic baseline/naive/heuristic scenarios only with explicit authorization for their simulator state changes. Install/run k6 for normal, latency, and predictor-stop workloads and collect Docker stats. Trigger/inspect GitHub Actions; add docs link/markdown checks and coverage only when tool setup is verified.
4. **Sprint 7:** with disposable local data explicitly selected, run the volume-deleting cold-start check; rehearse the demo three times without edits; run the reversible chaos round; perform an independent docs audit; capture evidence; decide whether the sprint/release tags can be created.

## Workspace notes

- Preserve the uncommitted Sprint 5 work from the checkpoint and all user changes. `.env`, `.agents/`, `.local/`, personal instructions, and local prompts remain local and must not be staged.
- `.env` was not read or changed in this session. The prior checkpoint notes an existing `PREDICTOR_URL` override mismatch; verify current local configuration without exposing its value before restarting Compose.
- The simulator scenario runner and its measurements have not been implemented or invented. Sprint 6's prompt specifies simulation-only auto-approval, which must be reconciled with the stronger explicit human approval rule before any allocation-writing scenario is run.

## Sprint log

| Sprint | Status | Report |
|---|---|---|
| 1 | Passed historically with environment notes | [sprint-01.md](sprint-reports/sprint-01.md) |
| 2 | Passed historically with runtime evidence | [sprint-02.md](sprint-reports/sprint-02.md) |
| 3 | Passed historically with revised simulator semantics | [sprint-03.md](sprint-reports/sprint-03.md) |
| 4 | Live approval/arrival/replay open | [sprint-04.md](sprint-reports/sprint-04.md) |
| 5 | Local implementation verified; live gate open | [sprint-05.md](sprint-reports/sprint-05.md) |
| 6 | Tooling partial; scenario and performance evidence open | [sprint-06.md](sprint-reports/sprint-06.md) |
| 7 | Readiness artifacts partial; runtime/release gate open | [sprint-07.md](sprint-reports/sprint-07.md) |

## Five-minute status update

1. **Problem:** Operators need current simulated stock, shortage risk, explained feasible transfers, explicit approval, safe submission, and recovery visibility.
2. **What changed:** The existing Sprint 5 work was preserved; resilience cases and a predictor breaker regression were added, current docs aligned, and load/rehearsal tooling and final readiness docs prepared.
3. **Demo:** Current UI/Compose demo is unavailable because Docker is not running. Once restored, show health/data age, risk, recommendation explanation without approval, then an isolated fault/fallback demonstration.
4. **Evidence:** 129 Python tests, 6 frontend tests, lint/typecheck/build, Compose config, and whitespace checks passed. Current Compose services are healthy and a fresh recommendation has live constraint evidence; the live allocation gate is still pending approval.
5. **Remaining:** The Sprint 4 live write gate needs explicit operator approval. Docker and k6 runtime checks, scenario comparison, CI, demo rehearsal, and release review remain.
