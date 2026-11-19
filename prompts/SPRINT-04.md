# Sprint 4 (hours 12-16): Constrained allocation, explanations, human approval, execution

SAME REPOSITORY. Starting state: tag sprint-3 (forecasts, risk API, risk UI). Extend. Do not rewrite forecasting or ingestion.

Skills: allocation-engine, simulator-integration, test-driven-development, code-review-strict, verification-before-completion.

## Objective
From risk to a safe, explained, human-approved allocation that reaches the simulator exactly once.

## Work packages

### WP4.1 Constraint validator
TASK: core/validator.py. validate(recommendation, snapshot, reservations) returns a list of Violation(code, message) mirroring the simulator checks in order: NOT_FOUND, ROUTE_MISMATCH, DEPOT_CLOSED, STATION_CLOSED, ROUTE_DISRUPTED, ROUTE_CAPACITY_EXCEEDED, INSUFFICIENT_INVENTORY, DISPATCH_CAPACITY_EXCEEDED, DESTINATION_CAPACITY_EXCEEDED. Account for reservations made earlier in the same planning cycle. Follow docs/sim-findings.md for dispatch-capacity counting.
TESTS: one per rule plus reservation accounting.

### WP4.2 Heuristic allocation policy
TASK: core/policies/base.py (Policy protocol: recommend(snapshot, forecasts)) and heuristic.py. For each station-fuel pair at risk (under 24h or high probability): need = target (70% of capacity or 24h of demand) minus projected inventory at arrival, capped by free station capacity. Candidates: route AVAILABLE, depot OPEN or CONSTRAINED, station OPEN; prefer a route that arrives before the stockout. Cap quantity by max_shipment, depot inventory and remaining dispatch capacity, tracking reservations within the cycle. Split large needs into several shipments. Serve the most urgent first. Cooldown: do not re-recommend what is already in transit. Run the validator before emitting.
TESTS: no risk gives none; one critical gives one recommendation; disrupted route gives an alternative; depot short gives split or another depot; reservations prevent overspend; deterministic output.

### WP4.3 Explanations and recommendation job
TASK: core/explain.py and worker/recommend_job.py. Explanation JSON: drivers (hours to stockout, demand multiplier, recent trend, delayed supply), constraints applied, risk before and after (re-run the forecast with the shipment added), alternatives with the reason each was rejected, confidence, policy used, data status. The job runs after forecasts: PolicyRunner runs the primary policy with a timeout and falls back to the heuristic (sets fallback_used and a metric), dedupes against open PROPOSED items, expires stale ones, and persists with a stored key rec-<uuid>.
TESTS: before risk is greater than or equal to after; fallback path; dedupe; expiry.

### WP4.4 Approval and executor
TASK: API POST /api/recommendations/{id}/approve and /reject (header X-Operator-Token from OPERATOR_TOKEN; reject requires a reason), GET /api/recommendations, GET /api/decisions. worker/executor.py loops every 1s over APPROVED items: do a fresh REST read and validate; if data is stale or validation fails set EXPIRED or FAILED with a reason; otherwise POST with the stored key. Map 201 and 200 to success; a 409 sets FAILED with its code; a timeout is retried with the SAME key. Track SUBMITTED, IN_TRANSIT, ARRIVED from allocation status.
TESTS with a fake SimClient: double approve is idempotent; stale data is never sent; timeout then success creates one allocation.

### WP4.5 Recommendations UI
TASK: Recommendations tab: cards sorted by urgency (fuel, station, quantity, route, ETA, policy, confidence, needs-review badge). Detail drawer: explanation sections, before and after risk bars, alternatives table. Approve (with confirm) and reject (reason required). Operator token field kept in memory only. Decision history table showing status progression. Toasts for results.

## Docs to update
docs/intelligence.md (policy and explanation), docs/architecture.md (recommendation lifecycle), docs/decisions.md (outbox-style executor, idempotency design), docs/PROGRESS.md.

## Acceptance checklist (real output required)
- [ ] approve in the UI creates an allocation visible in /v1/allocations with the same idempotency_key and it reaches ARRIVED
- [ ] repeating the POST with the same key returns the existing allocation
- [ ] a rule-breaking recommendation is blocked locally (each of the 10 rules tested)
- [ ] route_disruption causes a reroute through another depot or a clearly marked blocked state
- [ ] the metric for simulator-rejected submissions stays near zero
- [ ] an independent review (prompts/REVIEW-PROMPTS.md, allocation safety) found no unresolved P0

## Finish
Run prompts/SPRINT-GATE.md with N=4. Do not start Sprint 5.
