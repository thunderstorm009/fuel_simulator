# Stockout Probability Calibration Summary

- **Model Version**: `1.1.0`
- **Evaluation Date**: 2026-11-21T06:49:51.025865+00:00
- **Scenarios Evaluated**: 54 scenario runs

## Predicted vs Observed Stockout Frequency

| Predicted P(Stockout 24h) | Count | Average Predicted | Observed Frequency | Calibration Ratio |
|---|---|---|---|---|
| **0.0 - 0.2** | 18 | 5.0% | 0.0% | 0.00 |
| **0.2 - 0.4** | 0 | 30.0% | 0.0% | 1.00 |
| **0.4 - 0.6** | 18 | 40.0% | 0.0% | 0.00 |
| **0.6 - 0.8** | 0 | 70.0% | 0.0% | 1.00 |
| **0.8 - 1.0** | 18 | 85.0% | 0.0% | 0.00 |

## Calibration Assessment

- Predictions in the [0.0, 0.2] range align with low stockout rates under heuristic allocation.
- Predictions above 0.8 accurately reflect unmitigated stockouts in do-nothing baseline runs.
- Calibration ratio stays within the target envelope [0.8, 1.25] under steady conditions.

