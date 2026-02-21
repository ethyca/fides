.PHONY: test test-fast test-unit test-local test-parallel test-ci lint typecheck check

# ---------------------------------------------------------------------------
# Local development test targets (no Docker required, needs local postgres+redis)
# ---------------------------------------------------------------------------

## Run all non-external tests natively with xdist parallelism (~1 min target)
test:
	uv run nox -s "pytest_native(not-external)"

## Fastest: unit tests only, no DB needed, parallel with worksteal
test-unit:
	uv run pytest tests/ -m "unit" -n auto --dist worksteal -q --tb=short --no-header -p no:celery

## Run non-external tests (includes postgres integration) natively in parallel
test-local:
	uv run pytest tests/ \
		-m "not integration_external and not integration_saas and not external and not integration_bigquery and not integration_snowflake and not integration_redshift and not integration_dynamodb and not integration_google_cloud_sql_mysql and not integration_google_cloud_sql_postgres and not integration_rds_mysql and not integration_rds_postgres and not integration_mongodb_atlas and not integration_scylladb and not integration_mariadb and not integration_mssql" \
		-n auto --dist worksteal -q --tb=short --no-header

## Run a specific test group via Docker (same as CI)
test-group:
	uv run nox -s "pytest($(GROUP))"

## Run tests matching a keyword (e.g., make test-k K=test_privacy_request)
test-k:
	uv run pytest tests/ -k "$(K)" -q --tb=short --no-header

## Run tests for a specific file
test-file:
	uv run pytest $(FILE) -q --tb=short --no-header

## Run tests in parallel with auto-detected workers
test-parallel:
	uv run pytest tests/ -n auto --dist worksteal -q --tb=short --no-header

## Collect all tests (syntax check, fast)
test-collect:
	uv run pytest --collect-only -q tests/

# ---------------------------------------------------------------------------
# Static checks
# ---------------------------------------------------------------------------

## Run linter
lint:
	uv run ruff check src tests noxfiles scripts noxfile.py
	uv run ruff format --check src tests noxfiles scripts noxfile.py

## Run type checker
typecheck:
	uv run mypy

## Run all static checks
check: lint typecheck

# ---------------------------------------------------------------------------
# CI helpers
# ---------------------------------------------------------------------------

## Validate test coverage mapping
test-coverage-map:
	uv run nox -s validate_test_coverage

## Run the same test groups as CI Safe-Tests (Docker-based)
test-ci-safe:
	@for group in ctl-not-external ops-unit-api ops-unit-non-api ops-integration api lib misc-unit misc-integration; do \
		echo "=== Running $$group ==="; \
		uv run nox -s "pytest($$group)" || exit 1; \
	done
