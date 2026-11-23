# Day 5 Engineering Update: Errors Found, Root Causes, and Permanent Fixes

- **Project:** Fuel Supply Intelligence & Resilience Platform
- **Event:** BUP CSE Fest 2026 Hackathon
- **Date:** 2026-11-23
- **Repository:** [https://github.com/thunderstorm009/fuel_simulator](https://github.com/thunderstorm009/fuel_simulator)
- **Branch:** `sprints-11-13`
- **Focus:** Complete, transparent disclosure of every bug, CI failure, documentation falsehood, and architectural defect uncovered and permanently resolved during Days 4 and 5.

---

## 1. Executive Summary & The Truth Principle

The core tenet of this engineering initiative is the **Truth Rule**:  
*Never claim a result you did not verify; never fabricate numbers or evidence; and honestly disclose errors rather than concealing them.*

Engineering maturity is demonstrated not by claiming flawless first-attempt execution, but by rigorous root-cause debugging, transparent post-mortems, and permanent regression guards. This document chronicles the defects discovered across GitHub Actions CI, runtime container configuration, local environment drift, and documentation claims, detailing the precise mechanism of each failure, the code and configuration changes implemented, and the automated tests preventing regression.

---

## 2. The Hosted CI Failure: Deep Dive

### 2.1 Symptom and Error Log
In GitHub Actions CI on Pull Request #3 (`sprints-11-13`), run **45139851657**, the `python`, `frontend`, and `security` jobs passed cleanly, but the `compose` job failed at the step:
`Run Playwright E2E and Accessibility Suite` after 23 seconds.

The execution log showed:
```text
> fuel-supply-platform-frontend@0.1.0 test:e2e
> playwright test

Error: No tests found
at tests/e2e/platform.spec.ts:1:1
import { test, expect } from "@playwright/test";
^
Error: Cannot find module '@playwright/test'
Process completed with exit code 1.
```

### 2.2 Root Cause Analysis in Plain Words
Why did local development pass while GitHub Actions CI failed?
1. **Directory Structure Separation:** The Playwright test specifications reside in `<repo_root>/tests/e2e/platform.spec.ts` (alongside `tests/unit/` and `tests/integration/`). The frontend and its npm dependencies reside in `<repo_root>/web/` with `@playwright/test` and `@axe-core/playwright` installed inside `<repo_root>/web/node_modules/`.
2. **Node.js Module Resolution Algorithm:** When Node evaluates an `import { test } from "@playwright/test"` inside a file located at `<repo_root>/tests/e2e/platform.spec.ts`, it searches:
   - `<repo_root>/tests/e2e/node_modules/`
   - `<repo_root>/tests/node_modules/`
   - `<repo_root>/node_modules/`
   - Global Node module paths.
   Crucially, Node **never traverses sideways** into sibling directory `<repo_root>/web/node_modules/` unless instructed via `NODE_PATH` or custom module loaders.
3. **The Developer Environment Mask:** In the local developer workspace, an untracked root-level symlink `node_modules -> web/node_modules` existed (ignored by `.gitignore`). As a result, local test runs resolved `@playwright/test` seamlessly through the root symlink.
4. **The Clean CI Clone Failure:** GitHub Actions CI performs a clean `actions/checkout` without untracked symlinks. When `npm --prefix web run test:e2e` ran, Playwright executed, found `tests/e2e/platform.spec.ts`, but Node failed to import `@playwright/test`. Playwright swallowed the module import exception and reported: `Error: No tests found`.

### 2.3 The Permanent Fix
We resolved this across three defense layers:
1. **Explicit `NODE_PATH` in `web/package.json`:**
   ```json
   "scripts": {
     "test:e2e": "NODE_PATH=node_modules playwright test"
   }
   ```
2. **In-Process Module Search Path Initialization (`web/playwright.config.ts`):**
   ```ts
   import moduleAlias from "module";

   const webNodeModules = path.resolve(__dirname, "node_modules");
   if (process.env.NODE_PATH) {
     process.env.NODE_PATH = `${webNodeModules}:${process.env.NODE_PATH}`;
   } else {
     process.env.NODE_PATH = webNodeModules;
   }
   // @ts-expect-error Node internal method to re-initialize module search paths
   if (typeof moduleAlias._initPaths === "function") {
     // @ts-expect-error Node internal method to re-initialize module search paths
     moduleAlias._initPaths();
   }
   ```
3. **Workflow Environment Configuration (`.github/workflows/ci.yml`):**
   Set `NODE_PATH: web/node_modules` in the `compose` job steps.

### 2.4 The Fail-Fast Discovery Guard
To ensure any future module resolution, syntax, or test registration regression is caught in **<2 seconds** without waiting for browser downloads or test timeouts, we added a dedicated verification step before the e2e suite in `.github/workflows/ci.yml`:
```yaml
      - name: Verify Playwright Test Discovery
        run: |
          npm --prefix web run test:e2e -- --list
        env:
          NODE_PATH: web/node_modules
```
This command runs `playwright test --list`. If zero tests are discovered or if module imports fail, the workflow fails immediately with the explicit stack trace.

### 2.5 CI Attempts & Resolution Ledger

| Attempt | Commit | Run ID | Job | Step | Result | Root Cause / Note |
|---|---|---|---|---|---|---|
| #1 (Initial) | `8b9f1f0` | `45139851657` | `compose` | Run Playwright E2E | **FAIL** | `Cannot find module '@playwright/test'` due to clean clone sibling directory resolution. |
| #2 (Fixed) | `cd9cf4b` | Automated | `compose` | Run Playwright E2E | **PASS** | Applied `NODE_PATH` fix, `_initPaths()` fallback, and fail-fast discovery guard. All 12 tests pass in 28.9s. |

---

## 3. Defects Found and Fixed on Days 4 & 5

The following table documents every bug and defect identified, diagnosed, and resolved during Days 4 and 5:

| ID | Sev | Subsystem | File / Component | Symptom & Discovery Method | Root Cause | Fix Applied | Regression Test / Guard | Evidence Path |
|---|---|---|---|---|---|---|---|---|
| **DEF-01** | **P0** | CI / E2E | `web/package.json`, `web/playwright.config.ts`, `.github/workflows/ci.yml` | `compose` job failed with `Error: No tests found` at `platform.spec.ts:1:1` | Sibling directory module resolution failure for `@playwright/test` in clean clone | Added `NODE_PATH=node_modules`, `moduleAlias._initPaths()` in config, and discovery guard step | `tests/unit/test_playwright_discovery.py`, `scripts/verify_clean_clone.sh` | `docs/decisions.md` (ADR-049), `docs/evidence/day-4/playwright.log` |
| **DEF-02** | **P1** | Tooling | `scripts/demo_director.py` | `ruff check` failed with 13 E501 errors | Command-line argument help strings exceeded 100 characters | Wrapped strings and multiline help text across lines | `ruff check scripts/demo_director.py`, `make lint` | Clean `make lint` output (111 files) |
| **DEF-03** | **P1** | Runtime | `.env` | Worker crashed on startup with `InvalidPasswordError` | Old local `.env` had `DATABASE_URL` with password `fuel` while omitting `POSTGRES_PASSWORD`, causing Compose default `fuel-local` mismatch | Aligned `.env` to canonical `.env.example` with `POSTGRES_PASSWORD=fuel-local` | `python3 scripts/check_compose_env.py` | `scripts/check_compose_env.py` passed; `make smoke` passed |
| **DEF-04** | **P2** | Frontend | `scripts/capture_day4_screenshots.js` | Guided tour screenshot omitted (`02-guided-tour.png`) on warm browser context | `localStorage` persistent flag `platform_tour_dismissed` prevented modal from rendering on fresh visit | Added explicit selector targeting `button[aria-label="Interactive Judging Tour"]` to force-open tour | `node scripts/capture_day4_screenshots.js` | `docs/evidence/day-4/screens/MANIFEST.md` |
| **DEF-05** | **P2** | Docs | `docs/PROBLEM-UNDERSTANDING.md` | Keyword scan flagged "Chittagong", "refinery feeder", "pipeline resupply" | Informal external supply chain terminology used instead of simulator-grounded concepts | Corrected to "Chattogram Division", "bulk storage depot", and "scheduled supply resupply factor" | `git grep -i "refinery\|pipeline capacity\|chittagong"` | `docs/evidence/day-4/verification.md` |
| **DEF-06** | **P2** | Script | `scripts/verify_clean_clone.sh` | Discovery check failed when invoked directly via `npx` from root without `--config` | Playwright defaulted to scanning root `tests/` and evaluated Vitest tests `web/tests/App.test.tsx` containing `import.meta.env` | Invoked test discovery via `npm --prefix web run test:e2e -- --list` so Playwright runs from `web/` | `bash scripts/verify_clean_clone.sh` | `docs/evidence/clean-clone-check.txt` |

---

## 4. Documentation Claims Corrected

In accordance with our empirical auditing standard, the following previous claims were identified as unsupported, derived without arithmetic, or based on incomplete counts, and were formally corrected:

| Topic | Previous Claim | Corrected Reality | Reason & Empirical Evidence |
|---|---|---|---|
| **Brief Coverage Count** | "26 sections covered" or "52 items" | **109 discrete requirements (100% MET/OPTIONAL)** | Day 3 counted high-level document headers; comprehensive audit in `docs/BRIEF-COMPLIANCE.md` systematically mapped all 109 atomic clauses across sections 4 through 26. |
| **Physical Bottlenecks** | "Depot dispatch capacity is 23,000 L/tick" | **Route truck shipment cap (5-7k L)** is the true binding constraint | Depots provide 24x average demand (91.4k L/day / 96 ticks = 952 L/tick). Stress sweeps proved depot dispatch is never the bottleneck; truck capacities and corridor transit times bind first (`scripts/measure_failure_boundaries.py`). |
| **Spike Adaptation Lag** | Model adapts via EWMA ratio | Model v1.1.0 had **7–19 tick lag** on spikes; upgraded to **Event-Aware v1.2.0 (0-tick lag)** | Empirical measurement revealed EWMA ratio required 7 ticks to track a 2.0x surge. Model v1.2.0 incorporates active event multipliers directly into expected demand (`tests/unit/test_forecast_event_aware.py`). |
| **API Throughput** | "320 req/s across 205k requests" | Saturated at **201 req/s** at 100 VUs; optimized to **625.8 req/s** at 200 VUs | Sprint 6 load test used light read paths. Rigorous k6 stress test in Sprint 12 exposed Seq Scans and Uvicorn single-worker saturation, resolved via 4 workers, pooling, and indexes (`docs/loadtest.md`). |
| **What-If Latency** | "<50ms unloaded, ~834ms under 100 VU load" | **<50ms unloaded, 288.3ms under 200 VU load** | Database indexing and model caching cut loaded What-If p95 latency from 834ms to 288.3ms, beating the 500ms target (`loadtest/summary.json`). |
| **Scenario Evaluations** | 54 scenario runs across 9 scenarios | **240 live simulation runs** across 60 randomized crisis scenarios | Expanded from 9 hand-crafted scenarios to 60 randomized seeds (seed=42) with 95% bootstrap confidence intervals and honest loss disclosure (`docs/results/scenario-sweep-summary.md`). |
| **Database RTO** | "Restores clean schema in ~34s (compose down -v)" | Measured **2.93 seconds RTO** for complete PostgreSQL restore drill | Cold-start container provisioning takes 34s; actual database schema and data restoration takes 2.93s (`scripts/drill_backup_restore.py`). |
| **Client Read Traffic** | 5-second polling interval across all clients | **95% reduction in read polling** via SSE push invalidation | In Sprint 12, added `GET /api/stream` using PostgreSQL `LISTEN/NOTIFY`, pushing invalidation hints only when state changes (`loadtest/summary.json`). |

---

## 5. Items Still Open and Operational Boundaries

The following items represent intentional operational boundaries and human-owner responsibilities recorded in `docs/known-issues.md`:

1. **Simulator Connection Prerequisite:** The platform API and web frontend read exclusively from PostgreSQL, allowing historical browsing while disconnected, but live data ingestion requires the simulator container to be accessible. If disconnected, data age is flagged and degraded banners are shown.
2. **Optional LLM Incident Summarization:** Natural language incident explanations (`backend/shared/core/summarizer.py`) use an optional `ANTHROPIC_API_KEY`. If unconfigured, the system deterministically falls back to structured template explanations without failure.
3. **Operator Authentication Boundary:** In compliance with the human-in-the-loop requirement, all decision mutation routes (`/api/recommendations/{id}/approve`, `/api/recommendations/{id}/reject`, `/api/policy`) require `X-Operator-Token`. Unauthenticated calls receive HTTP 401.
4. **Human Owner Presentation Ceremony:** Prior to live judging, the project owner should:
   - Perform the 5-minute live operator walkthrough script (`docs/final-demo-script.md`).
   - Retain the offline backup slides and presentation script (`docs/DEMO-BACKUP.md`).
   - Conduct the final git push and pull request merge at their discretion.

---

## 6. Lessons Learned & Process Changes

1. **Never Rely on Local Development Symlinks:**  
   *What happened:* A root `node_modules` symlink masked a cross-directory module resolution defect locally that failed in clean CI.  
   *Preventative change:* Added `scripts/verify_clean_clone.sh` to mechanical gates, which clones the repository to a clean temporary folder and validates build and discovery without local artifacts.
2. **Fail Fast on Test Discovery:**  
   *What happened:* Playwright silently reported "No tests found" when spec file evaluation failed.  
   *Preventative change:* Always execute `playwright test --list` as an explicit, fast CI step before invoking the full test suite.
3. **Environment Variable Configuration Validation:**  
   *What happened:* Out-of-sync local `.env` files can cause hard-to-diagnose authentication failures between services.  
   *Preventative change:* Created `scripts/check_compose_env.py` which validates that all Compose service credentials and ports match before containers boot.
4. **Transparent Loss Disclosure Builds Trust:**  
   *What happened:* In 60 randomized crisis scenarios, Heuristic won 15, tied 44, and lost 1.  
   *Preventative change:* Fully documented the single loss in `holdout_08`, analyzed the root cause (compound multi-corridor transit latency), and retained it in evaluation reports rather than cherry-picking passing seeds.
