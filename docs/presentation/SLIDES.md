# Fuel Supply Intelligence & Resilience Platform
## BUP CSE Fest 2026 Hackathon Final Presentation

---

### Slide 1: Title Slide

# Fuel Supply Intelligence & Resilience Platform
### A Simulation-Driven Control Loop for Shortage Forecasting, Risk Mitigation & Constrained Allocation
**BUP CSE Fest 2026 Hackathon**

- **Lead Engineer:** Faizul Kabir Abrar ([@thunderstorm009](https://github.com/thunderstorm009))
- **Repository:** `thunderstorm009/fuel_simulator` (Release `v1.0.0`)
- **Test Suite:** 262 Automated Tests (239 Python, 11 Vitest, 12 Playwright E2E)
- **Status:** 100% Brief Compliance (109 / 109 Requirements Met)

---

### Slide 2: The Challenge: Cascading Shortages in Regional Fuel Logistics

- **Vulnerable Topology:** 2 primary bulk supply depots (Gazipur, Patiya) feeding 8 retail filling stations across 4 transit corridors.
- **Cascading Failure Modes:**
  - Route blockages (highway protests, monsoons, bottlenecks) causing 3x travel delays.
  - Abrupt regional demand surges (panic buying, harvest season, industrial spikes).
  - Depot truck dispatch limits and strict station ullage constraints.
- **The Core Problem:** Telemetry is delayed, greedy allocation starves distant stations, and manual dispatchers lack counterfactual foresight.

---

### Slide 3: Architectural Control Loop: The 9-Stage Foundation

```
Observe ──> Detect ──> Predict ──> Decide ──> Simulate ──> Approve ──> Act ──> Monitor ──> Recover
```

- **Clean Architecture Boundaries:**
  - **Read Path:** API serves cached PostgreSQL snapshots with composite ETag invalidation (<1ms cached, 88ms p50).
  - **Background Worker:** Owns all external simulator I/O; consumes REST polling and SSE hints.
  - **Machine Learning / Predictor:** Pure microservice with zero-dependency baseline heuristic fallback.
  - **Human Governance Gate:** Mandatory operator authentication token before any dispatch action.
  - **Outbox Executor:** Background worker verifies freshness and constraints before permanent idempotent dispatch.

---

### Slide 4: Real-Time Observability & SSE Push Telemetry

![Dashboard Overview](../evidence/day-7/screens/01-dashboard-overview.png)
*Figure 4.1: Live Operator Dashboard with mandatory SIMULATED HUD, tick progression, active policy indicator, and SSE live push stream status.*

- **Dual-Mode Telemetry Synchronization:**
  - SSE push invalidation stream (`● LIVE PUSH`) cuts browser polling overhead by **95%**.
  - Automatic fallback to REST polling (2s interval) if SSE connection encounters transient disconnect.
- **Station Inventory & Ullage Tracking:**
  - Real-time tracking of Diesel, Petrol, and Octane across all 8 stations.
  - Physical tank ullage limits strictly enforced to prevent catastrophic tank overflows.

![Station Inventory and Ullage](../evidence/day-7/screens/03-station-inventory-ullage.png)
*Figure 4.2: Granular fuel matrix displaying tank capacity, on-hand volume, and available ullage.*

---

### Slide 5: Shortage Risk Forecasting: Diurnal Curves & Monte Carlo

![Shortage Risk Matrix](../evidence/day-7/screens/04-shortage-risk-matrix.png)
*Figure 5.1: Shortage Risk Matrix showing urgency ranking, probability of stockout, and confidence index.*

- **Pure Statistical Forecasting (`forecast.py`):**
  - Hour-of-day diurnal consumption curves with day-of-week seasonality factors.
  - Evaluated on backtests across 1h to 24h horizons: **2.11% Mean Absolute Percentage Error (MAPE)**.
- **Vectorized Monte Carlo Runway (`risk.py`):**
  - 300 stochastic simulation paths per station-fuel pair.
  - Computes P10 (pessimistic), P50 (median), and P90 (optimistic) stock trajectories in **<12ms**.

![Trajectory Drawer Monte Carlo](../evidence/day-7/screens/05-trajectory-drawer-mc.png)
*Figure 5.2: Interactive Trajectory Drawer rendering 24-hour stock projection with uncertainty bands and driver decomposition.*

---

### Slide 6: Crisis Detection & Event-Aware Calibration v1.2.0

![Alert Center Incidents](../evidence/day-7/screens/16-alert-center-incidents.png)
*Figure 6.1: Real-time Alert Center with severity classifications (CRITICAL, WARNING, INFO) and export capabilities.*

- **Pure Mathematical Anomaly Detection (`detect.py`):**
  - Evaluates demand surges ($Ratio \ge 1.3$), corridor disruptions, station stockouts, and depot depletion every tick.
- **Event-Aware Calibration v1.2.0:**
  - Traditional moving-average forecasts suffer from a 3–5 tick adaptation lag during crisis onset.
  - Our event-aware calibration hooks into detection signals to immediately update multipliers with **zero-tick lag**.
- **AI-Powered Incident Explanations:**
  - Generative structured summaries explaining root causes, affected stations, and recommended actions.
  - Enforces mandatory *"SIMULATED ENVIRONMENT — AI-generated summary"* disclaimer.

![Incident Explanation AI](../evidence/day-7/screens/17-incident-explanation-ai.png)
*Figure 6.2: Structured incident briefing drawer breaking down root cause, impact radius, and immediate actions.*

---

### Slide 7: Decision Support: Two-Pass Urgency Triage

![Recommendations Ranked](../evidence/day-7/screens/06-recommendations-ranked.png)
*Figure 7.1: Urgency-ranked replenishment recommendations generated by the Two-Pass Triage heuristic.*

- **Why Greedy Allocation Fails:**
  - Refilling non-critical nearby stations exhausts depot truck dispatches, starving remote stations before crisis resolution.
- **Two-Pass Urgency Triage Policy:**
  - **Pass 1 (Emergency):** Filters stations facing stockout within 12 hours. Allocates minimum survival volume to prevent depletion.
  - **Pass 2 (Target):** Distributes remaining depot capacity to restore non-critical stations toward safe operational buffers.
- **Five Physical Constraint Checklists:**
  1. $\text{Depot Unreserved Stock} \ge \text{Allocation}$
  2. $\text{Station Tank Ullage} \ge \text{Allocation}$
  3. $\text{Corridor Transit Status} = \text{OPEN}$
  4. $5,000\text{L} \le \text{Truck Payload} \le 7,000\text{L}$
  5. $\text{Daily Dispatches} \le \text{Depot Max Truck Limit}$

![Recommendation Constraint Audit](../evidence/day-7/screens/07-recommendation-constraint-audit.png)
*Figure 7.2: Card-level verification checklist displaying green checkmarks for all 5 physical constraints.*

---

### Slide 8: What-If Simulation Sandbox: Zero-Database Speed

![What-If Counterfactual Runway](../evidence/day-7/screens/08-what-if-counterfactual-runway.png)
*Figure 8.1: What-If Simulation Sandbox demonstrating candidate allocation slider, post-dispatch tank state, and averted stockout hours.*

- **Sub-50ms Counterfactual Exploration:**
  - Pure zero-database in-memory simulator (`POST /api/whatif`).
  - Executes directly inside API process memory using cached telemetry snapshots.
  - Evaluates candidate dispatch volume, timing adjustments, and truck size variations.
- **Immediate Impact Feedback:**
  - Recomputes destination stock trajectory and averted stockout hours instantly.
  - Audits physical constraints before human commitment, eliminating trial-and-error in live dispatch.
  - Benchmarked under load: **288.3 ms p95 at 200 concurrent Virtual Users**.

---

### Slide 9: Mandatory Human Authority & Permanent Idempotency

![Human Approval Flow](../evidence/day-7/screens/09-human-approval-flow.png)
*Figure 9.1: Human approval card requiring operator name and constant-time secret token validation.*

- **Strict Governance Boundary:**
  - The platform **never auto-submits** replenishment recommendations.
  - Every dispatch requires explicit operator sign-off with operator name logging and `OPERATOR_TOKEN` verification.
  - Rate-limited via sliding window (60 req/min) with constant-time hash comparison (`hmac.compare_digest`).
- **Permanent Idempotency Key Guarantees:**
  - Generated once per recommendation UUID.
  - Persisted in PostgreSQL outbox table; reused only for identical request payloads.
  - Network dropouts, server restarts, or simulator crashes will **never double-dispatch**.

![Decision History Audit Log](../evidence/day-7/screens/10-decision-history.png)
*Figure 9.2: Immutable decision history log showing operator actor, timestamp, UUID idempotency key, and status.*

---

### Slide 10: Supply Corridors & Disruption Mapping

![Network Topology](../evidence/day-7/screens/12-network-topology.png)
*Figure 10.1: Supply network topology map showing regional depots, connecting highway corridors, and transit trucks.*

- **Corridor Telemetry:**
  - Tracks 4 regional road arteries (Dhaka-Chittagong, Dhaka-Sylhet, Dhaka-Khulna, Dhaka-Rajshahi).
  - Dynamic travel time multipliers reflect active road disruptions and weather delays.
- **In-Transit Fuel Tracking:**
  - Explicitly separates **on-hand inventory** from **scheduled supply** and **in-transit trucks**.
  - Prevents double-counting inventory before fuel physically discharges into station tanks.

![Route Corridor Status](../evidence/day-7/screens/13-route-corridor-status.png)
*Figure 10.2: Granular corridor operational cards detailing transit ticks, active bottlenecks, and route capacities.*

---

### Slide 11: Fault Tolerance, Chaos & Rapid Recovery

![Degraded Mode Banner](../evidence/day-7/screens/19-degraded-mode-banner.png)
*Figure 11.1: Platform operating in DEGRADED mode during upstream simulator outage with amber warning banner.*

- **Resilience Engineering:**
  - Typed Circuit Breaker (`sim_client.py`) trips to `OPEN` on consecutive simulator failures.
  - Bounded retries with exponential backoff and jitter; never retries HTTP 409 or 422 errors.
  - Serves cached state with explicit data age telemetry (`X-Simulator-Stale: true`).
- **Concurrency-Hardened Recovery:**
  - Resolved half-open probe deadlock under `asyncio.gather` (ADR-051).
  - Verified sub-second recovery (**0.21s to 1.79s**) across all 8 fault scenes.
  - Disaster recovery drill: **2.93s RTO** complete database restore from cold backup.

![Recovery Cleared Banner](../evidence/day-7/screens/20-recovery-cleared-banner.png)
*Figure 11.2: Restored operational state with healthy telemetry badges and active push invalidation.*

---

### Slide 12: Empirical Validation: 60 Crisis Scenarios (240 Live Runs)

![Policy Evaluation Comparison](../evidence/day-7/screens/21-evaluation-policy-comparison.png)
*Figure 12.1: Policy evaluation dashboard comparing Heuristic, Optimizer, and Naive baselines across randomized scenarios.*

- **Methodology:** 60 randomized crisis scenarios (192 ticks / 2 simulated days each; 240 live simulation runs, seed=42) comparing Do-Nothing, Greedy Naive, and Two-Pass Heuristic.
- **Key Results:**
  - **Mean Network SLA:** Heuristic achieved **97.93%** vs Naive **97.14%** (+0.79% Mean Δ).
  - **95% Bootstrap Confidence Interval:** `[+0.41%, +1.27%]` (Statistically significant).
  - **Unmet Demand Reduction:** Cut unmet fuel demand by **35%** (4,798 L vs 7,324 L).
  - **Holdout Compound Disasters (10 Scenarios):** Heuristic achieved **96.26%** vs Naive **92.57%** (**+3.69% improvement**; 9 Wins, 0 Ties, 1 Loss).
  - **Honest Loss Disclosure:** Exactly 1 loss out of 60 scenarios (`holdout_08`, -0.08% SLA delta) due to extreme multi-corridor transit lag divergence.

---

### Slide 13: Production Quality, Cold Start & Scaled Performance

| Dimension | Measured Metric | Benchmark Standard | Status |
|---|---|---|:---:|
| **Automated Tests** | **262 tests passed** (239 Pytest, 11 Vitest, 12 Playwright) | 100% test pass rate | **PASS** |
| **API Throughput** | **625.8 requests/sec** (at 200 VUs) | Sub-300ms p95 read latency | **PASS** |
| **What-If Latency** | **288.3 ms p95** (under 200 VU load; <50ms unloaded) | <500ms brief SLA target | **PASS** |
| **Cold Start Timing** | **36 seconds** from wiped Docker volumes to healthy stack | Rapid recovery standard | **PASS** |
| **Database Restore RTO** | **2.93 seconds** complete disaster recovery | Resilient continuity target | **PASS** |
| **Security Audits** | **0 vulnerabilities** (pip-audit, npm audit, Trivy, Gitleaks) | Zero known High/Critical | **PASS** |
| **Accessibility Audit** | **0 Critical Violations** across all 8 views (Score: 98.75/100) | WCAG 2.1 AA standards | **PASS** |
| **Brief Compliance** | **109 of 109 requirements MET** (100% verified) | Official hackathon charter | **PASS** |

---

### Slide 14: Conclusion & Q&A Defense

- **Summary of Achievements:**
  1. A complete 9-stage engineering control loop that observes, forecasts, recommends, and safeguards fuel logistics.
  2. Pure algorithms: Diurnal curves, Monte Carlo simulations, and Two-Pass triage without opaque black boxes.
  3. Uncompromising governance: Human authority enforced with constant-time security and permanent idempotency.
  4. Extreme resilience: Sub-second fault recovery, 36s cold start, and 2.93s database RTO.
  5. Scientific truthfulness: 60-scenario sweep with 95% bootstrap CI and honest failure boundary disclosure.

**Repository:** `https://github.com/thunderstorm009/fuel_simulator`
**Tagged Release:** `v1.0.0`

*We welcome questions from the judging panel.*
