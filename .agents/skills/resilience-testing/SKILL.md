---
name: resilience-testing
description: Use when adding or testing retries, timeouts, circuit breakers, caching, fallbacks, health status or fault-demo scripts.
---
# Resilience and fault testing
- Timeouts: connect 2s, read 3s. Retries: 3 attempts at 0.2/0.4/0.8s with jitter. Breaker: open after 5 consecutive failures, half-open after 10s.
- Data status: HEALTHY (under 15s old, not stale, breaker closed), DEGRADED (stale, half-open, 15 to 120s old, or fallback active), OFFLINE (over 120s).
- Behavior: unavailable or error_rate means retry, breaker, cached state and a DEGRADED banner. latency means timeouts and polling off the request path. stale_data means flag and block submit. stream_disconnect means poll and reconnect with backoff. malformed data means reject, keep last good, alert. predictor down means baseline forecast with low confidence and a fallback metric. low confidence means human review.
- Test each fault through /admin/faults and events through /admin/events (hit /v1 paths to see faults; /admin bypasses them).
- Verify detection, degraded behavior AND recovery without restarting anything. Capture evidence in docs/evidence.
- Degraded states must be visible. Never swallow exceptions silently. Cap retries to avoid retry storms.
