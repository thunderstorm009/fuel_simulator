# Security and guardrails
- Simulator only. No real fuel infrastructure, purchases or dispatches. Everything is labelled SIMULATED.
- Human approval is required before any allocation is submitted. No auto-submit.
- Secrets only in environment variables; .env is git-ignored; .env.example has placeholders.
- Operator token (OPERATOR_TOKEN) protects approve, reject and chaos endpoints.
- Validate all external input with strict schemas; reject and alert on malformed data.
- CORS limited to the frontend origin; containers run as non-root; dependencies pinned.
- Out of scope: enterprise authentication, multi-tenant isolation.
