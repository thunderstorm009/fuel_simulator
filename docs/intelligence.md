# Intelligence design (planned; update to the exact code in Sprints 3-4 and 6)

## Forecast
Expected demand per tick = daily liters / (1440 / tick_minutes) x hour factor x station demand_multiplier. Calibrate with an EWMA ratio observed/expected (alpha 0.3, clamp 0.5-2.0). Project inventory forward tick by tick for 24 simulated hours with known arrivals; first tick at or below zero is the stockout. Do not divide inventory by current rate.

## Uncertainty and risk
Monte Carlo, 300 runs, per-tick noise from the profile plus 10% rate uncertainty. Outputs P(stockout within 24h), P10/P50/P90 hours. Risk: critical under 6h, high under 12h, medium under 24h. Confidence drops with stale data, short history or unstable ratio; below 0.5 means needs human review.

## Allocation policy (heuristic)
Rank pairs by urgency. Need = target (70% of capacity or 24h demand) minus projected inventory at arrival, capped by free station capacity. Prefer routes that arrive before stockout. Cap by max_shipment, depot inventory, remaining dispatch capacity; track reservations; split; cooldown for in-transit. Validate with core/validator.py.

## Explanation JSON
drivers, constraints applied, risk before and after, alternatives with rejection reasons, confidence, policy used, data status, timestamp.

## Evaluation
scripts/scenario_runner.py compares do-nothing, naive (refill to 70% below 30%) and heuristic on service_level and unmet liters across baseline, spike, route and combined scenarios. Results live in docs/results. State seeds and limits honestly.

## Fallbacks
Remote predictor down: baseline forecast (static profile, confidence capped at 0.4, needs_review). Primary policy fails or times out: heuristic.
