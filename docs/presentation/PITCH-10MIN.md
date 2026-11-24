# 10-Minute Judging Presentation Script

**Event:** BUP CSE Fest 2026 Hackathon
**Platform:** Fuel Supply Intelligence & Resilience Platform
**Target Duration:** 10:00 Minutes (Strictly Timed)
**Presenter:** Faizul Kabir Abrar
**Companion Artifacts:** [SLIDES.md](SLIDES.md), [slides.html](slides.html), [QA-CHEATSHEET.md](QA-CHEATSHEET.md), [Demo Director](../../scripts/demo_director.py)

---

## Presentation Timing Summary

| Act | Time Window | Section Title | Primary UI Route / Screen | Key Message |
|:---:|:---:|---|---|---|
| **0** | `00:00 - 01:00` | Context, Problem & 9-Stage Loop | Architecture Slide | Regional fuel logistics fail due to cascading blindspots; our closed loop restores control. |
| **1** | `01:00 - 02:15` | Real-Time Telemetry & SSE Push | `/` (Dashboard) & `01-dashboard` | Instant observability of 2 depots, 4 corridors, 8 stations with zero-lag SSE invalidation. |
| **2** | `02:15 - 03:30` | Shortage Risk & Monte Carlo Projections | `/risk` & `04-risk`, `05-trajectory` | Pure statistical forecasting with diurnal curves and 300-path Monte Carlo risk runway. |
| **3** | `03:30 - 04:30` | Crisis Injection & Real-Time Detection | `/alerts` & `16-alert-center` | Mathematical anomaly detectors trigger instant warnings with zero-tick adaptation lag. |
| **4** | `04:30 - 05:45` | Decision Support: Two-Pass Triage | `/recommendations` & `06-ranked` | Emergency 12h urgency triage with 5 strict physical constraint audits before any action. |
| **5** | `05:45 - 06:45` | What-If Simulation Sandbox | `/recommendations` (What-If modal) | In-memory zero-database simulation (<50ms) proving averted stockouts before committing. |
| **6** | `06:45 - 07:45` | Mandatory Human Approval & Idempotency | `/recommendations` & `09-approval` | Operator identity, constant-time token check, and permanent UUID idempotency key. |
| **7** | `07:45 - 08:45` | Resilience, Chaos & Recovery | `/health` & `19-degraded`, `20-recovery` | Circuit breaker trips under fault, surfaces degraded banner, auto-recovers in <1 second. |
| **8** | `08:45 - 10:00` | Scientific Proof, Verification & Q&A | `/evaluation` & `21-evaluation` | 60-scenario sweep (+0.79% SLA, +3.69% holdout), 262 tests, 36s cold start, 100% compliant. |

---

## Detailed Act-by-Act Speaking Script

### Act 0: Context, Problem & The 9-Stage Operational Loop (00:00 – 01:00)

> **[SLIDE 1 & 2: Title & Problem Architecture]**
>
> *"Good morning, respected judges. In downstream fuel distribution across Bangladesh—from the bulk terminals at Gazipur and Patiya out to retail stations in Chittagong, Sylhet, and Bogra—a single highway bottleneck or demand surge can trigger cascading retail stockouts within 12 hours.*
>
> *Existing systems operate in silos: telemetry lives in spreadsheets, dispatchers guess demand, and emergency dispatches violate tank ullage or depot truck capacity.*
>
> *We built the **Fuel Supply Intelligence & Resilience Platform** for the BUP CSE Fest 2026 Hackathon. It implements a rigorous, unified 9-stage engineering control loop:*
>
> **Observe, Detect, Predict, Decide, Simulate, Approve, Act, Monitor, and Recover.**
>
> *Every component is dockerized across 8 services, strictly separates read and write boundaries, and is governed by one non-negotiable rule: **All operations are SIMULATED, and NO allocation is ever autonomously executed without authenticated human authority.** Let's see it live."*

---

### Act 1: Real-Time Telemetry & SSE Push (01:00 – 02:15)

> **[SWITCH TO RUNNING PLATFORM: http://localhost:5173 / DASHBOARD]**
>
> *"Here is the operator dashboard running live on port 5173. Notice the persistent amber banner: 'SIMULATED ENVIRONMENT — Human Approval Required'.*
>
> *In the top HUD, we observe current simulator tick 0, system health 'HEALTHY', and active policy 'two_pass_urgency_12h_then_target'.*
>
> *Notice the green badge: **'● LIVE PUSH'**. Rather than pounding the database or simulator with aggressive polling, our background worker listens to simulator Server-Sent Events hints, updates our PostgreSQL state atomically, and broadcasts Postgres LISTEN/NOTIFY events through FastAPI SSE to the browser. This cut client read traffic by **95%**.*
>
> *On the main canvas, we see our network inventory matrix: Gazipur and Patiya bulk depots with over 200,000 liters of reserves, and stations across the regional corridors displaying Diesel, Petrol, and Octane levels against physical tank limits."*

---

### Act 2: Shortage Risk & Monte Carlo Projections (02:15 – 03:30)

> **[NAVIGATE TO: Shortage Risk View / `/risk`]**
>
> *"Telemetry alone cannot prevent stockouts. An operator needs foresight. Let's open the **Shortage Risk Matrix**.*
>
> *Our forecasting engine (`forecast.py`) uses a pure mathematical diurnal curve model with day-of-week seasonality. It decomposes historical consumption without external heavy machine learning dependencies.*
>
> *Feeding into this is our Monte Carlo risk projector (`risk.py`). For every station and fuel type, we simulate **300 stochastic consumption trajectories** over the next 24 hours.*
>
> *[CLICK STATION ROW TO OPEN TRAJECTORY DRAWER]*
>
> *Look at this interactive Trajectory Drawer. The blue line is our diurnal baseline consumption. The shaded area represents the **P10 to P90 confidence interval**. When the P10 trajectory crosses the critical safety threshold before incoming resupply can arrive, the station is flagged with a high stockout probability and ranked by urgency.*
>
> *All calculations are 100% vectorized in NumPy, completing in under **12 milliseconds** per cycle."*

---

### Act 3: Crisis Injection & Real-Time Detection (03:30 – 04:30)

> **[NAVIGATE TO: Alert Center / `/alerts`]**
>
> *"Now, let's look at crisis detection. Supply chains do not fail smoothly; they fail suddenly through surprise events.*
>
> *Our anomaly detector (`detect.py`) evaluates 5 distinct mathematical detectors every tick: sudden demand spikes (ratio >= 1.3), corridor disruptions, station stockouts, depot depletion, and forecast calibration drift.*
>
> *Under our Event-Aware Calibration model (v1.2.0), when a surge is detected, the forecasting model dynamically adapts its multiplier with **zero-tick adaptation lag**, preventing the common failure mode where historical moving averages lag behind real-time panic buying.*
>
> *Here in the Alert Center, each incident is categorized by severity—CRITICAL, WARNING, INFO—with human-readable generative operational summaries. Operators can immediately export full audit logs via CSV or JSON with a single click."*

---

### Act 4: Decision Support: Two-Pass Triage (04:30 – 05:45)

> **[NAVIGATE TO: Recommendations View / `/recommendations`]**
>
> *"When a crisis hits, what should the operator do? Greedy refill policies fail because they starve distant stations or exhaust depot truck capacity early.*
>
> *Our decision engine (`policies.py`) implements a **Two-Pass Urgency Triage heuristic**:*
> - *Pass 1: Identifies all stations facing imminent stockout within the next 12 hours and allocates minimum emergency fuel to prevent stockout, locking depot dispatch limits and available trucks.*
> - *Pass 2: Distributes remaining depot capacity to restore non-critical stations toward safe target inventory levels.*
>
> *Look at the recommendation card on screen. Before any proposal is presented to the operator, our pure constraint validator (`validator.py`) verifies all **5 physical laws**:*
> 1. *Source depot has sufficient unreserved fuel.*
> 2. *Destination tank has sufficient ullage—allocations can never exceed available space.*
> 3. *Transit corridor is open and unblocked.*
> 4. *Truck payload is between 5,000L and 7,000L.*
> 5. *Depot daily truck dispatch rate limit is not exceeded.*
>
> *Every check is marked with a green checkmark or an explicit failure explanation."*

---

### Act 5: What-If Simulation Sandbox (05:45 – 06:45)

> **[OPEN WHAT-IF SANDBOX MODAL]**
>
> *"Before approving an allocation, an operator often wonders: 'What if I increase this dispatch by 2,000 liters? What if the delivery arrives 2 ticks late?'*
>
> *We built the **What-If Simulation Sandbox** (`WhatIfSimulator.tsx`, `POST /api/whatif`).*
>
> *It is a zero-database, purely in-memory counterfactual simulator. It runs directly inside the API process using the latest cached network snapshot.*
>
> *Let's adjust the slider: increase dispatch volume to Chittagong Station by 5,000 liters.*
>
> *In **under 50 milliseconds** (and 288 ms under 200 virtual user load), the sandbox projects the counterfactual stock trajectory, computes the averted stockout hours, and audits physical feasibility.*
>
> *The operator knows the exact outcome of their decision before issuing a command."*

---

### Act 6: Mandatory Human Approval & Idempotent Submission (06:45 – 07:45)

> **[SHOW APPROVAL CARD ON SCREEN]**
>
> *"Now we reach the governance core: **Act**.*
>
> *Notice that the 'Approve' button is disabled until the operator enters their name and security token.*
>
> *When I input `Operator Faizul` and our secure operator token, our API validates the credentials using constant-time hash comparison (`hmac.compare_digest`) protected by a sliding-window rate limit (60 requests per minute).*
>
> *[CLICK APPROVE]*
>
> *The decision is recorded in our PostgreSQL immutable audit ledger. But look at what happens behind the scenes:*
> - *The API **never** calls the simulator directly.*
> - *Instead, our background worker uses the transactional Outbox Pattern. At the exact millisecond of dispatch, it re-verifies that data is fresh (rejecting if `X-Simulator-Stale: true`) and re-validates all 5 constraints.*
> - *It attaches a permanent UUID idempotency key inside the request body.*
>
> *If the simulator drops the connection or reboots, retries will NEVER double-dispatch fuel. Idempotency is permanent."*

---

### Act 7: Resilience, Chaos & Recovery (07:45 – 08:45)

> **[NAVIGATE TO: System Health View / `/health`]**
>
> *"A platform in this domain must survive hostile conditions. In Sprint 5, 12, and 14, we subjected this system to extreme fault testing:*
> - *HTTP 503 upstream outages*
> - *Simulated network latency up to 5,000ms*
> - *Simulator crash loops and process restarts*
> - *Corrupt and truncated SSE payloads*
>
> *Look at our typed Circuit Breaker (`sim_client.py`). When the simulator fails, the breaker trips to OPEN. The UI immediately displays an amber **DEGRADED MODE** banner, halts recommendations, and serves cached data labeled with its exact age in seconds.*
>
> *When the simulator recovers, our breaker uses a half-open probe. In Sprint 14, we resolved a concurrency edge case (ADR-051) where parallel probes under `asyncio.gather` could deadlock. Now, recovery is verified in **0.21 to 1.79 seconds** across all 8 fault scenarios.*
>
> *Furthermore, our database disaster recovery drill demonstrated a complete cold restore with **2.93 seconds RTO**."*

---

### Act 8: Scientific Proof, Verification & Q&A (08:45 – 10:00)

> **[NAVIGATE TO: Evaluation View / `/evaluation` & RETURN TO SLIDES]**
>
> *"Finally, we present our empirical evidence. We do not make claims without proof:*
>
> 1. **Robust 60-Scenario Sweep:** Across 240 simulation runs (192 ticks each, seed=42), our Two-Pass Triage heuristic achieved a **97.93% Mean Service Level**, outperforming greedy naive refill by **+0.79% [0.41%, 1.27%] 95% bootstrap CI**, cutting unmet demand by **35%**. On 10 unseen holdout disasters, the margin increased to **+3.69%**.
> 2. **Honest Boundary Disclosure:** We identified our system's exact physical failure ceiling—23,000 L/tick demand surge under 2 simultaneous corridor blocks—and published our single scenario loss (`holdout_08`, -0.08% SLA) due to transit timing lag.
> 3. **Engineering Rigor:**
>    - **262 automated tests** (239 Python, 11 Vitest, 12 Playwright E2E).
>    - **0 security vulnerabilities** across `pip-audit`, `npm audit`, `trivy`, and `gitleaks`.
>    - **0 critical accessibility violations** across all 8 views (axe-core score 98.75/100).
>    - **36-second cold-start** from wiped Docker volumes.
>    - **100% Brief Compliance** across all 109 charter items.
>
> *Thank you. We are ready for your questions."*
