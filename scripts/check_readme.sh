#!/usr/bin/env bash
set -euo pipefail

docker compose config -q
make test
make lint
make up
for url in http://localhost:8101/health http://localhost:8101/api/health http://localhost:8102/health http://localhost:8103/health; do
  curl --fail --silent --show-error "$url" >/dev/null
done
port="${FRONTEND_HOST_PORT:-5173}"
curl --fail --silent --show-error "http://localhost:$port/" >/dev/null
echo "README quickstart checks passed. Stack remains running; no volume was removed."
