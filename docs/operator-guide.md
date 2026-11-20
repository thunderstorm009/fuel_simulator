# Operator guide

All values and actions are **SIMULATED**.

## Start and inspect

1. Configure `.env` from `.env.example`; keep the operator token private.
2. Start with `make up`. Check the component health banner and data age before using recommendations.
3. Review Overview, Network, Stockout Risk, and System Health. A stale or degraded snapshot lowers confidence and blocks executor submission.

## Review a recommendation

Open Allocations and inspect the source/destination, route, fuel, quantity, ETA, constraints, before/after risk, alternatives, confidence, and review flag. Enter the operator token only in the in-memory UI field. Approve only a concrete recommendation after reviewing it; the API records intent and the worker performs a fresh non-stale simulator read and full revalidation before its simulator POST. Reject with a reason when declining.

Never use a fault demo, scenario tool, or script to bypass approval. Do not approve merely to make a demo look complete. A same-key retry must use the persisted exact request body.

## Stop and recover

`make down` preserves local data volumes. Consult [the runbook](runbook.md) for component failures. `docker compose down -v` deletes PostgreSQL and Grafana state; it is intended only for a confirmed disposable cold-start check.
