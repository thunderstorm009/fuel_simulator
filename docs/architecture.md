# Architecture (planned design: correct it to match the code as you build)

```
Simulator :8000 --REST poll + SSE hint--> WORKER (ingest, forecast job, recommend job, executor)
WORKER --> PREDICTOR (thin FastAPI around core forecast; baseline fallback if down)
WORKER --> POSTGRES <-- API (FastAPI, reads DB only) <-- FRONTEND (React)
Prometheus scrapes api, worker, predictor --> Grafana
```

## Components
- core/: pure logic and shared models. sim_client is the only I/O module. Contains models, forecast, risk, policies, validator, explain.
- worker/: owns all simulator traffic. Loops: ingest, forecast_job, recommend_job, executor. SSE client triggers refresh only.
- predictor/: POST /predict wrapper over core forecast so 'prediction service unavailable' can be demonstrated with docker stop.
- api/: operator API. Reads Postgres only. Approve and reject write decisions; the executor submits.
- frontend/: Overview, Risk matrix, Recommendations, Decision history, Health.
- infra/: Prometheus config, Grafana provisioning and dashboard JSON.

## Why the split
A slow or failing simulator hurts only the worker. The API serves the last good snapshot with its age, so the dashboard stays usable in degraded mode.

## Recommendation lifecycle
PROPOSED -> APPROVED -> SUBMITTED -> IN_TRANSIT -> ARRIVED; or REJECTED, EXPIRED, FAILED. The executor re-reads fresh state and re-validates before every submit.

## Data status (drives banner, alerts, confidence)
HEALTHY: last good snapshot under 15s, not stale, breaker closed. DEGRADED: stale header, breaker half-open, 15-120s old, or a fallback active. OFFLINE: no good snapshot for over 120s.

## Allowed adaptations
Fewer containers (worker as a background task of the API) if recorded in docs/decisions.md. Keep the predictor separate. No Kubernetes, Kafka or RL.
