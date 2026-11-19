# Simulator findings — Sprint 1

## Evidence status

The official image `asifmahmoud414/bup-fuel-supply-simulator:1.0.0` was run on 2026-11-19. Docker reports the image as `linux/amd64` on this host's `linux/arm64` platform, so Docker used emulation. `scripts/explore_sim.py` completed repeatedly against the live service; the responses and status/header/body-shape records are in `docs/sim-samples/`. The admin audit response is also captured as `admin-audit.json`.

The image's default settings were checked in its own `/app/app/config.py` with no simulator environment overrides: `simulation_speed = 8.0`, `tick_minutes = 15`, and `simulator_start_mode = "paused"`. The default-speed timing probe observed 60 ticks in 10.043 seconds (5.97 ticks/s) under AMD64 emulation; this measured rate is host/runtime dependent and is not the configured speed value. The project's local `.env` sets `SIMULATION_SPEED=1`; that value was not changed.

| VERIFY item | Live finding | Evidence or remaining limit |
|---|---|---|
| `tick_minutes` | **15 minutes.** The no-override image instance and Compose instance both reported 15. | `instance.json`; `exploration-results.json`; default image configuration. |
| Default speed | **Configured default is 8.0 ticks/second.** | Read from image `/app/app/config.py`. Runtime timing was 5.97 ticks/s over 10.043 seconds on AMD64 emulation under an ARM64 host. |
| Same-key replay status | Create and exact replay both returned **201** and the same allocation ID. Same key with a different body returned **409 `IDEMPOTENCY_KEY_MISMATCH`**. | `exploration-results.json`, `allocation-create.json`, `allocation-replay.json`, `allocation-key-mismatch.json`. The client should continue to accept 200 and 201 as the guide conflicts. |
| Hour-factor boundaries | Boundaries are inclusive at the named final hour. A full 96-tick day showed urban-high elevated at 09 and 20, highway at 09 and 20, industrial at 06 and 17, and regional at 20; adjacent low hours matched the lower factor. | `demand-history.json` has 1,152 observations. The factor comparison normalizes by the guide's profile/fuel daily liters; station multipliers were 1.0. |
| Region `demand_factor` effect | **It multiplies station demand.** Chattogram's normalized full-day totals were about 1.05–1.10 against 1.08 expected; Dhaka totals were about 0.94–1.00 against 1.00, within the documented per-observation noise. | `regions.json`, `stations.json`, `demand-history.json`; one simulated day, so this is a fitted result rather than a proof across seeds. |
| Dispatch capacity accounting | Two pending 6,000 L shipments from Gazipur at tick 0 were accepted at its 12,000 L/tick limit; a further 1 L shipment returned **409 `DISPATCH_CAPACITY_EXCEEDED`**. After stepping one tick, the first two were `IN_TRANSIT` and another 1 L shipment was accepted. The dispatch budget resets per tick; prior-tick in-transit quantities did not consume the new tick's budget in this probe. | Live controlled probe; details are in `docs/evidence/sprint-01-runtime.md`. |
| Event with past `start_tick` | At tick 10, an event with `start_tick=0` and `duration_ticks=1` was accepted with **201** as `SCHEDULED`. After one more step to tick 11 it appeared as `ACTIVE`, despite `end_tick=1`. | `event-past-start-tick.json`, `event-past-start-step.json`, and `exploration-results.json`. Record this observed status behavior; do not infer its side effects. |
| `curl` or `wget` in simulator image | **curl exists; wget does not.** Python also exists. | `docker exec ... command -v` probe. Compose's simulator healthcheck uses Python's standard library and passed. |
| Replay revalidates current inventory | An exact replay returned the original 201 allocation after the dispatch budget had been filled, showing that this replay was served without rechecking the current dispatch constraint. **A replay after exhausting source inventory was not directly tested.** | Controlled replay probe in `docs/evidence/sprint-01-runtime.md`; to settle the inventory-specific case, deplete depot inventory with allocations, then replay the exact stored body and compare response/ID. |

## Event and fault exploration

- Each of the six event types returned **201** on injection; each step returned **200**.
- Each of the five fault types returned **201** on injection and **200** when cleared. The clear response was `{"status":"cleared"}` for all five.
- `unavailable` and `error_rate` caused HTTP **503** with `error.code=FAULT_INJECTED`.
- `stale_data` returned HTTP **200** with `X-Simulator-Stale: true`.
- `stream_disconnect` returned HTTP **503** with a stream body line containing `{"detail":{"code":"FAULT_INJECTED"}}`.
- The final live `GET /admin/faults` returned `[]`; no injected fault remained active.

`exploration-results.json` records response status, headers, and body shapes. The canonical stream sample is the normal HTTP 200 response; the stream-fault response has its own file. The explorer writes a single `.json` suffix and keeps the canonical event, allocation, and demand samples populated after its probes.
