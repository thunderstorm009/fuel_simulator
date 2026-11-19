# Sprint 4 runtime evidence — 2026-11-19

## Local verification

- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make test`: **108 passed in 1.34s**.
- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make lint`: Ruff check passed; 48 files formatted; Vite production build passed. Main bundle 249.06 kB (76.85 kB gzip); trajectory chunk 426.04 kB (122.33 kB gzip).
- `FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 docker compose config -q`: exit 0.
- `git diff --check`: exit 0.
- `SMOKE_SKIP_BUILD=1 FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 make smoke`: passed. All eight Compose services healthy; simulator reported `PAUSED`, tick 114; API, worker, and predictor health endpoints returned `{"status":"ok"...}`.
- `docker compose build api worker`: passed; rebuilt images started healthy.
- `docker compose build frontend`: **blocked** twice while Docker attempted to load `node:22.14.0-alpine` and `nginx:1.27.5-alpine` metadata; BuildKit returned `DeadlineExceeded: context deadline exceeded`. Host `npm run build` passed. To verify the new UI against the running services, the generated `frontend/dist` files were copied into the existing Nginx container for this local runtime check.

## Runtime integration

- `GET /health` on API and worker returned `status=ok`; `docker compose ps` showed all eight services healthy.
- API `GET /api/recommendations` returned six persisted `PROPOSED` items; `GET /api/decisions` returned zero decisions. Worker metrics showed `recommendations_created_total 6`, `recommendation_job_failures_total 0`, and `simulator_allocation_rejections_total 0`.
- Simulator `GET /v1/allocations` returned zero allocations. None of the six recommendation keys appeared in simulator allocations. The worker did not submit any proposal without an operator approval.
- Headless Chrome opened the Recommendations view and found six cards, six approval controls, an in-memory password token field, the decision-history section, and the `SIMULATED` label. It reported zero page or console errors. No approval button was activated.
- Focused API and executor tests verify token enforcement, idempotent double approval, required rejection reason, stale-data blocking, local validation blocking, exact-body retry after timeout, and fail-closed handling of an existing idempotency key bound to another request body.

## Live acceptance not run

The simulator remained paused at tick 114. The required live approve → allocation → ARRIVED → exact same-key replay sequence was not run because it requires an operator to approve a concrete recommendation. The no-auto-submit rule was preserved. Simulator rejection count is zero because there were no submissions; it is not evidence of a successful live accepted-write scenario.

## Independent safety review

An independent read-only R3 review found no unresolved P0 or P1 allocation-safety defects. It traced validation order, reservations, approved/open recommendation dedupe, fresh reads, approval, stable-key retries, and mismatch handling. The reviewer marked the live simulator approval/arrival/replay as an outstanding P2 verification gap pending operator approval. No files were changed by the reviewer.
