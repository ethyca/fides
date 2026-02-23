# `src/fides/` Directory Structure

```
src/fides/
├── api/
│   ├── models/
│   ├── schemas/
│   ├── v1/
│   │   └── endpoints/
├── cli/
├── common/
│   ├── credentials.py
│   ├── scope_registry.py
│   ├── urn_registry.py
│   ├── utils.py
│   └── session/
│       └── session_management.py
├── config/
├── connectors/
│   ├── bigquery/
│   ...
│   ├── saas/
│   │   └── strategies/
│   │       ├── authentication/
│   │       ├── pagination/
│   │       └── processors/
│   ├── scylla/
│   ├── shared/
│   ├── snowflake/
│   ├── timescale/
│   ├── utils/
│   └── website/
└── service/
    ├── attachment/
    ├── connection/
    ├── dataset/
    ├── event_audit/
    ├── messaging/
    ├── privacy_request/
    │   ├── dsr_package/
    │   │   ├── assets/
    │   │   └── templates/
    │   ├── masking/
    │   │   └── strategy/
    ├── storage/
    │   ├── providers/
    ├── system/
    ├── taxonomy/
    └── user/
```

## `api/`

```
api/
├── models/
├── schemas/
└── v1/
    └── endpoints/
```

The application layer. Houses the FastAPI HTTP surface and data definitions.

- **`models/`** — SQLAlchemy ORM models defining all database tables: systems, privacy requests, connection configs, policies, users, audit logs, privacy notices/preferences, and more (~53 modules).
- **`schemas/`** — Pydantic request/response schemas for API validation and serialization. Organized by domain (privacy, users, policies, connections, etc.).
- **`v1/endpoints/`** — FastAPI route handlers. Thin HTTP entry points that parse requests, delegate to services, and translate exceptions to HTTP responses (~35 endpoint modules).

## `cli/`

```
cli/
├── commands/
├── connectors/
└── core/
```

Command-line interface for local and server operations. Provides commands for deploying, scanning systems, generating/annotating datasets, pushing/pulling configurations, managing users, running database migrations, and interacting with connectors (Okta, BigQuery, AWS).

## `common/`

```
common/
├── credentials.py
├── scope_registry.py
├── urn_registry.py
├── utils.py
└── session/
    └── session_management.py
```

Low-level shared utilities with no internal Fides imports (only third-party dependencies). Safe to import from anywhere without circular dependency risk.

- **`utils.py`** — General helpers: version cleaning, JSON handling, SQLAlchemy utilities, HTTP requests.
- **`credentials.py`** — Credential management for external service authentication.
- **`urn_registry.py`** — URN registry for resource identification.
- **`scope_registry.py`** — Scope registry for permission definitions.
- **`session/session_management.py`** — Database session lifecycle management (creation, scoping, teardown).

## `config/`

```
config/
└── schemas/
```

Centralized configuration via Pydantic settings. `FidesConfig` composes subsections for database, Redis, Celery, security, logging, notifications, consent, admin UI, and more. Supports TOML files (`fides.toml`) and environment variable overrides (`FIDES__*`).

## `connectors/`

```
connectors/
├── bigquery/
...
├── saas/
│   └── strategies/
│       ├── authentication/
│       ├── pagination/
│       └── processors/
├── scylla/
├── shared/
├── snowflake/
├── timescale/
├── utils/
└── website/
```

Data source integrations. All connectors implement `BaseConnector` and support access, erasure, and consent operations.

- **Database connectors**: Postgres, MySQL, MariaDB, MongoDB, DynamoDB, Scylla, BigQuery, Snowflake, Redshift, MSSQL, Timescale, RDS, Google Cloud SQL.
- **`saas/`** — Generic SaaS API connector with pluggable strategies for authentication (OAuth2, API key, bearer token, basic auth), pagination (offset, cursor, link-based), and post-processing (filtering, unwrapping, extraction).
- **Other**: S3, HTTP, Fides-to-Fides, manual/webhook, Okta, DataHub, email (consent/erasure), website scanning.
- **`shared/`** — Reusable query builders (SQL dialects). **`utils/`** — Rate limiting.

## `service/`

```
service/
├── attachment/
├── connection/
├── dataset/
├── event_audit/
├── messaging/
├── privacy_request/
│   ├── dsr_package/
│   │   ├── assets/
│   │   └── templates/
│   ├── masking/
│   │   └── strategy/
├── storage/
│   ├── providers/
├── system/
├── taxonomy/
└── user/
```

Business logic layer for major workflows, organized by domain. Each top-level directory represents a domain service. Service packages should be self-contained: alongside the core `service.py`, each domain directory should also house its own `repository.py` (data access), `entities.py` (domain dataclasses), and `exceptions.py` (domain-specific errors). Complex domains like `privacy_request/` additionally contain all related sub-domains (masking, DSR package generation, etc.) within their own directory rather than scattering them across the codebase.
