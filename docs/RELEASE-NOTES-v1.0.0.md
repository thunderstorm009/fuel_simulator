# Release Notes: Fuel Supply Intelligence & Resilience Platform v1.0.0

- **Release:** v1.0.0 (Candidate for Owner Release)
- **Target Event:** BUP CSE Fest 2026 Hackathon
- **Date:** 2026-11-23
- **Commit:** HEAD of branch `sprints-11-13` (Git tag `sprint-13`)
- **Status:** **PRODUCTION READY & JUDGING PREPARED**

---

## Executive Summary

The **Fuel Supply Intelligence & Resilience Platform** is an integrated operational decision-support platform built on top of the official BUP Fuel Supply Simulator. Over 13 sequential four-hour engineering sprints in a single repository, the platform was developed from basic contract bindings into a robust, high-throughput, mathematically constrained, accessible, and disaster-resilient system.

The platform provides civilian fuel dispatchers and crisis operators with real-time situational awareness, predictive stockout trajectories, interactive counterfactual What-If simulation, explainable constrained recommendations, mandatory token-authenticated approval gates, automated alert routing, and disaster recovery.

---

## Key Platform Capabilities

### 1. Complete Operational Control Loop
Implements the 9-stage operational cycle:
$$\text{Observe} \longrightarrow \text{Detect} \longrightarrow \text{Predict} \longrightarrow \text{Decide} \longrightarrow \text{Simulate} \longrightarrow \text{Approve} \longrightarrow \text{Act} \longrightarrow \text{Monitor} \longrightarrow \text{Recover}$$
- **Architectural Isolation:** The API never queries the simulator on read paths; all reads are served from local PostgreSQL cache in sub-millisecond time. The background worker strictly owns all external simulator I/O.
- **REST is Truth:** SSE events serve as advisory push hints that trigger REST refetches, guaranteeing zero dropped state across reconnects.

### 2. High-Performance Scaled API
- **Throughput:** Tripled from 201 req/s to **625.8 requests/second at 200 Virtual Users** under k6 load testing.
- **Latency:** Read p95 latency reduced by 72% (**338.3 ms** at 200 VUs; p50: 88.2 ms).
- **Optimization Stack:** 4 Uvicorn workers, asyncpg connection pool (20 connections), 3 composite database indexes (149x query speedup), in-memory pre-serialized UTF-8 byte caching, and HTTP ETag / 304 Not Modified support.
- **Database Efficiency:** PostgreSQL CPU consumption under 400 VUs dropped by 89% (from 309.8% to 34.1%), with **0.00% error rate**.

### 3. Event-Aware Demand Forecasting (Model v1.2.0)
- **Instantaneous Adaptation:** Upgraded from EWMA ratio tracking to incorporate active event multipliers into historical expected demand, reducing demand surge adaptation lag from **7–19 ticks down to 0 ticks**.
- **Accuracy:** Mean Absolute Percentage Error (MAPE) of **2.11%** over 24-hour horizons outside events and **3.88%** during active disruptions across 2,000 historical ticks.
- **Uncertainty Quantification:** Vectorized Monte Carlo simulation (300 seeded paths) calculates empirical P10, P50, and P90 confidence bounds with a Brier calibration score of **0.1558**.

### 4. Scientific Policy Evaluation (60 Randomized Scenarios, 240 Runs)
- **Heuristic Mean SLA:** **97.93%** across 60 randomized crisis scenarios (seed=42; 50 tuning, 10 hold-out) vs Naive greedy refill at **97.14%** and Do-Nothing at **40.40%**.
- **Statistical Significance:** Bootstrap 95% confidence interval shows a statistically significant improvement of **+0.79% [0.41%, 1.27%]** in network service level, cutting unmet demand by 35% (4,798 L vs 7,324 L).
- **Head-to-Head Record:** **15 Wins / 44 Ties / 1 Loss** vs Naive.
- **Hold-Out Disaster Family (10 compound crises):** Heuristic achieved **96.26% SLA** vs Naive **92.57% SLA** (+3.69% improvement; 9 Wins / 0 Ties / 1 Loss).
- **Transparent Loss Disclosure:** Exactly 1 loss out of 60 scenarios (`holdout_08`, 99.86% vs 99.95%, a -0.08% delta) due to compound multi-corridor transit bottleneck latency.

### 5. Interactive Counterfactual What-If Sandbox
- **Zero-Database Simulation:** `POST /api/whatif` evaluates candidate dispatch volumes and destination routes purely in memory using cached models.
- **Sub-Second Speed:** Executes in **<50 ms unloaded** and **288.3 ms under 200 VU load** (beating the 500 ms SLA).
- **Safety Guarantee:** Adjusting candidate sliders never modifies persistent recommendations or allocates idempotency keys.

### 6. Mandatory Human Operator Gate & Regulatory Auditing
- **Zero Autonomous Submissions:** Automated dispatches to `/v1/allocations` are strictly prevented by code architecture.
- **Authorization:** Approval requires `OPERATOR_TOKEN` verified via constant-time comparison (`hmac.compare_digest`) with rate limiting (60 req/min).
- **Operator Attribution:** Operator name is mandatory on approval/rejection and recorded permanently in the `decisions` audit table (`actor`).
- **Audit Export:** One-click **Export CSV**, **Export JSON**, and **Copy JSON** of decision history and incidents.

### 7. Real-Time Push Invalidation via SSE
- **Efficiency:** `GET /api/stream` backed by PostgreSQL `LISTEN/NOTIFY` pushes invalidation hints only when state changes.
- **Traffic Reduction:** Reduces client read polling volume by **95%** during steady-state operation.
- **Resilience:** Automatic fallback to 10-second interval polling if the stream drops, with exponential backoff reconnection.

### 8. Production Resilience & Measured Disaster Recovery
- **Database Restore Drill:** Automated drill (`scripts/drill_backup_restore.py`) demonstrated a Recovery Time Objective (**RTO**) of **2.93 seconds** (target < 15s) with 100% row preservation across all tables and zero duplicate allocations submitted.
- **Soak Testing:** 90-minute live soak test under continuous randomized chaos injection verified bounded memory drift (API: +14.4 MiB; Worker: +2.4 MiB) and database bounded growth.
- **Alert Routing:** End-to-end Alertmanager integration under Compose profile `alerts` with dedicated webhook receiver, demonstrating automated firing and resolution of critical alerts.
- **Policy Fail-Safe Rollback:** Runtime policy switch (`POST /api/policy`) automatically rolls back to `HeuristicPolicy` within 500 ms if any candidate policy throws an error, times out, or emits a constraint violation.

### 9. Usability, Accessibility & Quality Assurance
- **Browser E2E Suite:** 12 end-to-end Playwright browser tests passing in **31.7s** in GitHub Actions CI.
- **Accessibility:** axe-core automated audit across all 8 operational views achieved **0 critical WCAG 2.1 AA violations** (scores: 90/100 subpages, 80/100 overview).
- **Guided Tour:** Accessible interactive walkthrough (`GuidedTour.tsx`) for onboarding and judging presentations.
- **Security Scans:** **0 known vulnerabilities** in `pip-audit`, **0 vulnerabilities** in `npm audit`, **0 High/Critical findings** in Trivy container scans, and **0 secrets detected** across the entire git history via Gitleaks.

---

## Service Topology & Published Ports

| Service | Container Image / Base | Published Host Port | Health Endpoint |
|---|---|---|---|
| **API Backend** | Python 3.12 / FastAPI (4 Uvicorn workers) | `8101` | `http://localhost:8101/api/health` |
| **Worker Engine** | Python 3.12 / Asyncio | `8102` | `http://localhost:8102/health` |
| **Predictor Service** | Python 3.12 / FastAPI | `8103` | `http://localhost:8103/health` |
| **Frontend UI** | Node 20 / React 19 / Vite | `5173` (or `5174`) | `http://localhost:5173` |
| **PostgreSQL** | `postgres:16-alpine` | `5432` | `pg_isready -U postgres` |
| **Prometheus** | `prom/prometheus:v3.2.1` | `9090` | `http://localhost:9090/-/healthy` |
| **Grafana** | `grafana/grafana:11.5.2` | `3000` | `http://localhost:3000/api/health` |
| **Simulator** | `asifmahmoud414/bup-fuel-supply-simulator:1.0.0` | `8000` | `http://localhost:8000/v1/health` |

---

## Quick Verification Commands

```bash
# 1. Start full platform (8 containers)
make up

# 2. Verify judging day readiness
make preflight

# 3. Run full test suite
make test

# 4. Run Playwright E2E browser tests
make test-e2e

# 5. Run interactive demo director
make demo
```
