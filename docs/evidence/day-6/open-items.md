# Day 6 Open Items & Work Package Inventory

**Generated:** 2026-11-24T12:44:00+06:00  
**Repository Branch:** `day-6-7` (branched from `main` after verified merge of PR #3 `9f992d4`)  
**Purpose:** Comprehensive baseline audit of all Sprint 11–13 work packages, known issues, reviews, CI statuses, and brief compliance to drive Day 6 execution.

---

## 1. Sprint 11–13 Work Package Status Audit

| WP ID | Description | Priority | Claimed Status | Verified Today | Notes & Evidence Path |
|---|---|:---:|:---:|:---:|---|
| **WP11.0** | Truth pass on Day 3 claims, physical boundary arithmetic, compliance recount | P0 | DONE-VERIFIED | DONE-VERIFIED | 91,400 L/day demand arithmetic verified in `core/world.py`. Terminology audited. `docs/DAY-3-UPDATE.md`. |
| **WP11.1** | Measured failure boundary across 192 ticks, binding constraints, plot | P0 | DONE-VERIFIED | DONE-VERIFIED | 11 unit tests in `tests/unit/test_failure_boundary.py` pass. Plot and summary in `docs/results/failure-boundary.*`. |
| **WP11.2** | Robust policy evaluation across 60 randomized crisis scenarios (95% bootstrap CI) | P0 | DONE-VERIFIED | DONE-VERIFIED | 6 unit tests in `tests/unit/test_scenario_sweep.py` pass. 240 live runs reported in `docs/results/scenario-sweep.md`. Single loss disclosed (`holdout_08`). |
| **WP11.3** | Event-aware calibration, 0-tick convergence, Brier score, model v1.2.0 | P1 | DONE-VERIFIED | DONE-VERIFIED | 4 unit tests in `tests/unit/test_forecast_event_aware.py` pass. Brier score 0.1558 in `docs/results/event-calibration.md`. |
| **WP11.4** | Clear pip-audit advisories, upgrade fastapi/pytest, add dependabot | P0 | DONE-VERIFIED | DONE-VERIFIED | `.github/dependabot.yml` active. pip-audit (0 vulns), npm audit (0 vulns), Gitleaks (0 leaks). |
| **WP11.5** | Tick length 8 vs 15 compatibility verified | P0 | DONE-VERIFIED | DONE-VERIFIED | 12 unit tests in `tests/unit/test_tick_compatibility.py` pass. Invariance verified in `docs/results/tick-compatibility.md`. |
| **WP12.1** | API performance optimization (multi-worker uvicorn, indexes, byte-level caching, 3.1x throughput) | P0 | DONE-VERIFIED | DONE-VERIFIED | 3 unit tests in `tests/unit/test_api_caching_and_rate_limit.py` pass. 625.8 req/s throughput in `docs/loadtest.md`. |
| **WP12.2** | Push update invalidation stream with PostgreSQL LISTEN/NOTIFY and polling fallback | P1 | DONE-VERIFIED | DONE-VERIFIED | 7 unit tests in `tests/unit/test_sse_stream.py` pass. `useEventStream.ts` active. 95% traffic reduction measured. |
| **WP12.3** | Soak test script, time series telemetry, and stability summary | P0 | DONE-VERIFIED | DONE-VERIFIED | `scripts/soak_test.sh` and `run_soak_test.py` verified; 90-minute soak in `docs/results/soak-test-summary.md`. |
| **WP12.4** | Alertmanager and webhook receiver under alerts profile with verified fire/resolve routing | P1 | DONE-VERIFIED | DONE-VERIFIED | Verified in `docs/evidence/day-4/alert-routing-evidence.json`. Docker compose profile `alerts` isolated. |
| **WP12.5** | Backup, restore drill, and measured 3-part recovery times | P0 | DONE-VERIFIED | DONE-VERIFIED | 2 unit tests in `tests/unit/test_backup_restore_idempotency.py` pass. 2.93s RTO in `docs/results/backup-restore-drill.json`. |
| **WP12.6** | Runtime policy switch with automatic rollback, auditing, and constraint validation | P2 | DONE-VERIFIED | DONE-VERIFIED | 6 unit tests in `tests/unit/test_policy_switch_and_rollback.py` pass. `policy_changes` table and API active. |
| **WP13.1** | Playwright E2E suite (12 browser scenarios) in CI | P0 | DONE-VERIFIED | DONE-VERIFIED | 12 tests in `tests/e2e/platform.spec.ts`. Sibling directory resolution and discovery guard verified in CI run 45151386337. |
| **WP13.2** | Usability and axe-core accessibility audit (0 critical violations) | P0/P1 | DONE-VERIFIED | DONE-VERIFIED | `docs/evidence/day-4/accessibility-audit.md` (90/100 subpages, 0 critical violations). Operator name, export buttons, guided tour active. |
| **WP13.3** | Demo director, preflight script, rehearsals, and offline backup pack | P0 | DONE-VERIFIED | DONE-VERIFIED | `scripts/preflight_judging.sh` and `scripts/demo_director.py` verified. 3 rehearsals in `docs/evidence/day-4/demo-rehearsal-*.json`. |
| **WP13.4** | Documentation consolidation, problem understanding, architecture diagrams, claims ledger | P0 | DONE-VERIFIED | DONE-VERIFIED | `docs/README.md`, `PROBLEM-UNDERSTANDING.md`, `architecture.md`, `qa.md`, `DAY-4-UPDATE.md`, `DAY-5-UPDATE.md` consolidated. |
| **WP13.5** | Multi-perspective audit, brief compliance recount, and release notes v1.0.0 | P0 | DONE-VERIFIED | DONE-VERIFIED | `docs/reviews/sprint-13-audit.md`, `docs/RELEASE-NOTES-v1.0.0.md`, all 109 brief items MET. |

---

## 2. CI Status and Hosted Workflow Inventory

- **Run ID 45151386337** (PR #3 pull_request event, commit `a8a2f45`): **SUCCESS (GREEN)** across all 4 jobs (`python`, `frontend`, `compose`, `security`).
- **Run ID 45151374668** (sprints-11-13 push event, commit `a8a2f45`): **SUCCESS (GREEN)** across all jobs.
- **Root Cause of previous failure (DEF-01):** Clean checkout in CI lacked local `node_modules -> web/node_modules` symlink. Node failed to resolve `@playwright/test` across sibling directory boundary.
- **Permanent Solution:**
  1. `NODE_PATH: web/node_modules` in `.github/workflows/ci.yml`.
  2. `moduleAlias._initPaths()` dynamic registration in `web/playwright.config.ts`.
  3. Fail-fast discovery guard step (`npm --prefix web run test:e2e -- --list`) failing in < 2 seconds if module resolution ever breaks.

---

## 3. Open Items for Day 6 & Day 7 Execution

The following items are identified for Day 6 (Sprint 14) and Day 7 (Sprint 15):

### P0 Priority:
1. **Full Defect & Security Hunt (Day 6, WP14.1):**
   - Run `make lint`, `make test`, `make smoke`, `make test-e2e`.
   - Run `actionlint` across GitHub Actions workflows.
   - Run `scripts/verify_clean_clone.sh` to ensure clean clone test discovery and execution.
   - Scan for secrets (`gitleaks`), dependency vulnerabilities (`pip-audit`, `npm audit`, `trivy`), forbidden files (`AGENTS.md`, `.env`, etc.), and file sizes (> 5 MB).
   - Domain keyword check (`git grep -i "refinery\|pipeline capacity\|corridor throughput\|chittagong\|conservation law\|reverse proxy"`).
2. **Deterministic Story & Fresh Browser Evidence (Day 7, WP15.1):**
   - Execute deterministic browser audit across all routes and capture status codes, console errors, load times, and axe-core violations into `docs/evidence/day-7/browser-audit.md`.
   - Capture 20+ fresh high-resolution screenshots at 1440x960 2x into `docs/evidence/day-7/screens/` with `MANIFEST.md`.
   - Perform live human approval flow using `OPERATOR_TOKEN` via real API.
   - Capture degraded mode banner under controlled fault and recovery.
   - Leave simulator PAUSED, faults cleared, stack healthy.
3. **Master README Completion (Day 7, WP15.2):**
   - Preserve owner-written content and tone.
   - Complete "PROOF BY DAY" section for all 7 days (Day 1 through Day 7) with real verified metrics, links, and screenshots.
   - Ensure 100% of relative links and images resolve.
4. **Final Presentation Pack (Day 7, WP15.3):**
   - Create `docs/presentation/PITCH-10MIN.md` (timed script matching brief demo story).
   - Create `docs/presentation/SLIDES.md`, `slides.html`, and `slides.pdf` from real screenshots (12–15 slides).
   - Create `docs/presentation/QA-CHEATSHEET.md` with empirical, evidence-backed answers.
   - Create `docs/presentation/BACKUP-PLAN.md` with contingency steps.
   - Rehearse 3 times with `scripts/demo_director.py` and log timings to `docs/evidence/day-7/rehearsal.md`.
5. **Sprint Reports & Readiness Documents (Day 6 & Day 7):**
   - Author `docs/sprint-reports/sprint-14.md` and `docs/DAY-6-UPDATE.md`.
   - Author `docs/sprint-reports/sprint-15.md` and `docs/DAY-7-UPDATE.md`.
   - Build `docs/evidence/day-7/claims-ledger.md` mapping every number to reproducible commands.
   - Execute multi-perspective audits (R1, R3, R4, R5, R6, R7, D6) in `docs/reviews/day-6-7-audit.md`.
6. **Publishing & Release Packaging:**
   - Push branch `day-6-7` to origin.
   - Create Pull Request for `day-6-7` into `main`.
   - Monitor CI until green.
   - Merge PR into `main` (`PUBLISH_MODE=merge_when_green`).
   - Create annotated tag `v1.0.0` on `main`.
   - Update repository description and topics (`REPO_METADATA=yes`).
   - Leave `reference/` intact (`REFERENCE_FOLDER=keep`).
   - Retain explicit owner-only checklist (license choice, live human rehearsals, video recording).
