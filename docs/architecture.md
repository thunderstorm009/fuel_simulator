# System Architecture & Technical Specification

The Fuel Supply Intelligence & Resilience Platform is architected as an integrated, multi-container system adhering to strict boundaries: **the API never talks to the simulator; the worker owns external I/O; pure domain logic has no side-effects; human approval is mandatory for simulator mutations; and REST is truth while SSE serves as an advisory invalidation hint.**

---

## 1. High-Level Component Topology

```mermaid
flowchart TD
  subgraph SimulatorBoundary["External Simulator Boundary"]
    SIM["Official BUP Simulator<br/>(REST :8000 + SSE /v1/events)"]
  end

  subgraph WorkerContainer["Worker Service (:8102)"]
    W_ING["Ingestion Job<br/>(REST Poller + SSE Invalidation)"]
    W_REC["Recommendation Runner<br/>(Two-Pass Heuristic / LP / Buffer)"]
    W_EXEC["Outbox Executor<br/>(Re-validator + Idempotent Submitter)"]
    W_BREAKER["Circuit Breaker<br/>(5 failures, 10s cooldown)"]
  end

  subgraph Storage["Persistence Layer"]
    DB[("PostgreSQL 16 (:5432)<br/>- snapshots & trajectory forecasts<br/>- recommendations & decisions<br/>- incidents & audit logs<br/>- LISTEN/NOTIFY platform_events")]
  end

  subgraph PredictorContainer["Predictor Service (:8103)"]
    PRED["FastAPI Predictor<br/>- Diurnal baseline model<br/>- Vectorized Monte Carlo (300 paths)<br/>- Event-Aware v1.2.0 calibration"]
  end

  subgraph APIContainer["API Service (:8101)"]
    API["FastAPI Backend (4 Uvicorn Workers)<br/>- Sub-millisecond pre-serialized byte cache<br/>- ETag / 304 Not Modified<br/>- In-memory What-If counterfactual engine<br/>- SSE EventBroadcaster (/api/stream)"]
  end

  subgraph WebFrontend["Web Client (:5173)"]
    WEB["React 19 / TypeScript / Vite<br/>- TanStack Query (invalidation-based)<br/>- Recharts trajectory visualization<br/>- Interactive guided tour<br/>- Accessible WCAG 2.1 AA UI"]
  end

  subgraph Telemetry["Observability Stack"]
    PROM["Prometheus (:9090)<br/>Scrapes API, Worker, Predictor"]
    GRAF["Grafana (:3000)<br/>4-tier operational dashboards"]
    AM["Alertmanager (:9093)<br/>(Profile: 'alerts')"]
  end

  SIM -->|REST poll & hints| W_ING
  W_ING -->|validated state| DB
  W_REC -->|query snapshot| DB
  W_REC -->|POST /predict| PRED
  PRED -.->|outage fallback| W_REC
  W_REC -->|persist proposals| DB
  W_ING -.->|"pg_notify('platform_events')"| DB
  DB -.->|"LISTEN 'platform_events'"| API
  API -->|GET /api/stream (SSE push)| WEB
  WEB -->|REST queries on push hint| API
  API -->|read-only DB queries| DB
  WEB -->|POST /api/recommendations/:id/approve| API
  API -->|record decision intent| DB
  W_EXEC -->|poll approved & unsubmitted| DB
  W_EXEC -->|fresh non-stale read| SIM
  W_EXEC -->|re-validate all 5 constraints| W_EXEC
  W_EXEC -->|POST /v1/allocations| SIM

  API -->|metrics| PROM
  W_ING -->|metrics| PROM
  PRED -->|metrics| PROM
  PROM --> GRAF
  PROM -.-> AM
```

---

## 2. Sequence Diagram: Snapshot Ingestion to Recommendation Proposal

```mermaid
sequenceDiagram
  autonumber
  actor Simulator as BUP Simulator (:8000)
  participant Worker as Worker (:8102)
  participant DB as PostgreSQL (:5432)
  participant Predictor as Predictor (:8103)
  participant API as API (:8101)
  participant UI as Web Frontend (:5173)

  Simulator-->>Worker: SSE event hint (or periodic 5s poll)
  Worker->>Simulator: GET /v1/instance & GET /v1/state
  Simulator-->>Worker: HTTP 200 (Snapshot + X-Simulator-Stale header)
  Worker->>Worker: Validate schema via core.models.Snapshot
  Worker->>DB: INSERT snapshot & depot risks
  Worker->>Predictor: POST /predict (station demand & uncertainty)
  alt Predictor Healthy
    Predictor-->>Worker: Forecast trajectories (P10, P50, P90, Brier)
  else Predictor Outage or Timeout
    Worker->>Worker: Local baseline fallback (cap confidence at 0.4, mark review)
  end
  Worker->>DB: INSERT forecasts
  Worker->>Worker: Execute Active Policy (core.policy.HeuristicPolicy)
  Worker->>Worker: Validate proposals via pure core.validator.validate
  Worker->>DB: INSERT recommendations (status: PROPOSED, with UUID idempotency_key)
  Worker->>DB: NOTIFY platform_events ('recommendations', 'forecasts')
  DB-->>API: PostgreSQL LISTEN trigger
  API-->>UI: SSE Push Invalidation Event ('recommendations')
  UI->>API: GET /api/recommendations (fresh fetch)
  API-->>UI: Display updated urgency-ranked allocation cards
```

---

## 3. Sequence Diagram: Interactive What-If Simulation

```mermaid
sequenceDiagram
  autonumber
  actor Operator as Human Operator
  participant UI as Web Frontend
  participant API as API (:8101)
  participant Core as Pure Core Engine (in-memory)

  Operator->>UI: Click "Simulate Candidate (What-If)"
  Operator->>UI: Adjust quantity slider (e.g., 5,000 L -> 10,000 L)
  UI->>API: POST /api/whatif (candidate allocation payload)
  Note over API: API serves directly from memory / cached models.<br/>ZERO database writes. ZERO simulator I/O.
  API->>Core: core.what_if.simulate_what_if(snapshot, candidate)
  Core->>Core: Pure constraint validation (core.validator)
  Core->>Core: Counterfactual inventory projection (hours-to-stockout delta)
  Core-->>API: WhatIfResponse (valid, runway before/after, violated constraints)
  API-->>UI: HTTP 200 (executed in <50ms unloaded, ~288ms under load)
  UI-->>Operator: Real-time counterfactual runway visualization
```

---

## 4. Sequence Diagram: Human Approval to Simulator Execution

```mermaid
sequenceDiagram
  autonumber
  actor Operator as Human Operator
  participant UI as Web Frontend
  participant API as API (:8101)
  participant DB as PostgreSQL (:5432)
  participant Worker as Outbox Executor (:8102)
  actor Simulator as BUP Simulator (:8000)

  Operator->>UI: Input operator token & name, click "Approve"
  UI->>API: POST /api/recommendations/:id/approve (token, name)
  API->>API: Verify token against OPERATOR_TOKEN environment variable
  API->>DB: BEGIN TRANSACTION<br/>UPDATE recommendations SET status = 'APPROVED'<br/>INSERT INTO decisions (recommendation_id, action, actor)<br/>COMMIT
  API->>DB: NOTIFY platform_events ('decisions')
  API-->>UI: HTTP 200 (Decision recorded)

  Note over Worker: Worker owns ALL simulator writes.<br/>Strict outbox pattern guarantees idempotency.
  Worker->>DB: Poll approved recommendations (status: 'APPROVED')
  Worker->>Simulator: GET /v1/instance & GET /v1/state (fresh read)
  Simulator-->>Worker: HTTP 200 Snapshot (check X-Simulator-Stale: false)
  Worker->>Worker: RE-VALIDATE all 5 physical constraints against fresh state!
  alt Constraint Violated or Stale State
    Worker->>DB: UPDATE recommendations SET status = 'REJECTED' (reason: constraint_violated)
    Worker->>DB: Log incident & abort submission
  else Invariants Satisfied
    Worker->>Simulator: POST /v1/allocations (payload + stored permanent idempotency_key)
    Simulator-->>Worker: HTTP 200 Allocation Created
    Worker->>DB: UPDATE recommendations SET status = 'SUBMITTED'
    Worker->>DB: NOTIFY platform_events ('recommendations')
  end
```

---

## 5. Sequence Diagram: Server-Sent Events (SSE) Push & Polling Fallback

```mermaid
sequenceDiagram
  autonumber
  participant UI as React Web Client
  participant API as API SSE Stream (/api/stream)
  participant DB as PostgreSQL LISTEN/NOTIFY
  participant Worker as Worker Ingestion

  UI->>API: GET /api/stream (Accept: text/event-stream)
  API->>UI: HTTP 200 (SSE connected, header: text/event-stream)
  UI->>UI: Display "● LIVE PUSH" badge in header; DISABLE periodic polling

  loop Every 15 seconds
    API-->>UI: : ping\n\n (keepalive heartbeat)
  end

  Worker->>DB: NOTIFY platform_events, '{"event_type": "snapshot", "tick": 185}'
  DB-->>API: LISTEN callback received
  API-->>UI: data: {"event_type": "snapshot", "timestamp": "...", "data": {"tick": 185}}\n\n
  UI->>API: TanStack Query selectively invalidates ['snapshot'] query

  alt Network Drop or API Restart
    API--xUI: Connection closed
    UI->>UI: Switch badge to "○ POLLING FALLBACK"
    UI->>UI: Activate 10-second background polling timer
    loop Exponential Backoff Reconnection
      UI->>API: Attempt GET /api/stream
    end
    API-->>UI: Connection restored; revert to "● LIVE PUSH"
  end
```

---

## 6. Sequence Diagram: Fault Detection, Circuit Breakers & Policy Rollback

```mermaid
sequenceDiagram
  autonumber
  actor Admin as Fault Injector / Simulator
  participant Worker as Worker
  participant Breaker as Circuit Breaker
  participant Policy as PolicyRunner
  participant DB as PostgreSQL
  participant Webhook as Webhook Receiver / Alertmanager

  Admin->>Worker: Simulator injects 503 Service Unavailable
  Worker->>Breaker: Record failure (tripped after 5 consecutive failures)
  Breaker->>Worker: State = OPEN (cooldown 10s)
  Worker->>DB: Mark data_status = 'DEGRADED', record incident
  Worker->>DB: NOTIFY platform_events ('incidents')
  Worker-->>Webhook: Alert 'SimulatorCircuitBreakerOpen' (severity: critical)

  Note over Policy: Dynamic Policy Switch (e.g. candidate LP / Buffer policy)
  Policy->>Policy: Candidate policy executes
  alt Policy Exception, Timeout (>0.5s), or Validator Violation
    Policy->>Policy: AUTOMATIC ROLLBACK TO HeuristicPolicy!
    Policy->>DB: INSERT INTO policy_changes (actor: 'system:rollback', reason: 'violation')
    Policy->>DB: INSERT INTO incidents (type: 'policy_rollback')
    Policy->>Policy: Discard invalid proposals (zero violations emitted!)
  end

  Admin->>Worker: Clear fault
  Worker->>Breaker: Probe simulator health (single test request)
  Breaker->>Breaker: State = CLOSED
  Worker-->>Webhook: Alert 'SimulatorCircuitBreakerOpen' RESOLVED
```

---

## 7. Performance & Optimization Architecture

The API service incorporates five distinct optimization layers introduced in Sprint 12 that tripled throughput and reduced database CPU consumption by 89%:

1. **Uvicorn Concurrency:** 4 independent worker processes bound to port 8101.
2. **Connection Pooling:** PostgreSQL connection pool enlarged to 20 connections per process with 30s recycle.
3. **Composite Database Indexes:**
   - `idx_forecasts_snapshot_station_fuel ON forecasts (snapshot_id, station_id, fuel_type)`
   - `idx_depot_risks_snapshot_depot ON depot_risks (snapshot_id, depot_id)`
   - `idx_snapshots_tick_desc ON snapshots (tick DESC)`
   (Reduced query planning and execution times from 15.3ms to 0.103ms — a 149x speedup).
4. **Sub-Millisecond Byte Caching:** In-memory pre-serialized UTF-8 byte cache for `GET /api/overview` and `GET /api/forecasts` with automatic eviction on state changes.
5. **HTTP ETag / 304 Not Modified:** Client-side cache validation eliminates redundant payload transfers when underlying ticks have not advanced.
