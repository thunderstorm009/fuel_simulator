# Sprint 1 runtime evidence

Date: 2026-11-19 | Branch: `main` | Simulator image: `asifmahmoud414/bup-fuel-supply-simulator:1.0.0`

## Runtime startup and health

Docker Desktop was started locally; `docker info --format '{{.ServerVersion}}'` returned `29.6.2`.

The first `docker compose up --build -d` built the API, worker, predictor, and frontend images and started the backend services. It exited 1 when binding the frontend: `Bind for 0.0.0.0:5173 failed: port is already allocated`. `lsof` and `docker ps` showed that an unrelated existing `porikroma-frontend` container owns port 5173. It was left running.

Compose now reads `FRONTEND_HOST_PORT` (default 5173), and the smoke script resolves the published port from Compose config. With the unrelated container preserved, this command passed:

```text
SMOKE_SKIP_BUILD=1 FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 make smoke
```

The script exited 0 after reporting these responses:

```text
{"status":"ok","database":"ok","simulation":{"status":"PAUSED","tick":96}}
{"status":"ok","service":"api"}
{"status":"ok","service":"worker"}
{"status":"ok","service":"predictor"}
```

At the time of `docker compose ps`, all eight services were healthy:

```text
api healthy
frontend healthy (0.0.0.0:5174->80/tcp)
grafana healthy
postgres healthy
predictor healthy
prometheus healthy
simulator healthy
worker healthy
```

Additional checks returned HTTP 200 for simulator health, frontend root, Prometheus `/-/healthy`, and Grafana `/api/health`. API, worker, and predictor returned `{"status":"ok","service":"..."}`. Simulator health returned `{"status":"ok","database":"ok","simulation":{"status":"PAUSED","tick":0}}` before the explorer's tick probes.

## Live contract probes

- `scripts/explore_sim.py --base-url http://localhost:8000` completed successfully multiple times and returned exit 0. `docs/sim-samples/exploration-results.json` contains 214 response records from the final run, including HTTP statuses, headers, and body shapes. The samples include endpoint reads, depot/station details, admin audit, six events, five faults, idempotency, stream behavior, and 96 demand ticks.
- Every event injection returned 201 and its step returned 200. Every fault injection returned 201 and clear returned 200. Final `GET /admin/faults` returned `[]`.
- Stale data returned HTTP 200 with `X-Simulator-Stale: true`. Unavailable/error-rate returned 503 with `error.code=FAULT_INJECTED`; stream disconnect returned 503 with `detail.code=FAULT_INJECTED` in the stream body.
- Same-body allocation replay returned 201 with the same ID; same key/different body returned 409 `IDEMPOTENCY_KEY_MISMATCH`.
- The full-day demand sample has 1,152 rows over 96 ticks and 4 stations. Hourly normalized demand showed the documented inclusive hour boundaries and the 1.08 Chattogram region multiplier within demand noise.
- Dispatch probe: two 6,000 L same-tick pending shipments at the Gazipur 12,000 L limit were accepted; a third 1 L request returned 409 `DISPATCH_CAPACITY_EXCEEDED`. After one step, the first two allocations were `IN_TRANSIT`, and another 1 L shipment on the new tick was accepted.
- Replay probe: after the original request and additional allocations filled the dispatch budget, exact replay returned 201 with the original ID. The separate source-inventory-exhaustion replay case was not run.
- Past event probe: at tick 10, `start_tick=0`, `duration_ticks=1` returned 201 with `SCHEDULED`; after one step to tick 11, GET events reported `ACTIVE` despite `end_tick=1`.
- The image reports `linux/amd64`; this host is ARM64. Image config inspection found `simulation_speed=8.0`, `tick_minutes=15`, and paused startup defaults. With no environment overrides, 60 ticks advanced in 10.043 seconds (5.97 observed ticks/s under emulation).
- In the image, `command -v curl` returned `/usr/bin/curl`, `command -v wget` returned no path, and Python was at `/opt/venv/bin/python`.

## Checks

- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make test`: 26 passed.
- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make lint`: Ruff check and format passed; frontend production build passed.
- `docker compose config -q`: exit 0. `FRONTEND_HOST_PORT=5174 docker compose config -q`: exit 0.
- `git diff --check`: exit 0.
- The first `make smoke` rebuild retry and `docker compose build --pull=false` were interrupted after Docker Hub metadata lookups stopped making progress. The service images had already built successfully during the first `docker compose up --build -d`; runtime smoke then passed using those images with `SMOKE_SKIP_BUILD=1`.
- `.env` is ignored and untracked; no `.env` path is returned by `git ls-files -- .env`.
