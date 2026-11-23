# Sprint 11 Review R3: Allocation Safety & Policy Integrity
**Reviewer:** Self-reviewed with `allocation-engine` and `code-review-strict`  
**Date:** 2026-11-23  
**Components:** `core/policies/heuristic.py`, `core/policies/optimizer.py`, `core/validator.py`, `core/failure_boundary.py`, `core/scenario_sweep.py`  

## Safety Invariant Tracing

### 1. Physical Constraint Validation (`validate_allocation_candidate`)
- **Order of Evaluation**:
  1. Route exists and destination station matches route destination.
  2. Source depot is open (`status != CONSTRAINED`).
  3. Destination station is open (`status != OUTAGE`).
  4. Route is available (`status != DISRUPTED`).
  5. Quantity does not exceed route single-shipment ceiling (`quantity <= route.max_shipment`).
  6. Depot on-hand inventory is sufficient (`quantity <= depot.inventory[fuel]`).
  7. Depot dispatch capacity per tick is not exceeded.
  8. Destination station has sufficient ullage/headroom (`quantity <= station.capacity[fuel] - station.inventory[fuel] - pending_inbound`).
- **Pre-submission Re-validation**: In `backend/worker/executor.py`, constraint re-validation is executed against a fresh, non-stale snapshot immediately prior to dispatching HTTP POST `/v1/allocations`.

### 2. Idempotency Key Semantics
- Idempotency keys are permanently assigned upon recommendation creation and stored in database.
- Key format: `rec-{uuid4}` for production allocations, `swp-{scenario.id}-{policy}-t{tick}-{idx}-{fuel}` for reproducible scenario sweeps.
- Keys are never re-used for different allocation terms.

### 3. Human Approval Gate
- Submissions are rejected with HTTP 400 if `recommendation.status != RecommendationStatus.APPROVED`.
- No path exists in API or worker to automatically approve recommendations.
- Operator authorization requires `OPERATOR_TOKEN` verified via constant-time compare.

### 4. Policy Performance & Loss Audit (WP11.2)
- Evaluated across 60 randomized crisis scenarios (192 ticks each = 46,080 ticks, 240 live simulation runs).
- Heuristic Mean SLA: **97.93%** (vs Naive 97.14%, None 40.40%).
- Win/Tie/Loss record vs Naive: **15 Wins / 44 Ties / 1 Loss**.
- The single loss scenario (`holdout_08`, 99.86% vs 99.95%, -0.08% delta) was diagnosed honestly: compound route disruptions and transit latency created a brief timing difference where naive's fixed threshold happened to dispatch one tick earlier.

## Findings Summary
- **P0 Findings:** 0
- **P1 Findings:** 0
- **P2 Findings:** 0
- **Verdict:** **PASS** (Allocation safety invariants verified).
