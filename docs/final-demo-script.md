# Final demo script (8-10 minutes; runtime rehearsal pending)

This walkthrough is prepared but has not been rehearsed against the current Compose stack. Do not approve a recommendation or submit an allocation unless the operator explicitly authorizes that specific live action.

| Time | Step and command | Expected visual | Recovery line |
|---|---|---|---|
| 0:00–1:00 | Start with `make up`; check `curl -fsS http://localhost:8101/api/health`. | SIMULATED app, component health and data age. | If the daemon or build registry fails, show the saved sprint evidence and state the exact missing runtime check. |
| 1:00–2:00 | Open Overview, Network, and Stockout Risk. | Inventory, route state, risk matrix and freshness. | Refresh once; if API is down, use documented cached-state behavior and show worker/API logs. |
| 2:00–3:00 | Inspect a persisted recommendation without approving it. | Constraints, explanation, alternatives, confidence and review badge. | If no recommendation is present, explain that generation follows a distinct validated snapshot; do not fabricate one. |
| 3:00–4:00 | Show `GET /api/decisions`, API/worker `/metrics`, and Grafana. | Approval audit, low-cardinality metrics and provisioned dashboard. | If Grafana is unavailable, show Prometheus targets and `/metrics`; label runtime as unverified. |
| 4:00–6:00 | Run one reversible fault scene using `bash scripts/fault_demo.sh` only on a dedicated demo simulator. | Stale/degraded state, retained snapshot, then recovery. | The script clears the active fault on exit. If recovery is delayed, wait for the next REST poll and show data age. |
| 6:00–7:00 | In an isolated demo stack, stop/start predictor and inspect fallback metrics. | Confidence cap 0.4, `needs_review`, fallback incident/metric. | Restart predictor and wait for a successful remote forecast. |
| 7:00–8:00 | Present load-test and scenario results only if real reports exist under `docs/results/`. | Measured numbers with raw summary path. | Current resumed run has no measurements; say so directly. |
| 8:00–9:00 | Summarize limitations and answer questions. | Separate historical evidence from current-run evidence. | Keep Sprint 4 live approval/arrival/replay open until operator-authorized evidence exists. |

Roles: driver and narrator; add a fault injector only for a dedicated simulator instance. Preserve a backup recording after a complete rehearsal. Current demo runtime rehearsal and three no-code-repeat runs are NOT-RUN.
