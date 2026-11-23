# Security and guardrails

## Core Operating Principles
- **Simulator Only**: Everything is labelled SIMULATED. No real fuel infrastructure, purchase orders, or real-world physical dispatches.
- **Mandatory Human-in-the-Loop**: An approved recommendation from a human operator is required before any allocation is submitted to the simulator. No automatic approval or submission is permitted in backend, worker, or UI.
- **Secrets Management**: Credentials live only in environment variables. Local `.env` is git-ignored and never committed; `.env.example` provides documented placeholders.
- **Operator Authentication**: Endpoints modifying system state (`/api/recommendations/{id}/approve`, `/api/recommendations/{id}/reject`, and chaos inject routes) require `OPERATOR_TOKEN` via `X-Operator-Token` header.
- **Token Hardening**: Verified using constant-time string comparison (`hmac.compare_digest`) to prevent timing attacks. Sensitive tokens are never logged or exposed in HTTP responses.
- **Rate Limiting**: In-memory sliding-window rate limiter enforces a burst ceiling (60 requests/minute per client IP) on operator write paths, returning HTTP 429 when exceeded.
- **Strict Input Validation**: Every external input and simulator payload is validated via strict Pydantic schemas. Malformed payloads are rejected immediately.
- **CORS & Network Isolation**: CORS is restricted to declared frontend origins. Containers run as non-root users with least privilege.

## Automated Dependency Auditing & Security Debt Resolution

| Scanner | Tool / Engine | Scope | Target | Result (Sprint 11) |
|---|---|---|---|---|
| **Python Dependency Audit** | `pip-audit` | Python runtime & test dependencies | 0 High / Critical | **0 Vulnerabilities** (Cleared 16 Starlette/pytest advisories) |
| **Frontend Dependency Audit** | `npm audit` | React/TypeScript web dependencies | 0 High / Critical | **0 Vulnerabilities** (Clean) |
| **Container Vulnerability Scan** | `aquasec/trivy:latest` | `requirements.txt` & `package-lock.json` | 0 High / Critical | **0 Vulnerabilities** (Clean) |
| **Secret & Credential Scan** | `zricethezav/gitleaks:latest` | Full repository git history & files | 0 Leaks | **0 Leaks Found** (247 MB scanned) |

### Package Upgrades Applied (WP11.4)
- **Starlette**: Upgraded to `1.10.0` (resolving CVE-2024-47874, CVE-2023-30798, and related advisory notices).
- **FastAPI**: Upgraded to `0.165.0` to maintain native compatibility with Starlette >= 1.0+.
- **Pytest**: Upgraded to `9.2.0` (resolving PYSEC-2026-1845).
- **Pytest-Asyncio**: Upgraded to `1.5.0` for full compatibility with Pytest 9.2+.
- **Annotated-Doc & Opentelemetry-API**: Pinned as explicit runtime dependencies.

## Continuous Security in CI & Automated Updates
- **Dependabot Configuration**: Located at `.github/dependabot.yml`, configured for weekly updates across `pip`, `npm`, `github-actions`, and `docker`.
- **CI Security Gate**: Executed on every push and pull request via `.github/workflows/ci.yml`:
  - `gitleaks` scans all commits for committed secrets.
  - `pip-audit` strictly checks `requirements.txt` and `requirements-dev.txt` (fails the build if any vulnerability is detected).
  - `npm audit` checks frontend packages with `--audit-level=high`.

## Out of Scope
- Enterprise identity federation (SAML/OAuth2), multi-tenant tenancy isolation, and Kubernetes RBAC remain out of scope for this single-operator festival build.
