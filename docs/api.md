# API reference

The API is a database boundary: it does not call the simulator. The worker owns simulator REST and SSE traffic and persists validated data in PostgreSQL. All operator-facing domain responses include `simulated: true`.

## API service

Base URL: `http://localhost:8101`.

| Method | Path | Behavior |
|---|---|---|
| GET | `/health` | API liveness. |
| GET | `/metrics` | Prometheus request/latency and service-health metrics. |
| GET | `/api/state` | Latest persisted simulator snapshot and freshness/stale metadata. |
| GET | `/api/data-health` | Snapshot age, status and stale marker. |
| GET | `/api/events` | Latest simulator events and open platform incidents. |
| GET | `/api/metrics-summary` | Simulator service-level and allocation metrics from the latest snapshot. |
| GET | `/api/risks` | Latest forecast per station/fuel pair and freshness. |
| GET | `/api/risks/{station_id}/{fuel_type}/trajectory` | Persisted inventory trajectory and risk details for one pair. |
| GET | `/api/recommendations` | Persisted recommendations, explanations and execution status. |
| GET | `/api/decisions` | Operator approval/rejection history. |
| POST | `/api/recommendations/{id}/approve` | Records approval intent; requires `X-Operator-Token`. It does not call the simulator. Repeating approval is idempotent. |
| POST | `/api/recommendations/{id}/reject` | Records rejection and required non-blank reason; requires `X-Operator-Token`. |

The operator token is read from `OPERATOR_TOKEN`. A missing repository returns HTTP 503. Unknown forecast pairs return HTTP 404; invalid fuel types return HTTP 422. CORS is limited to the configured `CORS_ORIGIN` value(s).

## Worker service

Base URL: `http://localhost:8102`.

- `GET /health` reports worker liveness.
- `GET /metrics` exposes ingestion, forecast, recommendation, allocation-executor, simulator-client, SSE and health metrics.

The worker polls validated simulator REST resources and uses SSE only as a refetch hint. The approved-allocation executor fetches fresh REST state and revalidates immediately before its only simulator write: `POST /v1/allocations`.

## Predictor service

Base URL: `http://localhost:8103`.

- `GET /health` reports predictor service liveness.
- `GET /metrics` exposes service-health metrics.

The independent service is currently a health/metrics skeleton. Forecasting is computed by the worker using shared code; the worker-to-predictor request/fallback path is planned for Sprint 5 and is not described as implemented here.

## Frontend API configuration

The web build reads `VITE_API_URL` (default `http://localhost:8101`). The frontend talks to the API only; it does not call the simulator or predictor directly.
