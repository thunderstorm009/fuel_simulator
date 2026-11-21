# Operator guide

All values and actions are **SIMULATED**.

## Start and inspect

1. Configure `.env` from `.env.example`; keep the operator token private.
2. Start with `make up`. Check the component health banner and data age before using recommendations.
3. Review Overview, Network, Stockout Risk, Regional Demand, Incoming Supply, Alert Center, and System Health. A stale or degraded snapshot lowers confidence and blocks executor submission.

## Operator views

- **Overview:** Unified operator HUD with summary metrics, active crisis events, fleet dispatch tracking, and speed warning indicator.
- **Network View:** Topology schematic displaying real-time status of all depots, routes, and stations (OPEN, CONSTRAINED, OUTAGE, AVAILABLE, DISRUPTED) and in-transit trucks.
- **Stockout Risk:** Color-coded risk matrix across stations and fuel types with interactive 24-hour projected inventory trajectories and P10/P90 confidence bounds.
- **Regional Demand:** Rollup of demand versus served liters and service level per geographic region with active demand multipliers.
- **Incoming Supply:** Forward timeline of scheduled and delayed bulk supply arrivals at depots alongside active in-transit delivery allocations with tick ETAs.
- **Alert Center:** Unified audit log of detected operational anomalies (demand surges, inventory drops, bottlenecks, calibration drift) with one-click AI-generated plain-language incident explanations.
- **Evaluation & Offline Benchmarks:** Policy benchmark scorecard (do-nothing vs. naive vs. heuristic) and backtesting accuracy metrics (MAPE, bias, interval coverage).

## Review and simulate a recommendation

Open Allocations and inspect the source/destination, route, fuel, quantity, ETA, constraints, before/after risk, alternatives, confidence, and review flag.

- **What-If Simulation:** Operators can simulate candidate allocations before approving. Use the quantity slider and route selectors to project immediate impact on hours-to-stockout and depot net cover without modifying stored proposals or calling the simulator.
- **Review Confirmation:** Any recommendation tagged `needs_review` (confidence < 0.65 or fallback prediction) requires an explicit operator acknowledgment checkbox before the approval button becomes active.
- Enter the operator token only in the in-memory UI field. Approve only a concrete recommendation after reviewing it; the API records intent and the worker performs a fresh non-stale simulator read and full revalidation before its simulator POST. Reject with a reason when declining.

Never use a fault demo, scenario tool, or script to bypass approval. Do not approve merely to make a demo look complete. A same-key retry must use the persisted exact request body.

## Stop and recover

`make down` preserves local data volumes. Consult [the runbook](runbook.md) for component failures. `docker compose down -v` deletes PostgreSQL and Grafana state; it is intended only for a confirmed disposable cold-start check.
