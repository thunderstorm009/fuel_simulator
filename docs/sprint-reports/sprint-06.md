# Sprint 06 Report: Load evidence, CI, and documentation

Time window: 2026-11-20 | Owner: Codex | Branch: `main` | Status: **Partial; acceptance open**

## 1. Objective

Provide deterministic scenario evidence, measured API load results, stronger CI, and implementation-aligned operating documentation.

## 2. What now exists

- Added a read-only k6 workload for `/api/risks`, `/api/state`, and `/api/recommendations`, a JSON summary renderer, and Docker stats CSV collector.
- Added a README quickstart checker and expanded CI to use exact action release tags, dependency caching, Compose startup/health check, and failure log artifact upload.
- Updated architecture, API, observability, resilience, CI, README, and limitations documentation.

## 3. Decisions and constraints

- Load requests are read-only. No recommendation generation endpoint was added because it does not currently exist and no API endpoint should call the simulator.
- Did not implement the prompt's auto-approving simulator scenario loop. It conflicts with the user's instruction that allocations must not be submitted without explicit human authorization. A safe isolated-mode contract needs an explicit decision before implementing/running it.
- No new dependency was added for load testing; k6 remains an external runner.

## 4. Key files

`loadtest/k6.js`, `scripts/loadtest_report.py`, `scripts/collect_stats.sh`, `scripts/check_readme.sh`, `.github/workflows/ci.yml`, `docs/loadtest.md`, `docs/testing-and-ci.md`, and `README.md`.

## 5. APIs

No API behavior changed in Sprint 6. The load script reads existing GET routes only.

## 6. Verification

| Check | Actual result | Status |
|---|---|---|
| Python/frontend tests and lint/build | 123 Python, 3 frontend; make lint passes | PASS |
| Compose config and whitespace | Exit 0 | PASS |
| k6 availability | `k6-installed=False` | NOT-RUN |
| Normal/latency/predictor load runs | Docker/API unavailable; no numeric output | NOT-RUN |
| Hosted GitHub Actions | Not triggered | NOT-RUN |
| Scenario runner and repeated policy comparison | Not implemented; approval conflict documented | BLOCKED |
| Clean-clone README check | Not run; depends on Docker and available service images | NOT-RUN |

## 7. Evidence

`docs/loadtest.md` explicitly records that there are no measured values. No performance claims are made.

## 8. Problems / limitations

Docker is unavailable and k6 is absent. The simulator scenario prompt's automatic approval mode requires reconciliation with the explicit approval rule before it can safely produce allocation outcomes.

## 9. Next dependency

Obtain an isolated simulator environment and a human-approved scenario execution design. Install/run k6 against a healthy stack and retain raw summaries and Docker stats. Trigger CI in GitHub.

## 10. Acceptance checklist

- [ ] Heuristic beats do-nothing and naive with deterministic repeated evidence — NOT-RUN / scenario runner absent.
- [ ] Three load runs and knee analysis — NOT-RUN.
- [ ] README quickstart independently verified on clean clone — NOT-RUN.
- [ ] Hosted CI green — NOT-RUN.
- [ ] Docs audit has no P0/P1 — NOT-RUN.

## 11. Five-minute update

1. Problem: make performance, repeatability, and run instructions measurable.
2. Change: read-only k6 workload, report renderer, resource capture, CI startup checks, and docs alignment.
3. Demo: no load chart is available; show the workload definition and state that measurements are pending.
4. Evidence: local suite and build pass; runtime unavailable; no invented numbers.
5. Gap: scenario comparison, three load profiles, hosted CI, and clean clone remain.

## Gate decision

**Not passed.** Tooling is partial; required scenario and measured performance evidence remain open.
