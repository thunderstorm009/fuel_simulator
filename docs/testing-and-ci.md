# Testing and CI

## Test organization

- `tests/unit/`: pure domain behavior, forecasting/risk, validator/policy, explanations, recommendation jobs, and executor behavior.
- `tests/integration/`: simulator client, ingestion, SSE, API routes, service health, and Compose configuration.
- `tests/scenarios/`: simulator exploration output and saved sample contract checks.
- `web/tests/`: React Testing Library behavior for navigation/stale presentation and operator token handling.

Tests that require simulator behavior use captured payloads or controlled simulator integration evidence. Unit domain logic remains free of I/O. Historical live event/fault and browser results are recorded under `docs/evidence/` and the individual sprint reports.

## Local commands

```sh
make lint       # Ruff lint/format check, frontend typecheck and production build
make test       # Python suite and frontend component tests
make smoke      # Compose service health and HTTP smoke checks
npm --prefix web run typecheck
npm --prefix web run test
npm --prefix web run build
docker compose config -q
```

## GitHub Actions

`.github/workflows/ci.yml` pins action release tags, caches Python/frontend dependencies, runs Python lint/tests and frontend typecheck/tests/build, then builds and starts the Compose stack, waits for health, curls `/api/health`, and uploads Compose logs on failure. The hosted workflow has not been triggered for this work. Its Compose job has not been exercised locally in this resumed session because Docker is unavailable.

## Current evidence and limits

136 Python tests (unit + integration) and 6 frontend tests pass locally. Frontend typecheck and production build pass. `make lint` (ruff + tsc + vite) is clean. `actionlint` reports no errors on `.github/workflows/ci.yml`. Load test results are present in `docs/results/`; see `docs/loadtest.md`.

The hosted GitHub Actions workflow has not been triggered. It cannot be triggered from this environment. The local equivalent commands (Python lint/test, frontend test/typecheck/build, `docker compose config -q`) all pass.

The read-only k6 workload (`loadtest/k6.js`) runs against the live stack; see `docs/results/` for the measured summaries. No load measurements are invented.
