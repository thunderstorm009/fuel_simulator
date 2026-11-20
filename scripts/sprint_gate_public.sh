#!/usr/bin/env bash
# Public mechanical gate. Private sprint prompts and repository instructions are
# intentionally absent from clean clones, so report those checks as skipped.
set -euo pipefail
N=${1:?usage: scripts/sprint_gate_public.sh <1-7>}
if ! [[ "$N" =~ ^[1-7]$ ]]; then
  echo "FAIL: sprint number must be 1-7" >&2
  exit 2
fi
printf -v NN '%02d' "$N"

for local_path in AGENTS.md ".local/prompts/SPRINT-$NN.md" .agents/skills; do
  if [ -e "$local_path" ]; then
    echo "PRESENT: $local_path (local-only development workspace)"
  else
    echo "SKIP: local-only file absent ($local_path)"
  fi
done

make lint
make test
docker compose config -q
git diff --check
test -f "docs/sprint-reports/sprint-$NN.md"
grep -q "Sprint $N" docs/PROGRESS.md
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  echo 'FAIL: .env is tracked by Git' >&2
  exit 1
fi
if git grep -qE '(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC )?PRIVATE KEY)' -- . ':!docs' 2>/dev/null; then
  echo 'FAIL: possible secret in tracked source' >&2
  exit 1
fi
echo "MECHANICAL GATE: PASS (Sprint $N)"
