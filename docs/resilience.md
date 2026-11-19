# Resilience matrix

| Failure | Expected behavior | Observed (evidence path) |
|---|---|---|
| unavailable / error_rate (503) | retries with jitter, breaker, cached state, DEGRADED banner | Sprint 2 runtime evidence: `docs/evidence/sprint-02-runtime.md` |
| latency | timeouts, polling off the request path, UI p95 unaffected | Client timeout unit tests; live latency probe pending |
| stale_data | flag snapshot, lower confidence, block submit | Sprint 2 runtime evidence: `docs/evidence/sprint-02-runtime.md` |
| stream_disconnect | poll only, reconnect with backoff, refetch after reconnect | Sprint 2 runtime evidence and `tests/test_sse.py` |
| malformed data | reject, keep last good, raise alert | Sprint 2 malformed-field test and `docs/evidence/sprint-02-runtime.md` |
| predictor down | Predictor is not called by the worker yet; fallback behavior is not implemented | Not implemented; Sprint 5 work |
| worker down | API serves last persisted state; new ingest/forecast/execution stops | Compose health behavior is configured; no dedicated live worker-stop evidence recorded |
| low confidence | Forecast is marked for human review | Unit behavior is covered in forecast/risk tests |
| executor timeout on POST | Retry with the same stored body/key | Executor unit tests cover ambiguous transport handling; live accepted-write/replay remains unverified |
| executor sees the same key with a different body | fail closed locally; do not submit or record mismatched allocation as success | `tests/test_executor.py` and `tests/test_validator.py` |
| simulator rejects allocation (409/422) | mark FAILED, record rejection code metric, never retry business validation errors | `tests/test_executor.py`; live accepted-write scenario pending operator approval |
| stale or degraded executor read | expire recommendation without simulator write | `tests/test_executor.py` |
| demand_spike active/resolved | forecast includes/removes station multiplier; consumed inventory remains depleted and risk is recalculated | Sprint 3 runtime evidence and `tests/test_forecast.py` |
| shipment_delay with no dependent station allocation | delayed depot ETA changes; station risk is unchanged; no scheduled/in-transit supply is counted as on-hand | Sprint 3 runtime evidence and `tests/test_forecast.py` |

Parameters: timeouts connect 2s, read 3s; up to 3 retries after the initial attempt at 0.2/0.4/0.8s plus jitter; breaker opens after 5 consecutive failed requests and half-opens after 10s. Runtime evidence is recorded per sprint; unit, integration, and live evidence are distinguished above.
