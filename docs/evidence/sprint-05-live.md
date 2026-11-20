# Sprint 5 live resilience evidence — 2026-11-20

Environment: project Docker Compose stack; simulator PAUSED, tick 150 at start. Existing allocation ID 1 remained ARRIVED. The run did not reset simulator state or submit allocations. Exact transcript: [sprint-05-fault-demo-accepted.txt](sprint-05-fault-demo-accepted.txt). Earlier failed attempts are retained separately and are not used as acceptance evidence.

| Requirement | Procedure and observed output | Result |
|---|---|---|
| `unavailable` fault | `bash scripts/fault_demo.sh`; live simulator `/v1/instance` returned 503; retry/failure counters and breaker-open gauge increased; data health DEGRADED; clear produced fresh HEALTHY snapshot | PASS |
| `error_rate` fault | Injected rate 1.0; endpoint returned 503; retries and breaker state observed; cached data DEGRADED; clear produced fresh HEALTHY snapshot | PASS |
| `latency` fault | Injected 3500 ms; direct probe took 3.51 s versus 3 s client read timeout; cached snapshot exceeded 15 s and became DEGRADED; clear recovered | PASS |
| `stale_data` fault | Endpoint returned HTTP 200 with `X-Simulator-Stale: true`; API exposed `stale=true`, DEGRADED; clear recovered to non-stale HEALTHY | PASS |
| `stream_disconnect` fault | Stream returned HTTP 503 with nested `detail.code`; REST remained healthy; reconnect counter increased; after clearing, JSON `simulator_stream_connected` log appeared without another worker restart | PASS |
| malformed response | `PYTHON_BIN=/tmp/fuel-sprint1-venv/bin/python ... scripts/fault_demo.sh`; test output `1 passed, 4 deselected`; simulator state was unchanged | PASS |
| predictor unavailable/recovery | Stopped predictor; health OFFLINE; fallback count 0→12; tick 151 stored 12 baseline forecasts, all `needs_review`, max confidence 0; active fallback incident visible. Restarted predictor; health HEALTHY; tick 152 stored 12 remote forecasts | PASS |
| worker unavailable/recovery | Stopped worker; health DEGRADED, data age 19.2 s; API and frontend HTTP 200; restart restored fresh HEALTHY ingestion | PASS |
| monitoring | Prometheus had three active targets, all up; Grafana health database `ok`, version 11.6.0; provisioned dashboard found. A one-tick demand spike moved its queried stockout-hours metric 19.5→19.25 | PASS |
| final simulator state | Script printed `Final state: PAUSED tick 152; faults clear; events resolved` | PASS |

`docker compose ps` reported all eight services running and healthy after the run. API overall health may later show DEGRADED while the simulator remains paused because the decision-engine heartbeat ages; worker and simulator component health remain independently visible, as designed. SMTP notification delivery remains unconfigured and unverified.

Related evidence: [fault matrix details](../resilience.md), [Grafana event query](sprint-05-grafana-event.txt), [earlier live verification](sprint-05-fault-demo-final.txt), and [local tests/build record](sprint-05-runtime.md). The files `sprint-05-fault-demo-output.txt`, `sprint-05-fault-demo-final-rerun.txt`, and `sprint-05-fault-demo-complete.txt` are preserved incomplete attempts and are not treated as passing evidence.
