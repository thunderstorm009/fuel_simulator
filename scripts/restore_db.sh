#!/usr/bin/env bash
set -euo pipefail

# Database restore script targeting THIS project's postgres container only.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file.sql>" >&2
    exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: backup file ${BACKUP_FILE} does not exist" >&2
    exit 1
fi

echo "Restoring database into fuel_simulator-postgres-1 from ${BACKUP_FILE}..."
docker compose -f "${REPO_ROOT}/docker-compose.yml" exec -T postgres psql -U fuel -d fuel < "${BACKUP_FILE}"

echo "Database restore completed successfully."
