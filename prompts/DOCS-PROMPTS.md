# Documentation prompts (run in Sprint 6 and Sprint 7; same repo, same docs folder)

Paste COMMON-HEADER.md first. Wrapper for ALL documentation prompts:
Read the code, docs/results and docs/evidence, not memory. Every command you write must be run or marked UNTESTED. Every number must cite a file path. Do not describe features that are not implemented. Keep terms consistent with AGENTS.md. End with a list of things you could not verify. Update existing docs in place; do not create duplicates.

## D1 README and architecture
Write README.md (replace the kit README with the project README: what it is, SIMULATED notice, screenshot, features, Mermaid architecture diagram, 5-command quickstart, config table from .env.example, how to use, fault demo, tests and CI, results summary, project layout, limitations, credits) and update docs/architecture.md with a Mermaid component diagram and three Mermaid sequence diagrams (snapshot to recommendation; approve to simulator submit; simulator fault handling). Keep the kit README as docs/KIT-README.md.

## D2 Intelligence, assumptions, limitations
Update docs/intelligence.md and write docs/assumptions-and-limitations.md. Read core/world.py, core/forecast.py, core/risk.py, core/policies/, core/explain.py and docs/results/. Document formulas and constants exactly as coded. Put the policy comparison table from docs/results into the evaluation section with seeds and scenarios. List limitations honestly, including where the heuristic loses.

## D3 Observability, operations, security
Update docs/observability.md, docs/operations.md and docs/security-and-guardrails.md. Build the metrics catalog by scanning the code for metric definitions. Build the env var table from .env.example. Describe CI stages from .github/workflows/ci.yml and the rollback procedure using git tags and image tags.

## D4 Operator guide and runbook
Write docs/operator-guide.md (screen tour, reading risk and recommendations, approve and reject, what DEGRADED and OFFLINE mean, glossary, what the system never does) and docs/runbook.md with one entry per incident type using docs/templates/runbook-entry.md: simulator unavailable, breaker open, stale data, SSE disconnected, predictor down, worker down, database down, malformed data rejected, high simulator rejection rate, recommendation backlog, API latency high, snapshot table growing.

## D5 Testing, resilience, load test wrap-up
Update docs/testing-and-ci.md and finalise docs/resilience.md and docs/loadtest.md from real test output, scripts/fault_demo.sh and docs/results. Replace every EVIDENCE placeholder with a file reference or mark it MISSING.

## D6 Documentation auditor (different tool, read-only)
Use the docs-auditor skill. Compare every claim in README.md and docs/*.md with the code, docker-compose.yml, .env.example, the CI workflow and docs/results. List false or unimplemented statements, commands that would fail, numbers without a source, missing items from docs/SUBMISSION-MAP.md, inconsistent terms and broken links. Rank P0/P1/P2. Output the list only; do not edit files.

## D7 Submission map and AI usage
Fill docs/SUBMISSION-MAP.md (each of the 11 required deliverables mapped to a repo file and an evidence file) and write docs/ai-usage.md: which tools and skills were used for which sprint, how every diff was reviewed by a human and by a second tool, what the humans wrote by hand (contracts, scenarios, verification), and any third-party skills (none by default).
