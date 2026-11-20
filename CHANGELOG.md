# Changelog

All notable changes to the Fuel Supply Intelligence & Resilience Platform are documented in this file.

## [Sprint 7] - 2026-11-20 - Freeze, Rehearsal, and Release Readiness
- Added guarded cold-start recovery script `scripts/cold_start_check.sh` with live timing (34s recovery).
- Added clean-clone verification script `scripts/verify_clean_clone.sh` validating isolated builds without private workspace files.
- Added reversible random chaos rehearsal script `scripts/chaos_random.py` with HTTP POST fault clearing and zero unexplained 5xx errors.
- Added dual-port compatibility routing (ports 8103 and 8100) in `intel/predictor` and `backend/api/routes/health.py`.
- Finalized operator demonstration guide in `docs/final-demo-script.md` and complete judge Q&A in `docs/qa.md`.
- Completed documentation audit (D6) ensuring clean separation between public assets and local-only development files.

## [Sprint 6] - 2026-11-20 - Evaluation, Load Proof, and Hardening
- Implemented declarative disruption scenario runner `scripts/scenario_runner.py` with 4 scenarios in `scenarios/*.yaml`.
- Verified 100% deterministic policy execution across 24 evaluation runs (delta 0.0000 on all scenario pairs).
- Executed empirical k6 load tests across three operational conditions (normal, simulator latency fault, predictor stopped) with 205k+ requests, 0% error rate, and knee analysis at 100 VUs.
- Captured container CPU and memory resource profiles in `docs/results/docker-stats-*.csv`.
- Hardened GitHub Actions CI workflow with actionlint compliance and scenario smoke execution.

## [Sprint 5] - 2026-11-20 - Observability, Resilience, and Fault Verification
- Provisioned Prometheus and Grafana observability stack with pre-configured dashboards and alerting rules as code.
- Added aggregated `/api/health` endpoint reporting HEALTHY, DEGRADED, and OFFLINE status across all system components.
- Extracted standalone `predictor` service with typed `RemoteForecaster` and local baseline heuristic fallback.
- Executed end-to-end live resilience matrix against all 5 simulator faults, malformed payloads, and service stoppage.
- Validated Grafana alerting live when worker ingestion is interrupted (`docs/evidence/sprint-05-worker-alert-check.txt`).

## [Sprint 4] - 2026-11-20 - Live Verification and End-to-End Decision Flow
- Verified single live operator approval workflow under project-owner authorization.
- Validated allocation progression to `ARRIVED` state at simulator tick 137.
- Verified idempotency protection with exact-key replay returning identical allocation ID 1.
- Corrected recommendation arrival estimation logic to account for current tick transit offsets.

## [Sprint 3] - 2026-11-20 - Core Intelligence Engine
- Implemented pure demand forecasting models (`core/forecast.py`) with seasonal profile tracking.
- Implemented pure inventory stockout risk assessment (`core/risk.py`) with configurable operational buffers.
- Implemented candidate allocation heuristic policies (`core/policies/`) with multi-station priority ranking.
- Implemented strict physical constraint validator (`core/validator.py`) enforcing depot capacity and station limits.

## [Sprint 2] - 2026-11-20 - Operator Frontend and Ingestion
- Built operator dashboard in React 19 + TypeScript + Tailwind with real-time status and telemetry displays.
- Implemented background simulator ingestion worker with SSE reconnection and REST synchronization.
- Added token-protected operator approval interaction in web interface.

## [Sprint 1] - 2026-11-20 - Foundational Infrastructure
- Scaffolding of multi-service repository (backend API, background worker, database, simulator).
- PostgreSQL schema definitions for snapshots, forecasts, recommendations, and decisions.
- Typed simulator REST client with circuit breaking and bounded retries.
