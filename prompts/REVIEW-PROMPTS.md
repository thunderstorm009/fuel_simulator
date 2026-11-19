# Independent review prompts

Run these in a DIFFERENT tool from the one that wrote the code. The reviewer must not edit files unless asked. Use the code-review-strict skill. Paste COMMON-HEADER.md first.

## R1 Architecture and boundaries (after Sprint 2, 3, 5)
Read AGENTS.md, PROJECT_PLAN.md, docs/architecture.md and the actual code. Find boundary violations (API calling the simulator, impure functions in core/, I/O in forecast or policies), unnecessary complexity, duplicated logic, stale-data hazards, and docs that disagree with the code. Return findings ranked P0/P1/P2 with file and line and a minimal fix. Do not invent issues; do not edit files.

## R2 Simulator contract (after Sprint 2)
Compare core/sim_client.py, core/models.py and the tests with reference/ (the official guide), docs/sim-findings.md and live /docs responses. Check methods, paths, fields, stale header, SSE semantics, timeout and retry rules, the three error shapes, and idempotency. Return a contract matrix: verified, mismatch, unknown. Do not change code.

## R3 Allocation safety (after Sprint 4, mandatory)
Independently trace candidate generation, the validator, reservation accounting, pending and in-flight handling, approval, fresh-state re-validation, idempotency and execution. Try to find a path that can oversubscribe a depot or a route, submit twice, submit on stale data, submit without approval, or reuse a key with a different body. Return concrete failing test cases, severity and fixes. Do not modify code.

## R4 Resilience (after Sprint 5)
For each fault in the simulator (latency, unavailable, error_rate, stale_data, stream_disconnect), malformed data, predictor down and worker down, trace what the code does and what the operator sees. Find silent failures, retry storms, missing alerts and states that look healthy but are not. Return findings and test proposals.

## R5 Performance and load test (after Sprint 6)
Check the k6 script, the workload definition, thresholds, resource sampling and the reported numbers for honesty (single run, cherry-picked scenarios, missing error rate, testing the simulator instead of our API). Return findings.

## R6 Final release review (Sprint 7)
Inspect the diff, tests, CI, Docker, docs and demo evidence. Check for secrets, hard-coded fake live data, unsupported ML claims, missing tests, unverified success statements and incomplete sprint reports. Return release blockers, non-blocking issues and a go or no-go. Do not mark a test passed unless you ran it or inspected trustworthy output.
