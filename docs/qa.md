# Judge questions and answers

1. **Why start with a heuristic instead of a full MIP/RL optimizer?**
   The heuristic is fast (under 5 ms), deterministic, fully explainable, and constraint-guaranteed. In real-world emergency fuel dispatch, operators require instant explanations with explicit constraint checks rather than black-box recommendations.

2. **How does demand forecasting work?**
   A shared pure domain pipeline (`core.forecast`, `core.risk`) combines profile-based diurnal curves (`core.world`), historical EWMA ratio calibration (alpha=0.3 clamped to [0.5, 2.0]), and event multipliers. Vectorized Monte Carlo (300 seeded paths) projects trajectory intervals (P10, P50, P90) and 24-hour stockout probability.

3. **Does the forecasting engine make allocation decisions or submit to the simulator?**
   No. Forecast and risk functions are strictly pure functions with no I/O (AGENTS.md rule 4). They produce recommendations with human explanations. An operator must review and approve; the worker executor revalidates constraints before the single `POST /v1/allocations`.

4. **What happens if the simulator returns stale data?**
   The worker detects `X-Simulator-Stale: true` (or snapshot age > 30s), flags the state as `stale: true`, downgrades data status to `DEGRADED`, drops confidence, blocks allocation submission, and displays a prominent warning badge in the operator UI.

5. **What happens if the simulator is temporarily unavailable?**
   The typed `SimClient` uses bounded retries with jitter and a circuit breaker (threshold 5 failures, 10s cooldown). The API continues serving the last valid snapshot from PostgreSQL. Never retry 409 or 422 errors (AGENTS.md rule 3).

6. **Why is SSE not the single source of truth?**
   The simulator SSE stream has no message replay or resume guarantee upon disconnect. Therefore, SSE events are treated strictly as advisory hints to refetch authoritative state via REST endpoints (AGENTS.md rule 1).

7. **Can scheduled or in-transit depot replenishments count as station stock?**
   No. Depot shipments do not equal station inventory. Station inventory projections count strictly on-hand station stock and verified station-bound allocations at their expected arrival ticks (AGENTS.md rule 7).

8. **How are duplicate allocations prevented?**
   Every recommendation generates a unique, permanent idempotency key stored alongside the exact request body. This key is placed in the `POST /v1/allocations` JSON body. A replay with the same key returns the existing allocation without creating duplicates (AGENTS.md rule 5).

9. **What happens if an allocation submission times out?**
   The worker preserves the allocation in SUBMITTED state with its permanent key. Upon next refresh, it checks if the simulator created the allocation or retries with the exact same body and key.

10. **Can an idempotency key be reused after cancellation or rejection?**
    No. Idempotency keys are permanently tied to their original payload. Reusing a key with a different body is rejected by the simulator with a 409 Conflict.

11. **Why is the predictor an independent microservice?**
    Separating the predictor (`intel/predictor` on port 8103) allows isolated scaling, independent deployment, and controlled failure injection. When the predictor is stopped, the worker smoothly falls back to its local baseline model without crashing.

12. **What does baseline fallback mean in practice?**
    When the predictor fails or times out (1.5s timeout, breaker threshold 5), the worker computes a local diurnal baseline forecast, caps confidence at 0.4, marks `needs_review: true`, and emits an observability metric and incident.

13. **How is determinism proven across scenarios?**
    `scripts/scenario_runner.py` evaluates all 4 disruption scenarios (`baseline`, `spike`, `route`, `combined`) across 3 policies (`none`, `naive`, `heuristic`) twice (24 total runs). The delta in service level and stockout count between Run 1 and Run 2 is 0.0000 across all pairs (`docs/results/scenario-summary.md`).

14. **What load can the platform handle?**
    Under k6 load testing with 10, 50, and 100 virtual users over 3m35s, the platform sustained ~320 requests/second with 0.0% error rate across 205,728 total requests. A concurrency knee appears at 100 VUs where p95 latency crosses 500 ms (`docs/loadtest.md`).

15. **What are the next production hardening steps?**
    Container orchestration (Kubernetes manifests), persistent message queuing for asynchronous events, automated SSL termination, and integrating an optional mixed-integer linear programming (MILP) optimizer alongside the heuristic policy.

16. **How does the pure anomaly detection engine work?**
    `backend/shared/core/detect.py` implements 5 pure algorithmic detectors (demand anomalies >1.3x baseline for 3 ticks, regional surge clusters, unexplained inventory drops, depot dispatch bottlenecks, emerging corridor blockades) with zero database or network I/O. Incidents are deduplicated by stable keys, logged in PostgreSQL, surfaced in the Alert Center, and automatically resolved when normal operational envelopes resume.

17. **How does the interactive What-If simulation tool ensure safety?**
    `POST /api/whatif` executes purely in-memory on the latest cached snapshot via `core.what_if.simulate_what_if`. It re-evaluates all 5 physical constraints using `core.validator`, models projected inventory trajectories with and without the candidate dispatch, and returns hours-to-stockout deltas in <50ms unloaded (~834ms under 100 VU load) without writing to PostgreSQL or the simulator. Changing sliders in the UI does NOT alter stored proposals or reuse idempotency keys.

18. **How does automated rollback work in production?**
    `scripts/deploy.sh <tag>` records the previous active tag, sets the proposed image tag, and executes an immediate health gate (`scripts/smoke.sh`). If any container crashes or health checks fail, `scripts/rollback.sh` is automatically invoked, restoring the previous verified release tag and bringing the stack back to healthy state with zero data corruption.

19. **What are the platform's physical failure boundaries?**
    From the simulator demand profiles (`core/world.py`), total network baseline demand across all 4 stations is 91,400 L/day (about 952 L per 15-minute tick average, or 508 L per 8-minute tick). Depots provide 23,000 L/tick combined dispatch capacity (Gazipur 12,000 + Patiya 11,000 L/tick), which is >24x average demand—meaning depot dispatch capacity is not the binding constraint. The real physical boundaries are depot inventory plus scheduled bulk supply arrivals (initial depot reserves 252,000 L = ~2.76 days of baseline cover), route shipment caps (5,000–7,000 L/truck), station tank ullage, and corridor transit ticks (1–4 ticks). When supply shortfalls or severe surges strike, the heuristic policy degrades gracefully by entering Pass 1 emergency triage (guaranteeing 12h survival fuel first) and tagging partial allocations with `is_partial=True` and unserved reason codes.

20. **What safeguards govern generative AI incident explanations?**
    `backend/shared/core/summarize.py` uses a deterministic `TemplateSummarizer` by default, with an optional `LLMSummarizer` wrapper configured with a strict 3-second timeout and zero logging of secrets. Any error, timeout, or missing API key falls back instantly to the template. The LLM has zero authority to approve allocations or determine feasibility, and all outputs carry a mandatory operator disclaimer: `"AI-generated summary of simulated data"`.
