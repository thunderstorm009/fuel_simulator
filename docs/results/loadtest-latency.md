# Load test results

Source: `docs/results/k6-latency-summary.json`
Workload: GET /api/risks, /api/state, /api/recommendations
Stages: 10s ramp + 60s hold per level; 5s ramp down

| Measure | Value |
|---|---:|
| Requests | 66588 |
| Throughput (req/s) | 309.6929109316993 |
| Average latency (ms) | 164.62087337057648 |
| p50 latency (ms) | 100.7835 |
| p95 latency (ms) | 523.8732 |
| p99 latency (ms) | unavailable |
| Error rate | 0 |

Repeat normal, simulator-latency, and predictor-unavailable runs. Keep raw summaries beside the report.

