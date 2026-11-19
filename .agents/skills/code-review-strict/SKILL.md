---
name: code-review-strict
description: Use to review a git diff against AGENTS.md rules before merging. Read-only unless asked.
---
# Strict code review
- Run git diff main...HEAD (or against the last tag). Cite the AGENTS.md rule number for each violation.
- Look for bugs, missing timeouts or validation, constraint violations, impure core functions, API-calls-simulator, flaky tests, secrets, security issues, unmeasured claims and rewrites of earlier sprint work.
- Rank P0, P1, P2. Suggest minimal fixes; do not rewrite code.
