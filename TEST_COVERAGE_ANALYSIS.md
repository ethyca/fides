# Fides Backend Test Coverage Analysis

_Generated: 2026-02-22_

## Overview

The Fides backend has **430 test files** containing approximately **6,160 test functions** spread across the following directories:

| Test Directory | Test Files | Test Functions | Description |
|---|---|---|---|
| `tests/ops` | 314 | 4,526 | Privacy operations (largest suite) |
| `tests/api` | 45 | 720 | API models, middleware, conditional dependencies |
| `tests/ctl` | 43 | 568 | CLI and core CRUD operations |
| `tests/service` | 9 | 196 | Top-level service layer |
| `tests/lib` | 12 | 120 | Library utilities (crypto, OAuth, sessions) |
| `tests/task` | 3 | 26 | Celery tasks and async polling |
| `tests/integration` | 2 | 3 | End-to-end integration |
| `tests/qa` | 1 | 1 | QA smoke tests |

### Test Marker Distribution

- Only **46 / 430** test files use the `@pytest.mark.unit` marker
- Only **80 / 430** test files use the `@pytest.mark.integration` marker
- **304 files (~71%)** lack any test category marker
- **144 / 430** test files use mocking (`unittest.mock`, `@patch`, `MagicMock`)

---

## Critical Coverage Gaps

### 1. API Endpoints Without Tests

Three endpoint modules have **zero** corresponding test files. (Note: `connection_endpoints.py`, `connection_type_endpoints.py`, and `manual_webhook_endpoints.py` were initially flagged but actually have tests under different names — `test_connection_config_endpoints.py`, `test_connection_template_endpoints.py`, and `test_manual_webhooks.py` respectively.)

| File | Lines | Impact |
|---|---|---|
| `api/v1/endpoints/health.py` | ~50 | Health check endpoints (`/health`, `/health/database`, `/health/workers`) — critical for monitoring |
| `api/v1/endpoints/worker_endpoints.py` | 82 | Celery worker task management |
| `api/v1/endpoints/view.py` | 62 | UI evaluation view serving |
| `api/v1/endpoints/router_factory.py` | N/A | Dynamic router creation for generic CRUD |

The **health check endpoints** are the most notable gap — these are infrastructure-critical endpoints used for monitoring and load balancer health probes but have zero test coverage. The existing `test_healthcheck_server.py` tests Celery worker health, not these API-level health endpoints.

Overall, API endpoint coverage is strong at **~94%** (30 of 32 endpoint files have tests).

### 2. Service Layer — Untested Core Services

The `src/fides/service/` top-level module has only **9 test files** for **23 source files**. The following services have no dedicated tests:

| File | Lines | Functionality |
|---|---|---|
| `service/system/system_service.py` | 153 | System CRUD operations |
| `service/user/user_service.py` | 143 | User management (create, update, delete) |
| `service/messaging/messaging_service.py` | 317 | Email/messaging dispatch orchestration |
| `service/attachment_service.py` | 307 | File attachment handling for privacy requests |
| `service/privacy_request/privacy_request_csv_download.py` | 152 | CSV export of privacy request data |
| `service/privacy_request/privacy_request_query_utils.py` | 308 | Complex query building for privacy request filtering |
| `service/dataset/dataset_validator.py` | 67 | Dataset configuration validation |
| `service/taxonomy/handlers/legacy_handler.py` | 95 | Legacy taxonomy migration handling |

**`messaging_service.py` (317 lines)** and **`privacy_request_query_utils.py` (308 lines)** are particularly concerning — both implement complex business logic that is prone to subtle bugs.

### 3. Connectors Without Unit Tests

The `api/service/connectors/` directory contains 44+ connector files. Many have integration tests (which test end-to-end against real databases), but the following connectors lack any **unit-level** test file:

| Connector | Lines | Notes |
|---|---|---|
| `dynamodb_connector.py` | 178 | AWS DynamoDB — complex NoSQL logic |
| `rds_mysql_connector.py` | 164 | AWS RDS MySQL |
| `rds_postgres_connector.py` | 153 | AWS RDS Postgres |
| `rds_connector_mixin.py` | N/A | Shared RDS logic (no dedicated test) |
| `okta_connector.py` | 112 | Okta identity provider |
| `microsoft_sql_server_connector.py` | 59 | MSSQL connector |
| `redshift_connector.py` | 88 | AWS Redshift |
| `s3_connector.py` | 76 | AWS S3 storage access |
| `timescale_connector.py` | 5 | TimescaleDB |
| `website_connector.py` | 85 | Web scraping connector |
| `manual_task_connector.py` | 97 | Manual task processing |
| `manual_webhook_connector.py` | 61 | Manual webhook processing |

Additionally, the following **query config** modules have no tests:

- `bigquery_query_config.py`, `postgres_query_config.py`, `mysql_query_config.py`
- `mongodb_query_config.py`, `microsoft_sql_server_query_config.py`
- `redshift_query_config.py`, `google_cloud_postgres_query_config.py`
- `manual_query_config.py`

(Note: some of these may be indirectly exercised by end-to-end privacy request tests, but there are no isolated unit tests verifying query-building logic.)

### 4. Message Dispatch — Zero Unit Tests

`api/service/messaging/message_dispatch_service.py` is **957 lines** with zero corresponding test file. This service handles:
- Dispatching emails via multiple providers (Mailgun, SendGrid, Twilio, AWS SES)
- Subject access request notifications
- Consent verification emails
- Template rendering

Similarly, `api/service/messaging/messaging_crud_service.py` has tests, but the dispatch layer that actually sends messages does not.

### 5. Privacy Request Processing — Undertested Core

`api/service/privacy_request/request_runner_service.py` is **1,314 lines** — the largest single service file — and orchestrates the entire DSR (Data Subject Request) execution pipeline. While some integration tests exercise it end-to-end, there are **no isolated unit tests** that verify:
- Error handling paths
- Retry logic
- Edge cases in multi-connector orchestration
- Partial failure recovery

### 6. Utility Modules Without Tests

19 utility modules under `api/util/` have no tests:

| File | Lines | Risk |
|---|---|---|
| `connection_util.py` | 296 | Connection config helpers — heavily used |
| `consent_util.py` | 339 | Consent preference processing |
| `endpoint_utils.py` | 164 | API endpoint helpers |
| `fuzzy_search_utils.py` | 135 | Search functionality |
| `aws_util.py` | 118 | AWS credential handling |
| `cors_middleware_utils.py` | 48 | CORS configuration |
| `masking_util.py` | 31 | Data masking helpers |
| `sqlalchemy_filter.py` | 30 | Database query filtering |
| `url_util.py` | N/A | URL manipulation |
| `saas_config_updater.py` | N/A | SaaS config patching |

**`consent_util.py` (339 lines)** is notable — consent processing is a legally sensitive area where incorrect behavior could have compliance implications.

### 7. Schema Validation — Almost Entirely Untested

Out of 60+ schema files under `api/schemas/`, only a handful have dedicated tests. All 30+ `connection_secrets_*.py` schema files have **zero tests**. These schemas define Pydantic models for connection configuration secrets — missing validation tests means:
- Invalid connection configurations might pass validation silently
- Required field changes could break without detection
- Secret masking/serialization behavior is unverified

### 8. Models Without Tests

17 model files have no corresponding test files:

- `privacy_assessment.py` (330 lines) — privacy impact assessments
- `messaging_template.py` (150 lines) — email template management
- `worker_task.py` (123 lines) — async task tracking
- `openid_provider.py` (59 lines) — OIDC integration
- `tcf_purpose_overrides.py` — TCF consent framework
- `privacy_preferences.py` (v3) — new privacy preference model

---

## Structural Issues

### Test Organization is Fragmented

Tests for source code in `src/fides/api/service/` are spread across three different directories:
- `tests/service/` (9 files)
- `tests/ops/service/` (106 files)
- Inline within `tests/ops/` endpoint tests

This makes it difficult to assess coverage and find relevant tests for a given source file. A developer modifying `api/service/connectors/bigquery_connector.py` needs to look in at least 3 different places.

### Most Tests Lack Category Markers

71% of test files don't use `@pytest.mark.unit` or `@pytest.mark.integration`. This makes it impossible to:
- Run a fast unit-test-only CI pipeline
- Distinguish tests that need external dependencies from those that don't
- Measure the unit-to-integration test ratio

### Low Mocking Adoption

Only **144/430 (33%)** test files use mocking. In `tests/ops/` (the largest suite), only **75/312 (24%)** files use mocks. This suggests most tests are integration tests that depend on real database connections, making the test suite:
- Slower to run
- More fragile (flaky due to external dependencies)
- Harder to run in isolation

---

## Recommended Improvements (Prioritized)

### P0 — High Impact, High Risk

1. **Add unit tests for `request_runner_service.py`** (1,314 lines)
   - Test error handling, retry logic, partial failure scenarios
   - Mock connector dependencies to test orchestration logic in isolation
   - Estimated scope: 25-30 test functions

3. **Add unit tests for `message_dispatch_service.py`** (957 lines)
   - Test provider selection, template rendering, error handling per provider
   - Estimated scope: 15-20 test functions

4. **Add unit tests for `consent_util.py`** (339 lines)
   - Compliance-sensitive code — consent processing bugs have legal risk
   - Estimated scope: 10-15 test functions

5. **Add tests for `health.py` API endpoints** (3 endpoints, zero tests)
   - `/health`, `/health/database`, `/health/workers` — infrastructure-critical for monitoring
   - Estimated scope: 5-10 test functions

### P1 — Important Business Logic

6. **Add tests for `system_service.py` and `user_service.py`**
   - Core CRUD operations for two fundamental entities
   - Estimated scope: 10-15 test functions each

7. **Add tests for `messaging_service.py`** (317 lines)
   - Email orchestration logic — messaging failures cause user-facing issues
   - Estimated scope: 10-15 test functions

8. **Add tests for `privacy_request_query_utils.py`** (308 lines)
   - Complex query building is highly testable with unit tests
   - Estimated scope: 15-20 test functions

9. **Add schema validation tests for `connection_secrets_*.py`**
   - 30+ schema files with zero tests
   - Test required fields, secret masking, validation errors
   - Could be templated/parameterized since schemas share a common pattern
   - Estimated scope: 2-3 test functions per schema, ~90 total

### P2 — Structural Improvements

10. **Add `@pytest.mark.unit` / `@pytest.mark.integration` markers to all test files**
    - Enables running unit tests separately in CI (faster feedback loop)
    - 304 files currently lack markers

11. **Increase mocking in existing integration tests**
    - Extract testable business logic and add isolated unit tests
    - Focus on `tests/ops/service/` where only 24% of files use mocks

12. **Add unit tests for query config modules**
    - `bigquery_query_config.py`, `postgres_query_config.py`, etc.
    - Query building logic is pure/functional and highly unit-testable

13. **Consolidate test directory structure**
    - Service tests are split between `tests/service/`, `tests/ops/service/`, and `tests/api/`
    - Consider a consistent mapping: `src/fides/X/ → tests/X/`

### P3 — Nice to Have

14. **Add tests for utility modules** (`connection_util.py`, `fuzzy_search_utils.py`, `aws_util.py`, etc.)
15. **Add model-level tests** for `privacy_assessment.py`, `messaging_template.py`, `worker_task.py`
16. **Add coverage enforcement thresholds** in CI to prevent regression
17. **Set up coverage reporting** — the `[tool.coverage.run]` config exists but there's no evidence of coverage thresholds or CI enforcement
