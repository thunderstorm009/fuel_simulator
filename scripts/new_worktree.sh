#!/usr/bin/env bash
# usage: scripts/new_worktree.sh <branch-name>
# Creates a sibling folder on its own branch so a second agent can work without file conflicts.
set -euo pipefail
B=${1:?branch name, for example s2-wp1-simclient}
D="../$(basename "$PWD")-$B"
git worktree add "$D" -b "$B"
echo "Worktree ready: $D (open your agent there). Merge into the sprint branch when tests pass."
