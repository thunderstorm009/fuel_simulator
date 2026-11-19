---
name: simulator-integration
description: Use when writing or changing code that talks to the BUP Fuel Supply Simulator (client, ingestion, SSE, executor, tests). Covers endpoints, error shapes, idempotency, stale data and fault behavior.
---
# Simulator integration
- REST is truth. SSE only triggers a refetch; there is no Last-Event-ID replay, so refetch after every reconnect. A 15s silence is normal (keepalive).
- Error shapes: allocation errors use detail.code; injected faults use error.code with HTTP 503; the stream fault is 503 with nested detail.code; 422 has a detail list. One parser handles all.
- Retry only timeouts, connection errors and 503 FAULT_INJECTED. Never retry 409 or 422.
- POST /v1/allocations: idempotency_key is in the BODY and is permanent once used (even after cancel). Same key and same body is a safe retry (200 or 201). Same key and a different body gives 409 IDEMPOTENCY_KEY_MISMATCH. Only PENDING allocations can be cancelled.
- Validation order on submit: not found, route mismatch, depot closed, station closed, route disrupted, route capacity, depot inventory, dispatch capacity, destination capacity.
- X-Simulator-Stale: true means stale: mark the snapshot stale, lower confidence, block submissions.
- Always pass limit to demand-history (max 2000); 12 rows are added per tick.
- /v1/health bypasses faults (liveness). /admin/* is for tests and demos only, never in production code paths.
- tick_minutes comes from /v1/instance. Where the guide is ambiguous, use docs/sim-findings.md; if it is silent, test against the live simulator and record the answer.
- Use captured fixtures in docs/sim-samples for tests. Never hard-code simulator values as live data.
