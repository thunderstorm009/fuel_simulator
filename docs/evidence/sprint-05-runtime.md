# Sprint 5 local verification evidence — 2026-11-20

This evidence is local and does not represent live Compose acceptance.

- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make test`: **123 passed**; frontend Vitest: **3 passed**.
- `PATH=/tmp/fuel-sprint1-venv/bin:$PATH make lint`: Ruff passed, 59 files formatted; TypeScript passed; Vite production build transformed 500 modules and completed successfully (main JS 251.09 kB; trajectory chunk 426.04 kB).
- `python3 -m compileall -q backend intel scripts tests`: passed.
- `bash -n scripts/fault_demo.sh scripts/collect_stats.sh scripts/cold_start_check.sh scripts/check_readme.sh`: passed.
- `docker compose config -q`: exit 0.
- `git diff --check`: exit 0.
- The focused half-open breaker test initially failed because a second request entered during recovery. After adding the single-probe guard, the full 123-test suite passed.
- `docker compose ps` could not connect to `/Users/abrar/.docker/run/docker.sock`. Requests to local API port 8101 and simulator port 8000 were refused. No live fault, service-stop, Grafana, browser, or simulator allocation test was run.
- `k6` was not installed. No performance measurements were taken.

Historical Sprints 1–3 runtime evidence is kept in its existing files; it was not repeated here.
