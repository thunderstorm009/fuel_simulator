# AI-assisted engineering record

## Overview and governance

This repository was developed with AI-assisted software engineering. Development was governed by strict repository rules (`AGENTS.md`), sprint milestone definitions, automated quality gates, and mechanical verification scripts.

## Tools used

- **Antigravity CLI (Agy):** Primary autonomous orchestration agent, running Google DeepMind models. Used for architecture navigation, implementation, test writing, load benchmark execution, chaos rehearsal, documentation synchronization, and mechanical verification.
- **Codex & Claude:** Used during earlier sprints for initial contract exploration, foundational service scaffolding, and test suite creation.

## Boundaries and separation of responsibilities

1. **Pure deterministic core logic:**
   - All forecasting algorithms (`backend/shared/core/forecast.py`), inventory risk modeling (`backend/shared/core/risk.py`), allocation heuristic policies (`backend/shared/core/policies/`), and physical constraint validators (`backend/shared/core/validator.py`) are implemented in pure, mathematical Python code with zero network I/O or external side effects.
   - AI models never decide feasibility, invent constraints, or execute unconstrained optimization.
2. **Strict human approval boundary:**
   - The platform strictly enforces mandatory human operator approval for all simulator dispatches (`POST /v1/allocations`).
   - AI tools never approve recommendations or bypass the operator authorization barrier. Live verification in Sprint 4 was conducted exclusively under explicit project-owner authorization.
3. **Evidence-based verification:**
   - Every sprint report and evidence artifact is generated from actual command executions (`make test`, `make lint`, `docker compose`, `k6`, `curl`).
   - No benchmark numbers, latency metrics, or test outputs were synthesized or claimed without empirical logs.

## Quality control and review protocol

- **Architectural review:** Structured review prompts (R3, R4, R5) were executed at sprint boundaries as rigorous self-reviews using the code-review-strict skill to audit code against `AGENTS.md` rules, boundary integrity, stale-data hazards, and exception ergonomics.
- **Documentation auditing:** Public documentation was audited to guarantee zero references or links to private development files (`.env`, local prompts, private agent skills).
- **Clean clone validation:** Independent verification was performed in clean, temporary directories to ensure full reproducibility from public repository assets alone.
