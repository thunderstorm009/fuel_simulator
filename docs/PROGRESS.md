# Project progress

Last updated: 2026-11-19. This file is the working status record; sprint reports preserve the evidence available at each sprint boundary.

## Current state

- Current milestone: repository organization, engineering documentation, and Day 1 publication for Sprints 1–4.
- Current branch: `main`; last repository tag is `sprint-0`. Existing local Sprint 0 commit is ahead of the originally inspected `origin/main`; no history was reset or rewritten.
- Publication commit/push: not yet completed. The local changes are being reviewed and staged for the requested commit.
- Sprints 1–3: locally passed and documented.
- Sprint 4: implementation and local verification are present, but the live acceptance gate remains open. No operator-approved simulator allocation was submitted; `ARRIVED` and exact same-key replay remain unverified.
- User authorized continuing with Sprint 5 after this publication milestone. Preserve the Sprint 4 gap as an explicit unresolved acceptance item; do not claim it passed or perform a simulator write without an operator decision.

## Current repository organization

- API: `backend/api/`; worker: `backend/worker/`; shared backend core: `backend/shared/core/`.
- Independent predictor: `intel/predictor/`; React application: `web/`; Prometheus/Grafana: `observability/`.
- Tests: `tests/unit/`, `tests/integration/`, `tests/scenarios/`, plus frontend tests in `web/tests/`.
- Application and engineering docs remain public. Personal instructions, `.agents/skills/`, prompts, local helper scripts, and migration notes remain on disk under their existing paths or `.local/` and are excluded from the Git index.

## Verification after organization

- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make test`: 108 Python tests passed in 1.50s; 2 frontend tests passed.
- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make lint`: Ruff passed, 49 Python files formatted, frontend TypeScript check passed, Vite production build passed (499 modules).
- `docker compose config -q`: passed.
- `FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 docker compose up -d --no-build`: returned 0. API, worker, predictor images rebuilt; existing frontend image remained in use because the frontend image build was blocked by Docker Hub metadata timeout.
- `SMOKE_SKIP_BUILD=1 FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 make smoke`: passed. Simulator was PAUSED at tick 114; API, worker and predictor returned `status: ok`; all six platform services reported healthy. Frontend returned HTTP 200. Prometheus targets for API, worker, predictor were all `up`.
- `docker compose build`: API, worker, and predictor images built; frontend image build was blocked fetching `nginx:1.27.5-alpine` metadata (`DeadlineExceeded: context deadline exceeded`). This is an external image metadata failure, not a host frontend compilation failure.
- Final backend/frontend tests, Compose config, and `git diff --check` passed. `.env`, local prompts, and local skills are ignored; `.env.example` remains publishable. Hosted GitHub Actions has not been run.

## Sprint 1–4 implementation summary

- Sprint 1: simulator contract exploration, typed models, service skeletons, Compose and monitoring topology. Historical gate: 26 tests passed; local runtime/health and exploration evidence recorded. Source-inventory-exhaustion replay remains a simulator probe gap.
- Sprint 2: resilient worker client/ingestion, PostgreSQL snapshots, database-backed API, live dashboard and fault handling. Historical gate: 51 tests passed with live runtime evidence.
- Sprint 3: demand and inventory forecasting, Monte Carlo risk, API and UI. Revised acceptance preserves official simulator semantics: event resolution restores the multiplier, not consumed stock; an unrelated depot ETA change does not alter station risk. Historical gate: 72 tests passed and live evidence recorded.
- Sprint 4: constrained recommendations, explanations, token-protected decision routes, and safe worker executor. Current code has local test/build/runtime coverage, but the live approved allocation → `ARRIVED` → exact replay acceptance has not run.
- Detailed single engineering update: `docs/DAY-1-UPDATE.md`. Individual reports and runtime observations: `docs/sprint-reports/` and `docs/evidence/`.

## Known limitations and environment notes

- No simulator allocation was submitted. Do not use a live approval as a routine smoke test.
- Predictor is currently an independent health/metrics service; worker forecast RPC/fallback is not implemented.
- Prometheus scrape configuration and Grafana data source exist; dashboards and alert rules are not provisioned.
- A measured load test and report remain unimplemented; no performance numbers are claimed.
- GitHub Actions workflow exists, but a hosted run has not been triggered.
- Docker Hub metadata timeout prevented the fresh frontend image build. Host typecheck, component tests, and production build passed.
- Development host is ARM64 running the official AMD64 simulator image; tick speed is environment-dependent.
- Local `.env` database credentials must match the initialized PostgreSQL volume. The local port 5173 was occupied during prior runs; port 5174 with matching CORS origin is verified.

## Next work

After this publication milestone, proceed with Sprint 5 as explicitly authorized, following its local acceptance criteria and preserving the Sprint 4 live gate as open. First inspect `.local/prompts/SPRINT-05.md` and `docs/PROGRESS.md`; do not redo earlier implementation or infer predictor/fallback behavior that is not present.

## Sprint log

| Sprint | Status | Report |
|---|---|---|
| 1 | Passed locally with environment notes | [sprint-01.md](sprint-reports/sprint-01.md) |
| 2 | Passed locally with runtime evidence | [sprint-02.md](sprint-reports/sprint-02.md) |
| 3 | Passed locally with revised simulator-semantic acceptance | [sprint-03.md](sprint-reports/sprint-03.md) |
| 4 | Implementation/local checks complete; live approval, arrival, and replay open | [sprint-04.md](sprint-reports/sprint-04.md) |
| 5 | Not started in this publication checkpoint; authorized next | |
| 6 | Not started | |
| 7 | Not started | |
