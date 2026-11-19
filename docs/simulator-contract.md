# Simulator contract (summary of the official guide; the guide and the live API override this)

## Endpoints
Read: /v1/health (bypasses faults), /v1/instance, /v1/regions, /v1/depots, /v1/stations, /v1/routes, /v1/supply-arrivals, /v1/events, /v1/allocations, /v1/demand-history?station_id=&limit= (limit 1-2000), /v1/metrics, /v1/stream (SSE).
Write: POST /v1/allocations; POST /v1/allocations/{id}/cancel (PENDING only).
Admin (tests and demos only; bypass faults): /admin/run, /pause, /toggle, /step, /reset, /events, /faults, /faults/clear, /audit.

## World
2 regions (dhaka, chattogram), 2 depots (gazipur, patiya), 4 stations (mirpur urban_high, tongi industrial, karnaphuli highway, coxsbazar regional), 6 routes, fuels DIESEL, PETROL, OCTANE. 22 scheduled supply arrivals (4 initial burst at ticks 12-20, then 18 recurring every 64 ticks).

## Allocation request
idempotency_key (body, 1-150 chars, permanent), source_depot_id, destination_station_id, route_id, fuel_type, quantity (>0 and <= route.max_shipment).
Validation order: idempotency, NOT_FOUND (404), ROUTE_MISMATCH, DEPOT_CLOSED, STATION_CLOSED, ROUTE_DISRUPTED, ROUTE_CAPACITY_EXCEEDED, INSUFFICIENT_INVENTORY, DISPATCH_CAPACITY_EXCEEDED, DESTINATION_CAPACITY_EXCEEDED (all 409 except NOT_FOUND).
Same key and same body returns the existing allocation (guide says 201 in one place and 200 in another: handle both). Same key and a different body gives 409 IDEMPOTENCY_KEY_MISMATCH. Cancel does not free the key.

## Error shapes
Allocation errors {detail:{code,message}}. Injected faults {error:{code:FAULT_INJECTED,message}} HTTP 503. Stream fault 503 {detail:{code:FAULT_INJECTED}}. Validation 422 {detail:[...]}.

## SSE
Events: simulation.tick, allocation.status_changed, inventory.updated, simulator.notice. 15s keepalive. Queue of 200 per subscriber; falling behind drops you silently. No Last-Event-ID replay. Treat as a hint; refetch via REST.

## Events and faults
Events: demand_spike, route_disruption, station_outage, depot_constraint, shipment_delay (one-shot), supply_shortfall (one-shot). Faults: latency, unavailable, error_rate, stale_data (X-Simulator-Stale: true header), stream_disconnect.

## Demand model (guide section 8)
Daily liters per profile (DIESEL/PETROL/OCTANE): urban_high 8500/10500/5600 noise 0.10; industrial 14000/4500/2200 0.08; highway 10500/11000/6200 0.12; regional 7200/7600/3600 0.10. Hour factors: industrial 06-17:59 1.55 else 0.45; highway 06-09 or 16-20 1.35 else 0.75; urban_high 07-09 or 16-20 1.45 else 0.70; regional 07:00-20:59 1.25 else 0.65.

## VERIFY list (answer in docs/sim-findings.md during Sprint 1)
- Tick length: guide text says 15 minutes, compose default says 8. Read /v1/instance.
- Default speed: 15 vs 8 ticks per second in different places.
- Replay status code 200 or 201.
- Hour-factor boundaries (is 09 inclusive in 07-09?).
- Does region demand_factor multiply station demand?
- How in-flight plus pending counts toward dispatch capacity.
- Event with start_tick in the past: behavior.
- Does the image contain curl or wget (for a compose healthcheck)?
- Is a replayed idempotent request re-validated against current inventory?
