# Day 7 Live Judging Demonstration Rehearsals

**Generated:** 2026-11-24
**Harness:** `scripts/demo_director.py` (live execution against running multi-container stack)
**Storyline:** 10-Minute Operational Loop (Observe -> Detect -> Predict -> Decide -> Simulate -> Approve -> Act -> Monitor -> Recover)
**Preflight Target:** `make preflight` (`scripts/preflight_judging.sh`) -> `>>> PREFLIGHT VERDICT: GO <<<`

---

## 1. Rehearsal Execution Log

| Rehearsal | Timestamp (UTC) | Mode | Duration | Phased Steps Verified | Output Evidence Path | Result |
|:---:|:---:|:---:|:---:|---|---|:---:|
| **Run 1** | `2026-11-24T07:26:48Z` | Live Stack | 2.0s (@ 10.0x speed) | Phase 0–5: Baseline, Surge, What-If, Approval, Fault, Recovery | [`demo-rehearsal-1.json`](demo-rehearsal-1.json) | **PASS** |
| **Run 2** | `2026-11-24T07:26:50Z` | Live Stack | 1.9s (@ 10.0x speed) | Phase 0–5: Baseline, Surge, What-If, Approval, Fault, Recovery | [`demo-rehearsal-2.json`](demo-rehearsal-2.json) | **PASS** |
| **Run 3** | `2026-11-24T07:26:52Z` | Live Stack | 1.9s (@ 10.0x speed) | Phase 0–5: Baseline, Surge, What-If, Approval, Fault, Recovery | [`demo-rehearsal-3.json`](demo-rehearsal-3.json) | **PASS** |

---

## 2. Operational Phasing & Presenter Cues

### Phase 0: Baseline State & HUD Observation (0:00 – 1:30)
- **Harness Action:** Pauses simulator at tick 0, checks live container health across all 8 services.
- **Presenter Cue:** Highlight header HUD: Tick counter, 1.0x simulator speed, mandatory `SIMULATED` pill, and `● LIVE PUSH` streaming telemetry indicator.
- **Key Metric:** Network aggregate demand of 91,400 L/day across Mirpur, Uttara, Dhanmondi, and Gulshan.

### Phase 1: Demand Surge Crisis Injection (1:30 – 3:00)
- **Harness Action:** Injects 2.5x demand surge on `station-mirpur` for 10 ticks via simulator admin endpoint.
- **Presenter Cue:** Navigate to *Stockout Risk Matrix*. Show immediate drop in hours to stockout from 18.4h to 4.2h and widening P10/P90 Monte Carlo probability fan.
- **Key Metric:** Anomaly detector emits `demand_surge` incident (`severity: high`, Brier score 0.1558).

### Phase 2: Decision & What-If Counterfactual (3:00 – 4:30)
- **Harness Action:** Generates candidate proposal via pure `HeuristicPolicy` with physical constraint validator.
- **Presenter Cue:** Navigate to *Recommendations*. Click *Review Explanation*. Drag the *What-If Simulator* volume slider: demonstrate instant in-memory counterfactual stockout runway extension from 4.2h to 14.8h.
- **Key Metric:** Sub-20ms What-If response latency; all 5 hard physical constraints verified green.

### Phase 3: Human Approval & Execution Lifecycle (4:30 – 6:00)
- **Harness Action:** Fills operator name `Senior Dispatcher Rahat` and token `OPERATOR_TOKEN`. Submits decision.
- **Presenter Cue:** Click *Approve Allocation*. Show live status transition: `PROPOSED` -> `APPROVED` -> `SUBMITTED` -> `IN_TRANSIT`.
- **Key Metric:** Permanent idempotency key `rec-<uuid>` committed once to PostgreSQL; worker outbox executor submits to `POST /v1/allocations`.

### Phase 4: Surprise Fault & Circuit Breaker (6:00 – 8:00)
- **Harness Action:** Injects transient HTTP 503 fault into upstream simulator.
- **Presenter Cue:** Show amber *Data is degraded* notification banner, Alert Center incident card, and automatic Alertmanager webhook routing. Note that cached state remains visible to the operator and zero invalid allocations can ever be submitted.
- **Key Metric:** Client circuit breaker opens after 5 failures; worker retries bounded with jitter.

### Phase 5: Fault Recovery & Stand-Down (8:00 – 9:30)
- **Harness Action:** Clears simulator fault. Ingestion worker automatically reconnects via sequential health pre-flight.
- **Presenter Cue:** Point to instant green recovery banner, restored `● LIVE PUSH` stream, and zero corrupted state.
- **Key Metric:** Sub-second recovery time (0.24s latency recovery, 0.82s worker restart recovery).

### Close & Stand-Down (9:30 – 10:00)
- **Harness Action:** Restores simulator to clean standby state with simulator `PAUSED` at tick 0 and 0 active faults.
- **Presenter Cue:** Conclude with core platform metrics: 97.93% heuristic SLA (+0.79% [0.41%, 1.27%] bootstrap CI), 2.93s RTO, 625.8 req/s throughput, 262 automated tests, and 0 security vulnerabilities.
