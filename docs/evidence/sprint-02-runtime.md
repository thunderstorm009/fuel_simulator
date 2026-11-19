# Sprint 2 runtime evidence

Date: 2026-11-19 | Branch: `main` | Local Compose stack

## Runtime wiring

- Rebuilt the API, worker, and frontend images from the current worktree. The build completed; Vite transformed 75 modules and emitted the production bundle.
- The first startup exposed a mismatch between the existing Postgres role password and the `DATABASE_URL` in the existing local `.env`. The role password was aligned to that existing URL through the local Postgres socket. The `postgres_data` volume and rows were retained. No `.env` file was edited.
- `FRONTEND_HOST_PORT=5174` and `CORS_ORIGIN=http://localhost:5174` were used because the unrelated service still owns port 5173.
- `docker compose ps` showed all eight services running. `make smoke` returned 0 and its health output was:

  ```text
  {"status":"ok","database":"ok","simulation":{"status":"PAUSED","tick":102}}
  {"status":"ok","service":"api"}
  {"status":"ok","service":"worker"}
  {"status":"ok","service":"predictor"}
  ```

- `GET /api/state`, `/api/data-health`, `/api/events`, and `/api/metrics-summary` each returned HTTP 200. Responses included `simulated: true`; the latest state was HEALTHY and fresh. `GET /` on frontend port 5174 returned HTTP 200.
- Source scan `rg -n "sim_client" api` returned no matches; API routes read the database repository only.

## Acceptance scenarios

| Scenario | Observed result |
|---|---|
| Dashboard numbers move while simulator runs | Started at tick 96/service level `0.879158`; after six seconds the API returned tick 102/service level `0.851422`. The simulator was paused afterward. |
| `stale_data` injection | Created through `/admin/faults`; within 2.59s `/api/data-health` returned `stale: true`, `data_status: DEGRADED`, and `simulated: true`. `/admin/faults/clear` returned `{"status":"cleared"}`. |
| `unavailable` for 60 seconds | In a 120s fault window, held the fault active for 60 seconds before clearing. API returned DEGRADED within 6.73s. The cached tick and station inventory matched the prior response. After clear, status returned HEALTHY in 2.57s while the simulator remained paused at the same tick. |
| Browser behavior when API is stopped | Headless Chrome rendered all four station rows at tick 102. After stopping only the API container, it showed “API unreachable” and retained all four rows and the same tick. API was started again in a `finally` cleanup. |
| Rendered stale/degraded banner | With a live `stale_data` fault, Chrome displayed both the degraded banner and “marked stale by the simulator”; four station rows remained visible. The fault was cleared after the check. |
| `stream_disconnect` | Injected the fault, restarted only the worker to establish a fresh stream connection, then observed two SSE reconnect attempts and two successful ingestions within 1.56s. API snapshot age was 0.58s and status HEALTHY. Fault clear returned `{"status":"cleared"}`; final active-fault list was `[]`. Worker logs contained `simulator_stream_disconnected` with `SimUnavailable`. |
| Malformed fixture missing required station fields | `pytest -q tests/test_ingest.py::test_missing_station_field_is_rejected_and_keeps_last_snapshot`: `1 passed`. The test verifies `ValidationError`, the `snapshot_rejected` log and integration event, and retention of the last good snapshot. |

The temporary browser harness was installed under `/tmp/fuel-sprint2-browser`; no frontend package or project dependency was added for the browser check.

## Final verification commands

- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make test` -> `51 passed in 0.96s`.
- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make lint` -> Ruff passed; 26 files already formatted; Vite transformed 75 modules and built successfully (CSS 11.49 kB, JS 234.47 kB).
- `docker compose config -q` -> exit 0.
- `FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 docker compose config -q` -> exit 0.
- `git diff --check` -> exit 0, no output.
- `SMOKE_SKIP_BUILD=1 FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 make smoke` -> exit 0; all eight services healthy; simulator paused at tick 102; API, worker, predictor and simulator health checks returned `ok`.
- `rg -n "sim_client" api` -> no matches (exit 1 is expected when no source reference exists).
