#!/usr/bin/env bash
set -euo pipefail

# Database backup script targeting THIS project's postgres container only.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${REPO_ROOT}/backups"
mkdir -p "${BACKUP_DIR}"

OUTPUT_FILE="${1:-${BACKUP_DIR}/fuel_backup_$(date +%Y%m%d_%H%M%S).sql}"

echo "Backing up database from fuel_simulator-postgres-1 to ${OUTPUT_FILE}..."
docker compose -f "${REPO_ROOT}/docker-compose.yml" exec -T postgres pg_dump -U fuel -d fuel --clean --if-exists > "${OUTPUT_FILE}"

SIZE=$(wc -c < "${OUTPUT_FILE}" | tr -d ' ')
echo "Backup completed successfully (${SIZE} bytes written to ${OUTPUT_FILE})."
