#!/usr/bin/env bash
set -euo pipefail

# Simple dev orchestrator for local Fides (non-Docker)
# - Ensures Conda env, exports .env.local, starts Redis (passworded), API, and workers
# - Provides commands: up, down, api, w1, w2, w3, status, logs, reset-db, health

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
RUN_DIR="/tmp/fides-dev"
POSTGRES_LOG="$RUN_DIR/postgres.log"
REDIS_PID_FILE="$RUN_DIR/redis.pid"
REDIS_LOG="$RUN_DIR/redis.log"
API_PID_FILE="$RUN_DIR/api.pid"
W1_PID_FILE="$RUN_DIR/w1.pid"
W2_PID_FILE="$RUN_DIR/w2.pid"
W3_PID_FILE="$RUN_DIR/w3.pid"
UI_PID_FILE="$RUN_DIR/ui.pid"
ENV_FILE="$PROJECT_ROOT/.env.local"

require_cmds() {
  local missing=()
  for cmd in "$@"; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      missing+=("$cmd")
    fi
  done
  if [ ${#missing[@]} -gt 0 ]; then
    echo "Missing required commands: ${missing[*]}" >&2
    echo "Run dockerless/install.sh to install prerequisites." >&2
    exit 1
  fi
}

ensure_conda() {
  # shellcheck disable=SC1091
  source "$HOME/miniconda3/etc/profile.d/conda.sh" 2>/dev/null || true
  if ! command -v conda >/dev/null 2>&1; then
    echo "Conda not found at ~/miniconda3; please install Miniconda and re-run." >&2
    exit 1
  fi
  conda activate fides >/dev/null 2>&1 || {
    echo "Conda env 'fides' not found. Create via: conda create -y -n fides python=3.10" >&2
    exit 1
  }
}

ensure_node() {
  export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
  if [ -s "$NVM_DIR/nvm.sh" ]; then
    # shellcheck disable=SC1090
    source "$NVM_DIR/nvm.sh"
  else
    echo "nvm not found at $NVM_DIR; install Node 20 or set NVM_DIR." >&2
    exit 1
  fi
  if ! nvm use 20 >/dev/null 2>&1; then
    if ! nvm use default >/dev/null 2>&1; then
      echo "Unable to switch to Node 20 (nvm use 20); install Node 20 via nvm." >&2
      exit 1
    fi
  fi
}

export_env() {
  if [ -f "$ENV_FILE" ]; then
    set -a; # export
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
  else
    echo ".env.local not found at $ENV_FILE" >&2
    exit 1
  fi
}

start_postgres() {
  mkdir -p "$RUN_DIR"
  if ( cd "$PROJECT_ROOT" && dockerless/start_postgres.sh > "$POSTGRES_LOG" 2>&1 ); then
    echo "Postgres ready (log: $POSTGRES_LOG)"
  else
    echo "Postgres failed to start; see $POSTGRES_LOG" >&2
    exit 1
  fi
}

start_redis() {
  mkdir -p "$RUN_DIR"
  local host="${FIDES__REDIS__HOST:-127.0.0.1}"
  local port="${FIDES__REDIS__PORT:-6380}"
  local password="${FIDES__REDIS__PASSWORD:-redispassword}"

  if command -v redis-cli >/dev/null 2>&1 && redis-cli -h "$host" -p "$port" -a "$password" PING >/dev/null 2>&1; then
    echo "Redis already running with correct password."
    return
  fi

  nohup "$PROJECT_ROOT/dockerless/start_redis.sh" > "$REDIS_LOG" 2>&1 & echo $! > "$REDIS_PID_FILE"
  sleep 1
  if ! redis-cli -h "$host" -p "$port" -a "$password" PING >/dev/null 2>&1; then
    echo "Redis failed to start; see $REDIS_LOG" >&2
    exit 1
  fi
  echo "Redis ready (log: $REDIS_LOG)"
}

start_api() {
  mkdir -p "$RUN_DIR"
  cd "$PROJECT_ROOT"
  nohup dockerless/start_api.sh > "$RUN_DIR/api.log" 2>&1 & echo $! > "$API_PID_FILE"
  echo "API started (pid $(cat "$API_PID_FILE"))"
}

start_workers() {
  mkdir -p "$RUN_DIR"
  cd "$PROJECT_ROOT"
  nohup dockerless/start_workers.sh other > "$RUN_DIR/w1.log" 2>&1 & echo $! > "$W1_PID_FILE"
  nohup dockerless/start_workers.sh privacy > "$RUN_DIR/w2.log" 2>&1 & echo $! > "$W2_PID_FILE"
  nohup dockerless/start_workers.sh dsr > "$RUN_DIR/w3.log" 2>&1 & echo $! > "$W3_PID_FILE"
  echo "Workers started (pids: $(cat "$W1_PID_FILE" 2>/dev/null) $(cat "$W2_PID_FILE" 2>/dev/null) $(cat "$W3_PID_FILE" 2>/dev/null))"
}

start_ui() {
  ensure_node
  mkdir -p "$RUN_DIR"
  local clients_dir="$PROJECT_ROOT/clients"
  cd "$clients_dir"

  local lock_file="package-lock.json"
  local stamp="$RUN_DIR/npm-ci.stamp"
  if [ ! -d node_modules ] || [ ! -f "$stamp" ] || [ "$lock_file" -nt "$stamp" ]; then
    echo "Installing front-end deps via npm ci..."
    npm ci
    touch "$stamp"
  fi

  echo "Starting npm run dev (clients workspace)..."
  nohup npm run dev > "$RUN_DIR/ui.log" 2>&1 & echo $! > "$UI_PID_FILE"
  echo "UI started (pid $(cat "$UI_PID_FILE"))"
}

stop_pidfile() {
  local f="$1"
  if [ -f "$f" ]; then
    local pid
    pid="$(cat "$f" 2>/dev/null || true)"
    if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" || true
    fi
    rm -f "$f"
  fi
}

down_all() {
  stop_pidfile "$W3_PID_FILE"
  stop_pidfile "$W2_PID_FILE"
  stop_pidfile "$W1_PID_FILE"
  stop_pidfile "$API_PID_FILE"
  stop_pidfile "$UI_PID_FILE"
  stop_pidfile "$REDIS_PID_FILE"
  pkill -f "uvicorn.*fides.api.main:app" >/dev/null 2>&1 || true
  pkill -f "fides worker" >/dev/null 2>&1 || true
  if [ -f "$REDIS_LOG" ]; then
    pkill -f "redis-server" >/dev/null 2>&1 || true
  fi
  ( cd "$PROJECT_ROOT" && dockerless/stop_postgres.sh > "$POSTGRES_LOG" 2>&1 || true )
}

status() {
  for f in "$API_PID_FILE" "$W1_PID_FILE" "$W2_PID_FILE" "$W3_PID_FILE" "$REDIS_PID_FILE" "$UI_PID_FILE"; do
    if [ -f "$f" ]; then echo "$(basename "$f" .pid): running (pid $(cat "$f"))"; else echo "$(basename "$f" .pid): stopped"; fi
  done
  if command -v pg_isready >/dev/null 2>&1; then
    if pg_isready -h "${FIDES__DATABASE__SERVER:-127.0.0.1}" -p "${FIDES__DATABASE__PORT:-15432}" -U "${FIDES__DATABASE__USER:-postgres}" >/dev/null 2>&1; then
      echo "postgres: ready"
    else
      echo "postgres: stopped"
    fi
  fi
}

health() {
  local base_url="${NEXT_PUBLIC_FIDESCTL_API_SERVER:-http://localhost:8080}"
  base_url="${base_url%/}"
  local url="${base_url}/health"

  if ! command -v curl >/dev/null 2>&1; then
    echo "curl is required to perform the health check." >&2
    return 1
  fi

  if curl -fsS "$url" >/dev/null; then
    echo "API healthy at $url"
  else
    echo "API not responding at $url" >&2
    return 1
  fi
}

reset_db() {
  local server="${FIDES__DATABASE__SERVER:-127.0.0.1}"
  local port="${FIDES__DATABASE__PORT:-15432}"
  local user="${FIDES__DATABASE__USER:-postgres}"
  local password="${FIDES__DATABASE__PASSWORD:-fides}"
  PGPASSWORD="$password" psql -U "$user" -h "$server" -p "$port" -d postgres \
    -c "DROP DATABASE IF EXISTS fides; CREATE DATABASE fides;" || {
      echo "DB reset failed" >&2; exit 1; }
  echo "DB reset complete"
}

logs() {
  tail -n 100 -F "$RUN_DIR"/*.log
}

usage() {
  cat <<EOF
Usage: $(basename "$0") <command>
Commands:
  up         - start Redis, API, and workers
  down       - stop API and workers
  api        - start API only
  w1|w2|w3   - start individual workers (default|privacy_prefs|dsr)
  ui         - install deps (as needed) and run npm dev workspace
  seed       - populate the database with sample data
  status     - show process status
  logs       - tail logs
  health     - check API health
  reset-db   - drop and recreate fides DB (danger!)
EOF
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    up)
      require_cmds initdb pg_ctl pg_isready psql redis-server uvicorn fides
      ensure_conda; export_env; start_postgres; start_redis; start_api; start_workers; status; sleep 2; health ;;
    down)
      down_all ;;
    api)
      require_cmds initdb pg_ctl pg_isready psql uvicorn
      ensure_conda; export_env; start_postgres; start_redis; start_api ;;
    w1)
      require_cmds initdb pg_ctl pg_isready psql redis-server fides
      ensure_conda; export_env; start_postgres; start_redis; cd "$PROJECT_ROOT"; nohup dockerless/start_workers.sh other > "$RUN_DIR/w1.log" 2>&1 & echo $! > "$W1_PID_FILE" ;;
    w2)
      require_cmds initdb pg_ctl pg_isready psql redis-server fides
      ensure_conda; export_env; start_postgres; start_redis; cd "$PROJECT_ROOT"; nohup dockerless/start_workers.sh privacy > "$RUN_DIR/w2.log" 2>&1 & echo $! > "$W2_PID_FILE" ;;
    w3)
      require_cmds initdb pg_ctl pg_isready psql redis-server fides
      ensure_conda; export_env; start_postgres; start_redis; cd "$PROJECT_ROOT"; nohup dockerless/start_workers.sh dsr > "$RUN_DIR/w3.log" 2>&1 & echo $! > "$W3_PID_FILE" ;;
    ui)
      require_cmds initdb pg_ctl pg_isready psql redis-server uvicorn fides
      ensure_conda; export_env; start_postgres; start_redis; start_ui ;;
    seed)
      require_cmds initdb pg_ctl pg_isready psql redis-server
      ensure_conda; export_env; start_postgres; start_redis; cd "$PROJECT_ROOT"; PYTHONPATH="$PROJECT_ROOT/src" python dockerless/seed_data.py ;;
    status)
      status ;;
    logs)
      logs ;;
    health)
      health ;;
    reset-db)
      ensure_conda; export_env; reset_db ;;
    *)
      usage ;;
  esac
}

main "$@"
