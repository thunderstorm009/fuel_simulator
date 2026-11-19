# Sprint 7 (hours 24-28): Freeze, rehearse, deliver

SAME REPOSITORY. Starting state: tag sprint-6. Feature freeze starts now. Only fixes that break the demo (P0) and documentation work are allowed.

Skills: verification-before-completion, docs-auditor, code-review-strict, systematic-debugging, sprint-reporting.

## Objective
A demo that cannot fail, complete documentation, and a release tag.

## Work packages

### WP7.1 Cold start and chaos
TASK: scripts/cold_start_check.sh (docker compose down -v, up, wait healthy, curl a smoke list, print elapsed time). scripts/chaos_random.py: for N minutes inject random events and faults at random intervals, then assert the API stays up and returns no 5xx outside active faults; log everything. Create docs/known-issues.md. Fix only P0 bugs found.

### WP7.2 Demo and Q&A
TASK: finalise docs/final-demo-script.md with exact commands, expected visuals, timing per step and a recovery line if a step fails. Create docs/qa.md with the 15 questions judges are most likely to ask (why a heuristic first, how the forecast works, what if the simulator lies, limits, what next) with honest answers based on this repository's real code and results.

### WP7.3 Final documentation and release (prompts/DOCS-PROMPTS.md D6)
TASK: run the documentation auditor in a different tool from the one that wrote the docs and fix every P0 and P1. Complete docs/assumptions-and-limitations.md, docs/ai-usage.md (tools, skills, review process), docs/SUBMISSION-MAP.md (the 11 required deliverables mapped to files and evidence), CHANGELOG.md. Capture the evidence list in docs/FINAL-DOCS-CHECKLIST.md.

### WP7.4 Stretch (ONLY if every box below is checked and the human approves)
Option A: core/summarize.py with a TemplateSummarizer (default) and an LLM summarizer (key from env, 3s timeout) that falls back to the template; label 'AI-generated summary of simulated data'. Option B: core/policies/optimizer.py with PuLP under the same constraints, wrapped by PolicyRunner with the heuristic as fallback; keep it only if scenario_runner shows it beats the heuristic.

## Acceptance checklist (real output required)
- [ ] docker compose down -v then up works on a clean clone, timed
- [ ] the demo script ran three times without touching the code; backup recording saved
- [ ] chaos round: no crash, no unexplained 5xx
- [ ] auditor reports no P0 or P1 documentation problems
- [ ] SUBMISSION-MAP points to real files for all 11 deliverables
- [ ] repository clean, tags sprint-7 and release created

## Finish
Run prompts/SPRINT-GATE.md with N=7, then tag release.
