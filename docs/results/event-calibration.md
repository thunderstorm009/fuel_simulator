# Event-Aware Calibration & Spike Convergence

- **Model Version**: `1.2.0`
- **Policy Version**: `2.1.0`
- **Evaluation Date**: 2026-11-23T06:17:44.311177+00:00

> **Truth Rule Disclaimer**: The simulator is deterministic and the model follows its
> documented demand profile, so accuracy shows consistency, not real-world performance.

## Convergence Under Demand Shocks

When an external demand spike event begins (e.g. 2.0x or 2.5x demand surge), we measure
the simulation ticks required for forecast convergence within 5% of realized demand.

| Shock Scenario | Legacy Model v1.1.0 Lag | Event-Aware Model v1.2.0 Lag | Improvement |
|---|---|---|---|
| **2.0x Demand Surge** | 7 ticks (~105 min) | 0 ticks (~0 min) | **Eliminated lag (7 -> 0 ticks)** |
| **2.5x Demand Surge** | 19 ticks (~285 min) | 0 ticks (~0 min) | **Eliminated lag (19 -> 0 ticks)** |

## Technical Mechanics

1. **Root Cause of Legacy Lag**: In Model v1.1.0, `expected_demand` for historical ticks was computed using a hardcoded `multiplier=1.0`. When actual demand doubled during an event, the EWMA ratio was forced to absorb the entire surge. With smoothing parameter `alpha=0.3`, it took 4–6 ticks to reach 2.0.
2. **Double-Counting Elimination**: In Model v1.1.0, once the EWMA ratio adapted to 2.0, multiplying `station.demand_multiplier (2.0) * ratio (2.0)` led to a 4.0x demand projection. Model v1.2.0 evaluates historical expected demand against the known event multiplier, isolating `ratio` to residual noise (~1.0).
3. **Instantaneous Transition**: At event onset and end, the model adapts in 0–1 ticks.

