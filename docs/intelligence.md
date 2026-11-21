# Intelligence design — Sprint 3-4 implementation

## Demand and stock projection

`backend/shared/core/world.py` defines daily liters and profile noise for urban-high, industrial, highway, and regional stations. Per-tick baseline demand is:

`daily_liters / (1440 / tick_minutes) * hour_factor(profile, sim_time) * max(0, multiplier)`

The inclusive hour-factor boundaries are recorded from the simulator in `docs/sim-findings.md`. `tick_minutes` comes from each snapshot's instance. Historical `demand_liters` is compared with the baseline multiplier-1 demand. Calibration starts at 1.0 and applies `ratio = alpha * observed/expected + (1-alpha) * prior_ratio` for each sample, clamping each result to [0.5, 2.0] (alpha 0.3).

Projection starts from station on-hand inventory, adds known station allocation quantities at their expected arrival ticks, then subtracts non-negative expected demand each tick for `ceil(1440 / tick_minutes)` future ticks. The first zero-or-lower projected level is the stockout tick. `IN_TRANSIT` uses `expected_arrival_tick`; `PENDING` assumes departure next tick plus the known route transit duration. Depot supply arrivals are not station inventory and are not treated as station allocation arrivals.

## Uncertainty, risk and confidence

The vectorized Monte Carlo runs 300 seeded paths by default. Each future tick multiplies the expected rate by independent non-negative normal factors `max(0, 1 + N(0, profile_noise))` and `max(0, 1 + N(0, 0.10))`. It reports the fraction with stockout in the horizon and P10/P50/P90 first-stockout hours. Paths without stockout are censored at 24 hours. The trajectory stores mean, P10, and P90 remaining inventory at each tick.

The deterministic first-stockout hours are classified as critical below 6, high below 12, medium below 24, and ok at or above 24; probability zero is ok. When hours are `None`, probability at least 0.1 is medium, otherwise ok. Confidence is the product of a data-status factor (HEALTHY 1.0, DEGRADED 0.5, OFFLINE/unknown 0.2), `min(1, max(0, history_ticks)/6)`, and `min(1, max(0, 1 - population_stdev(observed/baseline ratios)))`. Stale snapshots are treated as degraded. Confidence below 0.5 sets `needs_review`.

## Forecast job and metrics

The worker calculates one forecast per station/fuel after each distinct snapshot signature and persists the forecast, trajectory, and explanatory drivers. The `forecast_error_liters` gauge is labeled by station and fuel and reports mean absolute error over the latest 12 available observations, comparing observed demand with the calibrated baseline. Forecast count and job failure counters are also exposed on the worker `/metrics` endpoint.

High/critical transitions open or update a `stockout_risk` incident; leaving both levels resolves it. The API reads persisted forecasts only. It exposes the latest risk matrix and a per-pair projected inventory trajectory. The local Forecaster is replaceable through the worker interface; no remote predictor is used in Sprint 3.

## Simulator event semantics

The official integration guide says `demand_spike` changes affected station demand multipliers and `shipment_delay` changes scheduled depot supply arrival ticks. While the spike is active, expected demand includes the elevated station multiplier. When it resolves, the multiplier returns to its normal value; projected expected demand therefore moves toward normal. Historical EWMA calibration can retain some elevated observed-demand effect and converges as later observations arrive. Inventory consumed during the spike remains consumed. Risk is recalculated from remaining inventory and the now-normal multiplier; the previous stockout hours do not automatically return.

A depot supply schedule is not station inventory or a station allocation. A shipment delay changes no station shortage projection when no allocation or projected station supply coverage depends on it. This implementation does not invent future dispatches. When a station allocation exists, projection uses its verified `expected_arrival_tick` (or, for a pending allocation, next-tick departure plus route transit); scheduled and in-transit depot supply is never counted as current station inventory.

## Allocation policy and explanation

Sprint 4 adds an urgency-first heuristic that considers station/fuel pairs under 24 hours to stockout or with at least 50% 24-hour stockout probability. It targets the lower of 70% station capacity and one day of forecast demand, using projected station inventory at route arrival. It accounts for open or constrained depots, available routes, route shipment limits, depot on-hand stock, current-tick dispatch budget, destination capacity, same-cycle reservations, and allocations already pending or in transit. It prefers routes arriving before forecast stockout, splits quantities across feasible shipments, and validates every candidate before persistence. It does not count scheduled depot arrivals as on-hand stock or automatically dispatch.

The recommendation worker stores a permanent `rec-<uuid>` idempotency key together with its exact request body. The explanation records forecast drivers, applied limits, rejected route alternatives, before/after risk from re-running the forecast with the proposed known station arrival, confidence, policy, and snapshot status. The UI labels all values SIMULATED and requires an operator decision. Approvals and rejections are stored in the decision log; operator credentials exist only in browser memory.

Forecasts still describe the do-nothing path plus already-known station allocation arrivals. Depot supply schedule changes affect station risk only when a verified station allocation depends on that supply; the current implementation does not invent future dispatches.

## Two-pass constrained triage (Sprint 8)

During constrained supply (refinery shortfalls, depot throughput limits, or multiple competing stations), single-pass greedy allocation risks starving downstream stations. Sprint 8 introduces a deterministic two-pass triage policy in `core/policies/heuristic.py`:
- **Pass 1 (Emergency stockout prevention):** Determines the minimum 12-hour survival fuel need ($D_{12h} = \sum_{t=0}^{48} r_t$) for every at-risk pair, allocating survival fuel to the most urgent stations first.
- **Pass 2 (Target top-up):** Uses remaining depot physical inventory and remaining tick dispatch capacity to top stations up toward their 70% target inventory.
- Physical reservations carry across passes monotonically.
- When depot stock or dispatch limits truncate an allocation, it is flagged with `is_partial=True`, `unserved_liters`, and `unserved_reason` (e.g. `depot gazipur DIESEL exhausted`), identifying the physical constraint for the operator.

## Pure detection layer (Sprint 8)

`backend/shared/core/detect.py` implements pure detection algorithms with zero I/O, no database imports, and no simulator network calls. All detectors evaluate snapshot history deterministically:
1. **Demand anomaly (`demand_anomaly`):** Observed station demand is compared against the diurnal baseline WITHOUT the station multiplier over the last 4 observations. Flags when the observed/baseline ratio exceeds 1.3 for 3 consecutive ticks, enforcing `PROFILE_NOISE` as the noise floor. Recovery condition: demand returns below 1.3x baseline for 2 ticks.
2. **Regional surge (`regional_surge`):** Flags when 2 or more stations in the same geographic region exhibit demand anomalies within 8 ticks. Recovery condition: fewer than 2 regional stations remain flagged.
3. **Abnormal inventory change (`abnormal_inventory`):** Detects volume variances not accounted for by deliveries or recorded demand. Stations in `OUTAGE` or `CLOSED` status are explicitly excluded to prevent false positives.
4. **Bottleneck (`bottleneck`):** Flags when depot dispatch capacity utilization reaches or exceeds 80%, or when served 24-hour station demand exceeds depot physical stock plus scheduled arrivals within the 24-hour horizon.
5. **Emerging regional disruption (`emerging_regional_disruption`):** Flags active station outages or 2+ disrupted transport routes connecting into a region.

All detections create deduplicated incident records with type, severity, entity ID, stable `dedup_key`, plain-language explanation, recovery condition, and evidence JSON, and increment `detections_total{type}`.

## Forward depot supply risk (Sprint 8)

`backend/shared/core/depot_risk.py` computes forward supply cover across all network depots:
$$\text{Net 24h Cover} = \text{Current Inventory} + \text{Scheduled Arrivals}_{\le 24h} - \text{Committed Allocations} - \text{Projected 24h Served Demand}$$
- **Shipment delay effect:** When scheduled arrivals are delayed beyond the 24-hour horizon, they fall out of $\text{Scheduled Arrivals}_{\le 24h}$, lowering net cover and cover hours.
- **Supply shortfall effect:** When an arrival volume is reduced (e.g. halved by factor 0.5), net cover drops proportionally.
- Unrelated depots are provably unaffected.
- Projections are persisted by the worker into `depot_risks` and rendered in the dashboard's `DepotRiskPanel`.

## Backtesting, calibration, and drift tracking (Sprint 9)

### Empirical backtesting performance (docs/results/backtest-summary.md)
Evaluated across 2,000 recorded demand history ticks across all 4 stations and 3 fuel types using `core/backtest.py`:
- **1-hour horizon (4 ticks):** MAPE **3.07%**, Bias **+0.01%**, P10–P90 interval coverage **91.49%** (nominal target 80.0%).
- **6-hour horizon (24 ticks):** MAPE **2.19%**, Bias **-0.13%**, P10–P90 interval coverage **65.57%**.
- **12-hour horizon (48 ticks):** MAPE **2.10%**, Bias **-0.31%**, P10–P90 interval coverage **49.86%**.
- **24-hour horizon (96 ticks):** MAPE **2.11%**, Bias **-0.42%**, P10–P90 interval coverage **36.08%**.

### Honest reporting of weaknesses
- **Point Forecast Accuracy vs Interval Coverage:** The point forecast remains highly accurate across all horizons (~2.1% MAPE). However, because demand noise accumulates as independent stochastic variances across 96 ticks, the nominal 80% coverage interval coverage drops from 91.5% at 1h to 36.1% at 24h.
- **Drift Under Sudden Shock:** Under sudden demand spikes (e.g. 2.5x multiplier), the calibration EWMA ratio takes 4–6 ticks to catch up, during which bias is temporarily negative.

### Drift detection and metric (`calibration_drift`)
`backend/shared/core/detect.py` implements pure `detect_calibration_drift`. If the calibration ratio stays outside $[0.8, 1.25]$ for $\ge 4$ consecutive ticks, a `calibration_drift` incident (severity WARNING) is opened, recording direction (`SURGE` or `COLLAPSE`), mean ratio, and tick evidence, and incrementing `forecast_drift_total{direction}`.

### Model and policy versioning
- Constant `MODEL_VERSION = "1.1.0"` in `backend/shared/core/version.py`.
- Constant `POLICY_VERSION = "2.0.0"` in `backend/shared/core/version.py`.
- Stored on every forecast and recommendation database row, serialized in `explanation_json`, returned in `GET /api/state`, and recorded in `docs/results/experiments.csv`.
