# Rescue prompts

## RESUME (new session, lost context, quota switch to another tool)
Paste COMMON-HEADER.md, then: Do not change any files yet. Read docs/PROGRESS.md, docs/decisions.md, the latest docs/sprint-reports file, git log -20 and git status. Tell me: the current sprint, what exists and works (verify by running make test), what is half-done, and the first task for this session. Wait for my OK.

## DEBUG (use the systematic-debugging skill)
Paste COMMON-HEADER.md, then: Problem: <describe, with the exact error output>. Do not guess. Reproduce it, form hypotheses, test one at a time, find the root cause, fix it minimally, add a regression test, and show the passing output. If it is not solved after three hypotheses, stop and report what you learned.

## SCOPE CUT (when behind schedule)
Paste COMMON-HEADER.md, then: We are <X> hours behind in sprint <N>. Using PROJECT_PLAN.md section 6, propose the smallest scope that still meets the sprint's P0 acceptance items. List what is cut, what moves to PROGRESS.md Carried over, and the risk of each cut. Never cut re-validation, human approval, stale-data handling, executor tests or the fault demo. Do not write code until I approve.

## UNSTICK (agent started a new project or rewrote earlier work)
Stop. Run git status and git diff --stat. Do not continue. Tell me which earlier files you changed or recreated, then revert those changes with git checkout or git restore for files that were working in the last tag, keep only the intended changes, and re-read AGENTS.md ('ONE REPOSITORY BUILT IN PARTS'). Then continue the current work package only.
