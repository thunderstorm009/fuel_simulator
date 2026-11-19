# Sprint gate prompt: run at the end of EVERY sprint (set N to the sprint number)

Paste COMMON-HEADER.md first. Use the skills verification-before-completion and sprint-reporting. Do NOT write new features in this step.

1. Read prompts/SPRINT-0N.md, its acceptance checklist, docs/PROGRESS.md, the git diff since the last tag, and test output.
2. Run for real: make lint, make test, docker compose config -q, git diff --check, and every command or scenario in the acceptance checklist (including the fault injections for that sprint). Record each as PASS, FAIL, BLOCKED or NOT-RUN with the actual output. Never infer success.
3. Write docs/sprint-reports/sprint-0N.md using docs/templates/sprint-report.md. Describe behavior, not just files. Put screenshots, logs or output in docs/evidence/ and reference their paths. Do not invent evidence; mark missing items MISSING.
4. Update docs/PROGRESS.md: sprint status, what now exists (files and features), tag to create, items carried over, known gaps and risks, and the exact first task for the next sprint.
5. Update docs/decisions.md for any decision made, and correct any design doc in docs/ that no longer matches the code.
6. Give the five-minute oral update: problem solved, what changed, live demo steps, evidence, remaining gap and next dependency.
7. Output a table of the acceptance checklist with PASS/FAIL, a list of failures, and your recommendation: gate passed or not.
8. Stop. Do not commit, tag or start the next sprint. The human decides.
