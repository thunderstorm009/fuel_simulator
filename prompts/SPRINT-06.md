# Sprint 6 (hours 20-24): Proof, load test, CI and main documentation

SAME REPOSITORY. Starting state: tag sprint-5. Extend. This sprint adds evidence and documents; avoid new features.

Skills: test-driven-development, verification-before-completion, docs-auditor, sprint-reporting.

## Objective
Evidence that the system works, helps and performs, and that a stranger can run it.

## Work packages

### WP6.1 Scenario runner
TASK: scripts/scenario_runner.py CLI: --scenario baseline|spike|route|combined --policy none|naive|heuristic --ticks N. Scenario definitions in scenarios/*.yaml with events and start ticks. Flow: /admin/reset, pause, schedule events, then loop: step one tick, run the policy cycle using core and sim_client, auto-approve (simulation mode only), finally read /v1/metrics. naive = refill to 70% when below 30%. Output markdown and CSV to docs/results/ with service_level, unmet liters, served liters, allocation liters, failures, station-tick stockouts. Run each twice to prove determinism.

### WP6.2 Load test
TASK: loadtest/k6.js against OUR API (GET /api/risks, GET /api/state and the recommendation generate or what-if endpoint). Ramp 10, 50, 100 virtual users, 60s each; thresholds p95 under 300ms and error rate under 1%; BASE_URL from env; JSON summary export. scripts/loadtest_report.py turns the summary into docs/loadtest.md (average, p50, p95, p99, throughput, error rate, workload definition). scripts/collect_stats.sh logs docker stats CPU and memory to CSV during the run. Three runs: normal, simulator latency fault, predictor stopped. Find and report the knee where p95 passes about 500ms.

### WP6.3 CI hardening
TASK: Extend CI: lint, unit tests with coverage, frontend build and tests, compose smoke job (up, wait healthy, curl /api/health, run scenario_runner for 20 ticks with heuristic and none and assert the heuristic service_level is at least as high), docker layer caching, pinned action versions, upload logs as artifacts on failure, markdown lint and link check for docs.

### WP6.4 Main documentation (run the prompts in prompts/DOCS-PROMPTS.md: D1 to D5)
TASK: README, architecture.md, intelligence.md, simulator-integration notes, observability.md, deployment (operations.md), testing-and-ci.md, security-and-guardrails.md, operator guide and runbook, resilience.md and loadtest.md finalised. Every number cites a file in docs/results or docs/evidence. Add scripts/check_readme.sh that runs the quickstart commands on a clean checkout.
DONT: describe features that are not implemented.

## Acceptance checklist (real output required)
- [ ] a table shows the heuristic policy beats do-nothing and naive on service_level, with determinism proof
- [ ] docs/loadtest.md has workload and numbers from three runs
- [ ] a teammate runs the README quickstart on a clean clone without help
- [ ] CI green including the smoke job
- [ ] the docs-auditor skill finds no P0 documentation problems

## Finish
Run prompts/SPRINT-GATE.md with N=6. Do not start Sprint 7.
