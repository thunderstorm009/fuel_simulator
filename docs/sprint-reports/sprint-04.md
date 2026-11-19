# Sprint 04 Report: Constrained allocation, explanation, approval, and execution

**Path note:** The key paths below reflect the repository layout at Sprint 4 and have since moved into `backend/`, `intel/predictor/`, and `web/`; see `docs/DAY-1-UPDATE.md` for the current tree. The referenced implementation prompt is retained in the local-only development workspace.

Time window: 2026-11-19 | Owner(s): project team | Branch and tag: `main`, last tag `sprint-0` | Status: **Blocked**

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
- The operator approval barrier remains mandatory. No live allocation was submitted during this session.
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
| `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make test` | Complete suite | 108 passed in 1.34s | PASS |
| `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make lint` | Ruff, format, frontend build | Ruff passed; 48 files formatted; Vite build passed | PASS |
| Vite production build | TypeScript and bundle complete | Main 249.06 kB (76.85 kB gzip); chart 426.04 kB (122.33 kB gzip) | PASS |
| `FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 docker compose config -q` | Valid Compose model | Exit 0 | PASS |
| `git diff --check` | No whitespace errors | Exit 0 | PASS |
| `docker compose build api worker` | Updated service images build | Both images built and started healthy | PASS |
| `docker compose build frontend` | Frontend image builds | Docker Hub metadata fetch failed twice with `DeadlineExceeded`; host build passed and copied `dist` was served in Nginx for browser inspection | BLOCKED |
| `SMOKE_SKIP_BUILD=1 FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 make smoke` | Eight services healthy | Passed; all eight healthy; simulator PAUSED at tick 114 | PASS |
| Recommendation browser inspection | Cards, token, history, SIMULATED label render | Six cards; password field; decision history; no browser errors | PASS |
| Ten local validator checks, including idempotency key mismatch | Each violation blocked in simulator order | Covered by validator tests; exact-key replay accepted and changed-body reuse blocked | PASS |
| Route disruption policy test | Use another depot/route or block candidate | Fixture rerouted Mirpur recommendation through the available Patiya route | PASS |
| Independent R3 safety review | No unresolved P0 | No P0/P1; live approve/arrival/replay remains an explicit verification gap | PASS with gap |
| Live approve → ARRIVED → exact same-key replay | One accepted allocation, same key returns existing ID | Not run; no operator approved a concrete live recommendation | BLOCKED |

Detailed command output and runtime observations: `docs/evidence/sprint-04-runtime.md`.

## 7. Evidence

- `docs/evidence/sprint-04-runtime.md`: test/build/smoke results, service health, live proposal counts, browser inspection, and independent review disposition.
- Existing test fixtures in `docs/sim-samples/` anchor local policy and validation behavior to the documented simulator contract.

## 8. Problems, root causes, fixes

- The resumed executor test file lacked postponed annotations, causing test collection to fail on an optional union annotation. Added the future import; tests collected and passed.
- Tests exposed that a matching key with a changed request body could be mistaken for a replay. Validator and executor now compare every allocation term before accepting an existing key; regression tests cover exact replay and mismatch.
- Code review found the recommendation job originally deduped only PROPOSED items. An approved or ambiguous SUBMITTED item could therefore receive another key while awaiting simulator visibility. Dedupe now covers PROPOSED, APPROVED, SUBMITTED, and IN_TRANSIT; tests cover the latter three states.
- API tests exposed whitespace-only rejection reasons being accepted. The API now strips and rejects blank reasons.
- The first browser check found a 5173/5174 CORS mismatch after the API restart. Recreated the local API with the 5174 origin; browser requests then succeeded.
- Docker Hub timed out resolving the frontend build base metadata twice. The local Vite production build and running Nginx browser check passed, but a fresh Compose frontend image build remains unverified.

## 9. Not done or limitations

- No live recommendation was approved or sent to the simulator. The required live allocation arrival and exact replay have not been verified.
- The six live proposals remain PROPOSED at simulator tick 114; the live simulator allocation list contains zero records and the decision list contains zero rows.
- `simulator_allocation_rejections_total` is zero because no submission was attempted; this does not demonstrate live accepted-write behavior.
- Frontend Compose image rebuild is blocked by external image metadata timeouts.

## 10. Risks and next-sprint dependencies

- Sprint 4 cannot be marked complete until an operator approves a concrete recommendation and the live simulator proves the allocation reaches ARRIVED and an exact same-key replay returns the existing allocation.
- A reviewer may then repeat the gate after Docker Hub metadata is reachable or accept the verified host build plus Nginx runtime evidence for frontend packaging.
- Do not begin Sprint 5 until the Sprint 4 gate is passed.

## 11. Acceptance checklist

- [ ] Live UI approval creates an allocation with the stored key/body and reaches ARRIVED — **BLOCKED: operator approval not performed**
- [ ] Repeating the exact simulator POST returns the existing allocation — **BLOCKED: dependent on approved live allocation**
- [x] Ten local validation rules are covered; invalid requests are blocked before POST
- [x] Route disruption fixture reroutes through an available alternative
- [x] Simulator rejection metric remains zero; no writes were attempted, so this is not an accepted-write result
- [x] Independent R3 review found no unresolved P0/P1
- [x] Tests, lint, host frontend build, Compose config, smoke, browser check, and `git diff --check` recorded
- [x] Docs and `docs/PROGRESS.md` updated; earlier sprint changes and simulator samples preserved
- [ ] Gate passed — **No. Two live simulator acceptance items remain blocked.**

## 12. Five-minute update

1. **Problem solved:** Operators can now review grounded allocation proposals and record approval/rejection; only the worker may submit approved requests.
2. **What we built:** Ordered simulator validation, reservation-aware heuristic, forecast-based explanations, token-protected decisions, safe stable-key executor, and a SIMULATED review UI.
3. **Live demonstration:** Open the Recommendations tab at the configured frontend port; inspect the six persisted proposal cards and decision history. The simulator remains paused at tick 114. Do not press Approve until the operator explicitly selects a proposal.
4. **Evidence:** 108 tests passed; lint/build, Compose config, smoke, API/worker health, browser UI, and independent safety review passed. Full outputs are recorded in the evidence file.
5. **Remaining gap and next step:** An operator must approve a concrete proposal so the simulator can prove ARRIVED and exact-key replay. Docker Hub also timed out on the frontend image base metadata. Sprint 5 has not started.

## Gate decision

**Blocked.** Independent R3 review found no P0/P1 allocation-safety defect. Local verification passed. Live approval, arrival, and replay need an explicit operator decision; frontend Docker image rebuild also remains blocked by the Docker Hub metadata timeout.
