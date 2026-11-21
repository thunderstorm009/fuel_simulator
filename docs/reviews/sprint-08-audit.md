# Sprint 8 Pre-Implementation Audit Report

- **Date:** 2026-11-21
- **Branch:** `sprints-8-10`
- **Auditor:** Engineering Agent (adversarial audit of post-Sprint-7 commits and codebase against SPRINT-08 and BRIEF requirements)
- **Status:** AUDIT COMPLETE; REMEDIATION IN PROGRESS

---

## 1. Audit Scope & Methodology

This audit evaluates the codebase at the head of `sprints-8-10` (commits since tag `sprint-7`: `8ab932e` and `dc7f60f`) against:
1. Hard safety rules in platform engineering guidelines (no auto-approval in app/worker, no `/admin` in app code, secret hygiene, simulator integrity).
2. The Sprint 8 specification (WP8.0 through WP8.5).
3. The official BUP Hackathon Brief (`reference/`) and requirement gap analysis.

Evidence is derived from direct command execution (`git grep`, `pytest`, `docker compose`, API curls) rather than existing summaries.

---

## 2. Audit Checklist Results

| Checklist Item | Category | Target | Result | Real Output / Evidence |
|---|---|---|---|---|
| **A.1 Auto-Approve Check** | Safety | `backend web intel` | **PASS** | `git grep -n -i "auto_approve\|autoapprove\|auto-approve" -- backend web intel` returned 0 hits. |
| **A.2 Admin Route Check** | Safety | `backend web intel` | **FAIL (P0)** | Hits in `backend/api/routes/chaos.py:31` (`/admin/fail`) and `intel/predictor/app/main.py:105` (`@app.post("/admin/fail")`). App code must contain no `/admin` routes. |
| **A.3 Secret Scan** | Safety | `git log -p sprint-7..HEAD` | **PASS** | `git log -p sprint-7..HEAD \| grep -nE "OPERATOR_TOKEN=\|POSTGRES_PASSWORD=\|AKIA\|BEGIN .*PRIVATE KEY"` returned 0 secrets. |
| **A.4 Simulator State** | Safety | Live Simulator | **PASS** | `curl http://localhost:8000/v1/instance` confirms status `PAUSED` at tick 0. Active events: `[]`. Faults: all `active: false`. |
| **B.1 Code Quality Gates** | Quality | Lint, Test, Config | **PASS** | 141 Python tests pass; 6 Vitest tests pass; `ruff check` and `ruff format` clean; `docker compose config -q` clean. |
| **B.2 Mechanical Gate Script** | Quality | `scripts/sprint_gate_public.sh` | **FAIL (P1)** | Script restricted to sprints 1–7 regex (`^[1-7]$`); needs update for Sprint 8–10. |
| **C.1 Truth Pass Grep** | Accuracy | Tracked files | **FAIL (P0)** | Falsehoods found: "vehicle quotas" in `README.md:40`, `docs/DAY-2-UPDATE.md:17`; "price spikes" in `docs/DAY-2-UPDATE.md:30`; "cryptographically stable" in `docs/DAY-2-UPDATE.md:49`; "independent review" in docs when self-reviewed. |
| **C.2 Git Tag Claims** | Accuracy | `docs/DAY-2-UPDATE.md` | **FAIL (P0)** | Day 2 update claims tags `S1`, `S2`, `S3` exist. `git tag` output shows only `sprint-0`, `sprint-4`, `sprint-5`, `sprint-6`, `sprint-7`. |
| **C.3 README Results Table** | Accuracy | `README.md` | **FAIL (P1)** | README lacks the explicit do-nothing vs naive vs heuristic table citing `docs/results/scenario-summary.md`. |
| **D.1 Brief Compliance Matrix** | Compliance | `docs/BRIEF-COMPLIANCE.md` | **FAIL (P1)** | File absent. Must document sections 4–26 with evidence or planned sprint. |
| **E.1 Event Scenarios** | Features | `scenarios/` | **FAIL (P0)** | Missing `shipment_delay.yaml`, `depot_constraint.yaml`, `station_outage.yaml`, `supply_shortfall.yaml`, and combined crisis. |
| **E.2 Event Handling Doc** | Features | `docs/event-handling.md` | **FAIL (P1)** | File absent. |
| **E.3 Constrained Triage** | Engine | `core/policies/heuristic.py` | **FAIL (P0)** | Two-pass emergency triage (12h stockout removal first, then top-up) and unserved-need reasons not yet implemented. |
| **F.1 Detection Layer** | Intelligence | `core/detect.py`, API, Worker | **FAIL (P0)** | Pure detector module, `GET /api/incidents`, `detections_total` metric, and worker job do not exist. |
| **G.1 Depot Supply Risk** | Risk | `core/`, `/api/depots/risk`, UI | **FAIL (P1)** | Depot cover projection, risk endpoint, and UI panel do not exist. |
| **H.1 Running-Simulator Robustness** | Resilience | Speed tests, demo clock | **FAIL (P0)** | Speed benchmarks (1, 4, default) not measured; `scripts/demo_clock.py` absent; tick-aware freshness warning banner needed. |

---

## 3. Findings Register

### Priority P0 (Unsafe, Inaccurate, or Violates Hard Rules)
- **F-01 [P0]: `/admin` endpoint in predictor and chaos route**
  - *File/Line:* `intel/predictor/app/main.py:105`, `backend/api/routes/chaos.py:31`
  - *Evidence:* `git grep -n "/admin" -- backend web intel` matched `@app.post("/admin/fail")` and `/admin/fail`.
  - *Fix:* Rename predictor endpoint to `/chaos/fail` and update chaos client and integration tests.
- **F-02 [P0]: Inaccurate statements in public docs and README**
  - *File/Line:* `README.md:40, 293`, `docs/DAY-2-UPDATE.md:17, 30, 49`, `docs/ai-usage.md:26`
  - *Evidence:* Grep hits for "vehicle quota" (simulator has no vehicle quotas), "price spikes" (simulator has no pricing), "cryptographically stable" (stored UUID keys), "independent review" (agent self-reviews).
  - *Fix:* Replace with truthful descriptions: route max shipment, depot dispatch capacity, stored stable idempotency keys, self-reviewed with code-review-strict skill.
- **F-03 [P0]: Non-existent tags in Day 2 update**
  - *File/Line:* `docs/DAY-2-UPDATE.md:66-68`
  - *Evidence:* Mentions `S1`, `S2`, `S3`. `git tag` contains only `sprint-0`, `sprint-4`, `sprint-5`, `sprint-6`, `sprint-7`.
  - *Fix:* Correct table to reflect real git tags.
- **F-04 [P0]: Missing crisis event scenarios and handling**
  - *File:* `scenarios/*.yaml`, `core/policies/heuristic.py`, `docs/event-handling.md`
  - *Evidence:* Only 4 scenarios exist. Six simulator event types are defined in integration guide; four lack scenarios.
  - *Fix:* Create the 5 missing scenarios, implement handling (station outage rejection, depot constraint awareness, shipment delay & shortfall cover adjustments), run scenario runner, and write `docs/event-handling.md`.
- **F-05 [P0]: Missing two-pass triage in heuristic policy**
  - *File:* `backend/shared/core/policies/heuristic.py`
  - *Evidence:* Current heuristic uses single-pass greedy allocation without two-pass triage (pass 1: 12h emergency cover; pass 2: top-up), and does not record unserved-need reasons.
  - *Fix:* Implement two-pass triage algorithm with priority ranking, partial allocations, and explicit unserved rationale.
- **F-06 [P0]: Missing pure detection engine**
  - *File:* `backend/shared/core/detect.py`, `backend/worker/jobs.py`, `backend/api/routes/`
  - *Evidence:* No incident detection module exists.
  - *Fix:* Implement pure functions for demand anomaly, regional surge, abnormal inventory, bottleneck, emerging regional disruption; add worker persistence and `GET /api/incidents`.
- **F-07 [P0]: Simulator speed robustness and demo clock**
  - *File:* `scripts/demo_clock.py`, `backend/api/routes/state.py`, `web/src/`
  - *Evidence:* Platform not benchmarked at simulation speeds 1, 4, default; no demo clock script; no tick rate freshness indicator.
  - *Fix:* Measure speeds, build `demo_clock.py`, expose tick rate in `/api/state`, add UI warning banner.

### Priority P1 (Broken, Unproven, or Incomplete Scope)
- **F-08 [P1]: Missing Brief Compliance Matrix**
  - *File:* `docs/BRIEF-COMPLIANCE.md`
  - *Fix:* Construct comprehensive matrix covering sections 4–26 with evidence paths.
- **F-09 [P1]: Missing Depot Supply Risk Projection**
  - *File:* `backend/shared/core/depot_risk.py`, `/api/depots/risk`, UI panel
  - *Fix:* Implement depot cover calculation, API route, and frontend panel.
- **F-10 [P1]: README Results section incomplete**
  - *File:* `README.md`
  - *Fix:* Insert full scenario benchmark comparison table citing `docs/results/scenario-summary.md`.
- **F-11 [P1]: Sprint gate script bounds**
  - *File:* `scripts/sprint_gate_public.sh`
  - *Fix:* Update regex to support sprints 1–10.

---

## 4. Remediation Execution Plan

1. **Step 1 (WP8.0 Truth Pass & Admin Route Remediation):**
   - Fix `/admin/fail` in predictor and chaos route.
   - Clean all falsehoods from README and docs.
   - Align git tag table in Day 2 update.
   - Add Results comparison table to README.
2. **Step 2 (WP8.1 Brief Compliance Matrix):**
   - Read and map brief sections 4–26 into `docs/BRIEF-COMPLIANCE.md`.
3. **Step 3 (WP8.2 Event Scenarios, Triage Engine & Documentation):**
   - Add 5 crisis scenarios.
   - Implement two-pass triage in `core/policies/heuristic.py`.
   - Add unit tests for triage and event rules.
   - Run scenario runner and record results.
   - Write `docs/event-handling.md`.
4. **Step 4 (WP8.3 Pure Detection Layer):**
   - Implement `core/detect.py` with 5 pure detectors.
   - Add DB schema/table and API endpoint `/api/incidents`.
   - Add worker job and Prometheus metric `detections_total`.
   - Add UI incident list.
5. **Step 5 (WP8.4 Depot Risk Engine):**
   - Implement depot cover projection in `core/`.
   - Add endpoint `GET /api/depots/risk` and UI panel.
6. **Step 6 (WP8.5 Running-Simulator Robustness):**
   - Measure simulator at speeds 1, 4, and default.
   - Implement `scripts/demo_clock.py`.
   - Expose tick rate and freshness in `/api/state` and UI warning banner.
7. **Step 7 (Sprint 8 Gate & Tag):**
   - Run full test suite, lint, smoke, and mechanical sprint gate.
   - Self-review with `code-review-strict`.
   - Write `docs/sprint-reports/sprint-08.md`.
   - Tag `sprint-8`.
