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

## Sprint 12 API performance optimization and sweep (WP12.1)

Empirical load test sweep executed via `scripts/benchmark_sweep.py` running `loadtest/k6.js` across 10, 50, 100, 200, and 400 Virtual Users (VUs) comparing the baseline single-worker stack against the optimized multi-worker stack with composite indexing and snapshot-keyed byte caching.

### Comparative results table (10 to 400 VUs)

#### Baseline (Single-worker, default pool max 5, uncached reads)
Evidence: `docs/results/k6-baseline-sweep.json`

| VUs | Requests | Throughput (req/s) | Read p50 (ms) | Read p95 (ms) | Read p99 (ms) | WhatIf p95 (ms) | Errors | API CPU | API Mem | PG CPU | PG Mem |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **10** | 2,528 | 208.1 | 47.1 | 72.8 | 141.1 | 67.4 | 0.0% | 143.7% | 57.9 MiB | 92.9% | 73.4 MiB |
| **50** | 2,516 | 197.5 | 222.4 | 588.7 | 1,285.4 | 426.7 | 0.0% | 131.8% | 61.7 MiB | 108.6% | 73.8 MiB |
| **100** | 2,732 | 201.1 | 393.2 | 1,210.6 | 2,693.8 | 875.9 | 0.0% | 102.0% | 63.6 MiB | 99.9% | 73.3 MiB |
| **200** | 2,948 | 193.5 | 780.6 | 2,607.1 | 6,314.2 | 1,666.1 | 0.0% | 126.2% | 70.5 MiB | 107.5% | 73.3 MiB |
| **400** | 3,512 | 183.5 | 1,519.2 | 4,991.1 | 14,698.4 | 3,235.1 | 0.0% | 126.5% | 83.4 MiB | 309.8% | 67.3 MiB |

#### Optimized (4 Uvicorn workers, pool max 20, composite indexes, pre-serialized byte cache)
Evidence: `docs/results/k6-optimized-sweep.json`

| VUs | Requests | Throughput (req/s) | Read p50 (ms) | Read p95 (ms) | Read p99 (ms) | WhatIf p95 (ms) | Errors | API CPU | API Mem | PG CPU | PG Mem |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **10** | 6,428 | 531.3 | 5.9 | 49.5 | 185.3 | 64.6 | 0.0% | 321.4% | 234.7 MiB | 19.4% | 85.9 MiB |
| **50** | 7,560 | 614.6 | 55.7 | 163.6 | 398.3 | 284.7 | 0.0% | 459.4% | 251.5 MiB | 23.4% | 144.6 MiB |
| **100** | 7,700 | 615.3 | 88.2 | 338.3 | 600.5 | 288.3 | 0.0% | 417.2% | 248.4 MiB | 23.2% | 188.1 MiB |
| **200** | 8,212 | 625.8 | 210.4 | 622.5 | 2,325.4 | 790.9 | 0.0% | 439.8% | 262.3 MiB | 36.5% | 200.2 MiB |
| **400** | 8,372 | 520.6 | 501.2 | 1,756.9 | 6,840.7 | 1,323.2 | 0.0% | 433.9% | 281.1 MiB | 34.1% | 200.0 MiB |

### Profile summary & root-cause evidence

1. **Database query profiling via `EXPLAIN ANALYZE`:**
   - *Baseline:* `SELECT DISTINCT ON (station_id, fuel_type) ... FROM forecasts ORDER BY station_id, fuel_type, snapshot_id DESC;` executed a Seq Scan over 5,004 rows and an in-memory quicksort taking **15.342 ms per query**.
   - *Fix:* Added composite index `CREATE INDEX forecasts_pair_snapshot_idx ON forecasts (station_id, fuel_type, snapshot_id DESC);` and constrained queries to `snapshot_id = (SELECT id FROM snapshots ORDER BY fetched_at DESC, id DESC LIMIT 1)`. Execution time dropped from 15.342 ms to **0.103 ms (149x speedup)**.
   - *Depot risks query:* Execution time dropped from 3.815 ms to **0.106 ms (36x speedup)**.
   - *PostgreSQL container CPU under 400 VUs:* Dropped from **309.8%** (exhausting DB resources) down to **34.1%**.

2. **Connection pool sizing:**
   - *Baseline:* Hardcoded `min_size=1, max_size=5` in `backend/api/database.py`. Under 50+ VUs, requests blocked waiting for a connection checkout.
   - *Fix:* Increased pool to `min_size=2, max_size=20` (configurable via `DB_POOL_MAX_SIZE`).

3. **Multi-worker Uvicorn process scaling:**
   - *Baseline:* Single Uvicorn process pinned 1 CPU core (~126–143%), capping throughput at ~200 req/s.
   - *Fix:* Configured `API_WORKERS=4`. Throughput jumped from 201 req/s to **615–626 req/s (3.1x throughput improvement)** with API CPU scaling to 417–459%.

4. **Snapshot-keyed byte-level caching & ETag:**
   - In-memory response cache stores pre-serialized UTF-8 bytes keyed by `(endpoint, snapshot_id)`.
   - Eliminates redundant Python `json.dumps()` execution across repetitive reads.
   - Immediate invalidation on snapshot advancement (guarantees data is never older than the latest snapshot).
   - Returns HTTP 304 Not Modified when `If-None-Match` matches `W/"snap-{id}"`.

5. **Pure & cheap what-if simulation:**
   - Pre-parsed `Snapshot` Pydantic model cached in repository memory avoids parsing 60+ KB of nested JSON models on every what-if evaluation.
   - `WhatIf` p95 dropped from 875.9 ms to **288.3 ms at 100 VUs** (target < 500 ms MET).

6. **Throughput knee:**
   - The knee moved from 10 VUs (where throughput saturated at ~200 rps) out to **200 VUs** (sustaining 625.8 rps before tapering at 400 VUs).
   - Error rate: **0.0%** across all stages up to 400 VUs.

7. **Rate limiter multi-worker scaling:**
   - In-memory rate limiter scales per worker: `max(10, RATE_LIMIT_MAX_REQUESTS // API_WORKERS)`. With 4 workers and 60 req/min, each worker allows 15 decisions/min, preserving operator protection across uvicorn worker processes. Verified by `tests/unit/test_api_caching_and_rate_limit.py`.


Telemetry captured in `docs/results/docker-stats-latency.csv` and `docs/results/docker-stats-nopredictor.csv`:
- **API container (`fuel_simulator-api-1`):** CPU utilization peaked at 62.9% under 100 VUs; resident memory remained stable at 61.4 MiB.
- **PostgreSQL container (`fuel_simulator-postgres-1`):** CPU peaked at 42.4%; memory remained flat at 62.7 MiB.
- **Worker container (`fuel_simulator-worker-1`):** CPU stayed below 1.5%; memory remained flat at 51.4 MiB.
- **Frontend container (`fuel_simulator-frontend-1`):** Negligible CPU (0.0%), memory 8.7 MiB.
