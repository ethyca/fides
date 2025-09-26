#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="${RUN_DIR:-/tmp/fides-dev}"
PGDATA="${RUN_DIR}/postgres/data"

if [ ! -d "$PGDATA" ]; then
  exit 0
fi

if command -v pg_ctl >/dev/null 2>&1; then
  if pg_ctl -D "$PGDATA" status >/dev/null 2>&1; then
    pg_ctl -D "$PGDATA" stop -m fast >/dev/null 2>&1 || true
  fi
fi
