# Assumptions and limitations

## Operational and architectural assumptions

- **Simulation environment:** The simulator, fuel stations, depots, transit trucks, and all displayed inventories, forecasts, decisions, and dispatches are simulated.
- **Authoritative state:** REST endpoints (`/v1/snapshot`, `/v1/instance`, `/v1/allocations`) are the single source of truth. SSE stream events serve strictly as advisory reconnection and invalidation hints; SSE reconnect does not replay missed messages and triggers an immediate REST refetch.
- **Asynchronous pipeline ownership:** API read paths query PostgreSQL exclusively. The background worker owns all simulator I/O, scheduled snapshot polling, heartbeat emission, and the sole simulator allocation write path (`POST /v1/allocations`).
- **Strict approval boundary:** Live allocation submissions require a persisted human operator approval (`OPERATOR_TOKEN`), an unexpired recommendation, a fresh non-stale snapshot, and a pre-submission constraint revalidation pass. No autonomous or unapproved dispatches are permitted in production paths.
- **Intelligence and risk modeling:** Demand forecasts combine empirical consumption rates with daily periodicity models. Stockout risk assessments project station inventory against safe operational thresholds. When the remote predictor fails or circuit-breaks, the worker falls back to local deterministic baseline heuristics, capping confidence at 0.4 and alerting the operator.
- **Inventory accounting:** Projections strictly count on-hand station stock and verified, in-transit station-bound shipments matching confirmed ETA ticks. Depot stock and unassigned supply are never counted as station inventory.
- **Deployment context:** Docker Compose serves as the reference deployment harness. No multi-tenant external authorization, distributed cloud key vaults, or cloud infrastructure management is included.

## Measured operational characteristics (Sprints 1–7)

- **Sprint 4 Live Approval:** Live operator approval workflow verified at tick 134, arriving at tick 137 (`ARRIVED`), with exact-key replay returning identical allocation ID 1 (`docs/evidence/sprint-04-overnight.md`).
- **Sprint 5 Resilience:** Live resilience matrix confirmed against all 5 simulator faults (unavailable, latency, error_rate, stale_data, stream_disconnect), malformed JSON payloads, worker stoppage, and predictor outages (`docs/evidence/sprint-05-fault-demo-accepted.txt`). Prometheus alerting rules and Grafana dashboards provisioned and validated live (`docs/evidence/sprint-05-worker-alert-check.txt`).
- **Sprint 6 Scenario Benchmarks:** Deterministic scenario runner evaluated 4 disruption scenarios (`scenarios/*.yaml`) across 3 policies (`none`, `naive`, `heuristic`) over 24 runs with 100% determinism (delta 0.0000 on every pair). Heuristic allocated 15,238 liters across scenarios with 0 failures (`docs/results/scenario-summary.md`).
- **Sprint 6 Load Benchmarks:** Three k6 load benchmark profiles executed (normal, simulator latency fault, predictor stopped) with 205,000+ total requests and 0% error rate. Performance knee identified at 100 virtual users where p95 latency exceeds 500ms (`docs/loadtest.md`).
- **Sprint 7 Cold-Start Recovery:** Cold start from clean state with volume destruction measured at 34 seconds (`scripts/cold_start_check.sh`, `docs/evidence/sprint-07-cold-start.txt`).
- **Sprint 7 Clean-Clone Verification:** Clean clone in isolated temporary directory without private development files passed all 141 Python unit/integration tests, 6 frontend tests, and mechanical gates (`docs/evidence/clean-clone-check.txt`).
- **Sprint 7 Chaos Testing:** Reversible random fault injection completed with zero unexplained 5xx API errors and automatic system recovery (`docs/evidence/sprint-07-chaos.json`).

## Known system boundaries

- **Single depot topology:** The platform models supply from a primary depot to regional retail stations; dynamic multi-depot inter-depot transfers and vehicle routing heuristics are out of scope.
- **Human operator latency:** Because dispatches require human confirmation, rapid unexpected multi-station cascades require operator responsiveness. Recommendation ranking presents the highest-urgency stations first to minimize review latency.
