# Scenario comparison & determinism proof

Generated: 2026-11-21T06:09:09.138322+00:00

## Policy performance across scenarios (Run 1)

| Scenario | Policy | Service Level | Served (L) | Unmet (L) | Allocs (L) | Failures | Stockouts |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline | none | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| baseline | naive | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| baseline | heuristic | 100.0% | 12860 | 0 | 15238 | 0 | 0 |
| combined | none | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| combined | naive | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| combined | heuristic | 100.0% | 12860 | 0 | 15238 | 0 | 0 |
| crisis_combined | none | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| crisis_combined | naive | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| crisis_combined | heuristic | 100.0% | 12860 | 0 | 15238 | 0 | 0 |
| depot_constraint | none | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| depot_constraint | naive | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| depot_constraint | heuristic | 100.0% | 12860 | 0 | 15238 | 0 | 0 |
| route | none | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| route | naive | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| route | heuristic | 100.0% | 12860 | 0 | 15238 | 0 | 0 |
| shipment_delay | none | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| shipment_delay | naive | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| shipment_delay | heuristic | 100.0% | 12860 | 0 | 15238 | 0 | 0 |
| spike | none | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| spike | naive | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| spike | heuristic | 100.0% | 12860 | 0 | 15238 | 0 | 0 |
| station_outage | none | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| station_outage | naive | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| station_outage | heuristic | 100.0% | 12860 | 0 | 15238 | 0 | 0 |
| supply_shortfall | none | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| supply_shortfall | naive | 100.0% | 12860 | 0 | 0 | 0 | 0 |
| supply_shortfall | heuristic | 100.0% | 12860 | 0 | 15238 | 0 | 0 |

## Determinism verification (Run 1 vs Run 2)

| Scenario | Policy | Run 1 Svc Level | Run 2 Svc Level | Delta | Deterministic? |
|---|---|---:|---:|---:|---|
| baseline | none | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| baseline | naive | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| baseline | heuristic | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| combined | none | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| combined | naive | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| combined | heuristic | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| crisis_combined | none | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| crisis_combined | naive | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| crisis_combined | heuristic | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| depot_constraint | none | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| depot_constraint | naive | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| depot_constraint | heuristic | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| route | none | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| route | naive | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| route | heuristic | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| shipment_delay | none | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| shipment_delay | naive | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| shipment_delay | heuristic | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| spike | none | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| spike | naive | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| spike | heuristic | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| station_outage | none | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| station_outage | naive | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| station_outage | heuristic | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| supply_shortfall | none | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| supply_shortfall | naive | 100.00% | 100.00% | 0.0000 | ✅ PASS |
| supply_shortfall | heuristic | 100.00% | 100.00% | 0.0000 | ✅ PASS |

## Key findings

- **Heuristic policy** achieves equal or higher service level than do-nothing.
- **Naive policy** requests fuel without full constraint checking.
- **Determinism** is verified across Run 1 and Run 2.
