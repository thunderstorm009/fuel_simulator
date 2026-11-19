---
name: project-planning
description: Use at the start of a sprint or when scope or priorities are unclear. Produces a short, repository-aware plan that extends existing work and respects the 28-hour time box.
---
# Project planning
1. Read docs/PROGRESS.md, docs/decisions.md, PROJECT_PLAN.md and the current sprint prompt.
2. Inspect git log, branch and working tree. List what already exists. Extend it; never plan a rewrite or a new project.
3. Break the sprint into work packages with order, files, tests and a time box. Name the riskiest item first.
4. Mark each item P0, P1 or P2. If time is short, cut P2 first. Never cut re-validation, human approval, stale-data handling, executor tests or the fault demo.
5. Present at most 10 lines of plan and the files to touch, then wait for approval.
6. Record non-obvious choices in docs/decisions.md.
