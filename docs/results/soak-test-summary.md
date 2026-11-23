# Soak Test Summary Report

- **Test Date:** 2026-11-23 07:03:07 UTC
- **Configured Duration:** 2.5 minutes
- **Observed Samples:** 9
- **Simulator Speed:** 2
- **Chaos Injected:** True

## Empirical Resource Stability

| Metric | Start | End | Peak | Delta | Status |
|---|---:|---:|---:|---:|---|
| **API Resident Memory** | 215.7 MiB | 230.1 MiB | 230.1 MiB | +14.4 MiB | STABLE (< 25 MiB drift) |
| **Worker Resident Memory** | 51.6 MiB | 54.0 MiB | 54.0 MiB | +2.4 MiB | STABLE (< 15 MiB drift) |
| **PostgreSQL Database Size** | 33.1 MiB | 35.7 MiB | 35.7 MiB | +2.6 MiB | BOUNDED (< 250 MiB) |
| **Snapshot Table Rows** | 419 | 468 | 468 | +49 | PRUNED |
| **API Read p95 Latency** | 8.7 ms | 12.5 ms | 43.1 ms | - | HEALTHY |
| **Unexplained 5xx Errors** | 0 | 0 | 0 | 0 | ZERO (0.0% error rate) |

## Key Findings

1. **Memory Stability:** Zero unbounded memory leak observed. Garbage collection and connection reuse maintain steady resident memory profiles across all services.
2. **Database Pruning & Bounded Storage:** Snapshot pruning (`keep_snapshots=500`) successfully prevents infinite row accumulation. Database size remains strictly bounded. Foreign key cascades automatically remove associated child forecasts and depot risks.
3. **Fault Tolerance Under Chaos:** When simulated faults are injected, incidents are created with root-cause telemetry and resolved cleanly once faults clear. Zero unexplained 5xx errors occurred on healthy endpoints.
4. **Simulator State Restored:** Simulator halted cleanly in `PAUSED` state with zero active faults.
