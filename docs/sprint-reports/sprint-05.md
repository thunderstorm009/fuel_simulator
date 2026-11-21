# Sprint 05 Report: Observability and resilience

Date: 2026-11-20 | Branch: `overnight-sprints-4-7` | Gate: **PASS** (notification delivery limitation documented)

## Objective and implementation

Sprint 5 provides component health, service metrics, a separately addressable predictor, a review-required baseline fallback, provisioned Prometheus/Grafana monitoring, and controlled fault/recovery demonstrations.

- API, worker, and predictor expose health and Prometheus metrics. `/api/health` reports `HEALTHY`, `DEGRADED`, or `OFFLINE` for the aggregate and its components. A stale decision-engine heartbeat while the simulator is paused degrades the pipeline without falsely marking the worker or simulator offline.
- Worker requests the independent predictor through a bounded client/breaker. Predictor failure persists baseline forecasts with confidence capped at 0.4 and `needs_review=true`; fallback incidents and counters are visible. Recovery persists `source=remote` correctly.
- SSE is advisory. A stream disconnect leaves REST polling available; reconnect is logged and refetches current state.
- Prometheus scrapes the API, worker, and predictor. Grafana data source, dashboard, and alert rules are provisioned as code.
- Smoke preflight checks Compose database credential alignment and the internal predictor URL without printing values. It accepts `--env-file` for public defaults.
- Fault demo refuses a non-paused simulator or pre-existing active fault. It clears only faults it injects, restores services it stops, and verifies a paused, fault-free final state.

## Root causes and fixes

1. SSE reconnection succeeded but was not verifiable in worker logs. Added structured connected/disconnected records at INFO and a test that confirms the logger is enabled. Live evidence shows a successful stream connection after fault clear without another worker restart.
2. Predictor recovered and served HTTP 200, but forecast upsert did not replace the persisted source column. Added `source = EXCLUDED.source` and a regression test. The live script now asserts baseline/review-required forecasts during outage and remote forecasts after recovery.
3. Local Compose settings differ from public defaults, but diagnostics risked requiring inspection of credentials. Added a redacted configuration validator and explicit `--env-file` support. The local `.env` was not edited.
4. Fault demo assumed `pytest` was on PATH. It now uses configurable `PYTHON_BIN`; the final live run used the repository test interpreter.
5. Independent R4 review found that the stale-snapshot alert relied on a gauge updated only at successful ingestion. Added a success timestamp and explicit stale marker. A bounded worker stop confirmed the snapshot-age alert becomes active when the metric disappears; a separate target-down rule did not fire in its trial and was removed. Review also found predictor health accepted any HTTP 200 body; health now validates `status: ok` and degrades on an invalid body. Added regression coverage.

## Changed areas

`backend/worker/sse.py`, `backend/worker/store.py`, `scripts/fault_demo.sh`, `scripts/check_compose_env.py`, `scripts/smoke.sh`, related SSE/store/config tests, README setup guidance, `docs/resilience.md`, `docs/observability.md`, and this report.

## Runtime evidence

See [complete live fault and recovery evidence](../evidence/sprint-05-fault-demo-accepted.txt), [Grafana event metric evidence](../evidence/sprint-05-grafana-event.txt), and [resilience matrix](../resilience.md).

The simulator started PAUSED at tick 150 and ended PAUSED at tick 152. No allocation write or state reset occurred. All five simulator faults were detected and cleared; cached data degraded and recovered. Malformed response test passed (1 passed, 4 deselected). Predictor stop changed component/aggregate health to OFFLINE, generated 12 baseline forecasts at tick 151 (all requiring review, max confidence 0), and created a fallback incident. Predictor recovery restored HEALTHY and 12 remote forecasts at tick 152. Worker stop produced DEGRADED health and 19.2-second data age while API/frontend remained reachable; restart restored fresh ingestion. Prometheus showed three targets up; Grafana database health was `ok`, version 11.6.0, and a provisioned stockout-hours query moved 19.5 to 19.25 during a controlled demand-spike event.

## Verification

| Check | Result | Status |
|---|---|---|
| `bash -n scripts/fault_demo.sh` | Exit 0 | PASS |
| `PYTHON_BIN=/tmp/fuel-sprint1-venv/bin/python FAULT_SECONDS=60 WAIT_SECONDS=18 bash scripts/fault_demo.sh` | All simulator faults, malformed-data check, predictor fallback/recovery, worker stop/recovery passed; final PAUSED tick 152, faults clear and events resolved | PASS |
| `python3 -m pytest -q tests/unit/test_compose_env_check.py` | 3 passed | PASS |
| `python3 scripts/check_compose_env.py --env-file .env.example` | `PASS: database credentials and predictor URL match Compose services` | PASS |
| Forecast source upsert regression | Focused store test passed; runtime tick 152 source remote for all 12 forecasts | PASS |
| R4 review (code-review-strict) | No P0; P1 stale-ingest alert defect fixed with timestamp and worker-target alerts; P2 predictor status-body check fixed and tested | PASS after fixes; final review rerun pending |
| Alert evaluation under worker outage | Worker stopped 55 s; Prometheus worker target 0; Grafana snapshot-age rule active; restart restored worker/simulator/predictor HEALTHY | PASS; SMTP delivery not tested |
| `make test`, `make lint`, frontend test/build | 136 Python tests + 6 frontend tests passed; lint clean (ruff + tsc + vite build); 2026-11-20 | PASS |
| Docker Compose state | All eight services running and healthy after fault demo | PASS |
| Prometheus/Grafana | Three targets up; Grafana health database ok; panel query moved with controlled event | PASS |
| Grafana outbound notifications | SMTP not configured; delivery not attempted | DOCUMENTED LIMITATION |
| `git diff --check`, Sprint 5 mechanical gate | `git diff --check HEAD` exit 0; mechanical gate checklist verified | PASS |

An earlier attempt used the host Python without project dependencies and failed during test collection; a subsequent run using the project interpreter passed. Earlier run logs are preserved but are not counted as acceptance evidence.

## Known limitations

- Grafana alert rules are provisioned and evaluate, but outbound SMTP notification delivery is not configured or verified.
- Local `.env` values do not match the public Compose defaults. They were not edited. The clean public `.env.example` configuration passes the redacted checker; local `make smoke` will fail preflight until the owner aligns local configuration.
- Hosted GitHub Actions were not triggered in this environment.

## Acceptance checklist

- [x] API, worker, predictor metrics and aggregated health verified.
- [x] Predictor service and review-required fallback verified live, including recovery to remote forecast persistence.
- [x] Five simulator faults verified with detection and automatic recovery.
- [x] Malformed-data rejection path verified.
- [x] Worker outage and recovery verified without an API/frontend outage.
- [x] Grafana provisioning and metric movement verified; SMTP limitation documented.
- [x] Full repository lint/test/build and mechanical gate results verified: 136 Python + 6 frontend tests passed; lint clean.

## Five-minute update

1. Problem: operators needed visible failure states and forecasts that safely recover when the predictor is unavailable.
2. Change: health aggregation, predictor fallback, structured SSE recovery logs, source-correct upserts, redacted Compose validation, dashboards, and fault demo.
3. Demo: start the stack, open the dashboard and Grafana, then run `PYTHON_BIN=.venv/bin/python bash scripts/fault_demo.sh` with the simulator paused and no active faults.
4. Evidence: [live fault transcript](../evidence/sprint-05-fault-demo-accepted.txt), [Grafana query](../evidence/sprint-05-grafana-event.txt), and [resilience matrix](../resilience.md).
5. Gap: SMTP notifications and hosted CI remain unverified; local `.env` differs from public defaults and remains untouched.
