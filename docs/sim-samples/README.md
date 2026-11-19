Sprint 1 fixture provenance:

- The canonical endpoint samples were captured from the official simulator image on 2026-11-19. `exploration-results.json` records response statuses, headers, and body shapes for the endpoint, event, and fault probes.
- `events.json`, `allocations.json`, and `demand-history.json` are populated live captures so the model tests cover non-empty values. `admin-audit.json` captures `/admin/audit?limit=100`.
- `allocation-pending.json` and `depot-detail.json` remain guide-derived examples. These are kept as additional contract fixtures; they are not represented as live captures.
- Some `.json.json` probe files were produced by an earlier explorer run before suffix handling was fixed. They are preserved; reruns now use one `.json` suffix.
- `scripts/explore_sim.py` resets and pauses the simulator before probes, clears faults after each fault case, and performs a final fault clear if a probe fails.
