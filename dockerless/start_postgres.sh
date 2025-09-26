#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUN_DIR="${RUN_DIR:-/tmp/fides-dev}"
PG_DIR="${RUN_DIR}/postgres"
PGDATA="${PG_DIR}/data"
LOGFILE="${RUN_DIR}/postgres.log"

HOST="${FIDES__DATABASE__SERVER:-127.0.0.1}"
PORT="${FIDES__DATABASE__PORT:-15432}"
DB_USER="${FIDES__DATABASE__USER:-postgres}"
DB_PASSWORD="${FIDES__DATABASE__PASSWORD:-fides}"

for dep in initdb pg_ctl pg_isready psql; do
  if ! command -v "$dep" >/dev/null 2>&1; then
    echo "Required Postgres utility '$dep' not found on PATH." >&2
    exit 1
  fi
done

mkdir -p "$PG_DIR"

if [ ! -f "${PGDATA}/PG_VERSION" ]; then
  echo "Initializing postgres data directory at ${PGDATA}" >&2
  initdb -D "$PGDATA" -U "$DB_USER" >/dev/null
  cat >>"${PGDATA}/postgresql.conf" <<CFG
listen_addresses = '${HOST}'
port = ${PORT}
unix_socket_directories = '${PG_DIR}'
CFG
  cat >"${PGDATA}/pg_hba.conf" <<HBA
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
HBA
fi

if pg_ctl -D "$PGDATA" status >/dev/null 2>&1; then
  echo "Postgres already running using ${PGDATA}" >&2
  exit 0
fi

pg_ctl -D "$PGDATA" -l "$LOGFILE" start

for _ in {1..30}; do
  if pg_isready -h "$HOST" -p "$PORT" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! pg_isready -h "$HOST" -p "$PORT" >/dev/null 2>&1; then
  echo "Postgres failed to become ready; check ${LOGFILE}" >&2
  exit 1
fi

# Ensure the configured user has the expected password
PGPASSWORD="" psql -U "$DB_USER" -h "$HOST" -p "$PORT" -d postgres \
  -v ON_ERROR_STOP=1 <<SQL >/dev/null 2>&1
ALTER USER "$DB_USER" WITH PASSWORD '$DB_PASSWORD';
SQL

echo "Postgres started on ${HOST}:${PORT} (data dir ${PGDATA})"
