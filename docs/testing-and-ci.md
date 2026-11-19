# Testing and CI (planned)
- Unit: pure core functions (hand-calculated cases, property tests), validator rule per test, error parser.
- Client: respx mocks for success, each error shape, timeout, malformed JSON, stale header, breaker transitions with a fake clock.
- Integration: ingest and executor with a fake SimClient; resilience tests for each fault shape.
- Scenario regression: scripts/scenario_runner.py, deterministic runs (twice, identical).
- Load: k6 against our API, three runs (normal, simulator latency fault, predictor stopped), CPU and memory sampled.
- CI stages: lint (ruff), tests with coverage, frontend build, docker build, compose smoke (up, healthy, /api/health, 20-tick scenario), docs lint and link check.
- Commands: make lint, make test, make smoke.
