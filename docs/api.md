# API reference

The API is a database boundary: it does not call the simulator. The worker owns simulator REST and SSE traffic and persists validated data in PostgreSQL. All operator-facing domain responses include `simulated: true`.

## API service

Base URL: `http://localhost:8101`.

| Method | Path | Behavior |
|---|---|---|
| GET | `/health` | API liveness. |
| GET | `/metrics` | Prometheus request/latency and service-health metrics. |
| GET | `/api/state` | Latest persisted simulator snapshot, freshness metadata (`ticks_per_second`, `snapshot_age_ticks`, `speed_warning`). |
| GET | `/api/data-health` | Snapshot age, status and stale marker. |
| GET | `/api/health` | Database-backed component health and API latency/error summary. |
| GET | `/api/events` | Latest simulator events and open platform incidents. |
| GET | `/api/incidents` | Deduplicated anomaly/incident detections from the database (`?status=open|resolved|all`). |
| GET | `/api/incidents/{id}/summary` | Plain-language incident explanation (template/LLM fallback), labelled `AI-generated summary of simulated data`. |
| GET | `/api/depots/risk` | Forward 24-hour depot supply cover, scheduled arrivals, projected demand, and bottleneck indicators. |
| GET | `/api/regional-demand` | Regional aggregated demand, served liters, unmet liters, and service levels across recent ticks. |
| GET | `/api/evaluation/summary` | Offline benchmark and backtest results (MAPE, bias, interval coverage across 1h, 6h, 12h, 24h horizons) and scenario outcomes. |
| POST | `/api/whatif` | Simulates candidate allocation impact on station trajectory, stockout runway, and depot cover without DB/simulator writes. |
| GET | `/api/metrics-summary` | Simulator service-level and allocation metrics from the latest snapshot. |
| GET | `/api/stream` | Read-only Server-Sent Events (SSE) stream delivering push invalidation hints (`snapshot`, `forecasts`, `recommendations`, `incidents`). Heartbeat `: ping\n\n` every 15s. |
| GET | `/api/version` | Platform component versions, tag, and currently active recommendation policy. |
| GET | `/api/policy` | Currently active recommendation policy, history of changes, and simulated flag. |
| POST | `/api/policy` | Selects active policy (`heuristic`, `heuristic_buffer`, `optimizer`); requires `X-Operator-Token`, audited reason, and is rate-limited. |
| GET | `/api/risks` | Latest forecast per station/fuel pair and freshness. |
| GET | `/api/risks/{station_id}/{fuel_type}/trajectory` | Persisted inventory trajectory and risk details for one pair. |
| GET | `/api/recommendations` | Persisted recommendations, explanations and execution status. |
| GET | `/api/decisions` | Operator approval/rejection history. |
| POST | `/api/recommendations/{id}/approve` | Records approval intent; requires `X-Operator-Token`. It does not call the simulator. Repeating approval is idempotent. |
| POST | `/api/recommendations/{id}/reject` | Records rejection and required non-blank reason; requires `X-Operator-Token`. |
| POST | `/api/chaos/forecast-fail` | Toggles predictor failure for demonstrations; requires `X-Operator-Token`. |

The operator token is read from `OPERATOR_TOKEN`. A missing repository returns HTTP 503. Unknown forecast pairs return HTTP 404; invalid fuel types return HTTP 422. CORS is limited to the configured `CORS_ORIGIN` value(s).

## Worker service

Base URL: `http://localhost:8102`.

- `GET /health` reports worker liveness.
- `GET /metrics` exposes ingestion, forecast, recommendation, allocation-executor, simulator-client, SSE and health metrics.

The worker polls validated simulator REST resources and uses SSE only as a refetch hint. The approved-allocation executor fetches fresh REST state and revalidates immediately before its only simulator write: `POST /v1/allocations`.

## Predictor service

Base URL: `http://localhost:8103`.

- `GET /health` reports predictor service liveness.
- `POST /predict` accepts a validated snapshot slice, station/fuel pair, and seed; returns forecast, trajectory, drivers, and source.
- `GET /metrics` exposes service-health metrics.

The service uses the shared pure risk implementation. The worker calls it with a 1.5-second default timeout and independent breaker, then uses a profile-only local fallback on service, timeout, or schema failures. Fallback output has confidence capped at 0.4 and requires review.

## Frontend API configuration

The web build reads `VITE_API_URL` (default `http://localhost:8101`). The frontend talks to the API only; it does not call the simulator or predictor directly.
