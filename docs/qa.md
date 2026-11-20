# Judge questions and answers

1. **Why start with a heuristic?** It is deterministic, explainable, dependency-light, and constrained by the simulator validator. Optimizer comparisons have not been measured.
2. **How is demand forecast?** Shared pure code combines profile-based expected demand, recent observations, event multipliers, and inventory projections; seeded Monte Carlo produces risk intervals.
3. **Does a forecast decide or submit?** No. Forecasts inform recommendations; only an operator can approve, and the worker validates again before submission.
4. **What if the simulator returns stale data?** The worker preserves the stale marker, lowers confidence, and the executor blocks submission.
5. **What if the simulator is unavailable?** Bounded retries and a circuit breaker protect the worker; the last accepted snapshot remains available with degraded freshness.
6. **Why is SSE not the source of truth?** The simulator stream has no replay guarantee; it only signals that REST state should be fetched again.
7. **Can depot scheduled supply count as station stock?** No. Station projection uses on-hand stock and verified station allocation arrivals.
8. **How are duplicate allocations prevented?** A permanent idempotency key is stored with the exact request body and reused only for that identical body.
9. **What if a POST times out?** The worker retains submitted state and retries with the same key and exact body after a fresh read.
10. **Can a key be reused after cancel?** No. Keys are permanent and a changed body fails closed.
11. **Why a separate predictor?** It isolates forecast service failures and allows a bounded fallback demonstration without moving feasibility decisions out of shared code.
12. **What does fallback mean?** A profile-only baseline with confidence at most 0.4, `needs_review`, a metric, and an incident.
13. **What is tested live?** Historical Sprints 1–3 include live evidence. Current Sprint 4 approval-to-arrival/replay and Sprint 5–7 live acceptance are still open.
14. **What are the main limitations?** Local Compose deployment, simulator assumptions, unmeasured comparative performance, and no current live acceptance for an operator-approved allocation.
15. **What would be next?** Obtain explicit operator authorization for one concrete recommendation, run the live idempotency/arrival gate, then run isolated resilience, scenario, load, and release rehearsals.
