# Documentation Directory Index

This directory contains the complete technical, operational, architectural, and verification documentation for the **Fuel Supply Intelligence & Resilience Platform** built for the BUP CSE FEST 2026 hackathon.

---

## 1. Domain & Architecture

- **[PROBLEM-UNDERSTANDING.md](PROBLEM-UNDERSTANDING.md)** — Comprehensive domain model of Bangladesh fuel logistics: depots, transit routes, stations, tick temporal dynamics, mathematical demand vs supply balancing, physical bottleneck identification, and operational metrics.
- **[architecture.md](architecture.md)** — System architecture, container topology, service responsibilities, and Mermaid sequence diagrams (ingestion, triage, what-if, approval-to-submit, SSE push invalidation, and fault circuit breakers).
- **[data-model.md](data-model.md)** — Relational database schema, entity contracts, and state transition lifecycles.
- **[simulator-contract.md](simulator-contract.md)** — Formal specification of the external BUP Fuel Supply Simulator API, headers (`X-Simulator-Stale`), error shapes, and idempotency guarantees.
- **[event-handling.md](event-handling.md)** — Server-Sent Events (SSE) integration guide, push invalidation architecture, and automatic polling fallback mechanics.

---

## 2. Operational & Judging Guides

- **[JUDGING-DAY.md](JUDGING-DAY.md)** — Official judging day runbook: 10-minute presentation choreography, demo director commands, surprise injection rehearsal guide, and contingency matrix.
- **[DEMO-BACKUP.md](DEMO-BACKUP.md)** — Offline static presentation fallback pack: ordered screenshots and full word-for-word voiceover script.
- **[operator-guide.md](operator-guide.md)** — Step-by-step user guide for fuel dispatch operators: reviewing risks, using the What-If simulator, and executing token-authenticated approvals/rejections.
- **[runbook.md](runbook.md)** — Operational runbook: failure diagnosis, circuit breaker recovery, Alertmanager silencing, and service troubleshooting.
- **[operations.md](operations.md)** — Production operations: container management, backup and restore drills, and metric scrape targets.
- **[qa.md](qa.md)** — Comprehensive, evidence-backed answers to judges' technical, architectural, and mathematical questions.

---

## 3. Intelligence, Policies & Verification

- **[intelligence.md](intelligence.md)** — Predictive engine details: diurnal baseline models, Monte Carlo probabilistic simulation (P10/P90), event-aware calibration, and anomaly detection.
- **[decisions.md](decisions.md)** — Architectural Decision Records (ADRs) log indexing all 49 key architectural choices (ADR-001 through ADR-049).
- **[BRIEF-COMPLIANCE.md](BRIEF-COMPLIANCE.md)** — Exhaustive line-by-line verification matrix against all 109 requirements in the official hackathon specification.
- **[security-and-guardrails.md](security-and-guardrails.md)** — Security posture: token authentication, secret scanning (Gitleaks), container vulnerability audits (Trivy), dependency checks (pip-audit), and LLM guardrails.
- **[known-issues.md](known-issues.md)** — Transparent log of known operational boundaries, residual risks, and non-blocking edge cases.
- **[assumptions-and-limitations.md](assumptions-and-limitations.md)** — Explicit system assumptions, physical boundaries, and intentional architectural trade-offs.

---

## 4. Empirical Benchmark Reports (`docs/results/`)

- **[results/scenario-sweep.md](results/scenario-sweep.md)** — 60-scenario randomized crisis sweep (240 live simulation runs, 46,080 ticks) with 95% bootstrap confidence intervals and honest loss disclosure.
- **[results/failure-boundary.md](results/failure-boundary.md)** — Stress-testing failure boundaries across demand spikes, supply shocks, and multi-route severed links.
- **[results/backtest-summary.md](results/backtest-summary.md)** — 2,000-tick historical backtesting report: MAPE across fuel types and prediction horizons.
- **[results/event-calibration.md](results/event-calibration.md)** — Empirical calibration evaluation comparing Legacy v1.1.0 vs Event-Aware v1.2.0 models, Brier reliability curves, and spike adaptation latency.
- **[results/soak-test-summary.md](results/soak-test-summary.md)** — 90-minute live soak test report under continuous chaos: memory drift bounds, DB growth, and error boundedness.
- **[results/tick-compatibility.md](results/tick-compatibility.md)** — Dynamic tick-length scaling verification across 8-minute and 15-minute simulation temporalities.
- **[results/loadtest-normal.md](results/loadtest-normal.md)** — k6 load benchmark before and after API performance optimization (tripled throughput to 625.8 req/s).
- **[results/loadtest-latency.md](results/loadtest-latency.md)** — Endpoint latency breakdowns (p50, p90, p95, p99) under concurrent load.
- **[results/loadtest-nopredictor.md](results/loadtest-nopredictor.md)** — Load benchmark during predictor service outage verifying local fallback resilience.

---

## 5. Progress & Sprint Archives

- **[PROGRESS.md](PROGRESS.md)** — Cumulative sprint-by-sprint progress log, active work package tracker, and 5-minute status updates.
- **[DAY-4-UPDATE.md](DAY-4-UPDATE.md)** — Day 4 final delivery summary, corrections ledger vs Day 3, today's re-run verification table, and claims ledger.
- **[DAY-5-UPDATE.md](DAY-5-UPDATE.md)** — Day 5 post-mortem report on errors found, CI failure deep dive, root causes, permanent fixes, and regression guards.
- **[sprint-reports/](sprint-reports/)** — Formal sprint reports for Sprints 01 through 13.
- **[reviews/](reviews/)** — Independent architectural reviews (R1, R3, R4, R5, R6, R7, and docs audit).
- **[evidence/](evidence/)** — Raw empirical logs, timing JSONs, and high-resolution interface screenshots.
