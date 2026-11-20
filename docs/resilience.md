# Resilience matrix

| Failure | Expected behavior | Observed (evidence path) |
|---|---|---|
| unavailable / error_rate (503) | retries with jitter, breaker, cached state, DEGRADED banner | Prior live evidence: `docs/evidence/sprint-02-runtime.md`; current rerun pending |
| latency | bounded client timeout and retry; UI remains on persisted state | Client tests; current live rerun pending |
| stale_data | stale marker, lower confidence, execution blocked | Prior live evidence: `docs/evidence/sprint-02-runtime.md`; current rerun pending |
| stream_disconnect | REST polling continues; reconnect triggers a refetch | Prior live evidence and `tests/integration/test_sse.py`; current live rerun pending |
| malformed data | reject, keep last good, log and count rejection | `tests/integration/test_ingest.py`, `tests/integration/test_resilience.py`; live malformed injection is unavailable |
| predictor down | profile-only fallback, confidence <= 0.4, review required, incident and fallback metric | `tests/integration/test_predictor.py`; current container stop/recovery pending |
| worker down | API serves last persisted state; new ingest/forecast/execution stops | Compose health behavior is configured; no dedicated live worker-stop evidence recorded |
| low confidence | Forecast is marked for human review | Unit behavior is covered in forecast/risk tests |
| executor timeout on POST | Retry with the same stored body/key | Executor unit tests cover ambiguous transport handling; live accepted-write/replay remains unverified |
| executor sees the same key with a different body | fail closed locally; do not submit or record mismatched allocation as success | `tests/test_executor.py` and `tests/test_validator.py` |
| simulator rejects allocation (409/422) | mark FAILED, record rejection code metric, never retry business validation errors | `tests/test_executor.py`; live accepted-write scenario pending operator approval |
| stale or degraded executor read | expire recommendation without simulator write | `tests/test_executor.py` |
| demand_spike active/resolved | forecast includes/removes station multiplier; consumed inventory remains depleted and risk is recalculated | Sprint 3 runtime evidence and `tests/test_forecast.py` |
| shipment_delay with no dependent station allocation | delayed depot ETA changes; station risk is unchanged; no scheduled/in-transit supply is counted as on-hand | Sprint 3 runtime evidence and `tests/test_forecast.py` |

Parameters: simulator timeouts connect 2s, read 3s; up to 3 retries after the initial attempt at 0.2/0.4/0.8s plus jitter; simulator breaker opens after 5 consecutive failed requests and half-opens after 10s. Predictor timeout defaults to 1.5s with an independent breaker. `scripts/fault_demo.sh` runs the five documented simulator fault scenes and clears each through a trap. Runtime evidence is recorded per sprint; unit, integration, and live evidence are distinguished above. In the current resumed environment, Docker is unavailable and the live reruns are NOT-RUN.
