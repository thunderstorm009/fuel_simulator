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

`.github/workflows/ci.yml` runs Python lint/tests, frontend install/typecheck/tests/build, and a Compose image build on GitHub Actions. It does not launch the live simulator stack. The hosted workflow has not yet been triggered for this work; local command results are reported separately in `docs/PROGRESS.md` and sprint evidence.

## Current evidence and limits

After the repository moves, the local suite reported 108 passing Python tests and 2 passing frontend tests. Frontend typecheck and production build passed. Sprint reports record earlier per-sprint counts, which reflect their respective code snapshots. The live Sprint 4 approval-to-`ARRIVED` and exact-key replay scenario has not been run; ordinary automated tests do not establish that live write acceptance. The source-inventory-exhaustion replay probe is also still open.

No load-test tool or measured load report is currently present. A future CI change should add it only with a defined deterministic environment and a report containing real measured output.
