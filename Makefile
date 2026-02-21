.PHONY: test test-fast test-unit test-parallel test-ci lint typecheck check

# ---------------------------------------------------------------------------
# Local development test targets
# ---------------------------------------------------------------------------

## Run all tests (inside Docker, same as CI)
test:
	uv run nox -s "pytest(ops-unit)"

## Fast: run unit tests in parallel without coverage (no Docker needed for pure unit tests)
test-fast:
	uv run pytest tests/ -m "unit" -n auto --dist worksteal -q --tb=short --no-header -p no:celery

## Run a specific test group (e.g., make test-group GROUP=ops-unit-api)
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

## Collect all tests (syntax check)
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

## Run the same test groups as CI Safe-Tests
test-ci-safe:
	@for group in ctl-not-external ops-unit-api ops-unit-non-api ops-integration api lib misc-unit misc-integration; do \
		echo "=== Running $$group ==="; \
		uv run nox -s "pytest($$group)" || exit 1; \
	done
