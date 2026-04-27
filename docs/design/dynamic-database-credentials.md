# Dynamic Database Credentials via AWS Secrets Manager

## Problem

Fides loads database credentials once at startup (from environment variables or `fides.toml`) and bakes them into SQLAlchemy engine connection pools. Rotating credentials requires changing the env var and restarting all pods, causing downtime.

Customers using AWS Secrets Manager for credential rotation need Fides to pick up new credentials dynamically, with minimal or no downtime.

## Goals

- Fides can pull its application database credentials from AWS Secrets Manager at runtime.
- Credential rotation is handled transparently — no pod restarts required.
- Auth failures during rotation trigger an immediate credential refresh and retry.
- Existing deployments using static credentials (env vars / TOML) are unaffected.

## Non-Goals

- Rotating credentials for customer-configured connectors (these use `ConnectionConfig`, a separate system).
- Supporting secret providers other than AWS Secrets Manager (though the design should make this easy to add later).
- Upgrading SQLAlchemy to 2.0 (planned separately).

---

## Design

### 1. Secret Provider Abstraction

The secret provider is a general-purpose abstraction for fetching secrets from external stores. It is not specific to database credentials — any part of Fides that needs a dynamically-resolved secret can use it.

```
SecretProvider (ABC)
├── StaticSecretProvider              — returns a fixed value (current behavior, wraps config values)
└── AWSSecretsManagerProvider         — fetches from Secrets Manager with local caching
```

The provider interface exposes two operations:

- **`get_secret(secret_id)`** — returns the current value of a named secret. In the normal case this returns a cached value with no network call.
- **`invalidate(secret_id)`** — marks a specific cached secret as stale, forcing the next `get_secret()` call to fetch a fresh value from the upstream source.

A secret value is returned as a `SecretValue` wrapper around a dict (matching the JSON structure stored in Secrets Manager), so a single secret can contain multiple fields (e.g., `{"username": "...", "password": "..."}`). The caller accesses fields via subscript (`secret["username"]`). The `SecretValue` class overrides `__repr__` and `__str__` to return `"<redacted>"`, preventing accidental credential leakage in logs, tracebacks, or debug output. The raw dict is accessible internally but never exposed through string coercion.

**Database credentials as a consumer:**

The database engine layer is the first consumer of this abstraction. It calls `provider.get_secret(secret_id)` to retrieve the current username and password when opening connections. But the same provider instance can serve other consumers in the future (e.g., Redis credentials, encryption keys, external API tokens) without any changes to the provider itself.

### 2. AWS Secrets Manager Provider

The `AWSSecretsManagerProvider` wraps a `boto3` Secrets Manager client and maintains a local cache keyed by secret ID, with a configurable TTL (default: 5 minutes).

**Cache refresh logic:**

- `get_secret(secret_id)` checks whether the cached value for that secret ID is within TTL. If yes, returns it. If expired, attempts to fetch from Secrets Manager and updates the cache. If the fetch fails (network error, SM outage, rate limiting), the provider falls back to the last-known-good value and logs a warning rather than raising — this "stale-while-revalidate" behavior keeps connections alive during transient Secrets Manager unavailability. A separate `cache_stale_ttl_seconds` (default: 1800) controls how long stale credentials are served; once both the primary TTL and the stale TTL have expired, `get_secret()` raises to force a hard failure.
- `invalidate(secret_id)` resets the cache timestamp for that secret ID, forcing the next call to fetch regardless of TTL. This is used by the retry-on-auth-failure path (see section 4).

**Thread safety:**

Multiple threads may hit an auth failure simultaneously during credential rotation. A per-secret lock with a timestamp check ensures only one thread per process actually calls Secrets Manager — subsequent threads see the already-refreshed cache. This is standard thundering-herd protection.

Each pod/worker process runs its own provider instance. There is no cross-pod coordination; each independently fetches from Secrets Manager on rotation (typically a handful of API calls total, well within rate limits).

**Configuration:**

New top-level config section (not nested under `database`, since the provider is general-purpose):

- `secrets.provider`: `"static"` (default) or `"aws_secrets_manager"`
- `secrets.aws_secrets_manager.region`: AWS region
- `secrets.aws_secrets_manager.cache_ttl_seconds`: TTL for cached values (default: 300)
- `secrets.aws_secrets_manager.cache_stale_ttl_seconds`: grace period for serving last-known-good credentials when Secrets Manager is unreachable (default: 1800)
- `secrets.aws_secrets_manager.endpoint_url`: optional custom endpoint (e.g., LocalStack for local dev/CI)

**AWS authentication:** The provider uses the standard boto3 credential chain — IAM role on the pod (recommended for EKS/EC2), environment variables (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`), or any other mechanism boto3 supports. The IAM principal must have `secretsmanager:GetSecretValue` (and `secretsmanager:DescribeSecret` if version-stage filtering is needed) on the target secret ARN(s). The provider always fetches the `AWSCURRENT` staging label.

Database-specific settings on `DatabaseSettings` reference which secret to use:

- `database.credential_secret_id`: the Secrets Manager secret name/ARN containing the DB credentials. When `secrets.provider` is `"static"`, this is ignored and credentials come from `user`/`password` as today.
- `database.readonly_credential_secret_id`: the secret for read-only replica credentials. Follows the same fallback logic as existing readonly fields: if not set but `readonly_server` is configured, falls back to `credential_secret_id`. If neither is set, falls back to static `readonly_user`/`readonly_password` (which themselves fall back to `user`/`password`).

When `secrets.provider` is `"static"`, behavior is identical to today. The provider is instantiated once during config construction and is available to any subsystem that needs it.

### 3. Engine Integration

Fides creates 6 application database engines across 3 files:

| Engine | File | Driver | Pattern |
|---|---|---|---|
| Sync API engine (`_engine`) | `session_management.py` | psycopg2 | Lazy singleton |
| Sync readonly engine (`_readonly_engine`) | `session_management.py` | psycopg2 | Lazy singleton |
| Celery task engine (`_task_engine`) | `tasks/__init__.py` | psycopg2 | Lazy singleton per worker |
| Async API engine (`async_engine`) | `ctl_session.py` | asyncpg | Module-level singleton |
| Async readonly engine (`readonly_async_engine`) | `ctl_session.py` | asyncpg | Module-level singleton |
| Sync test engine (`sync_engine`) | `ctl_session.py` | asyncpg | Module-level singleton |

All engines use the **`creator` pattern**: instead of passing a connection URI to `create_engine` / `create_async_engine`, we pass a `creator` callable that opens a connection using credentials from the provider. The engine still receives a minimal URI for dialect selection (e.g., `postgresql+psycopg2://`), but all actual connection parameters come from the creator.

**Sync engines (psycopg2):**

The `creator` callable calls `psycopg2.connect()` with credentials from `provider.get_secret()`. This is a fully supported public API in SQLAlchemy 1.4. The creator is wired in through `get_db_engine()` in `session.py`, which already serves as the factory for all sync engines.

**Async engines (asyncpg):**

SQLAlchemy 1.4 does not expose `async_creator`. The async engine's pool manages connections through an internal greenlet bridge that makes async `asyncpg.connect()` calls appear synchronous. We use this same greenlet mechanism inside our `creator` to call `asyncpg.connect()` with fresh credentials.

This depends on a SQLAlchemy internal (`greenlet_spawn`), which is acceptable because:

- SQLAlchemy is hard-pinned to `1.4.27` — the internal cannot change underneath us.
- The planned SQLAlchemy 2.0 upgrade will replace this with the public `async_creator` API.
- The code should include a clear TODO and comments explaining this constraint.

The module-level engines in `ctl_session.py` need to be refactored into lazy factories (similar to how `session_management.py` already works) so the `creator` can be injected at construction time.

### 4. Automatic Retry on Auth Failure

When credentials are rotated, existing pooled connections may still be valid (if the DB/proxy accepts both old and new), but new connections will fail if the old password has been invalidated. The retry logic lives inside the `creator` callable:

1. Fetch credentials from the provider (cached, fast).
2. Attempt to open a connection.
3. If the connection fails with an authentication error:
   a. Call `provider.invalidate()` to bust the cache.
   b. Wait briefly (1–2 seconds) to allow for propagation — during rotation, there is a short window where the `AWSPENDING` → `AWSCURRENT` swap may not have completed yet.
   c. Fetch credentials again (forces a Secrets Manager call).
   d. Retry the connection once with the new credentials.
4. If the retry also fails, raise the error normally (the credentials are genuinely wrong, not a rotation issue).

This means the first connection attempt after rotation absorbs a single failure and Secrets Manager round-trip. All subsequent connections from other threads use the already-refreshed cache (see thundering-herd protection above).

**Circuit breaker:** If a refresh yields credentials that also fail authentication, the provider records a "last failed fetch" timestamp. Subsequent `invalidate()` calls within a configurable cooldown window (default: 30 seconds) are no-ops — the provider returns the cached value without hitting Secrets Manager again. This prevents retry amplification when credentials are genuinely wrong (misconfigured secret, bad rotation lambda) rather than mid-rotation. The circuit resets automatically after the cooldown expires or when the TTL-based refresh succeeds.

**Error detection:**

- psycopg2: `OperationalError` with `exc.pgcode == "28P01"` (SQLSTATE `invalid_password`). This is locale-independent and version-stable, unlike string matching on the error message.
- asyncpg: `InvalidPasswordError` (already maps to SQLSTATE `28P01` internally). Note: Aurora/RDS can sometimes emit SQLSTATE `28000` (`InvalidAuthorizationSpecificationError`) instead of `28P01` during rotation — the implementation should catch both to be safe.

The retry happens at the connection level, invisible to application code. Combined with the existing `pool_pre_ping=True` setting (which evicts dead connections before use), this provides self-healing behavior across the full rotation window.

---

## What Stays the Same

- `DatabaseSettings` continues to hold all the same fields (server, port, db, params, pool sizes, keepalives, SSL, etc.). The only addition is `credential_secret_id`. A new top-level `secrets` config section is added for provider configuration.
- The `StaticSecretProvider` returns values from config directly, so existing deployments with env vars or TOML are completely unaffected.
- Engine pool configuration, pool sizes, and other `create_engine` keyword options remain unchanged. However, the `creator` callable is responsible for explicitly forwarding all connection-level parameters that currently live in `connect_args` (keepalive settings, `sslmode`, `sslcert`, `sslkey`, `sslrootcert`, JSON type registration, etc.) into the `psycopg2.connect()` / `asyncpg.connect()` call — these are **not** automatically passed through when using the `creator` pattern. The implementation must merge these from `DatabaseSettings` to avoid silent regressions (e.g., SSL enforcement being dropped).
- Alembic migrations are short-lived and create their own engine. They can simply fetch current credentials from the provider at migration start.

## Future Work

- **SQLAlchemy 2.0 upgrade:** Replace the greenlet-based async creator with the public `async_creator` API. This is a targeted change in `ctl_session.py` engine construction only.
- **Additional providers:** The `SecretProvider` interface makes it straightforward to add providers for other secret stores (Vault, GCP Secret Manager, Azure Key Vault) without changing any consumer logic.
- **Additional consumers:** Other subsystems that use static credentials today (Redis, external API keys, encryption keys) can adopt the same provider with no changes to the provider layer — just call `get_secret()` with the appropriate secret ID.
- **RDS IAM auth:** A future provider could use `boto3.generate_db_auth_token()` instead of Secrets Manager, eliminating stored credentials entirely for RDS deployments.
