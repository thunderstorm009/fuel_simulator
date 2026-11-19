# Resilience matrix (fill the Observed column with real evidence in Sprint 5)

| Failure | Expected behavior | Observed (evidence path) |
|---|---|---|
| unavailable / error_rate (503) | retries with jitter, breaker, cached state, DEGRADED banner | EVIDENCE: |
| latency | timeouts, polling off the request path, UI p95 unaffected | EVIDENCE: |
| stale_data | flag snapshot, lower confidence, block submit | EVIDENCE: |
| stream_disconnect | poll only, reconnect with backoff, refetch after reconnect | EVIDENCE: |
| malformed data | reject, keep last good, raise alert | EVIDENCE: |
| predictor down | baseline forecast, low confidence, fallback metric and incident | EVIDENCE: |
| worker down | API serves last state with data age, OFFLINE or DEGRADED | EVIDENCE: |
| low confidence | needs human review flag | EVIDENCE: |
| executor timeout on POST | retry with the same key, one allocation | EVIDENCE: |

Parameters: timeouts connect 2s, read 3s; retries 3 at 0.2/0.4/0.8s with jitter; breaker opens after 5 consecutive failures and half-opens after 10s.
