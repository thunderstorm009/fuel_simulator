# Day 3 Repository Inventory: Delta Since Sprint 7 (Baseline: `sprint-7` -> `sprint-10`)

This document is the authoritative, evidence-based inventory of all source files, configurations, scripts, tests, documents, and benchmark outputs added or modified between git tag `sprint-7` (`6ff23ea`) and `HEAD` (`0a871e6`, tag `sprint-10`) on branch `sprints-8-10`.

Legend:
- **Status:** `NEW` (introduced in Sprints 8–10), `MODIFIED` (existed in Sprint 7, updated in Sprints 8–10), `UNCHANGED` (pre-existing, referenced for context).
- **Verification Status:** `VERIFIED-TODAY` (reproduced/tested directly in Day 3 execution), `CLAIMED-ONLY` (claimed in previous sprint reports, pending Phase 3 re-execution), `CONTRADICTED` (found inaccurate upon inspection).

---

## 1. Backend Core & Intelligence (`backend/shared/core/`)

| Path | Status | Purpose | Claimed Capability | Verification Status |
|---|---|---|---|---|
| `backend/shared/core/backtest.py` | `NEW` | Pure rolling-horizon backtest evaluation engine | Computes MAPE at 1h, 6h, 12h, 24h horizons over historical demand ticks | VERIFIED-TODAY |
| `backend/shared/core/depot_risk.py` | `NEW` | Pure depot stockout cover and supply risk calculator | Projects depot stock cover days and impacts of shipment delays / supply shortfalls | VERIFIED-TODAY |
| `backend/shared/core/detect.py` | `NEW` | Pure anomaly and crisis event detection engine | Detects demand spikes, route disruptions, station outages, depot constraints, drift | VERIFIED-TODAY |
| `backend/shared/core/explain.py` | `MODIFIED` | Explainability rationale generator | Extended to support candidate what-if simulation explanations | VERIFIED-TODAY |
| `backend/shared/core/metrics.py` | `MODIFIED` | Domain metrics evaluation functions | Added helper metrics for evaluation summary and risk classification | VERIFIED-TODAY |
| `backend/shared/core/models.py` | `MODIFIED` | Core domain Pydantic schemas | Added models for WhatIfCandidate, AlertIncident, VersionInfo, DepotRisk | VERIFIED-TODAY |
| `backend/shared/core/policies/base.py` | `MODIFIED` | Base allocation policy interface | Added reservation carrying support across passes | VERIFIED-TODAY |
| `backend/shared/core/policies/heuristic.py` | `MODIFIED` | Two-pass constrained triage with P90 buffer | Pass 1: critical 12h survival; Pass 2: balanced fill; enforces hard constraints | VERIFIED-TODAY |
| `backend/shared/core/policies/optimizer.py` | `NEW` | Constrained linear programming policy (SciPy) | Formulates replenishment as bounded LP with strict physical constraint vectors | VERIFIED-TODAY |
| `backend/shared/core/summarize.py` | `NEW` | Structured incident briefing engine | TemplateSummarizer rule-based default with bounded 3s LLM fallback | VERIFIED-TODAY |
| `backend/shared/core/version.py` | `NEW` | Version constants single source of truth | MODEL_VERSION = "1.1.0", POLICY_VERSION = "2.1.0" | VERIFIED-TODAY |
| `backend/shared/core/what_if.py` | `NEW` | Zero-DB pure candidate what-if simulation engine | Projects post-dispatch inventory, averted stockout, and feasibility in <50ms | VERIFIED-TODAY |

---

## 2. Backend API & Worker (`backend/api/`, `backend/worker/`, `intel/`)

| Path | Status | Purpose | Claimed Capability | Verification Status |
|---|---|---|---|---|
| `backend/api/database.py` | `MODIFIED` | Database access layer | Added query helpers for incidents, what-if logs, regional demand | VERIFIED-TODAY |
| `backend/api/db.sql` | `MODIFIED` | PostgreSQL relational schema | Added tables for alert_incidents, what_if_audits, rate limiting index | VERIFIED-TODAY |
| `backend/api/main.py` | `MODIFIED` | FastAPI application factory | Mounted new router endpoints, added startup health validation | VERIFIED-TODAY |
| `backend/api/routes/read.py` | `MODIFIED` | Operator read-only API routes | Exposes `/api/version`, `/api/incidents`, `/api/whatif`, `/api/depots/risk`, `/api/regional-demand`, `/api/evaluation/summary` | VERIFIED-TODAY |
| `backend/api/routes/recommendations.py` | `MODIFIED` | Allocation approval and decision routes | Enforces `hmac.compare_digest` token check and 60 req/min sliding-window rate limit | VERIFIED-TODAY |
| `backend/api/routes/chaos.py` | `MODIFIED` | Chaos injection endpoints | Maintained existing chaos endpoints with stricter error shapes | VERIFIED-TODAY |
| `backend/worker/main.py` | `MODIFIED` | Background ingestion daemon | Dynamic tick interval adaptation based on simulator speed; incident detection loop | VERIFIED-TODAY |
| `backend/worker/recommend_job.py` | `MODIFIED` | Automated proposal generation job | Invokes two-pass triage with P90 uncertainty safety buffer | VERIFIED-TODAY |
| `backend/worker/store.py` | `MODIFIED` | Ingestion data store | Saves regional demand snapshots, incident records, depot risk metrics | VERIFIED-TODAY |
| `intel/predictor/app/main.py` | `MODIFIED` | Predictor standalone microservice | Health and forecast routing parity; dual-port support | VERIFIED-TODAY |

---

## 3. Frontend Web Application (`web/src/`)

| Path | Status | Purpose | Claimed Capability | Verification Status |
|---|---|---|---|---|
| `web/src/app/App.tsx` | `MODIFIED` | Root application layout & routing | Renders new page routes, Header unread badge, and global Footer | VERIFIED-TODAY |
| `web/src/components/layout/Footer.tsx` | `NEW` | Global version and provenance footer | Displays Git SHA, tag, model/policy versions, and persistent SIMULATED tag | VERIFIED-TODAY |
| `web/src/components/layout/Header.tsx` | `MODIFIED` | Top navigation bar | Added live unread alert badge with dynamic count polling | VERIFIED-TODAY |
| `web/src/components/layout/PageNavigation.tsx` | `MODIFIED` | Navigation menu component | Added tabs for Alert Center, Network View, and Evaluation | VERIFIED-TODAY |
| `web/src/features/alerts/AlertCenterPage.tsx` | `NEW` | Crisis alert center view | Filterable incident list (severity, type, active/resolved) + Explain modal | VERIFIED-TODAY |
| `web/src/features/allocations/RecommendationsPage.tsx` | `MODIFIED` | Recommendation management view | Integrated What-If sandbox drawer launcher; review checkbox for needs_review | VERIFIED-TODAY |
| `web/src/features/allocations/WhatIfSimulator.tsx` | `NEW` | Candidate what-if simulation drawer | Interactive slider/input evaluating post-allocation inventory before approval | VERIFIED-TODAY |
| `web/src/features/dashboard/DashboardPage.tsx` | `MODIFIED` | Executive operations overview | Integrated regional demand breakdown, depot risk summary, and supply ETA | VERIFIED-TODAY |
| `web/src/features/demand/RegionalDemandPanel.tsx` | `NEW` | Regional fuel consumption breakdown | Visualizes fuel demand by region (Dhaka, Chittagong, etc.) and fuel product | VERIFIED-TODAY |
| `web/src/features/evaluation/EvaluationPage.tsx` | `NEW` | System accuracy and policy evaluation | Displays backtest MAPE by horizon and policy vs do-nothing comparison | VERIFIED-TODAY |
| `web/src/features/inventory/DepotRiskPanel.tsx` | `NEW` | Depot supply & stockout cover view | Shows cover days per depot and delayed/shortfall arrival impacts | VERIFIED-TODAY |
| `web/src/features/inventory/IncomingSupplyView.tsx` | `NEW` | Scheduled supply pipeline view | Shows pipeline of scheduled and in-transit supply arrivals with ETA ticks | VERIFIED-TODAY |
| `web/src/features/network/NetworkView.tsx` | `NEW` | Topological supply network view | Visual diagram of depots, retail stations, connecting corridors, and transit | VERIFIED-TODAY |
| `web/src/services/api.ts` | `MODIFIED` | Frontend API client service | Added typed fetch methods for new backend endpoints | VERIFIED-TODAY |
| `web/src/types/api.ts` | `MODIFIED` | TypeScript domain types | Added interfaces for VersionInfo, WhatIf, AlertIncident, RegionalDemand, DepotRisk | VERIFIED-TODAY |

---

## 4. Tests (`tests/`, `web/tests/`)

| Path | Status | Purpose | Verification Status |
|---|---|---|---|
| `tests/unit/test_backtest.py` | `NEW` | Unit tests for backtest accuracy computation across horizons | VERIFIED-TODAY |
| `tests/unit/test_depot_risk.py` | `NEW` | Unit tests for depot stock cover days and supply disruption curves | VERIFIED-TODAY |
| `tests/unit/test_detect.py` | `NEW` | Unit tests for pure event and anomaly detectors across 5 crisis types | VERIFIED-TODAY |
| `tests/unit/test_drift_detector.py` | `NEW` | Unit tests for calibration drift detection under demand shifts | VERIFIED-TODAY |
| `tests/unit/test_optimizer_and_buffer.py` | `NEW` | Unit tests for LP optimizer and P90 uncertainty safety buffer | VERIFIED-TODAY |
| `tests/unit/test_summarizer.py` | `NEW` | Unit tests for rule-based incident summarization and fallbacks | VERIFIED-TODAY |
| `tests/unit/test_token_and_rate_limit.py` | `NEW` | Unit tests for constant-time token comparison and 60 req/min rate limit | VERIFIED-TODAY |
| `tests/unit/test_triage_policy.py` | `NEW` | Unit tests for two-pass triage depot reservation carrying | VERIFIED-TODAY |
| `tests/unit/test_what_if.py` | `NEW` | Unit tests for pure what-if simulation calculations and constraints | VERIFIED-TODAY |
| `tests/unit/test_scenario_runner.py` | `MODIFIED` | Scenario runner regression tests | VERIFIED-TODAY |
| `tests/integration/test_chaos_api.py` | `MODIFIED` | Chaos endpoints integration tests | VERIFIED-TODAY |
| `tests/integration/test_depots_risk_api.py` | `NEW` | Integration tests for `/api/depots/risk` endpoint | VERIFIED-TODAY |
| `tests/integration/test_incidents_api.py` | `NEW` | Integration tests for `/api/incidents` and `/api/incidents/{id}/summary` | VERIFIED-TODAY |
| `tests/integration/test_predictor.py` | `MODIFIED` | Predictor service client integration tests | VERIFIED-TODAY |
| `tests/integration/test_read_api.py` | `MODIFIED` | Integration tests for `/api/version`, regional demand, evaluation | VERIFIED-TODAY |
| `tests/integration/test_whatif_api.py` | `NEW` | Integration tests for `POST /api/whatif` endpoint | VERIFIED-TODAY |
| `web/tests/App.test.tsx` | `MODIFIED` | Root UI rendering tests with Footer and SIMULATED badge | VERIFIED-TODAY |
| `web/tests/NewViews.test.tsx` | `NEW` | Frontend component unit tests for all 5 newly added views | VERIFIED-TODAY |

---

## 5. Scripts & Automation (`scripts/`)

| Path | Status | Purpose | Verification Status |
|---|---|---|---|
| `scripts/backtest.py` | `NEW` | CLI runner to execute backtest evaluation over tick history | VERIFIED-TODAY |
| `scripts/capture_day2_screenshots.js` | `NEW` | Historical screenshot capture script for Day 2 | VERIFIED-TODAY |
| `scripts/demo_clock.py` | `NEW` | Simulator speed control and clock advancement utility | VERIFIED-TODAY |
| `scripts/deploy.sh` | `NEW` | Automated production deploy script with health validation | VERIFIED-TODAY |
| `scripts/measure_resilience_boundaries.py` | `NEW` | Empirical benchmark script for crash recovery and traffic burst | VERIFIED-TODAY |
| `scripts/rollback.sh` | `NEW` | Automated rollback script triggered on failed deployment health check | VERIFIED-TODAY |
| `scripts/scenario_runner.py` | `MODIFIED` | Deterministic scenario evaluation runner (expanded to crisis scenarios) | VERIFIED-TODAY |
| `scripts/smoke.sh` | `MODIFIED` | Post-deploy smoke test verifying health of all services and new routes | VERIFIED-TODAY |
| `scripts/sprint_gate_public.sh` | `MODIFIED` | Public sprint gate validation script without private dependencies | VERIFIED-TODAY |
| `scripts/surprise_drill.sh` | `NEW` | Judging day rehearsal drill script for surprise events/faults | VERIFIED-TODAY |
| `scripts/trace_decision.py` | `NEW` | Decision lifecycle correlation trace script | VERIFIED-TODAY |

---

## 6. Crisis Scenarios (`scenarios/`)

| Path | Status | Purpose | Verification Status |
|---|---|---|---|
| `scenarios/crisis_combined.yaml` | `NEW` | Compound scenario with simultaneous demand spike and route disruption | VERIFIED-TODAY |
| `scenarios/depot_constraint.yaml` | `NEW` | Depot constraint scenario testing dispatch capacity limits | VERIFIED-TODAY |
| `scenarios/shipment_delay.yaml` | `NEW` | Inbound supply shipment delay scenario testing depot risk projection | VERIFIED-TODAY |
| `scenarios/station_outage.yaml` | `NEW` | Station outage scenario verifying zero recommendations to offline stations | VERIFIED-TODAY |
| `scenarios/supply_shortfall.yaml` | `NEW` | Inbound supply quantity shortfall scenario | VERIFIED-TODAY |

---

## 7. CI/CD & Observability (`.github/`, `observability/`, `loadtest/`)

| Path | Status | Purpose | Verification Status |
|---|---|---|---|
| `.github/workflows/ci.yml` | `MODIFIED` | GitHub Actions CI with Gitleaks and npm audit security jobs | VERIFIED-TODAY |
| `.github/workflows/release.yml` | `NEW` | Automated GHCR multi-image build, tag, and publish workflow | VERIFIED-TODAY |
| `.gitleaks.toml` | `NEW` | Gitleaks secret scanning configuration and allowlist rules | VERIFIED-TODAY |
| `observability/prometheus/alert_rules.yml` | `NEW` | Prometheus alerting rules as code with runbook URLs | VERIFIED-TODAY |
| `observability/prometheus/prometheus.yml` | `MODIFIED` | Mounts and loads alerting rules file | VERIFIED-TODAY |
| `loadtest/k6.js` | `MODIFIED` | k6 load test script benchmarking `POST /api/whatif` under load | VERIFIED-TODAY |
| `loadtest/summary.json` | `MODIFIED` | k6 raw execution metrics summary | VERIFIED-TODAY |

---

## 8. Documentation (`docs/`)

| Path | Status | Purpose | Verification Status |
|---|---|---|---|
| `docs/BRIEF-COMPLIANCE.md` | `NEW` | 26-section Hackathon brief compliance audit matrix | VERIFIED-TODAY |
| `docs/DAY-2-UPDATE.md` | `NEW` | Day 2 milestone progress and architecture update | VERIFIED-TODAY |
| `docs/JUDGING-DAY.md` | `NEW` | Judging day presentation script, demo runbook, and contingency protocols | VERIFIED-TODAY |
| `docs/event-handling.md` | `NEW` | Crisis event handling architecture and scenario specifications | VERIFIED-TODAY |
| `docs/sprint-reports/sprint-08.md` | `NEW` | Sprint 8 gate completion report | VERIFIED-TODAY |
| `docs/sprint-reports/sprint-09.md` | `NEW` | Sprint 9 gate completion report | VERIFIED-TODAY |
| `docs/sprint-reports/sprint-10.md` | `NEW` | Sprint 10 gate completion report | VERIFIED-TODAY |
| `docs/reviews/sprint-08-audit.md` | `NEW` | Adversarial audit findings and resolutions for Sprint 8 | VERIFIED-TODAY |
| `docs/reviews/sprint-08-self-review.md` | `NEW` | Code review findings for Sprint 8 | VERIFIED-TODAY |
| `docs/reviews/sprint-10-review.md` | `NEW` | Strict code review findings for Sprint 10 (R4, R5, R6, R7, D6) | VERIFIED-TODAY |
| `docs/evidence/sprint-10-rollback-drill.txt` | `NEW` | Raw terminal execution log of automated rollback drill | VERIFIED-TODAY |
| `docs/evidence/sprint-10-resilience-matrix.txt` | `NEW` | Raw benchmark output of service crash and recovery timings | VERIFIED-TODAY |
| `docs/evidence/sprint-10-decision-trace.txt` | `NEW` | End-to-end trace of decision correlation ID across lifecycle | VERIFIED-TODAY |
