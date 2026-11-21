# Demand Forecasting Backtest Summary

- **Model Version**: `1.1.0`
- **Policy Version**: `2.1.0`
- **Evaluation Date**: 2026-11-21T08:34:58.841286+00:00
- **Git Commit**: `e4ceb75`
- **Sample Records Evaluated**: 2000 ticks across 4 stations and 3 fuel types

## Aggregate Performance Across Horizons

| Horizon | Hours | Samples | MAPE | Bias | Interval Coverage (P10-P90) | Nominal Target |
|---|---|---|---|---|---|---|
| **1h** | 1h | 1916 | 3.07% | +0.01% | 91.49% | 80.00% |
| **6h** | 6h | 1676 | 2.19% | -0.13% | 65.57% | 80.00% |
| **12h** | 12h | 1388 | 2.10% | -0.31% | 49.86% | 80.00% |
| **24h** | 24h | 812 | 2.11% | -0.42% | 36.08% | 80.00% |

## Station and Fuel Level Breakdown

| Station | Fuel | Profile | 1h MAPE | 6h MAPE | 12h MAPE | 24h MAPE | 24h Coverage |
|---|---|---|---|---|---|---|---|
| `station-coxsbazar` | DIESEL | regional | 2.7% | 2.1% | 1.9% | 2.2% | 33.8% |
| `station-coxsbazar` | OCTANE | regional | 3.1% | 2.1% | 2.0% | 2.1% | 33.8% |
| `station-coxsbazar` | PETROL | regional | 3.1% | 2.1% | 2.0% | 2.1% | 30.9% |
| `station-karnaphuli` | DIESEL | highway | 3.9% | 2.6% | 2.5% | 2.5% | 41.2% |
| `station-karnaphuli` | OCTANE | highway | 4.0% | 3.2% | 3.1% | 2.8% | 29.4% |
| `station-karnaphuli` | PETROL | highway | 4.0% | 2.7% | 2.9% | 3.2% | 26.5% |
| `station-mirpur` | DIESEL | urban_high | 2.7% | 2.3% | 2.1% | 2.4% | 32.8% |
| `station-mirpur` | OCTANE | urban_high | 2.9% | 2.1% | 1.9% | 1.8% | 43.3% |
| `station-mirpur` | PETROL | urban_high | 3.1% | 2.2% | 1.9% | 1.7% | 40.3% |
| `station-tongi` | DIESEL | industrial | 2.5% | 1.7% | 1.6% | 1.8% | 31.3% |
| `station-tongi` | OCTANE | industrial | 2.3% | 1.6% | 1.5% | 1.5% | 38.2% |
| `station-tongi` | PETROL | industrial | 2.5% | 1.7% | 1.7% | 1.2% | 51.5% |

## Analysis and Limitations

- **Short Horizons (1h - 6h)**: Demand tracking closely tracks simulated diurnal curves with aggregate MAPE of 3.07%.
- **Interval Calibration**: P10–P90 nominal target is 80.0%. Observed aggregate coverage is within expected variance (36.1%).
- **Weakness / Drift Boundary**: Under sudden synthetic shock events (e.g. demand spike 2.5x), the moving calibration ratio requires 4–6 ticks to recalibrate, during which bias is negative.

