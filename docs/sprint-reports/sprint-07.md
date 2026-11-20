# Sprint 07 Report: Freeze, rehearsal, and release readiness

Time window: 2026-11-20 | Owner: Codex | Branch: `main` | Status: **Partial; release gate open**

## 1. Objective

Prepare a reliable cold start, reversible chaos rehearsal, final demo, judge answers, limitations, and release evidence.

## 2. What now exists

- `scripts/cold_start_check.sh` times full startup and checks health, but requires `--confirm-volume-destroy` because it deletes named database and Grafana volumes.
- `scripts/chaos_random.py` injects and clears simulator API faults with a deterministic seed and records API health responses. It does not submit allocations.
- Final demo script, Q&A, assumptions/limitations, known issues, AI-use record, changelog, and submission map were updated.

## 3. Decisions and constraints

- Destructive volume deletion is guarded and was not executed.
- The allocation approval gate remains intact. Demo steps explicitly require approval before a live write.
- No tag, release, or backup recording was created.

## 4. Key files

`scripts/cold_start_check.sh`, `scripts/chaos_random.py`, `docs/final-demo-script.md`, `docs/qa.md`, `docs/known-issues.md`, `docs/assumptions-and-limitations.md`, `docs/ai-usage.md`, `CHANGELOG.md`, and `docs/SUBMISSION-MAP.md`.

## 5. Verification

| Check | Actual result | Status |
|---|---|---|
| Local suite/lint/build | 123 Python, 3 frontend; make lint passes | PASS |
| Script syntax | `bash -n` passed for shell scripts; `compileall` passed for Python scripts | PASS |
| Cold start after volume deletion | Not run; Docker unavailable and data destruction requires explicit local confirmation | NOT-RUN |
| Random chaos round | Not run; Docker/API unavailable | NOT-RUN |
| Three no-code demo rehearsals / backup recording | Not run | NOT-RUN |
| Independent docs audit | Not performed | NOT-RUN |
| Release tags and clean worktree | Not created; working changes intentionally remain | NOT-RUN |

## 6. Evidence and limitations

No new runtime evidence or recording exists. `docs/known-issues.md` contains the full blocker list. Existing historical evidence is not a substitute for current rehearsal.

## 7. Acceptance checklist

- [ ] Cold start from disposable clean data — NOT-RUN.
- [ ] Demo script run three times and backup recording saved — NOT-RUN.
- [ ] Chaos round with no unexplained API 5xx — NOT-RUN.
- [ ] Independent audit has no P0/P1 — NOT-RUN.
- [x] Submission map points to existing files; evidence/status limitations are recorded.
- [ ] Repository clean; sprint-7/release tags created — NOT-RUN.

## 8. Five-minute update

1. Problem: provide a repeatable demo and honest submission/readiness record.
2. Change: guarded cold-start, reversible fault chaos, demo sequence, Q&A and final docs.
3. Demo: rehearsal is pending; do not claim an unrehearsed run.
4. Evidence: local tests, lint, build and script syntax pass; no runtime rehearsal.
5. Gap: restore Docker, authorize destructive cold start on disposable data, rehearse three times, run audit and decide release tagging.

## Gate decision

**Not passed.** Runtime rehearsal, chaos, documentation audit, clean-tree review, and release actions remain open.
