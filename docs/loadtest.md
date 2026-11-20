# Load test

## Workload

`loadtest/k6.js` makes read-only GET requests to `/api/risks`, `/api/state`, and `/api/recommendations`. Set `BASE_URL` to the API base. The ramp stages reach 10, 50, and 100 virtual users, holding each level for 60 seconds. The thresholds are p95 under 300 ms and request error rate under 1%.

Run on a healthy dedicated stack:

```sh
k6 run loadtest/k6.js
mkdir -p docs/results
python scripts/loadtest_report.py loadtest/summary.json > docs/results/loadtest-normal.md
bash scripts/collect_stats.sh docs/results/docker-stats.csv
```

Run three times: normal service, simulator latency fault, and predictor stopped. Save raw k6 JSON output per run before rendering the report. Do not run fault or stop scenarios on a shared demo stack.

## Measurements

**NOT-RUN in the 2026-11-20 resumed session.** The Docker daemon was unavailable, local API endpoints refused connections, and k6 was not verified available. There are no latency, throughput, error-rate, CPU, memory, or knee measurements to report. Do not infer measurements from the thresholds or from earlier sprint tests.
