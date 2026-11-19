---
name: allocation-engine
description: Use when writing or reviewing allocation policies, the constraint validator, explanations, recommendation lifecycle or the executor that submits to the simulator.
---
# Allocation engine
- The validator mirrors the simulator checks in order (see simulator-integration). Hard constraints are never relaxed silently.
- Heuristic: rank by urgency, target about 70% of capacity or 24h of demand, prefer a route that arrives before stockout, cap by max_shipment, depot inventory and remaining dispatch capacity (include pending and in-flight), track reservations inside the planning cycle, split large needs, skip what is already in transit.
- Every recommendation carries an explanation: drivers, constraints, risk before and after, alternatives rejected with reasons, confidence, policy used, data status, timestamp.
- Lifecycle: PROPOSED, APPROVED, SUBMITTED, IN_TRANSIT, ARRIVED, or REJECTED, EXPIRED, FAILED.
- Only the executor submits, only after approval, after a fresh REST read and re-validation, never on stale data. Key: rec-<uuid>, created once, stored, reused only for the identical body.
- Review attempt list: oversubscribed depot or route, duplicate submit on retry or double click, stale submit, key reuse with a different body, approval bypass.
- An LLM may explain results; it never decides feasibility.
