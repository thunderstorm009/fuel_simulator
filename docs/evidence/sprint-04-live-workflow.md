# Sprint 4 live workflow — pending operator approval

Date: 2026-11-20 (Asia/Dhaka) | State: **Approval not recorded; no allocation POST performed**

## Environment and current simulator state

- Existing Docker Compose project was started with `PREDICTOR_URL=http://predictor:8103 FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 docker compose up --build -d`. No `down`, volume deletion, or simulator reset was run.
- All eight Compose services reported `running healthy`; frontend returned HTTP 200 at `http://localhost:5174/`.
- API `/api/data-health`: `data_status=HEALTHY`, `stale=false`, data age about 1.3 seconds at the check.
- Simulator `/v1/instance`: baseline scenario, tick 134, 15-minute ticks, **PAUSED**.
- Simulator `/v1/allocations`: `[]`; API `/api/decisions`: `[]`.
- Worker generated six new proposals at tick 134 after the simulator advanced from tick 114 to tick 134 using `/admin/run`. It was paused with `/admin/pause` before human review. No allocation was submitted.
- Prometheus targets for API, worker, and predictor all reported `health=up`. Grafana `/api/search` returned HTTP 401 when called without credentials; dashboard content was not verified in this check.
- At the latest health check, API aggregate status was `OFFLINE` solely because the `decision_engine` heartbeat age was about 196 seconds. Backend, database, predictor, and simulator components were healthy; snapshot data remained `HEALTHY` and under one second old. The simulator is intentionally paused while the operator reviews the proposal, so no new forecast/decision-engine cycle has run.
- Current simulator metrics at tick 134: service level 0.668096, unmet demand 42,425.902 L, served demand 85,399.852 L, allocation failures 0. These are the simulator's cumulative values at the captured tick, not a projection.
- A separate runtime check found repeated SSE reconnects despite HTTP 200 and active REST polling. Root cause was the worker's 3s REST read timeout being applied to an SSE endpoint with a documented 15s keepalive. A separate `SIM_STREAM_READ_TIMEOUT_S=20` was added and the worker image rebuilt. Over the following 22s, worker logs showed no `simulator_stream_disconnected` events and `worker_sse_reconnects_total` stayed at one; the selected recommendation remained PROPOSED and simulator allocations stayed empty.
- After this regression fix: `make test` reported 124 Python tests and 3 frontend tests passed; `make lint` passed including Ruff, formatting, TypeScript, and Vite build. `docker compose config -q`, `git diff --check`, Python compileall, and shell syntax checks passed.

## Candidate presented for approval

Recommendation `1cb05b67-3440-45e5-a6d8-398482678d8c`, created at `2026-11-20T08:45:11.958424Z`, status `PROPOSED`, current snapshot tick 134. The API row was freshly generated from the running simulator state; it is not one of the prior-day proposals.

Exact stored request body:

```json
{
  "source_depot_id": "depot-patiya",
  "destination_station_id": "station-coxsbazar",
  "route_id": "route-patiya-coxsbazar",
  "fuel_type": "DIESEL",
  "quantity": 6000.0,
  "idempotency_key": "rec-cd2db2c8-5d87-4bc7-876c-d06373049a8a"
}
```

## Constraint revalidation on the fresh snapshot

| Simulator validation rule | Live facts for this request | Result |
|---|---|---|
| Idempotency key | Key not present in the simulator's zero allocations; exact body is persisted | PASS |
| Entity existence | Patiya depot, Cox's Bazar station, and `route-patiya-coxsbazar` exist | PASS |
| Route matches endpoints | Route source is Patiya and destination is Cox's Bazar | PASS |
| Depot open | Patiya status `OPEN` | PASS |
| Station open | Cox's Bazar status `OPEN` | PASS |
| Route available | Status `AVAILABLE` | PASS |
| Route shipment maximum | 6,000 L requested; route maximum 6,000 L | PASS |
| Depot inventory | Patiya DIESEL inventory 81,000 L | PASS |
| Dispatch capacity | 0 L allocated this tick; 11,000 L/tick limit | PASS |
| Destination capacity | Cox's Bazar DIESEL inventory 0 L; capacity/free space 12,000 L | PASS |

The local `core.validator.validate()` call returned no violations. Data status was `HEALTHY`, stale was false, and the worker's executor will re-fetch and revalidate again after approval.

Route transit is 3 ticks. The proposal estimates arrival at tick 138, from departure tick 135, if approved and the simulator advances normally. The simulator is paused now to keep tick 134 stable during review. The proposal's `expires_tick` is 138.

Risk caveat: Cox's Bazar DIESEL is already at zero. The explanation reports critical risk and 100% 24-hour stockout probability both before and after this shipment, because the station is already empty and delivery takes three ticks. The shipment does not reverse stockout before arrival.

## Gate status

Awaiting explicit operator approval of recommendation `1cb05b67-3440-45e5-a6d8-398482678d8c`. Until that authorization arrives, the recommendation remains `PROPOSED`, the simulator remains paused, and no worker submission or idempotency replay is performed. After approval, capture the approval row, worker submission, simulator allocation/status through `ARRIVED`, then replay this exact JSON body and verify one allocation ID remains.

## Read-only identity, health, and freshness recheck — 2026-11-20

No approval, rejection, allocation POST, replay, reset, injected-fault change, or tick advancement was performed.

- Read-only SQL against `recommendations` confirmed candidate `1cb05b67-3440-45e5-a6d8-398482678d8c` has column quantity `6000`, key `rec-cd2db2c8-5d87-4bc7-876c-d06373049a8a`, and request-body quantity/key `6000.0` / the same key. Its route, depot, station, and fuel fields match the body.
- The similar proposal is a separate row: ID `dab6db72-4f94-4b09-a167-d1dea8c1f2fc`, quantity `1543.5502472239223`, and key `rec-9a2da662-644a-4256-ab25-41695ffb753e`. The API returned both rows with these same ID/quantity/key/body associations. The discrepancy was a UI association ambiguity: cards omitted recommendation IDs, while liters were rounded to whole numbers.
- The recommendation card now shows ID, idempotency key, full precision request quantity, and the exact persisted request body. A summary/body mismatch disables UI decisions; the API also refuses approval without writing a decision when persisted row fields differ from the request body.
- A stale decision-engine heartbeat now degrades aggregate health while a healthy worker remains reported separately. A live post-rebuild health read showed overall `DEGRADED`, `worker=HEALTHY`, `simulator=HEALTHY`, `decision_engine=DEGRADED`, and `predictor=HEALTHY`.
- Same-tick successful ingestion now replaces `raw_json` and `sim_time` together with freshness metadata. After rebuilding, `/api/state` reported the live simulator's `PAUSED` status at tick 134, matching direct `GET /v1/instance`; data age was about 2.4 seconds at that read, stale was false, and data status was healthy.
- A new fresh `SnapshotIngestor.fetch_snapshot()` read inside the worker, validated with the persisted exact request and local simulator-order validator, returned tick 134, `PAUSED`, zero allocations, healthy/non-stale data, and `violations=[]`.
- Post-rebuild, both proposals remained `PROPOSED`; simulator allocations and API decisions remained empty. Frontend returned HTTP 200 on port 5174. The candidate expires at tick 138 and estimates arrival at tick 138 (3 route ticks after next-tick departure at 135).
- Regression verification: `make test` passed 129 Python and 6 frontend tests; `make lint` passed Ruff, formatting, TypeScript, and Vite production build; Compose config validation and `git diff --check` passed. API, worker, and frontend images were rebuilt with the demo predictor/port configuration. The served frontend bundle contains the recommendation ID, idempotency key, exact body, and malformed-request guard UI. A final post-build read still showed tick 134 PAUSED, both proposals PROPOSED, and no decisions or simulator allocations. The Sprint 4 human approval/arrival/replay gate remains open.
