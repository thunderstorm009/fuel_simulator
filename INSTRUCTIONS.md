# INSTRUCTIONS: how to run this kit, step by step

Read this once before hour 0. It covers setup, the sprint loop, each tool, parallel work, recovery and the final delivery.

## 1. The one-repository rule (read twice)

All seven sprints happen in ONE repository. You never create a new repo or a new project per sprint. Sprint N+1 extends the code from sprint N. Between sprints only three things change: the code grows, `docs/PROGRESS.md` is updated, and a git tag marks the end of the part.

Why this matters for agents: an agent starts every session with no memory. `docs/PROGRESS.md`, `docs/decisions.md`, the sprint reports and git history are its memory. If you skip updating them, the next sprint's agent will rebuild things that already exist.

## 2. One-time setup (about 30 minutes)

1. Install the tools you will use. Check each tool's docs for the current installer.
   - Claude Code: `npm install -g @anthropic-ai/claude-code`, then `claude`.
   - Codex CLI: `curl -fsSL https://chatgpt.com/codex/install.sh | sh` (or `brew install --cask codex`, or `npm install -g @openai/codex`), then `codex login`.
   - Antigravity CLI: `curl -fsSL https://antigravity.google/cli/install.sh | bash`, then `agy auth login`.
   Log in to each tool with its own account. Do not route one vendor's login into another vendor's tool. Check quotas before the event.
2. Make the repository and copy the kit in:
   ```
   mkdir fuel-ops && cd fuel-ops && git init
   cp -r /path/to/fuel-ops-hackathon-kit/. .
   ```
   The dot after the path matters: it copies hidden files (`.agents/`, `.gitignore`, `.env.example`).
3. Put the official PDFs in `reference/` (hackathon brief, simulator integration guide).
4. `bash scripts/bootstrap_agents.sh` creates CLAUDE.md and GEMINI.md from AGENTS.md and links `.claude/skills` to `.agents/skills`. Re-run it whenever you edit AGENTS.md.
5. `cp .env.example .env` (never commit `.env`).
6. `git add -A && git commit -m 'Add hackathon kit' && git tag sprint-0`
7. Start the simulator once to be sure Docker works (`docker compose up -d` with the organizers' compose file, then `curl -s localhost:8000/v1/health`). Sprint 1 will add it to your own compose file.

## 3. Check that each tool sees the rules and skills

Open a NEW session in the repo root for each tool and ask: `List the skills you can see and summarize the 12 hard rules in AGENTS.md.`
- Claude Code: expects to read CLAUDE.md and see skills through `.claude/skills`.
- Codex: expects to read AGENTS.md; skills in `.agents/skills`; you can name a skill in the prompt (for example $simulator-integration) or let the tool match by description.
- Antigravity: run `agy inspect` and `agy skills list`. If skills are missing, use the fallback below.

Fallback for any tool that does not load skills: tell the agent `Read .agents/skills/<name>/SKILL.md and follow it`, or paste that file into the prompt.

## 4. The sprint loop (same for every sprint)

Replace N with the sprint number. Total 4 hours.

1. (5 min) `git switch main && git pull` if you use a remote. Create a branch for the sprint: `git switch -c sprint-N`.
2. (5 min) Open a fresh agent session at the repo root. Paste `prompts/COMMON-HEADER.md` followed by `prompts/SPRINT-0N.md`. Mode A: the whole sprint file to one agent. Mode B: the header plus ONE work package (WP) per agent, each on its own worktree (section 6).
3. (10 min) The agent reads PROGRESS.md, inspects the repo and states its plan. Read it. Approve or correct. Do not let it start the next sprint.
4. (2.5 h) The agent builds. Watch the diffs. Stop it if it creates a new project, rewrites earlier sprint code, or adds big dependencies.
5. Run the tests yourself: `make lint && make test`. Do not trust a summary without output.
6. (20 min) Cross-review: open a DIFFERENT tool and paste the matching prompt from `prompts/REVIEW-PROMPTS.md`. Fix P0 and P1 findings.
7. (20 min) Gate: paste `prompts/SPRINT-GATE.md`. The agent runs verification, writes `docs/sprint-reports/sprint-0N.md`, updates `docs/PROGRESS.md` and gives the five-minute update. Then run `bash scripts/sprint_gate.sh N` yourself.
8. (10 min) You review the report and evidence. If the gate passes: `git add -A && git commit -m 'Sprint N: <title>'`, `git switch main && git merge sprint-N`, then `git tag -a sprint-N -m 'Sprint N'` (or `bash scripts/sprint_gate.sh N --tag`).
9. If the gate fails: fix, do not tag, and carry the unfinished items to the top of the next sprint in PROGRESS.md.
10. Take a short break before the next sprint.

## 5. Per-tool tips

Claude Code: start `claude` in the repo root. Skills are used when the task matches the description, or you can name one. For headless review: `claude -p "<prompt>"`.
Codex CLI: start `codex`. Name a skill with `$skill-name`. Headless: `codex exec "<prompt>"`. Tools and approvals differ by version; keep approvals tight on main.
Antigravity: open the folder or run `agy`. After adding skills, start a new session. Headless: `agy -p "<prompt>"`. Use `agy usage` to see quota. Do not depend on multi-agent features; run your own parallel sessions.
Headless runs are best for reviews, reports and audits. Use interactive sessions for code-writing work.

`bash scripts/run_prompt.sh <prompt-file> <claude|codex|agy>` assembles COMMON-HEADER plus the prompt file and runs it headless.

## 6. Parallel work without conflicts

Inside one sprint, work packages touch different folders, so they can run in parallel:
```
bash scripts/new_worktree.sh s2-wp1-simclient
bash scripts/new_worktree.sh s2-wp4-frontend
```
Each creates a sibling folder on its own branch. Run one agent per folder. Merge branches one at a time into the sprint branch, run `make test` after each merge, and resolve conflicts yourself. Never let two agents edit the same file at once.

## 7. Who writes and who reviews

The tool that writes a module must not be the tool that reviews it. Rotate: Claude Code writes, Codex or Antigravity reviews, and so on. Keep one human owner per sprint who can explain every changed file to the judges. If a tool hits its quota, continue with another: the repo, AGENTS.md, skills, PROGRESS.md and prompts are identical for all tools.

## 8. If you fall behind

1. Look at the cut order in PROJECT_PLAN.md section 6. Cut P2 first.
2. Move unfinished items to PROGRESS.md under Carried over, with a reason.
3. Never silently borrow time from the next sprint. Never cut re-validation, human approval, stale-data handling, the executor tests, or the fault demo.
4. If an agent is looping, use `prompts/RESCUE-PROMPTS.md` (debug, scope cut, resume).

## 9. Resuming after a lost session, quota or crash

Open a fresh session and paste the RESUME prompt from `prompts/RESCUE-PROMPTS.md`. It makes the agent read PROGRESS.md, git log and the working tree, and report where things stand before touching code.

## 10. The five-minute update (for every sprint end)

1. Which operator problem did this sprint solve? 2. What changed in code and architecture? 3. Show it running. 4. Show the evidence: test output, screenshots in docs/evidence. 5. What failed or is risky, and what does the next sprint depend on? Never say done because files exist. Show behavior.

## 11. Final delivery (Sprint 7)

Follow `docs/FINAL-DOCS-CHECKLIST.md` and `docs/SUBMISSION-MAP.md`. Run `prompts/DOCS-PROMPTS.md` (D1 to D6) in Sprint 6 and 7. Tag `sprint-7`, then `release`. Rehearse the demo in `docs/final-demo-script.md` three times, with a backup recording.

## 12. Common mistakes

- Creating a new repo or folder per sprint (do not).
- Letting an agent re-scaffold the project in Sprint 2 or later.
- Not updating docs/PROGRESS.md (the next agent will repeat work).
- Committing `.env` or API keys.
- Accepting 'all tests pass' without seeing the output.
- Running two agents on the same files.
- Downloading random third-party skills. Read any skill before using it; the 12 in this kit are enough.
