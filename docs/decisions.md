# Decision log (ADR style). Add an entry when a decision is made. Template: docs/templates/adr.md

Statuses: PROPOSED, ACCEPTED, SUPERSEDED.

| ID | Decision | Status | Sprint |
|---|---|---|---|
| ADR-001 | REST is truth; SSE is only a hint to refetch | PROPOSED | 1 |
| ADR-002 | Worker owns simulator I/O; API reads the database only | PROPOSED | 1 |
| ADR-003 | Heuristic allocation first; optimizer only if time remains | PROPOSED | 1 |
| ADR-004 | Monte Carlo for stockout uncertainty | PROPOSED | 3 |
| ADR-005 | Outbox-style executor: approve records intent, executor re-validates and submits | PROPOSED | 4 |
| ADR-006 | Idempotency key rec-<uuid>, stored, reused only for the identical body | PROPOSED | 4 |
| ADR-007 | Predictor as its own container with baseline fallback | PROPOSED | 5 |
| ADR-008 | No Kubernetes or RL; Docker Compose only | PROPOSED | 1 |
| ADR-009 | Operator token from env protects approve, reject and chaos endpoints | PROPOSED | 4 |

## Entries
(Add full entries below as decisions are made.)
