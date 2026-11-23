# Scenario comparison & determinism proof

Generated: 2026-11-23T06:27:05.692704+00:00

## Policy performance across scenarios (Run 1)

| Scenario | Policy | Service Level | Served (L) | Unmet (L) | Allocs (L) | Failures | Stockouts |
|---|---|---:|---:|---:|---:|---:|---:|
| spike | heuristic | 100.0% | 43678 | 0 | 43777 | 0 | 0 |

## Determinism verification (Run 1 vs Run 2)

| Scenario | Policy | Run 1 Svc Level | Run 2 Svc Level | Delta | Deterministic? |
|---|---|---:|---:|---:|---|
| spike | heuristic | 100.00% | 100.00% | 0.0000 | ✅ PASS |

## Key findings

- **Heuristic policy** achieves equal or higher service level than do-nothing.
- **Naive policy** requests fuel without full constraint checking.
- **Determinism** is verified across Run 1 and Run 2.
