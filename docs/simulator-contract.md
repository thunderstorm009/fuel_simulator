# Simulator contract (summary of the official guide; the guide and the live API override this)

## Endpoints
Read: /v1/health (bypasses faults), /v1/instance, /v1/regions, /v1/depots, /v1/depots/{entity_id}, /v1/stations, /v1/stations/{entity_id}, /v1/routes, /v1/supply-arrivals, /v1/events, /v1/allocations, /v1/demand-history?station_id=&limit= (limit 1-2000), /v1/metrics, /v1/stream (SSE).
Write: POST /v1/allocations; POST /v1/allocations/{id}/cancel (PENDING only).
Admin (tests and demos only; bypass faults): GET /admin, /admin/events, /admin/faults, /admin/audit?limit=; POST /admin/run, /pause, /toggle, /step, /reset, /events, /faults, /faults/clear.

## World
2 regions (dhaka, chattogram), 2 depots (gazipur, patiya), 4 stations (mirpur urban_high, tongi industrial, karnaphuli highway, coxsbazar regional), 6 routes, fuels DIESEL, PETROL, OCTANE. 22 scheduled supply arrivals (4 initial burst at ticks 12-20, then 18 recurring every 64 ticks).

## Allocation request
idempotency_key (body, 1-150 chars, permanent), source_depot_id, destination_station_id, route_id, fuel_type, quantity (>0 and <= route.max_shipment).
Validation order: idempotency, NOT_FOUND (404), ROUTE_MISMATCH, DEPOT_CLOSED, STATION_CLOSED, ROUTE_DISRUPTED, ROUTE_CAPACITY_EXCEEDED, INSUFFICIENT_INVENTORY, DISPATCH_CAPACITY_EXCEEDED, DESTINATION_CAPACITY_EXCEEDED (all 409 except NOT_FOUND).
Same key and same body returns the existing allocation (guide says 201 in one place and 200 in another: handle both). Same key and a different body gives 409 IDEMPOTENCY_KEY_MISMATCH. Cancel does not free the key.

## Error shapes
Allocation errors {detail:{code,message}}. Injected faults {error:{code:FAULT_INJECTED,message}} HTTP 503. Stream fault 503 {detail:{code:FAULT_INJECTED}}. Validation 422 {detail:[...]}.

## SSE
Events: simulation.tick, allocation.status_changed, inventory.updated, simulator.notice. 15s keepalive. Queue of 200 per subscriber; falling behind drops you silently. No Last-Event-ID replay. Treat as a hint; refetch via REST. The worker uses a 20s SSE read timeout so normal keepalive silence does not look like a disconnect; ordinary REST reads keep their separate 3s timeout.

## Client behavior implemented in Sprint 2
`backend/shared/core/sim_client.py` validates each response against the shared typed models, returns the `X-Simulator-Stale` marker with the result, and exposes typed unavailable, invalid-response, and business errors. Requests use 2s connect and 3s read timeouts and up to three retries after the first attempt with jitter for timeouts, connection errors, and HTTP 503 `FAULT_INJECTED`; 409 and 422 are not retried. The per-client breaker opens after five failed requests and permits one half-open probe after 10s. The worker is the only owner of this client in production.

## Events and faults
Events: demand_spike, route_disruption, station_outage, depot_constraint, shipment_delay (one-shot), supply_shortfall (one-shot). Faults: latency, unavailable, error_rate, stale_data (X-Simulator-Stale: true header), stream_disconnect.

## Demand model (guide section 8)
Daily liters per profile (DIESEL/PETROL/OCTANE): urban_high 8500/10500/5600 noise 0.10; industrial 14000/4500/2200 0.08; highway 10500/11000/6200 0.12; regional 7200/7600/3600 0.10. Hour factors: industrial 06-17:59 1.55 else 0.45; highway 06-09 or 16-20 1.35 else 0.75; urban_high 07-09 or 16-20 1.45 else 0.70; regional 07:00-20:59 1.25 else 0.65.

## Live verification results

The live findings are recorded in `docs/sim-findings.md`. The official image reports 15-minute ticks and a configured default speed of 8 ticks per second. Same-key replay returned 201; event hour boundaries were inclusive; region `demand_factor` multiplied demand. Controlled probes found that pending shipments consume dispatch capacity within a tick, while in-transit shipments from the preceding tick did not consume the next tick's budget. The image contains curl and Python, but not wget. The inventory-specific replay case remains untested.

## Official-guide coverage notes

- The official guide also documents `GET /v1/depots/{entity_id}` and `GET /v1/stations/{entity_id}`.
- Admin reads include `GET /admin`, `GET /admin/events`, `GET /admin/faults`, and `GET /admin/audit?limit=`. The short endpoint inventory above omits the first three reads; `/admin/audit` is listed without its optional query parameter.
- The guide contradicts itself about default `TICK_MINUTES` (8 vs 15), default `SIMULATION_SPEED` (15 vs 8), and replay status (201 vs 200). The live image reports 15 minutes, configures 8 ticks/second, and returned 201 for replay. The client accepts both replay success statuses.
- `docs/sim-samples/` contains live captures from the official image and a small number of retained guide-derived contract fixtures; provenance is listed in `docs/sim-samples/README.md`.
