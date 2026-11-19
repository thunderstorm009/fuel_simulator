# Repository instructions: Fuel Supply Intelligence & Resilience Platform

## Mission
Build ONE integrated operator-facing platform for the BUP CSE FEST 2026 hackathon on top of the organizer's Fuel Supply Simulator. It observes simulator state, detects and forecasts shortage risk, recommends feasible allocations with explanations, requires human approval, submits approved allocations, survives failures and records outcomes. Loop: Observe, Detect, Predict, Decide, Simulate, Approve, Act, Monitor, Recover.

## ONE REPOSITORY, BUILT IN PARTS
- Seven 4-hour sprints all happen in THIS repository. A sprint is a part of the same build, never a new project.
- Before any work: read `docs/PROGRESS.md`, then inspect the repo, branch and working tree. Extend what exists. Never scaffold a replacement app, never recreate earlier sprint work, never rewrite working code without a stated reason.
- After any work: update `docs/PROGRESS.md` and `docs/decisions.md`.

## Source of truth (highest first)
1. Official hackathon brief and simulator integration guide (in `reference/`), and the live simulator.
2. Existing repository code and tests.
3. `PROJECT_PLAN.md` and `docs/` (planned design, to be corrected when reality differs).
4. Never invent endpoint fields, constraints, data, test results or completed work. If sources conflict, stop and report. Do not silently reconcile.

## Hard rules
1. REST is truth. SSE is only a hint to refetch; there is no replay, so refetch after every reconnect.
2. The API never calls the simulator on read paths; it reads the database. The worker owns simulator I/O.
3. Every external call has a timeout, bounded retry with jitter, and strict schema validation. Never retry 409 or 422.
4. forecast, risk, policies and validator are pure functions with no I/O.
5. The only simulator write is POST /v1/allocations. The idempotency_key goes in the request body, is created once per recommendation, stored, and reused only for the identical body. Keys are permanent, even after cancel.
6. Never submit without an APPROVED recommendation, a fresh non-stale read, and re-validation of every constraint just before submit.
7. Do not count scheduled or in-transit supply as on-hand inventory. Do not confuse demand with served demand.
8. tick_minutes comes from /v1/instance; never hard-code it.
9. Parse all error shapes: detail.code (allocations), error.code (injected faults, HTTP 503), nested detail.code (stream fault), 422 detail list.
10. Treat X-Simulator-Stale: true as stale: flag it, lower confidence, block submissions, show data age in the UI.
11. Metric labels are low cardinality. No secrets in code; config through environment variables documented in `.env.example`.
12. Everything shown to an operator is labelled SIMULATED. No auto-submission of recommendations.

## Working protocol
- State the plan and affected files before broad changes. Work in small vertical slices: contract, service, API, UI, tests, docs.
- Work only on the current sprint's scope. Do not start the next sprint until the human says the gate passed.
- Add or update tests for every behavior change, including failure paths.
- Never claim success without running the command and reporting its real output. Do not fabricate screenshots, metrics, logs or benchmark numbers.
- Do not add dependencies or infrastructure without a reason recorded in `docs/decisions.md`.
- If blocked, report the blocker, impact, workaround and the decision needed.

## Definition of done (every feature)
Visible in the UI, emits a metric, writes a log line, has a test, handles its failure mode, and is documented.

## Commands (created in Sprint 1)
`make up` | `make down` | `make test` | `make lint` | `make smoke`

## Quality gates
Run lint, tests, build and `git diff --check` for changed code. Keep docs aligned with actual behavior.

## Sprint end
Use `prompts/SPRINT-GATE.md`: verify, write `docs/sprint-reports/sprint-NN.md`, update `docs/PROGRESS.md`, give the five-minute update, then stop for human review.

## Out of scope unless the core is finished and the human approves
Kubernetes, Kafka, microservice sprawl, reinforcement learning, multi-agent systems, vehicle routing, LLM-driven decisions. An LLM may only explain structured outputs and must never decide feasibility.

## Skills
Project skills live in `.agents/skills/<name>/SKILL.md`: project-planning, simulator-integration, forecast-risk, allocation-engine, resilience-testing, observability-metrics, test-driven-development, systematic-debugging, verification-before-completion, sprint-reporting, docs-auditor, code-review-strict. If your tool cannot load skills, read the file directly.
