# Sprint 4 mechanical gate evidence

Date: 2026-11-20 | Branch: `overnight-sprints-4-7`

Commands run after the final Sprint 4 code and report changes:

```text
PATH=/tmp/fuel-sprint1-venv/bin:$PATH FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 bash scripts/sprint_gate_public.sh 4
MECHANICAL GATE: PASS (Sprint 4)

PATH=/tmp/fuel-sprint1-venv/bin:$PATH FRONTEND_HOST_PORT=5174 CORS_ORIGIN=http://localhost:5174 bash .local/scripts/sprint_gate.sh 4
PASS: make lint
PASS: make test
PASS: docker compose config
PASS: git diff --check
PASS: report docs/sprint-reports/sprint-04.md exists
PASS: PROGRESS.md mentions Sprint 4
PASS: .env not tracked
PASS: no obvious secrets
MECHANICAL GATE: PASS
```

Both runs executed Ruff, formatting, TypeScript, Vite production build, 130 Python tests, and 6 frontend tests. The public gate checks local-only instructions without requiring them in clean clones; the legacy ignored gate path is not force-added. Live allocation acceptance and the separate R3 review are recorded in [sprint-04-overnight.md](sprint-04-overnight.md) and [sprint-04-r3-review.md](sprint-04-r3-review.md).
