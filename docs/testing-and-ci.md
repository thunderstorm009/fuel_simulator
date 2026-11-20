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

After the repository moves, the local suite reported 108 passing Python tests and 2 passing frontend tests. Frontend typecheck and production build passed. Sprint reports record earlier per-sprint counts, which reflect their respective code snapshots. The live Sprint 4 approval-to-`ARRIVED` and exact-key replay scenario has not been run; ordinary automated tests do not establish that live write acceptance. The source-inventory-exhaustion replay probe is also still open.

The read-only k6 workload and summary renderer are present. No load measurements are available yet; see `docs/loadtest.md`.
