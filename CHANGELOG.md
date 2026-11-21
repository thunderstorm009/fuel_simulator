# Changelog

All notable changes to the Fuel Supply Intelligence & Resilience Platform are documented in this file.

## [Sprint 10] - 2026-11-21 - Delivery Excellence, Resilience Limits, Observability, Load Proof & Final Freeze
- Added `/api/version` endpoint exposing git sha, tag, build time, `model_version` (1.1.0), and `policy_version` (2.1.0), with UI footer component.
- Added constant-time operator token verification via `hmac.compare_digest` with sliding-window rate limiting (60 decisions/min, HTTP 429).
- Added multi-architecture container release workflow `.github/workflows/release.yml` with automatic GHCR publishing.
- Added automated rollback scripts `scripts/deploy.sh` and `scripts/rollback.sh` with live rollback drill verified in `docs/evidence/sprint-10-rollback-drill.txt`.
- Added Prometheus alert rules in `observability/prometheus/alert_rules.yml` with runbook URLs for all critical conditions.
- Measured empirical resilience matrix: per-service kill -9 recovery (0.10s-0.23s), database outage recovery (0.16s), and 5x traffic surge burst in `docs/evidence/sprint-10-resilience-matrix.txt`.
- Benchmarked decision path under load via `loadtest/k6.js` (9,584 requests across 10-100 VUs, median 122ms, 0% errors).
- Added judging day demonstration guide in `docs/JUDGING-DAY.md` and rehearsal drill script `scripts/surprise_drill.sh`.
- Achieved 100% compliance across all 26 sections of official hackathon brief in `docs/BRIEF-COMPLIANCE.md`.

## [Sprint 9] - 2026-11-21 - Decision Intelligence Quality and Operator Experience
- Implemented pure backtesting and calibration engine (`core/backtest.py`), replaying 2,000 historical ticks (1h: 3.07% MAPE, 24h: 2.11% MAPE).
- Added interactive pure What-If impact simulation tool (`core/what_if.py`, `POST /api/whatif`, `WhatIfSimulator.tsx`) executing in <50ms without database writes.
- Built 5 operator views: Regional Demand Panel, Incoming Supply Timeline, Alert Center with live bell badge, Network Topology View, and Offline Evaluation Scorecard.
- Added P90 uncertainty safety buffer in heuristic policy and implemented linear flow optimizer (`core/policies/optimizer.py`, ADR-039).
- Added generative incident summarization engine (`core/summarize.py`) with deterministic template default and bounded LLM wrapper (ADR-040).

## [Sprint 8] - 2026-11-21 - Truth Pass, Event Coverage, Anomaly Detection & Running Simulator Robustness
- Completed truth pass: eliminated non-compliant `/admin` routes from app code and purged unproven claims.
- Built 26-section brief compliance matrix in `docs/BRIEF-COMPLIANCE.md`.
- Implemented pure deterministic two-pass triage heuristic prioritizing 12h emergency survival fuel, with 5 crisis scenarios and 100% determinism across 54 runs.
- Implemented pure anomaly detection engine (`core/detect.py`) covering demand surges, regional spikes, inventory drops, bottlenecks, and corridor disruptions with automatic resolution.
- Added forward depot supply risk modeling (`core/depot_risk.py`) and operator dashboard risk panel.
- Added adaptive simulator speed telemetry (`ticks_per_second`) and operator speed warning banner.

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
