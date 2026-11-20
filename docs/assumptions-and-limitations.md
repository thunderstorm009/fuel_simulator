# Assumptions and limitations

- The simulator and all displayed inventory, forecasts, decisions, and actions are simulated.
- REST is authoritative. SSE events only trigger refetch; reconnect does not replay missed messages.
- API read routes use PostgreSQL. The worker owns simulator I/O and the only simulator allocation write.
- Allocation submission requires a persisted operator approval, a fresh non-stale snapshot, and immediate constraint validation.
- Forecasts use observed demand history plus profile assumptions. The predictor currently runs the shared pure risk implementation remotely; baseline fallback discards calibration, caps confidence at 0.4, and requires review.
- Risk projections include known station allocations, not inferred future dispatches or scheduled depot supply as current stock.
- Compose is a local demo deployment. No hosted production deployment, external secret manager, multi-tenant authentication, or SLO guarantee is provided.
- Historical reports document prior simulator runs and environment conditions. Current Sprint 4 live allocation acceptance and Sprint 5–7 runtime checks remain open; see `docs/known-issues.md`.
- Policy comparison and load-test numbers are not claimed because no valid current measured result is available.
