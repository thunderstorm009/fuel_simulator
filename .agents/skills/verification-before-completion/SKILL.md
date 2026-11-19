---
name: verification-before-completion
description: Use before declaring a task, sprint or demo complete. Evidence-based verification with real command output.
---
# Verification before completion
1. Translate the acceptance checklist into observable checks.
2. Inspect the real diff; confirm it stays within the sprint scope and extends (not replaces) earlier work.
3. Run lint, tests, build, docker compose config -q, git diff --check; run the sprint's smoke and fault checks.
4. Scan for secrets and accidental files (.env, keys).
5. Check docs match behavior.
6. Mark each item PASS, FAIL, BLOCKED or NOT-RUN with the actual output or an evidence path. Never infer success from code presence or an earlier claim.
7. State residual risk for anything not run.
