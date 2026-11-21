# Resilience and fault verification

All exercises below use the simulated BUP Fuel Supply Simulator. The live fault demo does not reset state or submit allocation writes. It requires a paused simulator, no pre-existing active faults, Docker Compose, and a Python environment with project test dependencies.

Run it with:

```sh
PYTHON_BIN=.venv/bin/python bash scripts/fault_demo.sh
```

`PYTHON_BIN` may point at another environment that has the repository test dependencies installed. The script rejects a running simulator or pre-existing active fault, clears the fault it injects, restarts only worker/predictor containers that it stopped, and checks at exit that faults are clear, events are resolved, and the simulator is PAUSED. It does not reset the simulator.

## Live result — 2026-11-20

Evidence: [complete controlled fault demo](evidence/sprint-05-fault-demo-accepted.txt). The run began at tick 150 and ended PAUSED at tick 152. No allocation was created. The same stack remained healthy after recovery.

| Fault | Detection and degraded behavior | Recovery evidence | Result |
|---|---|---|---|
| `unavailable` | Simulator returned HTTP 503; retries and breaker-open metric increased; cached snapshot became DEGRADED | Fault cleared; accepted non-stale snapshot returned HEALTHY | PASS |
| `error_rate` | Injected HTTP 503; retry/failure counters and open breaker observed; cached snapshot became DEGRADED | Fault cleared; snapshot returned HEALTHY | PASS |
| `latency` | 3500 ms simulator delay; client probe took about 3.51 s; cached snapshot aged beyond 15 s and became DEGRADED | Fault cleared; fresh snapshot returned HEALTHY | PASS |
| `stale_data` | HTTP 200 included `X-Simulator-Stale: true`; API data health showed `stale=true`, `DEGRADED` | Fault cleared; fresh non-stale snapshot returned HEALTHY | PASS |
| `stream_disconnect` | Stream endpoint returned HTTP 503 with nested fault code; REST ingestion stayed HEALTHY; reconnect metric increased | After clear, worker logged `simulator_stream_connected` without a subsequent worker restart | PASS |
| Malformed simulator response | Controlled test fixture returned malformed content; last-known-good behavior and rejection path tested | `1 passed, 4 deselected` | PASS (test fixture; no live simulator mutation) |
| Predictor stopped | `/api/health` reported OFFLINE; fallback counter increased; tick 151 persisted 12 `baseline` forecasts, all review-required, confidence at most 0.4; fallback incident visible | Predictor restarted; `/api/health` HEALTHY; tick 152 persisted 12 `remote` forecasts | PASS |
| Worker stopped | API and frontend stayed reachable; health DEGRADED and snapshot age grew past 19 s | Worker restarted; ingestion returned HEALTHY | PASS |

Prometheus had three active targets and all were `up`. Grafana `/api/health` returned database `ok`, version 11.6.0. A controlled one-tick `demand_spike` changed the provisioned `hours_to_stockout{station="station-coxsbazar",fuel="DIESEL"}` query from 19.5 to 19.25, and the event resolved at tick 145. Evidence: [Grafana event and panel query](evidence/sprint-05-grafana-event.txt).

## Recovery and limits

- REST polling is authoritative. SSE disconnects trigger reconnect and refetch; stream availability is not required for REST health.
- Predictor fallback is persisted with low confidence and `needs_review`; recovery replaces same-key forecast rows with their remote `source` value. A regression test covers this upsert behavior.
- Grafana freshness alerting uses `worker_last_ingest_timestamp_seconds`, which ages while ingest is failing and alerts if the worker metric disappears. A successful poll alone is not enough to refresh the alert timestamp. A stopped-worker exercise observed Prometheus `up{job="worker"}=0` and the Grafana snapshot-age alert active; see [worker alert check](evidence/sprint-05-worker-alert-check.txt).
- The local `.env` contains values that differ from the public Compose defaults. It was left untouched. The safe configuration check passes with `.env.example` and reports the local mismatch by variable name only, without printing values. Run `python3 scripts/check_compose_env.py --env-file .env.example` to check clean-clone defaults.
- Grafana dashboards and alert rules are provisioned and evaluate locally. Email delivery is not configured (Grafana logs report SMTP is unconfigured), so notification delivery is not verified.
- Fault durations are bounded and the script does not clear unrelated/pre-existing faults; it refuses to start if any are active.

## Running simulator resilience & speed adaptation (Sprint 8)

When the simulator runs in continuous `RUNNING` mode (rather than paused and stepped), ticks advance at real-time speeds:
1. **Adaptive Freshness:** `GET /api/state` reports dynamic `ticks_per_second` and `snapshot_age_ticks`.
2. **Speed Warning Banner:** When observed tick velocity exceeds 0.5 ticks/s, a high-priority warning banner is displayed to the operator warning that recommendations may expire before manual approval.
3. **Pre-Submission Re-validation:** The executor re-reads fresh authoritative non-stale REST state from the simulator and re-validates all 5 constraint rules immediately prior to issuing `POST /v1/allocations`. If simulator ticks advanced and made the allocation infeasible, or if the snapshot is marked stale, the submission is rejected locally and marked failed without corrupting simulator state.
4. **Idempotency Stability:** Recommendation IDs and idempotency keys are permanent UUIDs stored in PostgreSQL and never reused across different allocation bodies.
