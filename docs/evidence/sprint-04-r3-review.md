# Sprint 4 R3 allocation-safety review

Date: 2026-11-20 | Review mode: separate Codex read-only session

## Scope and method

The reviewer traced candidate generation, ordered validation, reservation accounting, pending/in-flight handling, the operator API approval barrier, worker fresh-state validation, stable idempotency body handling, and simulator submission. The review did not modify files or perform simulator requests. Live allocation evidence is recorded separately in [sprint-04-overnight.md](sprint-04-overnight.md).

## Findings

- **P0:** none.
- **P1:** none.
- **P2:** the heuristic's advertised ETA used current tick plus route transit, but route ranking and projected arrival inventory still used `transit_ticks + 1`. This could make the proposed quantity use the next tick's forecast instead of the observed arrival tick.

## Resolution

Added `test_estimated_arrival_matches_simulator_dispatch_tick_semantics`, which asserts both ETA and projected inventory against the route's transit offset. It failed before the fix because projected inventory was one tick later (2,850 L vs 2,900 L on the fixture), then passed after route ranking and projected-inventory offsets were changed to `transit_ticks`. The prior live recommendation and approval record were not changed.

## Review disposition

No P0/P1 findings remain. The P2 finding was fixed and regression-tested. Final verification after the fix: 130 Python tests and 6 frontend tests passed; Ruff, format check, TypeScript, production Vite build, Docker Compose config validation, and `git diff --check` passed. The simulator live acceptance outcome is independently captured in the linked live evidence.
