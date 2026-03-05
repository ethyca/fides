#!/bin/bash
# Run lib tests with local Postgres and Redis (no Docker)
# Requires: PostgreSQL and Redis installed and running locally

export PATH="$HOME/.local/bin:$PATH"

# Database: point to localhost instead of fides-db
export FIDES__DATABASE__SERVER="127.0.0.1"
export FIDES__DATABASE__USER="postgres"
export FIDES__DATABASE__PASSWORD="fides"
export FIDES__DATABASE__PORT="5432"
export FIDES__DATABASE__DB="fides"
export FIDES__DATABASE__TEST_DB="fides_test"

# Redis: point to localhost (default redis-server has no password)
export FIDES__REDIS__HOST="127.0.0.1"
export FIDES__REDIS__PORT="6379"
export FIDES__REDIS__PASSWORD=""

# Test mode - use test_db
export FIDES__TEST_MODE="true"

# Clear config cache so env vars are picked up
unset FIDES__CONFIG_PATH

exec uv run --python 3.13 pytest tests/lib/ -v "$@"
