# Sprint 3 runtime evidence — 2026-11-19

## Stack and UI

- `SMOKE_SKIP_BUILD=1 FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 make smoke` exited 0. Output reported simulator `PAUSED`, tick 114; API, worker, and predictor health endpoints returned `{"status":"ok"}`. Compose services were already running; smoke waited for simulator, Postgres, worker, API, predictor, and Prometheus health.
- `GET http://localhost:8101/api/risks` returned 12 station/fuel forecasts at tick 114, `data_status=HEALTHY`, `simulated=true`.
- `GET /api/risks/station-mirpur/DIESEL/trajectory` returned 97 points, `HEALTHY`, `simulated=true`.
- Headless Chrome on `http://localhost:5174` found four Overview stations, the SIMULATED label, all 12 enabled risk cells, and a rendered Recharts surface after opening a pair.
- Worker `/metrics` exposed 12 `forecast_error_liters` series. Example at final check: `forecast_error_liters{fuel_type="DIESEL",station_id="station-mirpur"} 22.340651855453338`. `forecast_job_failures_total` remained 0.

## Live demand-spike scenario

The simulator was paused at tick 102 with no events. The API's Mirpur DIESEL forecast was 2.5 hours and Tongi OCTANE was 11.5 hours. Created `demand_spike` for `region-dhaka`, multiplier 1.8, start tick 103, duration 4 ticks (HTTP 201), then ran the simulator.

- At API tick 104, the forecast drivers showed multiplier 1.8; Mirpur DIESEL fell to 1.0h and Tongi OCTANE to 6.5h.
- The event resolved by tick 108. Its multiplier returned to 1.0, but Mirpur DIESEL was 0h and Tongi OCTANE 7.0h. The simulator consumed inventory during the event and did not replenish it, so hours-to-stockout did not return to the tick-102 values. This verifies demand normalization alongside persistent inventory depletion.
- The historical ratio remained elevated immediately after resolution; the revised fixture test adds normal-demand observations and verifies the EWMA-adjusted forecast rate moves toward baseline without restoring consumed stock.
- The simulator was paused after resolution. Both `demand_spike` and `shipment_delay` were RESOLVED at final tick 111.

## Live shipment-delay scenario

At tick 108, scheduled depot arrival `supply-201` (Gazipur DIESEL, 12,000 L) had planned tick 128. Created a `shipment_delay` for Gazipur DIESEL with `delay_ticks=5`, start tick 109 (HTTP 201), and stepped the simulator. The arrival became `planned_tick=133`, status `DELAYED`. No pending or in-transit station allocation depended on that depot arrival. Mirpur DIESEL remained 0h / critical at API tick 111. The event correctly changed the depot schedule but did not change station stockout risk.

The revised Sprint 3 gate was rerun using scheduled Gazipur PETROL arrival `supply-202`. At tick 111 it had planned tick 132. A `shipment_delay` event (HTTP 201, `delay_ticks=5`) moved it to tick 137. DB-backed `GET /api/state` at tick 114 returned `supply-202` with `planned_tick=137`, `status=DELAYED`, and `simulated=true`. No allocation depended on it; Mirpur DIESEL stayed 0h / critical at API tick 114. Both live shipment events and the demand event are RESOLVED; the simulator remains PAUSED.

## Local verification

- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make test`: **72 passed in 1.18s** after the acceptance updates.
- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make lint`: Ruff passed, all 34 Python files formatted, TypeScript build passed, Vite production build passed (240.73 kB main JS, 426.04 kB lazy chart chunk; gzip 74.76/122.33 kB).
- `docker compose config -q`: exit 0.
- `FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 docker compose config -q`: exit 0.
- `git diff --check`: exit 0.

## Gate interpretation

The acceptance criteria now match the simulator: the spike raises expected demand; after resolution the multiplier returns to 1.0 and later normal observations move the EWMA-adjusted demand toward baseline, while consumed inventory remains depleted and risk is recalculated from that stock. A depot delay changes the ETA; without a dependent allocation it does not change station risk. Pending/in-transit station allocation arrival coverage remains tested. No future dispatch is inferred, and no simulator reset or database deletion was performed.
