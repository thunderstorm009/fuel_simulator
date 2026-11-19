# Fuel Supply Intelligence & Resilience Platform: 28-hour Hackathon Kit

BUP CSE FEST 2026 Final Hackathon. This kit is the project harness: rules, skills, prompts, docs templates and scripts for building ONE application in seven 4-hour sprints with Claude Code, Codex CLI and Google Antigravity (agy). It is not the application itself.

## The one rule that matters

**ONE repository for the whole 28 hours.** A sprint is not a new repo and not a new project. Sprint 2 extends the code from Sprint 1, Sprint 3 extends Sprint 2, and so on. Each sprint is just the next part of the same build, marked by a git tag (sprint-1 ... sprint-7). Every sprint prompt tells the agent to inspect what already exists and extend it. Progress between sessions lives in `docs/PROGRESS.md`, not in anyone's memory.

```
one repo: fuel-ops/
  main  ---- sprint-1 ---- sprint-2 ---- sprint-3 ---- ... ---- sprint-7 (release)
            (foundation)  (ingest+UI)   (forecast)            (final)
```

## Start here (about 30 minutes, once)

1. Create one empty git repo, for example `fuel-ops`, and open a terminal in it.
2. Unzip this kit and copy EVERYTHING (including hidden files such as `.agents/` and `.gitignore`) into the repo root:
   `cp -r fuel-ops-hackathon-kit/. fuel-ops/`
3. Put the two official PDFs in `reference/` (hackathon brief, simulator integration guide).
4. Run `bash scripts/bootstrap_agents.sh`. It creates CLAUDE.md and GEMINI.md from AGENTS.md and links `.claude/skills` to `.agents/skills`.
5. Open the repo in your tools and check that they see the rules and skills (see INSTRUCTIONS.md section 3).
6. `git add -A && git commit -m 'kit' && git tag sprint-0`
7. Run `prompts/00-MASTER-BOOTSTRAP.md` once (planning only), approve the plan, then start Sprint 1.

Full step-by-step instructions are in `INSTRUCTIONS.md`. Read it once before hour 0.

## Where every file goes (all paths are relative to the repo root)

| File or folder | Purpose | Read by | When |
|---|---|---|---|
| `AGENTS.md` | Durable rules for every agent | Codex, Antigravity, (copies for Claude Code and Gemini) | Every session |
| `CLAUDE.md`, `GEMINI.md` | Copies of AGENTS.md made by the bootstrap script | Claude Code, Antigravity | Every session |
| `PROJECT_PLAN.md` | Scope, architecture, 28-hour schedule, gates | You and agents | Start, each gate |
| `INSTRUCTIONS.md` | How to run the kit, tool by tool | You | Before hour 0 |
| `.agents/skills/<name>/SKILL.md` | 12 reusable skills | Agents | Loaded on demand |
| `.claude/skills` | Link to `.agents/skills` (created by script) | Claude Code | Automatic |
| `prompts/` | Bootstrap, 7 sprint prompts, header, gate, review, docs and rescue prompts | You paste them into the agent | Each sprint |
| `docs/PROGRESS.md` | Running state: what exists, what is next | Agents and you | Start and end of every session |
| `docs/decisions.md` | Decision log (ADR style) | Agents and you | When a decision is made |
| `docs/architecture.md` and other design docs | Planned design; update to match reality | Agents | While building |
| `docs/templates/` | Sprint report, ADR, demo evidence, runbook templates | Agents | Sprint ends |
| `docs/sprint-reports/` | One report per sprint (sprint-01.md ...) | Judges and you | End of each sprint |
| `docs/evidence/` | Screenshots, logs, command output | Docs | Whenever a feature works |
| `docs/results/` | Scenario comparison and load-test results | Docs | Sprint 6 |
| `docs/sim-samples/` | Captured simulator JSON (test fixtures) | Tests | Sprint 1 |
| `reference/` | Official brief and simulator guide PDFs | Agents | Always |
| `scripts/` | bootstrap, sprint gate, run prompt, worktree helper | You | Throughout |
| `.env.example` | Config template (copy to `.env`, never commit) | You | Sprint 1 |

The application folders (`core/`, `worker/`, `predictor/`, `api/`, `frontend/`, `infra/`, `tests/`, `loadtest/`) do not exist yet. The agents create them across the sprints, inside this same repo.

## Agent compatibility

| Tool | Reads rules from | Skills location | Start |
|---|---|---|---|
| Claude Code | CLAUDE.md | `.claude/skills` (linked to `.agents/skills`) | `claude` in the repo root |
| Codex CLI | AGENTS.md | `.agents/skills` | `codex` in the repo root |
| Antigravity (agy) | AGENTS.md and GEMINI.md | `.agents/skills` | `agy` in the repo root, or open the folder in the app |

Tool conventions change. If a tool does not find the skills, check its current docs, restart the session, or paste the skill text into the prompt. References: Antigravity skills https://antigravity.google/docs/skills ; Codex skills https://developers.openai.com/codex/skills ; the open Agent Skills standard https://agentskills.io .

## Safety and scope

Simulator only. No real fuel systems, purchases or dispatches. All values are SIMULATED and labelled so. Human approval is required before any allocation is sent to the simulator. The official brief and the live simulator override this kit if they disagree.

## What is in the kit

See `KIT-MANIFEST.json` for the full file list.
