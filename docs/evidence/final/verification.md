# Final Independent Clean-Clone Verification Report

- **Date:** 2026-11-26
- **Auditor Model:** Gemini 4 Hydrogen (Medium) — independent from Gemini 3.8 Flash (Day 6–7)
- **Repository:** `thunderstorm009/fuel_simulator`
- **Verified Commit (`main` / `v1.0.0`):** `1bdbeb9806cab8248943a9aa62d10dde4090ccbb`
- **Clone Path:** `/tmp/final-audit-clone` (fresh `git clone` of `https://github.com/thunderstorm009/fuel_simulator.git`, configured with `cp .env.example .env`)

---

## 1. Hosted GitHub Actions CI Verification (REST API)

Verified via unauthenticated GitHub REST API (`https://api.github.com/repos/thunderstorm009/fuel_simulator/actions/runs`):

| Target | Commit | Run ID | Job | Status | Conclusion | URL |
|---|---|---|---|---|---|---|
| `main` | `1bdbeb9` | `45350506449` | `python` | completed | **success** | https://github.com/thunderstorm009/fuel_simulator/actions/runs/45350506449/job/138295449140 |
| `main` | `1bdbeb9` | `45350506449` | `frontend` | completed | **success** | https://github.com/thunderstorm009/fuel_simulator/actions/runs/45350506449/job/138295449442 |
| `main` | `1bdbeb9` | `45350506449` | `compose` | completed | **success** | https://github.com/thunderstorm009/fuel_simulator/actions/runs/45350506449/job/138295449437 |
| `main` | `1bdbeb9` | `45350506449` | `security` | completed | **success** | https://github.com/thunderstorm009/fuel_simulator/actions/runs/45350506449/job/138295449367 |
| PR #19 (`day-6-7`) | `0ce890b` | `45349978104` | `python` | completed | **success** | https://github.com/thunderstorm009/fuel_simulator/actions/runs/45349978104/job/138293701051 |
| PR #19 (`day-6-7`) | `0ce890b` | `45349978104` | `frontend` | completed | **success** | https://github.com/thunderstorm009/fuel_simulator/actions/runs/45349978104/job/138293701158 |
| PR #19 (`day-6-7`) | `0ce890b` | `45349978104` | `compose` | completed | **success** | https://github.com/thunderstorm009/fuel_simulator/actions/runs/45349978104/job/138293700750 |
| PR #19 (`day-6-7`) | `0ce890b` | `45349978104` | `security` | completed | **success** | https://github.com/thunderstorm009/fuel_simulator/actions/runs/45349978104/job/138293701222 |

---

## 2. Clean-Clone Reproduction Results

| Check | Command / Tool | Result | Real Observed Output |
|---|---|---|---|
| **README Quickstart (Stack)** | `cp .env.example .env && make up && make smoke && bash scripts/preflight_judging.sh` | **PASS** | All 8 services healthy (`simulator`, `postgres`, `api`, `worker`, `predictor`, `frontend`, `prometheus`, `grafana`); simulator `PAUSED` at tick 0; `PREFLIGHT VERDICT: GO`. |
| **README Quickstart (Lint/Test)** | `make lint && make test` (Note: requires `npm ci --prefix web` first on clean clone; without it `tsc: command not found`) | **PASS** (after `npm ci --prefix web`) | `ruff check .` clean; `ruff format --check .` (111 files); `tsc -b` 0 errors; `vite build` 2.20s (main chunk `278.23 kB`); `pytest` **239 passed** in 5.17s; `vitest` **11 passed** (2 files) in 1.37s. |
| **Compose Config** | `docker compose config -q` | **PASS** | Exit 0 (`compose config OK`). |
| **Browser E2E Suite** | `NODE_PATH=web/node_modules OPERATOR_TOKEN=change-me ... make test-e2e` | **PASS** | **12 passed** in 40.9s (`tests/e2e/platform.spec.ts`). |
| **Clean-Clone Script** | `bash scripts/verify_clean_clone.sh` | **PASS** | Confirmed absent: `.env`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.agents`, `.claude`, `.local`, `prompts`; Compose env check passed; Playwright discovery 12 tests; `MECHANICAL GATE: PASS (Sprint 6)`. |
| **Sprint Gate Script** | `bash scripts/sprint_gate.sh 15` | **FAIL (gitignored)** | `scripts/sprint_gate.sh: No such file or directory` (gitignored by `.gitignore:19`). Public script `bash scripts/sprint_gate_public.sh 15` **PASSED** (`MECHANICAL GATE: PASS (Sprint 15)`). |
| **Git Diff Whitespace** | `git diff --check` | **PASS** | Exit 0, 0 whitespace/conflict issues. |
| **Scenario Determinism** | `python3 scripts/scenario_runner.py --scenario baseline --policy heuristic --ticks 5` | **PASS** | 2 runs (`r1`, `r2`), both `svc=100.0% stockouts=0`; simulator reset, paused, faults cleared. |
| **k6 Load Test (100 VUs)** | `k6 run loadtest/k6.js` (stages 10→50→100 VUs, 65s) | **THRESHOLD CROSSED (exit 99)** | 24,368 reqs (`374.57 req/s`), 0% errors; `http_req_duration` p50 `99.06 ms`, **p95 `378.84 ms`** (crossed `<300 ms` threshold); `whatif_duration_ms` p50 `155.34 ms`, p95 `514.49 ms`. |
| **k6 Load Test (200 VUs)** | `k6 run --vus 200 --duration 15s loadtest/k6.js` | **THRESHOLD CROSSED (exit 99)** | 5,964 reqs (`338.41 req/s`), 0% errors; `http_req_duration` p50 `304.67 ms`, **p95 `1719.42 ms`**; `whatif_duration_ms` p50 `791.65 ms`, p95 `1804.00 ms`. |
| **Unloaded What-If** | 25 sequential `POST /api/whatif` | **PASS** | `min=12.30ms`, `p50=14.67ms`, `p95=18.87ms`, `max=52.39ms`. |
| **Python Dependency Audit** | `pip-audit -r requirements.txt -r requirements-dev.txt` | **PASS** | `No known vulnerabilities found`. |
| **NPM Dependency Audit** | `npm audit --prefix web --audit-level=high` | **PASS** | `found 0 vulnerabilities`. |
| **Trivy Filesystem Scan** | `docker run --rm ... aquasec/trivy:latest fs /repo --severity HIGH,CRITICAL` | **PASS** | `requirements.txt`: 0 vulns; `web/package-lock.json`: 0 vulns; 0 secrets. |
| **Gitleaks History Scan** | `docker run --rm ... zricethezav/gitleaks:latest git /repo --verbose` | **PASS** | `68 commits scanned` (~4.08 MB in 3.44s), `no leaks found`. |
| **Forbidden-File Check** | `git ls-files \| grep -E '^(\.env$\|prompts/\|AGENTS\.md$\|CLAUDE\.md$\|GEMINI\.md$\|\.agents/\|\.claude/)'` | **PASS** | 0 forbidden files tracked. |
| **File-Size Check (>5 MB)** | `find . -path ./.git -prune -o -type f -size +5000k -print` | **PASS** | 0 files over 5 MB. |
| **Terminology Keyword Grep** | `git grep -n -i "refinery\|pipeline capacity\|corridor throughput\|chittagong\|conservation law\|reverse proxy\|vehicle quota\|price spike\|redis\|cryptograph" -- . ':!prompts'` | **FINDINGS (P1/P2)** | Active public docs/presentations still contain `Chittagong` (`README.md`, `PITCH-10MIN.md`, `SLIDES.md`, `slides.html`, `MANIFEST.md`) and `Cryptographic Proof` (`MANIFEST.md`, `capture_day7_evidence.js`). Also `README.md:22` lists 5 regions including Sylhet/Khulna/Rajshahi instead of the simulator's actual 2 regions (`region-dhaka`, `region-chattogram`). |
