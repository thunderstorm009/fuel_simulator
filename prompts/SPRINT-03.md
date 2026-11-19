# Sprint 3 (hours 8-12): Forecast and risk

SAME REPOSITORY. Starting state: tag sprint-2 (client, ingestion, read API, overview UI). Extend. Do not rewrite ingestion or the UI shell.

Skills: forecast-risk, test-driven-development, observability-metrics, verification-before-completion.

## Objective
Hours to stockout with uncertainty for every station and fuel, visible on the dashboard.

## Work packages

### WP3.1 Demand model and projection
TASK: core/world.py constants and core/forecast.py (pure). Constants (daily liters DIESEL/PETROL/OCTANE and noise): urban_high 8500/10500/5600 0.10; industrial 14000/4500/2200 0.08; highway 10500/11000/6200 0.12; regional 7200/7600/3600 0.10. Hour factors: industrial 06:00-17:59 1.55 else 0.45; highway 06-09 or 16-20 1.35 else 0.75; urban_high 07-09 or 16-20 1.45 else 0.70; regional 07:00-20:59 1.25 else 0.65 (apply the boundaries found in docs/sim-findings.md). Stations: mirpur urban_high, tongi industrial, karnaphuli highway, coxsbazar regional. Functions: expected_demand(profile, fuel, sim_time, multiplier, tick_minutes); calibrate_ratio(observed, expected, alpha=0.3, clamp 0.5-2.0); project_inventory(inventory, rates, arrivals) returning the trajectory and the first stockout tick over a 24-hour horizon; hours_to_stockout. Arrivals: IN_TRANSIT uses expected_arrival_tick; PENDING assumes departure next tick plus route transit_ticks.
TESTS: three hand-calculated cases with the arithmetic in comments; properties: more demand never delays stockout, more arrivals never advance it, zero demand gives none.
DONT: use inventory divided by current rate; hard-code tick length; do any I/O.

### WP3.2 Uncertainty and risk
TASK: core/risk.py. monte_carlo(...) with numpy, n=300, per-tick noise from the profile plus 10% rate uncertainty, seed parameter; returns P(stockout within 24h) and P10/P50/P90 stockout hours. classify(hours, prob): critical under 6h, high under 12h, medium under 24h, else ok. confidence(data_status, history_len, ratio_stability) in 0..1; needs_review when below 0.5. Output Forecast models. Vectorised; all 12 station-fuel pairs in under 50ms.
TESTS: determinism with the seed, monotonicity, timing, stale data lowers confidence.

### WP3.3 Forecast job and risk API
TASK: worker/forecast_job.py runs after each new snapshot behind a Forecaster interface (LocalForecaster now; a remote one comes in Sprint 5). Compute and persist forecasts for all pairs. Record forecast error (predicted vs observed demand over the last N ticks) as a metric. Open or resolve an incident when a pair crosses into or out of high or critical. API: GET /api/risks (latest per pair with band, probability, confidence) and GET /api/risks/{station}/{fuel}/trajectory (projected inventory with P10 and P90).
TESTS with fixtures, including a demand_spike scenario.

### WP3.4 Risk UI
TASK: Risk matrix page (stations by fuels, colour by level, hours text, probability). Drill-down drawer with a Recharts area chart of the projection and band, plus drivers (multiplier, recent ratio, arrivals). Alerts list. 'Needs review' badge for low confidence. Keep the Overview page working.

## Docs to update
docs/intelligence.md (formulas exactly as coded), docs/data-model.md, docs/decisions.md, docs/PROGRESS.md.

## Acceptance checklist (real output required)
- [ ] injecting demand_spike x1.8 on region-dhaka lowers hours-to-stockout for Mirpur and Tongi within one cycle, and it recovers after the event resolves
- [ ] a shipment_delay event changes projected arrivals and the risk
- [ ] the forecast error metric is visible
- [ ] hand-calculated and property tests pass; lint green

## Finish
Run prompts/SPRINT-GATE.md with N=3. Do not start Sprint 4.
