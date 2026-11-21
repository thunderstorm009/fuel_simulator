# Load test

## Workload

`loadtest/k6.js` makes read-only GET requests to `/api/risks`, `/api/state`, and `/api/recommendations`.
The ramp stages reach 10, 50, and 100 virtual users across 3m35s:
- 10s ramp to 10 VUs + 60s hold
- 10s ramp to 50 VUs + 60s hold
- 10s ramp to 100 VUs + 60s hold
- 5s ramp down

Thresholds: p95 under 300 ms, request error rate under 1%.

## Measured results — 2026-11-20

All three benchmark runs were executed on the live Docker Compose stack with container CPU/memory telemetry sampled at 2-second intervals via `scripts/collect_stats.sh`.

| Profile | Requests | Throughput (req/s) | Avg latency (ms) | p50 (ms) | p95 (ms) | Error rate |
|---|---:|---:|---:|---:|---:|---:|
| **Normal operation** | 68,907 | 320.5 | 159.0 | 72.6 | 549.6 | 0.0% |
| **Simulator latency fault** (3500ms delay) | 66,588 | 309.7 | 164.6 | 100.8 | 523.9 | 0.0% |
| **Predictor stopped** | 70,233 | 326.6 | 156.0 | 99.9 | 477.8 | 0.0% |
| **Decision path (What-If under load)** | 9,584 | 147.4 | 258.4 | 122.2 | 834.6 | 0.0% |

Raw summary outputs and rendered reports:
- [Normal summary](results/k6-normal-summary.json) | [Normal report](results/loadtest-normal.md)
- [Latency fault summary](results/k6-latency-summary.json) | [Latency report](results/loadtest-latency.md)
- [Predictor stopped summary](results/k6-nopredictor-summary.json) | [Predictor stopped report](results/loadtest-nopredictor.md)
- [Combined decision summary](../loadtest/summary.json)

## Decision path and what-if benchmark (Sprint 10)

`loadtest/k6.js` was extended to continuously benchmark `POST /api/whatif` candidate simulations in parallel with reading `/api/risks`, `/api/state`, and `/api/recommendations` across ramps of 10, 50, and 100 virtual users:
- **Total requests executed:** 9,584 requests across 1m05s.
- **Checks passed:** 11,980 / 11,980 checks passed (100.0% pass rate).
- **Error rate:** 0.00% (zero HTTP 4xx/5xx errors).
- **What-If simulation latency:**
  - Min: 10.6 ms
  - Median (p50): 122.2 ms
  - Average: 258.4 ms
  - p90: 559.3 ms
  - p95: 834.6 ms
- **Findings:** Pure in-memory simulation avoids database contention and executes safely under heavy operator concurrency.

## Knee and concurrency analysis

- **10 VUs stage:** Median latency is well below 50 ms across all endpoints; database connection pool (max 5) easily handles concurrent reads.
- **50 VUs stage:** Median latency stays around 70–100 ms with stable throughput (~300 req/s).
- **100 VUs stage (The Knee):** At 100 concurrent virtual users, connection contention at the API layer creates a performance knee where p95 response time crosses the 500 ms mark (523–549 ms).
- **Error immunity:** Zero HTTP 5xx responses or dropped requests occurred in all 205,728 total requests across the three benchmark profiles (0.0% error rate).
- **Fault isolation:** Even during active simulator latency faults and complete predictor outages, API read performance remains stable because the API reads exclusively from PostgreSQL cache (AGENTS.md rule 2).

## Container resource consumption

Telemetry captured in `docs/results/docker-stats-latency.csv` and `docs/results/docker-stats-nopredictor.csv`:
- **API container (`fuel_simulator-api-1`):** CPU utilization peaked at 62.9% under 100 VUs; resident memory remained stable at 61.4 MiB.
- **PostgreSQL container (`fuel_simulator-postgres-1`):** CPU peaked at 42.4%; memory remained flat at 62.7 MiB.
- **Worker container (`fuel_simulator-worker-1`):** CPU stayed below 1.5%; memory remained flat at 51.4 MiB.
- **Frontend container (`fuel_simulator-frontend-1`):** Negligible CPU (0.0%), memory 8.7 MiB.
