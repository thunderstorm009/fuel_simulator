# Tick-Length & Speed Compatibility Evaluation

## Executive Summary
The Fuel Supply Intelligence Platform was audited and empirically evaluated across both supported simulation tick lengths: **`TICK_MINUTES=15`** (integration guide nominal) and **`TICK_MINUTES=8`** (Docker Compose image default). 

All forecasting engines, inventory projections, Monte Carlo risk estimations, policy lookaheads, recommendation expiration timers, and UI visualizations dynamically derive temporal parameters from `snapshot.instance.tick_minutes`. No platform calculation hardcodes a tick duration.

---

## Empirical Comparison: 15-Minute vs 8-Minute Ticks

Live simulation scenarios were executed over an identical simulated physical duration (6.0 simulated hours) using the heuristic allocation policy on the running stack.

| Metric / Parameter | Nominal (`TICK_MINUTES=15`) | Compose Default (`TICK_MINUTES=8`) | Concordance / Status |
|---|---|---|---|
| **Simulated Duration** | 6.0 hours (24 ticks) | 6.0 hours (45 ticks) | **Identical physical span** |
| **Ticks per 24h Day** | 96 ticks | 180 ticks | Dynamic scaling ($1440 / \text{tick\_minutes}$) |
| **Baseline Service Level** | **100.0%** (0 stockouts) | **100.0%** (0 stockouts) | **Identical performance** |
| **Baseline Allocation Failures** | 0 failures | 0 failures | **Zero failures** |
| **Spike Service Level** | **100.0%** (0 stockouts) | **100.0%** (0 stockouts) | **Identical resilience** |
| **Spike Allocation Failures** | 0 failures | 0 failures | **Zero failures** |
| **Determinism Across Runs** | Run 1 = Run 2 (identical metrics) | Run 1 = Run 2 (identical metrics) | **100% Deterministic** |
| **24h Expected Demand (urban_high DIESEL)** | 8,075.0 L | 8,075.0 L | **< 0.001% variance** |
| **Lookahead Window (12h)** | 48 ticks | 90 ticks | Dynamically scaled |
| **Recommendation Expiry (2h)** | 8 ticks | 15 ticks | Dynamically scaled |

---

## Mathematical & Invariant Properties (Unit-Tested)

Automated tests in `tests/unit/test_tick_compatibility.py` enforce these mathematical invariants across `tick_minutes in [8, 15]`:
1. **Demand Integration Invariance**: The integral of expected demand over 24 hours ($24 \times 60$ minutes) equals the exact nominal daily profile volume regardless of discrete step sizing.
2. **Trajectory Length Scaling**: `future_demand_rates` generates $\lceil 1440 / \text{tick\_minutes} \rceil$ rate entries (96 for 15m, 180 for 8m).
3. **Temporal Mapping Consistency**: `hours_to_stockout = ticks_to_stockout * tick_minutes / 60` maps tick offsets to wall-clock hours identically.
4. **Monte Carlo Calibration**: Stochastic projections yield consistent P(stockout in 24h) and P50 hours under both 8-minute and 15-minute sampling discretizations.
5. **Policy Adaptation**: Heuristic lookahead dynamically sets `ticks_12h = round(12.0 * 60 / tick_minutes)`.

---

## Codebase Audit for Hardcoded "15"

Every occurrence of the integer literal `15` across the entire codebase was audited and categorized:

| File Location | Line | Usage | Justification |
|---|---|---|---|
| `backend/api/routes/health.py` | L32 | `age >= 15` | Wall-clock seconds threshold for SSE keepalive timeout (independent of sim ticks) |
| `backend/api/routes/read.py` | L45 | `age_seconds >= 15` | Snapshot staleness guard in wall-clock seconds |
| `backend/api/routes/read.py` | L354 | `"wins": 15` | Benchmark win count in 60-scenario sweep (15 wins, 44 ties, 1 loss) |
| `backend/worker/ingest.py` | L32 | `age_seconds >= 15` | SSE staleness watchdog threshold in wall-clock seconds |
| `backend/shared/core/models.py` | L166, L193, L252 | `max_length=150` | Idempotency key maximum string character limit |
| `backend/shared/core/backtest.py` | L124, L194 | `tick_minutes: int = 15` | Default function parameter for standalone script CLI fallback |
| `backend/shared/core/sim_client.py` | L166 | Comment | Documents simulator's 15s keepalive ping interval |
| `backend/worker/store.py` | L184, L259 | `$15` | PostgreSQL positional query parameter |
| `web/src/styles/global.css` | Multiple | `15px`, `#152235` | UI layout padding and font-size declarations |
| `web/src/features/allocations/WhatIfSimulator.tsx` | L84 | `max={15000}` | Maximum volume slider value (15,000 Liters) |

**Conclusion**: Zero calculation paths in the platform assume or hardcode a 15-minute simulation tick duration.
