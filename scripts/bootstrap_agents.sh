#!/usr/bin/env bash
# Run from the repo root. Re-run after editing AGENTS.md.
set -euo pipefail
[ -f AGENTS.md ] || { echo 'AGENTS.md not found. Run from the repo root.'; exit 1; }
mkdir -p .agents/skills .claude docs/evidence docs/results docs/sim-samples docs/sprint-reports reference
cp -f AGENTS.md CLAUDE.md
cp -f AGENTS.md GEMINI.md
if [ ! -e .claude/skills ]; then ln -s ../.agents/skills .claude/skills || cp -r .agents/skills .claude/skills; fi
echo 'Skills in repo:'; ls .agents/skills
for t in claude codex agy; do
  if command -v "$t" >/dev/null 2>&1; then echo "$t: found"; else echo "$t: not installed"; fi
done
echo 'Done. Next: open a NEW session in each tool and ask it to list the skills and summarize AGENTS.md.'
