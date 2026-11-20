Reading additional input from stdin...
OpenAI Codex v0.171.0
--------
workdir: /Users/abrar/project/fuel_simulator
model: gpt-6-luna
provider: openai
approval: never
sandbox: read-only
reasoning effort: high
reasoning summaries: none
session id: 01a1f88d-858d-7822-87fd-d98338ff3f39
--------
user
Perform the separate read-only Sprint 5 R4 resilience review. Follow the repository common header and the R4 prompt in .local/prompts/REVIEW-PROMPTS.md. Inspect actual code, tests, current diff, docs/resilience.md and docs/evidence/sprint-05-fault-demo-accepted.txt. Do not edit files. Do not inspect .env or print any credentials. For each of latency, unavailable, error_rate, stale_data, stream_disconnect, malformed data, predictor down, and worker down, trace behavior and operator visibility. Identify silent failures, retry storms, missing alerts, falsely healthy states, and test proposals. Rank findings P0/P1/P2 with file and line; clearly state if no P0/P1 findings.
codex
I’ll read the repository review instructions and resilience review prompt first, then trace each injected fault through implementation, tests, and operator surfaces. I’ll keep this read-only and avoid `.env` and credential values.
exec
/bin/zsh -lc 'rg -n "fuel_simulator|resilience review|Sprint 5|R4" /Users/abrar/.codex/memories/MEMORY.md' in /Users/abrar/project/fuel_simulator
 exited 1 in 0ms:
codex
I didn’t find relevant prior project notes, so I’m grounding the review in the current repository. I’m applying the repository’s strict review skill and will begin with `docs/PROGRESS.md`, then check branch/worktree and the required R4 materials.
exec
/bin/zsh -lc 'cat .agents/skills/code-review-strict/SKILL.md && cat docs/PROGRESS.md && git status --short --branch && git diff --stat && git diff --' in /Users/abrar/project/fuel_simulator
 succeeded in 0ms:
---
name: code-review-strict
description: Use to review a git diff against AGENTS.md rules before merging. Read-only unless asked.
---
# Strict code review
- Run git diff main...HEAD (or against the last tag). Cite the AGENTS.md rule number for each violation.
- Look for bugs, missing timeouts or validation, constraint violations, impure core functions, API-calls-simulator, flaky tests, secrets, security issues, unmeasured claims and rewrites of earlier sprint work.
- Rank P0, P1, P2. Suggest minimal fixes; do not rewrite code.
# Project progress

Last updated: 2026-11-20. Resume point for the shared repository worktree.

## Current status

- Branch: `overnight-sprints-4-7`, based on `b1fc38b`. The pre-run tree is preserved in commit `ee830cc`; Sprint 4 is tagged at `3fe2353` as `sprint-4`. No pushes have been made.
- Sprint 1–3: historical reports record those sprint gates as passed. Their implementation remains preserved.
- Sprint 4: **PASS**. One project-owner-authorized recommendation was approved at tick 134, submitted by the worker, reached `ARRIVED` at tick 137, and one exact body/key replay returned the same allocation ID. The simulator is PAUSED at tick 138; only one allocation and one decision exist. Details: [Sprint 4 live evidence](evidence/sprint-04-overnight.md). The measured ETA discrepancy and the review's P2 projection-offset finding are corrected and regression-tested. Independent R3 review found no P0/P1; public and local mechanical gates passed after final changes. Tag: `sprint-4`.
- Sprint 5: API/worker/predictor metrics, health aggregation, remote predictor with baseline fallback, token-protected chaos switch, Grafana/Prometheus provisioning, and fault demo are present. Local unit/integration tests and builds passed earlier; live fault/recovery evidence is still required.
- Sprint 6: k6 workload, stats collector, report renderer, docs/quickstart checks and CI changes are present. Deterministic scenario runner, three measured load runs, and local CI validation remain.
- Sprint 7: cold-start and chaos scripts, final demo notes, Q&A, assumptions, AI-use and known-issues docs are present. Cold-start, chaos round, docs audit, final documentation audit and readiness report remain.
- Public local-instruction check: private development instructions and sprint prompts are intentionally absent from clean clones. `scripts/sprint_gate_public.sh` reports absent local-only inputs as SKIP. The legacy `scripts/sprint_gate.sh` path is ignored by existing repository rules and will not be force-added or made trackable by changing those rules.

## Verification in this work package

- Focused ETA regression initially failed on the old calculation, then passed after correcting the estimate to current simulator tick plus route transit.
- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make lint`: Ruff and formatting passed; TypeScript typecheck and Vite production build passed.
- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make test`: 130 Python tests and 6 frontend tests passed.
- `FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 docker compose config -q`: passed.
- `git diff --check`: passed.
- One replay through worker `SimClient` returned allocation ID 1, `ARRIVED`, same key and `stale=false`; read-only final verification found one matching allocation, one decision, and PAUSED tick 138.

## Current work package and exact next action

Sprint 5 first task: inspect its complete requirements/report/evidence and current Compose health, then run the latency fault scene with recovery while keeping simulator PAUSED and preserving allocation ID 1. Do not add another live operator-app approval or simulator allocation.

## Workspace constraints

Do not edit `.env`, stage ignored local instructions, expose secrets, reset state outside authorized scenario/cold-start runs, or push. Preserve current Compose volumes and simulator state except for user-authorized simulation scenarios after evidence and commits. Keep public documentation self-sufficient without private development files.

## Sprint log

| Sprint | Status | Report |
|---|---|---|
| 1 | Passed historically; local verification only | [sprint-01.md](sprint-reports/sprint-01.md) |
| 2 | Passed historically with runtime evidence | [sprint-02.md](sprint-reports/sprint-02.md) |
| 3 | Passed historically with revised simulator semantics | [sprint-03.md](sprint-reports/sprint-03.md) |
| 4 | PASS; live workflow, R3 review, and mechanical gates passed; tag `sprint-4` | [sprint-04.md](sprint-reports/sprint-04.md) |
| 5 | Implementation present; runtime fault gate open | [sprint-05.md](sprint-reports/sprint-05.md) |
| 6 | Tooling partial; scenarios and measurements open | [sprint-06.md](sprint-reports/sprint-06.md) |
| 7 | Readiness artifacts partial; final verification open | [sprint-07.md](sprint-reports/sprint-07.md) |

## Five-minute status update

1. **Problem:** Operators need current simulated fuel state, shortage risk, feasible explained allocations, mandatory human approval, and recovery visibility.
2. **Change:** Sprint 4's single authorized live workflow is complete. It exposed and corrected a one-tick recommendation ETA error; approval identity/body, health, and snapshot freshness safeguards are in place.
3. **Demo:** Open the frontend at `http://localhost:5174`; inspect health, inventories, risks and the allocation decision history. The simulator is PAUSED at tick 138 with the accepted 6,000 L allocation ARRIVED. Do not issue another live allocation.
4. **Evidence:** `docs/evidence/sprint-04-overnight.md` contains the owner authorization record, request body, constraint checks, tick-by-tick progression, exact replay and duplicate check. The current local test run passed 130 Python and 6 frontend tests, plus lint/build and Compose config.
5. **Remaining:** Commit/tag Sprint 4 and proceed to Sprint 5 live fault/recovery tests, then Sprint 6 load proof and Sprint 7 freeze checks. Hosted GitHub CI remains unavailable here.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-KnsX2ZtQ' (errno=Operation not permitted)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-QvGVXpUS' (errno=Operation not permitted)
## overnight-sprints-4-7
 M README.md
 M backend/worker/sse.py
 M backend/worker/store.py
 M docs/decisions.md
 M docs/observability.md
 M docs/resilience.md
 M docs/sprint-reports/sprint-05.md
 M scripts/fault_demo.sh
 M scripts/smoke.sh
 M tests/integration/test_sse.py
 M tests/unit/test_store_snapshot.py
?? docs/evidence/sprint-05-fault-demo-accepted.txt
?? docs/evidence/sprint-05-fault-demo-complete.txt
?? docs/evidence/sprint-05-fault-demo-final-rerun.txt
?? docs/evidence/sprint-05-fault-demo-final.txt
?? docs/evidence/sprint-05-fault-demo-output.txt
?? docs/evidence/sprint-05-fault-demo-verified.txt
?? docs/evidence/sprint-05-grafana-event.txt
?? docs/evidence/sprint-05-live.md
?? docs/evidence/sprint-05-r4-review.md
?? scripts/check_compose_env.py
?? tests/unit/test_compose_env_check.py
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-HqohSWit' (errno=Operation not permitted)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-xPI7Wmzu' (errno=Operation not permitted)
 README.md                         |  11 +-
 backend/worker/sse.py             |  23 ++++
 backend/worker/store.py           |   1 +
 docs/decisions.md                 |   7 ++
 docs/observability.md             |   4 +-
 docs/resilience.md                |  56 +++++----
 docs/sprint-reports/sprint-05.md  | 122 ++++++++++----------
 scripts/fault_demo.sh             | 234 ++++++++++++++++++++++++++++++++++----
 scripts/smoke.sh                  |   2 +
 tests/integration/test_sse.py     |  12 +-
 tests/unit/test_store_snapshot.py |  33 +++++-
 11 files changed, 390 insertions(+), 115 deletions(-)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-7WONYX7X' (errno=Operation not permitted)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-N9q8awT9' (errno=Operation not permitted)
diff --git a/README.md b/README.md
index dbdc2a6..a4419a9 100644
--- a/README.md
+++ b/README.md
@@ -36,7 +36,7 @@ The platform has six independently running services:
 | API | Database-backed operator reads and approval/rejection records; no simulator reads | `http://localhost:8101` |
 | Worker | Simulator REST/SSE, validation, persistence, forecasting, recommendation and approved execution jobs | `http://localhost:8102` |
 | Predictor | Validated forecast endpoint; worker timeout/breaker and review-required baseline fallback | `http://localhost:8103` |
-| Frontend | React + TypeScript operator interface | `http://localhost:5173` |
+| Frontend | React + TypeScript operator interface | `http://localhost:${FRONTEND_HOST_PORT:-5173}` |
 | Prometheus | Scrapes API, worker and predictor metrics | `http://localhost:9090` |
 | Grafana | Provisioned Prometheus data source | `http://localhost:3000` |
 
@@ -62,9 +62,10 @@ docs/                    Architecture, decisions, evidence and sprint reports
 
 ## Run locally
 
-1. Copy `.env.example` to `.env` and configure `DATABASE_URL` and `POSTGRES_PASSWORD` to match. Set `OPERATOR_TOKEN` for approval/rejection actions. The defaults are for local development only.
-2. Start the stack with `make up`. If host port 5173 is occupied, set `FRONTEND_HOST_PORT=5174` and `CORS_ORIGIN=http://localhost:5174` in `.env`.
-3. Check service health at each service's `/health` endpoint, and open the frontend URL above.
+1. Copy `.env.example` to `.env`. For approval/rejection actions, set a local `OPERATOR_TOKEN`; never commit `.env`. The defaults are for local simulated development.
+2. Start the stack with `make up`. If host port 5173 is occupied, set `FRONTEND_HOST_PORT=5174` and `CORS_ORIGIN=http://localhost:5174` in `.env` before startup.
+3. Run `python3 scripts/check_compose_env.py` to catch database or predictor endpoint mismatches before startup. Clean-clone defaults can be checked without a local `.env` using `python3 scripts/check_compose_env.py --env-file .env.example`.
+4. Check service health at each service's `/health` endpoint, and open the configured frontend URL.
 
 `make down` stops containers and preserves volumes. Do not use `docker compose down -v` unless you intend to delete local database and Grafana data.
 
@@ -86,6 +87,6 @@ See `.env.example` for supported environment variables and [docs/operations.md](
 
 ## Development status
 
-Sprints 1–3 have historical local acceptance evidence. Sprint 4 code and local checks are present, while its live acceptance gate remains open: an operator-approved allocation reaching `ARRIVED` and an identical body/key replay have not been verified, and no simulator allocation was submitted. Sprint 5 predictor, fallback, health UI, and dashboard code is present; its live resilience gate remains unverified in the current environment. Sprints 6–7 still require scenario and performance evidence, CI execution, and a cold-start/demo rehearsal. See [the current progress record](docs/PROGRESS.md) and [final execution report](docs/FINAL-EXECUTION-REPORT.md).
+Sprints 1–4 have acceptance evidence, including one explicitly authorized Sprint 4 allocation that reached `ARRIVED` and an exact body/key replay. Sprint 5's simulator fault, predictor fallback/recovery, worker recovery, and monitoring checks are recorded in [the resilience report](docs/resilience.md). Sprints 6–7 remain in progress; see [the current progress record](docs/PROGRESS.md) and [final execution report](docs/FINAL-EXECUTION-REPORT.md).
 
 The consolidated engineering update is [Day 1 Engineering Progress — Sprints 1–4](docs/DAY-1-UPDATE.md).
diff --git a/backend/worker/sse.py b/backend/worker/sse.py
index fea1e85..f180b3a 100644
--- a/backend/worker/sse.py
+++ b/backend/worker/sse.py
@@ -7,11 +7,17 @@ import json
 import logging
 import time
 from collections.abc import Awaitable, Callable
+from datetime import datetime, timezone
 
 from core.metrics import sse_events, sse_reconnects
 from core.sim_client import SimClient
 
 logger = logging.getLogger("fuel_simulator.worker.sse")
+logger.setLevel(logging.INFO)
+if not logger.handlers:
+    handler = logging.StreamHandler()
+    handler.setFormatter(logging.Formatter("%(message)s"))
+    logger.addHandler(handler)
 
 
 class SSEConsumer:
@@ -44,6 +50,18 @@ class SSEConsumer:
             sse_reconnects.inc()
             try:
                 async with self.client.stream() as lines:
+                    logger.info(
+                        json.dumps(
+                            {
+                                "timestamp": datetime.now(timezone.utc).isoformat(),
+                                "level": "info",
+                                "service": "worker",
+                                "event": "simulator_stream_connected",
+                                "tick": None,
+                                "correlation_id": None,
+                            }
+                        )
+                    )
                     await self._refresh_if_due()
                     backoff_s = 0.5
                     async for line in lines:
@@ -58,8 +76,13 @@ class SSEConsumer:
                 logger.warning(
                     json.dumps(
                         {
+                            "timestamp": datetime.now(timezone.utc).isoformat(),
+                            "level": "warning",
+                            "service": "worker",
                             "event": "simulator_stream_disconnected",
                             "error_type": type(exc).__name__,
+                            "tick": None,
+                            "correlation_id": None,
                         }
                     )
                 )
diff --git a/backend/worker/store.py b/backend/worker/store.py
index 40bf03f..bb03d4d 100644
--- a/backend/worker/store.py
+++ b/backend/worker/store.py
@@ -149,6 +149,7 @@ class PostgresStore:
                             confidence = EXCLUDED.confidence,
                             risk_level = EXCLUDED.risk_level,
                             needs_review = EXCLUDED.needs_review,
+                            source = EXCLUDED.source,
                             trajectory = EXCLUDED.trajectory,
                             drivers = EXCLUDED.drivers
                         """,
diff --git a/docs/decisions.md b/docs/decisions.md
index a9073c3..9b8a5c6 100644
--- a/docs/decisions.md
+++ b/docs/decisions.md
@@ -195,3 +195,10 @@ The live `demand_spike` x1.8 event on `region-dhaka` reduced Mirpur DIESEL from
 - **Context:** The overnight execution log and morning handoff can contain environment-specific operational details and are not product documentation. The repository intentionally keeps local prompts and instructions out of the public tree.
 - **Decision:** Ignore only `docs/OVERNIGHT-LOG.md` and `docs/MORNING-TODO.md` for the overnight run; keep reusable, redacted execution evidence and sprint results in tracked `docs/evidence/` and sprint reports.
 - **Trade-off:** These two handoff files exist only in the local workspace; repository progress and evidence remain the shared source of truth.
+
+### ADR-029 — Validate resolved Compose service credentials without exposing values
+
+- **Status:** ACCEPTED
+- **Context:** The local `.env` differs from the public Compose defaults for database credentials and predictor port. Editing that local file is prohibited, and a mismatch otherwise appears later as a confusing service startup failure.
+- **Decision:** Add a smoke preflight that parses resolved Compose JSON and compares API/worker database credentials with PostgreSQL and the worker predictor URL with the predictor's internal port. Diagnostics identify only the mismatched variable names and redact values. Accept `--env-file` so clean-clone defaults can be verified explicitly. Keep `.env.example` and Compose defaults authoritative for public setup.
+- **Trade-off:** The smoke preflight intentionally fails in this local checkout until its owner aligns local settings; clean public defaults remain testable without changing local secrets.
diff --git a/docs/observability.md b/docs/observability.md
index 6f52e67..2c28ce5 100644
--- a/docs/observability.md
+++ b/docs/observability.md
@@ -32,4 +32,6 @@ Python services log operational errors and job events using JSON records for rel
 
 ## Verification and gaps
 
-The sprint reports and `docs/evidence/` contain service health, scrape/metric, and runtime observations from the runs that were actually available. Current Grafana runtime and panel movement under fault injection have not been rechecked in this resumed session because Docker is unavailable. Do not treat configuration presence as proof that a dashboard loaded or an alert fired.
+Live verification on 2026-11-20 found API, worker, and predictor Prometheus targets all `up`; Grafana `/api/health` returned database `ok` on version 11.6.0. The provisioned dashboard was found by UID `fuel-supply-platform`. During a one-tick simulated demand-spike event, the Grafana-backed `hours_to_stockout{station="station-coxsbazar",fuel="DIESEL"}` query changed from 19.5 to 19.25; the event later resolved. See [Grafana event evidence](evidence/sprint-05-grafana-event.txt) and [fault/recovery evidence](evidence/sprint-05-fault-demo-accepted.txt).
+
+Alert rules are provisioned and evaluating, but outbound notification delivery is not configured: Grafana logs report SMTP is unconfigured. No email notification delivery is claimed. Metric values are process-local and may reset after a service restart.
diff --git a/docs/resilience.md b/docs/resilience.md
index 8570124..1de785b 100644
--- a/docs/resilience.md
+++ b/docs/resilience.md
@@ -1,20 +1,36 @@
-# Resilience matrix
-
-| Failure | Expected behavior | Observed (evidence path) |
-|---|---|---|
-| unavailable / error_rate (503) | retries with jitter, breaker, cached state, DEGRADED banner | Prior live evidence: `docs/evidence/sprint-02-runtime.md`; current rerun pending |
-| latency | bounded client timeout and retry; UI remains on persisted state | Client tests; current live rerun pending |
-| stale_data | stale marker, lower confidence, execution blocked | Prior live evidence: `docs/evidence/sprint-02-runtime.md`; current rerun pending |
-| stream_disconnect | REST polling continues; reconnect triggers a refetch | Prior live evidence and `tests/integration/test_sse.py`; current live rerun pending |
-| malformed data | reject, keep last good, log and count rejection | `tests/integration/test_ingest.py`, `tests/integration/test_resilience.py`; live malformed injection is unavailable |
-| predictor down | profile-only fallback, confidence <= 0.4, review required, incident and fallback metric | `tests/integration/test_predictor.py`; current container stop/recovery pending |
-| worker down | API serves last persisted state; new ingest/forecast/execution stops | Compose health behavior is configured; no dedicated live worker-stop evidence recorded |
-| low confidence | Forecast is marked for human review | Unit behavior is covered in forecast/risk tests |
-| executor timeout on POST | Retry with the same stored body/key | Executor unit tests cover ambiguous transport handling; live accepted-write/replay remains unverified |
-| executor sees the same key with a different body | fail closed locally; do not submit or record mismatched allocation as success | `tests/test_executor.py` and `tests/test_validator.py` |
-| simulator rejects allocation (409/422) | mark FAILED, record rejection code metric, never retry business validation errors | `tests/test_executor.py`; live accepted-write scenario pending operator approval |
-| stale or degraded executor read | expire recommendation without simulator write | `tests/test_executor.py` |
-| demand_spike active/resolved | forecast includes/removes station multiplier; consumed inventory remains depleted and risk is recalculated | Sprint 3 runtime evidence and `tests/test_forecast.py` |
-| shipment_delay with no dependent station allocation | delayed depot ETA changes; station risk is unchanged; no scheduled/in-transit supply is counted as on-hand | Sprint 3 runtime evidence and `tests/test_forecast.py` |
-
-Parameters: simulator timeouts connect 2s, read 3s; up to 3 retries after the initial attempt at 0.2/0.4/0.8s plus jitter; simulator breaker opens after 5 consecutive failed requests and half-opens after 10s. Predictor timeout defaults to 1.5s with an independent breaker. `scripts/fault_demo.sh` runs the five documented simulator fault scenes and clears each through a trap. Runtime evidence is recorded per sprint; unit, integration, and live evidence are distinguished above. In the current resumed environment, Docker is unavailable and the live reruns are NOT-RUN.
+# Resilience and fault verification
+
+All exercises below use the simulated BUP Fuel Supply Simulator. The live fault demo does not reset state or submit allocation writes. It requires a paused simulator, no pre-existing active faults, Docker Compose, and a Python environment with project test dependencies.
+
+Run it with:
+
+```sh
+PYTHON_BIN=.venv/bin/python bash scripts/fault_demo.sh
+```
+
+`PYTHON_BIN` may point at another environment that has the repository test dependencies installed. The script rejects a running simulator or pre-existing active fault, clears the fault it injects, restarts only worker/predictor containers that it stopped, and checks at exit that faults are clear, events are resolved, and the simulator is PAUSED. It does not reset the simulator.
+
+## Live result — 2026-11-20
+
+Evidence: [complete controlled fault demo](evidence/sprint-05-fault-demo-accepted.txt). The run began at tick 150 and ended PAUSED at tick 152. No allocation was created. The same stack remained healthy after recovery.
+
+| Fault | Detection and degraded behavior | Recovery evidence | Result |
+|---|---|---|---|
+| `unavailable` | Simulator returned HTTP 503; retries and breaker-open metric increased; cached snapshot became DEGRADED | Fault cleared; accepted non-stale snapshot returned HEALTHY | PASS |
+| `error_rate` | Injected HTTP 503; retry/failure counters and open breaker observed; cached snapshot became DEGRADED | Fault cleared; snapshot returned HEALTHY | PASS |
+| `latency` | 3500 ms simulator delay; client probe took about 3.51 s; cached snapshot aged beyond 15 s and became DEGRADED | Fault cleared; fresh snapshot returned HEALTHY | PASS |
+| `stale_data` | HTTP 200 included `X-Simulator-Stale: true`; API data health showed `stale=true`, `DEGRADED` | Fault cleared; fresh non-stale snapshot returned HEALTHY | PASS |
+| `stream_disconnect` | Stream endpoint returned HTTP 503 with nested fault code; REST ingestion stayed HEALTHY; reconnect metric increased | After clear, worker logged `simulator_stream_connected` without a subsequent worker restart | PASS |
+| Malformed simulator response | Controlled test fixture returned malformed content; last-known-good behavior and rejection path tested | `1 passed, 4 deselected` | PASS (test fixture; no live simulator mutation) |
+| Predictor stopped | `/api/health` reported OFFLINE; fallback counter increased; tick 151 persisted 12 `baseline` forecasts, all review-required, confidence at most 0.4; fallback incident visible | Predictor restarted; `/api/health` HEALTHY; tick 152 persisted 12 `remote` forecasts | PASS |
+| Worker stopped | API and frontend stayed reachable; health DEGRADED and snapshot age grew past 19 s | Worker restarted; ingestion returned HEALTHY | PASS |
+
+Prometheus had three active targets and all were `up`. Grafana `/api/health` returned database `ok`, version 11.6.0. A controlled one-tick `demand_spike` changed the provisioned `hours_to_stockout{station="station-coxsbazar",fuel="DIESEL"}` query from 19.5 to 19.25, and the event resolved at tick 145. Evidence: [Grafana event and panel query](evidence/sprint-05-grafana-event.txt).
+
+## Recovery and limits
+
+- REST polling is authoritative. SSE disconnects trigger reconnect and refetch; stream availability is not required for REST health.
+- Predictor fallback is persisted with low confidence and `needs_review`; recovery replaces same-key forecast rows with their remote `source` value. A regression test covers this upsert behavior.
+- The local `.env` contains values that differ from the public Compose defaults. It was left untouched. The safe configuration check passes with `.env.example` and reports the local mismatch by variable name only, without printing values. Run `python3 scripts/check_compose_env.py --env-file .env.example` to check clean-clone defaults.
+- Grafana dashboards and alert rules are provisioned and evaluate locally. Email delivery is not configured (Grafana logs report SMTP is unconfigured), so notification delivery is not verified.
+- Fault durations are bounded and the script does not clear unrelated/pre-existing faults; it refuses to start if any are active.
diff --git a/docs/sprint-reports/sprint-05.md b/docs/sprint-reports/sprint-05.md
index b116566..58bb52b 100644
--- a/docs/sprint-reports/sprint-05.md
+++ b/docs/sprint-reports/sprint-05.md
@@ -1,80 +1,72 @@
 # Sprint 05 Report: Observability and resilience
 
-Time window: 2026-11-20 | Owner: Codex | Branch: `main`, base `b1fc38b` | Status: **Blocked on live runtime acceptance**
+Date: 2026-11-20 | Branch: `overnight-sprints-4-7` | Gate: **PASS** (notification delivery limitation documented)
 
-## 1. Objective
+## Objective and implementation
 
-Make service state and failure responses visible, add predictor fallback, and demonstrate fault detection and recovery.
+Sprint 5 provides component health, service metrics, a separately addressable predictor, a review-required baseline fallback, provisioned Prometheus/Grafana monitoring, and controlled fault/recovery demonstrations.
 
-## 2. What now exists
+- API, worker, and predictor expose health and Prometheus metrics. `/api/health` reports `HEALTHY`, `DEGRADED`, or `OFFLINE` for the aggregate and its components. A stale decision-engine heartbeat while the simulator is paused degrades the pipeline without falsely marking the worker or simulator offline.
+- Worker requests the independent predictor through a bounded client/breaker. Predictor failure persists baseline forecasts with confidence capped at 0.4 and `needs_review=true`; fallback incidents and counters are visible. Recovery persists `source=remote` correctly.
+- SSE is advisory. A stream disconnect leaves REST polling available; reconnect is logged and refetches current state.
+- Prometheus scrapes the API, worker, and predictor. Grafana data source, dashboard, and alert rules are provisioned as code.
+- Smoke preflight checks Compose database credential alignment and the internal predictor URL without printing values. It accepts `--env-file` for public defaults.
+- Fault demo refuses a non-paused simulator or pre-existing active fault. It clears only faults it injects, restores services it stops, and verifies a paused, fault-free final state.
 
-- Predictor `POST /predict` validates a snapshot slice and returns shared-core forecast output. Worker uses a bounded remote client and a single-probe circuit breaker; fallback uses profile demand only, caps confidence at 0.4, and sets `needs_review`.
-- Predictor fallback creates/resolves an incident, emits a low-cardinality counter and structured log record, and continues to persist forecast results.
-- `/api/health` aggregates database, worker/simulator heartbeat and age, predictor ping, decision engine age, request p95, and observed API 5xx ratio. Frontend health view/banner and Grafana dashboard/alerts are provisioned.
-- Added integration coverage for unavailable/error-rate/latency-shaped ingestion failure, stale responses, malformed data, and a regression proving only one predictor half-open probe proceeds.
-- Added `scripts/fault_demo.sh`; runtime scenes were not executed.
+## Root causes and fixes
 
-## 3. Decisions
+1. SSE reconnection succeeded but was not verifiable in worker logs. Added structured connected/disconnected records at INFO and a test that confirms the logger is enabled. Live evidence shows a successful stream connection after fault clear without another worker restart.
+2. Predictor recovered and served HTTP 200, but forecast upsert did not replace the persisted source column. Added `source = EXCLUDED.source` and a regression test. The live script now asserts baseline/review-required forecasts during outage and remote forecasts after recovery.
+3. Local Compose settings differ from public defaults, but diagnostics risked requiring inspection of credentials. Added a redacted configuration validator and explicit `--env-file` support. The local `.env` was not edited.
+4. Fault demo assumed `pytest` was on PATH. It now uses configurable `PYTHON_BIN`; the final live run used the repository test interpreter.
 
-- Kept forecast/risk computation in shared pure core code and used a separate predictor HTTP boundary. Remote failure does not affect the recommendation feasibility validator.
-- Used a profile-only fallback with review required; no confidence higher than 0.4 is claimed for fallback forecasts.
-- The live fault script clears simulator faults on exit. It does not approve or submit recommendations.
+## Changed areas
 
-## 4. Key files
+`backend/worker/sse.py`, `backend/worker/store.py`, `scripts/fault_demo.sh`, `scripts/check_compose_env.py`, `scripts/smoke.sh`, related SSE/store/config tests, README setup guidance, `docs/resilience.md`, `docs/observability.md`, and this report.
 
-`backend/worker/forecaster.py`, `forecast_job.py`, `store.py`, `backend/api/routes/health.py`, `backend/api/routes/chaos.py`, `intel/predictor/app/main.py`, `web/src/features/system-health/`, `observability/grafana/provisioning/`, `scripts/fault_demo.sh`, and `tests/integration/test_resilience.py`.
+## Runtime evidence
 
-## 5. APIs
+See [complete live fault and recovery evidence](../evidence/sprint-05-fault-demo-accepted.txt), [Grafana event metric evidence](../evidence/sprint-05-grafana-event.txt), and [resilience matrix](../resilience.md).
 
-- `POST /predict`: validated forecast request to independent predictor.
-- `POST /api/chaos/forecast-fail`: token-protected predictor failure switch.
-- `GET /api/health`: database-backed component health and API latency/error summary.
+The simulator started PAUSED at tick 150 and ended PAUSED at tick 152. No allocation write or state reset occurred. All five simulator faults were detected and cleared; cached data degraded and recovered. Malformed response test passed (1 passed, 4 deselected). Predictor stop changed component/aggregate health to OFFLINE, generated 12 baseline forecasts at tick 151 (all requiring review, max confidence 0), and created a fallback incident. Predictor recovery restored HEALTHY and 12 remote forecasts at tick 152. Worker stop produced DEGRADED health and 19.2-second data age while API/frontend remained reachable; restart restored fresh ingestion. Prometheus showed three targets up; Grafana database health was `ok`, version 11.6.0, and a provisioned stockout-hours query moved 19.5 to 19.25 during a controlled demand-spike event.
 
-## 6. Verification
+## Verification
 
-| Check | Actual result | Status |
+| Check | Result | Status |
 |---|---|---|
-| Full Python suite | 123 passed; frontend Vitest 3 passed | PASS |
-| Frontend tests | 3 passed | PASS |
-| `make lint` | Ruff and format checks passed; TypeScript passed; Vite production build passed (500 modules) | PASS |
-| Compose config / `git diff --check` | Exit 0 | PASS |
-| Fault injection and recovery, five simulator faults | Docker socket unavailable; not run | NOT-RUN |
-| Predictor stop/fallback/recovery and worker stop | Docker socket unavailable; not run | NOT-RUN |
-| Grafana panels move during event/fault | Docker socket unavailable; not run | NOT-RUN |
-
-## 7. Evidence
-
-Local test/build output is recorded in `docs/evidence/sprint-05-runtime.md`. No new live runtime capture was produced. Historical Sprint 2 fault evidence is in `docs/evidence/sprint-02-runtime.md` and does not verify this Sprint 5 runtime.
-
-## 8. Problems and fixes
-
-The first new half-open breaker test failed because concurrent calls could all pass after reset. Added an async-lock-protected single-probe guard; full verification was rerun. Docker daemon unavailability prevented live acceptance checks.
-
-## 9. Not done / risks
-
-The fault demo, predictor-stop and recovery, worker-stop behavior, dashboard movement, and five-fault recovery are not demonstrated in this environment. The frontend image was not rebuilt. No live runtime pass is claimed.
-
-## 10. Next dependency
-
-Restore Docker and run the live resilience matrix on a dedicated demo stack. Confirm `PREDICTOR_URL` configuration without exposing `.env` values.
-
-## 11. Acceptance checklist
-
-- [x] Predictor endpoint, fallback, health UI, and dashboards implemented.
-- [x] Local resilience tests, lint, frontend tests/build, Compose config, and whitespace check passed.
-- [ ] Five simulator faults detected and recovered live — NOT-RUN.
-- [ ] Predictor stop/fallback/recovery and worker stop/data-age demonstrated — NOT-RUN.
-- [ ] Grafana panels move under injected conditions — NOT-RUN.
-- [ ] Sprint 5 gate passed — No; live runtime acceptance remains open.
-
-## 12. Five-minute update
-
-1. Problem: failures were not sufficiently visible and predictor failure needed a review-required path.
-2. Change: remote predictor, bounded breaker/fallback, health aggregation, UI banner, Grafana provisioning, tests and fault demo.
-3. Demo: not available while Docker daemon is offline; planned steps are in `docs/final-demo-script.md`.
-4. Evidence: 123 Python and 3 frontend tests; lint/typecheck/build and Compose config pass.
-5. Gap: current live fault, recovery, Grafana, and stop/restart evidence is absent.
-
-## Gate decision
-
-**Blocked.** Local checks pass. Live acceptance is NOT-RUN because Docker is unavailable.
+| `bash -n scripts/fault_demo.sh` | Exit 0 | PASS |
+| `PYTHON_BIN=/tmp/fuel-sprint1-venv/bin/python FAULT_SECONDS=60 WAIT_SECONDS=18 bash scripts/fault_demo.sh` | All simulator faults, malformed-data check, predictor fallback/recovery, worker stop/recovery passed; final PAUSED tick 152, faults clear and events resolved | PASS |
+| `python3 -m pytest -q tests/unit/test_compose_env_check.py` | 3 passed | PASS |
+| `python3 scripts/check_compose_env.py --env-file .env.example` | `PASS: database credentials and predictor URL match Compose services` | PASS |
+| Forecast source upsert regression | Focused store test passed; runtime tick 152 source remote for all 12 forecasts | PASS |
+| `make test`, `make lint`, frontend test/build | To be rerun after all current changes; results recorded in this gate section before commit | PENDING |
+| Docker Compose state | All eight services running and healthy after fault demo | PASS |
+| Prometheus/Grafana | Three targets up; Grafana health database ok; panel query moved with controlled event | PASS |
+| Grafana outbound notifications | SMTP not configured; delivery not attempted | DOCUMENTED LIMITATION |
+| `git diff --check`, Sprint 5 mechanical gate | To be run after final documentation updates | PENDING |
+
+An earlier attempt used the host Python without project dependencies and failed during test collection; a subsequent run using the project interpreter passed. Earlier run logs are preserved but are not counted as acceptance evidence.
+
+## Known limitations
+
+- Grafana alert rules are provisioned and evaluate, but outbound SMTP notification delivery is not configured or verified.
+- Local `.env` values do not match the public Compose defaults. They were not edited. The clean public `.env.example` configuration passes the redacted checker; local `make smoke` will fail preflight until the owner aligns local configuration.
+- Hosted GitHub Actions were not triggered in this environment.
+
+## Acceptance checklist
+
+- [x] API, worker, predictor metrics and aggregated health verified.
+- [x] Predictor service and review-required fallback verified live, including recovery to remote forecast persistence.
+- [x] Five simulator faults verified with detection and automatic recovery.
+- [x] Malformed-data rejection path verified.
+- [x] Worker outage and recovery verified without an API/frontend outage.
+- [x] Grafana provisioning and metric movement verified; SMTP limitation documented.
+- [ ] Full repository lint/test/build and mechanical gate results to be appended after final rerun.
+
+## Five-minute update
+
+1. Problem: operators needed visible failure states and forecasts that safely recover when the predictor is unavailable.
+2. Change: health aggregation, predictor fallback, structured SSE recovery logs, source-correct upserts, redacted Compose validation, dashboards, and fault demo.
+3. Demo: start the stack, open the dashboard and Grafana, then run `PYTHON_BIN=.venv/bin/python bash scripts/fault_demo.sh` with the simulator paused and no active faults.
+4. Evidence: [live fault transcript](../evidence/sprint-05-fault-demo-accepted.txt), [Grafana query](../evidence/sprint-05-grafana-event.txt), and [resilience matrix](../resilience.md).
+5. Gap: SMTP notifications and hosted CI remain unverified; local `.env` differs from public defaults and remains untouched.
diff --git a/scripts/fault_demo.sh b/scripts/fault_demo.sh
index 91dc0eb..1892e67 100644
--- a/scripts/fault_demo.sh
+++ b/scripts/fault_demo.sh
@@ -3,47 +3,241 @@ set -euo pipefail
 
 SIM_BASE_URL="${SIM_BASE_URL:-http://localhost:8000}"
 API_BASE_URL="${API_BASE_URL:-http://localhost:8101}"
-PREDICTOR_BASE_URL="${PREDICTOR_BASE_URL:-http://localhost:8103}"
-WAIT_SECONDS="${WAIT_SECONDS:-8}"
+WORKER_BASE_URL="${WORKER_BASE_URL:-http://localhost:8102}"
+FRONTEND_BASE_URL="${FRONTEND_BASE_URL:-http://localhost:5174}"
+PYTHON_BIN="${PYTHON_BIN:-python3}"
+FAULT_SECONDS="${FAULT_SECONDS:-60}"
+WAIT_SECONDS="${WAIT_SECONDS:-18}"
 fault_active=0
+predictor_stopped=0
+worker_stopped=0
 
 clear_fault() {
   if (( fault_active )); then
-    curl --fail --silent --show-error -X POST "$SIM_BASE_URL/admin/faults/clear" >/dev/null || true
+    curl --fail --silent --show-error -X POST "$SIM_BASE_URL/admin/faults/clear" >/dev/null
     fault_active=0
   fi
 }
-trap clear_fault EXIT INT TERM
+
+recover_services() {
+  if (( worker_stopped )); then
+    docker compose start worker >/dev/null
+    worker_stopped=0
+  fi
+  if (( predictor_stopped )); then
+    docker compose start predictor >/dev/null
+    predictor_stopped=0
+  fi
+}
+
+cleanup() {
+  clear_fault || true
+  recover_services || true
+}
+trap cleanup EXIT INT TERM
+
+require_paused_and_clean() {
+  python3 - "$SIM_BASE_URL" <<'PY'
+import json, sys, urllib.request
+base = sys.argv[1]
+def get(path):
+    with urllib.request.urlopen(base + path, timeout=5) as response:
+        return json.load(response)
+instance = get('/v1/instance')
+faults = get('/admin/faults')
+active = [fault.get('id') for fault in faults if fault.get('active')]
+if instance.get('status') != 'PAUSED':
+    raise SystemExit(f"simulator must be PAUSED; found {instance.get('status')}")
+if active:
+    raise SystemExit(f"refusing to run with pre-existing active faults: {active}")
+print(f"Preflight: PAUSED at tick {instance['tick']}; no active faults")
+PY
+}
+
+data_health() {
+  curl --fail --silent --show-error "$API_BASE_URL/api/data-health"
+}
+
+wait_for_data_recovery() {
+  local attempt payload
+  for attempt in $(seq 1 40); do
+    if payload=$(data_health 2>/dev/null) && python3 -c \
+      'import json,sys;x=json.load(sys.stdin);sys.exit(0 if x.get("data_status")=="HEALTHY" and not x.get("stale") else 1)' \
+      <<<"$payload"; then
+      echo "Recovery verified: $payload"
+      return 0
+    fi
+    sleep 1
+  done
+  echo "FAIL: snapshot did not recover within 40 seconds; last response: ${payload:-unavailable}" >&2
+  return 1
+}
+
+wait_for_stream_recovery() {
+  local since="$1" attempt logs
+  for attempt in $(seq 1 40); do
+    logs=$(docker compose logs --no-color --since "$since" worker 2>&1 || true)
+    if grep -q '"event": "simulator_stream_connected"' <<<"$logs"; then
+      grep '"event": "simulator_stream_connected"' <<<"$logs" | tail -1
+      echo "SSE recovery verified after fault clear without another worker restart."
+      return 0
+    fi
+    sleep 1
+  done
+  echo "FAIL: worker did not log successful SSE reconnection after clearing stream fault" >&2
+  return 1
+}
+
+fault_probe() {
+  local fault="$1" headers body status elapsed
+  headers=$(mktemp)
+  body=$(mktemp)
+  case "$fault" in
+    unavailable|error_rate)
+      status=$(curl --silent --show-error -o "$body" -w '%{http_code}' "$SIM_BASE_URL/v1/instance")
+      echo "Probe $fault: HTTP $status; response $(cat "$body")"
+      [[ "$status" == 503 ]]
+      ;;
+    latency)
+      elapsed=$(curl --silent --show-error --max-time 8 -o "$body" -w '%{time_total}' "$SIM_BASE_URL/v1/instance")
+      echo "Probe latency: HTTP response received in ${elapsed}s (fault injects 3500ms; client read timeout is 3s)"
+      python3 -c 'import sys;sys.exit(0 if float(sys.argv[1]) >= 3.0 else 1)' "$elapsed"
+      ;;
+    stale_data)
+      status=$(curl --silent --show-error -D "$headers" -o "$body" -w '%{http_code}' "$SIM_BASE_URL/v1/instance")
+      echo "Probe stale_data: HTTP $status; $(tr -d '\r' <"$headers" | grep -i '^x-simulator-stale:' || true)"
+      [[ "$status" == 200 ]] && tr -d '\r' <"$headers" | grep -qi '^x-simulator-stale: true'
+      ;;
+    stream_disconnect)
+      status=$(curl --silent --show-error --max-time 5 -N -D "$headers" -o "$body" -w '%{http_code}' "$SIM_BASE_URL/v1/stream" || true)
+      echo "Probe stream_disconnect: HTTP $status; response $(head -c 200 "$body")"
+      [[ "$status" == 503 ]]
+      ;;
+  esac
+  rm -f "$headers" "$body"
+}
 
 scene() {
-  local fault="$1" params="$2"
-  echo "Scene: $fault. Expected UI: simulator data health/banner reflects stale or degraded data; cached values remain visible."
+  local fault="$1" params="$2" fault_start=""
+  echo "Scene: $fault — expected: simulator-client failure/stale signal; cached state remains visible; no allocation write."
+  if [[ "$fault" == stream_disconnect ]]; then
+    docker compose stop worker >/dev/null
+    worker_stopped=1
+  fi
+  fault_start=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
+  fault_active=1
   curl --fail --silent --show-error -H 'Content-Type: application/json' \
-    -d "{\"type\":\"$fault\",\"duration_seconds\":30,\"parameters\":$params}" \
+    -d "{\"type\":\"$fault\",\"duration_seconds\":$FAULT_SECONDS,\"parameters\":$params}" \
     "$SIM_BASE_URL/admin/faults"
-  fault_active=1
+  echo
+  if [[ "$fault" == stream_disconnect ]]; then
+    docker compose start worker >/dev/null
+    worker_stopped=0
+  fi
+  fault_probe "$fault"
   sleep "$WAIT_SECONDS"
-  curl --silent --show-error "$API_BASE_URL/api/data-health" || true
+  echo "During $fault data-health: $(data_health)"
+  echo "During $fault worker signals:"
+  curl --fail --silent --show-error "$WORKER_BASE_URL/metrics" | grep -E '^(sim_client_retries_total|sim_client_failures_total|sim_breaker_state|snapshot_rejected_total|worker_sse_reconnects_total)' || true
   clear_fault
-  echo "Recovery requested for $fault; allow the worker to complete its next REST refresh."
+  echo "Cleared $fault; waiting for an accepted non-stale REST snapshot."
+  wait_for_data_recovery
+  if [[ "$fault" == stream_disconnect ]]; then
+    wait_for_stream_recovery "$fault_start"
+  fi
 }
 
+require_paused_and_clean
+
 for fault in unavailable error_rate latency stale_data stream_disconnect; do
   case "$fault" in
     error_rate) params='{"rate":1.0}' ;;
-    latency) params='{"delay_ms":500}' ;;
+    latency) params='{"delay_ms":3500}' ;;
     *) params='{}' ;;
   esac
   scene "$fault" "$params"
 done
 
-echo 'Scene: malformed simulator data. Use a test-only malformed response fixture; do not alter simulator state.'
-echo 'Expected UI: last good snapshot retained; snapshot rejection is logged and counted.'
-echo 'Automated malformed-data coverage: tests/integration/test_resilience.py'
+echo 'Scene: malformed simulator data — test-only malformed response; simulator state is unchanged.'
+"$PYTHON_BIN" -m pytest -q tests/integration/test_resilience.py -k malformed_data_fault
+
+echo 'Scene: predictor unavailable — expected baseline fallback, low confidence, incident and fallback metric.'
+before=$(curl --fail --silent --show-error "$WORKER_BASE_URL/metrics" | awk '/^policy_fallback_total/ {sum += $NF} END {print sum+0}')
+docker compose stop predictor >/dev/null
+predictor_stopped=1
+curl --silent --show-error "$API_BASE_URL/api/health"
+echo
+curl --fail --silent --show-error -H 'Content-Type: application/json' -X POST \
+  "$SIM_BASE_URL/admin/step" >/dev/null
+echo "Stepped simulator once to produce a new forecast input while predictor was stopped."
+sleep 8
+after=$(curl --fail --silent --show-error "$WORKER_BASE_URL/metrics" | awk '/^policy_fallback_total/ {sum += $NF} END {print sum+0}')
+echo "Predictor fallback counter before=$before after=$after"
+python3 -c 'import sys;sys.exit(0 if float(sys.argv[2]) > float(sys.argv[1]) else 1)' "$before" "$after"
+curl --fail --silent --show-error "$API_BASE_URL/api/risks" | python3 -c '
+import json,sys
+payload=json.load(sys.stdin); forecasts=payload["forecasts"]
+latest=max((item["tick"] for item in forecasts), default=-1)
+rows=[item for item in forecasts if item["tick"]==latest]
+if not rows or any(item["source"]!="baseline" or not item["needs_review"] or item["confidence"]>0.4 for item in rows):
+    raise SystemExit("FAIL: predictor outage did not persist review-required baseline forecasts")
+maximum=max(item["confidence"] for item in rows)
+print(f"Fallback verified: tick={latest}; forecasts={len(rows)}; source=baseline; all require review; max confidence={maximum:.3f}")
+'
+curl --fail --silent --show-error "$API_BASE_URL/api/events" | python3 -c '
+import json,sys
+payload=json.load(sys.stdin)
+if not any(item.get("type")=="predictor_fallback" and item.get("resolved_at") is None for item in payload.get("incidents", [])):
+    raise SystemExit("FAIL: active predictor fallback incident was not persisted")
+print("Predictor fallback incident verified in API.")
+'
+docker compose start predictor >/dev/null
+predictor_stopped=0
+sleep 11
+curl --fail --silent --show-error -X POST "$SIM_BASE_URL/admin/step" >/dev/null
+echo "Stepped simulator once after predictor recovery to produce a remote forecast input."
+sleep 8
+curl --fail --silent --show-error "$API_BASE_URL/api/health"
+echo
+curl --fail --silent --show-error "$API_BASE_URL/api/risks" | python3 -c '
+import json,sys
+payload=json.load(sys.stdin); forecasts=payload["forecasts"]
+latest=max((item["tick"] for item in forecasts), default=-1)
+rows=[item for item in forecasts if item["tick"]==latest]
+if not rows or any(item["source"]!="remote" for item in rows):
+    raise SystemExit("FAIL: predictor recovery did not replace persisted fallback forecasts with remote forecasts")
+print(f"Recovery verified: tick={latest}; forecasts={len(rows)}; source=remote")
+'
+
+echo 'Scene: worker unavailable — API and frontend remain reachable while snapshot age advances.'
+docker compose stop worker >/dev/null
+worker_stopped=1
+sleep 18
+curl --fail --silent --show-error "$API_BASE_URL/api/health"
+echo
+curl --fail --silent --show-error "$API_BASE_URL/api/data-health"
+echo
+curl --fail --silent --show-error "$FRONTEND_BASE_URL/" >/dev/null
+echo 'Frontend HTTP 200 while worker is stopped.'
+docker compose start worker >/dev/null
+worker_stopped=0
+wait_for_data_recovery
 
-echo 'Scene: predictor unavailable. Expected UI: review-required baseline forecast; fallback metric and incident increase.'
-if command -v docker >/dev/null 2>&1; then
-  echo 'Run `docker compose stop predictor`, observe /api/health and worker metrics, then `docker compose start predictor`.'
-else
-  echo 'Docker unavailable; skip predictor stop/recovery.'
-fi
+clear_fault
+python3 - "$SIM_BASE_URL" <<'PY'
+import json, sys, urllib.request
+base = sys.argv[1]
+with urllib.request.urlopen(base + '/admin/faults', timeout=5) as response:
+    active = [fault for fault in json.load(response) if fault.get('active')]
+with urllib.request.urlopen(base + '/admin/events', timeout=5) as response:
+    events = json.load(response)
+with urllib.request.urlopen(base + '/v1/instance', timeout=5) as response:
+    instance = json.load(response)
+if active:
+    raise SystemExit(f"active faults remain: {active}")
+if any(event.get('status') == 'ACTIVE' for event in events):
+    raise SystemExit('unresolved simulator events remain')
+if instance.get('status') != 'PAUSED':
+    raise SystemExit(f"simulator not paused: {instance.get('status')}")
+print(f"Final state: PAUSED tick {instance['tick']}; faults clear; events resolved")
+PY
diff --git a/scripts/smoke.sh b/scripts/smoke.sh
index 1a95938..e80522c 100644
--- a/scripts/smoke.sh
+++ b/scripts/smoke.sh
@@ -1,6 +1,8 @@
 #!/usr/bin/env bash
 set -euo pipefail
 
+python3 scripts/check_compose_env.py
+
 if [[ "${SMOKE_SKIP_BUILD:-0}" == "1" ]]; then
   docker compose up -d
 else
diff --git a/tests/integration/test_sse.py b/tests/integration/test_sse.py
index b4660ee..a36eb36 100644
--- a/tests/integration/test_sse.py
+++ b/tests/integration/test_sse.py
@@ -1,14 +1,20 @@
 from __future__ import annotations
 
+import logging
 from contextlib import asynccontextmanager
 from typing import Any
 
 import pytest
-from worker.sse import SSEConsumer
+from worker.sse import SSEConsumer, logger
 
 from core.sim_client import SimUnavailable
 
 
+def test_sse_connection_logs_are_enabled_at_info_level() -> None:
+    assert logger.isEnabledFor(logging.INFO)
+    assert logger.handlers
+
+
 class FakeClient:
     def __init__(self, streams: list[Any]) -> None:
         self.streams = streams
@@ -47,7 +53,8 @@ async def test_stream_event_refresh_is_rate_limited_and_keepalive_is_ignored() -
 
 
 @pytest.mark.asyncio
-async def test_reconnect_uses_backoff_and_refetches_after_successful_reconnect() -> None:
+async def test_reconnect_uses_backoff_and_refetches_after_successful_reconnect(caplog) -> None:
+    caplog.set_level(logging.INFO, logger="fuel_simulator.worker.sse")
     refreshes = 0
     delays: list[float] = []
 
@@ -69,3 +76,4 @@ async def test_reconnect_uses_backoff_and_refetches_after_successful_reconnect()
     assert client.connections == 2
     assert delays == [0.5]
     assert refreshes == 1
+    assert '"event": "simulator_stream_connected"' in caplog.text
diff --git a/tests/unit/test_store_snapshot.py b/tests/unit/test_store_snapshot.py
index 617d859..e8cd5ef 100644
--- a/tests/unit/test_store_snapshot.py
+++ b/tests/unit/test_store_snapshot.py
@@ -7,7 +7,8 @@ from typing import Any
 import pytest
 from worker.store import PostgresStore
 
-from core.models import DataStatus, Instance, Metrics, Snapshot
+from core.models import DataStatus, Forecast, FuelType, Instance, Metrics, RiskLevel, Snapshot
+from core.risk import ForecastRecord, TrajectoryPoint
 
 
 class FakeConnection:
@@ -18,9 +19,12 @@ class FakeConnection:
     async def transaction(self):
         yield
 
-    async def fetchval(self, query: str) -> int:
+    async def fetchval(self, query: str, *args: Any) -> int:
         return 134
 
+    async def fetch(self, query: str) -> list[Any]:
+        return []
+
     async def execute(self, query: str, *args: Any) -> str:
         self.executed.append((query, args))
         return "UPDATE 1"
@@ -80,3 +84,28 @@ async def test_same_tick_refresh_replaces_raw_payload_as_well_as_freshness_metad
     assert "raw_json = $" in query
     assert '"status":"PAUSED"' in args[1]
     assert args[0].year == 2026
+
+
+@pytest.mark.asyncio
+async def test_forecast_upsert_replaces_source_after_predictor_recovery() -> None:
+    connection = FakeConnection()
+    store = PostgresStore(FakePool(connection))  # type: ignore[arg-type]
+    forecast = Forecast(
+        station_id="station-mirpur",
+        fuel_type=FuelType.DIESEL,
+        hours_to_stockout=4,
+        p10_hours=3,
+        p50_hours=4,
+        p90_hours=5,
+        stockout_probability_24h=0.5,
+        confidence=0.9,
+        risk_level=RiskLevel.HIGH,
+        needs_review=False,
+    )
+    record = ForecastRecord(forecast, [TrajectoryPoint(0, 100, 90, 110)], {}, source="remote")
+
+    await store.persist_forecasts(snapshot("PAUSED"), [record])
+
+    query, args = next(row for row in connection.executed if "INSERT INTO forecasts" in row[0])
+    assert "source = EXCLUDED.source" in query
+    assert args[12] == "remote"

exec
/bin/zsh -lc "sed -n '1,240p' .local/prompts/REVIEW-PROMPTS.md && sed -n '1,260p' docs/resilience.md && cat docs/evidence/sprint-05-fault-demo-accepted.txt" in /Users/abrar/project/fuel_simulator
 succeeded in 0ms:
# Independent review prompts

Run these in a DIFFERENT tool from the one that wrote the code. The reviewer must not edit files unless asked. Use the code-review-strict skill. Paste COMMON-HEADER.md first.

## R1 Architecture and boundaries (after Sprint 2, 3, 5)
Read AGENTS.md, PROJECT_PLAN.md, docs/architecture.md and the actual code. Find boundary violations (API calling the simulator, impure functions in core/, I/O in forecast or policies), unnecessary complexity, duplicated logic, stale-data hazards, and docs that disagree with the code. Return findings ranked P0/P1/P2 with file and line and a minimal fix. Do not invent issues; do not edit files.

## R2 Simulator contract (after Sprint 2)
Compare core/sim_client.py, core/models.py and the tests with reference/ (the official guide), docs/sim-findings.md and live /docs responses. Check methods, paths, fields, stale header, SSE semantics, timeout and retry rules, the three error shapes, and idempotency. Return a contract matrix: verified, mismatch, unknown. Do not change code.

## R3 Allocation safety (after Sprint 4, mandatory)
Independently trace candidate generation, the validator, reservation accounting, pending and in-flight handling, approval, fresh-state re-validation, idempotency and execution. Try to find a path that can oversubscribe a depot or a route, submit twice, submit on stale data, submit without approval, or reuse a key with a different body. Return concrete failing test cases, severity and fixes. Do not modify code.

## R4 Resilience (after Sprint 5)
For each fault in the simulator (latency, unavailable, error_rate, stale_data, stream_disconnect), malformed data, predictor down and worker down, trace what the code does and what the operator sees. Find silent failures, retry storms, missing alerts and states that look healthy but are not. Return findings and test proposals.

## R5 Performance and load test (after Sprint 6)
Check the k6 script, the workload definition, thresholds, resource sampling and the reported numbers for honesty (single run, cherry-picked scenarios, missing error rate, testing the simulator instead of our API). Return findings.

## R6 Final release review (Sprint 7)
Inspect the diff, tests, CI, Docker, docs and demo evidence. Check for secrets, hard-coded fake live data, unsupported ML claims, missing tests, unverified success statements and incomplete sprint reports. Return release blockers, non-blocking issues and a go or no-go. Do not mark a test passed unless you ran it or inspected trustworthy output.
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
- The local `.env` contains values that differ from the public Compose defaults. It was left untouched. The safe configuration check passes with `.env.example` and reports the local mismatch by variable name only, without printing values. Run `python3 scripts/check_compose_env.py --env-file .env.example` to check clean-clone defaults.
- Grafana dashboards and alert rules are provisioned and evaluate locally. Email delivery is not configured (Grafana logs report SMTP is unconfigured), so notification delivery is not verified.
- Fault durations are bounded and the script does not clear unrelated/pre-existing faults; it refuses to start if any are active.
Preflight: PAUSED at tick 150; no active faults
Scene: unavailable — expected: simulator-client failure/stale signal; cached state remains visible; no allocation write.
{"id":36,"type":"unavailable","start_wall_time":"2026-11-20T10:36:12.393445+00:00","end_wall_time":"2026-11-20T10:37:12.393445+00:00","active":true,"parameters":{}}
Probe unavailable: HTTP 503; response {"error":{"code":"FAULT_INJECTED","message":"Simulator API temporarily unavailable."}}
During unavailable data-health: {"fetched_at":"2026-11-20T10:36:07.725111+00:00","data_age_seconds":22.734151,"data_status":"DEGRADED","stale":false,"simulated":true}
During unavailable worker signals:
sim_client_retries_total{endpoint="/v1/instance"} 6.0
sim_client_retries_total{endpoint="/v1/regions"} 3.0
sim_client_retries_total{endpoint="/v1/routes"} 3.0
sim_client_retries_total{endpoint="/v1/allocations"} 3.0
sim_client_retries_total{endpoint="/v1/stations"} 3.0
sim_client_retries_total{endpoint="/v1/supply-arrivals"} 3.0
sim_client_retries_total{endpoint="/v1/metrics"} 3.0
sim_client_retries_total{endpoint="/v1/events"} 3.0
sim_client_retries_total{endpoint="/v1/depots"} 3.0
sim_client_failures_total{endpoint="/v1/stream"} 6.0
sim_client_failures_total{endpoint="/v1/depots"} 1.0
sim_client_failures_total{endpoint="/v1/allocations"} 1.0
sim_client_failures_total{endpoint="/v1/metrics"} 1.0
sim_client_failures_total{endpoint="/v1/routes"} 1.0
sim_client_failures_total{endpoint="/v1/regions"} 1.0
sim_client_failures_total{endpoint="/v1/instance"} 2.0
sim_client_failures_total{endpoint="/v1/stations"} 1.0
sim_client_failures_total{endpoint="/v1/supply-arrivals"} 1.0
sim_client_failures_total{endpoint="/v1/events"} 1.0
sim_breaker_state{state="closed"} 0.0
sim_breaker_state{state="open"} 1.0
sim_breaker_state{state="half_open"} 0.0
snapshot_rejected_total{reason="SimUnavailable"} 4.0
worker_sse_reconnects_total 7.0
Cleared unavailable; waiting for an accepted non-stale REST snapshot.
Recovery verified: {"fetched_at":"2026-11-20T10:36:47.771565+00:00","data_age_seconds":0.325405,"data_status":"HEALTHY","stale":false,"simulated":true}
Scene: error_rate — expected: simulator-client failure/stale signal; cached state remains visible; no allocation write.
{"id":37,"type":"error_rate","start_wall_time":"2026-11-20T10:36:48.180057+00:00","end_wall_time":"2026-11-20T10:37:48.180057+00:00","active":true,"parameters":{"rate":1.0}}
Probe error_rate: HTTP 503; response {"error":{"code":"FAULT_INJECTED","message":"Injected transient API error."}}
During error_rate data-health: {"fetched_at":"2026-11-20T10:36:47.771565+00:00","data_age_seconds":18.49511,"data_status":"DEGRADED","stale":false,"simulated":true}
During error_rate worker signals:
sim_client_retries_total{endpoint="/v1/instance"} 9.0
sim_client_retries_total{endpoint="/v1/regions"} 6.0
sim_client_retries_total{endpoint="/v1/routes"} 6.0
sim_client_retries_total{endpoint="/v1/allocations"} 6.0
sim_client_retries_total{endpoint="/v1/stations"} 6.0
sim_client_retries_total{endpoint="/v1/supply-arrivals"} 6.0
sim_client_retries_total{endpoint="/v1/metrics"} 6.0
sim_client_retries_total{endpoint="/v1/events"} 6.0
sim_client_retries_total{endpoint="/v1/depots"} 6.0
sim_client_failures_total{endpoint="/v1/stream"} 6.0
sim_client_failures_total{endpoint="/v1/depots"} 2.0
sim_client_failures_total{endpoint="/v1/allocations"} 2.0
sim_client_failures_total{endpoint="/v1/metrics"} 2.0
sim_client_failures_total{endpoint="/v1/routes"} 2.0
sim_client_failures_total{endpoint="/v1/regions"} 2.0
sim_client_failures_total{endpoint="/v1/instance"} 3.0
sim_client_failures_total{endpoint="/v1/stations"} 2.0
sim_client_failures_total{endpoint="/v1/supply-arrivals"} 2.0
sim_client_failures_total{endpoint="/v1/events"} 2.0
sim_breaker_state{state="closed"} 0.0
sim_breaker_state{state="open"} 1.0
sim_breaker_state{state="half_open"} 0.0
snapshot_rejected_total{reason="SimUnavailable"} 10.0
worker_sse_reconnects_total 7.0
Cleared error_rate; waiting for an accepted non-stale REST snapshot.
Recovery verified: {"fetched_at":"2026-11-20T10:37:12.804264+00:00","data_age_seconds":0.123234,"data_status":"HEALTHY","stale":false,"simulated":true}
Scene: latency — expected: simulator-client failure/stale signal; cached state remains visible; no allocation write.
{"id":38,"type":"latency","start_wall_time":"2026-11-20T10:37:12.998335+00:00","end_wall_time":"2026-11-20T10:38:12.998335+00:00","active":true,"parameters":{"delay_ms":3500}}
Probe latency: HTTP response received in 3.514714s (fault injects 3500ms; client read timeout is 3s)
During latency data-health: {"fetched_at":"2026-11-20T10:37:12.804264+00:00","data_age_seconds":21.845083,"data_status":"DEGRADED","stale":false,"simulated":true}
During latency worker signals:
sim_client_retries_total{endpoint="/v1/instance"} 12.0
sim_client_retries_total{endpoint="/v1/regions"} 9.0
sim_client_retries_total{endpoint="/v1/routes"} 9.0
sim_client_retries_total{endpoint="/v1/allocations"} 9.0
sim_client_retries_total{endpoint="/v1/stations"} 9.0
sim_client_retries_total{endpoint="/v1/supply-arrivals"} 9.0
sim_client_retries_total{endpoint="/v1/metrics"} 9.0
sim_client_retries_total{endpoint="/v1/events"} 9.0
sim_client_retries_total{endpoint="/v1/depots"} 9.0
sim_client_failures_total{endpoint="/v1/stream"} 6.0
sim_client_failures_total{endpoint="/v1/depots"} 3.0
sim_client_failures_total{endpoint="/v1/allocations"} 3.0
sim_client_failures_total{endpoint="/v1/metrics"} 3.0
sim_client_failures_total{endpoint="/v1/routes"} 3.0
sim_client_failures_total{endpoint="/v1/regions"} 3.0
sim_client_failures_total{endpoint="/v1/instance"} 4.0
sim_client_failures_total{endpoint="/v1/stations"} 3.0
sim_client_failures_total{endpoint="/v1/supply-arrivals"} 3.0
sim_client_failures_total{endpoint="/v1/events"} 3.0
sim_breaker_state{state="closed"} 0.0
sim_breaker_state{state="open"} 1.0
sim_breaker_state{state="half_open"} 0.0
snapshot_rejected_total{reason="SimUnavailable"} 12.0
worker_sse_reconnects_total 7.0
Cleared latency; waiting for an accepted non-stale REST snapshot.
Recovery verified: {"fetched_at":"2026-11-20T10:37:35.295955+00:00","data_age_seconds":0.522533,"data_status":"HEALTHY","stale":false,"simulated":true}
Scene: stale_data — expected: simulator-client failure/stale signal; cached state remains visible; no allocation write.
{"id":39,"type":"stale_data","start_wall_time":"2026-11-20T10:37:35.900721+00:00","end_wall_time":"2026-11-20T10:38:35.900721+00:00","active":true,"parameters":{}}
Probe stale_data: HTTP 200; x-simulator-stale: true
During stale_data data-health: {"fetched_at":"2026-11-20T10:37:51.930691+00:00","data_age_seconds":2.06242,"data_status":"DEGRADED","stale":true,"simulated":true}
During stale_data worker signals:
sim_client_retries_total{endpoint="/v1/instance"} 13.0
sim_client_retries_total{endpoint="/v1/regions"} 10.0
sim_client_retries_total{endpoint="/v1/routes"} 10.0
sim_client_retries_total{endpoint="/v1/allocations"} 10.0
sim_client_retries_total{endpoint="/v1/stations"} 10.0
sim_client_retries_total{endpoint="/v1/supply-arrivals"} 10.0
sim_client_retries_total{endpoint="/v1/metrics"} 10.0
sim_client_retries_total{endpoint="/v1/events"} 10.0
sim_client_retries_total{endpoint="/v1/depots"} 10.0
sim_client_failures_total{endpoint="/v1/stream"} 6.0
sim_client_failures_total{endpoint="/v1/depots"} 3.0
sim_client_failures_total{endpoint="/v1/allocations"} 3.0
sim_client_failures_total{endpoint="/v1/metrics"} 3.0
sim_client_failures_total{endpoint="/v1/routes"} 3.0
sim_client_failures_total{endpoint="/v1/regions"} 3.0
sim_client_failures_total{endpoint="/v1/instance"} 4.0
sim_client_failures_total{endpoint="/v1/stations"} 3.0
sim_client_failures_total{endpoint="/v1/supply-arrivals"} 3.0
sim_client_failures_total{endpoint="/v1/events"} 3.0
sim_breaker_state{state="closed"} 1.0
sim_breaker_state{state="open"} 0.0
sim_breaker_state{state="half_open"} 0.0
snapshot_rejected_total{reason="SimUnavailable"} 12.0
worker_sse_reconnects_total 7.0
Cleared stale_data; waiting for an accepted non-stale REST snapshot.
Recovery verified: {"fetched_at":"2026-11-20T10:37:56.932477+00:00","data_age_seconds":0.417448,"data_status":"HEALTHY","stale":false,"simulated":true}
Scene: stream_disconnect — expected: simulator-client failure/stale signal; cached state remains visible; no allocation write.
 Container fuel_simulator-worker-1 Stopping 
 Container fuel_simulator-worker-1 Stopped 
{"id":40,"type":"stream_disconnect","start_wall_time":"2026-11-20T10:37:58.056275+00:00","end_wall_time":"2026-11-20T10:38:58.056275+00:00","active":true,"parameters":{}}
 Container fuel_simulator-simulator-1 Waiting 
 Container fuel_simulator-postgres-1 Waiting 
 Container fuel_simulator-simulator-1 Healthy 
 Container fuel_simulator-postgres-1 Healthy 
 Container fuel_simulator-worker-1 Starting 
 Container fuel_simulator-worker-1 Started 
Probe stream_disconnect: HTTP 503; response {"detail":{"code":"FAULT_INJECTED"}}
During stream_disconnect data-health: {"fetched_at":"2026-11-20T10:38:14.989270+00:00","data_age_seconds":1.8666,"data_status":"HEALTHY","stale":false,"simulated":true}
During stream_disconnect worker signals:
sim_client_failures_total{endpoint="/v1/stream"} 6.0
sim_breaker_state{state="closed"} 1.0
sim_breaker_state{state="open"} 0.0
sim_breaker_state{state="half_open"} 0.0
worker_sse_reconnects_total 6.0
Cleared stream_disconnect; waiting for an accepted non-stale REST snapshot.
Recovery verified: {"fetched_at":"2026-11-20T10:38:14.989270+00:00","data_age_seconds":1.943899,"data_status":"HEALTHY","stale":false,"simulated":true}
worker-1  | {"timestamp": "2026-11-20T10:38:31.518589+00:00", "level": "info", "service": "worker", "event": "simulator_stream_connected", "tick": null, "correlation_id": null}
SSE recovery verified after fault clear without another worker restart.
Scene: malformed simulator data — test-only malformed response; simulator state is unchanged.
.                                                                        [100%]
1 passed, 4 deselected in 0.24s
Scene: predictor unavailable — expected baseline fallback, low confidence, incident and fallback metric.
 Container fuel_simulator-predictor-1 Stopping 
 Container fuel_simulator-predictor-1 Stopped 
{"status":"OFFLINE","components":{"backend":{"status":"HEALTHY","age_seconds":0.0},"predictor":{"status":"OFFLINE","age_seconds":null},"database":{"status":"HEALTHY","age_seconds":null},"worker":{"status":"HEALTHY","age_seconds":1.354286},"simulator":{"status":"HEALTHY","age_seconds":1.362428},"decision_engine":{"status":"DEGRADED","age_seconds":33.072965}},"last_check_at":"2026-11-20T10:38:32.926128+00:00","latency":{"p95_seconds":0.05,"error_rate":0.0},"simulated":true}
Stepped simulator once to produce a new forecast input while predictor was stopped.
Predictor fallback counter before=0 after=12
Fallback verified: tick=151; forecasts=12; source=baseline; all require review; max confidence=0.000
Predictor fallback incident verified in API.
 Container fuel_simulator-predictor-1 Starting 
 Container fuel_simulator-predictor-1 Started 
Stepped simulator once after predictor recovery to produce a remote forecast input.
{"status":"HEALTHY","components":{"backend":{"status":"HEALTHY","age_seconds":0.0},"predictor":{"status":"HEALTHY","age_seconds":null},"database":{"status":"HEALTHY","age_seconds":null},"worker":{"status":"HEALTHY","age_seconds":0.48694},"simulator":{"status":"HEALTHY","age_seconds":0.49411},"decision_engine":{"status":"HEALTHY","age_seconds":7.90004}},"last_check_at":"2026-11-20T10:39:00.505038+00:00","latency":{"p95_seconds":0.05,"error_rate":0.0},"simulated":true}
Recovery verified: tick=152; forecasts=12; source=remote
Scene: worker unavailable — API and frontend remain reachable while snapshot age advances.
 Container fuel_simulator-worker-1 Stopping 
 Container fuel_simulator-worker-1 Stopped 
{"status":"DEGRADED","components":{"backend":{"status":"HEALTHY","age_seconds":0.0},"predictor":{"status":"HEALTHY","age_seconds":null},"database":{"status":"HEALTHY","age_seconds":null},"worker":{"status":"DEGRADED","age_seconds":19.174445},"simulator":{"status":"DEGRADED","age_seconds":19.181911},"decision_engine":{"status":"DEGRADED","age_seconds":26.588671}},"last_check_at":"2026-11-20T10:39:19.193892+00:00","latency":{"p95_seconds":0.05,"error_rate":0.0},"simulated":true}
{"fetched_at":"2026-11-20T10:39:00.042484+00:00","data_age_seconds":19.210177,"data_status":"DEGRADED","stale":false,"simulated":true}
Frontend HTTP 200 while worker is stopped.
 Container fuel_simulator-simulator-1 Waiting 
 Container fuel_simulator-postgres-1 Waiting 
 Container fuel_simulator-simulator-1 Healthy 
 Container fuel_simulator-postgres-1 Healthy 
 Container fuel_simulator-worker-1 Starting 
 Container fuel_simulator-worker-1 Started 
Recovery verified: {"fetched_at":"2026-11-20T10:39:21.026582+00:00","data_age_seconds":0.065828,"data_status":"HEALTHY","stale":false,"simulated":true}
Final state: PAUSED tick 152; faults clear; events resolved

exec
/bin/zsh -lc "cat .local/prompts/COMMON-HEADER.md && rg --files backend tests frontend | sort | rg '(health|sim_client|sse|forecast|predict|worker|snapshot|resilien|metrics|alert)'" in /Users/abrar/project/fuel_simulator
 succeeded in 0ms:
# Common header: paste this FIRST in every agent session, then the sprint prompt (or one work package)

You are an engineering agent on the BUP CSE FEST 2026 Fuel Supply Intelligence & Resilience Platform.

THIS IS ONE REPOSITORY BUILT IN PARTS. Do not create a new project. Do not scaffold over existing code. Do not redo earlier sprints. Extend what exists.

Before anything else:
1. Read AGENTS.md, docs/PROGRESS.md, docs/decisions.md and PROJECT_PLAN.md, then the sprint prompt below.
2. Inspect git log, the current branch and the working tree. Check what code and tests already exist.
3. Use the project skills that apply (names are listed in AGENTS.md). If you cannot load skills, read .agents/skills/<name>/SKILL.md directly.

Then:
4. State a plan (at most 10 lines) and the files you will touch. Wait for my OK.
5. Implement in small vertical slices with tests. Run make lint and make test (or the closest available commands) and show real output.
6. Do not start the next sprint or work outside the current scope.
7. If anything conflicts with the official brief, the simulator guide or the live simulator, stop and tell me instead of guessing.
8. At the end report: files changed, commands run with results, what is verified, what is not, and open questions.
rg: frontend: No such file or directory (os error 2)
backend/api/routes/health.py
backend/shared/core/forecast.py
backend/shared/core/metrics.py
backend/shared/core/sim_client.py
backend/worker/Dockerfile
backend/worker/__init__.py
backend/worker/executor.py
backend/worker/forecast_job.py
backend/worker/forecaster.py
backend/worker/ingest.py
backend/worker/main.py
backend/worker/recommend_job.py
backend/worker/sse.py
backend/worker/store.py
tests/integration/test_health_api.py
tests/integration/test_predictor.py
tests/integration/test_resilience.py
tests/integration/test_sim_client.py
tests/integration/test_sse.py
tests/unit/test_forecast.py
tests/unit/test_forecast_job.py
tests/unit/test_store_snapshot.py

codex
The R4 evidence records all eight scenarios and recovery, including the actual operator health/data-health responses. I’m now checking whether those observations match the implementation paths and tests, especially whether degradation is surfaced soon enough and whether retry/breaker behavior is bounded under overlapping failures.
exec
/bin/zsh -lc "cat docs/decisions.md && cat PROJECT_PLAN.md && git log -5 --oneline --decorate && git status --short --branch && rg --files | rg '("'^|/)(src|frontend|web|ui)/|health|alerts|dashboard|resilience'"'" in /Users/abrar/project/fuel_simulator
 succeeded in 0ms:
# Decision log (ADR style). Add an entry when a decision is made. Template: docs/templates/adr.md

Statuses: PROPOSED, ACCEPTED, SUPERSEDED.

| ID | Decision | Status | Sprint |
|---|---|---|---|
| ADR-001 | REST is truth; SSE is only a hint to refetch | PROPOSED | 1 |
| ADR-002 | Worker owns simulator I/O; API reads the database only | PROPOSED | 1 |
| ADR-003 | Heuristic allocation first; optimizer only if time remains | PROPOSED | 1 |
| ADR-004 | Monte Carlo for stockout uncertainty | PROPOSED | 3 |
| ADR-005 | Outbox-style executor: approve records intent, executor re-validates and submits | ACCEPTED | 4 |
| ADR-006 | Idempotency key rec-<uuid>, stored, reused only for the identical body | ACCEPTED | 4 |
| ADR-007 | Predictor as its own container with baseline fallback | PROPOSED | 5 |
| ADR-008 | No Kubernetes or RL; Docker Compose only | PROPOSED | 1 |
| ADR-009 | Operator token from env protects approve, reject and chaos endpoints | ACCEPTED | 4 |
| ADR-010 | Co-host API and worker in one application container while preserving the DB-only API / worker-I/O boundary | SUPERSEDED | 1 |
| ADR-011 | Defer predictor and Prometheus/Grafana containers until their sprint; retain predictor separation for the outage demo | SUPERSEDED | 1 |
| ADR-012 | Treat minimum operator-visible metrics, logs, and one meaningful load-test report as core deliverables; Grafana polish remains P1 | ACCEPTED | 1 |
| ADR-013 | Follow Sprint 1's separate API, worker, predictor, frontend, Prometheus and Grafana Compose topology | ACCEPTED | 1 |
| ADR-014 | Keep frontend host port configurable with 5173 as the default | ACCEPTED | 1 |
| ADR-015 | Use TanStack Query for overview polling and Tailwind for the Sprint 2 frontend | ACCEPTED | 2 |
| ADR-016 | Allow repeated simulator ticks across reset cycles; skip only an unchanged latest tick | ACCEPTED | 2 |
| ADR-017 | Mark cached state degraded immediately on ingestion failure and refresh same-tick status on recovery | ACCEPTED | 2 |
| ADR-018 | Use Recharts for the Sprint 3 forecast trajectory band | ACCEPTED | 3 |
| ADR-019 | Project only known station allocation arrivals; do not infer future depot-to-station dispatches | ACCEPTED | 3 |
| ADR-020 | Separate demand forecast recovery from inventory recovery after demand events | ACCEPTED | 3 |
| ADR-021 | Organize application source by runtime responsibility while preserving independent services | ACCEPTED | Publication |
| ADR-022 | Keep personal AI workspace local and publish application/engineering artifacts only | ACCEPTED | Publication |
| ADR-023 | Use feature-based React modules with shared transport, types and UI components | ACCEPTED | Publication |
| ADR-024 | Set a separate SSE read timeout above the simulator's 15s keepalive interval | ACCEPTED | 2 |

## Entries
(Add full entries below as decisions are made.)

### ADR-005 — Persist approval intent before simulator execution

- **Status:** ACCEPTED
- **Context:** Approval and simulator I/O have different failure and security boundaries. The API is a database-only read path except for recording operator decisions; worker owns all simulator traffic.
- **Decision:** Approve/reject updates the recommendation and decision log in a database transaction. The worker polls approved rows, fetches a fresh simulator snapshot, checks freshness, validates again, and then submits the stored request. An ambiguous transport failure leaves the recommendation SUBMITTED so the executor can retry safely.
- **Trade-off:** An approved item may remain pending during simulator outage; the UI shows its progression and errors.

### ADR-006 — Bind permanent idempotency keys to exact request bodies

- **Status:** ACCEPTED
- **Context:** Simulator keys are permanent. An uncertain POST result must be replayable without creating a second allocation, and the same key cannot be reused for a changed request.
- **Decision:** Generate and persist one `rec-<uuid>` key and the exact JSON body when creating a recommendation. Retry with that body only. A fresh simulator read may match an existing allocation by key only after verifying every allocation term; a key with a different body fails closed locally before any POST.
- **Trade-off:** If stored request data is inconsistent, execution requires operator investigation rather than attempting repair or inventing a new key.

### ADR-009 — Protect operator decisions with an environment token

- **Status:** ACCEPTED
- **Context:** The browser exposes approve and reject actions, but the UI must not persist operator credentials or call simulator write endpoints.
- **Decision:** Require `X-Operator-Token` sourced from `OPERATOR_TOKEN` for API decision routes. Keep the token in React memory only; API writes local decision state and worker performs simulator I/O.
- **Trade-off:** Reloading the page requires entering the token again.

### ADR-010 — Co-host API and worker in one application container

- **Status:** SUPERSEDED by ADR-013
- **Context:** The 28-hour plan calls for a usable API, background ingestion and execution, database, UI, simulator, predictor, and monitoring stack. Separate API and worker containers add orchestration and health-check work during the foundation sprint.
- **Proposal:** Keep API routes database-only and keep all simulator calls inside a worker module, but run the worker as a managed background task in the same application container. Preserve clear module boundaries and worker heartbeat/status. This saves one container while retaining the hard I/O ownership rule.
- **Trade-off:** API and worker process failures become coupled; a later split can happen only if the demo shows a concrete need.

### ADR-011 — Stage optional service containers

- **Status:** SUPERSEDED by ADR-013
- **Context:** Building and validating all eight planned containers in Sprint 1 consumes time before the core operator workflow exists.
- **Proposal:** Sprint 1 brings up only the simulator, database, combined application service, and UI. Add the separate predictor in Sprint 5 to demonstrate predictor failure and fallback. Add Prometheus and Grafana in Sprint 5 after core workflow metrics and logs exist.
- **Trade-off:** Monitoring dashboards and predictor-failure demonstration arrive later, but do not block the live data, risk, recommendation, approval, and safe-submit path.

### ADR-012 — Core delivery priority for observability and load evidence

- **Status:** ACCEPTED
- **Context:** The participant brief calls for meaningful observability and requires a load test with reported measurements. The current project plan labels metrics/Grafana and load testing P1, which could leave required evidence until after the core time budget.
- **Proposal:** Keep low-cardinality metrics and structured logs on each implemented behavior, plus one measured load-test path and honest report, in the 28-hour core. Keep Grafana panels, broad multi-scenario load runs, and dashboard polish P1.
- **Trade-off:** Protect evidence for brief requirements while limiting monitoring infrastructure and benchmark scope.

### ADR-013 — Follow the separate-service Sprint 1 topology

- **Status:** ACCEPTED
- **Context:** The Sprint 1 specification explicitly requires separate API, worker, predictor, frontend, Prometheus, and Grafana services. That supersedes the earlier bootstrap proposals to co-host services or defer containers.
- **Decision:** Implement the specified services in Docker Compose, with PostgreSQL and the official simulator. Keep service code minimal in Sprint 1 and preserve the API-read/worker-I/O boundary.
- **Trade-off:** More startup and image-build work now; separate process health and the predictor outage demonstration are available without a later topology change.

### ADR-014 — Keep frontend host port configurable with 5173 as the default

- **Status:** ACCEPTED
- **Context:** An unrelated existing container may already bind the conventional frontend host port, which prevented Compose from starting the frontend and Grafana health chain in this environment.
- **Decision:** Publish the frontend on `FRONTEND_HOST_PORT` with a default of 5173, and have the smoke script read the resolved port from Compose config. Operators can select a free port without stopping other services.
- **Trade-off:** When changing the frontend port, set `CORS_ORIGIN` to the matching browser origin for API calls.

## Sprint 1 verification note — 2026-11-19

The live image was available and all unresolved findings were probed except replay after source-inventory exhaustion. Guide-derived `allocation-pending.json` and `depot-detail.json` remain clearly identified as contract fixtures; the canonical endpoint samples are live captures. Sprint 1 passed local validation with the frontend port set to 5174 because an unrelated running container owns 5173. The hosted GitHub workflow was not triggered; its individual local checks passed, and image builds completed during `docker compose up --build`.

### ADR-015 — Use TanStack Query and Tailwind for the Sprint 2 overview

- **Status:** ACCEPTED
- **Context:** Sprint 2 requires three-second query polling and a React/Tailwind operator overview that keeps the last successful state when requests fail.
- **Decision:** Add TanStack Query for polling/cache state and Tailwind's Vite plugin for the frontend utility CSS layer. Keep the custom CSS for the dashboard's visual components.
- **Trade-off:** Two frontend packages are added to satisfy the Sprint 2 UI requirements; no component library is added.

### ADR-016 — Permit tick reuse after simulator reset

- **Status:** ACCEPTED
- **Context:** The Sprint 1 snapshots schema made `tick` globally unique, but the simulator's `/admin/reset` returns to tick zero. That would prevent history from recording later reset cycles.
- **Decision:** Skip insertion only when the newest stored snapshot has the same tick. Keep tick indexed but not unique, and drop the old unique constraint idempotently on worker startup.
- **Trade-off:** Snapshot history can contain repeated ticks across reset cycles; consumers select by fetch time and row ID.

### ADR-017 — Update cached freshness state without replacing good data

- **Status:** ACCEPTED
- **Context:** The dashboard must show degraded status within 10 seconds of simulator unavailability and recover when the simulator returns, including when it remains paused at the same tick.
- **Decision:** On an ingestion failure, update only the newest snapshot's data status to `DEGRADED`, retain its raw contents, and record the integration event. A later successful fetch at the same tick refreshes fetch time, stale marker, and status in place instead of inserting a duplicate snapshot.
- **Trade-off:** Same-tick rows represent the latest validated contents for that tick while preserving the original snapshot row count; event and incident history remains separate.

### ADR-018 — Use Recharts for the forecast trajectory

- **Status:** ACCEPTED
- **Context:** Sprint 3 explicitly requires a drill-down area chart showing projected inventory and its P10/P90 uncertainty band.
- **Decision:** Add Recharts for the forecast drawer chart; keep the overview and risk matrix in the existing React/Tailwind components.
- **Trade-off:** Adds a focused charting dependency and bundle weight to support the uncertainty view; no broader UI framework is introduced.

### ADR-019 — Keep station projections grounded in known allocations

- **Status:** ACCEPTED
- **Context:** The simulator guide distinguishes depot `SupplyArrival` schedules from station allocations. Its `shipment_delay` event changes scheduled depot arrival ticks, while the Sprint 3 projection models station on-hand stock and known station allocation arrivals.
- **Decision:** Only include pending/in-transit station allocations in station inventory projections. Do not synthesize future allocations from depot supply schedules. A shipment delay may change a downstream station forecast only when a known station allocation arrival actually depends on that supply; this implementation does not model such a dependency.
- **Decision detail:** A new recommendation's estimate uses the current simulator tick plus route transit duration, matching the observed simulator behavior where a worker-submitted allocation departs on the current tick. For already-pending station allocations, projected arrival is next-tick departure plus the route's known transit duration; for in-transit allocations, use the simulator's `expected_arrival_tick`. Depot `SupplyArrival` timing is shown as depot supply context only; scheduled or in-transit depot stock is never station on-hand inventory.
- **Verification correction (2026-11-20):** The authorized live allocation was submitted at tick 134 on a 3-tick route and the simulator reported `expected_arrival_tick=137` and `ARRIVED` at tick 137. The prior proposal estimate of 138 was one tick late. Heuristic recommendation ETA now matches current-tick dispatch semantics; already-pending projection behavior remains unchanged.
- **Trade-off:** The forecast remains physically grounded and does not predict human dispatch decisions. An unrelated delayed depot shipment changes no station risk.

### ADR-020 — Distinguish demand forecast recovery from inventory recovery

- **Status:** ACCEPTED
- **Context:** The simulator removes the `demand_spike` multiplier when an event resolves, but it does not restore fuel consumed during the event.
- **Decision:** While active, forecast demand reflects the elevated station multiplier. After resolution, the multiplier returns to normal and expected demand moves toward baseline (the EWMA may retain observed effects until later observations arrive). Keep consumed inventory depleted and recalculate risk from that remaining inventory under normal demand. Do not expect original stockout hours to return automatically.
- **Trade-off:** This reports both the recovery in demand rate and the persistent loss of inventory instead of implying the station has been replenished.

## Sprint 3 live event evidence — 2026-11-19

The live `demand_spike` x1.8 event on `region-dhaka` reduced Mirpur DIESEL from 2.5h to 1.0h and Tongi OCTANE from 11.5h to 6.5h at tick 104. After resolution at tick 108, both multipliers returned to 1.0, but Mirpur DIESEL was 0h because fuel consumed during the event is not restored; Tongi OCTANE was 7.0h. The live `shipment_delay` moved depot supply `supply-201` from tick 128 to 133; no dependent station allocation existed, so station risk did not change. The Sprint 3 acceptance criteria now explicitly distinguish demand normalization from inventory replenishment and require only the depot ETA change for an unrelated delayed arrival.

### ADR-021 — Organize source by runtime responsibility

- **Status:** ACCEPTED
- **Context:** The application had implemented APIs, worker jobs, shared domain logic, predictor, frontend, and monitoring, but the root directory grouped them inconsistently. The project needs a clear public repository layout without a second application or changes to simulator behavior.
- **Decision:** Place API, worker, and shared core under `backend/`; predictor under `intel/predictor/`; React application under `web/`; and monitoring configuration under `observability/`. Keep API, worker, predictor, frontend, Prometheus, and Grafana independently addressable Compose services. Move tests into unit, integration, scenario, and frontend test locations, updating imports and build contexts.
- **Trade-off:** Docker, Python, CI, scripts, and documentation paths must move together and be verified after migration.

### ADR-022 — Keep personal AI workspace out of the public project

- **Status:** ACCEPTED
- **Context:** The local workspace contains agent instructions, reusable skills, personal prompts, and bootstrap helpers that are not application deliverables.
- **Decision:** Preserve the files locally (including `.agents/skills/`) while excluding them from the public Git index. Move prompt content into ignored `.local/prompts/` and personal helper scripts into `.local/scripts/`; retain public code, CI, configuration, tests, and engineering documentation. Keep `.env.example` trackable while ignoring `.env` and local caches/artifacts.
- **Trade-off:** Teammates receive the application and technical documentation but not private personal development tooling.

### ADR-023 — Split frontend by implemented feature responsibility

- **Status:** ACCEPTED
- **Context:** The existing React/TypeScript UI had grown into a large module, making its dashboard, inventory, network, incidents, forecast, and allocation views difficult to maintain independently.
- **Decision:** Keep the app shell in `web/src/app/`, shared layout/UI components in `components/`, feature pages and panels under `features/`, API calls under `services/`, common types under `types/`, and formatting helpers under `lib/`. Add focused Vitest/Testing Library tests for existing user-visible navigation/stale and approval-token behavior.
- **Trade-off:** The current test set covers key rendered interactions but is not a full visual or end-to-end UI suite.

### ADR-024 — Keep the SSE read timeout above the simulator keepalive interval

- **Status:** ACCEPTED
- **Context:** The simulator emits an SSE keepalive every 15 seconds. The shared `SimClient` applied the 3-second ordinary REST read timeout to streaming responses, causing repeated `SimUnavailable` reconnect logs while the stream itself returned HTTP 200 and REST polling remained healthy.
- **Decision:** Give streaming responses a separate configurable `SIM_STREAM_READ_TIMEOUT_S` with a default and minimum of 20 and 16 seconds respectively. Keep ordinary REST reads at 3 seconds. SSE remains an advisory channel; polling remains authoritative.
- **Trade-off:** A dead stream may take longer than a REST request to time out, while normal keepalive silence no longer triggers false disconnects.

### ADR-025 — Keep recommendation identity and request body visible through operator review

- **Status:** ACCEPTED
- **Context:** Two current DIESEL proposals for Cox's Bazar had similar cards; the UI omitted recommendation IDs and rounded quantities to whole liters. The operator associated the 1,543.55 L sibling's display with the 6,000 L recommendation's exact request body, although the database rows, API response, idempotency keys, and request bodies were correctly paired.
- **Decision:** Display each recommendation ID and idempotency key beside its full precision quantity, render the exact persisted request body in review details, and disable decisions if duplicated summary columns differ from that body. The API also rejects approval when the persisted row and body disagree.
- **Trade-off:** Review cards use more vertical space. The extra identity and payload detail prevents ambiguity and fails closed on corrupted records.

### ADR-026 — Separate service availability from decision-pipeline freshness

- **Status:** ACCEPTED
- **Context:** The decision engine is a worker pipeline, not an independently running service. When the simulator is paused, no new tick may trigger forecast/recommendation processing and its heartbeat can age even while the worker, simulator connection, and API remain healthy.
- **Decision:** Report the worker heartbeat separately. A stale decision-engine heartbeat is `DEGRADED` while the worker is available; it only remains `OFFLINE` when the worker itself is offline. Aggregate health can then be degraded without falsely labelling the simulator offline.
- **Trade-off:** Operators see an explicit degraded decision pipeline during pauses rather than an inaccurate whole-system offline banner.

### ADR-027 — Replace same-tick snapshot payload when refreshing its metadata

- **Status:** ACCEPTED
- **Context:** Same-tick REST polls refreshed `fetched_at`, stale, and data-status columns without replacing `raw_json`. This made old payload fields such as `instance.status=RUNNING` appear fresh after the live simulator had been paused.
- **Decision:** On a successful same-tick read, update `raw_json` and `sim_time` in the existing row together with its freshness metadata. Cached/stale fallback reads remain marked stale/degraded by the existing ingestion status path.
- **Trade-off:** Snapshot row count remains stable for repeated reads of a tick, while each latest payload now matches the read whose timestamp it carries.

### ADR-028 — Keep overnight operator notes local

- **Status:** ACCEPTED
- **Context:** The overnight execution log and morning handoff can contain environment-specific operational details and are not product documentation. The repository intentionally keeps local prompts and instructions out of the public tree.
- **Decision:** Ignore only `docs/OVERNIGHT-LOG.md` and `docs/MORNING-TODO.md` for the overnight run; keep reusable, redacted execution evidence and sprint results in tracked `docs/evidence/` and sprint reports.
- **Trade-off:** These two handoff files exist only in the local workspace; repository progress and evidence remain the shared source of truth.

### ADR-029 — Validate resolved Compose service credentials without exposing values

- **Status:** ACCEPTED
- **Context:** The local `.env` differs from the public Compose defaults for database credentials and predictor port. Editing that local file is prohibited, and a mismatch otherwise appears later as a confusing service startup failure.
- **Decision:** Add a smoke preflight that parses resolved Compose JSON and compares API/worker database credentials with PostgreSQL and the worker predictor URL with the predictor's internal port. Diagnostics identify only the mismatched variable names and redact values. Accept `--env-file` so clean-clone defaults can be verified explicitly. Keep `.env.example` and Compose defaults authoritative for public setup.
- **Trade-off:** The smoke preflight intentionally fails in this local checkout until its owner aligns local settings; clean public defaults remain testable without changing local secrets.
# Project plan: 28 hours, seven sprints, one repository

## 1. Product outcome
An operator-facing platform that shows live simulated fuel state, forecasts hours to stockout with uncertainty, recommends feasible allocations with explanations, lets a human approve or reject, submits approved shipments to the simulator, and keeps working through simulator faults and its own component failures. A notebook, static dashboard or chatbot alone does not meet the brief.

## 2. Key insight
Stations are refilled only by our allocations. Depots are refilled by 22 scheduled supply arrivals. With no action, stations run dry in roughly a simulated day. The platform's value is measured against that do-nothing baseline.

## 3. Architecture (current implementation)
The six platform services remain separate: simulator REST/SSE feeds the worker; the worker persists validated state and domain results in PostgreSQL; the API serves database-backed operator routes; the React frontend calls the API; Prometheus scrapes API, worker and predictor; Grafana uses Prometheus. The predictor exposes `POST /predict`; the worker calls it through a bounded client with an independent breaker and profile-only fallback. Predictor, health, Grafana, resilience, and Sprint 6–7 runtime acceptance still require the evidence listed in `docs/PROGRESS.md`.

- `backend/api/`: API, routes, database access and schema.
- `backend/worker/`: ingestion, forecast/recommendation jobs, SSE and approved execution.
- `backend/shared/core/`: pure models, simulator client, forecast/risk/policy/validator logic and shared metrics.
- `intel/predictor/`: independent predictor service.
- `web/`: React application organized by feature.
- `observability/`: Prometheus and Grafana provisioning.
- `scripts/`, `tests/`: operational scripts and unit/integration/scenario suites.

The topology is defined in `docker-compose.yml`; API, worker and predictor are not combined into one runtime.

## 4. Application API (confirm against code)
GET /api/state, /api/data-health, /api/events, /api/risks, /api/risks/{station}/{fuel}/trajectory, /api/recommendations, /api/decisions, /api/health; POST /api/recommendations/{id}/approve and /reject (operator token); POST /api/chaos/forecast-fail (operator token, demo only).

## 5. Schedule
| Sprint | Hours | Outcome | Tag |
|---|---|---|---|
| 1 | 0-4 | Simulator explored, contract and DB schema, compose and CI skeleton | sprint-1 |
| 2 | 4-8 | Resilient simulator client, ingestion, read API, live dashboard | sprint-2 |
| 3 | 8-12 | Forecast, Monte Carlo risk, risk UI | sprint-3 |
| 4 | 12-16 | Validator, allocation policy, explanations, approval, executor, recommendations UI | sprint-4 |
| 5 | 16-20 | Metrics, Grafana, health, predictor and fallback, fault demo | sprint-5 |
| 6 | 20-24 | Scenario runner, load test, CI hardening, main docs | sprint-6 |
| 7 | 24-28 | Freeze, cold start, chaos, demo, final docs, release | sprint-7 |

Rhythm inside each sprint: 0:00-0:20 read PROGRESS and plan; 0:20-3:10 build; 3:10-3:40 test, integrate, cross-review; 3:40-4:00 gate, report, tag.

## 6. Priorities
P0: simulator connectivity, live dashboard, explainable stockout risk, feasible recommendations, human approval, safe submission, crisis demo, fault fallback, `docker compose up`.
P1: persistence and audit, metrics and Grafana, tests and CI, load test, scenario comparison, complete docs.
P2: LP optimizer, LLM summaries, what-if endpoint, extra charts.
Cut order when behind: P2, then polish, then extra charts. Never cut: hard constraints, re-validation, human approval, stale-data handling, fault demo, tests of the executor.

## 7. Sprint acceptance gates
Sprint acceptance prompts are retained in the local-only `.local/prompts/` workspace. A sprint passes only when every acceptance item has real command output or evidence in its report.

## 8. Scoring map
Product and UX 20, Intelligence 20, Architecture 15, DevOps 15, Resilience 15, Observability and performance 10, Demo 5. Most points come from a working, resilient, observable system, not from model sophistication.

## 9. End-of-sprint presentation (five minutes)
1. Operator problem solved. 2. What changed in architecture and code. 3. Live demo. 4. Evidence (tests, outputs). 5. What failed, remains risky, and next sprint's dependency.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-X1IceUkK' (errno=Operation not permitted)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-gcKD2Bo2' (errno=Operation not permitted)
40f21a3 (HEAD -> overnight-sprints-4-7) docs: record sprint 4 gate and tag
3fe2353 (tag: sprint-4) fix: align allocation ETA with simulator arrival
0aaaaf5 docs: capture fresh sprint 4 approval candidate
ece9d5a docs: initialize overnight execution handoff
ee830cc WIP: snapshot before overnight run
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-jq3aoRaM' (errno=Operation not permitted)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-5Ps9unwx' (errno=Operation not permitted)
## overnight-sprints-4-7
 M README.md
 M backend/worker/sse.py
 M backend/worker/store.py
 M docs/decisions.md
 M docs/observability.md
 M docs/resilience.md
 M docs/sprint-reports/sprint-05.md
 M scripts/fault_demo.sh
 M scripts/smoke.sh
 M tests/integration/test_sse.py
 M tests/unit/test_store_snapshot.py
?? docs/evidence/sprint-05-fault-demo-accepted.txt
?? docs/evidence/sprint-05-fault-demo-complete.txt
?? docs/evidence/sprint-05-fault-demo-final-rerun.txt
?? docs/evidence/sprint-05-fault-demo-final.txt
?? docs/evidence/sprint-05-fault-demo-output.txt
?? docs/evidence/sprint-05-fault-demo-verified.txt
?? docs/evidence/sprint-05-grafana-event.txt
?? docs/evidence/sprint-05-live.md
?? docs/evidence/sprint-05-r4-review.md
?? scripts/check_compose_env.py
?? tests/unit/test_compose_env_check.py
observability/grafana/provisioning/dashboards/fuel-supply-platform.json
observability/grafana/provisioning/dashboards/default.yml
observability/grafana/provisioning/alerting/alerts.yml
docs/sim-samples/health.json
docs/resilience.md
tests/integration/test_health_api.py
tests/integration/test_resilience.py
web/package-lock.json
backend/api/routes/health.py
web/tsconfig.json
web/package.json
web/nginx.conf
web/vite.config.ts
web/index.html
web/Dockerfile
web/tests/setup.ts
web/tests/App.test.tsx
web/src/services/api.ts
web/src/features/incidents/EventsPanel.tsx
web/src/app/main.tsx
web/src/components/layout/Header.tsx
web/src/app/App.tsx
web/src/components/layout/PageNavigation.tsx
web/src/lib/format.ts
web/src/features/inventory/InventoryMatrix.tsx
web/src/features/inventory/DepotsPanel.tsx
web/src/types/vite-env.d.ts
web/src/types/api.ts
web/src/features/shortage-risk/TrajectoryDrawer.tsx
web/src/features/shortage-risk/ShortageRiskPage.tsx
web/src/features/allocations/RecommendationsPage.tsx
web/src/features/system-health/HealthPage.tsx
web/src/components/ui/StatusPill.tsx
web/src/features/dashboard/DashboardPage.tsx
web/src/styles/global.css
web/src/features/network/RoutesPanel.tsx

exec
/bin/zsh -lc "nl -ba backend/shared/core/sim_client.py | sed -n '1,300p'; nl -ba backend/worker/ingest.py | sed -n '1,300p'; nl -ba backend/worker/sse.py | sed -n '1,240p'; nl -ba backend/worker/forecaster.py | sed -n '1,280p'" in /Users/abrar/project/fuel_simulator
 succeeded in 0ms:
     1	"""Typed, bounded-retry client for the official fuel simulator."""
     2	
     3	from __future__ import annotations
     4	
     5	import asyncio
     6	import random
     7	import time
     8	from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
     9	from contextlib import asynccontextmanager
    10	from dataclasses import dataclass
    11	from enum import Enum
    12	from typing import Any, Generic, TypeVar
    13	from urllib.parse import quote
    14	
    15	import httpx
    16	from pydantic import TypeAdapter, ValidationError
    17	from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt
    18	
    19	from core.metrics import (
    20	    sim_breaker_state,
    21	    sim_client_failures,
    22	    sim_client_requests,
    23	    sim_client_retries,
    24	)
    25	from core.models import (
    26	    Allocation,
    27	    DemandObs,
    28	    Depot,
    29	    Instance,
    30	    Metrics,
    31	    Region,
    32	    Route,
    33	    SimEvent,
    34	    Station,
    35	    SupplyArrival,
    36	    parse_sim_error,
    37	)
    38	
    39	T = TypeVar("T")
    40	ModelType = Any
    41	
    42	
    43	@dataclass(frozen=True)
    44	class SimResult(Generic[T]):
    45	    data: T
    46	    stale: bool = False
    47	
    48	
    49	class SimUnavailable(RuntimeError):
    50	    """The simulator cannot currently serve a valid request."""
    51	
    52	
    53	class SimInvalidResponse(RuntimeError):
    54	    """The simulator returned malformed JSON or a schema-invalid response."""
    55	
    56	
    57	class SimBusinessError(RuntimeError):
    58	    """A non-retryable simulator validation or business error."""
    59	
    60	    def __init__(self, code: str, message: str, status_code: int) -> None:
    61	        super().__init__(message)
    62	        self.code = code
    63	        self.status_code = status_code
    64	
    65	
    66	class BreakerState(str, Enum):
    67	    CLOSED = "closed"
    68	    OPEN = "open"
    69	    HALF_OPEN = "half_open"
    70	
    71	
    72	class CircuitBreaker:
    73	    """Per-client breaker; only one request may probe a half-open breaker."""
    74	
    75	    def __init__(
    76	        self,
    77	        *,
    78	        failure_threshold: int = 5,
    79	        reset_after_s: float = 10.0,
    80	        clock: Callable[[], float] = time.monotonic,
    81	    ) -> None:
    82	        self.failure_threshold = failure_threshold
    83	        self.reset_after_s = reset_after_s
    84	        self._clock = clock
    85	        self._state = BreakerState.CLOSED
    86	        self._failure_count = 0
    87	        self._opened_at = 0.0
    88	        self._probe_in_flight = False
    89	        self._lock = asyncio.Lock()
    90	        self._update_metric()
    91	
    92	    @property
    93	    def state(self) -> BreakerState:
    94	        return self._state
    95	
    96	    @property
    97	    def failure_count(self) -> int:
    98	        return self._failure_count
    99	
   100	    async def before_request(self) -> None:
   101	        async with self._lock:
   102	            if self._state is BreakerState.OPEN:
   103	                if self._clock() - self._opened_at < self.reset_after_s:
   104	                    raise SimUnavailable("circuit breaker is open")
   105	                self._state = BreakerState.HALF_OPEN
   106	                self._probe_in_flight = False
   107	                self._update_metric()
   108	            if self._state is BreakerState.HALF_OPEN:
   109	                if self._probe_in_flight:
   110	                    raise SimUnavailable("circuit breaker half-open probe is in flight")
   111	                self._probe_in_flight = True
   112	
   113	    async def record_success(self) -> None:
   114	        async with self._lock:
   115	            self._state = BreakerState.CLOSED
   116	            self._failure_count = 0
   117	            self._probe_in_flight = False
   118	            self._update_metric()
   119	
   120	    async def record_failure(self) -> None:
   121	        async with self._lock:
   122	            self._probe_in_flight = False
   123	            if self._state is BreakerState.HALF_OPEN:
   124	                self._state = BreakerState.OPEN
   125	                self._opened_at = self._clock()
   126	            else:
   127	                self._failure_count += 1
   128	                if self._failure_count >= self.failure_threshold:
   129	                    self._state = BreakerState.OPEN
   130	                    self._opened_at = self._clock()
   131	            self._update_metric()
   132	
   133	    def _update_metric(self) -> None:
   134	        for state in BreakerState:
   135	            sim_breaker_state.labels(state=state.value).set(float(state is self._state))
   136	
   137	
   138	class _RetryableRequest(RuntimeError):
   139	    pass
   140	
   141	
   142	class SimClient:
   143	    """Async client that returns validated models and preserves stale markers."""
   144	
   145	    def __init__(
   146	        self,
   147	        base_url: str,
   148	        *,
   149	        http_client: httpx.AsyncClient | None = None,
   150	        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
   151	        clock: Callable[[], float] = time.monotonic,
   152	        jitter: Callable[[float], float] | None = None,
   153	        max_retries: int = 3,
   154	        connect_timeout_s: float = 2.0,
   155	        read_timeout_s: float = 3.0,
   156	        stream_read_timeout_s: float = 20.0,
   157	        breaker_failure_threshold: int = 5,
   158	        breaker_reset_after_s: float = 10.0,
   159	    ) -> None:
   160	        self.base_url = base_url.rstrip("/")
   161	        self._sleep = sleep
   162	        self._jitter = jitter or (lambda upper: random.uniform(0.0, upper))
   163	        self.max_retries = max_retries
   164	        self.connect_timeout_s = max(0.1, connect_timeout_s)
   165	        self.read_timeout_s = max(0.1, read_timeout_s)
   166	        # The simulator sends an SSE keepalive every 15s; give it room to arrive.
   167	        self.stream_read_timeout_s = max(16.0, stream_read_timeout_s)
   168	        self._owns_client = http_client is None
   169	        self._http = http_client or httpx.AsyncClient(
   170	            base_url=self.base_url,
   171	            timeout=httpx.Timeout(
   172	                connect=self.connect_timeout_s,
   173	                read=self.read_timeout_s,
   174	                write=self.read_timeout_s,
   175	                pool=self.connect_timeout_s,
   176	            ),
   177	        )
   178	        self.breaker = CircuitBreaker(
   179	            clock=clock,
   180	            failure_threshold=breaker_failure_threshold,
   181	            reset_after_s=breaker_reset_after_s,
   182	        )
   183	
   184	    async def __aenter__(self) -> SimClient:
   185	        return self
   186	
   187	    async def __aexit__(self, *_: object) -> None:
   188	        await self.close()
   189	
   190	    async def close(self) -> None:
   191	        if self._owns_client:
   192	            await self._http.aclose()
   193	
   194	    async def get_health(self) -> SimResult[dict[str, Any]]:
   195	        return await self._get("/v1/health", "/v1/health", dict[str, Any])
   196	
   197	    async def get_instance(self) -> SimResult[Instance]:
   198	        return await self._get("/v1/instance", "/v1/instance", Instance)
   199	
   200	    async def get_regions(self) -> SimResult[list[Region]]:
   201	        return await self._get("/v1/regions", "/v1/regions", TypeAdapter(list[Region]))
   202	
   203	    async def get_depots(self) -> SimResult[list[Depot]]:
   204	        return await self._get("/v1/depots", "/v1/depots", TypeAdapter(list[Depot]))
   205	
   206	    async def get_depot(self, entity_id: str) -> SimResult[Depot]:
   207	        path = f"/v1/depots/{quote(entity_id, safe='')}"
   208	        return await self._get(path, "/v1/depots/{entity_id}", Depot)
   209	
   210	    async def get_stations(self) -> SimResult[list[Station]]:
   211	        return await self._get("/v1/stations", "/v1/stations", TypeAdapter(list[Station]))
   212	
   213	    async def get_station(self, entity_id: str) -> SimResult[Station]:
   214	        path = f"/v1/stations/{quote(entity_id, safe='')}"
   215	        return await self._get(path, "/v1/stations/{entity_id}", Station)
   216	
   217	    async def get_routes(self) -> SimResult[list[Route]]:
   218	        return await self._get("/v1/routes", "/v1/routes", TypeAdapter(list[Route]))
   219	
   220	    async def get_supply_arrivals(self) -> SimResult[list[SupplyArrival]]:
   221	        return await self._get(
   222	            "/v1/supply-arrivals", "/v1/supply-arrivals", TypeAdapter(list[SupplyArrival])
   223	        )
   224	
   225	    async def get_events(self) -> SimResult[list[SimEvent]]:
   226	        return await self._get("/v1/events", "/v1/events", TypeAdapter(list[SimEvent]))
   227	
   228	    async def get_allocations(self) -> SimResult[list[Allocation]]:
   229	        return await self._get("/v1/allocations", "/v1/allocations", TypeAdapter(list[Allocation]))
   230	
   231	    async def get_metrics(self) -> SimResult[Metrics]:
   232	        return await self._get("/v1/metrics", "/v1/metrics", Metrics)
   233	
   234	    async def get_demand_history(
   235	        self, station_id: str | None = None, *, limit: int = 100
   236	    ) -> SimResult[list[DemandObs]]:
   237	        if not 1 <= limit <= 2000:
   238	            raise ValueError("demand-history limit must be between 1 and 2000")
   239	        params: dict[str, Any] = {"limit": limit}
   240	        if station_id is not None:
   241	            params["station_id"] = station_id
   242	        return await self._get(
   243	            "/v1/demand-history",
   244	            "/v1/demand-history",
   245	            TypeAdapter(list[DemandObs]),
   246	            params=params,
   247	        )
   248	
   249	    async def create_allocation(self, body: Mapping[str, Any]) -> SimResult[Allocation]:
   250	        stable_body = dict(body)
   251	        return await self._request(
   252	            "POST",
   253	            "/v1/allocations",
   254	            "/v1/allocations",
   255	            Allocation,
   256	            json_body=stable_body,
   257	        )
   258	
   259	    @asynccontextmanager
   260	    async def stream(self) -> AsyncIterator[AsyncIterator[str]]:
   261	        endpoint = "/v1/stream"
   262	        await self.breaker.before_request()
   263	        try:
   264	            stream_timeout = httpx.Timeout(
   265	                connect=self.connect_timeout_s,
   266	                read=self.stream_read_timeout_s,
   267	                write=self.read_timeout_s,
   268	                pool=self.connect_timeout_s,
   269	            )
   270	            async with self._http.stream("GET", endpoint, timeout=stream_timeout) as response:
   271	                if response.is_error:
   272	                    content = await response.aread()
   273	                    error_response = httpx.Response(
   274	                        response.status_code, headers=response.headers, content=content
   275	                    )
   276	                    parsed = parse_sim_error(error_response)
   277	                    if response.status_code == 503 and parsed.code == "FAULT_INJECTED":
   278	                        raise SimUnavailable(parsed.message)
   279	                    raise SimBusinessError(parsed.code, parsed.message, response.status_code)
   280	                sim_client_requests.labels(endpoint=endpoint, outcome="success").inc()
   281	                await self.breaker.record_success()
   282	                yield response.aiter_lines()
   283	        except SimBusinessError:
   284	            await self.breaker.record_success()
   285	            sim_client_requests.labels(endpoint=endpoint, outcome="business_error").inc()
   286	            raise
   287	        except (SimUnavailable, httpx.TransportError) as exc:
   288	            await self.breaker.record_failure()
   289	            sim_client_failures.labels(endpoint=endpoint).inc()
   290	            sim_client_requests.labels(endpoint=endpoint, outcome="failure").inc()
   291	            if isinstance(exc, SimUnavailable):
   292	                raise
   293	            raise SimUnavailable(str(exc)) from exc
   294	
   295	    async def _get(
   296	        self,
   297	        path: str,
   298	        endpoint: str,
   299	        response_type: ModelType,
   300	        *,
     1	"""Atomic simulator snapshot collection and persistence."""
     2	
     3	from __future__ import annotations
     4	
     5	import asyncio
     6	import json
     7	import logging
     8	from collections.abc import Awaitable
     9	from datetime import datetime, timezone
    10	from typing import Callable
    11	
    12	from core.metrics import (
    13	    forecast_job_failures,
    14	    sim_service_level,
    15	    snapshot_age,
    16	    snapshot_rejected,
    17	    worker_ingest_failures,
    18	    worker_ingest_success,
    19	)
    20	from core.models import DataStatus, Snapshot
    21	from core.sim_client import BreakerState, SimClient
    22	from worker.store import SnapshotStore
    23	
    24	logger = logging.getLogger("fuel_simulator.worker.ingest")
    25	
    26	
    27	def derive_data_status(age_seconds: float, stale: bool, breaker_state: BreakerState) -> DataStatus:
    28	    if age_seconds > 120:
    29	        return DataStatus.OFFLINE
    30	    if stale or breaker_state in (BreakerState.OPEN, BreakerState.HALF_OPEN) or age_seconds >= 15:
    31	        return DataStatus.DEGRADED
    32	    return DataStatus.HEALTHY
    33	
    34	
    35	class SnapshotIngestor:
    36	    def __init__(
    37	        self,
    38	        client: SimClient,
    39	        store: SnapshotStore,
    40	        *,
    41	        now: Callable[[], datetime] | None = None,
    42	        demand_limit: int = 100,
    43	        keep_snapshots: int = 1000,
    44	        on_snapshot: Callable[[Snapshot], Awaitable[None]] | None = None,
    45	    ) -> None:
    46	        self.client = client
    47	        self.store = store
    48	        self._now = now or (lambda: datetime.now(timezone.utc))
    49	        self.demand_limit = demand_limit
    50	        self.keep_snapshots = keep_snapshots
    51	        self.on_snapshot = on_snapshot
    52	
    53	    async def fetch_snapshot(self) -> Snapshot:
    54	        results = await asyncio.gather(
    55	            self.client.get_instance(),
    56	            self.client.get_regions(),
    57	            self.client.get_depots(),
    58	            self.client.get_stations(),
    59	            self.client.get_routes(),
    60	            self.client.get_supply_arrivals(),
    61	            self.client.get_events(),
    62	            self.client.get_allocations(),
    63	            self.client.get_metrics(),
    64	        )
    65	        (
    66	            instance,
    67	            regions,
    68	            depots,
    69	            stations,
    70	            routes,
    71	            supply_arrivals,
    72	            events,
    73	            allocations,
    74	            metrics,
    75	        ) = results
    76	        station_rows = stations.data
    77	        histories = await asyncio.gather(
    78	            *(
    79	                self.client.get_demand_history(station.id, limit=self.demand_limit)
    80	                for station in station_rows
    81	            )
    82	        )
    83	        fetched_at = self._now()
    84	        stale = any(result.stale for result in results) or any(result.stale for result in histories)
    85	        data_status = derive_data_status(0.0, stale, self.client.breaker.state)
    86	        return Snapshot(
    87	            instance=instance.data,
    88	            regions=regions.data,
    89	            depots=depots.data,
    90	            stations=station_rows,
    91	            routes=routes.data,
    92	            supply_arrivals=supply_arrivals.data,
    93	            events=events.data,
    94	            allocations=allocations.data,
    95	            demand_history=[row for result in histories for row in result.data],
    96	            metrics=metrics.data,
    97	            fetched_at=fetched_at,
    98	            stale=stale,
    99	            data_status=data_status,
   100	        )
   101	
   102	    async def run_once(self) -> bool:
   103	        try:
   104	            snapshot = await self.fetch_snapshot()
   105	            inserted = await self.store.insert_snapshot(snapshot)
   106	            if self.on_snapshot is not None:
   107	                try:
   108	                    await self.on_snapshot(snapshot)
   109	                except Exception as forecast_exc:
   110	                    forecast_job_failures.inc()
   111	                    logger.exception(
   112	                        json.dumps(
   113	                            {
   114	                                "event": "forecast_job_failed",
   115	                                "error_type": type(forecast_exc).__name__,
   116	                            }
   117	                        )
   118	                    )
   119	                    try:
   120	                        await self.store.record_integration_event(
   121	                            "forecast_job_failed",
   122	                            {"error_type": type(forecast_exc).__name__},
   123	                        )
   124	                    except Exception:
   125	                        logger.exception(
   126	                            json.dumps({"event": "forecast_failure_event_write_failed"})
   127	                        )
   128	            await self.store.heartbeat(
   129	                "worker",
   130	                {
   131	                    "tick": snapshot.instance.tick,
   132	                    "data_status": snapshot.data_status.value,
   133	                    "breaker_state": self.client.breaker.state.value,
   134	                },
   135	            )
   136	            await self.store.prune_snapshots(self.keep_snapshots)
   137	            snapshot_age.set(max(0.0, (self._now() - snapshot.fetched_at).total_seconds()))
   138	            sim_service_level.set(snapshot.metrics.service_level)
   139	            worker_ingest_success.inc()
   140	            logger.info(
   141	                json.dumps(
   142	                    {
   143	                        "event": "snapshot_ingested" if inserted else "snapshot_unchanged",
   144	                        "tick": snapshot.instance.tick,
   145	                        "data_status": snapshot.data_status.value,
   146	                    }
   147	                )
   148	            )
   149	            return inserted
   150	        except Exception as exc:
   151	            worker_ingest_failures.inc()
   152	            reason = type(exc).__name__
   153	            snapshot_rejected.labels(reason=reason).inc()
   154	            event = {
   155	                "error_type": reason,
   156	                "message": str(exc),
   157	            }
   158	            logger.warning(json.dumps({"event": "snapshot_rejected", **event}))
   159	            try:
   160	                await self.store.mark_latest_degraded()
   161	            except Exception as store_exc:
   162	                logger.error(
   163	                    json.dumps(
   164	                        {
   165	                            "event": "snapshot_status_update_failed",
   166	                            "error_type": type(store_exc).__name__,
   167	                        }
   168	                    )
   169	                )
   170	            try:
   171	                await self.store.record_integration_event("snapshot_rejected", event)
   172	            except Exception as store_exc:
   173	                logger.error(
   174	                    json.dumps(
   175	                        {
   176	                            "event": "integration_event_write_failed",
   177	                            "error_type": type(store_exc).__name__,
   178	                        }
   179	                    )
   180	                )
   181	            try:
   182	                await self.store.heartbeat(
   183	                    "worker",
   184	                    {"last_ingest_ok": False, "last_error_type": reason},
   185	                )
   186	            except Exception as store_exc:
   187	                logger.error(
   188	                    json.dumps(
   189	                        {
   190	                            "event": "worker_heartbeat_write_failed",
   191	                            "error_type": type(store_exc).__name__,
   192	                        }
   193	                    )
   194	                )
   195	            return False
     1	"""SSE hint consumer; REST ingestion remains the only source of snapshot state."""
     2	
     3	from __future__ import annotations
     4	
     5	import asyncio
     6	import json
     7	import logging
     8	import time
     9	from collections.abc import Awaitable, Callable
    10	from datetime import datetime, timezone
    11	
    12	from core.metrics import sse_events, sse_reconnects
    13	from core.sim_client import SimClient
    14	
    15	logger = logging.getLogger("fuel_simulator.worker.sse")
    16	logger.setLevel(logging.INFO)
    17	if not logger.handlers:
    18	    handler = logging.StreamHandler()
    19	    handler.setFormatter(logging.Formatter("%(message)s"))
    20	    logger.addHandler(handler)
    21	
    22	
    23	class SSEConsumer:
    24	    def __init__(
    25	        self,
    26	        client: SimClient,
    27	        refresh: Callable[[], Awaitable[object]],
    28	        *,
    29	        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    30	        clock: Callable[[], float] = time.monotonic,
    31	        max_backoff_s: float = 30.0,
    32	    ) -> None:
    33	        self.client = client
    34	        self.refresh = refresh
    35	        self._sleep = sleep
    36	        self._clock = clock
    37	        self.max_backoff_s = max_backoff_s
    38	        self._last_refresh = float("-inf")
    39	
    40	    async def run(
    41	        self,
    42	        *,
    43	        stop_event: asyncio.Event | None = None,
    44	        max_connections: int | None = None,
    45	    ) -> None:
    46	        backoff_s = 0.5
    47	        connections = 0
    48	        while stop_event is None or not stop_event.is_set():
    49	            connections += 1
    50	            sse_reconnects.inc()
    51	            try:
    52	                async with self.client.stream() as lines:
    53	                    logger.info(
    54	                        json.dumps(
    55	                            {
    56	                                "timestamp": datetime.now(timezone.utc).isoformat(),
    57	                                "level": "info",
    58	                                "service": "worker",
    59	                                "event": "simulator_stream_connected",
    60	                                "tick": None,
    61	                                "correlation_id": None,
    62	                            }
    63	                        )
    64	                    )
    65	                    await self._refresh_if_due()
    66	                    backoff_s = 0.5
    67	                    async for line in lines:
    68	                        if stop_event is not None and stop_event.is_set():
    69	                            return
    70	                        if line.startswith("data:"):
    71	                            sse_events.inc()
    72	                            await self._refresh_if_due()
    73	            except asyncio.CancelledError:
    74	                raise
    75	            except Exception as exc:
    76	                logger.warning(
    77	                    json.dumps(
    78	                        {
    79	                            "timestamp": datetime.now(timezone.utc).isoformat(),
    80	                            "level": "warning",
    81	                            "service": "worker",
    82	                            "event": "simulator_stream_disconnected",
    83	                            "error_type": type(exc).__name__,
    84	                            "tick": None,
    85	                            "correlation_id": None,
    86	                        }
    87	                    )
    88	                )
    89	
    90	            if max_connections is not None and connections >= max_connections:
    91	                return
    92	            if stop_event is not None and stop_event.is_set():
    93	                return
    94	            await self._sleep(backoff_s)
    95	            backoff_s = min(backoff_s * 2, self.max_backoff_s)
    96	
    97	    async def _refresh_if_due(self) -> None:
    98	        now = self._clock()
    99	        if now - self._last_refresh < 1.0:
   100	            return
   101	        self._last_refresh = now
   102	        await self.refresh()
     1	"""Remote predictor client and deterministic no-calibration fallback."""
     2	
     3	from __future__ import annotations
     4	
     5	import asyncio
     6	import time
     7	from typing import Protocol
     8	
     9	import httpx
    10	
    11	from core.models import FuelType, Snapshot, Station
    12	from core.risk import ForecastRecord, TrajectoryPoint, forecast_pair
    13	
    14	
    15	class ForecastBackend(Protocol):
    16	    async def forecast(
    17	        self, snapshot: Snapshot, station: Station, fuel: FuelType, seed: int
    18	    ) -> ForecastRecord: ...
    19	
    20	
    21	class RemoteForecastError(RuntimeError):
    22	    def __init__(self, reason: str) -> None:
    23	        super().__init__(reason)
    24	        self.reason = reason
    25	
    26	
    27	class RemoteForecaster:
    28	    def __init__(
    29	        self,
    30	        base_url: str,
    31	        *,
    32	        timeout_s: float = 1.5,
    33	        failure_threshold: int = 5,
    34	        reset_after_s: float = 10.0,
    35	        transport: httpx.AsyncBaseTransport | None = None,
    36	    ) -> None:
    37	        self.base_url = base_url.rstrip("/")
    38	        self.client = httpx.AsyncClient(timeout=max(0.1, timeout_s), transport=transport)
    39	        self.failure_threshold = max(1, failure_threshold)
    40	        self.reset_after_s = max(0.1, reset_after_s)
    41	        self._failures = 0
    42	        self._opened_until = 0.0
    43	        self._half_open_probe = False
    44	        self._lock = asyncio.Lock()
    45	
    46	    async def forecast(
    47	        self, snapshot: Snapshot, station: Station, fuel: FuelType, seed: int
    48	    ) -> ForecastRecord:
    49	        async with self._lock:
    50	            if self._opened_until:
    51	                if time.monotonic() < self._opened_until or self._half_open_probe:
    52	                    raise RemoteForecastError("breaker_open")
    53	                self._half_open_probe = True
    54	        try:
    55	            station_snapshot = snapshot.model_copy(
    56	                update={
    57	                    "stations": [station],
    58	                    "demand_history": [
    59	                        row
    60	                        for row in snapshot.demand_history
    61	                        if row.station_id == station.id and row.fuel_type is fuel
    62	                    ],
    63	                }
    64	            )
    65	            response = await self.client.post(
    66	                f"{self.base_url}/predict",
    67	                json={
    68	                    "snapshot": station_snapshot.model_dump(mode="json"),
    69	                    "station_id": station.id,
    70	                    "fuel_type": fuel.value,
    71	                    "seed": seed,
    72	                },
    73	            )
    74	            if response.status_code >= 500:
    75	                raise RemoteForecastError("predictor_5xx")
    76	            if response.status_code >= 400:
    77	                raise RemoteForecastError("predictor_rejected_request")
    78	            payload = response.json()
    79	            record = self._parse_record(payload)
    80	            if record.forecast.station_id != station.id or record.forecast.fuel_type is not fuel:
    81	                raise RemoteForecastError("predictor_schema_error")
    82	        except httpx.TimeoutException as exc:
    83	            await self._record_failure()
    84	            raise RemoteForecastError("timeout") from exc
    85	        except httpx.HTTPError as exc:
    86	            await self._record_failure()
    87	            raise RemoteForecastError("unavailable") from exc
    88	        except RemoteForecastError:
    89	            await self._record_failure()
    90	            raise
    91	        except (ValueError, KeyError, TypeError) as exc:
    92	            await self._record_failure()
    93	            raise RemoteForecastError("predictor_schema_error") from exc
    94	        async with self._lock:
    95	            self._failures = 0
    96	            self._opened_until = 0.0
    97	            self._half_open_probe = False
    98	        return record
    99	
   100	    async def _record_failure(self) -> None:
   101	        async with self._lock:
   102	            self._failures += 1
   103	            if self._failures >= self.failure_threshold:
   104	                self._opened_until = time.monotonic() + self.reset_after_s
   105	            self._half_open_probe = False
   106	
   107	    @staticmethod
   108	    def _parse_record(payload: dict[str, object]) -> ForecastRecord:
   109	        from core.models import Forecast
   110	
   111	        forecast = Forecast.model_validate(payload["forecast"])
   112	        trajectory = [TrajectoryPoint(**point) for point in payload["trajectory"]]
   113	        drivers = payload["drivers"]
   114	        source = str(payload.get("source", "remote"))
   115	        return ForecastRecord(forecast, trajectory, drivers, source=source)
   116	
   117	    async def close(self) -> None:
   118	        await self.client.aclose()
   119	
   120	
   121	class BaselineForecaster:
   122	    """Fallback using profile demand only, with review-required confidence capped at 0.4."""
   123	
   124	    async def forecast(
   125	        self, snapshot: Snapshot, station: Station, fuel: FuelType, seed: int
   126	    ) -> ForecastRecord:
   127	        baseline_snapshot = snapshot.model_copy(update={"demand_history": []})
   128	        record = forecast_pair(baseline_snapshot, station, fuel, seed=seed)
   129	        forecast = record.forecast.model_copy(
   130	            update={"confidence": min(0.4, record.forecast.confidence), "needs_review": True}
   131	        )
   132	        return ForecastRecord(
   133	            forecast=forecast,
   134	            trajectory=record.trajectory,
   135	            drivers={**record.drivers, "fallback_reason": "predictor_unavailable"},
   136	            source="baseline",
   137	        )

exec
/bin/zsh -lc "nl -ba backend/shared/core/sim_client.py | sed -n '295,520p'; nl -ba backend/api/routes/health.py | sed -n '1,280p'; nl -ba backend/worker/main.py | sed -n '1,280p'; nl -ba backend/worker/forecast_job.py | sed -n '1,220p'; nl -ba web/src/features/system-health/HealthPage.tsx | sed -n '1,260p'; nl -ba observability/grafana/provisioning/alerting/alerts.yml | sed -n '1,300p'" in /Users/abrar/project/fuel_simulator
 succeeded in 0ms:
   295	    async def _get(
   296	        self,
   297	        path: str,
   298	        endpoint: str,
   299	        response_type: ModelType,
   300	        *,
   301	        params: Mapping[str, Any] | None = None,
   302	    ) -> SimResult[Any]:
   303	        return await self._request("GET", path, endpoint, response_type, params=params)
   304	
   305	    async def _request(
   306	        self,
   307	        method: str,
   308	        path: str,
   309	        endpoint: str,
   310	        response_type: ModelType,
   311	        *,
   312	        params: Mapping[str, Any] | None = None,
   313	        json_body: Mapping[str, Any] | None = None,
   314	    ) -> SimResult[Any]:
   315	        await self.breaker.before_request()
   316	
   317	        def wait_for_retry(retry_state: Any) -> float:
   318	            base = min(0.2 * (2 ** (retry_state.attempt_number - 1)), 0.8)
   319	            return base + max(0.0, self._jitter(base))
   320	
   321	        def count_retry(_: Any) -> None:
   322	            sim_client_retries.labels(endpoint=endpoint).inc()
   323	
   324	        retryer = AsyncRetrying(
   325	            stop=stop_after_attempt(self.max_retries + 1),
   326	            retry=retry_if_exception_type(
   327	                (_RetryableRequest, httpx.TimeoutException, httpx.ConnectError)
   328	            ),
   329	            wait=wait_for_retry,
   330	            sleep=self._sleep,
   331	            before_sleep=count_retry,
   332	            reraise=True,
   333	        )
   334	        try:
   335	            async for attempt in retryer:
   336	                with attempt:
   337	                    response = await self._http.request(
   338	                        method,
   339	                        path,
   340	                        params=params,
   341	                        json=json_body,
   342	                    )
   343	                    if response.status_code == 503:
   344	                        parsed = parse_sim_error(response)
   345	                        if parsed.code == "FAULT_INJECTED":
   346	                            raise _RetryableRequest(parsed.message)
   347	                    break
   348	        except (_RetryableRequest, httpx.TimeoutException, httpx.ConnectError) as exc:
   349	            await self.breaker.record_failure()
   350	            sim_client_failures.labels(endpoint=endpoint).inc()
   351	            sim_client_requests.labels(endpoint=endpoint, outcome="failure").inc()
   352	            raise SimUnavailable(str(exc) or "simulator unavailable") from exc
   353	
   354	        if response.is_error:
   355	            parsed = parse_sim_error(response)
   356	            if response.status_code >= 500:
   357	                await self.breaker.record_failure()
   358	                sim_client_failures.labels(endpoint=endpoint).inc()
   359	                sim_client_requests.labels(endpoint=endpoint, outcome="failure").inc()
   360	                raise SimUnavailable(parsed.message)
   361	            await self.breaker.record_success()
   362	            sim_client_requests.labels(endpoint=endpoint, outcome="business_error").inc()
   363	            raise SimBusinessError(parsed.code, parsed.message, response.status_code)
   364	
   365	        try:
   366	            payload = response.json()
   367	            adapter = (
   368	                response_type
   369	                if isinstance(response_type, TypeAdapter)
   370	                else TypeAdapter(response_type)
   371	            )
   372	            data = adapter.validate_python(payload)
   373	        except (ValueError, ValidationError, TypeError) as exc:
   374	            await self.breaker.record_failure()
   375	            sim_client_failures.labels(endpoint=endpoint).inc()
   376	            sim_client_requests.labels(endpoint=endpoint, outcome="invalid_response").inc()
   377	            raise SimInvalidResponse(f"invalid simulator response from {endpoint}: {exc}") from exc
   378	
   379	        await self.breaker.record_success()
   380	        sim_client_requests.labels(endpoint=endpoint, outcome="success").inc()
   381	        stale = response.headers.get("X-Simulator-Stale", "").lower() == "true"
   382	        return SimResult(data=data, stale=stale)
     1	"""Operator-facing component health aggregation from persisted state and bounded probes."""
     2	
     3	from __future__ import annotations
     4	
     5	import os
     6	from datetime import datetime, timezone
     7	from typing import Any
     8	
     9	import httpx
    10	from fastapi import APIRouter, Request
    11	
    12	from api.database import ReadRepository
    13	from core.metrics import api_http_request_duration, api_http_requests
    14	
    15	router = APIRouter(prefix="/api")
    16	
    17	
    18	def _age_seconds(value: datetime | str | None) -> float | None:
    19	    if value is None:
    20	        return None
    21	    parsed = (
    22	        datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    23	    )
    24	    if parsed.tzinfo is None:
    25	        parsed = parsed.replace(tzinfo=timezone.utc)
    26	    return max(0.0, (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds())
    27	
    28	
    29	def _status(age: float | None, data_status: str | None = None) -> str:
    30	    if age is None or age > 120:
    31	        return "OFFLINE"
    32	    if age >= 15 or data_status not in (None, "HEALTHY"):
    33	        return "DEGRADED"
    34	    return "HEALTHY"
    35	
    36	
    37	def _latency_summary() -> dict[str, float]:
    38	    samples = [
    39	        sample for family in api_http_request_duration.collect() for sample in family.samples
    40	    ]
    41	    count = sum(sample.value for sample in samples if sample.name.endswith("_count"))
    42	    target = count * 0.95
    43	    buckets: dict[float, float] = {}
    44	    for sample in samples:
    45	        if sample.name.endswith("_bucket"):
    46	            le = sample.labels.get("le")
    47	            if le is not None and le != "+Inf":
    48	                buckets[float(le)] = buckets.get(float(le), 0.0) + sample.value
    49	    p95 = next(
    50	        (bound for bound, observed in sorted(buckets.items()) if observed >= target),
    51	        max(buckets, default=0.0),
    52	    )
    53	
    54	    counters = [sample for family in api_http_requests.collect() for sample in family.samples]
    55	    total = sum(sample.value for sample in counters if sample.name.endswith("_total"))
    56	    errors = sum(
    57	        sample.value
    58	        for sample in counters
    59	        if sample.name.endswith("_total") and sample.labels.get("status_class") == "5xx"
    60	    )
    61	    return {"p95_seconds": p95, "error_rate": (errors / total if total else 0.0)}
    62	
    63	
    64	async def _predictor_status() -> str:
    65	    base_url = os.getenv("PREDICTOR_URL", "http://predictor:8103").rstrip("/")
    66	    try:
    67	        async with httpx.AsyncClient(timeout=0.5) as client:
    68	            response = await client.get(f"{base_url}/health")
    69	        return "HEALTHY" if response.status_code == 200 else "DEGRADED"
    70	    except httpx.HTTPError:
    71	        return "OFFLINE"
    72	
    73	
    74	async def _component_from_heartbeat(
    75	    repository: ReadRepository, component: str
    76	) -> tuple[str, float | None, dict[str, Any]]:
    77	    try:
    78	        record = await repository.get_heartbeat(component)
    79	    except Exception:
    80	        return "OFFLINE", None, {}
    81	    if record is None:
    82	        return "OFFLINE", None, {}
    83	    detail = record.get("detail") or {}
    84	    age = _age_seconds(record.get("last_seen"))
    85	    return _status(age, detail.get("data_status")), age, detail
    86	
    87	
    88	@router.get("/health")
    89	async def health(request: Request) -> dict[str, Any]:
    90	    repository: ReadRepository | None = getattr(request.app.state, "repository", None)
    91	    checked_at = datetime.now(timezone.utc).isoformat()
    92	    components: dict[str, dict[str, Any]] = {
    93	        "backend": {"status": "HEALTHY", "age_seconds": 0.0},
    94	        "predictor": {"status": await _predictor_status(), "age_seconds": None},
    95	    }
    96	    if repository is None:
    97	        components.update(
    98	            {
    99	                "database": {"status": "OFFLINE", "age_seconds": None},
   100	                "worker": {"status": "OFFLINE", "age_seconds": None},
   101	                "simulator": {"status": "OFFLINE", "age_seconds": None},
   102	                "decision_engine": {"status": "OFFLINE", "age_seconds": None},
   103	            }
   104	        )
   105	    else:
   106	        try:
   107	            db_ok = await repository.check_database()
   108	        except Exception:
   109	            db_ok = False
   110	        components["database"] = {
   111	            "status": "HEALTHY" if db_ok else "OFFLINE",
   112	            "age_seconds": None,
   113	        }
   114	        worker_status, worker_age, detail = await _component_from_heartbeat(repository, "worker")
   115	        components["worker"] = {"status": worker_status, "age_seconds": worker_age}
   116	        breaker = detail.get("breaker_state")
   117	        if worker_status == "HEALTHY" and breaker in ("OPEN", "HALF_OPEN"):
   118	            worker_status = "DEGRADED"
   119	        if detail.get("last_ingest_ok") is False and worker_status == "HEALTHY":
   120	            worker_status = "DEGRADED"
   121	        try:
   122	            latest = await repository.get_latest_snapshot()
   123	            snapshot_age = _age_seconds(latest.get("fetched_at")) if latest else None
   124	            snapshot_status = str(latest.get("data_status", "OFFLINE")) if latest else "OFFLINE"
   125	            if latest and latest.get("stale"):
   126	                snapshot_status = "DEGRADED"
   127	            simulator_status = _status(snapshot_age, snapshot_status)
   128	            if worker_status == "OFFLINE":
   129	                simulator_status = "OFFLINE"
   130	            elif worker_status == "DEGRADED" and simulator_status == "HEALTHY":
   131	                simulator_status = "DEGRADED"
   132	        except Exception:
   133	            snapshot_age = None
   134	            simulator_status = "OFFLINE"
   135	        components["simulator"] = {"status": simulator_status, "age_seconds": snapshot_age}
   136	        engine_status, engine_age, _ = await _component_from_heartbeat(
   137	            repository, "decision_engine"
   138	        )
   139	        # The decision pipeline shares the worker process. A stale pipeline
   140	        # heartbeat means processing is degraded; the worker heartbeat is the
   141	        # signal for process availability.
   142	        if worker_status != "OFFLINE" and engine_status == "OFFLINE":
   143	            engine_status = "DEGRADED"
   144	        components["decision_engine"] = {"status": engine_status, "age_seconds": engine_age}
   145	
   146	    statuses = [item["status"] for item in components.values()]
   147	    if "OFFLINE" in statuses:
   148	        overall = "OFFLINE"
   149	    elif "DEGRADED" in statuses:
   150	        overall = "DEGRADED"
   151	    else:
   152	        overall = "HEALTHY"
   153	    return {
   154	        "status": overall,
   155	        "components": components,
   156	        "last_check_at": checked_at,
   157	        "latency": _latency_summary(),
   158	        "simulated": True,
   159	    }
     1	from __future__ import annotations
     2	
     3	import asyncio
     4	import json
     5	import logging
     6	import os
     7	from contextlib import asynccontextmanager
     8	
     9	from fastapi import FastAPI
    10	from fastapi.responses import Response
    11	from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    12	
    13	from core.metrics import health_checks, recommendation_job_failures
    14	from core.sim_client import SimClient
    15	from worker.executor import Executor
    16	from worker.forecast_job import ForecastJob
    17	from worker.forecaster import RemoteForecaster
    18	from worker.ingest import SnapshotIngestor
    19	from worker.recommend_job import RecommendationJob
    20	from worker.sse import SSEConsumer
    21	from worker.store import PostgresStore
    22	
    23	logger = logging.getLogger("fuel_simulator.worker.main")
    24	
    25	
    26	async def _wait_for_stop(stop: asyncio.Event, seconds: float) -> None:
    27	    try:
    28	        await asyncio.wait_for(stop.wait(), timeout=seconds)
    29	    except TimeoutError:
    30	        pass
    31	
    32	
    33	async def _poll_loop(ingestor: SnapshotIngestor, interval_s: float, stop: asyncio.Event) -> None:
    34	    while not stop.is_set():
    35	        started = asyncio.get_running_loop().time()
    36	        await ingestor.run_once()
    37	        elapsed = asyncio.get_running_loop().time() - started
    38	        await _wait_for_stop(stop, max(0.0, interval_s - elapsed))
    39	
    40	
    41	@asynccontextmanager
    42	async def lifespan(app: FastAPI):
    43	    database_url = os.getenv("DATABASE_URL")
    44	    if not database_url:
    45	        yield
    46	        return
    47	
    48	    store = await PostgresStore.connect(database_url)
    49	    client = SimClient(
    50	        os.getenv("SIM_BASE_URL", "http://localhost:8000"),
    51	        max_retries=max(0, int(os.getenv("SIM_MAX_RETRIES", "3"))),
    52	        connect_timeout_s=max(0.1, float(os.getenv("SIM_CONNECT_TIMEOUT_S", "2"))),
    53	        read_timeout_s=max(0.1, float(os.getenv("SIM_READ_TIMEOUT_S", "3"))),
    54	        stream_read_timeout_s=max(16.0, float(os.getenv("SIM_STREAM_READ_TIMEOUT_S", "20"))),
    55	        breaker_failure_threshold=max(1, int(os.getenv("SIM_BREAKER_FAILURE_THRESHOLD", "5"))),
    56	        breaker_reset_after_s=max(0.1, float(os.getenv("SIM_BREAKER_RESET_S", "10"))),
    57	    )
    58	    predictor = RemoteForecaster(
    59	        os.getenv("PREDICTOR_URL", "http://predictor:8103"),
    60	        timeout_s=max(0.1, float(os.getenv("PREDICTOR_TIMEOUT_S", "1.5"))),
    61	        failure_threshold=max(1, int(os.getenv("PREDICTOR_BREAKER_FAILURE_THRESHOLD", "5"))),
    62	        reset_after_s=max(0.1, float(os.getenv("PREDICTOR_BREAKER_RESET_S", "10"))),
    63	    )
    64	    forecast_job = ForecastJob(store, predictor)
    65	    recommendation_job = RecommendationJob(store)
    66	
    67	    async def process_snapshot(snapshot):
    68	        forecasts = await forecast_job.run(snapshot)
    69	        if forecasts:
    70	            try:
    71	                await recommendation_job.run(snapshot, forecasts)
    72	                await store.heartbeat(
    73	                    "decision_engine",
    74	                    {"tick": snapshot.instance.tick, "status": "ok"},
    75	                )
    76	            except Exception as exc:
    77	                recommendation_job_failures.inc()
    78	                logger.exception(
    79	                    json.dumps(
    80	                        {
    81	                            "event": "recommendation_job_failed",
    82	                            "tick": snapshot.instance.tick,
    83	                            "error_type": type(exc).__name__,
    84	                        }
    85	                    )
    86	                )
    87	
    88	    ingestor = SnapshotIngestor(client, store, on_snapshot=process_snapshot)
    89	    executor = Executor(store, client, ingestor.fetch_snapshot)
    90	    stop = asyncio.Event()
    91	    app.state.store = store
    92	    app.state.sim_client = client
    93	    app.state.ingestor = ingestor
    94	    app.state.executor = executor
    95	    await ingestor.run_once()
    96	    interval_s = max(0.1, float(os.getenv("INGEST_INTERVAL_S", "5")))
    97	    poll_task = asyncio.create_task(_poll_loop(ingestor, interval_s, stop))
    98	    sse_task = asyncio.create_task(SSEConsumer(client, ingestor.run_once).run(stop_event=stop))
    99	    executor_task = asyncio.create_task(executor.run(stop))
   100	    try:
   101	        yield
   102	    finally:
   103	        stop.set()
   104	        for task in (poll_task, sse_task, executor_task):
   105	            task.cancel()
   106	        await asyncio.gather(poll_task, sse_task, return_exceptions=True)
   107	        await predictor.close()
   108	        await client.close()
   109	        await store.close()
   110	
   111	
   112	app = FastAPI(title="Fuel Supply Platform Worker", version="0.1.0", lifespan=lifespan)
   113	
   114	
   115	@app.get("/health")
   116	def health() -> dict[str, str]:
   117	    health_checks.labels(service="worker").inc()
   118	    return {"status": "ok", "service": "worker"}
   119	
   120	
   121	@app.get("/metrics", include_in_schema=False)
   122	def metrics() -> Response:
   123	    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
     1	"""Compute and persist station/fuel risk after each new validated snapshot."""
     2	
     3	from __future__ import annotations
     4	
     5	import inspect
     6	import json
     7	import logging
     8	from statistics import mean
     9	from typing import Protocol
    10	
    11	from core.forecast import expected_demand
    12	from core.metrics import (
    13	    forecast_error_liters,
    14	    forecast_mape,
    15	    forecasts_computed,
    16	    hours_to_stockout_gauge,
    17	    policy_fallbacks,
    18	    stockout_probability,
    19	)
    20	from core.models import FuelType, Snapshot, Station
    21	from core.risk import ForecastRecord, forecast_pair
    22	from worker.forecaster import BaselineForecaster, RemoteForecastError
    23	
    24	logger = logging.getLogger("fuel_simulator.worker.forecast")
    25	
    26	
    27	class Forecaster(Protocol):
    28	    def forecast(
    29	        self, snapshot: Snapshot, station: Station, fuel: FuelType, seed: int
    30	    ) -> ForecastRecord | object: ...
    31	
    32	
    33	class LocalForecaster:
    34	    """Pure local forecast implementation, replaceable by a remote service later."""
    35	
    36	    def forecast(
    37	        self, snapshot: Snapshot, station: Station, fuel: FuelType, seed: int
    38	    ) -> ForecastRecord:
    39	        return forecast_pair(snapshot, station, fuel, seed=seed)
    40	
    41	
    42	class ForecastStore(Protocol):
    43	    async def persist_forecasts(
    44	        self, snapshot: Snapshot, records: list[ForecastRecord]
    45	    ) -> None: ...
    46	
    47	    async def set_predictor_incident(self, active: bool, reason: str | None = None) -> None: ...
    48	
    49	
    50	class ForecastJob:
    51	    def __init__(
    52	        self,
    53	        store: ForecastStore,
    54	        forecaster: Forecaster | None = None,
    55	        fallback: Forecaster | None = None,
    56	    ) -> None:
    57	        self.store = store
    58	        self.forecaster = forecaster or LocalForecaster()
    59	        self.fallback = fallback or BaselineForecaster()
    60	        self._last_signature: tuple[object, ...] | None = None
    61	
    62	    async def run(self, snapshot: Snapshot) -> list[ForecastRecord]:
    63	        signature = (
    64	            snapshot.instance.id,
    65	            snapshot.instance.seed,
    66	            snapshot.instance.tick,
    67	            snapshot.instance.sim_time,
    68	            snapshot.stale,
    69	            snapshot.data_status,
    70	        )
    71	        if signature == self._last_signature:
    72	            return []
    73	        records: list[ForecastRecord] = []
    74	        fallback_reason: str | None = None
    75	        for station in snapshot.stations:
    76	            for fuel_index, fuel in enumerate(FuelType):
    77	                pair_offset = sum(station.id.encode("utf-8")) + fuel_index * 1009
    78	                seed = (
    79	                    snapshot.instance.seed + snapshot.instance.tick * 9176 + pair_offset
    80	                ) % 2**32
    81	                try:
    82	                    record = self.forecaster.forecast(snapshot, station, fuel, seed)
    83	                    if inspect.isawaitable(record):
    84	                        record = await record
    85	                except RemoteForecastError as exc:
    86	                    fallback_reason = fallback_reason or exc.reason
    87	                    policy_fallbacks.labels(reason=exc.reason).inc()
    88	                    logger.warning(
    89	                        json.dumps(
    90	                            {
    91	                                "timestamp": snapshot.fetched_at.isoformat(),
    92	                                "level": "warning",
    93	                                "service": "worker",
    94	                                "event": "predictor_fallback",
    95	                                "tick": snapshot.instance.tick,
    96	                                "correlation_id": None,
    97	                                "reason": exc.reason,
    98	                            }
    99	                        )
   100	                    )
   101	                    record = self.fallback.forecast(snapshot, station, fuel, seed)
   102	                    if inspect.isawaitable(record):
   103	                        record = await record
   104	                assert isinstance(record, ForecastRecord)
   105	                records.append(record)
   106	                forecasts_computed.labels(risk_level=record.forecast.risk_level.value).inc()
   107	                labels = {"station": station.id, "fuel": fuel.value}
   108	                probability = record.forecast.stockout_probability_24h
   109	                stockout_probability.labels(**labels).set(probability)
   110	                hours = record.forecast.hours_to_stockout
   111	                hours_to_stockout_gauge.labels(**labels).set(
   112	                    float(hours) if hours is not None else float("nan")
   113	                )
   114	                self._record_error(snapshot, station, fuel, record)
   115	        await self.store.set_predictor_incident(fallback_reason is not None, fallback_reason)
   116	        await self.store.persist_forecasts(snapshot, records)
   117	        self._last_signature = signature
   118	        return records
   119	
   120	    @staticmethod
   121	    def _record_error(
   122	        snapshot: Snapshot,
   123	        station: Station,
   124	        fuel: FuelType,
   125	        record: ForecastRecord,
   126	        *,
   127	        window: int = 12,
   128	    ) -> None:
   129	        history = sorted(
   130	            (
   131	                row
   132	                for row in snapshot.demand_history
   133	                if row.station_id == station.id and row.fuel_type is fuel
   134	            ),
   135	            key=lambda row: (row.tick, row.id),
   136	        )[-window:]
   137	        if not history:
   138	            return
   139	        ratio = float(record.drivers["recent_ratio"])
   140	        errors = []
   141	        percentage_errors = []
   142	        for observation in history:
   143	            baseline = expected_demand(
   144	                station.demand_profile,
   145	                fuel,
   146	                observation.sim_time,
   147	                1.0,
   148	                snapshot.instance.tick_minutes,
   149	            )
   150	            errors.append(abs(observation.demand_liters - baseline * ratio))
   151	            if baseline > 0:
   152	                percentage_errors.append(
   153	                    abs(observation.demand_liters - baseline * ratio) / baseline
   154	                )
   155	        forecast_error_liters.labels(station_id=station.id, fuel_type=fuel.value).set(mean(errors))
   156	        if percentage_errors:
   157	            forecast_mape.labels(station=station.id, fuel=fuel.value).set(mean(percentage_errors))
     1	import type { HealthResponse } from "../../types/api";
     2	
     3	const displayName: Record<string, string> = {
     4	  backend: "API backend",
     5	  database: "Database",
     6	  worker: "Worker",
     7	  simulator: "Simulator / worker feed",
     8	  predictor: "Predictor",
     9	  decision_engine: "Decision engine",
    10	};
    11	
    12	export default function HealthPage({
    13	  report,
    14	  loading,
    15	  error,
    16	}: {
    17	  report?: HealthResponse;
    18	  loading: boolean;
    19	  error: boolean;
    20	}) {
    21	  return (
    22	    <section className="health-page">
    23	      <div className="overview-heading">
    24	        <div><p className="eyebrow">SIMULATED PLATFORM HEALTH</p><h2>System health</h2></div>
    25	        {report && <span className={`health-overall health-${report.status.toLowerCase()}`}>{report.status}</span>}
    26	      </div>
    27	      {loading && <p className="empty-note" role="status">Checking services…</p>}
    28	      {error && <p className="notice notice-warning" role="status">Health details are temporarily unavailable.</p>}
    29	      {report && (
    30	        <>
    31	          <div className="health-grid">
    32	            {Object.entries(report.components).map(([name, component]) => (
    33	              <article className="health-card panel" key={name}>
    34	                <div><h3>{displayName[name] ?? name}</h3><span className={`health-overall health-${component.status.toLowerCase()}`}>{component.status}</span></div>
    35	                <p>{component.age_seconds === null ? "Live probe" : `Last update ${Math.floor(component.age_seconds)}s ago`}</p>
    36	              </article>
    37	            ))}
    38	          </div>
    39	          <section className="health-summary panel" aria-label="API performance">
    40	            <h3>API performance</h3>
    41	            <p>In-process p95 latency: {(report.latency.p95_seconds * 1000).toFixed(0)} ms</p>
    42	            <p>5xx error rate: {(report.latency.error_rate * 100).toFixed(2)}%</p>
    43	            <small>Last checked {new Date(report.last_check_at).toLocaleTimeString()}</small>
    44	          </section>
    45	        </>
    46	      )}
    47	    </section>
    48	  );
    49	}
     1	apiVersion: 1
     2	groups:
     3	  - orgId: 1
     4	    name: Fuel Supply Platform
     5	    folder: Fuel Supply Platform
     6	    interval: 1m
     7	    rules:
     8	      - uid: snapshot-age-high
     9	        title: Snapshot age over 30 seconds
    10	        condition: A
    11	        data:
    12	          - refId: A
    13	            relativeTimeRange: {from: 300, to: 0}
    14	            datasourceUid: prometheus
    15	            model: {expr: "snapshot_age_seconds > 30", instant: true, refId: A, datasource: {type: prometheus, uid: prometheus}, intervalMs: 1000, maxDataPoints: 43200}
    16	        noDataState: NoData
    17	        execErrState: Error
    18	        for: 1m
    19	        annotations: {summary: "The latest accepted simulator snapshot is older than 30 seconds."}
    20	        labels: {severity: warning}
    21	      - uid: simulator-breaker-open
    22	        title: Simulator circuit breaker open
    23	        condition: A
    24	        data:
    25	          - refId: A
    26	            relativeTimeRange: {from: 300, to: 0}
    27	            datasourceUid: prometheus
    28	            model: {expr: "sim_breaker_state{state=\"OPEN\"} == 1", instant: true, refId: A, datasource: {type: prometheus, uid: prometheus}, intervalMs: 1000, maxDataPoints: 43200}
    29	        noDataState: NoData
    30	        execErrState: Error
    31	        for: 1m
    32	        annotations: {summary: "The worker simulator client breaker is open."}
    33	        labels: {severity: critical}
    34	      - uid: api-5xx-rate-high
    35	        title: API 5xx rate high
    36	        condition: A
    37	        data:
    38	          - refId: A
    39	            relativeTimeRange: {from: 300, to: 0}
    40	            datasourceUid: prometheus
    41	            model: {expr: "sum(rate(http_requests_total{status_class=\"5xx\"}[5m])) > 1", instant: true, refId: A, datasource: {type: prometheus, uid: prometheus}, intervalMs: 1000, maxDataPoints: 43200}
    42	        noDataState: NoData
    43	        execErrState: Error
    44	        for: 2m
    45	        annotations: {summary: "The API is returning more than one 5xx response per second."}
    46	        labels: {severity: warning}
    47	      - uid: predictor-fallback-active
    48	        title: Predictor fallback active
    49	        condition: A
    50	        data:
    51	          - refId: A
    52	            relativeTimeRange: {from: 300, to: 0}
    53	            datasourceUid: prometheus
    54	            model: {expr: "increase(policy_fallback_total[5m]) > 0", instant: true, refId: A, datasource: {type: prometheus, uid: prometheus}, intervalMs: 1000, maxDataPoints: 43200}
    55	        noDataState: NoData
    56	        execErrState: Error
    57	        for: 0s
    58	        annotations: {summary: "A forecast or policy used its fallback path in the last five minutes."}
    59	        labels: {severity: warning}

exec
/bin/zsh -lc "rg -n 'snapshot_age|data-health|stale|OFFLINE|fallback|worker.*up|up\\{' backend/shared/core/metrics.py backend/api web/src tests observability/prometheus observability/grafana/provisioning/alerting tests/integration/test_resilience.py tests/integration/test_health_api.py && nl -ba backend/shared/core/metrics.py | sed -n '1,240p'; nl -ba backend/api/routes/data.py | sed -n '1,180p'; nl -ba web/src/features/dashboard/DashboardPage.tsx | sed -n '1,220p'; nl -ba tests/integration/test_resilience.py | sed -n '1,320p'; nl -ba tests/integration/test_health_api.py | sed -n '1,300p'" in /Users/abrar/project/fuel_simulator
 succeeded in 0ms:
observability/grafana/provisioning/alerting/alerts.yml:15:            model: {expr: "snapshot_age_seconds > 30", instant: true, refId: A, datasource: {type: prometheus, uid: prometheus}, intervalMs: 1000, maxDataPoints: 43200}
observability/grafana/provisioning/alerting/alerts.yml:47:      - uid: predictor-fallback-active
observability/grafana/provisioning/alerting/alerts.yml:48:        title: Predictor fallback active
observability/grafana/provisioning/alerting/alerts.yml:54:            model: {expr: "increase(policy_fallback_total[5m]) > 0", instant: true, refId: A, datasource: {type: prometheus, uid: prometheus}, intervalMs: 1000, maxDataPoints: 43200}
observability/grafana/provisioning/alerting/alerts.yml:58:        annotations: {summary: "A forecast or policy used its fallback path in the last five minutes."}
tests/integration/test_health_api.py:30:            "stale": False,
tests/integration/test_health_api.py:72:    assert report["status"] == "OFFLINE"
tests/integration/test_health_api.py:73:    assert report["components"]["database"]["status"] == "OFFLINE"
tests/integration/test_health_api.py:78:def test_health_marks_stale_worker_and_decision_engine(monkeypatch) -> None:
tests/integration/test_health_api.py:88:    assert report["status"] == "OFFLINE"
tests/integration/test_health_api.py:89:    assert report["components"]["simulator"]["status"] == "OFFLINE"
tests/integration/test_health_api.py:94:def test_stale_decision_engine_degrades_health_without_marking_simulator_offline(
tests/integration/test_health_api.py:30:            "stale": False,
tests/integration/test_health_api.py:72:    assert report["status"] == "OFFLINE"
tests/integration/test_health_api.py:73:    assert report["components"]["database"]["status"] == "OFFLINE"
tests/integration/test_health_api.py:78:def test_health_marks_stale_worker_and_decision_engine(monkeypatch) -> None:
tests/integration/test_health_api.py:88:    assert report["status"] == "OFFLINE"
tests/integration/test_health_api.py:89:    assert report["components"]["simulator"]["status"] == "OFFLINE"
tests/integration/test_health_api.py:94:def test_stale_decision_engine_degrades_health_without_marking_simulator_offline(
tests/integration/test_resilience.py:31:async def test_stale_data_fault_is_persisted_as_degraded_and_flagged():
tests/integration/test_resilience.py:33:    client.stale = True
tests/integration/test_resilience.py:37:    assert store.snapshots[0].stale is True
backend/shared/core/metrics.py:21:snapshot_age = Gauge("snapshot_age_seconds", "Age of the latest accepted snapshot")
backend/shared/core/metrics.py:34:recommendation_fallbacks = Counter(
backend/shared/core/metrics.py:35:    "recommendation_fallbacks_total", "Heuristic recommendation fallbacks"
backend/shared/core/metrics.py:37:policy_fallbacks = Counter("policy_fallback_total", "Fallback invocations by cause", ["reason"])
tests/integration/test_resilience.py:31:async def test_stale_data_fault_is_persisted_as_degraded_and_flagged():
tests/integration/test_resilience.py:33:    client.stale = True
tests/integration/test_resilience.py:37:    assert store.snapshots[0].stale is True
backend/api/routes/read.py:35:def _data_status(age_seconds: float, stale: bool, stored_status: str) -> str:
backend/api/routes/read.py:37:        return "OFFLINE"
backend/api/routes/read.py:38:    if stale or age_seconds >= 15 or stored_status != "HEALTHY":
backend/api/routes/read.py:49:    stale = bool(record["stale"])
backend/api/routes/read.py:50:    status = _data_status(age_seconds, stale, str(record["data_status"]))
backend/api/routes/read.py:53:    snapshot["stale"] = stale
backend/api/routes/read.py:55:    return snapshot, fetched_at, age_seconds, status, stale
backend/api/routes/read.py:60:    snapshot, fetched_at, age, status, stale = await _latest(repository)
backend/api/routes/read.py:66:        "stale": stale,
backend/api/routes/read.py:71:@router.get("/data-health")
backend/api/routes/read.py:73:    _, fetched_at, age, status, stale = await _latest(repository)
backend/api/routes/read.py:78:        "stale": stale,
backend/api/routes/read.py:85:    snapshot, fetched_at, age, status, stale = await _latest(repository)
backend/api/routes/read.py:93:        "stale": stale,
backend/api/routes/read.py:100:    snapshot, fetched_at, age, status, stale = await _latest(repository)
backend/api/routes/read.py:106:        "stale": stale,
backend/api/routes/read.py:113:    _, fetched_at, age, status, stale = await _latest(repository)
backend/api/routes/read.py:120:        "stale": stale,
backend/api/routes/read.py:133:    _, fetched_at, age, status, stale = await _latest(repository)
backend/api/routes/read.py:142:        "stale": stale,
web/src/app/App.tsx:40:      {state && (state.stale || state.data_status !== "HEALTHY") && (
web/src/app/App.tsx:42:          <strong>Data is {state.data_status.toLowerCase()}.</strong> The snapshot is {Math.floor(state.data_age_seconds)} seconds old{state.stale ? " and marked stale by the simulator" : ""}.
tests/unit/test_policy.py:30:        stale=False,
tests/integration/test_sim_client.py:30:async def test_get_instance_returns_typed_result_and_stale_flag() -> None:
tests/integration/test_sim_client.py:38:    assert result.stale is True
tests/integration/test_risk_api.py:43:        "stale": False,
tests/unit/test_store_snapshot.py:70:        stale=False,
tests/integration/test_predictor.py:30:    raw.update(fetched_at="2026-01-02T00:00:00Z", stale=False, data_status="HEALTHY")
web/src/types/api.ts:2:export type DataStatus = "HEALTHY" | "DEGRADED" | "OFFLINE";
web/src/types/api.ts:79:  stale: boolean;
web/src/types/api.ts:116:  stale: boolean;
web/src/types/api.ts:131:  stale: boolean;
web/src/types/api.ts:148:  fallback_used: boolean;
tests/integration/test_read_api.py:27:def seeded_record(age_seconds: int = 0, stale: bool = False) -> dict[str, Any]:
tests/integration/test_read_api.py:39:        "stale": stale,
tests/integration/test_read_api.py:45:        "stale": stale,
tests/integration/test_read_api.py:62:    health = api_client.get("/api/data-health")
tests/integration/test_read_api.py:71:def test_stale_snapshot_returns_200_with_degraded_status(api_client: TestClient) -> None:
tests/integration/test_read_api.py:73:        seeded_record(age_seconds=35, stale=True)
tests/integration/test_read_api.py:79:    assert response.json()["stale"] is True
tests/integration/test_read_api.py:92:    assert response.json()["data_status"] == "OFFLINE"
tests/integration/test_read_api.py:98:    for path in ("/api/state", "/api/data-health", "/api/events", "/api/metrics-summary"):
tests/integration/test_ingest.py:42:        self.stale = False
tests/integration/test_ingest.py:52:        return SimResult(value, self.stale)
tests/integration/test_ingest.py:204:async def test_stale_response_marks_snapshot_degraded() -> None:
tests/integration/test_ingest.py:206:    client.stale = True
tests/integration/test_ingest.py:214:    assert store.snapshots[0].stale is True
web/src/features/shortage-risk/ShortageRiskPage.tsx:86:      {selected && selectedStation && <Suspense fallback={<aside className="trajectory-drawer panel">Loading chart…</aside>}><TrajectoryDrawer station={selectedStation} fuel={selected.fuel} record={trajectory} onClose={onClose} /></Suspense>}
tests/unit/test_explain.py:32:        stale=False,
backend/api/routes/health.py:31:        return "OFFLINE"
backend/api/routes/health.py:71:        return "OFFLINE"
backend/api/routes/health.py:80:        return "OFFLINE", None, {}
backend/api/routes/health.py:82:        return "OFFLINE", None, {}
backend/api/routes/health.py:99:                "database": {"status": "OFFLINE", "age_seconds": None},
backend/api/routes/health.py:100:                "worker": {"status": "OFFLINE", "age_seconds": None},
backend/api/routes/health.py:101:                "simulator": {"status": "OFFLINE", "age_seconds": None},
backend/api/routes/health.py:102:                "decision_engine": {"status": "OFFLINE", "age_seconds": None},
backend/api/routes/health.py:111:            "status": "HEALTHY" if db_ok else "OFFLINE",
backend/api/routes/health.py:123:            snapshot_age = _age_seconds(latest.get("fetched_at")) if latest else None
backend/api/routes/health.py:124:            snapshot_status = str(latest.get("data_status", "OFFLINE")) if latest else "OFFLINE"
backend/api/routes/health.py:125:            if latest and latest.get("stale"):
backend/api/routes/health.py:127:            simulator_status = _status(snapshot_age, snapshot_status)
backend/api/routes/health.py:128:            if worker_status == "OFFLINE":
backend/api/routes/health.py:129:                simulator_status = "OFFLINE"
backend/api/routes/health.py:133:            snapshot_age = None
backend/api/routes/health.py:134:            simulator_status = "OFFLINE"
backend/api/routes/health.py:135:        components["simulator"] = {"status": simulator_status, "age_seconds": snapshot_age}
backend/api/routes/health.py:139:        # The decision pipeline shares the worker process. A stale pipeline
backend/api/routes/health.py:142:        if worker_status != "OFFLINE" and engine_status == "OFFLINE":
backend/api/routes/health.py:147:    if "OFFLINE" in statuses:
backend/api/routes/health.py:148:        overall = "OFFLINE"
backend/api/database.py:46:            SELECT raw_json, fetched_at, stale, data_status
backend/api/database.py:58:            "stale": row["stale"],
web/src/features/allocations/RecommendationsPage.tsx:108:          <span>{item.policy_used}{item.fallback_used ? " · fallback" : ""}</span>
backend/api/db.sql:7:    stale BOOLEAN NOT NULL DEFAULT FALSE,
backend/api/db.sql:8:    data_status TEXT NOT NULL CHECK (data_status IN ('HEALTHY', 'DEGRADED', 'OFFLINE'))
backend/api/db.sql:39:    fallback_used BOOLEAN NOT NULL DEFAULT FALSE,
tests/unit/test_validator.py:31:        stale=False,
tests/unit/test_executor.py:35:        stale=False,
tests/unit/test_executor.py:98:async def test_stale_fresh_read_expires_without_submitting() -> None:
tests/unit/test_executor.py:100:    snapshot.stale = True
tests/unit/test_executor.py:109:    assert "stale" in store.rows[0]["failure_reason"]
tests/unit/test_recommend_job.py:34:        stale=False,
tests/unit/test_recommend_job.py:45:    async def expire_stale_recommendations(self, tick: int) -> None:
tests/unit/test_recommend_job.py:123:    assert all(row["fallback_used"] is True for row in rows)
tests/unit/test_recommend_job.py:128:async def test_job_expires_old_proposals_and_skips_stale_snapshots() -> None:
tests/unit/test_recommend_job.py:140:    snapshot.stale = True
tests/unit/test_forecast_job.py:37:    raw["stale"] = False
tests/unit/test_forecast.py:102:            "stale": False,
tests/unit/test_forecast.py:168:    raw["stale"] = False
     1	"""Shared metric definitions for the Python services."""
     2	
     3	from prometheus_client import Counter, Gauge, Histogram
     4	
     5	health_checks = Counter("service_health_checks_total", "Health checks served", ["service"])
     6	sim_client_requests = Counter(
     7	    "sim_client_requests_total",
     8	    "Simulator requests by endpoint and outcome",
     9	    ["endpoint", "outcome"],
    10	)
    11	sim_client_retries = Counter("sim_client_retries_total", "Simulator request retries", ["endpoint"])
    12	sim_client_failures = Counter(
    13	    "sim_client_failures_total", "Simulator request failures", ["endpoint"]
    14	)
    15	sim_breaker_state = Gauge("sim_breaker_state", "Simulator circuit breaker state", ["state"])
    16	worker_ingest_success = Counter("worker_ingest_success_total", "Successful snapshot ingestions")
    17	worker_ingest_failures = Counter("worker_ingest_failures_total", "Failed snapshot ingestions")
    18	snapshot_rejected = Counter(
    19	    "snapshot_rejected_total", "Snapshots rejected before persistence", ["reason"]
    20	)
    21	snapshot_age = Gauge("snapshot_age_seconds", "Age of the latest accepted snapshot")
    22	forecasts_computed = Counter("forecasts_computed_total", "Forecasts calculated", ["risk_level"])
    23	hours_to_stockout_gauge = Gauge(
    24	    "hours_to_stockout", "Deterministic hours until station/fuel stockout", ["station", "fuel"]
    25	)
    26	stockout_probability = Gauge(
    27	    "stockout_probability", "24-hour stockout probability", ["station", "fuel"]
    28	)
    29	forecast_mape = Gauge(
    30	    "forecast_mape", "Mean absolute percentage demand forecast error", ["station", "fuel"]
    31	)
    32	forecast_job_failures = Counter("forecast_job_failures_total", "Failed forecast jobs")
    33	recommendations_created = Counter("recommendations_created_total", "Recommendations created")
    34	recommendation_fallbacks = Counter(
    35	    "recommendation_fallbacks_total", "Heuristic recommendation fallbacks"
    36	)
    37	policy_fallbacks = Counter("policy_fallback_total", "Fallback invocations by cause", ["reason"])
    38	recommendations_by_status = Gauge(
    39	    "recommendations_total", "Recommendation lifecycle events by status", ["status"]
    40	)
    41	alerts_active = Gauge("alerts_active", "Active stockout risk incidents by severity", ["severity"])
    42	sim_service_level = Gauge("sim_service_level", "Latest simulator service level")
    43	recommendation_job_failures = Counter(
    44	    "recommendation_job_failures_total", "Failed recommendation jobs"
    45	)
    46	allocation_executor_failures = Counter(
    47	    "allocation_executor_failures_total", "Failed allocation executor poll cycles"
    48	)
    49	simulator_allocation_rejections = Counter(
    50	    "simulator_allocation_rejections_total",
    51	    "Allocation submissions rejected by the simulator",
    52	    ["code"],
    53	)
    54	forecast_error_liters = Gauge(
    55	    "forecast_error_liters",
    56	    "Mean absolute demand forecast error in liters",
    57	    ["station_id", "fuel_type"],
    58	)
    59	sse_events = Counter("worker_sse_events_total", "SSE hints received")
    60	sse_reconnects = Counter("worker_sse_reconnects_total", "SSE reconnect attempts")
    61	api_http_requests = Counter(
    62	    "http_requests_total",
    63	    "API requests by route and status class",
    64	    ["method", "route", "status_class"],
    65	)
    66	api_http_request_duration = Histogram(
    67	    "http_request_duration_seconds", "API request duration by route", ["method", "route"]
    68	)
nl: backend/api/routes/data.py: No such file or directory
     1	import type { Incident, Snapshot, SimulatorEvent } from "../../types/api";
     2	import { localTime, quantity } from "../../lib/format";
     3	import DepotsPanel from "../inventory/DepotsPanel";
     4	import InventoryMatrix from "../inventory/InventoryMatrix";
     5	import EventsPanel from "../incidents/EventsPanel";
     6	import RoutesPanel from "../network/RoutesPanel";
     7	
     8	export default function DashboardPage({ snapshot, events, incidents }: { snapshot: Snapshot; events: SimulatorEvent[]; incidents: Incident[] }) {
     9	  const serviceLevel = Math.round(snapshot.metrics.service_level * 100);
    10	  return <>
    11	    <section className="overview-heading">
    12	      <div>
    13	        <p className="eyebrow">CURRENT NETWORK STATE</p>
    14	        <h2>Supply overview</h2>
    15	        <p className="muted">Simulator time {localTime(snapshot.instance.sim_time)} · Tick {snapshot.instance.tick} · {snapshot.instance.tick_minutes} minutes per tick</p>
    16	      </div>
    17	      <div className="metric-card"><span className="metric-label">SERVICE LEVEL</span><strong>{serviceLevel}%</strong><span>{quantity(snapshot.metrics.unmet_demand_liters)} L unmet demand</span></div>
    18	    </section>
    19	    <section className="panel section-panel">
    20	      <div className="section-heading"><div><p className="eyebrow">ON-HAND INVENTORY</p><h2>Stations by fuel</h2></div><span className="section-note">Inventory shown against station capacity</span></div>
    21	      <InventoryMatrix stations={snapshot.stations} />
    22	    </section>
    23	    <section className="panel section-panel">
    24	      <div className="section-heading"><div><p className="eyebrow">DEPOT INVENTORY</p><h2>Supply sources</h2></div><span className="section-note">On-hand liters by fuel type</span></div>
    25	      <DepotsPanel depots={snapshot.depots} />
    26	    </section>
    27	    <div className="lower-grid"><RoutesPanel routes={snapshot.routes} /><EventsPanel events={events} incidents={incidents} /></div>
    28	  </>;
    29	}
     1	from __future__ import annotations
     2	
     3	import pytest
     4	from tests.integration.test_ingest import FakeClient, FakeStore
     5	from worker.ingest import SnapshotIngestor
     6	
     7	from core.models import DataStatus
     8	
     9	
    10	@pytest.mark.asyncio
    11	@pytest.mark.parametrize(
    12	    ("fault", "expected_status"),
    13	    [("unavailable", "DEGRADED"), ("error_rate", "DEGRADED"), ("latency", "DEGRADED")],
    14	)
    15	async def test_transport_faults_keep_last_snapshot_and_mark_degraded(fault, expected_status):
    16	    assert fault in {"unavailable", "error_rate", "latency"}
    17	    client = FakeClient()
    18	    store = FakeStore()
    19	    ingestor = SnapshotIngestor(client, store)
    20	    await ingestor.run_once()
    21	    last_good = store.snapshots[0]
    22	    client.failure_method = "get_routes"
    23	
    24	    assert await ingestor.run_once() is False
    25	    assert store.snapshots == [last_good]
    26	    assert store.latest_status == expected_status
    27	    assert store.events[-1]["kind"] == "snapshot_rejected"
    28	
    29	
    30	@pytest.mark.asyncio
    31	async def test_stale_data_fault_is_persisted_as_degraded_and_flagged():
    32	    client = FakeClient()
    33	    client.stale = True
    34	    store = FakeStore()
    35	    await SnapshotIngestor(client, store).run_once()
    36	
    37	    assert store.snapshots[0].stale is True
    38	    assert store.snapshots[0].data_status is DataStatus.DEGRADED
    39	
    40	
    41	@pytest.mark.asyncio
    42	async def test_malformed_data_fault_retains_last_good_snapshot_and_records_rejection():
    43	    client = FakeClient()
    44	    store = FakeStore()
    45	    ingestor = SnapshotIngestor(client, store)
    46	    await ingestor.run_once()
    47	    last_good = store.snapshots[0]
    48	    client.malformed_stations = [{"id": "incomplete"}]
    49	
    50	    assert await ingestor.run_once() is False
    51	    assert store.snapshots == [last_good]
    52	    assert store.latest_status == "DEGRADED"
    53	    assert store.events[-1]["kind"] == "snapshot_rejected"
     1	from __future__ import annotations
     2	
     3	from datetime import datetime, timedelta, timezone
     4	from typing import Any
     5	
     6	import respx
     7	from api.main import app
     8	from fastapi.testclient import TestClient
     9	from httpx import Response
    10	
    11	
    12	class HealthRepository:
    13	    def __init__(self, *, database_ok: bool = True, worker_age_s: int = 1, engine_age_s: int = 1):
    14	        now = datetime.now(timezone.utc)
    15	        self.database_ok = database_ok
    16	        self.rows = {
    17	            "worker": {
    18	                "component": "worker",
    19	                "last_seen": now - timedelta(seconds=worker_age_s),
    20	                "detail": {"data_status": "HEALTHY", "breaker_state": "CLOSED"},
    21	            },
    22	            "decision_engine": {
    23	                "component": "decision_engine",
    24	                "last_seen": now - timedelta(seconds=engine_age_s),
    25	                "detail": {"status": "ok"},
    26	            },
    27	        }
    28	        self.snapshot = {
    29	            "fetched_at": now - timedelta(seconds=worker_age_s),
    30	            "stale": False,
    31	            "data_status": "HEALTHY",
    32	        }
    33	
    34	    async def check_database(self) -> bool:
    35	        return self.database_ok
    36	
    37	    async def get_heartbeat(self, component: str) -> dict[str, Any] | None:
    38	        return self.rows.get(component)
    39	
    40	    async def get_latest_snapshot(self) -> dict[str, Any]:
    41	        return self.snapshot
    42	
    43	
    44	@respx.mock
    45	def test_health_aggregates_components_and_latency(monkeypatch) -> None:
    46	    monkeypatch.setenv("PREDICTOR_URL", "http://predictor.test")
    47	    respx.get("http://predictor.test/health").mock(
    48	        return_value=Response(200, json={"status": "ok"})
    49	    )
    50	    with TestClient(app) as client:
    51	        app.state.repository = HealthRepository()
    52	        response = client.get("/api/health")
    53	
    54	    report = response.json()
    55	    assert report["status"] == "HEALTHY"
    56	    assert report["components"]["predictor"]["status"] == "HEALTHY"
    57	    assert report["components"]["simulator"]["status"] == "HEALTHY"
    58	    assert report["last_check_at"]
    59	    assert report["latency"]["p95_seconds"] >= 0
    60	    assert 0 <= report["latency"]["error_rate"] <= 1
    61	
    62	
    63	@respx.mock
    64	def test_health_reports_offline_database_and_predictor(monkeypatch) -> None:
    65	    monkeypatch.setenv("PREDICTOR_URL", "http://predictor.test")
    66	    respx.get("http://predictor.test/health").mock(return_value=Response(503))
    67	    with TestClient(app) as client:
    68	        app.state.repository = HealthRepository(database_ok=False)
    69	        response = client.get("/api/health")
    70	
    71	    report = response.json()
    72	    assert report["status"] == "OFFLINE"
    73	    assert report["components"]["database"]["status"] == "OFFLINE"
    74	    assert report["components"]["predictor"]["status"] == "DEGRADED"
    75	
    76	
    77	@respx.mock
    78	def test_health_marks_stale_worker_and_decision_engine(monkeypatch) -> None:
    79	    monkeypatch.setenv("PREDICTOR_URL", "http://predictor.test")
    80	    respx.get("http://predictor.test/health").mock(
    81	        return_value=Response(200, json={"status": "ok"})
    82	    )
    83	    with TestClient(app) as client:
    84	        app.state.repository = HealthRepository(worker_age_s=130, engine_age_s=20)
    85	        response = client.get("/api/health")
    86	
    87	    report = response.json()
    88	    assert report["status"] == "OFFLINE"
    89	    assert report["components"]["simulator"]["status"] == "OFFLINE"
    90	    assert report["components"]["decision_engine"]["status"] == "DEGRADED"
    91	
    92	
    93	@respx.mock
    94	def test_stale_decision_engine_degrades_health_without_marking_simulator_offline(
    95	    monkeypatch,
    96	) -> None:
    97	    monkeypatch.setenv("PREDICTOR_URL", "http://predictor.test")
    98	    respx.get("http://predictor.test/health").mock(
    99	        return_value=Response(200, json={"status": "ok"})
   100	    )
   101	    with TestClient(app) as client:
   102	        app.state.repository = HealthRepository(worker_age_s=1, engine_age_s=466)
   103	        response = client.get("/api/health")
   104	
   105	    report = response.json()
   106	    assert report["status"] == "DEGRADED"
   107	    assert report["components"]["worker"]["status"] == "HEALTHY"
   108	    assert report["components"]["simulator"]["status"] == "HEALTHY"
   109	    assert report["components"]["decision_engine"]["status"] == "DEGRADED"

exec
/bin/zsh -lc "nl -ba backend/api/routes/read.py | sed -n '25,100p'; nl -ba web/src/app/App.tsx | sed -n '1,130p'; nl -ba tests/integration/test_sim_client.py | sed -n '1,260p'; nl -ba tests/integration/test_sse.py | sed -n '1,150p'; nl -ba docs/resilience.md | sed -n '1,150p'; nl -ba backend/worker/store.py | sed -n '120,240p'; git diff -- backend/worker/sse.py backend/worker/store.py docs/resilience.md docs/sprint-reports/sprint-05.md tests/integration/test_sse.py tests/unit/test_store_snapshot.py" in /Users/abrar/project/fuel_simulator
 succeeded in 0ms:
    25	
    26	def _as_datetime(value: datetime | str) -> datetime:
    27	    parsed = (
    28	        datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    29	    )
    30	    if parsed.tzinfo is None:
    31	        return parsed.replace(tzinfo=timezone.utc)
    32	    return parsed.astimezone(timezone.utc)
    33	
    34	
    35	def _data_status(age_seconds: float, stale: bool, stored_status: str) -> str:
    36	    if age_seconds > 120:
    37	        return "OFFLINE"
    38	    if stale or age_seconds >= 15 or stored_status != "HEALTHY":
    39	        return "DEGRADED"
    40	    return "HEALTHY"
    41	
    42	
    43	async def _latest(repository: ReadRepository) -> tuple[dict[str, Any], datetime, float, str, bool]:
    44	    record = await repository.get_latest_snapshot()
    45	    if record is None:
    46	        raise HTTPException(status_code=503, detail="No snapshot has been stored")
    47	    fetched_at = _as_datetime(record["fetched_at"])
    48	    age_seconds = max(0.0, (datetime.now(timezone.utc) - fetched_at).total_seconds())
    49	    stale = bool(record["stale"])
    50	    status = _data_status(age_seconds, stale, str(record["data_status"]))
    51	    snapshot = dict(record["raw_json"])
    52	    snapshot["fetched_at"] = fetched_at.isoformat()
    53	    snapshot["stale"] = stale
    54	    snapshot["data_status"] = status
    55	    return snapshot, fetched_at, age_seconds, status, stale
    56	
    57	
    58	@router.get("/state")
    59	async def state(repository: RepositoryDep) -> dict[str, Any]:
    60	    snapshot, fetched_at, age, status, stale = await _latest(repository)
    61	    return {
    62	        "snapshot": snapshot,
    63	        "fetched_at": fetched_at.isoformat(),
    64	        "data_age_seconds": age,
    65	        "data_status": status,
    66	        "stale": stale,
    67	        "simulated": True,
    68	    }
    69	
    70	
    71	@router.get("/data-health")
    72	async def data_health(repository: RepositoryDep) -> dict[str, Any]:
    73	    _, fetched_at, age, status, stale = await _latest(repository)
    74	    return {
    75	        "fetched_at": fetched_at.isoformat(),
    76	        "data_age_seconds": age,
    77	        "data_status": status,
    78	        "stale": stale,
    79	        "simulated": True,
    80	    }
    81	
    82	
    83	@router.get("/events")
    84	async def events(repository: RepositoryDep) -> dict[str, Any]:
    85	    snapshot, fetched_at, age, status, stale = await _latest(repository)
    86	    incidents = await repository.get_incidents()
    87	    return {
    88	        "events": snapshot.get("events", []),
    89	        "incidents": incidents,
    90	        "fetched_at": fetched_at.isoformat(),
    91	        "data_age_seconds": age,
    92	        "data_status": status,
    93	        "stale": stale,
    94	        "simulated": True,
    95	    }
    96	
    97	
    98	@router.get("/metrics-summary")
    99	async def metrics_summary(repository: RepositoryDep) -> dict[str, Any]:
   100	    snapshot, fetched_at, age, status, stale = await _latest(repository)
     1	import { useState } from "react";
     2	import { useQuery } from "@tanstack/react-query";
     3	import Header from "../components/layout/Header";
     4	import PageNavigation, { type Page } from "../components/layout/PageNavigation";
     5	import DashboardPage from "../features/dashboard/DashboardPage";
     6	import RecommendationsPage from "../features/allocations/RecommendationsPage";
     7	import ShortageRiskPage from "../features/shortage-risk/ShortageRiskPage";
     8	import HealthPage from "../features/system-health/HealthPage";
     9	import { fetchEvents, fetchHealth, fetchRisks, fetchState, fetchTrajectory } from "../services/api";
    10	import type { Fuel } from "../types/api";
    11	import { localTime } from "../lib/format";
    12	
    13	export default function App() {
    14	  const [page, setPage] = useState<Page>("overview");
    15	  const [selected, setSelected] = useState<{ stationId: string; fuel: Fuel } | null>(null);
    16	  const [operatorToken, setOperatorToken] = useState("");
    17	  const stateQuery = useQuery({ queryKey: ["state"], queryFn: fetchState, refetchInterval: 3000 });
    18	  const eventsQuery = useQuery({ queryKey: ["events"], queryFn: fetchEvents, refetchInterval: 3000 });
    19	  const risksQuery = useQuery({ queryKey: ["risks"], queryFn: fetchRisks, refetchInterval: 3000 });
    20	  const healthQuery = useQuery({ queryKey: ["health"], queryFn: fetchHealth, refetchInterval: 5000 });
    21	  const trajectoryQuery = useQuery({
    22	    queryKey: ["trajectory", selected?.stationId, selected?.fuel],
    23	    queryFn: () => fetchTrajectory(selected!.stationId, selected!.fuel),
    24	    enabled: selected !== null,
    25	    refetchInterval: 3000,
    26	  });
    27	
    28	  const state = stateQuery.data;
    29	  const snapshot = state?.snapshot;
    30	  const events = eventsQuery.data?.events ?? snapshot?.events ?? [];
    31	  const incidents = eventsQuery.data?.incidents ?? [];
    32	  const apiUnavailable = stateQuery.isError || eventsQuery.isError || (page === "risk" && risksQuery.isError);
    33	
    34	  return (
    35	    <main className="page-shell">
    36	      <Header status={state?.data_status} ageSeconds={state?.data_age_seconds} />
    37	      <PageNavigation page={page} onChange={setPage} />
    38	      {apiUnavailable && <div className="notice notice-warning" role="status"><strong>API unreachable.</strong> Showing the last received state while polling continues.</div>}
    39	      {healthQuery.data && healthQuery.data.status !== "HEALTHY" && <div className="notice notice-degraded" role="status"><strong>System is {healthQuery.data.status.toLowerCase()}.</strong> Review the System health view for component status and data age.</div>}
    40	      {state && (state.stale || state.data_status !== "HEALTHY") && (
    41	        <div className="notice notice-degraded" role="status">
    42	          <strong>Data is {state.data_status.toLowerCase()}.</strong> The snapshot is {Math.floor(state.data_age_seconds)} seconds old{state.stale ? " and marked stale by the simulator" : ""}.
    43	        </div>
    44	      )}
    45	      {page === "health" ? (
    46	        <HealthPage report={healthQuery.data} loading={healthQuery.isLoading} error={healthQuery.isError} />
    47	      ) : !snapshot ? (
    48	        <section className="empty-state panel">
    49	          <p className="eyebrow">LIVE SIMULATOR SNAPSHOT</p>
    50	          <h2>{apiUnavailable ? "API unreachable" : "Waiting for the first snapshot"}</h2>
    51	          <p>{apiUnavailable ? "No saved state is available yet. The dashboard will reconnect automatically." : "The worker is collecting simulator state."}</p>
    52	        </section>
    53	      ) : page === "recommendations" ? (
    54	        <RecommendationsPage token={operatorToken} onTokenChange={setOperatorToken} />
    55	      ) : page === "risk" ? (
    56	        <ShortageRiskPage
    57	          stations={snapshot.stations}
    58	          forecasts={risksQuery.data?.forecasts ?? []}
    59	          trajectory={trajectoryQuery.data}
    60	          selected={selected}
    61	          onSelect={(stationId, fuel) => setSelected({ stationId, fuel })}
    62	          onClose={() => setSelected(null)}
    63	        />
    64	      ) : (
    65	        <DashboardPage snapshot={snapshot} events={events} incidents={incidents} />
    66	      )}
    67	      {state && <footer className="page-footer">All information is simulated. Last successful refresh {localTime(state.fetched_at)}.</footer>}
    68	    </main>
    69	  );
    70	}
     1	import json
     2	
     3	import httpx
     4	import pytest
     5	import respx
     6	
     7	from core.models import Allocation, Instance
     8	from core.sim_client import (
     9	    BreakerState,
    10	    SimBusinessError,
    11	    SimClient,
    12	    SimInvalidResponse,
    13	    SimUnavailable,
    14	)
    15	
    16	INSTANCE = {
    17	    "id": 1,
    18	    "scenario_id": "baseline",
    19	    "scenario_version": "1.0",
    20	    "seed": 12345,
    21	    "sim_time": "2026-01-01T00:00:00",
    22	    "tick": 0,
    23	    "tick_minutes": 15,
    24	    "status": "PAUSED",
    25	}
    26	
    27	
    28	@pytest.mark.asyncio
    29	@respx.mock
    30	async def test_get_instance_returns_typed_result_and_stale_flag() -> None:
    31	    respx.get("http://sim.test/v1/instance").mock(
    32	        return_value=httpx.Response(200, json=INSTANCE, headers={"X-Simulator-Stale": "true"})
    33	    )
    34	    async with SimClient("http://sim.test") as client:
    35	        result = await client.get_instance()
    36	    assert isinstance(result.data, Instance)
    37	    assert result.data.tick_minutes == 15
    38	    assert result.stale is True
    39	
    40	
    41	@pytest.mark.asyncio
    42	@respx.mock
    43	async def test_malformed_json_and_missing_fields_raise_invalid_response() -> None:
    44	    route = respx.get("http://sim.test/v1/instance").mock(
    45	        side_effect=[httpx.Response(200, text="not-json"), httpx.Response(200, json={"id": 1})]
    46	    )
    47	    async with SimClient("http://sim.test", max_retries=0) as client:
    48	        with pytest.raises(SimInvalidResponse):
    49	            await client.get_instance()
    50	        with pytest.raises(SimInvalidResponse):
    51	            await client.get_instance()
    52	    assert route.call_count == 2
    53	
    54	
    55	@pytest.mark.asyncio
    56	@respx.mock
    57	async def test_business_errors_are_typed_and_not_retried() -> None:
    58	    route = respx.get("http://sim.test/v1/instance").mock(
    59	        return_value=httpx.Response(
    60	            409, json={"detail": {"code": "ROUTE_DISRUPTED", "message": "route closed"}}
    61	        )
    62	    )
    63	    async with SimClient("http://sim.test") as client:
    64	        with pytest.raises(SimBusinessError) as caught:
    65	            await client.get_instance()
    66	    assert caught.value.code == "ROUTE_DISRUPTED"
    67	    assert route.call_count == 1
    68	
    69	
    70	@pytest.mark.asyncio
    71	@respx.mock
    72	async def test_validation_error_and_timeout_behavior() -> None:
    73	    validation_route = respx.get("http://sim.test/v1/instance").mock(
    74	        return_value=httpx.Response(
    75	            422,
    76	            json={"detail": [{"loc": ["body", "tick"], "msg": "invalid"}]},
    77	        )
    78	    )
    79	    async with SimClient("http://sim.test") as client:
    80	        with pytest.raises(SimBusinessError) as caught:
    81	            await client.get_instance()
    82	    assert caught.value.code == "VALIDATION_ERROR"
    83	    assert validation_route.call_count == 1
    84	
    85	
    86	@pytest.mark.asyncio
    87	@respx.mock
    88	async def test_connection_timeout_retries_then_succeeds_without_real_sleep() -> None:
    89	    route = respx.get("http://sim.test/v1/instance").mock(
    90	        side_effect=[
    91	            httpx.ConnectTimeout("connect timeout"),
    92	            httpx.Response(200, json=INSTANCE),
    93	        ]
    94	    )
    95	    delays: list[float] = []
    96	
    97	    async def sleep(delay: float) -> None:
    98	        delays.append(delay)
    99	
   100	    async with SimClient("http://sim.test", sleep=sleep, jitter=lambda _: 0) as client:
   101	        result = await client.get_instance()
   102	    assert result.data.tick == 0
   103	    assert route.call_count == 2
   104	    assert delays == [0.2]
   105	
   106	
   107	@pytest.mark.asyncio
   108	@respx.mock
   109	async def test_fault_injected_retries_with_bounded_jittered_backoff() -> None:
   110	    route = respx.get("http://sim.test/v1/instance").mock(
   111	        side_effect=[
   112	            httpx.Response(503, json={"error": {"code": "FAULT_INJECTED"}}),
   113	            httpx.Response(503, json={"detail": {"code": "FAULT_INJECTED"}}),
   114	            httpx.Response(503, json={"detail": {"code": "FAULT_INJECTED"}}),
   115	            httpx.Response(200, json=INSTANCE),
   116	        ]
   117	    )
   118	    delays: list[float] = []
   119	
   120	    async def sleep(delay: float) -> None:
   121	        delays.append(delay)
   122	
   123	    async with SimClient("http://sim.test", sleep=sleep, jitter=lambda _: 0.05) as client:
   124	        result = await client.get_instance()
   125	    assert result.data.tick == 0
   126	    assert route.call_count == 4
   127	    assert delays == pytest.approx([0.25, 0.45, 0.85])
   128	
   129	
   130	@pytest.mark.asyncio
   131	@respx.mock
   132	async def test_post_retry_reuses_identical_idempotent_body() -> None:
   133	    request_body = {
   134	        "idempotency_key": "rec-fixed",
   135	        "source_depot_id": "depot-gazipur",
   136	        "destination_station_id": "station-mirpur",
   137	        "route_id": "route-gazipur-mirpur",
   138	        "fuel_type": "DIESEL",
   139	        "quantity": 100,
   140	    }
   141	    response = {
   142	        "id": 1,
   143	        **request_body,
   144	        "created_tick": 0,
   145	        "departure_tick": None,
   146	        "expected_arrival_tick": None,
   147	        "actual_arrival_tick": None,
   148	        "status": "PENDING",
   149	        "failure_reason": None,
   150	    }
   151	    route = respx.post("http://sim.test/v1/allocations").mock(
   152	        side_effect=[
   153	            httpx.Response(503, json={"error": {"code": "FAULT_INJECTED"}}),
   154	            httpx.Response(201, json=response),
   155	        ]
   156	    )
   157	    async with SimClient(
   158	        "http://sim.test", sleep=lambda _: _no_sleep(), jitter=lambda _: 0
   159	    ) as client:
   160	        result = await client.create_allocation(request_body)
   161	    assert isinstance(result.data, Allocation)
   162	    assert route.call_count == 2
   163	    assert [json.loads(call.request.content) for call in route.calls] == [request_body] * 2
   164	
   165	
   166	async def _no_sleep() -> None:
   167	    return None
   168	
   169	
   170	@pytest.mark.asyncio
   171	@respx.mock
   172	async def test_breaker_opens_then_half_open_probe_closes_it() -> None:
   173	    now = [0.0]
   174	    route = respx.get("http://sim.test/v1/instance").mock(
   175	        side_effect=[
   176	            httpx.Response(503, json={"error": {"code": "FAULT_INJECTED"}}) for _ in range(5)
   177	        ]
   178	        + [httpx.Response(200, json=INSTANCE)]
   179	    )
   180	    async with SimClient("http://sim.test", max_retries=0, clock=lambda: now[0]) as client:
   181	        for _ in range(5):
   182	            with pytest.raises(SimUnavailable):
   183	                await client.get_instance()
   184	        assert client.breaker.state is BreakerState.OPEN
   185	        with pytest.raises(SimUnavailable, match="circuit breaker"):
   186	            await client.get_instance()
   187	        assert route.call_count == 5
   188	        now[0] = 10.1
   189	        result = await client.get_instance()
   190	    assert result.data.tick == 0
   191	    assert client.breaker.state is BreakerState.CLOSED
   192	
   193	
   194	@pytest.mark.asyncio
   195	@respx.mock
   196	async def test_demand_history_always_sends_bounded_limit_and_station() -> None:
   197	    rows = [
   198	        {
   199	            "id": 1,
   200	            "station_id": "station-mirpur",
   201	            "fuel_type": "DIESEL",
   202	            "tick": 0,
   203	            "sim_time": "2026-01-01T00:00:00",
   204	            "demand_liters": 100,
   205	            "served_liters": 90,
   206	            "unmet_liters": 10,
   207	        }
   208	    ]
   209	    route = respx.get("http://sim.test/v1/demand-history").mock(
   210	        return_value=httpx.Response(200, json=rows)
   211	    )
   212	    async with SimClient("http://sim.test") as client:
   213	        await client.get_demand_history("station-mirpur", limit=100)
   214	    assert route.calls[0].request.url.params["limit"] == "100"
   215	    assert route.calls[0].request.url.params["station_id"] == "station-mirpur"
   216	
   217	
   218	@pytest.mark.asyncio
   219	@respx.mock
   220	async def test_stream_fault_is_typed_for_reconnect_owner() -> None:
   221	    respx.get("http://sim.test/v1/stream").mock(
   222	        return_value=httpx.Response(503, json={"detail": {"code": "FAULT_INJECTED"}})
   223	    )
   224	    async with SimClient("http://sim.test") as client:
   225	        with pytest.raises(SimUnavailable):
   226	            async with client.stream():
   227	                pass
   228	
   229	
   230	@pytest.mark.asyncio
   231	async def test_stream_read_timeout_exceeds_documented_keepalive_interval() -> None:
   232	    timeouts = []
   233	
   234	    async def handler(request: httpx.Request) -> httpx.Response:
   235	        timeouts.append(request.extensions["timeout"])
   236	        return httpx.Response(200, text=": connected\n")
   237	
   238	    async with httpx.AsyncClient(
   239	        base_url="http://sim.test",
   240	        transport=httpx.MockTransport(handler),
   241	        timeout=httpx.Timeout(3.0),
   242	    ) as http_client:
   243	        async with SimClient(
   244	            "http://sim.test",
   245	            http_client=http_client,
   246	            read_timeout_s=3.0,
   247	            stream_read_timeout_s=20.0,
   248	        ) as client:
   249	            async with client.stream() as lines:
   250	                assert [line async for line in lines] == [": connected"]
   251	
   252	    assert timeouts[0]["read"] >= 20.0
   253	
   254	
   255	@pytest.mark.asyncio
   256	@respx.mock
   257	async def test_stream_reconnects_do_not_restart_open_breaker_cooldown() -> None:
   258	    now = [0.0]
   259	    respx.get("http://sim.test/v1/instance").mock(
   260	        side_effect=[
     1	from __future__ import annotations
     2	
     3	import logging
     4	from contextlib import asynccontextmanager
     5	from typing import Any
     6	
     7	import pytest
     8	from worker.sse import SSEConsumer, logger
     9	
    10	from core.sim_client import SimUnavailable
    11	
    12	
    13	def test_sse_connection_logs_are_enabled_at_info_level() -> None:
    14	    assert logger.isEnabledFor(logging.INFO)
    15	    assert logger.handlers
    16	
    17	
    18	class FakeClient:
    19	    def __init__(self, streams: list[Any]) -> None:
    20	        self.streams = streams
    21	        self.connections = 0
    22	
    23	    @asynccontextmanager
    24	    async def stream(self):
    25	        stream = self.streams[self.connections]
    26	        self.connections += 1
    27	        if isinstance(stream, Exception):
    28	            raise stream
    29	        yield stream
    30	
    31	
    32	@pytest.mark.asyncio
    33	async def test_stream_event_refresh_is_rate_limited_and_keepalive_is_ignored() -> None:
    34	    clock = [0.0]
    35	    refreshes = 0
    36	
    37	    async def lines():
    38	        yield ": keepalive"
    39	        yield "event: simulation.tick"
    40	        yield 'data: {"tick":1}'
    41	        clock[0] = 1.0
    42	        yield 'data: {"tick":2}'
    43	
    44	    async def refresh() -> None:
    45	        nonlocal refreshes
    46	        refreshes += 1
    47	
    48	    consumer = SSEConsumer(FakeClient([lines()]), refresh, clock=lambda: clock[0])
    49	
    50	    await consumer.run(max_connections=1)
    51	
    52	    assert refreshes == 2  # One after connection, one after the rate-limit window.
    53	
    54	
    55	@pytest.mark.asyncio
    56	async def test_reconnect_uses_backoff_and_refetches_after_successful_reconnect(caplog) -> None:
    57	    caplog.set_level(logging.INFO, logger="fuel_simulator.worker.sse")
    58	    refreshes = 0
    59	    delays: list[float] = []
    60	
    61	    async def refresh() -> None:
    62	        nonlocal refreshes
    63	        refreshes += 1
    64	
    65	    async def sleep(delay: float) -> None:
    66	        delays.append(delay)
    67	
    68	    async def one_event():
    69	        yield ": keepalive"
    70	
    71	    client = FakeClient([SimUnavailable("stream fault"), one_event()])
    72	    consumer = SSEConsumer(client, refresh, sleep=sleep, clock=lambda: 0.0)
    73	
    74	    await consumer.run(max_connections=2)
    75	
    76	    assert client.connections == 2
    77	    assert delays == [0.5]
    78	    assert refreshes == 1
    79	    assert '"event": "simulator_stream_connected"' in caplog.text
     1	# Resilience and fault verification
     2	
     3	All exercises below use the simulated BUP Fuel Supply Simulator. The live fault demo does not reset state or submit allocation writes. It requires a paused simulator, no pre-existing active faults, Docker Compose, and a Python environment with project test dependencies.
     4	
     5	Run it with:
     6	
     7	```sh
     8	PYTHON_BIN=.venv/bin/python bash scripts/fault_demo.sh
     9	```
    10	
    11	`PYTHON_BIN` may point at another environment that has the repository test dependencies installed. The script rejects a running simulator or pre-existing active fault, clears the fault it injects, restarts only worker/predictor containers that it stopped, and checks at exit that faults are clear, events are resolved, and the simulator is PAUSED. It does not reset the simulator.
    12	
    13	## Live result — 2026-11-20
    14	
    15	Evidence: [complete controlled fault demo](evidence/sprint-05-fault-demo-accepted.txt). The run began at tick 150 and ended PAUSED at tick 152. No allocation was created. The same stack remained healthy after recovery.
    16	
    17	| Fault | Detection and degraded behavior | Recovery evidence | Result |
    18	|---|---|---|---|
    19	| `unavailable` | Simulator returned HTTP 503; retries and breaker-open metric increased; cached snapshot became DEGRADED | Fault cleared; accepted non-stale snapshot returned HEALTHY | PASS |
    20	| `error_rate` | Injected HTTP 503; retry/failure counters and open breaker observed; cached snapshot became DEGRADED | Fault cleared; snapshot returned HEALTHY | PASS |
    21	| `latency` | 3500 ms simulator delay; client probe took about 3.51 s; cached snapshot aged beyond 15 s and became DEGRADED | Fault cleared; fresh snapshot returned HEALTHY | PASS |
    22	| `stale_data` | HTTP 200 included `X-Simulator-Stale: true`; API data health showed `stale=true`, `DEGRADED` | Fault cleared; fresh non-stale snapshot returned HEALTHY | PASS |
    23	| `stream_disconnect` | Stream endpoint returned HTTP 503 with nested fault code; REST ingestion stayed HEALTHY; reconnect metric increased | After clear, worker logged `simulator_stream_connected` without a subsequent worker restart | PASS |
    24	| Malformed simulator response | Controlled test fixture returned malformed content; last-known-good behavior and rejection path tested | `1 passed, 4 deselected` | PASS (test fixture; no live simulator mutation) |
    25	| Predictor stopped | `/api/health` reported OFFLINE; fallback counter increased; tick 151 persisted 12 `baseline` forecasts, all review-required, confidence at most 0.4; fallback incident visible | Predictor restarted; `/api/health` HEALTHY; tick 152 persisted 12 `remote` forecasts | PASS |
    26	| Worker stopped | API and frontend stayed reachable; health DEGRADED and snapshot age grew past 19 s | Worker restarted; ingestion returned HEALTHY | PASS |
    27	
    28	Prometheus had three active targets and all were `up`. Grafana `/api/health` returned database `ok`, version 11.6.0. A controlled one-tick `demand_spike` changed the provisioned `hours_to_stockout{station="station-coxsbazar",fuel="DIESEL"}` query from 19.5 to 19.25, and the event resolved at tick 145. Evidence: [Grafana event and panel query](evidence/sprint-05-grafana-event.txt).
    29	
    30	## Recovery and limits
    31	
    32	- REST polling is authoritative. SSE disconnects trigger reconnect and refetch; stream availability is not required for REST health.
    33	- Predictor fallback is persisted with low confidence and `needs_review`; recovery replaces same-key forecast rows with their remote `source` value. A regression test covers this upsert behavior.
    34	- The local `.env` contains values that differ from the public Compose defaults. It was left untouched. The safe configuration check passes with `.env.example` and reports the local mismatch by variable name only, without printing values. Run `python3 scripts/check_compose_env.py --env-file .env.example` to check clean-clone defaults.
    35	- Grafana dashboards and alert rules are provisioned and evaluate locally. Email delivery is not configured (Grafana logs report SMTP is unconfigured), so notification delivery is not verified.
    36	- Fault durations are bounded and the script does not clear unrelated/pre-existing faults; it refuses to start if any are active.
   120	                )
   121	                if snapshot_id is None:
   122	                    raise RuntimeError("cannot persist forecasts without a stored snapshot")
   123	                for record in records:
   124	                    forecast = record.forecast
   125	                    previous_risk = await connection.fetchval(
   126	                        """
   127	                        SELECT risk_level FROM forecasts
   128	                        WHERE station_id = $1 AND fuel_type = $2 AND snapshot_id < $3
   129	                        ORDER BY snapshot_id DESC LIMIT 1
   130	                        """,
   131	                        forecast.station_id,
   132	                        forecast.fuel_type.value,
   133	                        snapshot_id,
   134	                    )
   135	                    await connection.execute(
   136	                        """
   137	                        INSERT INTO forecasts (
   138	                            snapshot_id, tick, station_id, fuel_type, hours_to_stockout,
   139	                            p10, p50, p90, stockout_prob_24h, confidence, risk_level,
   140	                            needs_review, source, trajectory, drivers
   141	                        ) VALUES (
   142	                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
   143	                            $13, $14::jsonb, $15::jsonb
   144	                        )
   145	                        ON CONFLICT (snapshot_id, station_id, fuel_type) DO UPDATE SET
   146	                            hours_to_stockout = EXCLUDED.hours_to_stockout,
   147	                            p10 = EXCLUDED.p10, p50 = EXCLUDED.p50, p90 = EXCLUDED.p90,
   148	                            stockout_prob_24h = EXCLUDED.stockout_prob_24h,
   149	                            confidence = EXCLUDED.confidence,
   150	                            risk_level = EXCLUDED.risk_level,
   151	                            needs_review = EXCLUDED.needs_review,
   152	                            source = EXCLUDED.source,
   153	                            trajectory = EXCLUDED.trajectory,
   154	                            drivers = EXCLUDED.drivers
   155	                        """,
   156	                        snapshot_id,
   157	                        snapshot.instance.tick,
   158	                        forecast.station_id,
   159	                        forecast.fuel_type.value,
   160	                        forecast.hours_to_stockout,
   161	                        forecast.p10_hours,
   162	                        forecast.p50_hours,
   163	                        forecast.p90_hours,
   164	                        forecast.stockout_probability_24h,
   165	                        forecast.confidence,
   166	                        forecast.risk_level.value,
   167	                        forecast.needs_review,
   168	                        record.source,
   169	                        json.dumps(
   170	                            [point.__dict__ for point in record.trajectory],
   171	                            separators=(",", ":"),
   172	                        ),
   173	                        json.dumps(record.drivers, separators=(",", ":")),
   174	                    )
   175	                    await self._update_risk_incident(
   176	                        connection,
   177	                        forecast.station_id,
   178	                        forecast.fuel_type.value,
   179	                        previous_risk,
   180	                        forecast.risk_level.value,
   181	                    )
   182	                await self._refresh_active_alert_metrics(connection)
   183	
   184	    async def expire_stale_recommendations(self, tick: int) -> None:
   185	        await self.pool.execute(
   186	            """
   187	            UPDATE recommendations
   188	            SET status = 'EXPIRED', failure_reason = 'recommendation expired before review'
   189	            WHERE status = 'PROPOSED' AND expires_tick < $1
   190	            """,
   191	            tick,
   192	        )
   193	
   194	    async def get_open_proposal_pairs(self) -> set[tuple[str, str]]:
   195	        rows = await self.pool.fetch(
   196	            """
   197	            SELECT DISTINCT station_id, fuel_type FROM recommendations
   198	            WHERE status IN ('PROPOSED', 'APPROVED', 'SUBMITTED', 'IN_TRANSIT')
   199	            """
   200	        )
   201	        return {(row["station_id"], row["fuel_type"]) for row in rows}
   202	
   203	    async def persist_recommendations(self, rows: list[dict[str, Any]]) -> None:
   204	        async with self.pool.acquire() as connection:
   205	            async with connection.transaction():
   206	                for row in rows:
   207	                    await connection.execute(
   208	                        """
   209	                        INSERT INTO recommendations (
   210	                            id, status, policy_used, fallback_used, depot_id, station_id,
   211	                            route_id, fuel_type, quantity, idempotency_key, request_body,
   212	                            explanation_json, created_tick, expires_tick, correlation_id,
   213	                            sim_allocation_id, failure_reason
   214	                        ) VALUES (
   215	                            $1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, $10,
   216	                            $11::jsonb, $12::jsonb, $13, $14, $15, $16, $17
   217	                        )
   218	                        ON CONFLICT (idempotency_key) DO NOTHING
   219	                        """,
   220	                        row["id"],
   221	                        row["status"],
   222	                        row["policy_used"],
   223	                        row["fallback_used"],
   224	                        row["depot_id"],
   225	                        row["station_id"],
   226	                        row["route_id"],
   227	                        row["fuel_type"],
   228	                        row["quantity"],
   229	                        row["idempotency_key"],
   230	                        json.dumps(row["request_body"], separators=(",", ":")),
   231	                        json.dumps(row["explanation_json"], separators=(",", ":")),
   232	                        row["created_tick"],
   233	                        row["expires_tick"],
   234	                        row["correlation_id"],
   235	                        row["sim_allocation_id"],
   236	                        row["failure_reason"],
   237	                    )
   238	
   239	    async def get_recommendations_for_execution(self) -> list[dict[str, Any]]:
   240	        rows = await self.pool.fetch(
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-nvxGnaxY' (errno=Operation not permitted)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-WtoOrSyO' (errno=Operation not permitted)
diff --git a/backend/worker/sse.py b/backend/worker/sse.py
index fea1e85..f180b3a 100644
--- a/backend/worker/sse.py
+++ b/backend/worker/sse.py
@@ -7,11 +7,17 @@ import json
 import logging
 import time
 from collections.abc import Awaitable, Callable
+from datetime import datetime, timezone
 
 from core.metrics import sse_events, sse_reconnects
 from core.sim_client import SimClient
 
 logger = logging.getLogger("fuel_simulator.worker.sse")
+logger.setLevel(logging.INFO)
+if not logger.handlers:
+    handler = logging.StreamHandler()
+    handler.setFormatter(logging.Formatter("%(message)s"))
+    logger.addHandler(handler)
 
 
 class SSEConsumer:
@@ -44,6 +50,18 @@ class SSEConsumer:
             sse_reconnects.inc()
             try:
                 async with self.client.stream() as lines:
+                    logger.info(
+                        json.dumps(
+                            {
+                                "timestamp": datetime.now(timezone.utc).isoformat(),
+                                "level": "info",
+                                "service": "worker",
+                                "event": "simulator_stream_connected",
+                                "tick": None,
+                                "correlation_id": None,
+                            }
+                        )
+                    )
                     await self._refresh_if_due()
                     backoff_s = 0.5
                     async for line in lines:
@@ -58,8 +76,13 @@ class SSEConsumer:
                 logger.warning(
                     json.dumps(
                         {
+                            "timestamp": datetime.now(timezone.utc).isoformat(),
+                            "level": "warning",
+                            "service": "worker",
                             "event": "simulator_stream_disconnected",
                             "error_type": type(exc).__name__,
+                            "tick": None,
+                            "correlation_id": None,
                         }
                     )
                 )
diff --git a/backend/worker/store.py b/backend/worker/store.py
index 40bf03f..bb03d4d 100644
--- a/backend/worker/store.py
+++ b/backend/worker/store.py
@@ -149,6 +149,7 @@ class PostgresStore:
                             confidence = EXCLUDED.confidence,
                             risk_level = EXCLUDED.risk_level,
                             needs_review = EXCLUDED.needs_review,
+                            source = EXCLUDED.source,
                             trajectory = EXCLUDED.trajectory,
                             drivers = EXCLUDED.drivers
                         """,
diff --git a/docs/resilience.md b/docs/resilience.md
index 8570124..1de785b 100644
--- a/docs/resilience.md
+++ b/docs/resilience.md
@@ -1,20 +1,36 @@
-# Resilience matrix
-
-| Failure | Expected behavior | Observed (evidence path) |
-|---|---|---|
-| unavailable / error_rate (503) | retries with jitter, breaker, cached state, DEGRADED banner | Prior live evidence: `docs/evidence/sprint-02-runtime.md`; current rerun pending |
-| latency | bounded client timeout and retry; UI remains on persisted state | Client tests; current live rerun pending |
-| stale_data | stale marker, lower confidence, execution blocked | Prior live evidence: `docs/evidence/sprint-02-runtime.md`; current rerun pending |
-| stream_disconnect | REST polling continues; reconnect triggers a refetch | Prior live evidence and `tests/integration/test_sse.py`; current live rerun pending |
-| malformed data | reject, keep last good, log and count rejection | `tests/integration/test_ingest.py`, `tests/integration/test_resilience.py`; live malformed injection is unavailable |
-| predictor down | profile-only fallback, confidence <= 0.4, review required, incident and fallback metric | `tests/integration/test_predictor.py`; current container stop/recovery pending |
-| worker down | API serves last persisted state; new ingest/forecast/execution stops | Compose health behavior is configured; no dedicated live worker-stop evidence recorded |
-| low confidence | Forecast is marked for human review | Unit behavior is covered in forecast/risk tests |
-| executor timeout on POST | Retry with the same stored body/key | Executor unit tests cover ambiguous transport handling; live accepted-write/replay remains unverified |
-| executor sees the same key with a different body | fail closed locally; do not submit or record mismatched allocation as success | `tests/test_executor.py` and `tests/test_validator.py` |
-| simulator rejects allocation (409/422) | mark FAILED, record rejection code metric, never retry business validation errors | `tests/test_executor.py`; live accepted-write scenario pending operator approval |
-| stale or degraded executor read | expire recommendation without simulator write | `tests/test_executor.py` |
-| demand_spike active/resolved | forecast includes/removes station multiplier; consumed inventory remains depleted and risk is recalculated | Sprint 3 runtime evidence and `tests/test_forecast.py` |
-| shipment_delay with no dependent station allocation | delayed depot ETA changes; station risk is unchanged; no scheduled/in-transit supply is counted as on-hand | Sprint 3 runtime evidence and `tests/test_forecast.py` |
-
-Parameters: simulator timeouts connect 2s, read 3s; up to 3 retries after the initial attempt at 0.2/0.4/0.8s plus jitter; simulator breaker opens after 5 consecutive failed requests and half-opens after 10s. Predictor timeout defaults to 1.5s with an independent breaker. `scripts/fault_demo.sh` runs the five documented simulator fault scenes and clears each through a trap. Runtime evidence is recorded per sprint; unit, integration, and live evidence are distinguished above. In the current resumed environment, Docker is unavailable and the live reruns are NOT-RUN.
+# Resilience and fault verification
+
+All exercises below use the simulated BUP Fuel Supply Simulator. The live fault demo does not reset state or submit allocation writes. It requires a paused simulator, no pre-existing active faults, Docker Compose, and a Python environment with project test dependencies.
+
+Run it with:
+
+```sh
+PYTHON_BIN=.venv/bin/python bash scripts/fault_demo.sh
+```
+
+`PYTHON_BIN` may point at another environment that has the repository test dependencies installed. The script rejects a running simulator or pre-existing active fault, clears the fault it injects, restarts only worker/predictor containers that it stopped, and checks at exit that faults are clear, events are resolved, and the simulator is PAUSED. It does not reset the simulator.
+
+## Live result — 2026-11-20
+
+Evidence: [complete controlled fault demo](evidence/sprint-05-fault-demo-accepted.txt). The run began at tick 150 and ended PAUSED at tick 152. No allocation was created. The same stack remained healthy after recovery.
+
+| Fault | Detection and degraded behavior | Recovery evidence | Result |
+|---|---|---|---|
+| `unavailable` | Simulator returned HTTP 503; retries and breaker-open metric increased; cached snapshot became DEGRADED | Fault cleared; accepted non-stale snapshot returned HEALTHY | PASS |
+| `error_rate` | Injected HTTP 503; retry/failure counters and open breaker observed; cached snapshot became DEGRADED | Fault cleared; snapshot returned HEALTHY | PASS |
+| `latency` | 3500 ms simulator delay; client probe took about 3.51 s; cached snapshot aged beyond 15 s and became DEGRADED | Fault cleared; fresh snapshot returned HEALTHY | PASS |
+| `stale_data` | HTTP 200 included `X-Simulator-Stale: true`; API data health showed `stale=true`, `DEGRADED` | Fault cleared; fresh non-stale snapshot returned HEALTHY | PASS |
+| `stream_disconnect` | Stream endpoint returned HTTP 503 with nested fault code; REST ingestion stayed HEALTHY; reconnect metric increased | After clear, worker logged `simulator_stream_connected` without a subsequent worker restart | PASS |
+| Malformed simulator response | Controlled test fixture returned malformed content; last-known-good behavior and rejection path tested | `1 passed, 4 deselected` | PASS (test fixture; no live simulator mutation) |
+| Predictor stopped | `/api/health` reported OFFLINE; fallback counter increased; tick 151 persisted 12 `baseline` forecasts, all review-required, confidence at most 0.4; fallback incident visible | Predictor restarted; `/api/health` HEALTHY; tick 152 persisted 12 `remote` forecasts | PASS |
+| Worker stopped | API and frontend stayed reachable; health DEGRADED and snapshot age grew past 19 s | Worker restarted; ingestion returned HEALTHY | PASS |
+
+Prometheus had three active targets and all were `up`. Grafana `/api/health` returned database `ok`, version 11.6.0. A controlled one-tick `demand_spike` changed the provisioned `hours_to_stockout{station="station-coxsbazar",fuel="DIESEL"}` query from 19.5 to 19.25, and the event resolved at tick 145. Evidence: [Grafana event and panel query](evidence/sprint-05-grafana-event.txt).
+
+## Recovery and limits
+
+- REST polling is authoritative. SSE disconnects trigger reconnect and refetch; stream availability is not required for REST health.
+- Predictor fallback is persisted with low confidence and `needs_review`; recovery replaces same-key forecast rows with their remote `source` value. A regression test covers this upsert behavior.
+- The local `.env` contains values that differ from the public Compose defaults. It was left untouched. The safe configuration check passes with `.env.example` and reports the local mismatch by variable name only, without printing values. Run `python3 scripts/check_compose_env.py --env-file .env.example` to check clean-clone defaults.
+- Grafana dashboards and alert rules are provisioned and evaluate locally. Email delivery is not configured (Grafana logs report SMTP is unconfigured), so notification delivery is not verified.
+- Fault durations are bounded and the script does not clear unrelated/pre-existing faults; it refuses to start if any are active.
diff --git a/docs/sprint-reports/sprint-05.md b/docs/sprint-reports/sprint-05.md
index b116566..58bb52b 100644
--- a/docs/sprint-reports/sprint-05.md
+++ b/docs/sprint-reports/sprint-05.md
@@ -1,80 +1,72 @@
 # Sprint 05 Report: Observability and resilience
 
-Time window: 2026-11-20 | Owner: Codex | Branch: `main`, base `b1fc38b` | Status: **Blocked on live runtime acceptance**
+Date: 2026-11-20 | Branch: `overnight-sprints-4-7` | Gate: **PASS** (notification delivery limitation documented)
 
-## 1. Objective
+## Objective and implementation
 
-Make service state and failure responses visible, add predictor fallback, and demonstrate fault detection and recovery.
+Sprint 5 provides component health, service metrics, a separately addressable predictor, a review-required baseline fallback, provisioned Prometheus/Grafana monitoring, and controlled fault/recovery demonstrations.
 
-## 2. What now exists
+- API, worker, and predictor expose health and Prometheus metrics. `/api/health` reports `HEALTHY`, `DEGRADED`, or `OFFLINE` for the aggregate and its components. A stale decision-engine heartbeat while the simulator is paused degrades the pipeline without falsely marking the worker or simulator offline.
+- Worker requests the independent predictor through a bounded client/breaker. Predictor failure persists baseline forecasts with confidence capped at 0.4 and `needs_review=true`; fallback incidents and counters are visible. Recovery persists `source=remote` correctly.
+- SSE is advisory. A stream disconnect leaves REST polling available; reconnect is logged and refetches current state.
+- Prometheus scrapes the API, worker, and predictor. Grafana data source, dashboard, and alert rules are provisioned as code.
+- Smoke preflight checks Compose database credential alignment and the internal predictor URL without printing values. It accepts `--env-file` for public defaults.
+- Fault demo refuses a non-paused simulator or pre-existing active fault. It clears only faults it injects, restores services it stops, and verifies a paused, fault-free final state.
 
-- Predictor `POST /predict` validates a snapshot slice and returns shared-core forecast output. Worker uses a bounded remote client and a single-probe circuit breaker; fallback uses profile demand only, caps confidence at 0.4, and sets `needs_review`.
-- Predictor fallback creates/resolves an incident, emits a low-cardinality counter and structured log record, and continues to persist forecast results.
-- `/api/health` aggregates database, worker/simulator heartbeat and age, predictor ping, decision engine age, request p95, and observed API 5xx ratio. Frontend health view/banner and Grafana dashboard/alerts are provisioned.
-- Added integration coverage for unavailable/error-rate/latency-shaped ingestion failure, stale responses, malformed data, and a regression proving only one predictor half-open probe proceeds.
-- Added `scripts/fault_demo.sh`; runtime scenes were not executed.
+## Root causes and fixes
 
-## 3. Decisions
+1. SSE reconnection succeeded but was not verifiable in worker logs. Added structured connected/disconnected records at INFO and a test that confirms the logger is enabled. Live evidence shows a successful stream connection after fault clear without another worker restart.
+2. Predictor recovered and served HTTP 200, but forecast upsert did not replace the persisted source column. Added `source = EXCLUDED.source` and a regression test. The live script now asserts baseline/review-required forecasts during outage and remote forecasts after recovery.
+3. Local Compose settings differ from public defaults, but diagnostics risked requiring inspection of credentials. Added a redacted configuration validator and explicit `--env-file` support. The local `.env` was not edited.
+4. Fault demo assumed `pytest` was on PATH. It now uses configurable `PYTHON_BIN`; the final live run used the repository test interpreter.
 
-- Kept forecast/risk computation in shared pure core code and used a separate predictor HTTP boundary. Remote failure does not affect the recommendation feasibility validator.
-- Used a profile-only fallback with review required; no confidence higher than 0.4 is claimed for fallback forecasts.
-- The live fault script clears simulator faults on exit. It does not approve or submit recommendations.
+## Changed areas
 
-## 4. Key files
+`backend/worker/sse.py`, `backend/worker/store.py`, `scripts/fault_demo.sh`, `scripts/check_compose_env.py`, `scripts/smoke.sh`, related SSE/store/config tests, README setup guidance, `docs/resilience.md`, `docs/observability.md`, and this report.
 
-`backend/worker/forecaster.py`, `forecast_job.py`, `store.py`, `backend/api/routes/health.py`, `backend/api/routes/chaos.py`, `intel/predictor/app/main.py`, `web/src/features/system-health/`, `observability/grafana/provisioning/`, `scripts/fault_demo.sh`, and `tests/integration/test_resilience.py`.
+## Runtime evidence
 
-## 5. APIs
+See [complete live fault and recovery evidence](../evidence/sprint-05-fault-demo-accepted.txt), [Grafana event metric evidence](../evidence/sprint-05-grafana-event.txt), and [resilience matrix](../resilience.md).
 
-- `POST /predict`: validated forecast request to independent predictor.
-- `POST /api/chaos/forecast-fail`: token-protected predictor failure switch.
-- `GET /api/health`: database-backed component health and API latency/error summary.
+The simulator started PAUSED at tick 150 and ended PAUSED at tick 152. No allocation write or state reset occurred. All five simulator faults were detected and cleared; cached data degraded and recovered. Malformed response test passed (1 passed, 4 deselected). Predictor stop changed component/aggregate health to OFFLINE, generated 12 baseline forecasts at tick 151 (all requiring review, max confidence 0), and created a fallback incident. Predictor recovery restored HEALTHY and 12 remote forecasts at tick 152. Worker stop produced DEGRADED health and 19.2-second data age while API/frontend remained reachable; restart restored fresh ingestion. Prometheus showed three targets up; Grafana database health was `ok`, version 11.6.0, and a provisioned stockout-hours query moved 19.5 to 19.25 during a controlled demand-spike event.
 
-## 6. Verification
+## Verification
 
-| Check | Actual result | Status |
+| Check | Result | Status |
 |---|---|---|
-| Full Python suite | 123 passed; frontend Vitest 3 passed | PASS |
-| Frontend tests | 3 passed | PASS |
-| `make lint` | Ruff and format checks passed; TypeScript passed; Vite production build passed (500 modules) | PASS |
-| Compose config / `git diff --check` | Exit 0 | PASS |
-| Fault injection and recovery, five simulator faults | Docker socket unavailable; not run | NOT-RUN |
-| Predictor stop/fallback/recovery and worker stop | Docker socket unavailable; not run | NOT-RUN |
-| Grafana panels move during event/fault | Docker socket unavailable; not run | NOT-RUN |
-
-## 7. Evidence
-
-Local test/build output is recorded in `docs/evidence/sprint-05-runtime.md`. No new live runtime capture was produced. Historical Sprint 2 fault evidence is in `docs/evidence/sprint-02-runtime.md` and does not verify this Sprint 5 runtime.
-
-## 8. Problems and fixes
-
-The first new half-open breaker test failed because concurrent calls could all pass after reset. Added an async-lock-protected single-probe guard; full verification was rerun. Docker daemon unavailability prevented live acceptance checks.
-
-## 9. Not done / risks
-
-The fault demo, predictor-stop and recovery, worker-stop behavior, dashboard movement, and five-fault recovery are not demonstrated in this environment. The frontend image was not rebuilt. No live runtime pass is claimed.
-
-## 10. Next dependency
-
-Restore Docker and run the live resilience matrix on a dedicated demo stack. Confirm `PREDICTOR_URL` configuration without exposing `.env` values.
-
-## 11. Acceptance checklist
-
-- [x] Predictor endpoint, fallback, health UI, and dashboards implemented.
-- [x] Local resilience tests, lint, frontend tests/build, Compose config, and whitespace check passed.
-- [ ] Five simulator faults detected and recovered live — NOT-RUN.
-- [ ] Predictor stop/fallback/recovery and worker stop/data-age demonstrated — NOT-RUN.
-- [ ] Grafana panels move under injected conditions — NOT-RUN.
-- [ ] Sprint 5 gate passed — No; live runtime acceptance remains open.
-
-## 12. Five-minute update
-
-1. Problem: failures were not sufficiently visible and predictor failure needed a review-required path.
-2. Change: remote predictor, bounded breaker/fallback, health aggregation, UI banner, Grafana provisioning, tests and fault demo.
-3. Demo: not available while Docker daemon is offline; planned steps are in `docs/final-demo-script.md`.
-4. Evidence: 123 Python and 3 frontend tests; lint/typecheck/build and Compose config pass.
-5. Gap: current live fault, recovery, Grafana, and stop/restart evidence is absent.
-
-## Gate decision
-
-**Blocked.** Local checks pass. Live acceptance is NOT-RUN because Docker is unavailable.
+| `bash -n scripts/fault_demo.sh` | Exit 0 | PASS |
+| `PYTHON_BIN=/tmp/fuel-sprint1-venv/bin/python FAULT_SECONDS=60 WAIT_SECONDS=18 bash scripts/fault_demo.sh` | All simulator faults, malformed-data check, predictor fallback/recovery, worker stop/recovery passed; final PAUSED tick 152, faults clear and events resolved | PASS |
+| `python3 -m pytest -q tests/unit/test_compose_env_check.py` | 3 passed | PASS |
+| `python3 scripts/check_compose_env.py --env-file .env.example` | `PASS: database credentials and predictor URL match Compose services` | PASS |
+| Forecast source upsert regression | Focused store test passed; runtime tick 152 source remote for all 12 forecasts | PASS |
+| `make test`, `make lint`, frontend test/build | To be rerun after all current changes; results recorded in this gate section before commit | PENDING |
+| Docker Compose state | All eight services running and healthy after fault demo | PASS |
+| Prometheus/Grafana | Three targets up; Grafana health database ok; panel query moved with controlled event | PASS |
+| Grafana outbound notifications | SMTP not configured; delivery not attempted | DOCUMENTED LIMITATION |
+| `git diff --check`, Sprint 5 mechanical gate | To be run after final documentation updates | PENDING |
+
+An earlier attempt used the host Python without project dependencies and failed during test collection; a subsequent run using the project interpreter passed. Earlier run logs are preserved but are not counted as acceptance evidence.
+
+## Known limitations
+
+- Grafana alert rules are provisioned and evaluate, but outbound SMTP notification delivery is not configured or verified.
+- Local `.env` values do not match the public Compose defaults. They were not edited. The clean public `.env.example` configuration passes the redacted checker; local `make smoke` will fail preflight until the owner aligns local configuration.
+- Hosted GitHub Actions were not triggered in this environment.
+
+## Acceptance checklist
+
+- [x] API, worker, predictor metrics and aggregated health verified.
+- [x] Predictor service and review-required fallback verified live, including recovery to remote forecast persistence.
+- [x] Five simulator faults verified with detection and automatic recovery.
+- [x] Malformed-data rejection path verified.
+- [x] Worker outage and recovery verified without an API/frontend outage.
+- [x] Grafana provisioning and metric movement verified; SMTP limitation documented.
+- [ ] Full repository lint/test/build and mechanical gate results to be appended after final rerun.
+
+## Five-minute update
+
+1. Problem: operators needed visible failure states and forecasts that safely recover when the predictor is unavailable.
+2. Change: health aggregation, predictor fallback, structured SSE recovery logs, source-correct upserts, redacted Compose validation, dashboards, and fault demo.
+3. Demo: start the stack, open the dashboard and Grafana, then run `PYTHON_BIN=.venv/bin/python bash scripts/fault_demo.sh` with the simulator paused and no active faults.
+4. Evidence: [live fault transcript](../evidence/sprint-05-fault-demo-accepted.txt), [Grafana query](../evidence/sprint-05-grafana-event.txt), and [resilience matrix](../resilience.md).
+5. Gap: SMTP notifications and hosted CI remain unverified; local `.env` differs from public defaults and remains untouched.
diff --git a/tests/integration/test_sse.py b/tests/integration/test_sse.py
index b4660ee..a36eb36 100644
--- a/tests/integration/test_sse.py
+++ b/tests/integration/test_sse.py
@@ -1,14 +1,20 @@
 from __future__ import annotations
 
+import logging
 from contextlib import asynccontextmanager
 from typing import Any
 
 import pytest
-from worker.sse import SSEConsumer
+from worker.sse import SSEConsumer, logger
 
 from core.sim_client import SimUnavailable
 
 
+def test_sse_connection_logs_are_enabled_at_info_level() -> None:
+    assert logger.isEnabledFor(logging.INFO)
+    assert logger.handlers
+
+
 class FakeClient:
     def __init__(self, streams: list[Any]) -> None:
         self.streams = streams
@@ -47,7 +53,8 @@ async def test_stream_event_refresh_is_rate_limited_and_keepalive_is_ignored() -
 
 
 @pytest.mark.asyncio
-async def test_reconnect_uses_backoff_and_refetches_after_successful_reconnect() -> None:
+async def test_reconnect_uses_backoff_and_refetches_after_successful_reconnect(caplog) -> None:
+    caplog.set_level(logging.INFO, logger="fuel_simulator.worker.sse")
     refreshes = 0
     delays: list[float] = []
 
@@ -69,3 +76,4 @@ async def test_reconnect_uses_backoff_and_refetches_after_successful_reconnect()
     assert client.connections == 2
     assert delays == [0.5]
     assert refreshes == 1
+    assert '"event": "simulator_stream_connected"' in caplog.text
diff --git a/tests/unit/test_store_snapshot.py b/tests/unit/test_store_snapshot.py
index 617d859..e8cd5ef 100644
--- a/tests/unit/test_store_snapshot.py
+++ b/tests/unit/test_store_snapshot.py
@@ -7,7 +7,8 @@ from typing import Any
 import pytest
 from worker.store import PostgresStore
 
-from core.models import DataStatus, Instance, Metrics, Snapshot
+from core.models import DataStatus, Forecast, FuelType, Instance, Metrics, RiskLevel, Snapshot
+from core.risk import ForecastRecord, TrajectoryPoint
 
 
 class FakeConnection:
@@ -18,9 +19,12 @@ class FakeConnection:
     async def transaction(self):
         yield
 
-    async def fetchval(self, query: str) -> int:
+    async def fetchval(self, query: str, *args: Any) -> int:
         return 134
 
+    async def fetch(self, query: str) -> list[Any]:
+        return []
+
     async def execute(self, query: str, *args: Any) -> str:
         self.executed.append((query, args))
         return "UPDATE 1"
@@ -80,3 +84,28 @@ async def test_same_tick_refresh_replaces_raw_payload_as_well_as_freshness_metad
     assert "raw_json = $" in query
     assert '"status":"PAUSED"' in args[1]
     assert args[0].year == 2026
+
+
+@pytest.mark.asyncio
+async def test_forecast_upsert_replaces_source_after_predictor_recovery() -> None:
+    connection = FakeConnection()
+    store = PostgresStore(FakePool(connection))  # type: ignore[arg-type]
+    forecast = Forecast(
+        station_id="station-mirpur",
+        fuel_type=FuelType.DIESEL,
+        hours_to_stockout=4,
+        p10_hours=3,
+        p50_hours=4,
+        p90_hours=5,
+        stockout_probability_24h=0.5,
+        confidence=0.9,
+        risk_level=RiskLevel.HIGH,
+        needs_review=False,
+    )
+    record = ForecastRecord(forecast, [TrajectoryPoint(0, 100, 90, 110)], {}, source="remote")
+
+    await store.persist_forecasts(snapshot("PAUSED"), [record])
+
+    query, args = next(row for row in connection.executed if "INSERT INTO forecasts" in row[0])
+    assert "source = EXCLUDED.source" in query
+    assert args[12] == "remote"

exec
/bin/zsh -lc "nl -ba intel/predictor/app/main.py | sed -n '1,160p'; nl -ba backend/worker/store.py | sed -n '400,520p'; nl -ba docs/resilience.md | sed -n '1,100p'; git diff --check" in /Users/abrar/project/fuel_simulator
 succeeded in 0ms:
     1	import hmac
     2	import os
     3	from dataclasses import asdict
     4	from typing import Any
     5	
     6	from fastapi import FastAPI, HTTPException, Request
     7	from fastapi.responses import Response
     8	from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
     9	from pydantic import BaseModel, Field
    10	
    11	from core.metrics import health_checks
    12	from core.models import FuelType, Snapshot
    13	from core.risk import forecast_pair
    14	
    15	app = FastAPI(title="Fuel Supply Platform Predictor", version="0.2.0")
    16	app.state.fail_forecasts = False
    17	
    18	
    19	class PredictRequest(BaseModel):
    20	    snapshot: Snapshot
    21	    station_id: str = Field(min_length=1, max_length=150)
    22	    fuel_type: FuelType
    23	    seed: int
    24	
    25	
    26	class FailForecastRequest(BaseModel):
    27	    enabled: bool
    28	
    29	
    30	@app.get("/health")
    31	def health() -> dict[str, str]:
    32	    health_checks.labels(service="predictor").inc()
    33	    return {"status": "ok", "service": "predictor"}
    34	
    35	
    36	@app.post("/predict")
    37	def predict(payload: PredictRequest, request: Request) -> dict[str, Any]:
    38	    if request.app.state.fail_forecasts:
    39	        raise HTTPException(status_code=503, detail="Injected predictor failure")
    40	    station = next(
    41	        (item for item in payload.snapshot.stations if item.id == payload.station_id), None
    42	    )
    43	    if station is None:
    44	        raise HTTPException(status_code=404, detail="Unknown station")
    45	    record = forecast_pair(
    46	        payload.snapshot,
    47	        station,
    48	        payload.fuel_type,
    49	        seed=payload.seed,
    50	    )
    51	    return {
    52	        "forecast": record.forecast.model_dump(mode="json"),
    53	        "trajectory": [asdict(point) for point in record.trajectory],
    54	        "drivers": record.drivers,
    55	        "source": "remote",
    56	    }
    57	
    58	
    59	@app.post("/admin/fail")
    60	def set_failure(payload: FailForecastRequest, request: Request) -> dict[str, bool]:
    61	    token = request.headers.get("X-Operator-Token", "")
    62	    expected = os.getenv("OPERATOR_TOKEN", "")
    63	    if not expected or not hmac.compare_digest(token, expected):
    64	        raise HTTPException(status_code=401, detail="Invalid operator token")
    65	    request.app.state.fail_forecasts = payload.enabled
    66	    return {"enabled": request.app.state.fail_forecasts}
    67	
    68	
    69	@app.get("/metrics", include_in_schema=False)
    70	def metrics() -> Response:
    71	    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
   400	                    SELECT id FROM snapshots ORDER BY fetched_at DESC, id DESC LIMIT $1
   401	                )
   402	                """,
   403	                keep,
   404	            )
   405	
   406	    async def close(self) -> None:
   407	        await self.pool.close()
     1	# Resilience and fault verification
     2	
     3	All exercises below use the simulated BUP Fuel Supply Simulator. The live fault demo does not reset state or submit allocation writes. It requires a paused simulator, no pre-existing active faults, Docker Compose, and a Python environment with project test dependencies.
     4	
     5	Run it with:
     6	
     7	```sh
     8	PYTHON_BIN=.venv/bin/python bash scripts/fault_demo.sh
     9	```
    10	
    11	`PYTHON_BIN` may point at another environment that has the repository test dependencies installed. The script rejects a running simulator or pre-existing active fault, clears the fault it injects, restarts only worker/predictor containers that it stopped, and checks at exit that faults are clear, events are resolved, and the simulator is PAUSED. It does not reset the simulator.
    12	
    13	## Live result — 2026-11-20
    14	
    15	Evidence: [complete controlled fault demo](evidence/sprint-05-fault-demo-accepted.txt). The run began at tick 150 and ended PAUSED at tick 152. No allocation was created. The same stack remained healthy after recovery.
    16	
    17	| Fault | Detection and degraded behavior | Recovery evidence | Result |
    18	|---|---|---|---|
    19	| `unavailable` | Simulator returned HTTP 503; retries and breaker-open metric increased; cached snapshot became DEGRADED | Fault cleared; accepted non-stale snapshot returned HEALTHY | PASS |
    20	| `error_rate` | Injected HTTP 503; retry/failure counters and open breaker observed; cached snapshot became DEGRADED | Fault cleared; snapshot returned HEALTHY | PASS |
    21	| `latency` | 3500 ms simulator delay; client probe took about 3.51 s; cached snapshot aged beyond 15 s and became DEGRADED | Fault cleared; fresh snapshot returned HEALTHY | PASS |
    22	| `stale_data` | HTTP 200 included `X-Simulator-Stale: true`; API data health showed `stale=true`, `DEGRADED` | Fault cleared; fresh non-stale snapshot returned HEALTHY | PASS |
    23	| `stream_disconnect` | Stream endpoint returned HTTP 503 with nested fault code; REST ingestion stayed HEALTHY; reconnect metric increased | After clear, worker logged `simulator_stream_connected` without a subsequent worker restart | PASS |
    24	| Malformed simulator response | Controlled test fixture returned malformed content; last-known-good behavior and rejection path tested | `1 passed, 4 deselected` | PASS (test fixture; no live simulator mutation) |
    25	| Predictor stopped | `/api/health` reported OFFLINE; fallback counter increased; tick 151 persisted 12 `baseline` forecasts, all review-required, confidence at most 0.4; fallback incident visible | Predictor restarted; `/api/health` HEALTHY; tick 152 persisted 12 `remote` forecasts | PASS |
    26	| Worker stopped | API and frontend stayed reachable; health DEGRADED and snapshot age grew past 19 s | Worker restarted; ingestion returned HEALTHY | PASS |
    27	
    28	Prometheus had three active targets and all were `up`. Grafana `/api/health` returned database `ok`, version 11.6.0. A controlled one-tick `demand_spike` changed the provisioned `hours_to_stockout{station="station-coxsbazar",fuel="DIESEL"}` query from 19.5 to 19.25, and the event resolved at tick 145. Evidence: [Grafana event and panel query](evidence/sprint-05-grafana-event.txt).
    29	
    30	## Recovery and limits
    31	
    32	- REST polling is authoritative. SSE disconnects trigger reconnect and refetch; stream availability is not required for REST health.
    33	- Predictor fallback is persisted with low confidence and `needs_review`; recovery replaces same-key forecast rows with their remote `source` value. A regression test covers this upsert behavior.
    34	- The local `.env` contains values that differ from the public Compose defaults. It was left untouched. The safe configuration check passes with `.env.example` and reports the local mismatch by variable name only, without printing values. Run `python3 scripts/check_compose_env.py --env-file .env.example` to check clean-clone defaults.
    35	- Grafana dashboards and alert rules are provisioned and evaluate locally. Email delivery is not configured (Grafana logs report SMTP is unconfigured), so notification delivery is not verified.
    36	- Fault durations are bounded and the script does not clear unrelated/pre-existing faults; it refuses to start if any are active.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-nSct6K0k' (errno=Operation not permitted)
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-gX3PjAcT' (errno=Operation not permitted)

codex
## Findings

### P1 — Snapshot age alert does not detect an ingestion outage

[metrics.py](/Users/abrar/project/fuel_simulator/backend/shared/core/metrics.py:21) defines `snapshot_age_seconds` as the age of the latest accepted snapshot, but [ingest.py](/Users/abrar/project/fuel_simulator/backend/worker/ingest.py:137) updates it only after a successful ingestion—and computes it from that just-fetched snapshot. When ingestion fails or the worker stops, the gauge stops changing. The Grafana rule alerts only when that gauge exceeds 30 seconds ([alerts.yml](/Users/abrar/project/fuel_simulator/observability/grafana/provisioning/alerting/alerts.yml:8)). The API and UI calculate age from persisted timestamps and do show degradation, but this alert can remain quiet while the operator-facing health turns degraded or offline.

**Proposed test:** Set the age gauge with a successful ingestion, then simulate repeated ingestion failure and worker loss while advancing time. Verify the alert expression fires after the threshold, or change it to use a signal that continues to age without worker updates. Add a separate alert for a missing worker scrape or stale heartbeat.

### P2 — Predictor health trusts HTTP 200 without checking the response status

[health.py](/Users/abrar/project/fuel_simulator/backend/api/routes/health.py:64) marks the predictor `HEALTHY` for any HTTP 200 response. The current predictor returns `{"status":"ok"}` ([main.py](/Users/abrar/project/fuel_simulator/intel/predictor/app/main.py:30)), and the outage demo correctly observed `OFFLINE` while it was stopped. But a process that still serves `/health` with a non-healthy body could appear healthy while forecasts fail and fall back.

**Proposed test:** Mock `/health` returning HTTP 200 with `{"status":"degraded"}` or `{"status":"offline"}` and verify the API does not report the predictor healthy.

## Fault trace and operator visibility

| Fault | Behavior and what the operator sees |
|---|---|
| `latency` | Simulator calls have bounded retries and timeouts; rejected polls retain the last snapshot. Persisted snapshot age moves data health to `DEGRADED` after 15 seconds, which the dashboard banner and health view display. The accepted evidence records recovery. |
| `unavailable` | Injected 503s are retried, counted, and can open the simulator breaker. Ingestion marks the cached snapshot degraded; the UI shows its age/status. The evidence records breaker and retry metrics and recovery. |
| `error_rate` | The injected 503 path follows the same bounded retry, failure metric, breaker, and degraded-cache path. The evidence records those signals and recovery. |
| `stale_data` | HTTP 200 with `X-Simulator-Stale: true` is accepted but persisted as stale/degraded. The API returns the stale flag and the UI displays it. The evidence confirms this path. |
| `stream_disconnect` | SSE reconnects with backoff and logs disconnect/reconnect; a successful reconnect triggers a REST refresh. REST remains authoritative, so the dashboard can remain healthy while only the stream is unavailable. Stream status is visible in logs/metrics, not as a dedicated UI incident. |
| Malformed data | Schema/JSON validation rejects the snapshot; ingestion keeps the last good snapshot, marks it degraded, increments rejection metrics, logs the rejection, and records an integration event. The cited evidence covers a test fixture, not a live simulator mutation. |
| Predictor down | The health endpoint reports predictor offline and overall health offline. Forecasting uses the baseline fallback with review required and confidence capped at 0.4; the fallback counter and incident are visible. Evidence records recovery to remote forecasts. |
| Worker down | The API and frontend remain available. Persisted snapshot and heartbeat age drive degraded/offline health and the UI shows age/status. Evidence records degraded health at about 19 seconds and recovery. There is no dedicated worker-down Grafana alert; the snapshot-age rule has the P1 defect above. |

`docs/resilience.md` also states that Grafana email delivery is not configured, so alert notification delivery is unverified ([resilience.md](/Users/abrar/project/fuel_simulator/docs/resilience.md:30)). The accepted evidence records the scenarios, observed signals, and recovery ([fault-demo evidence](/Users/abrar/project/fuel_simulator/docs/evidence/sprint-05-fault-demo-accepted.txt)).

I found **no P0 findings**. The snapshot-age alert defect is the sole P1. This was a read-only review; I did not run tests or edit files.
tokens used
77,282
## Findings

### P1 — Snapshot age alert does not detect an ingestion outage

[metrics.py](/Users/abrar/project/fuel_simulator/backend/shared/core/metrics.py:21) defines `snapshot_age_seconds` as the age of the latest accepted snapshot, but [ingest.py](/Users/abrar/project/fuel_simulator/backend/worker/ingest.py:137) updates it only after a successful ingestion—and computes it from that just-fetched snapshot. When ingestion fails or the worker stops, the gauge stops changing. The Grafana rule alerts only when that gauge exceeds 30 seconds ([alerts.yml](/Users/abrar/project/fuel_simulator/observability/grafana/provisioning/alerting/alerts.yml:8)). The API and UI calculate age from persisted timestamps and do show degradation, but this alert can remain quiet while the operator-facing health turns degraded or offline.

**Proposed test:** Set the age gauge with a successful ingestion, then simulate repeated ingestion failure and worker loss while advancing time. Verify the alert expression fires after the threshold, or change it to use a signal that continues to age without worker updates. Add a separate alert for a missing worker scrape or stale heartbeat.

### P2 — Predictor health trusts HTTP 200 without checking the response status

[health.py](/Users/abrar/project/fuel_simulator/backend/api/routes/health.py:64) marks the predictor `HEALTHY` for any HTTP 200 response. The current predictor returns `{"status":"ok"}` ([main.py](/Users/abrar/project/fuel_simulator/intel/predictor/app/main.py:30)), and the outage demo correctly observed `OFFLINE` while it was stopped. But a process that still serves `/health` with a non-healthy body could appear healthy while forecasts fail and fall back.

**Proposed test:** Mock `/health` returning HTTP 200 with `{"status":"degraded"}` or `{"status":"offline"}` and verify the API does not report the predictor healthy.

## Fault trace and operator visibility

| Fault | Behavior and what the operator sees |
|---|---|
| `latency` | Simulator calls have bounded retries and timeouts; rejected polls retain the last snapshot. Persisted snapshot age moves data health to `DEGRADED` after 15 seconds, which the dashboard banner and health view display. The accepted evidence records recovery. |
| `unavailable` | Injected 503s are retried, counted, and can open the simulator breaker. Ingestion marks the cached snapshot degraded; the UI shows its age/status. The evidence records breaker and retry metrics and recovery. |
| `error_rate` | The injected 503 path follows the same bounded retry, failure metric, breaker, and degraded-cache path. The evidence records those signals and recovery. |
| `stale_data` | HTTP 200 with `X-Simulator-Stale: true` is accepted but persisted as stale/degraded. The API returns the stale flag and the UI displays it. The evidence confirms this path. |
| `stream_disconnect` | SSE reconnects with backoff and logs disconnect/reconnect; a successful reconnect triggers a REST refresh. REST remains authoritative, so the dashboard can remain healthy while only the stream is unavailable. Stream status is visible in logs/metrics, not as a dedicated UI incident. |
| Malformed data | Schema/JSON validation rejects the snapshot; ingestion keeps the last good snapshot, marks it degraded, increments rejection metrics, logs the rejection, and records an integration event. The cited evidence covers a test fixture, not a live simulator mutation. |
| Predictor down | The health endpoint reports predictor offline and overall health offline. Forecasting uses the baseline fallback with review required and confidence capped at 0.4; the fallback counter and incident are visible. Evidence records recovery to remote forecasts. |
| Worker down | The API and frontend remain available. Persisted snapshot and heartbeat age drive degraded/offline health and the UI shows age/status. Evidence records degraded health at about 19 seconds and recovery. There is no dedicated worker-down Grafana alert; the snapshot-age rule has the P1 defect above. |

`docs/resilience.md` also states that Grafana email delivery is not configured, so alert notification delivery is unverified ([resilience.md](/Users/abrar/project/fuel_simulator/docs/resilience.md:30)). The accepted evidence records the scenarios, observed signals, and recovery ([fault-demo evidence](/Users/abrar/project/fuel_simulator/docs/evidence/sprint-05-fault-demo-accepted.txt)).

I found **no P0 findings**. The snapshot-age alert defect is the sole P1. This was a read-only review; I did not run tests or edit files.
