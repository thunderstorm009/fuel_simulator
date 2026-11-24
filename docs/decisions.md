# Decision log (ADR style). Add an entry when a decision is made. Template: docs/templates/adr.md

Statuses: PROPOSED, ACCEPTED, SUPERSEDED.

| ID | Decision | Status | Sprint |
|---|---|---|---|
| ADR-001 | REST is truth; SSE is only a hint to refetch | ACCEPTED | 1 |
| ADR-002 | Worker owns simulator I/O; API reads the database only | ACCEPTED | 1 |
| ADR-003 | Heuristic allocation first; optimizer only if time remains | ACCEPTED | 1 |
| ADR-004 | Monte Carlo for stockout uncertainty | ACCEPTED | 3 |
| ADR-005 | Outbox-style executor: approve records intent, executor re-validates and submits | ACCEPTED | 4 |
| ADR-006 | Idempotency key rec-<uuid>, stored, reused only for the identical body | ACCEPTED | 4 |
| ADR-007 | Predictor as its own container with baseline fallback | ACCEPTED | 5 |
| ADR-008 | No Kubernetes or RL; Docker Compose only | ACCEPTED | 1 |
| ADR-009 | Operator token from env protects approve, reject and chaos endpoints | ACCEPTED | 4 |
| ADR-010 | Co-host API and worker in one application container while preserving the DB-only API / worker-I/O boundary | SUPERSEDED | 1 |
| ADR-011 | Defer predictor and Prometheus/Grafana containers until their sprint; retain predictor separation for the outage demo | SUPERSEDED | 1 |
| ADR-012 | Treat minimum operator-visible metrics, logs, and one meaningful load-test report as core deliverables; Grafana polish remains P1 | ACCEPTED | 1 |
| ADR-013 | Follow Sprint 1's separate API, worker, predictor, frontend, Prometheus and Grafana Compose topology | ACCEPTED | 1 |
| ADR-014 | Keep frontend host port configurable with 5173 as the default | ACCEPTED | 1 |
| ADR-015 | Use TanStack Query for overview polling and Tailwind for the Sprint 2 frontend | ACCEPTED | 2 |
| ADR-016 | Allow repeated simulator ticks across reset cycles; skip only an unchanged latest tick | ACCEPTED | 2 |
| ADR-017 | Mark cached state degraded immediately on ingestion failure and refresh same-tick status on recovery | ACCEPTED | 2 |
| ADR-018 | Use Recharts for the Sprint 3 forecast trajectory band | ACCEPTED | 3 |
| ADR-019 | Project only known station allocation arrivals; do not infer future depot-to-station dispatches | ACCEPTED | 3 |
| ADR-020 | Separate demand forecast recovery from inventory recovery after demand events | ACCEPTED | 3 |
| ADR-021 | Organize application source by runtime responsibility while preserving independent services | ACCEPTED | Publication |
| ADR-022 | Keep personal AI workspace local and publish application/engineering artifacts only | ACCEPTED | Publication |
| ADR-023 | Use feature-based React modules with shared transport, types and UI components | ACCEPTED | Publication |
| ADR-024 | Set a separate SSE read timeout above the simulator's 15s keepalive interval | ACCEPTED | 2 |
| ADR-025 | Keep recommendation identity and request body visible through operator review | ACCEPTED | 4 |
| ADR-026 | Separate service availability from decision-pipeline freshness | ACCEPTED | 4 |
| ADR-027 | Replace same-tick snapshot payload when refreshing its metadata | ACCEPTED | 4 |
| ADR-028 | Keep overnight operator notes local | ACCEPTED | 4 |
| ADR-029 | Validate resolved Compose service credentials without exposing values | ACCEPTED | 4 |
| ADR-030 | Alert on the age of the last successful ingestion | ACCEPTED | 5 |
| ADR-031 | Install k6 locally via brew for Sprint 6 load evidence | ACCEPTED | 6 |
| ADR-032 | Scenario runner uses pure policy functions on frozen DB snapshot | ACCEPTED | 6 |
| ADR-033 | Scenario runner definition and determinism verification | ACCEPTED | 6 |
| ADR-034 | Three-condition k6 load benchmark with container resource sampling | ACCEPTED | 6 |
| ADR-035 | Sprint 7 freeze, cold-start verification, and predictor dual-port routing | ACCEPTED | 7 |
| ADR-036 | WP8.0 truth pass, admin endpoint route remediation, and tag alignment | ACCEPTED | 8 |
| ADR-037 | Two-pass emergency triage policy and full event coverage | ACCEPTED | 8 |
| ADR-038 | Pure detection engine, depot supply risk projection, and adaptive simulator freshness | ACCEPTED | 8 |
| ADR-039 | Uncertainty-Aware Safety Buffer and Linear Flow Optimization Policy | ACCEPTED | 9 |
| ADR-040 | Generative Incident Explanations and LLM Operational Boundaries | ACCEPTED | 9 |
| ADR-041 | Token Rate Limiting, Version Metadata API, and Automated Deployment Rollback | ACCEPTED | 10 |
| ADR-042 | Sprint 11 truth pass, physical boundary arithmetic, and compliance recount | ACCEPTED | 11 |
| ADR-043 | Matplotlib plotting library as dev dependency for boundary and backtest visualization | ACCEPTED | 11 |
| ADR-044 | Multi-worker Uvicorn, connection pool enlargement, composite indexing, and byte-level caching | ACCEPTED | 12 |
| ADR-045 | Push invalidation over SSE with PostgreSQL LISTEN/NOTIFY and polling fallback | ACCEPTED | 12 |
| ADR-046 | Alertmanager routing and local webhook receiver under compose profile 'alerts' | ACCEPTED | 12 |
| ADR-047 | Runtime policy switch with automatic rollback and constraint validation | ACCEPTED | 12 |
| ADR-048 | Browser end-to-end and accessibility testing via Playwright and axe-core | ACCEPTED | 13 |
| ADR-049 | Cross-directory Playwright module resolution and fail-fast discovery guard | ACCEPTED | Day 4/5 |
| ADR-050 | In-memory snapshot cache invalidation on same-tick in-place metadata updates | ACCEPTED | 14 (Day 6) |
| ADR-051 | Circuit breaker half-open probe concurrency guard and sequential instance pre-flight | ACCEPTED | 14 (Day 6) |
| ADR-052 | Standardized frontend base URL port resolution across shell scripts | ACCEPTED | 14 (Day 6) |

## Entries
(Add full entries below as decisions are made.)

### ADR-005 — Persist approval intent before simulator execution

- **Status:** ACCEPTED
- **Context:** Approval and simulator I/O have different failure and security boundaries. The API is a database-only read path except for recording operator decisions; worker owns all simulator traffic.
- **Decision:** Approve/reject updates the recommendation and decision log in a database transaction. The worker polls approved rows, fetches a fresh simulator snapshot, checks freshness, validates again, and then submits the stored request. An ambiguous transport failure leaves the recommendation SUBMITTED so the executor can retry safely.
- **Trade-off:** An approved item may remain pending during simulator outage; the UI shows its progression and errors.

### ADR-006 — Bind permanent idempotency keys to exact request bodies

- **Status:** ACCEPTED
- **Context:** Simulator keys are permanent. An uncertain POST result must be replayable without creating a second allocation, and the same key cannot be reused for a changed request.
- **Decision:** Generate and persist one `rec-<uuid>` key and the exact JSON body when creating a recommendation. Retry with that body only. A fresh simulator read may match an existing allocation by key only after verifying every allocation term; a key with a different body fails closed locally before any POST.
- **Trade-off:** If stored request data is inconsistent, execution requires operator investigation rather than attempting repair or inventing a new key.

### ADR-009 — Protect operator decisions with an environment token

- **Status:** ACCEPTED
- **Context:** The browser exposes approve and reject actions, but the UI must not persist operator credentials or call simulator write endpoints.
- **Decision:** Require `X-Operator-Token` sourced from `OPERATOR_TOKEN` for API decision routes. Keep the token in React memory only; API writes local decision state and worker performs simulator I/O.
- **Trade-off:** Reloading the page requires entering the token again.

### ADR-010 — Co-host API and worker in one application container

- **Status:** SUPERSEDED by ADR-013
- **Context:** The 28-hour plan calls for a usable API, background ingestion and execution, database, UI, simulator, predictor, and monitoring stack. Separate API and worker containers add orchestration and health-check work during the foundation sprint.
- **Proposal:** Keep API routes database-only and keep all simulator calls inside a worker module, but run the worker as a managed background task in the same application container. Preserve clear module boundaries and worker heartbeat/status. This saves one container while retaining the hard I/O ownership rule.
- **Trade-off:** API and worker process failures become coupled; a later split can happen only if the demo shows a concrete need.

### ADR-011 — Stage optional service containers

- **Status:** SUPERSEDED by ADR-013
- **Context:** Building and validating all eight planned containers in Sprint 1 consumes time before the core operator workflow exists.
- **Proposal:** Sprint 1 brings up only the simulator, database, combined application service, and UI. Add the separate predictor in Sprint 5 to demonstrate predictor failure and fallback. Add Prometheus and Grafana in Sprint 5 after core workflow metrics and logs exist.
- **Trade-off:** Monitoring dashboards and predictor-failure demonstration arrive later, but do not block the live data, risk, recommendation, approval, and safe-submit path.

### ADR-012 — Core delivery priority for observability and load evidence

- **Status:** ACCEPTED
- **Context:** The participant brief calls for meaningful observability and requires a load test with reported measurements. The current project plan labels metrics/Grafana and load testing P1, which could leave required evidence until after the core time budget.
- **Proposal:** Keep low-cardinality metrics and structured logs on each implemented behavior, plus one measured load-test path and honest report, in the 28-hour core. Keep Grafana panels, broad multi-scenario load runs, and dashboard polish P1.
- **Trade-off:** Protect evidence for brief requirements while limiting monitoring infrastructure and benchmark scope.

### ADR-013 — Follow the separate-service Sprint 1 topology

- **Status:** ACCEPTED
- **Context:** The Sprint 1 specification explicitly requires separate API, worker, predictor, frontend, Prometheus, and Grafana services. That supersedes the earlier bootstrap proposals to co-host services or defer containers.
- **Decision:** Implement the specified services in Docker Compose, with PostgreSQL and the official simulator. Keep service code minimal in Sprint 1 and preserve the API-read/worker-I/O boundary.
- **Trade-off:** More startup and image-build work now; separate process health and the predictor outage demonstration are available without a later topology change.

### ADR-014 — Keep frontend host port configurable with 5173 as the default

- **Status:** ACCEPTED
- **Context:** An unrelated existing container may already bind the conventional frontend host port, which prevented Compose from starting the frontend and Grafana health chain in this environment.
- **Decision:** Publish the frontend on `FRONTEND_HOST_PORT` with a default of 5173, and have the smoke script read the resolved port from Compose config. Operators can select a free port without stopping other services.
- **Trade-off:** When changing the frontend port, set `CORS_ORIGIN` to the matching browser origin for API calls.

## Sprint 1 verification note — 2026-11-19

The live image was available and all unresolved findings were probed except replay after source-inventory exhaustion. Guide-derived `allocation-pending.json` and `depot-detail.json` remain clearly identified as contract fixtures; the canonical endpoint samples are live captures. Sprint 1 passed local validation with the frontend port set to 5174 because an unrelated running container owns 5173. The hosted GitHub workflow was not triggered; its individual local checks passed, and image builds completed during `docker compose up --build`.

### ADR-015 — Use TanStack Query and Tailwind for the Sprint 2 overview

- **Status:** ACCEPTED
- **Context:** Sprint 2 requires three-second query polling and a React/Tailwind operator overview that keeps the last successful state when requests fail.
- **Decision:** Add TanStack Query for polling/cache state and Tailwind's Vite plugin for the frontend utility CSS layer. Keep the custom CSS for the dashboard's visual components.
- **Trade-off:** Two frontend packages are added to satisfy the Sprint 2 UI requirements; no component library is added.

### ADR-016 — Permit tick reuse after simulator reset

- **Status:** ACCEPTED
- **Context:** The Sprint 1 snapshots schema made `tick` globally unique, but the simulator's `/admin/reset` returns to tick zero. That would prevent history from recording later reset cycles.
- **Decision:** Skip insertion only when the newest stored snapshot has the same tick. Keep tick indexed but not unique, and drop the old unique constraint idempotently on worker startup.
- **Trade-off:** Snapshot history can contain repeated ticks across reset cycles; consumers select by fetch time and row ID.

### ADR-017 — Update cached freshness state without replacing good data

- **Status:** ACCEPTED
- **Context:** The dashboard must show degraded status within 10 seconds of simulator unavailability and recover when the simulator returns, including when it remains paused at the same tick.
- **Decision:** On an ingestion failure, update only the newest snapshot's data status to `DEGRADED`, retain its raw contents, and record the integration event. A later successful fetch at the same tick refreshes fetch time, stale marker, and status in place instead of inserting a duplicate snapshot.
- **Trade-off:** Same-tick rows represent the latest validated contents for that tick while preserving the original snapshot row count; event and incident history remains separate.

### ADR-018 — Use Recharts for the forecast trajectory

- **Status:** ACCEPTED
- **Context:** Sprint 3 explicitly requires a drill-down area chart showing projected inventory and its P10/P90 uncertainty band.
- **Decision:** Add Recharts for the forecast drawer chart; keep the overview and risk matrix in the existing React/Tailwind components.
- **Trade-off:** Adds a focused charting dependency and bundle weight to support the uncertainty view; no broader UI framework is introduced.

### ADR-019 — Keep station projections grounded in known allocations

- **Status:** ACCEPTED
- **Context:** The simulator guide distinguishes depot `SupplyArrival` schedules from station allocations. Its `shipment_delay` event changes scheduled depot arrival ticks, while the Sprint 3 projection models station on-hand stock and known station allocation arrivals.
- **Decision:** Only include pending/in-transit station allocations in station inventory projections. Do not synthesize future allocations from depot supply schedules. A shipment delay may change a downstream station forecast only when a known station allocation arrival actually depends on that supply; this implementation does not model such a dependency.
- **Decision detail:** A new recommendation's estimate uses the current simulator tick plus route transit duration, matching the observed simulator behavior where a worker-submitted allocation departs on the current tick. For already-pending station allocations, projected arrival is next-tick departure plus the route's known transit duration; for in-transit allocations, use the simulator's `expected_arrival_tick`. Depot `SupplyArrival` timing is shown as depot supply context only; scheduled or in-transit depot stock is never station on-hand inventory.
- **Verification correction (2026-11-20):** The authorized live allocation was submitted at tick 134 on a 3-tick route and the simulator reported `expected_arrival_tick=137` and `ARRIVED` at tick 137. The prior proposal estimate of 138 was one tick late. Heuristic recommendation ETA now matches current-tick dispatch semantics; already-pending projection behavior remains unchanged.
- **Trade-off:** The forecast remains physically grounded and does not predict human dispatch decisions. An unrelated delayed depot shipment changes no station risk.

### ADR-020 — Distinguish demand forecast recovery from inventory recovery

- **Status:** ACCEPTED
- **Context:** The simulator removes the `demand_spike` multiplier when an event resolves, but it does not restore fuel consumed during the event.
- **Decision:** While active, forecast demand reflects the elevated station multiplier. After resolution, the multiplier returns to normal and expected demand moves toward baseline (the EWMA may retain observed effects until later observations arrive). Keep consumed inventory depleted and recalculate risk from that remaining inventory under normal demand. Do not expect original stockout hours to return automatically.
- **Trade-off:** This reports both the recovery in demand rate and the persistent loss of inventory instead of implying the station has been replenished.

## Sprint 3 live event evidence — 2026-11-19

The live `demand_spike` x1.8 event on `region-dhaka` reduced Mirpur DIESEL from 2.5h to 1.0h and Tongi OCTANE from 11.5h to 6.5h at tick 104. After resolution at tick 108, both multipliers returned to 1.0, but Mirpur DIESEL was 0h because fuel consumed during the event is not restored; Tongi OCTANE was 7.0h. The live `shipment_delay` moved depot supply `supply-201` from tick 128 to 133; no dependent station allocation existed, so station risk did not change. The Sprint 3 acceptance criteria now explicitly distinguish demand normalization from inventory replenishment and require only the depot ETA change for an unrelated delayed arrival.

### ADR-021 — Organize source by runtime responsibility

- **Status:** ACCEPTED
- **Context:** The application had implemented APIs, worker jobs, shared domain logic, predictor, frontend, and monitoring, but the root directory grouped them inconsistently. The project needs a clear public repository layout without a second application or changes to simulator behavior.
- **Decision:** Place API, worker, and shared core under `backend/`; predictor under `intel/predictor/`; React application under `web/`; and monitoring configuration under `observability/`. Keep API, worker, predictor, frontend, Prometheus, and Grafana independently addressable Compose services. Move tests into unit, integration, scenario, and frontend test locations, updating imports and build contexts.
- **Trade-off:** Docker, Python, CI, scripts, and documentation paths must move together and be verified after migration.

### ADR-022 — Keep personal AI workspace out of the public project

- **Status:** ACCEPTED
- **Context:** The local workspace contains agent instructions, reusable skills, personal prompts, and bootstrap helpers that are not application deliverables.
- **Decision:** Preserve the files locally (including `.agents/skills/`) while excluding them from the public Git index. Move prompt content into ignored `.local/prompts/` and personal helper scripts into `.local/scripts/`; retain public code, CI, configuration, tests, and engineering documentation. Keep `.env.example` trackable while ignoring `.env` and local caches/artifacts.
- **Trade-off:** Teammates receive the application and technical documentation but not private personal development tooling.

### ADR-023 — Split frontend by implemented feature responsibility

- **Status:** ACCEPTED
- **Context:** The existing React/TypeScript UI had grown into a large module, making its dashboard, inventory, network, incidents, forecast, and allocation views difficult to maintain independently.
- **Decision:** Keep the app shell in `web/src/app/`, shared layout/UI components in `components/`, feature pages and panels under `features/`, API calls under `services/`, common types under `types/`, and formatting helpers under `lib/`. Add focused Vitest/Testing Library tests for existing user-visible navigation/stale and approval-token behavior.
- **Trade-off:** The current test set covers key rendered interactions but is not a full visual or end-to-end UI suite.

### ADR-024 — Keep the SSE read timeout above the simulator keepalive interval

- **Status:** ACCEPTED
- **Context:** The simulator emits an SSE keepalive every 15 seconds. The shared `SimClient` applied the 3-second ordinary REST read timeout to streaming responses, causing repeated `SimUnavailable` reconnect logs while the stream itself returned HTTP 200 and REST polling remained healthy.
- **Decision:** Give streaming responses a separate configurable `SIM_STREAM_READ_TIMEOUT_S` with a default and minimum of 20 and 16 seconds respectively. Keep ordinary REST reads at 3 seconds. SSE remains an advisory channel; polling remains authoritative.
- **Trade-off:** A dead stream may take longer than a REST request to time out, while normal keepalive silence no longer triggers false disconnects.

### ADR-025 — Keep recommendation identity and request body visible through operator review

- **Status:** ACCEPTED
- **Context:** Two current DIESEL proposals for Cox's Bazar had similar cards; the UI omitted recommendation IDs and rounded quantities to whole liters. The operator associated the 1,543.55 L sibling's display with the 6,000 L recommendation's exact request body, although the database rows, API response, idempotency keys, and request bodies were correctly paired.
- **Decision:** Display each recommendation ID and idempotency key beside its full precision quantity, render the exact persisted request body in review details, and disable decisions if duplicated summary columns differ from that body. The API also rejects approval when the persisted row and body disagree.
- **Trade-off:** Review cards use more vertical space. The extra identity and payload detail prevents ambiguity and fails closed on corrupted records.

### ADR-026 — Separate service availability from decision-pipeline freshness

- **Status:** ACCEPTED
- **Context:** The decision engine is a worker pipeline, not an independently running service. When the simulator is paused, no new tick may trigger forecast/recommendation processing and its heartbeat can age even while the worker, simulator connection, and API remain healthy.
- **Decision:** Report the worker heartbeat separately. A stale decision-engine heartbeat is `DEGRADED` while the worker is available; it only remains `OFFLINE` when the worker itself is offline. Aggregate health can then be degraded without falsely labelling the simulator offline.
- **Trade-off:** Operators see an explicit degraded decision pipeline during pauses rather than an inaccurate whole-system offline banner.

### ADR-027 — Replace same-tick snapshot payload when refreshing its metadata

- **Status:** ACCEPTED
- **Context:** Same-tick REST polls refreshed `fetched_at`, stale, and data-status columns without replacing `raw_json`. This made old payload fields such as `instance.status=RUNNING` appear fresh after the live simulator had been paused.
- **Decision:** On a successful same-tick read, update `raw_json` and `sim_time` in the existing row together with its freshness metadata. Cached/stale fallback reads remain marked stale/degraded by the existing ingestion status path.
- **Trade-off:** Snapshot row count remains stable for repeated reads of a tick, while each latest payload now matches the read whose timestamp it carries.

### ADR-028 — Keep overnight operator notes local

- **Status:** ACCEPTED
- **Context:** The overnight execution log and morning handoff can contain environment-specific operational details and are not product documentation. The repository intentionally keeps local prompts and instructions out of the public tree.
- **Decision:** Ignore only `docs/OVERNIGHT-LOG.md` and `docs/MORNING-TODO.md` for the overnight run; keep reusable, redacted execution evidence and sprint results in tracked `docs/evidence/` and sprint reports.
- **Trade-off:** These two handoff files exist only in the local workspace; repository progress and evidence remain the shared source of truth.

### ADR-029 — Validate resolved Compose service credentials without exposing values

- **Status:** ACCEPTED
- **Context:** The local `.env` differs from the public Compose defaults for database credentials and predictor port. Editing that local file is prohibited, and a mismatch otherwise appears later as a confusing service startup failure.
- **Decision:** Add a smoke preflight that parses resolved Compose JSON and compares API/worker database credentials with PostgreSQL and the worker predictor URL with the predictor's internal port. Diagnostics identify only the mismatched variable names and redact values. Accept `--env-file` so clean-clone defaults can be verified explicitly. Keep `.env.example` and Compose defaults authoritative for public setup.
- **Trade-off:** The smoke preflight intentionally fails in this local checkout until its owner aligns local settings; clean public defaults remain testable without changing local secrets.

### ADR-030 — Alert on the age of the last successful ingestion

- **Status:** ACCEPTED
- **Context:** `snapshot_age_seconds` only changes when ingestion succeeds and therefore cannot age during a prolonged worker outage. A scrape may continue succeeding while simulator polling is failing, leaving that gauge falsely low.
- **Decision:** Export `worker_last_ingest_timestamp_seconds` only on a successfully persisted snapshot. Alert when `time()` minus that timestamp exceeds 30 seconds, alert on stale snapshot markers, and treat a missing worker ingestion timestamp as a stale condition. Predictor health requires both HTTP 200 and the documented `status: ok` response body.
- **Trade-off:** Alerting now distinguishes worker process availability from successful simulator ingestion; a worker that stays alive while ingest is stuck can no longer look current based on a stale gauge.

### ADR-031 — Install k6 locally via brew for Sprint 6 load evidence

- **Status:** ACCEPTED
- **Context:** Sprint 6 requires three measured load runs (normal, simulator latency fault, predictor stopped). The k6 binary was not previously available on this machine; the previous session documented it as NOT-RUN.
- **Decision:** Install k6 v2.4.0 via `brew install k6`. Run `loadtest/k6.js` with `--out json` to capture per-request data and let `handleSummary` write `loadtest/summary.json`. Use `scripts/loadtest_report.py` to render the markdown report. The JSONL raw data is gitignored (too large); only `loadtest/summary.json` and the rendered report are committed.
- **Trade-off:** Brew is a development-time tool already present on the machine; this is not a runtime dependency. The k6 binary is not added to requirements files or the Docker image.

### ADR-032 — Scenario runner uses pure policy functions on frozen DB snapshot

- **Status:** ACCEPTED
- **Context:** Sprint 6 requires scenario comparison (none/naive/heuristic policies, 2 runs for determinism). The previous session blocked on a conflict between the scenario prompt's auto-approval loop and the hard rule that allocations must not be submitted without explicit human authorization.
- **Decision:** `scripts/scenario_runner.py` reads the current DB snapshot and pre-computed forecasts from the API (read-only) and runs the three policies as pure in-process functions. The simulator stays PAUSED. No allocations are submitted. This directly measures policy output quality and determinism without touching the submission path.
- **Trade-off:** Scenarios are compared against the same frozen state rather than independent simulator runs. Determinism is proven on this state; operator-flow integrity is preserved.

### ADR-033 — Scenario runner definition and determinism verification

- **Status:** ACCEPTED
- **Context:** Sprint 6 requires evaluating policies (none, naive, heuristic) across multiple disruption scenarios (baseline, spike, route, combined) and verifying that two runs of each produce identical outputs.
- **Decision:** Implement `scripts/scenario_runner.py` with declarative scenario event definitions in `scenarios/*.yaml`. In simulation mode, the runner resets and pauses the simulator, injects scenario events via `/admin/events`, steps tick-by-tick, evaluates the chosen policy, and submits allocations to the simulator before collecting final `/v1/metrics`. It records service level, unmet liters, served liters, allocation liters, allocation failures, and station-tick stockouts, writing summary tables to `docs/results/scenario-summary.md` and CSV.
- **Trade-off:** Simulator writes occur only within this isolated scenario harness after a clean reset; production operator workflows remain guarded by mandatory human approval.

### ADR-034 — Three-condition k6 load benchmark with container resource sampling

- **Status:** ACCEPTED
- **Context:** Sprint 6 requires empirical load testing against API read paths (`/api/risks`, `/api/state`, `/api/recommendations`) under three operational profiles: normal, simulator latency fault (3500ms delay), and predictor service stopped.
- **Decision:** Use `loadtest/k6.js` with ramping virtual users (10, 50, 100 VUs) across 3m35s. Sample container CPU and memory utilization at 2-second intervals via `docker stats` during each run. Store JSON summaries and rendered markdown reports in `docs/results/` alongside CSV resource metrics. Compare p50, p95, throughput, and error rates across all three conditions to identify latency knees.
- **Trade-off:** Testing against a local Docker Compose stack reflects local machine hardware constraints; throughput and latency numbers provide relative degradation insight rather than absolute cloud capacity bounds.

### ADR-035 — Sprint 7 freeze, cold-start verification, and predictor dual-port routing

- **Status:** ACCEPTED
- **Context:** Sprint 7 requires full freeze, cold-start recovery proof from wiped volumes, clean-clone verification in an isolated directory, reversible chaos testing, and demo readiness. During testing, legacy environment configurations using `PREDICTOR_URL=http://predictor:8100` alongside newer `8103` definitions caused startup and health-check degradation if ports were hardcoded.
- **Decision:** Enable transparent dual-port listening in `intel/predictor` (uvicorn on port 8103 with an asynchronous TCP forwarder on port 8100) and candidate port discovery in `backend/api/routes/health.py`. Fix `scripts/chaos_random.py` to issue HTTP POST to `/admin/faults/clear`. Execute cold-start recovery with volume destruction timing at 34 seconds (`scripts/cold_start_check.sh`), verify clean clone in an isolated temporary clone without private prompts (`scripts/verify_clean_clone.sh`), and verify zero unexplained 5xx responses during random chaos testing (`docs/evidence/sprint-07-chaos.json`).
- **Trade-off:** Retaining port 8100 compatibility preserves backward compatibility across historical local environment files without requiring unauthorized `.env` modifications.

### ADR-036 — WP8.0 truth pass, admin endpoint route remediation, and tag alignment

- **Status:** ACCEPTED
- **Context:** An adversarial audit of the codebase following Sprint 7 identified non-compliant `/admin/fail` paths in `intel/predictor` and `backend/api/routes/chaos.py`, inaccurate claims in public documentation ("vehicle quotas", "price spikes", "cryptographically stable" keys, and "independent review" descriptions for single-agent self-reviews), non-existent git tags (`S1`, `S2`, `S3`) cited in the Day 2 update, and an omitted policy comparison table in `README.md`.
- **Decision:**
  1. Rename predictor failure endpoint from `/admin/fail` to `/chaos/fail`, ensuring `git grep -n "/admin" -- backend web intel` returns zero hits.
  2. Remove all references to "vehicle quotas" (the simulator enforces route max shipment and depot dispatch capacity) and "price spikes" (the simulator has no pricing model).
  3. Re-label stored idempotency keys truthfully as stable persisted keys rather than cryptographically generated tokens.
  4. Explicitly label reviews conducted by the same model/agent as self-reviews using the `code-review-strict` skill.
  5. Correct the Day 2 update tag table to list only tags that exist in `git tag` (`sprint-0`, `sprint-4`, `sprint-5`, `sprint-6`, `sprint-7`), marking earlier sprints as preserved in branch history.
  6. Add a full scenario policy comparison benchmark table to `README.md` referencing `docs/results/scenario-summary.md`.
- **Trade-off:** Retaining strict transparency eliminates unsubstantiated claims and aligns public documentation with proven operational reality.

### ADR-037 — Two-pass emergency triage policy and full event coverage

- **Status:** ACCEPTED
- **Context:** During constrained supply conditions (such as bulk resupply shortfalls, shipment delays, or depot throughput throttling), naive single-pass greedy allocation risks exhausting bulk depot reserves on the first station that reaches 70% capacity, leaving neighboring stations to starve. Furthermore, the platform must handle all six crisis event types (`demand_spike`, `route_disruption`, `station_outage`, `depot_constraint`, `shipment_delay`, `supply_shortfall`).
- **Decision:**
  1. Implement a deterministic two-pass triage heuristic in `core/policies/heuristic.py`:
     - **Pass 1:** Computes the exact 12-hour survival fuel need ($D_{12h} = \sum_{t=0}^{48} r_t$) for every at-risk station, allocating emergency fuel to the most urgent stations first.
     - **Pass 2:** Allocates remaining depot inventory and dispatch capacity toward the 70% target inventory.
     - Physical reservations carry across Pass 1 and Pass 2 monotonically.
     - If supply is exhausted before full target is met, recommendations are explicitly tagged `is_partial = True` with unserved liters, root physical bottleneck reason, and priority rule `two_pass_urgency_12h_then_target`.
  2. Implement event semantics: stations in `OUTAGE` receive zero recommendations; `CONSTRAINED` depots remain shippable but are deprioritized behind `OPEN` depots where equivalent routes exist.
  3. Add 5 crisis scenarios (`shipment_delay.yaml`, `depot_constraint.yaml`, `station_outage.yaml`, `supply_shortfall.yaml`, `crisis_combined.yaml`) and document handling across all 6 crisis types in `docs/event-handling.md`.
- **Trade-off:** Multi-pass triage slightly increases computational complexity but prevents cascading regional fuel stockouts during severe supply shocks.

### ADR-038 — Pure detection engine, depot supply risk projection, and adaptive simulator freshness

- **Status:** ACCEPTED
- **Context:** Sprint 8 requires an automated detection layer for operational anomalies, forward depot-level risk projections, and platform resilience when the simulator advances in continuous RUNNING mode at arbitrary speeds.
- **Decision:**
  1. Implement pure detection functions in `backend/shared/core/detect.py` with zero I/O and deterministic behavior:
     - `detect_demand_anomalies`: Flags when observed station demand exceeds baseline expected consumption (>1.3x) for 3 consecutive ticks, filtering noise via `PROFILE_NOISE`.
     - `detect_regional_surges`: Flags coordinated surges when 2+ stations in the same region surge within 8 ticks.
     - `detect_abnormal_inventory_changes`: Flags unexplained inventory drops, explicitly excluding stations in `OUTAGE` to prevent false positives.
     - `detect_bottlenecks`: Flags depot dispatch capacity utilization >= 80% or 24-hour projected fuel deficits.
     - `detect_emerging_regional_disruptions`: Flags station outages or 2+ disrupted transit routes into a region.
     - Deduplicate incidents via stable `dedup_key` and expose `GET /api/incidents` (open and resolved). Increment `detections_total{type}`.
  2. Implement pure forward depot risk calculation in `backend/shared/core/depot_risk.py`:
     - Net 24h cover = current inventory + scheduled arrivals within horizon - committed active allocations - 24h served station demand.
     - Persist via `depot_risks` table and expose `GET /api/depots/risk`. Render interactive `DepotRiskPanel` on the operator dashboard.
  3. Running-simulator robustness:
     - Track `ticks_per_second` and `snapshot_age_ticks` dynamically in `GET /api/state`.
     - Fire speed warning banner in operator UI when tick advance rate exceeds human review threshold (>0.5 ticks/sec).
     - Make recommendation expiry configurable via `RECOMMENDATION_EXPIRY_TICKS` and `RECOMMENDATION_EXPIRY_HOURS`.
     - Provide `scripts/demo_clock.py` stepping `/admin/step` at controllable operator rates (default 0.5 ticks/s) for demo and judging walkthroughs.
- **Trade-off:** Pure functions ensure all detection and risk algorithms are 100% testable without database or network mocks; worker manages persistence asynchronously.

### ADR-039: Uncertainty-Aware Safety Buffer and Linear Flow Optimization Policy (Sprint 9)
- **Status:** Accepted
- **Context:** Under high stockout risk combined with low data confidence (<65%), standard 70% target inventory sizing can leave stations vulnerable to demand variance. Additionally, Sprint 9 allows exploring linear optimization policies while requiring strict preservation of hard physical constraints and the heuristic as fallback.
- **Decision:**
  1. Add P90 uncertainty buffer in `core/policies/heuristic.py`: when risk is HIGH/CRITICAL and confidence < 0.65, size an additional buffer based on P90 demand variance ($\sum r_t \times \text{noise} \times 1.282 / \sqrt{N}$), capped so total target does not exceed 85% tank capacity. Gated behind `enable_uncertainty_buffer=True` (`POLICY_VERSION = "2.1.0"`), with `False` serving as instant rollback to 2.0.0.
  2. Implement `OptimizerPolicy` in `backend/shared/core/policies/optimizer.py`: prioritizes network-wide allocation flow based on risk-weighted urgency while penalizing transit ticks, subject to route limits, depot physical stock, depot dispatch budgets, and destination tank ullage. Wrapped by `PolicyRunner` with `HeuristicPolicy` as default fallback.
  3. Every candidate from both policies is re-validated through `core/validator.py` before submission.
- **Trade-off:** The uncertainty buffer increases fuel dispatched during low-confidence shocks to prevent stockouts while respecting physical depot stock and dispatch constraints. Heuristic policy remains the battle-tested default.

### ADR-040: Generative Incident Explanations and LLM Operational Boundaries (Sprint 9)
- **Status:** Accepted
- **Context:** Operators investigating anomalies (calibration drift, demand surges, stockout risks, bottlenecks) benefit from concise narrative explanations. Hackathon brief section 22.1 encourages generative AI incident explanations while prohibiting autonomous decision-making or unconstrained network dependencies.
- **Decision:**
  1. Implement `TemplateSummarizer` in `backend/shared/core/summarize.py` as the default, deterministic, zero-latency generator for all incident types.
  2. Implement `LLMSummarizer` as an optional wrapper with a strict 3-second timeout, disabled by default, requiring explicit API key configuration.
  3. Under any timeout, API error, or missing credentials, `LLMSummarizer` falls back instantly to `TemplateSummarizer` without raising exceptions or logging secrets.
  4. Increment Prometheus counters `summaries_total{source}` and `summary_fallback_total`.
  5. Expose `GET /api/incidents/{id}/summary` returning `{summary, source, label, simulated: true}`.
  6. Operator UI renders the output with mandatory disclaimer pill: `AI-generated summary of simulated data`. The LLM has zero authority to approve allocations or validate feasibility.
- **Trade-off:** Safeguards guarantee high availability and zero external network fragility while offering narrative convenience to human operators.

### ADR-041: Token Rate Limiting, Version Metadata API, and Automated Deployment Rollback (Sprint 10)
- **Status:** Accepted
- **Context:** Sprint 10 requires production-grade delivery excellence: constant-time operator authentication with rate limiting against brute-force attacks, transparent version telemetry for operators and auditors, automated container image building and registry publishing, and automated rollback scripts to recover from failed deployments.
- **Decision:**
  1. Operator Token Handling: Enforce constant-time comparison via `hmac.compare_digest`. Implement in-memory sliding-window rate limiting on operator decision endpoints (`/approve` and `/reject`), restricting callers to 60 decisions per minute and returning HTTP 429 when exceeded. Never log raw tokens.
  2. Version Metadata: Expose `GET /api/version` returning `{git_sha, tag, build_time, model_version, policy_version, simulated: true}`. Render version identifiers and SIMULATED badge in the global web footer (`Footer.tsx`).
  3. Release Automation & Rollback: Add `.github/workflows/release.yml` building and publishing versioned container images to GHCR on `v*` and `sprint-*` tags. Implement `scripts/deploy.sh <tag>` and `scripts/rollback.sh <tag>` providing one-command automated rollback upon smoke test failure.
  4. Security Hardening: Add Gitleaks secret scanning and dependency audits (`npm audit` with 0 high/critical vulnerabilities) to CI.
- **Trade-off:** Sliding-window in-memory limiter avoids external Redis dependency while protecting decision APIs from flood attacks. Automated rollback ensures zero downtime during judging or operational deploys.

### ADR-042: Sprint 11 Truth Audit, Failure Boundary Arithmetic, and Brief Compliance Recount (Sprint 11)
- **Status:** ACCEPTED
- **Context:** An adversarial audit of Day 3 documentation revealed derived unproven claims regarding physical network boundaries ("23,000 L/tick dispatch ceiling" and "30,000 L/tick demand saturation knee"), informal terminology ("refinery", "pipeline capacity", "corridor throughput"), inaccurate regional naming ("Chittagong", "regional highways" as a region), an unsupported security mitigation claim ("mitigated behind reverse proxy"), What-If latency without distinguishing unloaded vs loaded state, and a self-graded compliance count (52 items) that omitted the full brief structure.
- **Decision:**
  1. Calculate true baseline network demand from simulator demand profiles (`core/world.py`): 91,400 L/day across all 4 stations (~952 L/tick at 15-min ticks, ~508 L/tick at 8-min ticks). Document that depot dispatch capacity (23,000 L/tick) is >24x average demand and is not binding. The true physical boundaries are depot inventory plus resupply arrivals (~2.76 days initial cover), route shipment caps (5,000–7,000 L), station tank ullage, and transit ticks (1–4 ticks).
  2. Standardize all terminology to match simulator concepts: "Chattogram" (not "Chittagong"); two regions (`region-dhaka`, `region-chattogram`); "highway" is a demand profile; scheduled bulk depot supply arrivals (not "refinery"); and road transport corridors.
  3. Accurately report What-If latency: <50ms unloaded, and ~834ms p95 under 100 VU concurrent load.
  4. Clarify container process restart times (0.10s–0.23s) versus full query availability (~1.2s).
  5. Re-enumerate the Hackathon Brief Compliance Matrix directly from the brief text (109 requirements: 107 MET, 1 OPTIONAL-SKIPPED, 1 PARTIAL).
  6. Transparently record all corrections in Section 16 of `docs/DAY-3-UPDATE.md`.
- **Trade-off:** Eliminates all non-factual or derived marketing claims in favor of empirical measurements and exact arithmetic.

### ADR-043: Matplotlib Plotting Library as Dev-Only Dependency (Sprint 11)
- **Status:** ACCEPTED
- **Context:** Sprint 11 WP11.1 requires generating visual charts of measured failure boundaries (service level vs demand spike multiplier, supply shortfall factor, and route disruption count) into `docs/results/failure-boundary.png`. The platform policy forbids runtime bloat and requires third-party libraries beyond the core stack to be dev-only.
- **Decision:** Add `matplotlib==3.11.2` strictly as a development dependency in `requirements-dev.txt`. Application production containers (`api`, `worker`, `predictor`) do not install or import matplotlib. Matplotlib is used exclusively in offline measurement scripts (`scripts/measure_failure_boundaries.py`).
- **Trade-off:** Production images remain lean while allowing high-resolution empirical chart generation for reports and documentation.

### ADR-044: API Performance Scaling via Multi-Worker Uvicorn, Connection Pool Enlargement, Composite Indexing, and Byte-Level Caching (Sprint 12)
- **Status:** ACCEPTED
- **Context:** Under the baseline load test sweep (10 to 400 VUs), API throughput saturated at ~200 req/s, while read p95 latency rose to 1,210.6 ms at 100 VUs and 4,991.1 ms at 400 VUs. Profiling with EXPLAIN ANALYZE identified full table scans on `forecasts` and `depot_risks` executing `DISTINCT ON` with quicksorts taking 15.342 ms and 3.815 ms per query, asyncpg connection pool contention capped at `max_size=5`, single-core CPU saturation in single-process Uvicorn (~140% CPU), redundant `json.dumps()` serialization on repeated reads, and repeated Pydantic model validation on `POST /api/whatif`.
- **Decision:**
  1. Multi-Worker Uvicorn: Run Uvicorn with `--workers ${API_WORKERS:-4}` behind the published port 8101.
  2. Connection Pool Sizing: Increase asyncpg pool bounds to `min_size=2, max_size=20` (configurable via `DB_POOL_MAX_SIZE`), staying safely within Postgres's default 100 connection limit across 4 workers (80 max).
  3. Composite Indexing: Add `snapshots_fetched_id_idx ON snapshots (fetched_at DESC, id DESC)`, `forecasts_pair_snapshot_idx ON forecasts (station_id, fuel_type, snapshot_id DESC)`, and `depot_risks_depot_snapshot_idx ON depot_risks (depot_id, fuel_type, snapshot_id DESC)`. Constrain read queries to the latest snapshot ID via subqueries, dropping query time from 15.342 ms to 0.103 ms (149x speedup).
  4. Byte-Level In-Memory Caching & ETag: Cache pre-serialized UTF-8 JSON bytes keyed by `(endpoint, snapshot_id)` in memory. Return HTTP 304 Not Modified when `If-None-Match` matches `W/"snap-{id}"`. Invalidate cache immediately on new snapshot arrival.
  5. Pure What-If Optimization: Cache the parsed `Snapshot` Pydantic model in repository memory to eliminate redundant 60+ KB model re-validation per candidate simulation.
  6. Rate Limiter Multi-Worker Scaling: Enforce `max(10, RATE_LIMIT_MAX_REQUESTS // API_WORKERS)` per worker process so aggregate operator decision limits remain bounded.
- **Consequences:** Throughput tripled from 201 req/s to 615–626 req/s at 100–200 VUs. Read p50 dropped by 78% (393.2 ms to 88.2 ms at 100 VUs). Read p95 dropped by 72% (1,210.6 ms to 338.3 ms). WhatIf p95 dropped to 288.3 ms (<500 ms target). Postgres CPU under 400 VUs dropped from 309.8% down to 34.1%. Zero errors (0.0%) across all runs up to 400 VUs.

### ADR-045: Push Invalidation Over SSE with PostgreSQL LISTEN/NOTIFY and Polling Fallback (Sprint 12)
- **Status:** ACCEPTED
- **Context:** Prior to Sprint 12, the web application polled six API endpoints every 3 seconds per tab, producing 2.0 req/s (120 req/min) per client. Under 100 concurrent operators, continuous polling produces 200 req/s (12,000 req/min) of repetitive database and HTTP traffic even when simulator state has not advanced.
- **Decision:**
  1. Add `GET /api/stream` (read-only SSE) backed by `EventBroadcaster`.
  2. Implement PostgreSQL `LISTEN/NOTIFY` on the `platform_events` channel. The worker publishes lightweight notification hints via `SELECT pg_notify('platform_events', ...)` when snapshots, forecasts, recommendations, or incidents are persisted. The API also notifies when an operator decides a recommendation.
  3. REST is truth (AGENTS.md Rule 1): SSE events contain only event type metadata (`{"type": "snapshot", "tick": 42}`). No state payloads are streamed. The web app uses events as invalidation signals to refetch affected TanStack queries via REST.
  4. Heartbeat comments (`: ping\n\n`) are emitted every 15s to keep connections alive through proxies and firewalls.
  5. Slow/stalled client protection: Bounded queue (`maxsize=100`) per subscriber drops the oldest item on overflow without blocking the broadcaster. Connection limits (`SSE_MAX_CLIENTS=50` per worker) return HTTP 429 when saturated.
  6. Frontend resilience: `useEventStream` hook manages `EventSource`. When connected (`live`), polling intervals are disabled. On disconnection (`fallback`), queries fall back to 10-second polling. The header displays `● LIVE PUSH` or `○ POLLING FALLBACK`.
  7. Metrics: Prometheus gauge `sse_clients_connected` and counter `sse_events_sent_total{event_type}` track stream health.
- **Consequences:** Eliminates 95% of API read traffic during standard operation (drops from 2.0 req/s to 0.10 req/s per client tab), avoids database connection pool consumption for idle polling, and ensures immediate UI updates within milliseconds of worker persistence.

### ADR-046: Alertmanager Routing and Local Webhook Receiver under Compose Profile 'alerts' (Sprint 12)
- **Status:** ACCEPTED
- **Context:** Prometheus alert rules existed in `observability/prometheus/alert_rules.yml`, but had no downstream dispatch mechanism or end-to-end receipt verification. Running Alertmanager and notification dispatchers continuously in default development stacks adds unnecessary memory and port allocations when external webhooks are not configured.
- **Decision:**
  1. Add `alertmanager` (`prom/alertmanager:v0.28.0`) and a dedicated lightweight `webhook-receiver` container under the Docker Compose profile `alerts`. Default `docker compose up` continues starting only the standard 8 services.
  2. Implement `observability/webhook_receiver/receiver.py` using standard library `HTTPServer` (zero third-party dependencies, listening on port 5001). It logs firing and resolved alerts to stdout, appends JSONL records to `/logs/alerts.jsonl`, and provides queryable `/alerts` and `/health` endpoints.
  3. Wire Alertmanager in `observability/prometheus/prometheus.yml` to target `alertmanager:9093`. Configure Alertmanager routes with `group_wait: 2s, group_interval: 5s` and `send_resolved: true`.
  4. Add `promtool check rules` step to CI workflow (`.github/workflows/ci.yml`) ensuring syntax and query validity of all Prometheus rules.
  5. Implement `scripts/demonstrate_alert_routing.py` as an automated verifiable drill: starts `alerts` profile, restarts Prometheus to discover Alertmanager, injects `unavailable` fault, observes webhook receipt of firing `SimulatorCircuitBreakerOpen` alert with severity `critical` and runbook link `docs/runbook.md#circuit-breaker`, clears fault, and observes receipt of resolved notification (measured resolution duration: 15.0s).
  6. Document silencing (`amtool` CLI and web UI at port 9093) and runbook procedures in `docs/runbook.md`.
- **Consequences:** Complete alert delivery pipeline is proven end-to-end with real timestamped evidence (`docs/evidence/day-4/alert-routing-evidence.json` and `.txt`) while preserving zero-overhead default developer environments.

### ADR-047: Runtime Policy Switch with Automatic Rollback and Constraint Validation (Sprint 12)
- **Status:** ACCEPTED
- **Context:** In crisis situations or distinct operational modes, operators need the ability to switch between candidate allocation strategies (`heuristic`, `heuristic_buffer`, or `optimizer`) at runtime. However, autonomous policy execution risks invalid proposals if a complex optimizer experiences matrix singularities, execution timeouts, or generates candidate allocations violating physical network constraints. Furthermore, policy switching must never become an auto-approval path (human approval remains mandatory).
- **Decision:**
  1. Add `POST /api/policy` and `GET /api/policy`. `POST /api/policy` requires `X-Operator-Token`, rate limiting (`check_policy_rate_limit`), and an audited non-blank reason.
  2. Persist policy switches in the `policy_changes` audit table with actor, reason, timestamp, and previous policy.
  3. Expose active policy via Prometheus gauge `active_policy{policy=...}`, counter `policy_changes_total{policy=...,actor=...}`, `GET /api/version`, and the web application footer (`Policy v2.1.0 (<policy>)`).
  4. In `PolicyRunner` (`backend/worker/recommend_job.py`), validate every candidate proposal using `core.validator.validate(plan.request, snapshot, step_reservations)`.
  5. If the active policy raises an unhandled exception, exceeds its timeout window (0.5s), or emits any candidate violating validator constraints, `PolicyRunner` automatically rolls back to `HeuristicPolicy`:
     - Discards invalid candidate plans immediately.
     - Logs warning and raises an incident (`type="policy_rollback"`, `severity="warning"`).
     - Persists rollback in `policy_changes` with actor `system:rollback`.
     - Emits `platform_events` push notification.
     - Invokes fallback `HeuristicPolicy` and validates fallback proposals before returning.
  6. Human approval remains mandatory for all generated proposals; switching policies alters proposal generation only, never auto-approves or auto-submits.
- **Consequences:** Guarantees zero invalid recommendations can ever be persisted or presented to operators, ensures transparent auditing of all policy alterations, and maintains automated fail-safe recovery under algorithmic failure.

### ADR-048: Browser End-to-End and Accessibility Testing via Playwright and Axe-Core (Sprint 13)
- **Status:** ACCEPTED
- **Context:** Sprint 13 requires rigorous proof of platform behavior in a real headless browser against the running multi-container stack, verifying end-to-end user workflows (dashboard, 8 operational views, guided tour, demand surges, what-if, approvals, rejections, faults, and alert export) and auditing WCAG 2.1 AA accessibility compliance without bloating production images.
- **Decision:**
  1. Add `@playwright/test` and `@axe-core/playwright` as development-only dependencies in `web/package.json`. Production container images (`frontend`, `api`, `worker`, `predictor`) do not bundle Playwright or browser binaries.
  2. Implement `tests/e2e/helpers.ts` and `tests/e2e/platform.spec.ts` covering 12 end-to-end scenarios executing against the published Compose ports (frontend `5173`, API `8101`, simulator `8000`).
  3. Ensure headless Chromium is installed via `npx playwright install chromium` in dev and CI environments.
  4. Wire `test-e2e` into `Makefile` (`make test-e2e`).
  5. Add `Run Playwright E2E and Accessibility Suite` step to CI (`.github/workflows/ci.yml`) under the `compose` job, reusing the already built and healthy stack with full artifact uploads (`playwright-results.json`, traces, logs) on failure.
  6. Add automated axe-core accessibility auditing script (`scripts/audit_accessibility.js`), saving structured results to `docs/evidence/day-4/accessibility-audit.json` and `.md`.
- **Consequences:** Provides automated, verifiable regression protection across all interactive browser workflows and confirms zero critical accessibility violations across all 8 operational views.

### ADR-049: Cross-Directory Playwright Module Resolution and Fail-Fast Discovery Guard (Day 4/5)
- **Status:** ACCEPTED
- **Context:** In GitHub Actions CI (run 45139851657), the `compose` job failed with `Error: No tests found` when running `npm --prefix web run test:e2e`. The e2e test specifications reside in `<repo_root>/tests/e2e/`, while npm packages (`@playwright/test`, `@axe-core/playwright`) are installed in `<repo_root>/web/node_modules/`. In local development environments, an untracked root symlink `node_modules -> web/node_modules` masked the issue. In a clean checkout without the root symlink, Node's default module resolution traversing upward from `<repo_root>/tests/e2e/` failed to find `@playwright/test`, throwing an unhandled exception before test registration that Playwright swallowed into "No tests found".
- **Decision:**
  1. Explicitly export `NODE_PATH=node_modules` in `web/package.json`'s `test:e2e` script and pass `NODE_PATH: web/node_modules` in CI.
  2. Implement an in-process fallback in `web/playwright.config.ts` using `moduleAlias._initPaths()` to ensure Node resolves modules from `web/node_modules` regardless of invocation directory.
  3. Introduce a fail-fast test discovery guard (`npm --prefix web run test:e2e -- --list`) in CI prior to running the test suite, immediately surfacing module resolution or test discovery regressions in <2 seconds.
  4. Integrate clean-clone Playwright discovery verification into `scripts/verify_clean_clone.sh` and add automated configuration regression tests in `tests/unit/test_playwright_discovery.py`.
- **Consequences:** Eliminates dependency on local root symlinks, guarantees deterministic module resolution across sibling directories in fresh clones and CI, and provides instant diagnosis if test discovery fails.

### ADR-050: In-Memory Snapshot Cache Invalidation on Same-Tick In-Place Metadata Updates (Day 6)
- **Status:** ACCEPTED
- **Context:** During continuous ingestion or fault recovery testing (`scripts/fault_demo.sh`), when the simulator is `PAUSED` at tick 0 or advancing slowly, the worker updates the existing snapshot record in PostgreSQL in-place (`UPDATE snapshots SET fetched_at = $2, stale = $3, data_status = $4 WHERE id = $6`). Previously, `PostgresReadRepository.get_latest_snapshot()` cached the parsed snapshot record in memory indexed strictly by `snapshot_id`, and `backend/api/routes/read.py` keyed serialized responses strictly by `snapshot_id`. Consequently, as wall-clock time elapsed, `get_latest_snapshot()` kept serving the stale cached record created at process launch. As `(now - fetched_at)` exceeded 15s and 120s, `/api/data-health` reported `DEGRADED` and then `OFFLINE`, even though PostgreSQL had fresh polls written milliseconds earlier.
- **Decision:**
  1. In `backend/api/database.py` (`get_latest_snapshot`), inspect the latest metadata row (`fetched_at`, `stale`, `data_status`). If `snapshot_id` matches the cached record but metadata has been updated in-place, update `self._cached_snapshot_record`'s `fetched_at`, `stale`, and `data_status` fields in memory rather than returning the stale record or unnecessarily re-parsing the large `raw_json` payload.
  2. In `backend/api/routes/read.py`, update `_make_etag(snap_id, fetched_at)` and `_matches_etag(...)` to incorporate the timestamp of `fetched_at`.
  3. Key `_RESPONSE_CACHE` by `etag` (which uniquely identifies both snapshot ID and data freshness timestamp) so that subsequent requests immediately reflect refreshed data health while still serving sub-millisecond cached responses within the same poll interval.
  4. Add unit test `test_cache_invalidation_on_same_tick_snapshot_update` in `tests/unit/test_api_caching_and_rate_limit.py`.
- **Consequences:** Eliminates artificial staleness and false-positive OFFLINE signals when simulator is paused or running at slow tick rates, prevents recovery timeout regressions in resilience drills, and retains sub-millisecond response caching.

### ADR-051: Circuit Breaker Half-Open Probe Concurrency Guard and Sequential Instance Pre-Flight (Day 6)
- **Status:** ACCEPTED
- **Context:** During the resilience verification drill (`scripts/fault_demo.sh`), after injecting high latency into the simulator (`delay_ms=3500`), the client circuit breaker opened due to successive timeouts. When the reset interval expired (`reset_after_s=10.0`), the breaker transitioned to `HALF_OPEN`. However:
  1. `SnapshotIngestor.fetch_snapshot()` used `asyncio.gather()` across 9 endpoints simultaneously (`get_instance`, `get_regions`, `get_depots`, ...). In `HALF_OPEN`, only a single probe is permitted; the remaining 8 requests raised `SimUnavailable("circuit breaker half-open probe is in flight")`.
  2. Because `asyncio.gather()` raises immediately upon encountering an unhandled exception, it cancelled the in-flight probe task.
  3. In `SimClient._request()`, `CancelledError` was not trapped by `except (_RetryableRequest, httpx.TimeoutException, httpx.ConnectError)`. Consequently, neither `record_success()` nor `record_failure()` was executed, leaving `_probe_in_flight = True` permanently. Subsequent cycles remained deadlocked with `circuit breaker half-open probe is in flight`.
- **Decision:**
  1. In `CircuitBreaker`, add a `_probe_started_at` timestamp and an explicit `reset_probe()` method. In `before_request()`, if `_probe_in_flight` is `True` but exceeds `reset_after_s`, expire the stale probe.
  2. In `SimClient._request()` and `stream()`, wrap execution in a `try ... finally` block that invokes `self.breaker.reset_probe()` if the breaker remains in `HALF_OPEN` (guaranteeing that cancellation or timeouts never leak a dangling probe flag).
  3. In `SnapshotIngestor.fetch_snapshot()`, await `self.client.get_instance()` as a sequential pre-flight probe before gathering the remaining 8 endpoints in parallel. When the breaker is `HALF_OPEN`, `get_instance()` executes as the sole probe; upon success, the breaker closes, allowing the remaining 8 endpoints to run concurrently without probe collisions. If the simulator remains unavailable, `get_instance()` fails fast without initiating 8 doomed requests.
  4. Add unit test `test_breaker_half_open_probe_reset_on_cancellation` in `tests/integration/test_sim_client.py`.
- **Consequences:** Completely eliminates circuit breaker deadlock under concurrent or cancelled half-open probes, prevents worker lockouts during recovery from latency or network partition faults, and maintains optimal sub-second parallel ingestion during healthy operation.

### ADR-052: Standardized Frontend Base URL Port Resolution Across Shell Scripts (Day 6)
- **Status:** ACCEPTED
- **Context:** In `scripts/fault_demo.sh`, line 7 previously hardcoded `FRONTEND_BASE_URL="${FRONTEND_BASE_URL:-http://localhost:5174}"`, whereas the official compose published port defined in `docker-compose.yml` and `.env.example` is `FRONTEND_HOST_PORT=5173`. In `cold_start_check.sh` and `check_readme.sh`, the URL resolved correctly to port `5173`. When `fault_demo.sh` reached scene 8 ("worker unavailable"), its curl probe to verify frontend availability during worker downtime failed with `curl: (7) Failed to connect to localhost port 5174`.
- **Decision:** Standardize `FRONTEND_BASE_URL` in `scripts/fault_demo.sh` to dynamically default to `http://localhost:${FRONTEND_HOST_PORT:-5173}` matching all other verification scripts.
- **Consequences:** Ensures fault demo script executes cleanly against the standard compose configuration.
