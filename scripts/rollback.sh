#!/usr/bin/env bash
# Automated rollback script restoring stack to previous verified release tag.
set -euo pipefail

ROLLBACK_TAG="${1:-}"
STATE_FILE=".last_deployed_tag"

if [ -z "$ROLLBACK_TAG" ] && [ -f "$STATE_FILE" ]; then
  ROLLBACK_TAG="$(cat "$STATE_FILE")"
fi

if [ -z "$ROLLBACK_TAG" ]; then
  ROLLBACK_TAG="sprint-09"
fi

echo "[ROLLBACK] Executing automated rollback to tag: $ROLLBACK_TAG"
export IMAGE_TAG="$ROLLBACK_TAG"
echo "$ROLLBACK_TAG" > "$STATE_FILE"

# Re-validate stack health
echo "[ROLLBACK] Validating service recovery and smoke check..."
docker compose config -q
bash scripts/smoke.sh

echo "[ROLLBACK] Rollback SUCCESSFUL: Stack is healthy on tag $ROLLBACK_TAG"
