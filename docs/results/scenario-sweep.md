# Robust Policy Evaluation Report (60 Randomized Crisis Scenarios)

- **Generated:** 2026-11-23T05:01:30.665742+00:00
- **Simulation Horizon:** 192 ticks (2 simulated days per run)
- **Total Scenarios:** 60 (50 tuning + 10 holdout)
- **RNG Seed:** 42 (fully reproducible)
- **Model Version:** 1.1.0 | **Policy Version:** 2.1.0

## 1. Headline Policy Performance Table

| Policy | Mean SLA | Median SLA | P10 SLA | Worst Case | Wins / Ties / Losses vs Naive | 95% CI vs Naive (Mean Δ) |
|---|---:|---:|---:|---:|:---:|:---:|
| **none** | **40.40%** | 45.58% | 25.04% | 22.76% | Do Nothing | -56.74% |
| **naive** | **97.14%** | 100.00% | 90.20% | 86.27% | Baseline | N/A |
| **heuristic** | **97.93%** | 100.00% | 92.54% | 86.27% | 15W / 44T / 1L | +0.79% [0.41%, 1.27%] |
| **heuristic_buffer** | **97.93%** | 100.00% | 92.54% | 86.27% | 15W / 44T / 1L | +0.79% [0.41%, 1.27%] |

## 2. Unmet Demand Summary (Liters)

| Policy | Mean Unmet (L) | Median Unmet (L) | Worst-Case Unmet (L) |
|---|---:|---:|---:|
| **none** | 137,340 L | 102,604 L | 291,455 L |
| **naive** | 7,324 L | 0 L | 49,102 L |
| **heuristic** | 4,798 L | 0 L | 30,913 L |
| **heuristic_buffer** | 4,798 L | 0 L | 30,913 L |

## 3. Bootstrap 95% Confidence Intervals

- **Heuristic vs None (Do Nothing):** Mean improvement **+57.53%** SLA (95% CI: `[55.43%, 59.57%]`).
- **Heuristic vs Naive (Greedy Refill):** Mean improvement **+0.79%** SLA (95% CI: `[0.41%, 1.27%]`).
- **Heuristic+Buffer vs Naive:** Mean improvement **+0.79%** SLA (95% CI: `[0.41%, 1.27%]`).

## 4. Honest Loss Diagnosis & Boundary Analysis

Across all 60 randomized scenarios, the heuristic policy lost to naive in **1** cases:

| Scenario ID | Name | Heuristic SLA | Naive SLA | Delta | Loss Diagnosis / Root Cause |
|---|---|---:|---:|---:|---|
| `holdout_08` | Holdout holdout_08 | 99.86% | 99.95% | -0.08% | Holdout compound disaster with extreme multi-corridor transit bottleneck |

## 5. Hold-out Family Analysis

The 10 hold-out scenarios (`holdout_01` to `holdout_10`) were never used for parameter tuning.
On the hold-out set:
- **Heuristic Mean SLA on Holdout:** **96.26%** (Median: 95.99%, Worst: 91.67%)
- **Naive Mean SLA on Holdout:** **92.57%** (Median: 92.15%, Worst: 86.77%)
- **Record on Holdout:** **9 Wins**, **0 Ties**, **1 Losses**.
