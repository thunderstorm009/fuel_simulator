# Sprint 4 overnight live acceptance evidence

Date: 2026-11-20 (Asia/Dhaka) | State: live acceptance passed; one authorized approval, arrival, and exact replay verified

## Owner authorization and selection

The project owner explicitly authorized exactly one live verification approval in the overnight execution prompt and stated not to wait for them. No additional approval is authorized in the running operator app.

A fresh REST read through the worker's `SimClient` and `SnapshotIngestor.fetch_snapshot()` was compared with all seven current `PROPOSED` API records. The simulator was `PAUSED` at tick 134, `tick_minutes=15`, `stale=false`, `data_status=HEALTHY`, with zero allocations. Every proposed request passed `core.validator.validate()` and was unexpired at tick 134. The most urgent group was tied at critical risk, 0 hours to stockout, 100% 24-hour stockout probability, and estimated arrival tick 138. Other candidates for Karnaphuli had estimated arrival tick 139. The tie-break was earliest arrival, then the 6,000 L Cox's Bazar DIESEL shipment (the largest feasible single shipment on that route).

Selected recommendation `1cb05b67-3440-45e5-a6d8-398482678d8c`; status `PROPOSED`, created tick 134, expires tick 138.

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

## Fresh simulator constraint revalidation

Live values came from the fresh worker-owned simulator read at tick 134. The validator returned `[]`.

| Rule, in simulator order | Fresh state | Result |
|---|---|---|
| Idempotency key unused | Key absent from the 0 current allocations | PASS |
| Entities exist | Patiya, Cox's Bazar, and route all present | PASS |
| Route endpoints match | Patiya → Cox's Bazar | PASS |
| Depot open | Patiya `OPEN` | PASS |
| Station open | Cox's Bazar `OPEN` | PASS |
| Route available | `AVAILABLE` | PASS |
| Route maximum | 6,000 L requested ≤ 6,000 L maximum | PASS |
| Depot inventory | 81,000 L DIESEL ≥ 6,000 L | PASS |
| Dispatch capacity | 0 L used + 6,000 L ≤ 11,000 L/tick | PASS |
| Destination capacity | 0 L DIESEL + 6,000 L ≤ 12,000 L | PASS |

Patiya has 81,000 L diesel on hand. Cox's Bazar is open but already has 0 L diesel; its 12,000 L station capacity leaves room for the shipment. Route transit is 3 ticks. The proposal estimated tick 138, but live execution later showed a one-tick ETA overestimate: the worker submitted at tick 134, and the simulator recorded `expected_arrival_tick=137`. A regression test now ensures new recommendations use the simulator's current-tick dispatch behavior. This shipment replenished a current stockout after arrival; it did not prevent the already-current stockout.

At selection time, the sibling Cox's Bazar DIESEL proposal was a separate record (`dab6db72-4f94-4b09-a167-d1dea8c1f2fc`, 1,543.5502472239223 L, key `rec-9a2da662-644a-4256-ab25-41695ffb753e`). It was not associated with the selected body. The two quantities together fit the live 11,000 L dispatch limit and 12,000 L station capacity, but only the selected recommendation is authorized for approval.

## Approval and execution record

The API's `OPERATOR_TOKEN` was confirmed present without printing its value; the token is not stored in this evidence. The project owner's explicit one-approval authorization is the overnight execution prompt.

The real operator API approval returned HTTP 200 with `already_decided=false`, the selected recommendation ID, `status=APPROVED`, and `simulated=true`. The worker executor performed the simulator POST; no manual `/v1/allocations` submission was used. Simulator allocation ID `1` was created with the exact stored body and status `PENDING`, then API and worker lifecycle state updated to `SUBMITTED`/`IN_TRANSIT` as the simulator advanced.

The simulator was advanced with `/admin/step` only, one tick per request, remaining PAUSED after each step:

| Tick | Simulator allocation state | Recorded details |
|---:|---|---|
| 134 → 135 | IN_TRANSIT | departure tick 134; expected arrival tick 137 |
| 135 → 136 | IN_TRANSIT | still in transit |
| 136 → 137 | ARRIVED | actual arrival tick 137 |
| 137 → 138 | ARRIVED | remained arrived; this was the recorded expiry tick |

One exact replay was then sent once through `core.SimClient.create_allocation()` inside the worker container, loading the persisted `request_body` for recommendation `1cb05b67-3440-45e5-a6d8-398482678d8c`. The replay body was byte-for-field equivalent JSON with the same key, depot, station, route, fuel, and quantity. SimClient returned allocation ID `1`, status `ARRIVED`, the same idempotency key, and `stale=false`.

Final read-only verification at tick 138 returned simulator status `PAUSED`, exactly one allocation matching the idempotency key (ID `1`, `ARRIVED`), API recommendation status `ARRIVED`, `sim_allocation_id=1`, and exactly one decision record. Thus replay created no duplicate. Two preceding attempts to reach the read-only API endpoint used an incorrect internal port/path and failed before reaching the simulator; they did not send allocation requests.

### ETA regression

`tests/unit/test_policy.py::test_estimated_arrival_matches_simulator_dispatch_tick_semantics` reproduced the one-tick discrepancy before the fix (failed: expected `snapshot.tick + transit_ticks`, actual was one tick later), then passed after `HeuristicPolicy` changed recommendation arrival estimate to current tick plus route transit. ADR-019 records the distinction between a newly submitted allocation and an already-pending allocation projection. The historical approved recommendation and decision were not modified.
