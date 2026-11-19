---
name: test-driven-development
description: Use when implementing or changing behavior. Write a failing test first, then the minimum code, then refactor.
---
# Test-driven development
1. Write a test for the behavior, including a failure path, and watch it fail for the right reason.
2. Write the minimum code to pass. Keep functions pure where AGENTS.md requires it.
3. Refactor with tests green. Run make lint and make test.
4. Use fixtures from docs/sim-samples and mock HTTP with respx; avoid real sleeping (use a fake clock).
5. Cover boundaries: empty data, stale data, malformed payload, timeout, constraint limits.
6. Report the actual test output, never a summary alone.
