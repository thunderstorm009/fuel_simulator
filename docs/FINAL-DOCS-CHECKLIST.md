# Final documentation checklist (remaining Sprint 6-7 work)

Personal documentation prompts are retained locally under `.local/prompts/` and are not part of this public repository.

Documents (all in this same repo): README.md, docs/architecture.md, docs/simulator-contract.md and sim-findings.md, docs/intelligence.md, docs/resilience.md, docs/observability.md, docs/operations.md (deployment), docs/testing-and-ci.md, docs/loadtest.md, docs/operator-guide.md, docs/runbook.md, docs/security-and-guardrails.md, docs/decisions.md, docs/assumptions-and-limitations.md, docs/ai-usage.md, docs/final-demo-script.md, docs/qa.md, docs/known-issues.md, docs/sprint-reports/sprint-01..07.md, docs/results/, docs/evidence/, docs/SUBMISSION-MAP.md, CHANGELOG.md.

Evidence to capture in docs/evidence: dashboard overview, risk matrix, recommendation drawer, decision history, health page (HEALTHY and DEGRADED), Grafana normal and during a fault, compose all healthy with cold-start time, scenario comparison tables, load-test summaries and CPU/memory CSV, one capture per fault scene, CI green with coverage, a decision traced by correlation id.

Rules: every command run or marked UNTESTED; every number cites a file; no unimplemented features described; same terms everywhere; SIMULATED notice in README, operator guide and UI; markdown lint and link check in CI.

- [ ] README quickstart verified by someone else on a clean clone
- [ ] every document above exists with no placeholders
- [ ] auditor (D6) reports no P0 or P1
- [ ] SUBMISSION-MAP points to real files
- [ ] evidence folder complete
- [ ] CHANGELOG has all sprint tags
- [ ] final tags sprint-7 and release created
