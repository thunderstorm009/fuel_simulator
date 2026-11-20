# Sprint 04 Report: Constrained allocation, explanation, approval, and execution

**Path note:** The key paths below reflect the repository layout at Sprint 4 and have since moved into `backend/`, `intel/predictor/`, and `web/`; see `docs/DAY-1-UPDATE.md` for the current tree. The referenced implementation prompt is retained in the local-only development workspace.

Time window: 2026-11-19–2026-11-20 | Owner(s): project team | Branch: `overnight-sprints-4-7` | Status: **PASS — live acceptance verified**

## 1. Objective

Turn persisted stockout risk into a feasible, explainable recommendation that an operator can approve or reject, then have the worker submit the approved request safely to the official simulator.

## 2. What now exists

- A pure validator checks permanent idempotency first, then the simulator's ordered business rules. It accounts for same-cycle depot stock, dispatch, and station-capacity reservations. A key collision with a different body fails closed.
- An urgency-first heuristic selects station/fuel pairs at risk, considers route arrival, splits large quantities, tracks reservations, suppresses pending/in-transit duplicates, and validates each candidate.
- Recommendation generation runs after new forecasts, falls back to the heuristic on primary-policy failure or timeout, deduplicates through PROPOSED/APPROVED/SUBMITTED/IN_TRANSIT, expires old proposals, and stores a stable key with its exact request body.
- Explanations show demand and recent-trend drivers, arrival and delayed depot supply context, applied constraints, rejected alternatives, confidence, policy, snapshot status, and risk before/after a pure forecast rerun.
- API routes expose recommendation and decision history. Approve/reject routes require `X-Operator-Token`, validate a non-blank reject reason, and write decisions to PostgreSQL; API read paths still make no simulator calls.
- The frontend has a SIMULATED recommendations view, urgency ordering, explanation/risk details, in-memory token field, approval confirmation, rejection reason, and decision history.
- The worker executor re-reads simulator REST state, requires healthy non-stale data, revalidates immediately before submission, persists SUBMITTED before POST, retries ambiguous transport failures with the exact same body/key, and records simulator lifecycle status.

## 3. Decisions and rejected alternatives

- ADR-005, ADR-006, and ADR-009 are now ACCEPTED. See `docs/decisions.md`.
- Permanent simulator idempotency keys remain bound to one exact body. A different body with an existing key is failed locally rather than retried or recorded as a successful replay.
- The operator approval barrier remains mandatory. The project owner authorized exactly one live acceptance approval in the overnight execution prompt; the real operator API recorded it and the worker submitted the allocation.
- Live evidence showed that a newly submitted allocation departs on the current simulator tick. Recommendation ETA now reflects current-tick dispatch plus route transit; the correction is covered by a regression test and ADR-019.
- No new policy dependency or infrastructure was added.

## 4. Files created or modified (key paths and purpose)

- `core/validator.py`, `core/policies/`, `core/explain.py`, `core/models.py`: feasibility, allocation plans, and structured explanations.
- `worker/recommend_job.py`, `worker/executor.py`, `worker/main.py`, `worker/store.py`: recommendation persistence, fresh-state execution, retry safety, metrics, and lifecycle.
- `api/routes/recommendations.py`, `api/database.py`, `api/db.sql`, `api/main.py`: recommendation/decision API and local operator-decision writes.
- `frontend/src/api.ts`, `frontend/src/App.tsx`, `frontend/src/RecommendationsPage.tsx`, `frontend/src/style.css`: operator review and decision history.
- `tests/test_validator.py`, `tests/test_policy.py`, `tests/test_explain.py`, `tests/test_recommend_job.py`, `tests/test_recommendation_api.py`, `tests/test_executor.py`: Sprint 4 rules and failure paths.
- `docs/intelligence.md`, `docs/resilience.md`, `docs/architecture.md`, `docs/decisions.md`, local-only Sprint 4 prompt, `docs/PROGRESS.md`: design and acceptance record.

## 5. APIs added or changed

| Method | Path | Behavior |
|---|---|---|
| GET | `/api/recommendations` | Reads persisted recommendations from PostgreSQL. |
| GET | `/api/decisions` | Reads operator decision history from PostgreSQL. |
| POST | `/api/recommendations/{id}/approve` | Token-protected local approval intent; duplicate approval is idempotent. |
| POST | `/api/recommendations/{id}/reject` | Token-protected local rejection; requires a non-blank reason. |
| POST | simulator `/v1/allocations` | Worker-only; not exercised against the live simulator in this gate. |

## 6. Tests and verification

| Command or scenario | Expected | Actual result | Pass? |
|---|---|---|---|
| `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make test` | Complete suite | 130 Python and 6 frontend tests passed | PASS |
| `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make lint` | Ruff, format, frontend typecheck/build | Ruff passed; 61 files formatted; TypeScript and Vite build passed (500 modules) | PASS |
| `FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 docker compose config -q` | Valid Compose model | Exit 0 | PASS |
| `git diff --check` | No whitespace errors | Exit 0 | PASS |
| Docker Compose application build/start | API, worker and frontend images build and services start | Previously rebuilt; all eight project services were running; details in overnight runtime record | PASS |
| `make smoke` | Eight services healthy and endpoints reachable | Earlier Sprint 4 runtime check passed; simulator remained PAUSED; see `docs/evidence/sprint-04-runtime.md` | PASS |
| Recommendation browser inspection | Cards, token, history, SIMULATED label render | Six cards; ID/body mismatch regression UI displays exact body; frontend HTTP 200 on configured port | PASS |
| Ten local validator checks, including idempotency key mismatch | Each violation blocked in simulator order | Covered by validator tests; exact-key replay accepted and changed-body reuse blocked | PASS |
| Route disruption policy test | Use another depot/route or block candidate | Fixture rerouted Mirpur recommendation through the available Patiya route | PASS |
| Independent R3 safety review | No unresolved P0/P1 | Separate read-only review found no P0/P1; one P2 forecast offset mismatch was fixed with a failing-first regression test | PASS |
| Live approve → ARRIVED → exact same-key replay | One accepted allocation, same key returns existing ID | Approval HTTP 200; ID 1 ARRIVED at tick 137; one exact replay returned ID 1; one matching allocation at tick 138 | PASS |

Detailed original runtime output: `docs/evidence/sprint-04-runtime.md`; live overnight workflow output: `docs/evidence/sprint-04-overnight.md`; separate review and fix: `docs/evidence/sprint-04-r3-review.md`; mechanical gate output: `docs/evidence/sprint-04-gate.md`.

## 7. Evidence

- `docs/evidence/sprint-04-runtime.md`: test/build/smoke results, service health, live proposal counts, browser inspection, and independent review disposition.
- Existing test fixtures in `docs/sim-samples/` anchor local policy and validation behavior to the documented simulator contract.

## 8. Problems, root causes, fixes

- The resumed executor test file lacked postponed annotations, causing test collection to fail on an optional union annotation. Added the future import; tests collected and passed.
- Tests exposed that a matching key with a changed request body could be mistaken for a replay. Validator and executor now compare every allocation term before accepting an existing key; regression tests cover exact replay and mismatch.
- Code review found the recommendation job originally deduped only PROPOSED items. An approved or ambiguous SUBMITTED item could therefore receive another key while awaiting simulator visibility. Dedupe now covers PROPOSED, APPROVED, SUBMITTED, and IN_TRANSIT; tests cover the latter three states.
- API tests exposed whitespace-only rejection reasons being accepted. The API now strips and rejects blank reasons.
- The first browser check found a 5173/5174 CORS mismatch after the API restart. Recreated the local API with the 5174 origin; browser requests then succeeded.
- The first proposal's ETA overestimated simulator arrival by one tick. Live evidence reproduced the root cause (new allocation departure occurs at current tick); ETA, route ranking and projected arrival inventory now use the same transit offset. Regression coverage passes. The historical approval record remains immutable.

## 9. Not done or limitations

- The selected recommendation was generated under the prior ETA calculation, which was one tick conservative. Its approved record was preserved unchanged; ETA and related projection offsets for newly generated recommendations are corrected and regression-tested.
- Hosted GitHub CI has not been run in this environment.

## 10. Risks and next-sprint dependencies

- No Sprint 4 allocation acceptance gap remains. The simulator is PAUSED at tick 138 with one ARRIVED allocation. The R3 review found no P0/P1; its P2 finding was fixed. Continue to Sprint 5 after the final mechanical gate and commit/tag.

## 11. Acceptance checklist

- [x] Real recommendations generated from fresh simulator state and all simulator constraints revalidated.
- [x] Owner-authorized approval recorded through the token-protected operator API.
- [x] Worker submitted the exact approved body/key and simulator recorded allocation ID 1.
- [x] Allocation reached `ARRIVED` at tick 137; simulator remains PAUSED at tick 138.
- [x] One exact same-body/key replay returned allocation ID 1; readback found exactly one matching allocation.
- [x] Recommendation identity/body mismatch regression, health/freshness fixes and ETA regression covered by tests.
- [x] Independent R3 review found no P0/P1; its P2 finding was fixed and regression-tested.
- [x] Public mechanical gate passed after the final code changes.
- [x] Docs and progress updated; earlier sprint work preserved.

## 12. Five-minute update

1. **Problem solved:** Operators can inspect feasible simulated transfers, approve or reject with a token, and have the worker submit safely.
2. **What changed:** The live acceptance completed, recommendation identity is visible, stale health and snapshot freshness semantics were corrected, and ETA now matches observed current-tick departure.
3. **Live demo:** Open the frontend at port 5174, inspect system health and the allocation decision history; the simulator is paused at tick 138 and the accepted allocation is ARRIVED. Do not submit further live writes.
4. **Evidence:** [Sprint 4 live evidence](../evidence/sprint-04-overnight.md) records the exact approval response, tick progression, replay response, and duplicate check. The ETA regression test reproduced the old error then passed after the fix.
5. **Next step:** Complete the Sprint 4 review/gate, then exercise Sprint 5 faults and recovery.

## Gate decision

**PASS.** All Sprint 4 live acceptance criteria passed, the independent R3 P2 finding was fixed, and the public mechanical gate passed after final code changes. Evidence and verification outputs are recorded in the linked evidence files and overnight execution log.
