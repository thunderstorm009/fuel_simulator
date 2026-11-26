# Judge Questions & Technical Answers (Empirical Defense)

This document provides evidence-backed, empirical answers to the technical, algorithmic, and architectural questions most frequently posed by hackathon judges and domain experts evaluating the **Fuel Supply Intelligence & Resilience Platform**.

---

### 1. Why start with a heuristic instead of a full MIP/RL optimizer?
**Answer:**
The two-pass heuristic is deterministic, executes in under **5 milliseconds**, provides 100% transparent constraint explanations for human operators, and guarantees zero physical constraint violations. In emergency logistics, an operator facing acute fuel shortages cannot wait 30 seconds for an MILP solver to converge or trust a stochastic reinforcement learning agent with unpredictable boundary behavior.

In Sprint 9, we implemented an optional Linear Flow Optimization policy (`LinearFlowOptimizer`) alongside an uncertainty-aware buffer policy (`SafetyBufferPolicy`). In our 60-scenario randomized crisis sweep (240 live simulation runs, 46,080 ticks; `docs/results/scenario-sweep.md`), the heuristic policy achieved **97.93% average SLA** across compound crises (winning 15, tying 44, and losing only 1 match against naive reordering), proving that constrained triage heuristics outperform naive algorithms while preserving immediate explainability. Furthermore, our Sprint 12 runtime policy switch (`POST /api/policy`) allows operators to switch to LP or Buffer policies on demand, with an automatic circuit breaker that rolls back to heuristic within 500ms if any violation occurs.

---

### 2. How does demand forecasting work?
**Answer:**
The predictive pipeline combines three pure mathematical stages:
1. **Diurnal Baseline Modeling:** Hourly demand curves from `core/world.py` reflect real-world commuter, commercial, and highway traffic patterns.
2. **EWMA Ratio Tracking:** An Exponentially Weighted Moving Average ($\alpha = 0.3$, clamped to $[0.5, 2.0]$) adapts to persistent consumption drift.
3. **Event-Aware Calibration (v1.2.0):** In Event-Aware model v1.2.0, when known crisis events occur (e.g. 2.0x or 2.5x regional demand spikes), historical expected demand immediately factors the active event multiplier. This eliminated historical calibration lag completely: adaptation time dropped from **7–19 ticks down to 0 ticks** (instantaneous convergence).
4. **Vectorized Monte Carlo:** 300 pseudo-random paths (seeded with snapshot tick and station ID for deterministic replay) project 24-hour stockout probability and P10/P50/P90 confidence bands.

In our 3,152-tick historical backtest (`docs/results/backtest-summary.md`), 24-hour forecast MAPE was **2.10%** outside events, **3.88%** during disruption events, and **2.71%** overall, with a Brier calibration score of **0.1558**.

---

### 3. Does the forecasting or intelligence layer make allocation decisions or submit to the simulator?
**Answer:**
**Strictly NO.** Pure core functions (`core.forecast`, `core.risk`, `core.policies`, `core.validator`) have **zero I/O capabilities** (AGENTS.md Rule 4). They calculate numbers and return immutable dataclasses.
The API cannot submit allocations; it only records operator approval intent in PostgreSQL.
The worker executor is the **only component in the entire platform authorized to call `POST /v1/allocations`** (AGENTS.md Rule 5 & 6). Furthermore, before submitting, the worker re-fetches a fresh, non-stale snapshot and re-validates all five physical constraints.

---

### 4. What happens if the simulator returns stale data (`X-Simulator-Stale: true`)?
**Answer:**
The worker checks `X-Simulator-Stale` on every HTTP response (and monitors wall-clock snapshot age $> 30\text{s}$). If stale:
1. Data status is immediately downgraded to `DEGRADED`.
2. The UI header and cards display prominent amber warnings: `STALE DATA (Age: Xs)`.
3. Forecast confidence is capped below 0.4.
4. **All allocation submissions are strictly blocked** (Rule 10), preventing the system from dispatching real fuel trucks based on obsolete state.

---

### 5. What happens if the simulator is temporarily unavailable (HTTP 503 or network drop)?
**Answer:**
The typed client `SimClient` enforces bounded retries with exponential backoff and jitter. A circuit breaker trips after 5 consecutive failures, entering an `OPEN` state with a 10-second cooldown.
During this window:
- The API continues serving the latest valid snapshot and forecasts from PostgreSQL with sub-millisecond latency.
- The web interface displays a `DEGRADED` banner with the timestamp of the last authoritative read.
- Never retry 409 Conflict or 422 Unprocessable Entity (AGENTS.md Rule 3).

---

### 6. Why is SSE not the single source of truth?
**Answer:**
The simulator's Server-Sent Events stream (`GET /v1/events`) does not support message offset replay or historical resume after a connection drop (AGENTS.md Rule 1). Therefore, treating SSE as truth risks dropping critical events.
In our platform:
- **REST is truth.**
- SSE events are treated purely as **advisory invalidation hints** that prompt an immediate REST refetch.
- Upon every SSE reconnect, the worker unconditionally performs a full REST refetch.

---

### 7. Can scheduled or in-transit depot replenishments count as station inventory?
**Answer:**
**Never.** Counting unconfirmed incoming shipments as on-hand inventory is a primary cause of catastrophic stockouts in supply chain management (AGENTS.md Rule 7).
Station inventory projections count strictly on-hand tank stock plus verified, un-arrived station allocations at their specific expected arrival tick ($t_{\text{current}} + \text{transit\_ticks}$). Scheduled depot replenishments from refineries remain at the depot until dispatched.

---

### 8. How are duplicate allocations prevented under network retries?
**Answer:**
Every proposed recommendation generates an immutable UUID idempotency key (`rec-<uuid>`) stored alongside the exact request body in PostgreSQL.
This key is placed in the `idempotency_key` field of the `POST /v1/allocations` JSON body (AGENTS.md Rule 5).
If a network timeout occurs after the simulator created the allocation, subsequent retries resend the **identical key and body**. The simulator recognizes the key and returns the existing allocation without creating a duplicate. Reusing an existing key with a different request body produces a 409 Conflict, which our client treats as an unrecoverable invariant error.

---

### 9. What happens if an allocation submission times out?
**Answer:**
The worker preserves the recommendation in `SUBMITTED` state in PostgreSQL with its permanent idempotency key. On the next ingestion cycle, the worker inspects active transit shipments:
- If the allocation appears in simulator state, it transitions to `ARRIVED` when delivered.
- If the allocation is absent, the executor retries the exact same body with the exact same idempotency key.

---

### 10. Can an idempotency key be reused after cancellation or rejection?
**Answer:**
**No.** Idempotency keys are permanent and immutable. Once assigned to a recommendation, they are never deleted, reassigned, or mutated. If an operator rejects a recommendation, that key is retired forever. If the engine later generates a new recommendation for the same station, it receives a new, distinct UUID key.

---

### 11. Why is the predictor an independent microservice?
**Answer:**
The predictor runs in its own container (`intel/predictor` on port 8103). This architectural separation enables:
- Independent scaling of CPU-intensive Monte Carlo simulations.
- Isolated Python dependencies.
- Resilience testing: we can stop or crash the predictor container, and the worker gracefully switches to its local diurnal baseline fallback with zero 5xx errors and zero system downtime.

---

### 12. What does baseline fallback mean in practice?
**Answer:**
When the predictor service fails, times out (1.5s timeout), or trips its circuit breaker (5 failures), the worker calls `core.forecast.generate_forecast` locally.
It computes the diurnal profile with EWMA ratio calibration, caps confidence at **0.40**, marks `needs_review: true`, logs a structured warning, records an incident in PostgreSQL, and increments Prometheus counter `predictor_fallbacks_total{reason="service_error"}`.

---

### 13. How is scenario determinism proven?
**Answer:**
`scripts/scenario_runner.py` evaluates all 4 disruption scenarios (`baseline`, `spike`, `route`, `combined`) across 3 policies (`none`, `naive`, `heuristic`) twice in succession (24 total simulation runs).
The delta in service level (%) and stockout count between Run 1 and Run 2 is **0.0000 across every single metric** (`docs/results/scenario-summary.md`), proving 100% deterministic reproducibility.

---

### 14. What load can the platform handle, and how was it optimized?
**Answer:**
In Sprint 12, we profiled the API under concurrent k6 load. Initial baseline saturated at 201 req/s with 1,210ms read latency at 100 VUs, caused by sequential database scans and single-worker Uvicorn limits.
We introduced:
1. 4 Uvicorn worker processes.
2. Connection pool expanded to 20 connections.
3. 3 composite database indexes (reducing query times from 15.3ms to 0.103ms — a 149x speedup).
4. Sub-millisecond pre-serialized byte caching.
5. HTTP ETag / 304 Not Modified support.

**Optimized Results (`docs/loadtest.md`):**
- Throughput tripled to **625.8 requests/second** at 200 Virtual Users.
- Read latency dropped by 72% (**p95: 338.3 ms** at 200 VUs; p50: 88.2 ms).
- Interactive What-If simulation latency dropped by 67% (**p95: 288.3 ms**, comfortably beating the 500 ms target).
- PostgreSQL CPU dropped from 309.8% down to 34.1%.
- Error rate: **0.00% across all load profiles**.

---

### 15. What are the platform's measured physical failure boundaries?
**Answer:**
Total daily baseline demand across all 4 stations is **91,400 L/day** (~952 L per 15-minute tick average). Depots provide **23,000 L/tick** combined dispatch capacity (>24x average demand), meaning depot dispatch capacity is almost never the bottleneck.
Stress-testing sweeps across 192 ticks (`docs/results/failure-boundary.md`) established the real boundaries:
- **99% SLA Boundary:** Heuristic sustains 99% SLA up to **2.43x** demand surge (99.91% at 2.2x), whereas naive drops below 99% at **1.96x** (97.48% at 2.2x).
- **95% Critical Boundary:** Heuristic sustains 95% SLA up to **2.80x** demand surge (98.30% at 2.6x), whereas naive breaches 95% at **2.55x** (94.66% at 2.6x).
- **90% Collapse Boundary:** Heuristic preserves **>90%** service level across the entire range up to **>3.0x** (91.66% at 3.0x), whereas naive breaches 90% at **2.95x** (89.28% at 3.0x).
- **True Binding Physical Constraints:** Route truck capacity limits (5,000–7,000 L/truck) under spikes >2.2x, corridor transit delays (1–4 ticks), and depot inventory exhaustion when upstream pipeline supply drops below 0.40.

---

### 16. What was the outcome of the 60-scenario randomized crisis sweep, and where does the heuristic lose?
**Answer:**
Across 60 randomized crisis scenarios (240 live simulation runs, 46,080 ticks; `docs/results/scenario-sweep.md`) evaluated on the live simulator:
- **Heuristic Mean SLA:** **97.93%** (Median: 100.0%, Worst: 86.27%, Mean unmet: 4,798 L).
- **Naive Mean SLA:** **97.14%** (Median: 100.0%, Worst: 86.27%, Mean unmet: 7,324 L).
- **Do Nothing Mean SLA:** **40.40%** (Median: 45.58%, Worst: 22.76%, Mean unmet: 137,340 L).
- **Head-to-Head vs Naive:** **15 Wins / 44 Ties / 1 Loss**.
- **Bootstrap 95% Confidence Interval for Improvement vs Naive:** **+0.79% [0.41%, 1.27%]** SLA.
- **Hold-Out Compound Disasters (10 unseen scenarios):** Heuristic **96.26%** vs Naive **92.57%** (9 Wins / 0 Ties / 1 Loss).
- **Honest Loss Disclosure:** Exactly 1 loss out of 60 scenarios occurred in `holdout_08` (Heuristic 99.86% vs Naive 99.95%, a -0.08% delta) due to compound corridor transit bottleneck timing where a 4-tick transit delay overlapped an unannounced secondary surge.

---

### 17. How fast can the system recover from catastrophic database failure?
**Answer:**
In our Sprint 12 automated backup and restore drill (`python3 scripts/drill_backup_restore.py`; report: `docs/results/backup-restore-drill.json`):
- **Recovery Time Objective (RTO):** **2.93 seconds** (target $< 15\text{s}$).
- **Data Preservation:** **100.0% row preservation** across all snapshots (419), forecasts (5,004), recommendations (158), decisions (1), depot risks (1,572), and incidents (387).
- **Zero Duplicate Submissions:** Post-restore executor idempotency test confirmed zero duplicate allocations submitted to the simulator.

---

### 18. How does Server-Sent Events (SSE) push invalidation improve performance?
**Answer:**
In Sprint 12, we introduced `GET /api/stream` using PostgreSQL `LISTEN/NOTIFY` on channel `platform_events`.
When the worker ingests a snapshot or creates recommendations, it notifies PostgreSQL, which pushes invalidation hints to connected web clients.
- In validation testing (`docs/loadtest.md`), push invalidation eliminated redundant polling, reducing API read traffic by **95%** during steady-state operation.
- If the stream disconnects, the React client automatically falls back to 10-second polling until reconnection.

---

### 19. What safeguards govern generative AI incident explanations?
**Answer:**
`backend/shared/core/summarize.py` uses a deterministic `TemplateSummarizer` by default, with an optional `LLMSummarizer` wrapper configured with a strict 3-second timeout and zero logging of secrets. Any error, timeout, or missing API key falls back instantly to the template. The LLM has zero authority to approve allocations or determine feasibility, and all outputs carry a mandatory operator disclaimer: `"AI-generated summary of simulated data"`.

---

### 20. How is usability and accessibility verified?
**Answer:**
In Sprint 13, we integrated Playwright and `@axe-core/playwright`:
- **12 comprehensive end-to-end browser tests** run in CI (`make test-e2e`), passing in **31.7s**.
- Automated accessibility audits across all 8 operational views achieved **0 critical WCAG 2.1 AA violations**, with scores of 90/100 on subpages and 80/100 on overview (`docs/evidence/day-4/accessibility-audit.md`).
- Fully accessible keyboard navigation, visible focus rings, color-contrast compliant badges, and an interactive Guided Tour.
