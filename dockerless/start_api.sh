#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
HOST="${FIDES_API_HOST:-0.0.0.0}"
PORT="${FIDES_API_PORT:-8080}"

if ! command -v uvicorn >/dev/null 2>&1; then
  echo "uvicorn not found; ensure the Fides environment is activated." >&2
  exit 1
fi

cd "$PROJECT_ROOT"
exec uvicorn --host "$HOST" --port "$PORT" --reload \
  --reload-dir src --reload-dir data --reload-include='*.yml' fides.api.main:app
