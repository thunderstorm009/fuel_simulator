# Sprint 01 Report: Foundation, simulator discovery, contract, skeleton

**Path note:** The key paths below reflect the repository layout at Sprint 1. They were later moved into `backend/`, `intel/predictor/`, `web/`, and `observability/`; see `docs/DAY-1-UPDATE.md` for the current tree.

Time window: 2026-11-19 resume review | Owner(s): Codex | Branch and tag: `main`, last tag `sprint-0` | Status: Passed with environment notes

## 1. Objective

Create the first fixture-backed application contract and service skeleton, explore the official simulator, and leave a Compose stack that can be started and checked from a clean clone.

## 2. What now exists (behavior, not just files)

- Pydantic v2 models validate the documented simulator entities, enums, snapshots, forecasts, recommendations, and normalized error payloads. Unknown extra fields are ignored; missing required values, invalid types, and unknown enum values fail validation.
- The official simulator image was run. Live samples, status/header/body-shape records, and findings now cover the listed REST/admin endpoints, events, faults, idempotency, and a 96-tick demand history. Two retained examples remain explicitly guide-derived.
- API, worker, and predictor skeletons serve `/health` and `/metrics`. The frontend production build succeeds and its UI is labelled `SIMULATED`.
- A PostgreSQL schema, separate-service Compose topology, Prometheus configuration, simulator exploration script, and CI workflow are present. Frontend host port is configurable while defaulting to 5173.

## 3. Decisions and rejected alternatives

- ADR-012 keeps core metrics, logs, and one measured load path in scope; Grafana polish is lower priority.
- ADR-013 accepts the separate API, worker, predictor, frontend, Prometheus, and Grafana Compose topology.
- ADR-014 makes the frontend host port configurable after an unrelated container occupied 5173. The default remains 5173; the smoke script reads the resolved Compose port.
- Live simulator results are recorded in `docs/sim-findings.md`; details and command evidence are in `docs/evidence/sprint-01-runtime.md`.

## 4. Files created or modified (key paths and purpose)

- `core/models.py`, `tests/test_models.py`, `tests/test_sample_contract.py`: validated models and fixture/error-shape coverage.
- `api/`, `worker/`, `predictor/`, `frontend/`: minimal service health/metrics endpoints and labelled UI.
- `api/db.sql`, `docker-compose.yml`, `.github/workflows/ci.yml`, `infra/`, `Makefile`: persistence, service topology, CI, monitoring config, and local commands.
- `scripts/explore_sim.py`, `tests/test_explorer.py`, `docs/sim-samples/`, `docs/sim-findings.md`: re-runnable live exploration, captured samples, and findings.
- `docker-compose.yml`, `.env.example`, `scripts/smoke.sh`, `tests/test_compose_config.py`: configurable frontend publication and a smoke check that follows the resolved port.
- `docs/PROGRESS.md`, `docs/decisions.md`: current state, blockers, and decision record.

## 5. APIs added or changed

- `GET /health` and `GET /metrics` exist on API (`8101`), worker (`8102`), and predictor (`8103`). These are skeleton endpoints; the application read API and simulator ingestion behavior are not implemented in Sprint 1.

## 6. Tests and verification

| Command or scenario | Expected | Actual result | Pass? |
|---|---|---|---|
| `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make test` | Fixture/model/service tests pass | `26 passed in 0.57s` | PASS |
| `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make lint` | Ruff, format, frontend build pass | Ruff checks passed; `15 files already formatted`; Vite production build completed | PASS |
| `docker compose config -q` and `FRONTEND_HOST_PORT=5174 docker compose config -q` | Default and overridden Compose configs parse | Both exit 0 | PASS |
| Docker image build during `docker compose up --build -d` | API, worker, predictor, frontend images build | All four reported `Built`; startup later hit only the host port conflict | PASS |
| `SMOKE_SKIP_BUILD=1 FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 make smoke` | All services healthy; API and simulator health pass | Exit 0; all eight services healthy and all four API/simulator health requests returned `ok` | PASS |
| Live simulator explorer | Re-runnable; all configured probes captured; no fault left active | Exit 0; 214 final response records; six event injections and five fault cases captured; final `GET /admin/faults` returned `[]` | PASS |
| `docker info --format '{{.ServerVersion}}'`; image default probe | Docker and official simulator respond | Docker `29.6.2`; image default reports 15-minute ticks and speed 8.0 in `/app/app/config.py` | PASS |
| `git diff --check` | No whitespace errors | Exit 0, no output | PASS |
| `.env` tracked-file check | No `.env` committed | `git ls-files -- .env` returned no path; `.env` is ignored | PASS |
| Hosted GitHub CI run | Workflow reports green | Not triggered; local Python, frontend, Compose config, and image-build checks were run | NOT-RUN |

## 7. Evidence

- `docs/evidence/sprint-01-runtime.md` records real runtime commands, health outputs, integration probes, and the environment-specific port collision.
- `docs/sim-samples/exploration-results.json` and the live endpoint sample files contain captured statuses, headers, body shapes, and response bodies.

## 8. Problems, root causes, fixes

- An unrelated `porikroma-frontend` container owns port 5173. The first Compose startup therefore failed when binding the project frontend. Added `FRONTEND_HOST_PORT` (default 5173) and made smoke resolve the configured published port; the full runtime smoke passed on 5174 without stopping the unrelated service.
- One full-speed `make smoke` retry and a later `docker compose build --pull=false` stalled at Docker Hub metadata lookup and were interrupted. The images had already built successfully during the first Compose startup; the smoke run passed against those built images with `SMOKE_SKIP_BUILD=1`.
- The initial post-explorer test run exposed empty tick-zero fixtures overwriting the canonical event/allocation/demand samples. The explorer now refreshes these canonical samples after creating data; the repeat capture and all 26 tests passed.

## 9. Not done or limitations

- The source-inventory-exhaustion replay case remains untested. A replay after dispatch capacity was consumed returned the original ID; see the remaining procedure in `docs/sim-findings.md`.
- The GitHub-hosted workflow itself was not triggered. Its lint/test/frontend/config/build steps were checked locally, with image builds completed in the first Compose startup.
- The official simulator is an AMD64 image on this ARM64 host; the observed timing probe is emulation-dependent.

## 10. Risks and next-sprint dependencies

- Sprint 2 begins after this gate. Keep the inventory-specific replay question documented and preserve the rule to revalidate constraints immediately before submission.

## 11. Acceptance checklist

- [x] Compose starts all services healthy in under two minutes with `FRONTEND_HOST_PORT=5174`; the port override is needed only because an unrelated container owns 5173
- [x] `curl -s localhost:8000/v1/health` returns `ok`
- [x] Live sample JSON exists for the documented public and admin endpoints; explorer records status, headers, and body shapes
- [x] Every VERIFY item has a live finding or a remaining explicit unknown and a procedure in `docs/sim-findings.md`
- [x] Fixture model tests parse documented samples and reject invalid values; 26 tests pass
- [x] All CI job checks pass locally; GitHub workflow itself was not triggered
- [x] No `.env` committed
- [x] Tests, lint, frontend build, Compose config, image build, smoke, and `git diff --check` recorded above
- [x] Human explicitly authorized automatic continuation after Sprint 1 passes its verification criteria

## 12. Five-minute update

1. Problem solved: established a validated contract and runnable service skeleton for the integrated fuel platform.
2. What we built: typed models/error parsing, guide-derived fixtures, service health/metrics endpoints, PostgreSQL schema, Compose/CI skeleton, and a SIMULATED-labelled frontend.
3. Live demonstration: run `FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 make up`, verify simulator `/v1/health`, inspect API/worker/predictor health, and open the frontend on 5174.
4. Evidence: 26 tests pass; Ruff and frontend build pass; all eight containers are healthy; six event and five fault probes passed; live contract findings are captured under `docs/`.
5. Remaining gap and next step: hosted GitHub CI was not triggered and source-inventory-exhaustion replay is not directly probed. Proceed to Sprint 2 while retaining these limitations.

## Gate decision

Reviewer: automated continuation explicitly authorized by user | Decision: passed with environment notes | Notes: runtime smoke required host port 5174 because an unrelated container occupied 5173. No commit or tag was created.
