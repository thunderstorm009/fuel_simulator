# Sprint 1 (hours 0-4): Foundation, simulator discovery, contract, skeleton

SAME REPOSITORY. Starting state: only the kit exists (tag sprint-0). Sprint 1 creates the first application folders. Later sprints extend them.

Skills: project-planning, simulator-integration, test-driven-development, verification-before-completion.

## Objective
Remove every unknown about the simulator, fix the data contract, and leave a green skeleton that starts with one command.

## Work packages (can run in parallel on separate worktrees)

### WP1.1 Simulator explorer
TASK: Write scripts/explore_sim.py (httpx). With the simulator paused: GET every public endpoint and save each response to docs/sim-samples/<name>.json. Step 10 ticks via /admin/step. Create then cancel one allocation. Inject each of the 6 event types and each of the 5 fault types (clear after each) and record status codes, headers and body shapes. Test: the same idempotency key replayed (status code), the same key with a different body, an event with start_tick in the past. Write docs/sim-findings.md answering every VERIFY item in docs/simulator-contract.md: tick_minutes, default speed, replay status (200 or 201), hour-factor boundaries, whether region demand_factor changes demand (fit from /v1/demand-history), how dispatch capacity counts in-flight and pending, and whether the image has curl or wget. Each item gets an answer or 'unknown + how to test'.
ACCEPT: re-runnable after /admin/reset; no fault left active; findings file complete.
DONT: edit the simulator.

### WP1.2 Contract and database
TASK: From docs/sim-samples write core/models.py: Pydantic v2 models for Instance, Region, Depot, Station, Route, SupplyArrival, SimEvent, Allocation, DemandObs, Metrics and Snapshot (aggregate with fetched_at, stale, data_status). Enums for fuel type and every status. Add Recommendation, Explanation, Forecast, RiskLevel, DataStatus. Add parse_sim_error(response) for all error shapes. Write api/db.sql (tables per docs/data-model.md, with indexes) and docs/api.md listing every internal endpoint with example JSON.
TESTS: every sample parses; broken copies (missing field, wrong type, unknown enum) raise; table test for the error parser.
DONT: invent fields not in the samples. Ignore unknown extra fields but require known ones.

### WP1.3 Compose, CI, skeleton
TASK: docker-compose.yml with simulator (image asifmahmoud414/bup-fuel-supply-simulator:1.0.0, port 8000, start mode paused from .env), postgres, api, worker, predictor, frontend, prometheus, grafana. api, worker and predictor are minimal FastAPI apps exposing /health and /metrics, with slim non-root Dockerfiles and pinned versions. Healthchecks and depends_on service_healthy (use sim-findings for how to probe the simulator). Create the Makefile (up, down, test, lint, smoke), one trivial pytest, ruff config, and .github/workflows/ci.yml (ruff, pytest, frontend build, docker compose build). Keep CLAUDE.md and GEMINI.md identical to AGENTS.md via scripts/bootstrap_agents.sh.
ACCEPT: docker compose up from a clean clone gives all services healthy in under 2 minutes; CI is green.
DONT: add Kubernetes; bake in secrets; build features.

## Docs to update
docs/sim-findings.md (new), docs/api.md (new), docs/data-model.md and docs/simulator-contract.md (correct anything that differs), docs/decisions.md (first ADRs), docs/PROGRESS.md.

## Acceptance checklist (real output required)
- [ ] docker compose up from a clean clone: all healthy under 2 minutes
- [ ] curl -s localhost:8000/v1/health returns ok
- [ ] a sample JSON exists in docs/sim-samples for every endpoint
- [ ] every VERIFY item has an answer in docs/sim-findings.md
- [ ] models parse every sample and reject a deliberately broken copy
- [ ] CI green
- [ ] no .env committed

## Finish
Run prompts/SPRINT-GATE.md with N=1. Do not start Sprint 2.
