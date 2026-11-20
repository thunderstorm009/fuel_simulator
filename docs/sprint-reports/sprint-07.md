# Sprint 07 Report: Freeze, rehearsal, and release readiness

Time window: 2026-11-20 | Owner: Agy (Autonomous overnight run) | Branch: `overnight-sprints-4-7` | Status: **PASS**

## 1. Objective

Complete the final platform freeze, verify cold-start recovery with volume destruction, execute clean-clone verification in an isolated environment, conduct reversible chaos testing, finalize the 5-minute operator demonstration sequence and judge Q&A, audit documentation against code and privacy rules, and prepare release artifacts.

## 2. What now exists

- `scripts/cold_start_check.sh`: Automated cold-start script that wipes database and cache volumes, restarts the 8-container Compose stack, waits for health checks, and verifies operational readiness. Measured cold-start recovery time: **34 seconds**.
- `scripts/verify_clean_clone.sh`: Disposable verification script that clones the current branch into an isolated `/tmp/` directory, strips all local-only private files (`.env`, `prompts/`, `.agents/`), and proves that the public repository builds, lints, and passes all 141 Python unit/integration tests and 6 frontend tests out-of-the-box.
- `scripts/chaos_random.py`: Deterministic randomized chaos testing script (`--seed 20261120`) that injects reversible faults (`unavailable`, `error_rate`, `latency`, `stale_data`, `stream_disconnect`) over 1.0 minute and clears them via HTTP POST. Verified zero unexplained 5xx API errors and automatic system recovery.
- Transparent predictor dual-port routing (ports 8103 and 8100) ensuring seamless interoperability between legacy environment configurations and standard service ports.
- `docs/final-demo-script.md`: Turn-by-turn 5-minute live operator walkthrough with exact commands, expected visual indicators, narrative speaking points, and failure recovery lines.
- `docs/qa.md`: Exhaustive answers to 15 judge evaluation questions covering pure algorithmic design, simulator boundaries, idempotency, stale data handling, and operational resilience.
- Complete documentation alignment: `docs/assumptions-and-limitations.md`, `docs/ai-usage.md`, `docs/SUBMISSION-MAP.md`, `CHANGELOG.md`, and `docs/known-issues.md`.

## 3. Decisions and constraints

- **ADR-035:** Documented Sprint 7 freeze, cold-start verification timing, clean-clone verification, and predictor dual-port routing.
- **Strict human approval boundary maintained:** All live simulator dispatches require explicit human operator approval via authenticated API. AI tools never approve recommendations or bypass the operator gate.
- **No secrets in tracked source:** All evidence files and documentation were scanned and confirmed free of credentials, API tokens, and private development prompts.

## 4. Key files

- `scripts/cold_start_check.sh`
- `scripts/verify_clean_clone.sh`
- `scripts/chaos_random.py`
- `docs/evidence/sprint-07-cold-start.txt`
- `docs/evidence/clean-clone-check.txt`
- `docs/evidence/sprint-07-chaos.json`
- `docs/final-demo-script.md`
- `docs/qa.md`
- `docs/assumptions-and-limitations.md`
- `docs/ai-usage.md`
- `docs/SUBMISSION-MAP.md`
- `CHANGELOG.md`
- `docs/known-issues.md`

## 5. Verification

| Check | Command / Verification | Actual result | Status |
|---|---|---|---|
| Python unit & integration tests | `pytest` | 141 passed in 1.52s | PASS |
| Frontend unit tests | `npm --prefix web run test` | 6 passed in 1.02s | PASS |
| Code quality & formatting | `ruff check . && ruff format --check .` | Clean; 65 files formatted | PASS |
| TypeScript typecheck & build | `npm --prefix web run typecheck && npm --prefix web run build` | Zero errors; Vite production build built | PASS |
| Compose configuration | `docker compose config -q` | Valid; zero warnings | PASS |
| Cold-start recovery | `scripts/cold_start_check.sh --confirm-volume-destroy` | Full stack recovered from scratch in 34 seconds | PASS |
| Clean-clone isolated build | `scripts/verify_clean_clone.sh` | Clean clone passes lint, tests, and build without ignored files | PASS |
| Random chaos rehearsal | `scripts/chaos_random.py --minutes 1.0 --seed 20261120` | Zero unexplained 5xx errors; all faults cleared | PASS |
| Git whitespace & diff | `git diff --check` | Clean | PASS |
| Secret scan | Staged source secret scan | Zero secrets detected; no `.env` tracked | PASS |

## 6. Evidence and limitations

- Cold-start timing and health check evidence: `docs/evidence/sprint-07-cold-start.txt`.
- Clean-clone test results: `docs/evidence/clean-clone-check.txt`.
- Chaos execution log: `docs/evidence/sprint-07-chaos.json`.
- Live simulator state remains PAUSED with all faults cleared and all 8 Docker Compose containers healthy.
- Three live demo rehearsals and backup screen capture video recording are assigned to the human project owner prior to stage presentation.

## 7. Acceptance checklist

- [x] Cold start from disposable clean data executed and measured (34s elapsed).
- [x] Demo script completed with turn-by-turn actions and recovery paths (`docs/final-demo-script.md`).
- [x] Chaos round executed with zero unexplained API 5xx errors (`docs/evidence/sprint-07-chaos.json`).
- [x] Documentation audit (D6) completed with no broken links or private prompt leaks.
- [x] Submission map points to verified files and empirical evidence (`docs/SUBMISSION-MAP.md`).
- [x] Mechanical gate passes cleanly (`scripts/sprint_gate_public.sh 7`).
- [x] Tag `sprint-7` created.

## 8. Five-minute update

1. **Problem:** Finalize the platform for judging and release: verify cold-start resilience from destroyed volumes, prove clean-clone reproducibility, test system stability under random chaos, and align all presentation materials.
2. **Change:** Automated cold-start recovery (34s), isolated clean-clone validation, reversible chaos rehearsal with zero 5xx errors, dual-port predictor routing, complete judge Q&A, and full submission mapping.
3. **Demo:** Show all 8 containers healthy, verify cold-start timing, review operator walkthrough in `docs/final-demo-script.md`, and demonstrate system health recovery after fault clearance.
4. **Evidence:** `docs/evidence/sprint-07-cold-start.txt`, `docs/evidence/clean-clone-check.txt`, `docs/evidence/sprint-07-chaos.json`, 141 Python tests + 6 frontend tests passing.
5. **Remaining:** Project owner executes live demo rehearsal x3, records screen-capture backup video, reviews git log, and pushes tags to origin.

## Gate decision

**PASS.** All Sprint 7 objectives, verification checks, and documentation requirements are fully satisfied. Ready for tagging as `sprint-7`.
