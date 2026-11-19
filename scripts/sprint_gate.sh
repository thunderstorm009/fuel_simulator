#!/usr/bin/env bash
# usage: scripts/sprint_gate.sh <N> [--tag]
# Runs the mechanical gate checks. A human still decides whether the sprint passed.
set -uo pipefail
N=${1:?sprint number 1-7}
printf -v NN '%02d' "$N"
fail=0
run() { local d=$1; shift; echo; echo "== $d"; if "$@"; then echo "PASS: $d"; else echo "FAIL: $d"; fail=1; fi; return 0; }
note() { echo; echo "== $1"; echo "$2"; }

[ -f Makefile ] && run 'make lint' make lint || note 'make lint' 'SKIP: no Makefile yet (Sprint 1 creates it)'
[ -f Makefile ] && run 'make test' make test || note 'make test' 'SKIP: no Makefile yet'
[ -f docker-compose.yml ] && run 'docker compose config' docker compose config -q || note 'docker compose config' 'SKIP: no docker-compose.yml yet'
run 'git diff --check' git diff --check
if [ -f "docs/sprint-reports/sprint-$NN.md" ]; then echo; echo "PASS: report docs/sprint-reports/sprint-$NN.md exists"; else echo; echo "FAIL: missing docs/sprint-reports/sprint-$NN.md"; fail=1; fi
if grep -q "Sprint $N" docs/PROGRESS.md 2>/dev/null; then echo "PASS: PROGRESS.md mentions Sprint $N"; else echo "FAIL: PROGRESS.md does not mention Sprint $N"; fail=1; fi
if git ls-files --error-unmatch .env >/dev/null 2>&1; then echo 'FAIL: .env is tracked by git'; fail=1; else echo 'PASS: .env not tracked'; fi
if git grep -qE '(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC )?PRIVATE KEY)' -- . ':!docs' ':!prompts' ':!.agents' 2>/dev/null; then echo 'FAIL: possible secret found in tracked files'; fail=1; else echo 'PASS: no obvious secrets'; fi

echo
if [ "$fail" -eq 0 ]; then
  echo 'MECHANICAL GATE: PASS. Now review the acceptance checklist in prompts/SPRINT-'"$NN"'.md and the evidence yourself.'
  if [ "${2:-}" = '--tag' ]; then git tag -a "sprint-$N" -m "Sprint $N" && echo "Tagged sprint-$N"; fi
else
  echo 'MECHANICAL GATE: FAIL. Fix the items above. Do not tag.'; exit 1
fi
