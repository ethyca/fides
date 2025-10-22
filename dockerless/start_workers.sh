#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROLE="${1:-other}"

if ! command -v fides >/dev/null 2>&1; then
  echo "The 'fides' CLI is required; activate the environment first." >&2
  exit 1
fi

cd "$PROJECT_ROOT"

case "$ROLE" in
  other)
    exec fides worker --exclude-queues=fides.dsr,fides.privacy_preferences,fidesplus.discovery_monitors_detection,fidesplus.discovery_monitors_classification,fidesplus.discovery_monitors_promotion
    ;;
  privacy)
    exec fides worker --queues=fides.privacy_preferences
    ;;
  dsr)
    exec fides worker --queues=fides.dsr
    ;;
  *)
    echo "Unknown worker role '$ROLE'. Expected one of: other, privacy, dsr." >&2
    exit 1
    ;;
 esac
