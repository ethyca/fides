#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="${RUN_DIR:-/tmp/fides-dev}"
REDIS_DIR="${RUN_DIR}/redis"
CONF_FILE="${REDIS_DIR}/redis.conf"
LOG_FILE="${RUN_DIR}/redis.log"

HOST="${FIDES__REDIS__HOST:-127.0.0.1}"
PORT="${FIDES__REDIS__PORT:-6380}"
PASSWORD="${FIDES__REDIS__PASSWORD:-redispassword}"

if ! command -v redis-server >/dev/null 2>&1; then
  echo "redis-server not found on PATH." >&2
  exit 1
fi

mkdir -p "$REDIS_DIR"

cat >"$CONF_FILE" <<CFG
bind ${HOST}
port ${PORT}
requirepass ${PASSWORD}
daemonize no
protected-mode no
logfile "${LOG_FILE}"
appendonly yes
CFG

exec redis-server "$CONF_FILE"
