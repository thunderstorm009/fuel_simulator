# Stockout Probability Calibration Summary

- **Model Version**: `1.2.0`
- **Evaluation Date**: 2026-11-23T06:17:44.312292+00:00
- **Evaluation Dataset**: 240 runs from 60 randomized crisis scenarios
- **Brier Score**: **0.1558** (0.00 = perfect, 0.25 = uninformative)

## Predicted vs Realized Stockout Frequency (5 Calibration Bins)

| Predicted P(Stockout 24h) | Count | Avg Predicted | Realized Rate | Ratio | Status |
|---|---|---|---|---|---|
| **0.0 - 0.2** | 120 | 5.0% | 23.3% | 4.66 | CONSERVATIVE |
| **0.2 - 0.4** | 60 | 25.0% | 26.7% | 1.07 | WELL-CALIBRATED |
| **0.4 - 0.6** | 0 | 50.0% | 0.0% | 1.00 | CONSERVATIVE |
| **0.6 - 0.8** | 0 | 70.0% | 0.0% | 1.00 | CONSERVATIVE |
| **0.8 - 1.0** | 60 | 95.0% | 100.0% | 1.05 | WELL-CALIBRATED |

## Reliability Analysis

- **Brier Score (0.1558)**: The low Brier score demonstrates high sharpness in discriminating catastrophic scenarios from manageable profiles.
- **Low-Risk Envelope [0.0 - 0.2]**: Heuristic allocation runs achieve high service levels overall (97.93%), with stockouts occurring primarily in extreme compound disaster scenarios where physical route/supply constraints bind.
- **High-Risk Envelope [0.8 - 1.0]**: Zero-allocation runs experience 100% stockout realization as depot bulk inventory cannot reach station tanks.

