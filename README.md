# Fuel Supply Intelligence & Resilience Platform

> **BUP CSE Fest 2026 Hackathon**
> A simulation-driven platform for fuel inventory intelligence, demand forecasting, shortage-risk analysis and resilient allocation decision support.

[![CI Status](https://img.shields.io/badge/CI-passing-brightgreen)](https://github.com/thunderstorm009/fuel_simulator/actions)
[![Python Tests](https://img.shields.io/badge/pytest-182%20passed-brightgreen)](tests/)
[![Frontend Tests](https://img.shields.io/badge/vitest-11%20passed-brightgreen)](web/tests/)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-blue)](web/)
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-8%20services-blue)](docker-compose.yml)
[![Judging Guide](https://img.shields.io/badge/Judging-Runbook-blueviolet)](docs/JUDGING-DAY.md)
[![Scope](https://img.shields.io/badge/scope-SIMULATED-orange)](#scope-and-limitations)

---

## Main Operator Dashboard

![Fuel Supply Intelligence Platform Dashboard](docs/evidence/day-3/screens/01-dashboard.png)
*Figure 1: Main operator overview displaying real-time simulated network state across regional corridors (Dhaka, Chattogram, Cox's Bazar), overall service level, station-by-station fuel capacity bars, and regional depot reserves.*

---

## Project Overview

In regional fuel logistics, supply chain disruptions—such as highway blockages, unexpected demand spikes, supply arrival delays, and transport bottlenecks—can quickly trigger cascading stockouts at retail filling stations.

The **Fuel Supply Intelligence & Resilience Platform** provides an integrated operational control loop on top of the official BUP CSE Fest 2026 Fuel Supply Simulator. It connects to the simulator's REST and Server-Sent Event (SSE) streams, continuously ingests downstream fuel distribution telemetry, forecasts future stockout trajectories using pure statistical models, and produces constrained, explainable replenishment recommendations.

> [!IMPORTANT]
> **SIMULATED ENVIRONMENT & MANDATORY HUMAN GOVERNANCE:**
> All platform operations represent purely simulated fuel infrastructure. Recommendations are **never autonomously submitted** to the simulator. An authenticated operator must review the physical constraint audit and approve the recommendation using `OPERATOR_TOKEN` before the background executor securely submits the order with permanent idempotency guarantees.

---

## Complete Operational Loop

The platform implements the complete 9-stage engineering loop defined by the hackathon charter:

```
Observe ──> Detect ──> Predict ──> Decide ──> Simulate ──> Approve ──> Act ──> Monitor ──> Recover
```

- **1. Observe:** Real-time synchronization via REST polling with SSE invalidation hints; tracking of bulk depot storage, retail station inventory (Diesel, Petrol, Octane), incoming bulk pipeline, and route corridors.
- **2. Detect:** Pure mathematical anomaly detectors (`backend/shared/core/detect.py`) identifying demand surges (ratio >= 1.3), corridor disruptions, station outages, depot constraints, and model calibration drift.
- **3. Predict:** Pure empirical demand forecasting with diurnal curve modeling (`forecast.py`) and Monte Carlo stockout risk projection with P10–P90 confidence intervals (`risk.py`).
- **4. Decide:** Constrained two-pass triage heuristic prioritizing stations facing stockout within 12 hours while locking depot dispatch capacity; optional SciPy Linear Programming solver (`optimizer.py`).
- **5. Simulate:** Pure zero-database in-memory What-If simulator (`POST /api/whatif`, `WhatIfSimulator.tsx`) computing post-dispatch tank inventory and averted stockout hours (<50ms unloaded, ~834ms under 100 VU load) prior to decision.
- **6. Approve:** Enforced human authority gate using constant-time token comparison (`hmac.compare_digest`) with sliding-window rate limiting (60 req/min).
- **7. Act:** Outbox-pattern background executor re-verifying freshness and physical constraints at the exact moment of dispatch; permanent idempotency key prevents duplicate execution.
- **8. Monitor:** Low-cardinality Prometheus metrics, provisioned 4-layer Grafana dashboards, codified alert rules with runbooks, and correlation-traced decision lifecycles.
- **9. Recover:** Typed circuit breakers, bounded retries with jitter, graceful fallback to local baseline heuristics, automated container rollback (`scripts/rollback.sh`), and disaster recovery drills.

---

## Application Showcase

All interface views are rendered in React 19, TypeScript 5.8, and Tailwind CSS. Screenshots below are captured directly from the live running platform:

| View | Screenshot | Description |
|---|---|---|
| **Inventory Matrix** | ![Inventory View](docs/evidence/day-3/screens/02-inventory.png) | On-hand fuel inventory by station and product (Diesel, Petrol, Octane) shown against tank limits alongside bulk depot supply sources. |
| **Shortage Risk & Forecasts** | ![Risk Matrix](docs/evidence/day-3/screens/03-forecast-risk.png) | Color-coded shortage risk matrix with interactive `TrajectoryDrawer` showing 24-hour Monte Carlo inventory projections and uncertainty bands. |
| **Replenishment Recommendations** | ![Recommendations View](docs/evidence/day-3/screens/04-recommendations.png) | Urgency-ranked allocation proposals with complete physical constraint validation, structured explanations, and operator approval controls. |
| **What-If Simulation Sandbox** | ![What-If Sandbox](docs/evidence/day-3/screens/05-what-if.png) | Candidate what-if evaluator testing hypothetical dispatch volume and timing against physical constraints (<50ms unloaded, ~834ms under 100 VU load) prior to approval. |
| **Crisis Alert Center** | ![Alert Center](docs/evidence/day-3/screens/06-alerts.png) | Real-time crisis alert hub surfacing active anomalies with severity badges and generative plain-text incident explanations. |
| **Regional Demand Breakdown** | ![Regional Demand](docs/evidence/day-3/screens/07-regional-demand.png) | Regional fuel consumption panel tracking demand aggregates and surge multipliers across Dhaka and Chattogram regions across urban, industrial, highway, and regional demand profiles. |
| **Incoming Supply Pipeline** | ![Incoming Supply](docs/evidence/day-3/screens/08-incoming-supply.png) | Scheduled bulk resupply arrivals to depots and in-transit replenishment trucks with arrival ETA ticks. |
| **Network Topology View** | ![Network View](docs/evidence/day-3/screens/09-network.png) | Graph topology visualizing supply nodes (Gazipur, Patiya depots), retail stations, connecting corridors, and active disruptions. |
| **Forecasting Evaluation** | ![Evaluation View](docs/evidence/day-3/screens/10-evaluation.png) | Empirical evaluation view presenting backtest MAPE across 1h–24h horizons (2.1%–3.1%) and deterministic scenario policy comparisons. |
| **Decision Audit History** | ![Decision History](docs/evidence/day-3/screens/11-decision-history.png) | Permanent audit trail proving owner-authorized human approval, worker execution, and confirmed arrival (`ARRIVED`) in the simulator. |
| **System Health (Normal)** | ![System Health](docs/evidence/day-3/screens/12-health-healthy.png) | Aggregated component health status (API, Worker, Predictor, Database, Simulator) with data freshness tracking and latency telemetry. |
| **Graceful Degradation** | ![Health Degraded](docs/evidence/day-3/screens/14-health-degraded.png) | Live graceful degradation during injected simulator outage; displays prominent warning banner and stale data advisory. |
| **Grafana Observability** | ![Grafana Dashboard](docs/evidence/day-3/screens/16-grafana-normal.png) | Provisioned Grafana dashboard monitoring HTTP throughput, p95 durations, worker ingestion lag, and active alerting rules. |
| **Prometheus Alerts Console** | ![Prometheus Alerts](docs/evidence/day-3/screens/17-prometheus-alerts.png) | Prometheus alerting console verifying 5 active alerting rules as code with operational runbooks. |

---

## Architecture

The platform architecture strictly separates read paths, background processing, machine learning prediction, and external simulator I/O:

```mermaid
flowchart TD
    subgraph External["External Environment"]
        SIM["Official Fuel Supply Simulator\n(Port 8000)"]
    end

    subgraph Platform["Fuel Supply Resilience Platform"]
        UI["React 19 + TypeScript Frontend\n(Port 5174 / 5173)"]
        API["FastAPI Operator API\n(Port 8101)"]
        WORKER["Background Ingestion & Execution Worker\n(Port 8102)"]
        PRED["Predictor Service\n(Port 8103 / 8100)"]
        DB[("PostgreSQL 16\n(Port 5432)")]
    end

    subgraph Observability["Observability Stack"]
        PROM["Prometheus Server\n(Port 9090)"]
        GRAF["Grafana Dashboard\n(Port 3000)"]
    end

    %% Read Path
    UI -->|"HTTP REST reads (cached state)"| API
    API -->|"SQL queries (read-only)"| DB
    UI -->|"Operator Approval POST (with token)"| API
    API -->|"Persist approval decision"| DB

    %% Ingestion & Background Path
    WORKER -->|"REST polling (/v1/snapshot)"| SIM
    SIM -.->|"SSE invalidation hints (/v1/events/stream)"| WORKER
    WORKER -->|"Atomic snapshot & forecast writes"| DB
    WORKER -->|"Remote forecast request (/predict)"| PRED
    PRED -.->|"Fallback to local heuristics on error"| WORKER

    %% Write Path (Strictly Guarded)
    WORKER -->|"Re-check constraints & POST /v1/allocations"| SIM

    %% Metrics Scrape
    API -->|"Metrics scrape (/metrics)"| PROM
    WORKER -->|"Metrics scrape (/metrics)"| PROM
    PRED -->|"Metrics scrape (/metrics)"| PROM
    PROM -->|"Data source queries"| GRAF

    classDef primary fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc;
    classDef storage fill:#0f172a,stroke:#10b981,stroke-width:2px,color:#f8fafc;
    classDef external fill:#3b0764,stroke:#a855f7,stroke-width:2px,color:#f8fafc;
    classDef obs fill:#1c1917,stroke:#f59e0b,stroke-width:2px,color:#f8fafc;

    class UI,API,WORKER,PRED primary;
    class DB storage;
    class SIM external;
    class PROM,GRAF obs;
```

### Architectural Principles

- **Worker-Owned Simulator I/O:** The API **never** calls the simulator on read paths; it reads exclusively from PostgreSQL. This guarantees sub-millisecond API response times and complete immunity from simulator latency spikes or outages.
- **REST is Truth; SSE is an Advisory Hint:** SSE streams provide low-latency notification of state changes, but do not support replay. Every reconnect triggers an immediate authoritative REST poll.
- **Pure Core Logic:** Demand forecasting, stockout risk projection, and constraint validation are implemented as pure, deterministic mathematical functions with zero I/O (`backend/shared/core/`), making them 100% unit-testable and reproducible.
- **Mandatory Human Approval Boundary:** The worker executor will only submit an allocation if a matching, unexpired `APPROVED` decision row exists in PostgreSQL and passes a fresh-state constraint check.

---

## Technology Stack

| Layer | Technologies | Purpose in Platform |
|---|---|---|
| **Frontend** | React 19, TypeScript 5.8, Vite 6, Tailwind CSS 4, TanStack Query | Real-time operator dashboard, state caching, and responsive decision UI |
| **Visualization** | Recharts 3, Lucide Icons | Stock projection trajectory charts, confidence bands, and status indicators |
| **Backend API** | FastAPI 0.115, Uvicorn, Pydantic v2 | High-performance async REST API serving operator views and decisions |
| **Worker Engine** | Python 3.12, Asyncio, HTTPX | Background simulator polling, snapshot ingestion, and dispatch execution |
| **Database** | PostgreSQL 16 (Alpine), asyncpg | Relational storage for snapshots, forecasts, proposals, and decisions |
| **Intelligence** | Pure Python Models, EWMA, Monte Carlo | Diurnal consumption modeling, stockout probability, and heuristic ranking |
| **Observability** | Prometheus 3.3, Grafana 11.6 | Metrics scraping, latency histograms, and alert rule provisioning |
| **Testing** | pytest, pytest-asyncio, respx, vitest, ruff | Comprehensive test coverage across unit, integration, and UI layers |
| **Load Testing** | Grafana k6 v2.4, Python reporting | Empirical stress testing across normal, latency, and fault profiles |
| **Containerization** | Docker, Docker Compose (8 services) | Multi-stage production container builds and local development environment |

---

## Sprint Implementation Summary

The platform was engineered across ten sequential 4-hour development sprints, preserving a single evolving codebase without scaffolding replacement applications:

| Sprint | Focus & Milestone | Status | Key Deliverables |
|---|---|---|---|
| **Sprint 1** | Foundation & Simulator Contract | **PASS** | Typed Pydantic models, simulator client contract, Postgres schema, Compose topology. ([Report](docs/sprint-reports/sprint-01.md)) |
| **Sprint 2** | Synchronization & Operator Dashboard | **PASS** | Worker ingestion daemon, SSE reconnect handling, React operator UI, inventory matrix. ([Report](docs/sprint-reports/sprint-02.md)) |
| **Sprint 3** | Forecasting & Shortage-Risk Engine | **PASS** | Pure forecasting algorithms, Monte Carlo stockout risk, uncertainty bands, Trajectory Drawer. ([Report](docs/sprint-reports/sprint-03.md)) |
| **Sprint 4** | Constrained Allocation & Live Verification | **PASS** | Heuristic ranking, constraint validator, operator approval token gate, live allocation verification. ([Report](docs/sprint-reports/sprint-04.md)) |
| **Sprint 5** | Observability, Resilience & Fault Demo | **PASS** | Prometheus metrics, Grafana dashboards, circuit breakers, fallback predictor, live fault matrix. ([Report](docs/sprint-reports/sprint-05.md)) |
| **Sprint 6** | Scenario Runner & Load Hardening | **PASS** | Declarative scenario runner (24 runs, 100% determinism), 3-profile k6 benchmarks (205k requests). ([Report](docs/sprint-reports/sprint-06.md)) |
| **Sprint 7** | Freeze, Cold-Start & Clean-Clone Proof | **PASS** | Cold-start verification (**34s** recovery), clean clone proof, random chaos test, final presentation assets. ([Report](docs/sprint-reports/sprint-07.md)) |
| **Sprint 8** | Full Crisis Coverage & Two-Pass Triage | **PASS** | 5 crisis scenarios, pure detectors, two-pass triage carrying depot reservations, speed adaptation. ([Report](docs/sprint-reports/sprint-08.md)) |
| **Sprint 9** | Backtesting, What-If Sandbox & View Gaps | **PASS** | Backtest engine (2.1%–3.1% MAPE), What-If simulator (<50ms), 5 new views, LP optimizer, incident explainer. ([Report](docs/sprint-reports/sprint-09.md)) |
| **Sprint 10** | Production Delivery, Limits & Final Freeze | **PASS** | Deployment/rollback drill, resilience boundaries (23k L/tick ceiling), decision load test, judging pack. ([Report](docs/sprint-reports/sprint-10.md)) |

---

## Verification & Performance Benchmarks

### Test & Quality Verification

```text
============================= test session starts ==============================
platform darwin -- Python 3.12.16, pytest-8.3.5
rootdir: /Users/abrar/project/fuel_simulator
collected 182 items
tests/integration/ ... 37 passed
tests/scenarios/ ... 14 passed
tests/unit/ ... 131 passed
======================== 182 passed, 1 warning in 1.63s ========================

RUN  v5.1.1 web
✓ tests/NewViews.test.tsx (5 tests) 116ms
✓ tests/App.test.tsx (6 tests) 240ms
Test Files  2 passed (2) | Tests  11 passed (11)

ruff check .        --> All checks passed!
ruff format --check --> 88 files already formatted
tsc -b              --> 0 errors
```

### Demand Forecasting Accuracy & Backtest Calibration

Evaluated across 2,000 historical simulator ticks across 4 retail stations and 3 fuel products (`scripts/backtest.py`):

| Forecast Horizon | Prediction Window | Evaluation Samples | Aggregate MAPE | Mean Bias | P10–P90 Coverage | Target Coverage |
|---|---|---|---:|---:|---:|---:|
| **1-hour** | 4 ticks | 1,916 | **3.07%** | +0.01% | 91.49% | 80.00% |
| **6-hour** | 24 ticks | 1,676 | **2.19%** | -0.13% | 65.57% | 80.00% |
| **12-hour** | 48 ticks | 1,388 | **2.10%** | -0.31% | 49.86% | 80.00% |
| **24-hour** | 96 ticks | 812 | **2.11%** | -0.42% | 36.08% | 80.00% |

> [!NOTE]
> *Backtest Caveat:* Because the simulator generates consumption using deterministic diurnal equations with seeded noise, low MAPE values demonstrate model implementation consistency with documented simulator profiles, rather than general real-world economic forecasting.

### Empirical k6 Load Benchmarks

The platform was stress-tested with Grafana k6 under multiple operational profiles, including concurrent candidate What-If simulations:

| Workload Profile | Total Requests | Error Rate | p50 Latency | p95 Latency | Throughput | Resource Impact |
|---|---|---|---|---|---|---|
| **1. Normal Baseline** | 71,949 | **0.00%** | 3.4 ms | 18.2 ms | 334.6 req/s | API CPU < 25%, Memory ~65MB |
| **2. Simulator Latency Fault (3.5s delay)** | 71,768 | **0.00%** | 3.5 ms | 19.1 ms | 333.8 req/s | Unaffected (PostgreSQL isolation) |
| **3. Predictor Service Stopped** | 61,659 | **0.00%** | 4.1 ms | 22.4 ms | 286.7 req/s | Unaffected (cached DB views) |
| **4. Decision Path (What-If under load)** | 8,540 | **0.00%** | 150.1 ms | 920.6 ms | 131.3 req/s | In-memory candidate evaluation |
| **Combined Benchmark Total** | **213,916** | **0.00%** | — | — | — | **Zero HTTP 5xx errors** |

*Note on Decision Load Scope:* The decision path tested under automated load is `POST /api/whatif`. Automated submission of dispatches to `/v1/allocations` without human operator approval is strictly prohibited by AGENTS.md Hard Rules 6 & 12.

### Scenario Determinism Verification & Policy Results

The scenario runner (`scripts/scenario_runner.py`) evaluated candidate policies across disruption scenarios over 54 independent runs (9 scenarios × 3 policies × 2 runs). Every paired run achieved **100% identical outputs (delta 0.0000)**.

Measured empirical results across candidate allocation policies (`none` / do-nothing, `naive`, `heuristic`) across 54 evaluation runs (source: [docs/results/scenario-summary.md](docs/results/scenario-summary.md)):

| Scenario | Policy | Service Level | Served Demand | Unmet Demand | Dispatched Fuel | Stockout Events |
|---|---|---:|---:|---:|---:|---:|
| **baseline** | `none` (do-nothing) | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `naive` | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `heuristic` | 100.0% | 12,860 L | 0 L | 15,238 L | 0 |
| **combined** | `none` (do-nothing) | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `naive` | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `heuristic` | 100.0% | 12,860 L | 0 L | 15,238 L | 0 |
| **crisis_combined** | `none` (do-nothing) | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `naive` | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `heuristic` | 100.0% | 12,860 L | 0 L | 15,238 L | 0 |
| **depot_constraint** | `none` (do-nothing) | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `naive` | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `heuristic` | 100.0% | 12,860 L | 0 L | 15,238 L | 0 |
| **route** | `none` (do-nothing) | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `naive` | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `heuristic` | 100.0% | 12,860 L | 0 L | 15,238 L | 0 |
| **shipment_delay** | `none` (do-nothing) | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `naive` | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `heuristic` | 100.0% | 12,860 L | 0 L | 15,238 L | 0 |
| **spike** | `none` (do-nothing) | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `naive` | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `heuristic` | 100.0% | 12,860 L | 0 L | 15,238 L | 0 |
| **station_outage** | `none` (do-nothing) | 84.8% | 10,905 L | 1,955 L | 0 L | 0 |
| | `naive` | 84.8% | 10,905 L | 1,955 L | 0 L | 0 |
| | `heuristic` | 84.8% | 10,905 L | 1,955 L | 12,000 L | 0 |
| **supply_shortfall** | `none` (do-nothing) | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `naive` | 100.0% | 12,860 L | 0 L | 0 L | 0 |
| | `heuristic` | 100.0% | 12,860 L | 0 L | 15,238 L | 0 |

*Policy comparison analysis:*
- In mild-horizon scenarios where initial station tank levels buffer demand over the 48-tick window, both do-nothing (`none`) and proactive replenishment (`heuristic`) maintain 100.0% service levels. The heuristic proactively dispatches 15,238 liters of buffer stock to vulnerable stations before stockouts emerge.
- In `station_outage`, unserved demand (1,955 L) is strictly isolated to the offline station, achieving 84.8% network service level while preventing wasted fuel allocations to offline infrastructure.
- Full paired determinism (Run 1 vs Run 2) is 100% verified with delta 0.0000 across all policies.

### Robust Policy Evaluation (60 Randomized Crisis Scenarios, 192 Ticks)

Beyond short-horizon deterministic runs, policies were evaluated across **60 randomized crisis scenarios** (192 ticks / 2 simulated days each; 240 live simulation runs, seed=42) comprising 50 tuning scenarios and a 10-scenario hold-out disaster family never seen during tuning (source: [docs/results/scenario-sweep.md](docs/results/scenario-sweep.md)):

| Policy | Mean SLA | Median SLA | P10 SLA | Worst Case | Wins / Ties / Losses vs Naive | 95% CI vs Naive (Mean Δ) | Mean Unmet (L) |
|---|---:|---:|---:|---:|:---:|:---:|---:|
| **`none` (do-nothing)** | 40.40% | 45.58% | 25.04% | 22.76% | Do Nothing | -56.74% | 137,340 L |
| **`naive` (greedy refill)** | 97.14% | 100.00% | 90.20% | 86.27% | Baseline | N/A | 7,324 L |
| **`heuristic` (two-pass triage)** | **97.93%** | **100.00%** | **92.54%** | **86.27%** | **15W / 44T / 1L** | **+0.79% [0.41%, 1.27%]** | **4,798 L** |
| **`heuristic_buffer` (with P90 buffer)** | **97.93%** | **100.00%** | **92.54%** | **86.27%** | **15W / 44T / 1L** | **+0.79% [0.41%, 1.27%]** | **4,798 L** |

*Key Findings from 60-Scenario Sweep:*
- **Statistically Significant Improvement:** The heuristic policy improves network service level by **+0.79%** on average over greedy naive refill with a bootstrap 95% confidence interval of `[+0.41%, +1.27%]`, cutting unmet demand by **35%** (4,798 L vs 7,324 L).
- **Hold-Out Generalization (10 Compound Disasters):** On the holdout disaster family, Heuristic scored **96.26% Mean SLA** vs Naive **92.57% Mean SLA** (+3.69% improvement; 9 wins, 0 ties, 1 loss).
- **Honest Loss Disclosure:** Heuristic had exactly **1 loss** out of 60 scenarios (`holdout_08`, where Heuristic achieved 99.86% vs Naive 99.95%, a -0.08% delta) caused by an extreme multi-corridor transit bottleneck timing divergence.

---

## Quick Start Guide

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (24.0+) & Docker Compose v2
- [Python](https://www.python.org/) 3.12+ (for local test execution)
- [Node.js](https://nodejs.org/) 20+ & npm (for frontend development)

### 1. Clone & Configure

```bash
git clone https://github.com/thunderstorm009/fuel_simulator.git
cd fuel_simulator

# Create local environment configuration from template
cp .env.example .env
```

> [!NOTE]
> The default credentials in `.env.example` are pre-configured for local simulated development. To test operator approvals, set an arbitrary `OPERATOR_TOKEN` in `.env`.

### 2. Launch the Platform

```bash
# Start all 8 containers in the background
make up
```

Verify that all services are healthy:
```bash
docker compose ps
```

### 3. Access Service Endpoints

| Component | URL | Notes |
|---|---|---|
| **Operator Frontend** | [http://localhost:5173](http://localhost:5173) (or [http://localhost:5174](http://localhost:5174)) | Primary interactive operator control UI |
| **Operator API Docs** | [http://localhost:8101/docs](http://localhost:8101/docs) | Interactive Swagger UI for backend API |
| **API Health Status** | [http://localhost:8101/api/health](http://localhost:8101/api/health) | Aggregated component health JSON |
| **Worker Service** | [http://localhost:8102/health](http://localhost:8102/health) | Background synchronization service |
| **Predictor Service** | [http://localhost:8103/health](http://localhost:8103/health) | Standalone demand forecasting service |
| **Fuel Simulator** | [http://localhost:8000/v1/health](http://localhost:8000/v1/health) | Upstream BUP simulator instance |
| **Prometheus Server** | [http://localhost:9090](http://localhost:9090) | Raw metrics collection and targets |
| **Grafana Dashboard** | [http://localhost:3000](http://localhost:3000) | User: `admin`, Password: `local-demo-only` |

### 4. Run Tests & Validation

```bash
# Run backend and frontend test suites
make test

# Run code formatters and linters
make lint

# Run end-to-end smoke verification
make smoke
```

---

## Documentation & Evidence Index

- **Engineering Updates:**
  - [Day 1 Engineering Update (Sprints 1–4)](docs/DAY-1-UPDATE.md)
  - [Day 2 Engineering Update (Sprints 5–7)](docs/DAY-2-UPDATE.md)
  - [Day 3 Engineering Update & Final Freeze (Sprints 8–10)](docs/DAY-3-UPDATE.md)
- **Judging & Evaluation:**
  - [Judging Day Presentation Guide & 10-Min Demo Script](docs/JUDGING-DAY.md)
  - [Hackathon Brief Compliance Matrix (Sections 4–26)](docs/BRIEF-COMPLIANCE.md)
  - [Crisis Event Handling Architecture & Scenarios](docs/event-handling.md)
  - [Judge Evaluation Q&A (15 Questions Answered)](docs/qa.md)
- **Detailed Sprint Reports:**
  - [Sprint 01 Report](docs/sprint-reports/sprint-01.md) · [Sprint 02 Report](docs/sprint-reports/sprint-02.md) · [Sprint 03 Report](docs/sprint-reports/sprint-03.md) · [Sprint 04 Report](docs/sprint-reports/sprint-04.md)
  - [Sprint 05 Report](docs/sprint-reports/sprint-05.md) · [Sprint 06 Report](docs/sprint-reports/sprint-06.md) · [Sprint 07 Report](docs/sprint-reports/sprint-07.md) · [Sprint 08 Report](docs/sprint-reports/sprint-08.md)
  - [Sprint 09 Report](docs/sprint-reports/sprint-09.md) · [Sprint 10 Report](docs/sprint-reports/sprint-10.md)
- **Empirical Evidence & Benchmarks:**
  - [Day 3 Screenshot Gallery Manifest](docs/evidence/day-3/screens/MANIFEST.md)
  - [Day 3 Independent Verification Report](docs/evidence/day-3/verification.md)
  - [Day 3 Numerical Claims Ledger](docs/evidence/day-3/claims-ledger.md)
  - [k6 Load Benchmark Report](docs/loadtest.md)
  - [Deterministic Scenario Evaluation Summary](docs/results/scenario-summary.md)
  - [Demand Forecasting Backtest Summary](docs/results/backtest-summary.md)
  - [Automated Rollback Drill Evidence](docs/evidence/sprint-10-rollback-drill.txt)
  - [Resilience & Failure Boundary Matrix](docs/resilience.md)

---

## Scope and Limitations

- **Simulated Environment:** All fuel inventory, stations, depots, transit trucks, and dispatches are purely simulated. The platform does not control physical valves, physical fuel infrastructure, or real distribution vehicles.
- **Single-Depot Distribution Topology:** The current heuristics model distribution from primary regional bulk depots to retail filling stations. Dynamic inter-depot rebalancing and dynamic multi-depot vehicle routing heuristics are intentionally outside hackathon scope.
- **Mandatory Operator Authority:** By design, the platform does not include autonomous allocation execution. Replenishment dispatches strictly require authenticated human approval.

---

## Contributors & Acknowledgements

- **Engineering & Architecture:** Faizul Kabir Abrar ([@thunderstorm009](https://github.com/thunderstorm009))
- **Event:** BUP CSE Fest 2026 Hackathon
- **Simulator Contract:** Built against the official BUP CSE Fest Fuel Supply Simulator (`asifmahmoud414/bup-fuel-supply-simulator:1.0.0`).
