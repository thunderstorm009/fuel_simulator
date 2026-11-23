# Sprint 11 Review R1: Architecture and Boundaries
**Reviewer:** Self-reviewed with `code-review-strict`  
**Date:** 2026-11-23  
**Commit Range:** `sprint-10...HEAD` (`dda144e`)  

## AGENTS.md Hard Rules Audit

| Rule | Requirement | Findings & Evidence | Status |
|---|---|---|---|
| **Rule 1** | REST is truth. SSE is only a hint to refetch; no replay; refetch after reconnect. | SSE client in `backend/worker/sse.py` and `ingest.py` issues full REST fetch on every event hint and after reconnect. Zero data relies on SSE message bodies. | **PASS** |
| **Rule 2** | API never calls simulator on read paths; reads database. Worker owns simulator I/O. | Inspected `backend/api/routes/*.py`. All endpoints query `Repository` reading PostgreSQL. Simulator client is never imported or called in `backend/api`. | **PASS** |
| **Rule 3** | External calls have timeout, bounded retry with jitter, strict schema validation. Never retry 409/422. | `backend/shared/core/sim_client.py` strictly raises on 409 and 422 without retrying. Timeouts bounded (5s-10s). | **PASS** |
| **Rule 4** | Forecast, risk, policies, validator, failure boundary are pure functions with no I/O. | Inspected newly introduced and modified pure modules: `failure_boundary.py`, `scenario_sweep.py`, `backtest.py`, `risk.py`, `forecast.py`. All are pure functions with zero I/O, deterministic or seeded RNG. | **PASS** |
| **Rule 5** | Idempotency key permanent in request body, created once per recommendation, stored and reused only for identical body. | Checked `scenario_sweep.py`, `executor.py`, and models. Permanent structured idempotency key generation preserved. | **PASS** |
| **Rule 6** | Never submit without APPROVED recommendation, fresh non-stale read, and re-validation. | Mandatory approval gate in `executor.py` and `backend/api/routes/recommendations.py` strictly enforced. Re-validation occurs before submit. | **PASS** |
| **Rule 7** | Do not count scheduled or in-transit supply as on-hand inventory. Do not confuse demand with served demand. | Projections in `forecast.py` and `risk.py` separate on-hand stock from scheduled arrivals. Served demand separated from unmet demand. | **PASS** |
| **Rule 8** | `tick_minutes` comes from `/v1/instance`; never hard-code it. | Comprehensive codebase audit in WP11.5 confirmed zero hardcoded `15` for tick duration. Dynamic scaling verified for both 8 and 15 min ticks. | **PASS** |
| **Rule 9** | Parse all error shapes: detail.code, error.code, nested detail.code, 422 list. | Handled uniformly by `parse_simulator_error` in `sim_client.py`. | **PASS** |
| **Rule 10** | Treat `X-Simulator-Stale: true` as stale: flag it, lower confidence, block submissions. | Checked in `ingest.py` and snapshot headers. | **PASS** |
| **Rule 11** | Metric labels low cardinality; no secrets in code; config via `.env.example`. | Scanned with Gitleaks: zero leaks. Labels restricted to status enums. | **PASS** |
| **Rule 12** | Everything shown to operator is labelled SIMULATED. No auto-submission. | Global footer, dashboard, network, and evaluation views display SIMULATED pill. | **PASS** |

## Findings Summary
- **P0 Findings:** 0
- **P1 Findings:** 0
- **P2 Findings:** 0
- **Verdict:** **PASS** (Zero architectural or boundary violations detected).
