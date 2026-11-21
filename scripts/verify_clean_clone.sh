#!/usr/bin/env bash
# Verify clean-clone readiness in a temporary directory without ignored files.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMP_DIR="/tmp/fuel_sim_clean_verify_$(date +%s)"
OUTPUT_FILE="$ROOT_DIR/docs/evidence/clean-clone-check.txt"

mkdir -p "$(dirname "$OUTPUT_FILE")"

cleanup() {
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

echo "=== 1. Cloning repository into temporary folder ===" | tee "$OUTPUT_FILE"
git clone "$ROOT_DIR" "$TEMP_DIR" 2>&1 | tee -a "$OUTPUT_FILE"
cd "$TEMP_DIR"

echo "=== 2. Verifying ignored development files are absent ===" | tee -a "$OUTPUT_FILE"
for path in .env AGENTS.md CLAUDE.md GEMINI.md .agents .claude .local prompts; do
  if [ -e "$path" ]; then
    echo "FAIL: $path should not exist in clean clone" | tee -a "$OUTPUT_FILE"
    exit 1
  else
    echo "CONFIRMED ABSENT: $path" | tee -a "$OUTPUT_FILE"
  fi
done

echo "=== 3. Validating Compose model with public defaults (.env.example) ===" | tee -a "$OUTPUT_FILE"
docker compose --env-file .env.example config -q 2>&1 | tee -a "$OUTPUT_FILE"
python3 scripts/check_compose_env.py --env-file .env.example 2>&1 | tee -a "$OUTPUT_FILE"

echo "=== 4. Installing frontend dependencies in clean clone ===" | tee -a "$OUTPUT_FILE"
npm --prefix web ci 2>&1 | tee -a "$OUTPUT_FILE"

echo "=== 5. Running public mechanical gate ===" | tee -a "$OUTPUT_FILE"
VENV_BIN="${VIRTUAL_ENV:-$ROOT_DIR/.venv}/bin"
PATH="$VENV_BIN:/tmp/fuel-sprint1-venv/bin:$PATH" bash scripts/sprint_gate_public.sh 6 2>&1 | tee -a "$OUTPUT_FILE"

echo "=== Clean clone verification PASSED ===" | tee -a "$OUTPUT_FILE"
