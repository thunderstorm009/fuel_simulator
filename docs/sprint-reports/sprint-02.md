# Sprint 02 Report: Resilient ingestion, read API, live dashboard

**Path note:** The key paths below reflect the repository layout at Sprint 2. They were later moved into `backend/`, `intel/predictor/`, `web/`, and `observability/`; see `docs/DAY-1-UPDATE.md` for the current tree.

Time window: 2026-11-19 resume session | Owner(s): Codex | Branch and tag: `main`, last tag `sprint-0` | Status: Passed locally with environment notes

## 1. Objective

Show live simulator state in the operator overview and keep it usable through simulator faults, while keeping simulator I/O in the worker and serving API reads from PostgreSQL.

## 2. What now exists (behavior, not just files)

- `SimClient` validates simulator responses, preserves the stale header, exposes typed transport/schema/business errors, retries transient failures with bounded jitter, and maintains a locked circuit breaker.
- The worker polls all required simulator resources, validates one aggregate snapshot, persists it atomically, tracks heartbeats and integration failures, prunes snapshot history, and uses SSE events only as refresh hints. Polling continues when SSE disconnects.
- A failed ingest retains the last snapshot contents and marks its status DEGRADED immediately. A successful same-tick poll updates freshness and stale/status metadata without creating a duplicate row, allowing paused simulators to recover.
- The API serves `/api/state`, `/api/data-health`, `/api/events`, and `/api/metrics-summary` from PostgreSQL only. Old snapshots are returned with computed age/status; an empty store returns 503.
- The React overview polls every three seconds and shows station/fuel inventory, depots, routes, events, service level, status and age. Real Chrome checks confirmed the degraded/stale banner and that the last state remains visible with an “API unreachable” banner when the API is stopped.

## 3. Decisions and rejected alternatives

- ADR-015 adds TanStack Query and Tailwind, without adding a component library.
- ADR-016 permits repeated tick values after simulator reset and skips insertion only when the newest tick is unchanged.
- ADR-017 updates cached freshness/status in place so a failed refresh is visible quickly and same-tick recovery works without duplicate snapshots.

## 4. Files created or modified (key paths and purpose)

- `core/sim_client.py`, `core/metrics.py`: typed resilient simulator client and low-cardinality metrics.
- `worker/ingest.py`, `worker/store.py`, `worker/sse.py`, `worker/main.py`: snapshot validation/persistence, reset-aware schema migration, refresh loop, SSE reconnect, worker lifecycle.
- `api/database.py`, `api/routes/read.py`, `api/main.py`, `api/db.sql`: read-only repository and domain read routes with request metrics and CORS.
- `frontend/src/`, `frontend/Dockerfile`, `frontend/package*.json`: typed overview, three-second polling, cached state and degraded/error banners.
- `docker-compose.yml`, `.env.example`: client timeout/retry/breaker configuration.
- `tests/test_sim_client.py`, `tests/test_ingest.py`, `tests/test_sse.py`, `tests/test_read_api.py`: failure, retry, freshness, atomicity, read-only and reconnect coverage.
- `docs/api.md`, `docs/architecture.md`, `docs/data-model.md`, `docs/resilience.md`, `docs/simulator-contract.md`, `docs/decisions.md`: implementation-aligned contracts and decisions.

## 5. APIs added or changed

| Method and path | Behavior |
|---|---|
| `GET /api/state` | Latest validated snapshot plus fetch time, age, status, stale marker and `simulated: true`; 503 only when no snapshot exists. |
| `GET /api/data-health` | Latest snapshot freshness and stale status. |
| `GET /api/events` | Simulator events from the last snapshot plus open platform incidents. |
| `GET /api/metrics-summary` | Simulator service-level metrics from the last snapshot. |

## 6. Tests and verification

| Command or scenario | Expected | Actual result | Pass? |
|---|---|---|---|
| `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make test` | Full backend suite green | `51 passed in 0.96s` | PASS |
| `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make lint` | Ruff, formatting and production build green | Ruff passed; 26 files formatted; Vite transformed 75 modules and built successfully | PASS |
| `docker compose config -q` | Compose configuration valid | Exit 0 | PASS |
| `git diff --check` | No whitespace errors | Exit 0 | PASS |
| `SMOKE_SKIP_BUILD=1 FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 make smoke` | Eight services healthy; simulator and service health endpoints respond | Smoke completed; simulator reported `PAUSED`, tick 102; API, worker and predictor returned `status: ok`; frontend request succeeded | PASS |
| Live tick movement | API snapshot changes while simulator runs | Tick 96 -> 102 in six seconds; service level changed `0.879158` -> `0.851422` | PASS |
| Live stale-data fault | Stale marker and DEGRADED status appear | Detected in 2.59s; fault cleared | PASS |
| Live unavailable fault | Cached state retained, DEGRADED within 10s, recovers after clear | DEGRADED in 6.73s; same tick and station inventory retained for 60s; HEALTHY 2.57s after clear | PASS |
| Live stream-disconnect fault | Polling continues and SSE reconnects | Two reconnects and two ingests in 1.56s; snapshot age 0.58s; fault cleared | PASS |
| Missing station field | Reject aggregate, log alert, retain last good snapshot | Focused test: `1 passed`; `ValidationError`, `snapshot_rejected` log and event asserted | PASS |
| Browser API-stop scenario | Last state stays visible and shows API error | Headless Chrome retained four station rows and tick 102 and displayed “API unreachable” after API stop | PASS |
| Rendered stale/degraded state | UI marks stale snapshot and displays degraded banner | Headless Chrome displayed both labels with four station rows | PASS |
| API simulator-I/O boundary | API source has no simulator client dependency | `rg -n "sim_client" api` returned no matches | PASS |

## 7. Evidence

- `docs/evidence/sprint-02-runtime.md` records live API, simulator, browser, and fault-injection outcomes.
- Test command output and build results are summarized in Section 6; the focused malformed-field command is recorded in the evidence file.

## 8. Problems, root causes, fixes

- The initial rebuilt containers could not authenticate to the existing PostgreSQL volume. The existing local `.env` supplied a `DATABASE_URL` whose password differed from the initialized database role. The role was aligned to that existing URL through the local Postgres socket, preserving the volume and rows; `.env` was not edited.
- Live fault checks found that failure status was not persisted promptly, and same-tick success could not clear a prior DEGRADED state. Added in-place status/freshness updates and regression tests.
- The first lint run caught one overlong line in the new ingestion test. Ruff formatted the file; the subsequent full lint and build passed.
- Docker image metadata lookups initially timed out while Docker CLI credentials were consulted. An anonymous temporary Docker config fetched the pinned Python base; all three application images then built successfully. No registry configuration was changed.

## 9. Not done or limitations

- GitHub-hosted CI was not triggered. All local checks in the repository gate were run.
- The Sprint 1 inventory-exhaustion idempotent replay probe remains an explicitly carried-over simulator question.
- This machine's existing local `.env` has a database URL that differs from the Compose default Postgres password. The running database role was aligned to the local URL without editing `.env`; a newly initialized volume should use matching `DATABASE_URL` and `POSTGRES_PASSWORD` values.

## 10. Risks and next-sprint dependencies

- Simulator image runs AMD64 under emulation on this ARM64 host; observed running speed remains environment-dependent.
- Sprint 3 starts with pure forecasting and risk logic over stored snapshots/demand history; no forecast or risk behavior is claimed complete in Sprint 2.

## 11. Acceptance checklist

- [x] Dashboard numbers move while the simulator runs.
- [x] A 60-second unavailable fault retains the cached state, shows DEGRADED within 10 seconds, and recovers after clearing.
- [x] `stale_data` sets the stale marker and UI banner.
- [x] `stream_disconnect` reconnects while worker polling continues.
- [x] Missing-field input is rejected, logged, and does not replace last good data.
- [x] Tests and lint/build are green.
- [x] Docs, evidence, decisions, and sprint report updated.
- [x] User explicitly authorized automatic continuation; no commit or tag was created.

## 12. Five-minute update

1. Problem solved: operators can see current simulator state and retain a useful dashboard during simulator outages.
2. What we built: resilient typed client, atomic worker ingestion, SSE reconnect/refetch, DB-only read API, and a cached React overview with clear freshness/error states.
3. Live demonstration: run the Compose stack on port 5174, start the simulator, observe tick/inventory changes, then inject `stale_data`, `unavailable`, or `stream_disconnect` through the simulator admin endpoints.
4. Evidence: 51 backend tests pass; lint/build and smoke pass; live tick, stale, 60-second unavailable, stream, malformed-field, and Chrome API-stop checks are in `docs/evidence/sprint-02-runtime.md`.
5. Remaining gap and next step: hosted CI and the Sprint 1 inventory-exhaustion replay probe remain unrun. Sprint 3 begins with pure demand forecasting and risk calculations.

## Gate decision

Reviewer: user-authorized automatic continuation | Decision: passed locally with environment notes | No commit or tag created.
