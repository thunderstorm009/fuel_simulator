# Load test results

Source: `loadtest/summary.json`
Workload: GET /api/risks, /api/state, /api/recommendations
Stages: 10s ramp + 60s hold per level; 5s ramp down

| Measure | Value |
|---|---:|
| Requests | 68907 |
| Throughput (req/s) | 320.48945200085006 |
| Average latency (ms) | 159.04666242907194 |
| p50 latency (ms) | 72.628 |
| p95 latency (ms) | 549.636 |
| p99 latency (ms) | unavailable |
| Error rate | 0 |

Repeat normal, simulator-latency, and predictor-unavailable runs. Keep raw summaries beside the report.

