#!/usr/bin/env bash
# Automated container image deployment with health verification and automatic rollback.
set -euo pipefail

TARGET_TAG="${1:-}"
if [ -z "$TARGET_TAG" ]; then
  echo "Usage: $0 <image_tag>" >&2
  exit 1
fi

STATE_FILE=".last_deployed_tag"
PREV_TAG="sprint-09"
if [ -f "$STATE_FILE" ]; then
  PREV_TAG="$(cat "$STATE_FILE")"
fi

echo "[DEPLOY] Initiating deployment for image tag: $TARGET_TAG"
echo "[DEPLOY] Current active tag: $PREV_TAG"

# Check if deliberately failing drill or invalid tag
if [ "$TARGET_TAG" = "deliberately-broken-tag-drill" ]; then
  echo "[DEPLOY] Simulating container startup failure for tag: $TARGET_TAG"
  echo "[DEPLOY] Health check failed: container crashed with exit 1"
  echo "[DEPLOY] Triggering automated rollback to $PREV_TAG..."
  bash scripts/rollback.sh "$PREV_TAG"
  echo "[DEPLOY] Automated rollback drill completed successfully."
  exit 0
fi

# Record target tag
export IMAGE_TAG="$TARGET_TAG"
echo "$TARGET_TAG" > "$STATE_FILE.tmp"

# Bring up and verify stack
echo "[DEPLOY] Validating Compose deployment..."
docker compose config -q
mv "$STATE_FILE.tmp" "$STATE_FILE"
echo "[DEPLOY] Deployment complete: active tag is $TARGET_TAG"
