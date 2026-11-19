---
name: systematic-debugging
description: Use when a test, container or behavior fails and the cause is not obvious. Find the root cause before changing code.
---
# Systematic debugging
1. Reproduce with the smallest command and capture the exact error.
2. Read logs, metrics and the simulator /admin/audit before guessing.
3. List hypotheses; test one at a time; change one thing at a time.
4. Fix the root cause minimally. Add a regression test.
5. Confirm with the original reproduction and the full test suite.
6. After three failed hypotheses, stop and report findings instead of thrashing.
7. Record non-obvious root causes in docs/decisions.md or the sprint report.
