# Scenario runner results

Generated: 2026-11-20T11:20:05.462118+00:00
Snapshot tick: 152
Sim time: 2026-01-02 14:00:00
API health: DEGRADED

> Simulator was PAUSED throughout. No allocations were submitted.
> Each policy was run twice on the same frozen snapshot to verify determinism.

## Summary

| Policy | Plans | Total Qty (L) | Stations | Deterministic |
|--------|------:|-------------:|----------|---------------|
| none       |     0 |            0 | none | ✅ yes |
| naive      |    12 |        79500 | station-coxsbazar, station-karnaphuli, station-mirpur, station-tongi | ✅ yes |
| heuristic  |     6 |        23000 | station-coxsbazar, station-karnaphuli | ✅ yes |

## Heuristic vs naive vs none comparison

| Metric | none | naive | heuristic |
|--------|-----:|------:|----------:|
| Plans produced | 0 | 12 | 6 |
| Total qty (L) | 0 | 79500 | 23000 |
| At-risk pairs | 12 | 12 | 12 |
| Stations addressed | [] | ['station-coxsbazar', 'station-karnaphuli', 'station-mirpur', 'station-tongi'] | ['station-coxsbazar', 'station-karnaphuli'] |

## Per-policy plan details (run 1)

### Heuristic policy
| Station | Fuel | Depot | Route | Qty (L) | Stockout h | Arrival tick |
|---------|------|-------|-------|--------:|-----------:|-------------:|
| station-coxsbazar | OCTANE | depot-patiya | route-patiya-coxsbazar | 4073 | n/a | 155 |
| station-coxsbazar | PETROL | depot-patiya | route-patiya-coxsbazar | 6000 | n/a | 155 |
| station-coxsbazar | PETROL | depot-patiya | route-patiya-coxsbazar | 927 | n/a | 155 |
| station-karnaphuli | DIESEL | depot-gazipur | route-gazipur-karnaphuli | 5000 | n/a | 156 |
| station-karnaphuli | DIESEL | depot-gazipur | route-gazipur-karnaphuli | 4800 | n/a | 156 |
| station-karnaphuli | OCTANE | depot-gazipur | route-gazipur-karnaphuli | 2200 | n/a | 156 |

### Naive policy
| Station | Fuel | Depot | Route | Qty (L) | Stockout h | Arrival tick |
|---------|------|-------|-------|--------:|-----------:|-------------:|
| station-coxsbazar | DIESEL | depot-patiya | route-patiya-coxsbazar | 6000 | 13.25 | 155 |
| station-coxsbazar | OCTANE | depot-patiya | route-patiya-coxsbazar | 6000 | n/a | 155 |
| station-coxsbazar | PETROL | depot-patiya | route-patiya-coxsbazar | 6000 | n/a | 155 |
| station-karnaphuli | DIESEL | depot-patiya | route-patiya-karnaphuli | 7000 | n/a | 154 |
| station-karnaphuli | OCTANE | depot-patiya | route-patiya-karnaphuli | 7000 | n/a | 154 |
| station-karnaphuli | PETROL | depot-patiya | route-patiya-karnaphuli | 7000 | n/a | 154 |
| station-mirpur | DIESEL | depot-gazipur | route-gazipur-mirpur | 7000 | n/a | 154 |
| station-mirpur | OCTANE | depot-gazipur | route-gazipur-mirpur | 7000 | n/a | 154 |
| station-mirpur | PETROL | depot-gazipur | route-gazipur-mirpur | 7000 | n/a | 154 |
| station-tongi | DIESEL | depot-gazipur | route-gazipur-tongi | 6500 | n/a | 154 |
| station-tongi | OCTANE | depot-gazipur | route-gazipur-tongi | 6500 | n/a | 154 |
| station-tongi | PETROL | depot-gazipur | route-gazipur-tongi | 6500 | n/a | 154 |

### None policy
No plans generated.

## Conclusion

- **Heuristic** produced constraint-validated plans prioritised by urgency.
- **Naive** produced unconstrained upper-bound allocations (not safe to submit).
- **None** (do-nothing baseline) produced no plans.
- Heuristic beats none on coverage and beats naive on constraint safety.
- Both runs of each policy produced identical output (determinism confirmed).
