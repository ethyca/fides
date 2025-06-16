import pytest

# -----------------------------------------------------------------------------
# Lightweight overrides for heavy autouse fixtures defined in the repo-level
# `tests/conftest.py`.  These overrides are *local* to the `tests/ops/schemas`
# test package so they do not affect the broader suite.  They simply noop the
# fixtures that would otherwise initialise the application, database, or Celery
# infrastructure – none of which are required for pure TimeBasedPartitioning
# unit tests.
# -----------------------------------------------------------------------------


@pytest.fixture(scope="function", autouse=True)  # type: ignore[arg-type]
def clear_db_tables():  # pylint: disable=unused-argument
    """Override heavyweight fixture with no-op to avoid DB connectivity."""
    yield


@pytest.fixture(scope="session", autouse=True)  # type: ignore[arg-type]
def celery_use_virtual_worker():  # pylint: disable=unused-argument
    """Disable Celery worker spin-up for this test subset."""
    yield
