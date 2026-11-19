#!/usr/bin/env bash
# usage: scripts/run_prompt.sh <prompt-file> <claude|codex|agy>
# Headless run of COMMON-HEADER + prompt. Best for reviews, reports and audits.
# Check each tool's docs for permission flags; do not enable broad auto-approval on main.
set -euo pipefail
F=${1:?prompt file}
T=${2:?tool: claude, codex or agy}
PROMPT="$(cat prompts/COMMON-HEADER.md "$F")"
case "$T" in
  claude) claude -p "$PROMPT" ;;
  codex) codex exec "$PROMPT" ;;
  agy) agy -p "$PROMPT" ;;
  *) echo 'unknown tool: use claude, codex or agy'; exit 1 ;;
esac
