# Test Structure Analysis & Recommendations

> **Status:** Phase 1 has been implemented in this PR. See the "Phase 1" section below for details on what was done.

## Executive Summary

The test suite contains **~6,133 test functions** across **~483 test files**. The original architecture made it structurally impossible to run tests without a database, even for pure unit tests that don't need one. This was not because the tests themselves require a database, but because **autouse fixtures in the root `conftest.py` forced a DB dependency on every single test**. Fixing this did **not** require a huge refactor -- it required targeted changes to the conftest fixture architecture, and the test files themselves remained untouched.

---

## Current Test Structure

### Directory Layout

```
tests/
├── api/          (~720 tests)  - API layer tests (models, middleware, endpoints, tasks)
├── ctl/          (~566 tests)  - CLI/control plane tests
├── fixtures/     (shared fixtures, not test files)
├── integration/  (~3 tests)    - Workflow integration tests
├── lib/          (~120 tests)  - Library/utility tests
├── ops/          (~4,473 tests) - Core operations tests (largest area by far)
├── service/      (~196 tests)  - Service layer tests
├── task/         (~26 tests)   - Celery/task tests
├── util/         (~24 tests)   - Utility tests
├── qa/           (~1 test)     - QA scenario tests
└── conftest.py   (root conftest - ~2,500 lines)
```

### CI Test Groups (from `noxfiles/ci_nox.py`)

| CI Group | What it runs | Marker |
|---|---|---|
| `ctl-unit` | `tests/ctl/` | `unit` |
| `ctl-not-external` | `tests/ctl/` | `not external` |
| `ctl-integration` | `tests/ctl/` | `integration` |
| `ctl-external` | `tests/ctl/` | `external` |
| `ops-unit` / `ops-unit-api` / `ops-unit-non-api` | `tests/ops/` | `not integration and not integration_external and not integration_saas` |
| `ops-integration` | `tests/ops/` + `tests/integration/` | `integration` |
| `ops-external-datastores` | `tests/ops/` | `integration_external` |
| `ops-saas` | `tests/ops/` | `integration_saas` |
| `api` | `tests/api/` | `not integration and not integration_external and not integration_saas` |
| `lib` | `tests/lib/` | (all) |
| `misc-unit` | `tests/service/`, `tests/task/`, `tests/util/` | `not integration and not integration_*` |
| `misc-integration` | same dirs | `integration_bigquery or integration_snowflake or integration_postgres or integration` |

### Existing Markers (from `pyproject.toml`)

```
unit:        "only runs tests that don't require non-python dependencies (i.e. a database)"
integration: "only runs tests that require application dependencies (i.e. a database)"
external:    "only runs tests that require access to non-docker, external services (i.e. Snowflake)"
```

Plus many connector-specific markers: `integration_postgres`, `integration_mysql`, `integration_saas`, etc.

---

## The Core Problem: Why You Can't Run Tests Without a DB

### Problem 1: Autouse fixtures force DB on every test

In `tests/conftest.py`, there are three `autouse=True` fixtures that run for **every single test**:

```python
# Line 2061 - Runs for EVERY test function, requires db + async_session
@pytest.fixture(scope="function", autouse=True)
async def clear_db_tables(db, async_session):
    """Clear data from tables between tests."""
    yield
    # ... deletes all data from all tables ...

# Line 833 - Runs for the entire session, spins up a Celery worker
@pytest.fixture(autouse=True, scope="session")
def celery_use_virtual_worker(celery_session_worker):
    yield celery_session_worker

# Line 423 - This one is fine (no DB dependency)
@pytest.fixture(scope="function", autouse=True)
def clear_get_config_cache() -> None:
    get_config.cache_clear()
```

The `clear_db_tables` fixture is the primary blocker. Because it's `autouse=True` at the root conftest level, **every test in the entire suite** -- including pure schema validation tests, utility tests, and graph algorithm tests -- transitively depends on a live database session. The `db` fixture itself is `scope="session"` and connects to a real PostgreSQL database.

### Problem 2: Session-scoped DB fixture with global reach

The `db` fixture (line 134) is `scope="session"` and creates a real SQLAlchemy session to the test database. Since `clear_db_tables` is autouse and depends on `db`, this session is created at session startup even if no test actually needs it.

### Problem 3: All "unit" tests still run inside Docker with a DB

Looking at `noxfiles/setup_tests_nox.py`, even the "unit" test groups (`ops-unit`, `ctl-unit`, `misc-unit`) all run via `START_APP` which starts the full Docker Compose stack (including PostgreSQL and Redis). The `unit` marker definition says "tests that don't require non-python dependencies" but the test infrastructure still provides them.

### Problem 4: Massive root conftest with wildcard imports

The root `conftest.py` imports fixtures from **29 fixture files** via wildcard imports:

```python
from tests.fixtures.application_fixtures import *
from tests.fixtures.postgres_fixtures import *
from tests.fixtures.mongodb_fixtures import *
# ... 26 more ...
```

This means every test session loads hundreds of fixture definitions, even if the tests being run don't need any of them.

---

## Answering Your Questions

### "Are all tests that use a real DB considered integration tests?"

**No, not in the current codebase.** The distinction between "unit" and "integration" tests is currently based on **pytest markers**, not on actual DB usage. Many tests marked as "unit" (or unmarked) still use the `db` fixture directly:

- Test files where tests directly take `db` as a parameter: **~219 files / ~4,006 tests**
- Test files where tests do NOT directly take `db`: **~264 files / ~2,127 tests**

However, even the 2,127 tests that don't directly use `db` are still **forced to connect to a DB** due to the `clear_db_tables` autouse fixture.

A more useful classification would be:

| Category | Description | Needs DB? |
|---|---|---|
| **True Unit Tests** | Schema validation, graph algorithms, utility functions, config parsing, masking strategies, pagination logic | No |
| **DB Unit Tests** | Tests that verify ORM models, CRUD operations, or service logic by writing/reading from the app's own Postgres DB | Yes (app DB) |
| **API Tests** | Tests that hit API endpoints via TestClient, which need the app + DB to handle requests | Yes (app DB) |
| **Integration Tests** | Tests that verify connectivity and operations against external datastores (Postgres, MySQL, MongoDB, etc.) | Yes (external DBs) |
| **External Tests** | Tests against cloud services (Snowflake, BigQuery, Redshift, etc.) | Yes (cloud services) |

### "Will this require a huge refactor?"

**No.** The key changes are architectural (fixture organization), not test-level. Most test files won't need modification. Here's the breakdown:

| Change | Scope | Effort |
|---|---|---|
| Make `clear_db_tables` not autouse | 1 line in `conftest.py` | Trivial |
| Add `clear_db_tables` to tests that need it | ~219 test files or via conftest layering | Medium |
| Separate conftest into DB vs non-DB layers | New conftest architecture | Medium |
| Create a no-DB CI job | New nox session + CI config | Small |
| Move wildcard imports to appropriate conftest files | File reorganization | Medium |

The **individual test files** mostly don't need changes if you use conftest layering properly (see recommendations below).

---

## Recommendations

### Phase 1: Quick Win -- Enable True No-DB Unit Tests (Low effort, high impact)

**Goal:** Run ~1,500+ tests without needing a database at all.

#### Step 1a: Make `clear_db_tables` conditional instead of autouse

Change the root conftest so that `clear_db_tables` only runs for tests that actually use the `db` fixture. Two approaches:

**Option A: Remove autouse and use a marker-based conftest (Recommended)**

```python
# tests/conftest.py - Change from autouse=True to a conditional fixture
@pytest.fixture(scope="function")  # Remove autouse=True
async def clear_db_tables(db, async_session):
    yield
    # ... existing cleanup logic ...
```

Then add it as autouse in a sub-conftest for directories that need it:

```python
# tests/ops/conftest.py (and similar for tests/api/, tests/ctl/, etc.)
@pytest.fixture(autouse=True)
def _auto_clear_db(clear_db_tables):
    """Auto-apply DB cleanup for all tests in this directory."""
    yield
```

**Option B: Skip cleanup when db isn't used (simpler but less clean)**

```python
@pytest.fixture(scope="function", autouse=True)
async def clear_db_tables(request):
    yield
    if "db" in request.fixturenames:
        db = request.getfixturevalue("db")
        async_session = request.getfixturevalue("async_session")
        # ... existing cleanup logic ...
```

#### Step 1b: Make `celery_use_virtual_worker` conditional

Same pattern -- either remove autouse and apply it in sub-conftest files, or make it conditional.

#### Step 1c: Create a no-DB test runner

Add a new nox session and CI job:

```python
# In setup_tests_nox.py
def pytest_unit_no_db(session: Session, pytest_config: PytestConfig) -> None:
    """Runs true unit tests without any infrastructure."""
    run_command = (
        "pytest",
        *pytest_config.args,
        "-m", "unit",
        "tests/ops/schemas/",
        "tests/ops/util/",
        "tests/ops/graph/",
        "tests/ops/service/masking/",
        "tests/ops/service/pagination/",
        "tests/ops/service/processors/",
        "tests/ops/service/storage/streaming/",
        "tests/lib/",
    )
    session.run(*run_command)
```

This could run **outside of Docker** in CI, dramatically reducing CI time.

### Phase 2: Restructure Conftest Hierarchy (Medium effort, high impact)

**Goal:** Clean fixture ownership so each test directory only loads what it needs.

#### Step 2a: Split the root conftest.py

The root `conftest.py` is ~2,500 lines with 29 wildcard imports. Split it into layers:

```
tests/
├── conftest.py                    # ONLY: markers, config, non-DB fixtures
├── db_conftest.py                 # DB session fixtures (imported by sub-conftest files)
├── fixtures/                      # Keep as-is but don't wildcard-import at root
├── ops/
│   └── conftest.py                # Import DB + ops-specific fixtures
├── api/
│   └── conftest.py                # Import DB + api-specific fixtures
├── ctl/
│   └── conftest.py                # Import DB + ctl-specific fixtures
└── lib/
    └── conftest.py                # Minimal, mostly no-DB
```

The root conftest should contain only:
- Session config (`config`, `test_config_path`, etc.)
- Non-DB utility fixtures (`resources_dict`, `test_manifests`, `fides_toml_path`)
- Marker configuration
- The `clear_get_config_cache` autouse fixture

#### Step 2b: Move wildcard fixture imports to directory-level conftest files

Instead of importing all 29 fixture files at the root:

```python
# tests/ops/conftest.py
from tests.fixtures.application_fixtures import *
from tests.fixtures.postgres_fixtures import *
# ... only the fixtures this directory actually needs ...
```

This reduces import-time overhead and makes dependencies explicit.

### Phase 3: Improve Marker Discipline (Low effort, ongoing)

#### Step 3a: Enforce marker usage

Currently, many tests have no marker at all. The `ops-unit` CI group uses the negative pattern:
```
-m "not integration and not integration_external and not integration_saas"
```

This means any unmarked test is treated as a "unit" test, even if it uses the DB. Consider:

1. Adding a `pytest-marker-enforce` plugin or custom hook to require markers
2. Establishing a convention where DB-using tests are at minimum tagged `@pytest.mark.usefixtures("db")` or a custom marker

#### Step 3b: Add a `db_required` marker

```python
# pyproject.toml
markers = [
    "db_required: test requires a database connection",
    # ... existing markers ...
]
```

Use it to explicitly tag tests that need a DB, making it easy to exclude them:
```bash
pytest -m "unit and not db_required" tests/
```

### Phase 4: Consider Test Doubles for DB-Using Tests (High effort, selective)

Some tests that currently use the real DB could be refactored to use mocks or in-memory alternatives. Good candidates:

1. **Tests that create ORM objects just to test business logic** -- Use factory functions that return detached objects or dataclass equivalents
2. **API endpoint tests that could use dependency injection** -- FastAPI's `Depends` makes it easy to swap the DB session for a mock
3. **Tests that just need a "policy" or "connection config" object** -- Create builder/factory patterns that don't need the DB

However, this is a case-by-case decision. Many tests legitimately need the DB to verify ORM behavior, cascade deletes, constraints, etc. Don't over-mock.

---

## Quantified Impact

| Phase | Tests runnable without DB | Estimated CI time saved | Effort |
|---|---|---|---|
| Current state | 0 | - | - |
| Phase 1 (autouse fix) | ~1,500-2,000 | 5-10 min per run | 1-2 days |
| Phase 2 (conftest split) | Same count but faster imports | 1-2 min per run | 3-5 days |
| Phase 3 (marker discipline) | Better categorization | Organizational | Ongoing |
| Phase 4 (test doubles) | ~500 more | Varies | Weeks (selective) |

---

## Specific Files That Are True Unit Tests (No DB Needed)

These test files contain tests that are pure logic tests with no database dependency. They would immediately benefit from Phase 1:

### Schema/Validation Tests (~400+ tests)
- `tests/ops/schemas/test_partitioning_schema.py` (64 tests)
- `tests/ops/schemas/test_privacy_center_config.py` (22 tests)
- `tests/ops/schemas/test_saas_request.py` (14 tests)
- `tests/ops/schemas/test_identity_schema.py` (13 tests)
- `tests/ops/schemas/test_privacy_request.py` (11 tests)
- `tests/ops/schemas/connection_configuration/test_email_schemas.py` (12 tests)
- `tests/ops/schemas/connection_configuration/test_connection_secrets_saas.py` (9 tests)
- `tests/ops/schemas/test_consentable_item_schema.py` (5 tests)

### Graph/Algorithm Tests (~150+ tests)
- `tests/ops/graph/test_config.py` (35 tests)
- `tests/ops/task/test_filter_element_match.py` (33 tests)
- `tests/ops/task/test_refine_target_path.py` (30 tests)
- `tests/ops/graph/test_graph_traversal.py` (22 tests -- some marked integration)
- `tests/ops/task/test_filter_results.py` (19 tests)
- `tests/ops/graph/test_traversal_optimization_comparison.py` (15 tests)
- `tests/ops/graph/test_data_types.py` (9 tests)
- `tests/ops/graph/test_edge.py` (8 tests)

### Utility Tests (~200+ tests)
- `tests/ops/util/test_saas_util.py` (55 tests)
- `tests/ops/util/test_collection_util.py` (47 tests)
- `tests/ops/util/test_cache.py` (31 tests)
- `tests/ops/util/test_dataset_yaml.py` (10 tests)
- `tests/ops/util/test_logger.py` (13 tests)
- `tests/ops/util/test_text.py` (5 tests)
- `tests/ops/util/encryption/test_secrets_util.py` (10 tests)

### Service Logic Tests (~300+ tests)
- `tests/ops/service/storage/streaming/` (entire directory, ~170+ tests)
- `tests/ops/service/processors/` (~50+ tests)
- `tests/ops/service/pagination/` (~50+ tests)
- `tests/ops/service/masking/strategy/` (~30+ tests)
- `tests/ops/service/saas_request/` (20 tests)
- `tests/ops/service/authentication/` (20+ tests, some need mocking)

### Conditional Dependencies Tests (~176+ tests)
- `tests/api/task/conditional_dependencies/` (entire directory -- already uses mock_db)

### Config Tests (~100+ tests)
- `tests/ctl/core/config/` (entire directory)

---

## Recommended Starting Point

If you want maximum impact with minimum risk, start with **Phase 1, Option B** (the conditional `clear_db_tables`). It's a single change in `tests/conftest.py` that immediately unblocks running true unit tests without a database, while preserving existing behavior for all DB-using tests. Combined with a new no-DB CI job, this could save significant CI time on every PR.
