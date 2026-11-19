---
name: forecast-risk
description: Use when writing or changing demand forecasting, inventory projection, stockout risk, confidence or Monte Carlo code (core/forecast.py, core/risk.py).
---
# Forecast and risk
- Expected demand per tick = profile daily liters / (1440 / tick_minutes) x hour factor x station demand_multiplier. Constants live only in core/world.py.
- Calibrate with an EWMA ratio of observed to expected (alpha 0.3, clamp 0.5 to 2.0); ratio is 1 when history is short. The ratio absorbs unexplained factors such as a region factor.
- Demand is not served demand. Do not treat unmet demand as consumption.
- Project inventory forward tick by tick for 24 simulated hours, adding known arrivals (in-transit and scheduled supply are NOT on-hand inventory). Never use inventory divided by current rate: hour factors swing from 0.45 to 1.55.
- Monte Carlo: 300 runs, profile noise plus 10% rate uncertainty, seeded in tests. Output P(stockout in 24h) and P10/P50/P90 hours.
- Risk: critical under 6h, high under 12h, medium under 24h. Confidence falls with stale data, under 6 ticks of history or an unstable ratio; below 0.5 means needs_review.
- All functions are pure. Tests: hand-calculated cases with the arithmetic in comments, plus monotonic properties. Disclose limits; never claim accuracy that was not measured.
