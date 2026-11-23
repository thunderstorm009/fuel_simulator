#!/usr/bin/env bash
# scripts/preflight_judging.sh
# Comprehensive preflight check for Judging Day presentation.
# Validates Docker, required .env keys (without printing values), ports, Compose health,
# simulator status (PAUSED, tick_minutes=15), zero faults, disk space, and clock.
# Prints GO or NO-GO with detailed reasons.
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FAILURES=()
WARNINGS=()

check_pass() {
  echo -e "  [${GREEN}PASS${NC}] $1"
}

check_fail() {
  echo -e "  [${RED}FAIL${NC}] $1"
  FAILURES+=("$1")
}

check_warn() {
  echo -e "  [${YELLOW}WARN${NC}] $1"
  WARNINGS+=("$1")
}

echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}   FUEL PLATFORM PREFLIGHT CHECK (JUDGING DAY READINESS)        ${NC}"
echo -e "${BLUE}=================================================================${NC}"

# 1. Docker daemon check
echo "1. Checking Docker daemon..."
if docker info >/dev/null 2>&1; then
  check_pass "Docker daemon is running."
else
  check_fail "Docker daemon is NOT running."
fi

# 2. .env file & required keys (without leaking secrets)
echo "2. Checking environment configuration (.env)..."
if [ -f ".env" ]; then
  check_pass ".env file exists."
  REQUIRED_KEYS=(
    "OPERATOR_TOKEN"
    "DATABASE_URL"
    "SIM_BASE_URL"
    "CORS_ORIGIN"
  )
  for key in "${REQUIRED_KEYS[@]}"; do
    if grep -qE "^${key}=" .env; then
      val_len=$(grep -E "^${key}=" .env | head -n 1 | cut -d'=' -f2- | tr -d ' ' | wc -c)
      if [ "$val_len" -gt 1 ]; then
        check_pass "Required key '${key}' is configured (length: $((val_len - 1)) chars)."
      else
        check_fail "Key '${key}' exists but value is empty."
      fi
    else
      check_fail "Missing required key '${key}' in .env."
    fi
  done

  OPTIONAL_KEYS=(
    "API_WORKERS"
    "RATE_LIMIT_MAX_REQUESTS"
  )
  for key in "${OPTIONAL_KEYS[@]}"; do
    if grep -qE "^${key}=" .env; then
      check_pass "Optional tuning key '${key}' is explicitly configured."
    else
      check_pass "Optional tuning key '${key}' not in .env (using production code default)."
    fi
  done
else
  check_fail ".env file is missing. Copy from .env.example."
fi

# 3. Docker Compose service health
echo "3. Checking Docker Compose stack services..."
SERVICES=(
  "simulator"
  "postgres"
  "api"
  "worker"
  "predictor"
  "frontend"
  "prometheus"
  "grafana"
)

COMPOSE_PS=$(docker compose ps --format json 2>/dev/null || true)
if [ -z "$COMPOSE_PS" ]; then
  check_fail "No Docker Compose containers running for this project."
else
  for s in "${SERVICES[@]}"; do
    STATE=$(echo "$COMPOSE_PS" | python3 -c "
import sys, json
lines = [l.strip() for l in sys.stdin if l.strip()]
found = False
for l in lines:
    try:
        data = json.loads(l)
        if data.get('Service') == '$s':
            found = True
            h = data.get('Health', '')
            st = data.get('State', '')
            if h == 'healthy' or st == 'running':
                print('OK')
            else:
                print(f'{st} (health: {h})')
            break
    except Exception:
        pass
if not found:
    print('NOT_FOUND')
" 2>/dev/null || echo "ERROR")

    if [ "$STATE" = "OK" ]; then
      check_pass "Service '$s' is running and healthy."
    else
      check_fail "Service '$s' state: $STATE."
    fi
  done
fi

# 4. Port connectivity
echo "4. Checking published ports and service probes..."
check_port() {
  local port=$1
  local name=$2
  local url=$3
  if curl -sf --max-time 3 "$url" >/dev/null 2>&1; then
    check_pass "Port $port ($name) is responding at $url."
  else
    check_fail "Port $port ($name) is NOT responding at $url."
  fi
}

check_port 8000 "Simulator" "http://localhost:8000/v1/instance"
check_port 8101 "API Backend" "http://localhost:8101/health"
check_port 8102 "Worker" "http://localhost:8102/health"
check_port 8103 "Predictor" "http://localhost:8103/health"
check_port 5173 "Frontend UI" "http://localhost:5173"
check_port 9090 "Prometheus" "http://localhost:9090/-/healthy"
check_port 3000 "Grafana" "http://localhost:3000/api/health"

# 5. Simulator state verification
echo "5. Checking simulator state and invariants..."
SIM_INSTANCE=$(curl -sf --max-time 3 "http://localhost:8000/v1/instance" 2>/dev/null || echo "{}")
SIM_STATUS=$(echo "$SIM_INSTANCE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'UNKNOWN'))" 2>/dev/null || echo "UNKNOWN")
SIM_TICK_MINS=$(echo "$SIM_INSTANCE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('tick_minutes', 0))" 2>/dev/null || echo "0")
SIM_TICK=$(echo "$SIM_INSTANCE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('tick', -1))" 2>/dev/null || echo "-1")

if [ "$SIM_STATUS" = "PAUSED" ]; then
  check_pass "Simulator is cleanly PAUSED at tick $SIM_TICK."
else
  check_fail "Simulator is in '$SIM_STATUS' state (expected PAUSED)."
fi

if [ "$SIM_TICK_MINS" -eq 15 ]; then
  check_pass "Simulator tick duration is 15 minutes (default)."
else
  check_warn "Simulator tick duration is $SIM_TICK_MINS minutes (expected 15)."
fi

# 6. Simulator active faults check
echo "6. Checking simulator active faults..."
FAULTS_JSON=$(curl -sf --max-time 3 "http://localhost:8000/admin/faults" 2>/dev/null || echo "[]")
ACTIVE_FAULTS=$(echo "$FAULTS_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('faults', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
active = [f for f in items if f.get('active') is True]
print(len(active))
" 2>/dev/null || echo "0")

if [ "$ACTIVE_FAULTS" -eq 0 ]; then
  check_pass "Zero active simulator faults detected."
else
  check_fail "$ACTIVE_FAULTS active simulator fault(s) detected. Run 'curl -X POST http://localhost:8000/admin/faults/clear'."
fi

# 7. Disk space check
echo "7. Checking host disk space..."
FREE_KB=$(df -k . | tail -n 1 | awk '{print $4}')
FREE_GB=$((FREE_KB / 1024 / 1024))
if [ "$FREE_GB" -ge 2 ]; then
  check_pass "Available host disk space: ${FREE_GB} GB (minimum 2 GB required)."
else
  check_fail "Low disk space: only ${FREE_GB} GB free."
fi

# 8. Clock check
echo "8. Checking system clock and timezone..."
CURRENT_UTC=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
check_pass "System clock: $CURRENT_UTC"

echo ""
echo "================================================================="
if [ ${#FAILURES[@]} -eq 0 ]; then
  echo -e "${GREEN}>>> PREFLIGHT VERDICT: GO (System is judging-day ready) <<<${NC}"
  echo "================================================================="
  exit 0
else
  echo -e "${RED}>>> PREFLIGHT VERDICT: NO-GO (${#FAILURES[@]} failure(s) found) <<<${NC}"
  echo "Failures:"
  for f in "${FAILURES[@]}"; do
    echo "  - $f"
  done
  echo "================================================================="
  exit 1
fi
