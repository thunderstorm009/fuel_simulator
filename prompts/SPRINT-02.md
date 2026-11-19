# Sprint 2 (hours 4-8): Resilient ingestion, read API, live dashboard

SAME REPOSITORY. Starting state: tag sprint-1 (models, schema, compose skeleton, sim-findings). Extend those files. Do not recreate them.

Skills: simulator-integration, resilience-testing, observability-metrics, test-driven-development, verification-before-completion.

## Objective
The dashboard shows live simulator data and survives simulator faults.

## Work packages

### WP2.1 Resilient simulator client
TASK: core/sim_client.py. Async SimClient with a method per GET endpoint and create_allocation(body). Timeouts connect 2s, read 3s. tenacity retries: 3 attempts, 0.2/0.4/0.8s backoff with jitter on timeouts, connection errors and 503 FAULT_INJECTED; applies to GETs and to POST only with the same key and body. Never retry 409 or 422. Circuit breaker: open after 5 consecutive failures, half-open after 10s, state exposed. Return typed results including the stale flag from X-Simulator-Stale. Raise typed exceptions SimUnavailable, SimInvalidResponse, SimBusinessError(code). All settings from env. Prometheus counters for calls, retries, failures, breaker state.
TESTS (respx, fake clock, no real sleeping): success, each error shape, timeout, malformed JSON, missing field, stale header, replay with same key, breaker open then half-open then closed.
DONT: share mutable global state without a lock.

### WP2.2 Ingestion worker and SSE
TASK: worker/ingest.py, worker/sse.py, worker/main.py. Every INGEST_INTERVAL_S (default 5) fetch instance, depots, stations, routes, supply-arrivals, events, allocations, metrics and demand-history (limit=100 per station). Build and validate ONE Snapshot atomically. On success insert it (skip when the tick is unchanged); on failure keep the last good snapshot, write an integration_events row and increment a metric. Compute data_status (HEALTHY under 15s old, not stale, breaker closed; DEGRADED stale, half-open, 15-120s old or fallback active; OFFLINE over 120s). Write a worker heartbeat. SSE: consume /v1/stream; any event only triggers an immediate refresh (max 1 per second); reconnect with exponential backoff capped at 30s, including on 503; refetch after every reconnect; ignore 15s keepalive silence. Prune old snapshots.
TESTS with a fake SimClient: unchanged tick skipped, partial failure keeps last good, stale flag gives DEGRADED, SSE reconnect refetches.
DONT: use SSE payloads as state; block the event loop.

### WP2.3 Read API
TASK: api/main.py and api/routes/. GET /api/state (latest snapshot plus data_age_seconds and data_status), /api/data-health, /api/events (simulator events plus incidents), /api/metrics-summary (simulator service level). CORS origin from env. Read the database only. Return 200 with a stale marker when data is old; 503 only if no snapshot has ever been stored. Middleware for request count and latency histogram by route template and status class.
TESTS: seeded database, stale case, empty database case.
DONT: import sim_client in routes.

### WP2.4 Frontend overview
TASK: Vite React TS Tailwind app in frontend/. Overview page: header (permanent SIMULATED badge, tick and sim time, data status badge with data age), stations-by-fuel matrix with inventory/capacity bars, depots panel, routes list coloured by status, events timeline, degraded banner. TanStack Query polling every 3s. On API error keep the last data and show 'API unreachable'. Typed API client, VITE_API_URL env, nginx Dockerfile.
ACCEPT: values match the simulator; stopping the API keeps the last data on screen with a banner.
DONT: add heavy UI libraries; ship mock data in the production path.

## Docs to update
docs/simulator-contract.md and docs/resilience.md (what is implemented), docs/architecture.md, docs/decisions.md, docs/PROGRESS.md.

## Acceptance checklist (real output required)
- [ ] dashboard numbers move while the simulator runs
- [ ] inject unavailable for 60s: UI keeps last state, shows stale badge and degraded banner within 10s, and recovers by itself after clearing
- [ ] inject stale_data: badge appears and the snapshot is flagged
- [ ] inject stream_disconnect: polling continues and the SSE client reconnects
- [ ] a fixture with a missing field is rejected, an alert is logged, the UI is unaffected
- [ ] tests and lint green

## Finish
Run prompts/SPRINT-GATE.md with N=2. Do not start Sprint 3.
