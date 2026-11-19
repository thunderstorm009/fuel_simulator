# Project plan: 28 hours, seven sprints, one repository

## 1. Product outcome
An operator-facing platform that shows live simulated fuel state, forecasts hours to stockout with uncertainty, recommends feasible allocations with explanations, lets a human approve or reject, submits approved shipments to the simulator, and keeps working through simulator faults and its own component failures. A notebook, static dashboard or chatbot alone does not meet the brief.

## 2. Key insight
Stations are refilled only by our allocations. Depots are refilled by 22 scheduled supply arrivals. With no action, stations run dry in roughly a simulated day. The platform's value is measured against that do-nothing baseline.

## 3. Architecture (current implementation)
The six platform services remain separate: simulator REST/SSE feeds the worker; the worker persists validated state and domain results in PostgreSQL; the API serves database-backed operator routes; the React frontend calls the API; Prometheus scrapes API, worker and predictor; Grafana uses Prometheus. The predictor currently exposes health/metrics only. Forecasting runs in the worker with shared core logic; a remote predictor/fallback path is not yet implemented.

- `backend/api/`: API, routes, database access and schema.
- `backend/worker/`: ingestion, forecast/recommendation jobs, SSE and approved execution.
- `backend/shared/core/`: pure models, simulator client, forecast/risk/policy/validator logic and shared metrics.
- `intel/predictor/`: independent predictor service.
- `web/`: React application organized by feature.
- `observability/`: Prometheus and Grafana provisioning.
- `scripts/`, `tests/`: operational scripts and unit/integration/scenario suites.

The topology is defined in `docker-compose.yml`; API, worker and predictor are not combined into one runtime.

## 4. Application API (confirm against code)
GET /api/state, /api/data-health, /api/events, /api/risks, /api/risks/{station}/{fuel}/trajectory, /api/recommendations, /api/decisions, /api/health; POST /api/recommendations/{id}/approve and /reject (operator token); POST /api/chaos/forecast-fail (operator token, demo only).

## 5. Schedule
| Sprint | Hours | Outcome | Tag |
|---|---|---|---|
| 1 | 0-4 | Simulator explored, contract and DB schema, compose and CI skeleton | sprint-1 |
| 2 | 4-8 | Resilient simulator client, ingestion, read API, live dashboard | sprint-2 |
| 3 | 8-12 | Forecast, Monte Carlo risk, risk UI | sprint-3 |
| 4 | 12-16 | Validator, allocation policy, explanations, approval, executor, recommendations UI | sprint-4 |
| 5 | 16-20 | Metrics, Grafana, health, predictor and fallback, fault demo | sprint-5 |
| 6 | 20-24 | Scenario runner, load test, CI hardening, main docs | sprint-6 |
| 7 | 24-28 | Freeze, cold start, chaos, demo, final docs, release | sprint-7 |

Rhythm inside each sprint: 0:00-0:20 read PROGRESS and plan; 0:20-3:10 build; 3:10-3:40 test, integrate, cross-review; 3:40-4:00 gate, report, tag.

## 6. Priorities
P0: simulator connectivity, live dashboard, explainable stockout risk, feasible recommendations, human approval, safe submission, crisis demo, fault fallback, `docker compose up`.
P1: persistence and audit, metrics and Grafana, tests and CI, load test, scenario comparison, complete docs.
P2: LP optimizer, LLM summaries, what-if endpoint, extra charts.
Cut order when behind: P2, then polish, then extra charts. Never cut: hard constraints, re-validation, human approval, stale-data handling, fault demo, tests of the executor.

## 7. Sprint acceptance gates
Sprint acceptance prompts are retained in the local-only `.local/prompts/` workspace. A sprint passes only when every acceptance item has real command output or evidence in its report.

## 8. Scoring map
Product and UX 20, Intelligence 20, Architecture 15, DevOps 15, Resilience 15, Observability and performance 10, Demo 5. Most points come from a working, resilient, observable system, not from model sophistication.

## 9. End-of-sprint presentation (five minutes)
1. Operator problem solved. 2. What changed in architecture and code. 3. Live demo. 4. Evidence (tests, outputs). 5. What failed, remains risky, and next sprint's dependency.
