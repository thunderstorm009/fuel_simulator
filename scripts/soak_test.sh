#!/usr/bin/env bash
set -euo pipefail

# Configurable soak test runner (WP12.3)
DURATION_MINUTES="${1:-90.0}"
SAMPLE_INTERVAL="${2:-30.0}"
SPEED="${3:-2}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Starting soak test for ${DURATION_MINUTES} minutes (sample interval: ${SAMPLE_INTERVAL}s, speed: ${SPEED})..."
python3 "${REPO_ROOT}/scripts/run_soak_test.py" --minutes "${DURATION_MINUTES}" --sample-interval "${SAMPLE_INTERVAL}" --speed "${SPEED}" --chaos
