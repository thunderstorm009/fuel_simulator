# Load test results

Source: `docs/results/k6-nopredictor-summary.json`
Workload: GET /api/risks, /api/state, /api/recommendations
Stages: 10s ramp + 60s hold per level; 5s ramp down

| Measure | Value |
|---|---:|
| Requests | 70233 |
| Throughput (req/s) | 326.6371713296305 |
| Average latency (ms) | 156.0231665741197 |
| p50 latency (ms) | 99.878 |
| p95 latency (ms) | 477.79579999999976 |
| p99 latency (ms) | unavailable |
| Error rate | 0 |

Repeat normal, simulator-latency, and predictor-unavailable runs. Keep raw summaries beside the report.

