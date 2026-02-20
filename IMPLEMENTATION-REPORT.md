# Test Harness Implementation Report: Running Lib Tests Without Docker

## Objective

Set up a test harness that runs the Fides `tests/lib/` suite via `uv run pytest` without Docker, using local PostgreSQL and Redis instead.

## What Was Tried

### 1. Understanding the Failure Mode

**Problem:** Running `uv run pytest tests/lib/` failed with:
```
psycopg2.OperationalError: could not translate host name "fides-db" to address: Name or service not known
```

**Cause:** The default config in `.fides/fides.toml` points to `fides-db` (a Docker Compose service hostname) for PostgreSQL and `redis` for Redis. These hostnames only resolve inside Docker networks.

### 2. Python Version Pin (Required for uv)

**Tried:** Running `uv run pytest` without specifying Python version.

**Result:** Failed. uv defaulted to Python 3.14, and `snowflake-connector-python` failed to build (C++ extension incompatible with 3.14).

**Fix:** Install and pin Python 3.13:
```bash
uv python install 3.13
uv run --python 3.13 pytest ...
```

### 3. Config Override via Environment Variables

**Tried:** Override database and Redis settings via `FIDES__*` env vars so tests connect to localhost.

**Result:** Worked. Fides uses pydantic-settings with `env_prefix="FIDES__"` and double-underscore nesting (e.g. `FIDES__DATABASE__SERVER`). Env vars override `.fides/fides.toml` values.

**Required variables:**
- `FIDES__DATABASE__SERVER=127.0.0.1`
- `FIDES__DATABASE__USER=postgres`
- `FIDES__DATABASE__PASSWORD=fides`
- `FIDES__DATABASE__PORT=5432`
- `FIDES__DATABASE__DB=fides`
- `FIDES__DATABASE__TEST_DB=fides_test`
- `FIDES__REDIS__HOST=127.0.0.1`
- `FIDES__REDIS__PORT=6379`
- `FIDES__REDIS__PASSWORD=""` (local redis-server typically has no password; Docker uses `redispassword`)
- `FIDES__TEST_MODE=true` (ensures `test_db` is used)

### 4. Running Tests in Isolation (No Postgres/Redis)

**Tried:** Copy `tests/lib/test_version.py` to a temp dir with a minimal conftest, set `PYTHONPATH=src`, run pytest. This avoided loading the root `tests/conftest.py` which pulls in DB fixtures.

**Result:** Worked for `test_version.py` only (~0.27s). Not suitable for the full lib suite, which needs DB and Redis for most tests.

### 5. Disabling Redis

**Considered:** Setting `FIDES__REDIS__ENABLED=false` to avoid Redis dependency.

**Result:** Not pursued. Redis is used extensively (cache, locks, rate limiting). `get_cache()` raises `RedisNotConfigured` when disabled. Installing Redis locally was simpler.

## What Worked

### 1. Installing PostgreSQL

```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-client
sudo service postgresql start
```

### 2. Creating Databases and User

```bash
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'fides';"
sudo -u postgres psql -c "CREATE DATABASE fides;"
sudo -u postgres psql -c "CREATE DATABASE fides_test;"
```

Connection verified with:
```bash
PGPASSWORD=fides psql -h 127.0.0.1 -U postgres -d fides_test -c "SELECT 1;"
```

### 3. Installing and Starting Redis

```bash
sudo apt-get install -y redis-server
sudo service redis-server start
```

Local redis-server runs without a password by default; `FIDES__REDIS__PASSWORD=""` is used.

### 4. Running Migrations

Migrations run automatically when the FastAPI app starts. The `api_client` fixture uses `TestClient(app)`, which triggers app lifespan and `run_database_startup` (including `configure_db` and `ApplicationConfig.update_config_set`). No manual migration step was needed.

### 5. Test Runner Script

Created `scripts/run_lib_tests.sh` that:
- Sets all required env vars for local Postgres and Redis
- Invokes `uv run --python 3.13 pytest` with any path/args passed through

Usage:
```bash
./scripts/run_lib_tests.sh tests/lib/              # lib suite (recommended, full pass)
./scripts/run_lib_tests.sh noxfiles/               # noxfiles (full pass)
./scripts/run_lib_tests.sh tests/api/              # api suite (1 known fail)
./scripts/run_lib_tests.sh tests/ctl/ -m unit --ignore=tests/ctl/core/test_dataset.py
./scripts/run_lib_tests.sh tests/lib/test_version.py  # single file
./scripts/run_lib_tests.sh -x                      # stop on first failure
```

## What Didn't Work

1. **Docker-based nox:** `nox -s "pytest(lib)"` requires Docker (not available in this environment).
2. **uv without Python pin:** Defaulted to Python 3.14; snowflake-connector build failed.
3. **Skipping Redis:** Would require significant code changes; installing Redis was straightforward.
4. **SQLite:** Fides uses PostgreSQL-specific features (e.g. `citext` extension). Not explored.

## Suite-by-Suite Results

Run each suite with: `./scripts/run_lib_tests.sh <path> [pytest-args]`

| Suite | Command | Result | Notes |
|-------|---------|--------|-------|
| **lib** | `tests/lib/` | ✅ **293 passed** | Full pass, ~27s |
| **noxfiles** | `noxfiles/` | ✅ **315 passed** | Full pass, ~29s |
| **api** | `tests/api/` | 1390 passed, 1 failed | 1 fail: `test_read_only_cache_uses_fallback_settings` – expects fixture password `test-writer-password`, but `FIDES__REDIS__PASSWORD=""` overrides it |
| **ctl** | `tests/ctl/ -m unit --ignore=tests/ctl/core/test_dataset.py` | 405 passed, 8 failed | Collection error without `--ignore`: `test_dataset.py` imports `pymssql` (not installed). With ignore: config tests expect `fides-db` hostname; cli tests expect running server |
| **ctl** (no args) | `tests/ctl/` | ❌ 1 collection error | `tests/ctl/core/test_dataset.py` fails to import `pymssql` |
| **ops unit** | `tests/ops/ -m unit` | 282 passed, 3 failed, 26 errors | IntegrityError/FK violations (taxonomy seeding), ObjectDeletedError, some network-dependent tests |
| **service** | `tests/service/` | 563 passed, 6 failed, 17 errors | Shares fixtures with lib; taxonomy FK violations; `postgres_example` hostname in fixtures |
| **task** | `tests/task/` | 285 passed, 1 failed, 35 errors | Similar taxonomy/DB fixture issues |
| **util** | `tests/util/` | 303 passed, 2 failed, 13 errors | KeyOrNameAlreadyExists, ObjectDeletedError |
| **qa** | `tests/qa/` | 278 passed, 3 failed, 9 xfailed, 12 errors | 9 tests marked xfail (need external services); lib fixture pollution |
| **integration** | `tests/integration/` | 279 passed, 17 errors | Taxonomy FK violations during workflow setup |

### Common Failure Patterns

1. **Env var leakage:** `FIDES__REDIS__PASSWORD=""` overrides fixture config; some tests expect specific values (e.g. `test-writer-password`).
2. **Taxonomy seeding:** Tests that load fideslang taxonomy hit `ctl_data_categories_parent_key_fkey` when parent keys don’t exist (ordering/deduplication).
3. **Docker hostnames:** Fixtures reference `postgres_example`, `fides-db`, etc., which don’t resolve outside Docker.
4. **Missing deps:** `pymssql` is optional; `test_dataset.py` fails at import without it.
5. **Shared DB state:** Running broader paths collects and runs lib + other tests together; fixture/transaction interaction causes ObjectDeletedError, StaleDataError.

## Final Result

**lib and noxfiles pass fully.** Other suites partially pass; failures are mostly due to env overrides, taxonomy seeding, and fixture hostnames.

## Prerequisites (for fresh environment)

1. **uv** – `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. **Python 3.13** – `uv python install 3.13`
3. **PostgreSQL 16** – `sudo apt-get install postgresql postgresql-client`
4. **Redis** – `sudo apt-get install redis-server`
5. **Databases** – Create `fides` and `fides_test`, set postgres password to `fides`
6. **Services** – `sudo service postgresql start && sudo service redis-server start`

## Files Created/Modified

- **Created:** `scripts/run_lib_tests.sh` – Test runner with env configuration
- **Created:** `IMPLEMENTATION-REPORT.md` – This document
