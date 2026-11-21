# Decision log (ADR style). Add an entry when a decision is made. Template: docs/templates/adr.md

Statuses: PROPOSED, ACCEPTED, SUPERSEDED.

| ID | Decision | Status | Sprint |
|---|---|---|---|
| ADR-001 | REST is truth; SSE is only a hint to refetch | PROPOSED | 1 |
| ADR-002 | Worker owns simulator I/O; API reads the database only | PROPOSED | 1 |
| ADR-003 | Heuristic allocation first; optimizer only if time remains | PROPOSED | 1 |
| ADR-004 | Monte Carlo for stockout uncertainty | PROPOSED | 3 |
| ADR-005 | Outbox-style executor: approve records intent, executor re-validates and submits | ACCEPTED | 4 |
| ADR-006 | Idempotency key rec-<uuid>, stored, reused only for the identical body | ACCEPTED | 4 |
| ADR-007 | Predictor as its own container with baseline fallback | PROPOSED | 5 |
| ADR-008 | No Kubernetes or RL; Docker Compose only | PROPOSED | 1 |
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
| ADR-036 | WP8.0 truth pass, admin endpoint route remediation, and tag alignment | ACCEPTED | 8 |

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
