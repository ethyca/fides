# Envelope Encryption: Implementation Plan

## Problem Statement

Fides currently uses a single `app_encryption_key` as both the data encryption key (DEK) and the only secret protecting all encrypted data. This key is:

- Bound at module import time into 35 `StringEncryptedType` column definitions across 16 model files
- Stored as a plaintext environment variable
- Impossible to rotate without re-encrypting every encrypted value in the database
- The same key for all data domains (secrets, PII, tokens, etc.)

We want to introduce **envelope encryption** — separating a Key Encryption Key (KEK) from the DEK — without re-encrypting any existing data and without any breaking changes to existing deployments.

## Design Constraints

1. **No data re-encryption.** The current `app_encryption_key` value becomes the DEK. All existing ciphertext in the database remains valid.
2. **No breaking changes.** Existing deployments with only `FIDES__SECURITY__APP_ENCRYPTION_KEY` set continue to work identically. Envelope encryption is opt-in.
3. **Incremental delivery.** Each PR is independently mergeable and safe to deploy.
4. **Pluggable key providers.** Support local (in-process AES-GCM) and external KMS (AWS KMS, etc.) from the start.

## Architecture

### Key Hierarchy

```
┌──────────────────────────────────────────────────────────────┐
│  KEK (Key Encryption Key)                                    │
│  ─────────────────────────                                   │
│  Owned by the operator. Lives in an env var (local provider) │
│  or never leaves the KMS (AWS KMS provider).                 │
│                                                              │
│  Wraps / unwraps the DEK.                                    │
└──────────────────────┬───────────────────────────────────────┘
                       │ wraps
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  DEK (Data Encryption Key)                                   │
│  ─────────────────────────                                   │
│  = the current app_encryption_key value                      │
│  Stored encrypted (wrapped) by the provider.                 │
│  Unwrapped at runtime, cached in memory with a TTL.          │
│                                                              │
│  Used by all StringEncryptedType columns, AES-GCM utils,     │
│  JWE tokens, etc. — the entire existing encryption surface.  │
└──────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
                     ┌──────────────────┐
                     │  get_encryption   │
                     │  _key()           │◄── called by StringEncryptedType
                     │  (callable, lazy, │    (on every encrypt/decrypt)
                     │   TTL-cached)     │
                     └────────┬─────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
     ┌─────────────────┐           ┌──────────────────────┐
     │  Legacy mode     │           │  Envelope mode        │
     │  (no KEK set)    │           │  (KEK configured)     │
     │                  │           │                       │
     │  Return          │           │  provider = build()   │
     │  CONFIG.security │           │  dek = provider       │
     │  .app_encryption │           │    .get_dek()         │
     │  _key            │           │                       │
     └─────────────────┘           └──────────┬────────────┘
                                              │
                          ┌───────────────────┼──────────────────┐
                          │                   │                  │
                          ▼                   ▼                  ▼
                   ┌──────────────┐  ┌───────────────┐  ┌──────────────┐
                   │ Local        │  │ AWS KMS       │  │ Future       │
                   │ KeyProvider  │  │ KeyProvider   │  │ providers    │
                   │              │  │               │  │ (Vault, GCP, │
                   │ Storage: DB  │  │ Storage: DB   │  │  Azure, ...) │
                   │ Crypto: local│  │ Crypto: KMS   │  │              │
                   │ AES-GCM      │  │ API calls     │  │              │
                   └──────────────┘  └───────────────┘  └──────────────┘
```

### Key Provider Abstraction

Each provider owns both the **crypto** (wrap/unwrap) and the **storage** (where the wrapped DEK persists):

| Provider            | Wrapped DEK storage      | Wrap/unwrap mechanism                       | KEK location                                    |
| ------------------- | ------------------------ | ------------------------------------------- | ----------------------------------------------- |
| `LocalKeyProvider`  | `encryption_keys` DB table | In-process AES-256-GCM                      | Env var (`FIDES__SECURITY__KEY_ENCRYPTION_KEY`) |
| `AwsKmsKeyProvider` | `encryption_keys` DB table | AWS KMS API (`kms:Encrypt` / `kms:Decrypt`) | Inside AWS KMS (never leaves the HSM)           |

The `KeyProvider` ABC:

```python
class KeyProvider(ABC):
    @abstractmethod
    def get_dek(self) -> str:
        """Retrieve and unwrap the DEK."""
        ...
```

### How the DEK Reaches SQLAlchemy Columns

Today, every encrypted column captures the key at import time:

```python
# Current — key is a string, bound at class definition
Column(StringEncryptedType(JSONTypeOverride, CONFIG.security.app_encryption_key, AesGcmEngine, "pkcs5"))
```

`sqlalchemy-utils` supports **callable keys** — if `key` is a callable, it is invoked on each encrypt/decrypt operation. We introduce a factory function and a lazy resolver:

```python
# New — key is a callable, resolved on first use
def encrypted_type(type_in: TypeEngine | None = None) -> StringEncryptedType:
    return StringEncryptedType(
        type_in=type_in or Text(),
        key=get_encryption_key,  # callable
        engine=AesGcmEngine,
        padding="pkcs5",
    )

# Model usage becomes:
Column(MutableDict.as_mutable(encrypted_type(JSONTypeOverride)))
```

`get_encryption_key()` is lazy and cached with a configurable TTL (default 1 hour):

```python
_cached_dek: str | None = None
_cached_at: float = 0.0
_DEK_CACHE_TTL_SECONDS: float = 3600  # 1 hour

def get_encryption_key() -> str:
    global _cached_dek, _cached_at
    now = time.monotonic()
    if _cached_dek is not None and (now - _cached_at) < _DEK_CACHE_TTL_SECONDS:
        return _cached_dek

    config = get_config()
    if not config.security.key_provider or config.security.key_provider == "none":
        _cached_dek = config.security.app_encryption_key
    else:
        provider = _build_key_provider(config.security)
        _cached_dek = provider.get_dek()

    _cached_at = now
    return _cached_dek
```

This eliminates the import-time binding problem. The DEK is resolved lazily on the first encrypt/decrypt operation — long after the app is fully started and the database is reachable. The TTL ensures that key rotations propagate without requiring a restart: after the cache expires, the next operation re-fetches and unwraps the DEK from the provider.

---

## PR Breakdown

### PR 1: Migrate `Organization` to standard encryption — ✅ Done

**Goal:** Replace the `PGEncryptedString` mechanism (PostgreSQL `pgcrypto`) with `StringEncryptedType(AesGcmEngine)` on the `Organization` model, unifying it with the rest of the codebase.

**Context:**

`Organization` (`ctl_organizations` table) has 3 columns (`controller`, `data_protection_officer`, `representative`) using `PGEncryptedString` — a custom `TypeDecorator` that delegates to PostgreSQL's `pgp_sym_encrypt`/`pgp_sym_decrypt` via the `pgcrypto` extension. These columns use a different key (`CONFIG.user.encryption_key`) and a different algorithm (PGP symmetric) than everything else.

**Migration strategy:**

Uses the expand-contract pattern so the old columns remain readable throughout the migration. No maintenance window required.

1. **Expand:** Add new `Text` columns alongside the existing `BYTEA` ones (`controller_new`, `data_protection_officer_new`, `representative_new`)
2. **Migrate:** For each row, decrypt old columns using `pgp_sym_decrypt(column, user_encryption_key)` via raw SQL, re-encrypt plaintext using `AesGcmEngine` with `app_encryption_key`, write to the new columns. Skip `NULL` values.
3. **Contract:** Drop the old `BYTEA` columns, rename the new columns to the original names (`controller_new` → `controller`, etc.)

At every point during the migration, the old columns remain intact. The running application reads from the old columns until the rename, which is instantaneous. If anything fails mid-migration, the new columns can be dropped and the migration retried.

**Risk considerations:**

- The `ctl_organizations` table is small (typically single-digit rows), so the data migration is fast.
- The `PGEncryptedString` class and the `pgcrypto` extension dependency can be removed after this migration (or left as dead code and cleaned up separately).
- After this PR, `CONFIG.user.encryption_key` is no longer used by any model. It can be deprecated in a follow-up.

**Note:** `UserRegistration` (which uses `AesEngine` / AES-CBC) does not need a separate migration — the model will be removed entirely once fideslog is removed.

---

### PR 2: `encrypted_type()` factory + callable key (pure refactor) — 🔧 In progress

**Goal:** Centralize all `StringEncryptedType` construction and switch from import-time key binding to a callable key. Zero behavior change.

Create a new `get_encryption_key()` function (initially just returns `CONFIG.security.app_encryption_key`) and an `encrypted_type()` factory that passes it as a callable to `StringEncryptedType`. Replace all inline `StringEncryptedType(...)` calls across model files with `encrypted_type(...)`. Update `optionally_encrypted_type()`, `_get_sqlalchemy_compatible_key()`, and `_make_encryptor()` to use `get_encryption_key()`.

Alembic migration files are frozen historical snapshots and are not modified.

**Testing:** All existing tests pass with zero config changes. Add unit test verifying `get_encryption_key()` returns `CONFIG.security.app_encryption_key` in legacy mode.

#### Non-column encryption paths

In addition to the `StringEncryptedType` columns, several non-column code paths reference `CONFIG.security.app_encryption_key` directly. This PR updates them to use `get_encryption_key()` so that every encryption path benefits from envelope encryption once it is wired up in PR 7.

| Path | File(s) | Current key source | Change |
|------|---------|--------------------|--------|
| **JWE / OAuth tokens** (create) | `fides: oauth_endpoints.py`, `user_endpoints.py` | `CONFIG.security.app_encryption_key` passed to `create_access_code_jwe()` | Replace with `get_encryption_key()` |
| **JWE / OAuth tokens** (verify) | `fides: oauth/utils.py` (5 call sites) | `CONFIG.security.app_encryption_key` passed to `extract_payload()` | Replace with `get_encryption_key()` |
| **OAuth state tokens** (Jira, Slack, OpenID) | `fidesplus: jira_oauth_service.py`, `slack.py`, `openid_providers.py` | `CONFIG.security.app_encryption_key` / `CONFIG.fides.security.app_encryption_key` passed to `generate_state_token()` / `validate_state_token()` | Replace with `get_encryption_key()` |
| **JWE token creation** (fidesplus) | `fidesplus: external_login.py`, `connections.py`, `openid_providers.py` | `config.security.app_encryption_key` passed to `create_access_code_jwe()` | Replace with `get_encryption_key()` |
| **Consent preferences encrypt/decrypt** | `fidesplus: preferences_util.py` (2 call sites) | `config.fides.security.app_encryption_key.encode()` used as raw AES-GCM key bytes | Replace with `get_encryption_key().encode()` |
| **AES-GCM encryption scheme** (fidesplus override) | `fidesplus: aes_gcm_overrides.py` | Validates key length against `config.fides.security.app_encryption_key` | Update `verify_app_encryption_key()` to use `get_encryption_key()` |
| **Chunked external storage** | `fides: aes_gcm_encryption_util.py` | Already uses `get_encryption_key()` | No change needed |
| **SQLAlchemy-Utils external storage** | `fides: aes_gcm_encryption_util.py` | Already uses `get_encryption_key()` | No change needed |
| **Privacy request result encryption** | `fides: tasks/encryption_utils.py` | Per-request key from Redis (not `app_encryption_key`) | No change needed — independent key path |
| **Database startup validation** | `fides: db/database.py` | Error message references `app_encryption_key` | Update error message only (cosmetic) |

**Note:** The `aes_gcm_encryption_scheme.py` module in fides uses a **different key derivation** (raw `.encode()` instead of SHA256) and is called with per-request keys from Redis, not `app_encryption_key`. This path is unaffected by envelope encryption.

---

### PR 3: `encryption_keys` database table — 📋 To do

**Goal:** Create the database table used by both `LocalKeyProvider` and `AwsKmsKeyProvider` for wrapped DEK storage.

**Table schema:**

```sql
CREATE TABLE encryption_keys (
    id          VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    wrapped_dek TEXT NOT NULL,                 -- base64-encoded ciphertext
    kek_id_hash      VARCHAR NOT NULL,             -- identifies the KEK used to wrap (see below)
    provider    VARCHAR NOT NULL DEFAULT 'local',
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
```

The `kek_id_hash` column identifies which KEK was used to wrap the DEK, allowing the startup logic to determine whether re-wrapping is needed without trial decryption:

- **Local provider:** `HMAC-SHA256(key=b"fides-kek-id", msg=kek)[:16]` — a truncated HMAC that uniquely identifies the KEK without leaking key material. The fixed salt `"fides-kek-id"` provides domain separation.
- **AWS KMS provider:** The KMS key ARN (e.g., `arn:aws:kms:us-east-1:123456789:key/abcd-...`), which is already a public identifier.

**No behavioral change.** The table exists but nothing reads from or writes to it yet.

---

### PR 4: New config fields — 📋 To do

**Goal:** Add envelope encryption configuration to `SecuritySettings`. All fields are optional with backward-compatible defaults.

**New fields in `SecuritySettings`:**

| Field                            | Type  | Default  | Description                                                              |
| -------------------------------- | ----- | -------- | ------------------------------------------------------------------------ |
| `key_provider`                   | `str` | `"none"` | Provider type: `"none"` (legacy), `"local"`, `"aws_kms"`                 |
| `key_encryption_key`             | `str` | `""`     | Current KEK for local provider (32 chars)                                |
| `key_encryption_key_previous`    | `str` | `""`     | Previous KEK, set during rotation (see KEK Rotation below)               |
| `aws_kms_key_arn`                | `str` | `""`     | ARN of the KMS key to use for wrapping/unwrapping (operator-provisioned) |
| `aws_kms_region`                 | `str` | `""`     | AWS region for the KMS key                                               |

**Validation logic:**

- `key_provider = "none"`: require `app_encryption_key` (existing behavior)
- `key_provider = "local"`: require `key_encryption_key` (32 chars); `key_encryption_key_previous` is optional
- `key_provider = "aws_kms"`: require `aws_kms_key_arn` and `aws_kms_region`

**Update to `check_required_webserver_config_values`:** `app_encryption_key` is no longer unconditionally required — it is only required when `key_provider = "none"`.

**No behavioral change.** The new settings exist but nothing reads them yet. Existing deployments have `key_provider = "none"` by default.

---

### PR 5: `KeyProvider` ABC + `LocalKeyProvider` — 📋 To do

**Goal:** Introduce the provider abstraction and the local (in-process) implementation. New code only — nothing wired up yet.

Create a `KeyProvider` ABC with a `get_dek()` method, and a `LocalKeyProvider` implementation that reads the wrapped DEK from the `encryption_keys` DB table via raw SQL (not ORM) and decrypts it with AES-256-GCM using a KEK from config.

**Bootstrap:** Handled automatically on startup (see PR 7). When `key_provider = "local"` and no row exists in `encryption_keys`, the startup task wraps the current `app_encryption_key` with the configured KEK and inserts the row. No CLI command needed.

**No behavioral change.** Nothing calls these classes yet.

---

### PR 6: `AwsKmsKeyProvider` (optional, can be deferred) — 📋 To do

**Goal:** Add the AWS KMS provider implementation.

Create an `AwsKmsKeyProvider` that reads the wrapped DEK from the `encryption_keys` DB table (the same table used by `LocalKeyProvider`) and calls `kms:Decrypt` to unwrap it. The KEK never leaves the KMS HSM. No new dependencies — `boto3` is already in Fides's dependency tree.

**How it works:**

Both providers share the `encryption_keys` table for wrapped DEK storage. The only difference is who performs the wrap/unwrap:

- **`LocalKeyProvider`:** AES-256-GCM in-process using a KEK from an env var.
- **`AwsKmsKeyProvider`:** `kms:Decrypt(CiphertextBlob=wrapped_dek)` via boto3. KMS identifies the correct key and backing key version from metadata embedded in the ciphertext blob — no key ARN is needed at decrypt time, though we pass it for validation.

**Bootstrap:** Handled automatically on startup (see PR 7). When `key_provider = "aws_kms"` and no row exists in `encryption_keys`, the startup task calls `kms:Encrypt(KeyId=aws_kms_key_arn, Plaintext=app_encryption_key)` and stores the resulting `CiphertextBlob` in the `encryption_keys` table. After the first successful startup, `app_encryption_key` can be removed from the environment.

**Required IAM permissions:** `kms:Encrypt` (bootstrap only) and `kms:Decrypt` (runtime) on the configured KMS key ARN.

**Independent of PR 5.** Can land before or after. Can also be deferred to a later phase.

---

### PR 7: Wire `get_encryption_key()` to envelope mode — 📋 To do

**Goal:** Connect the callable key resolver to the provider system. This is the PR that activates envelope encryption.

#### Startup task

On application startup, before any request is served, a startup task runs the envelope encryption initialization. This handles three scenarios: first-time bootstrap, normal operation, and KEK rotation.

```
startup_envelope_encryption():
  config = get_config()
  if config.security.key_provider == "none":
      return  # legacy mode, nothing to do

  provider = _build_key_provider(config.security)
  row = read active row from encryption_keys table

  if row is None:
      # --- First-time bootstrap ---
      # Wrap the existing app_encryption_key with the configured KEK
      # and insert the first row. After this deploy succeeds,
      # app_encryption_key can be removed from the environment.
      wrapped_blob = provider.wrap(config.security.app_encryption_key)
      insert row: wrapped_dek=wrapped_blob, kek_id_hash=provider.kek_id_hash(), provider=...
      return

  if row.kek_id_hash == provider.kek_id_hash():
      # --- Normal operation ---
      # KEK hasn't changed, nothing to do.
      return

  # --- KEK rotation detected ---
  # The row was wrapped with a different KEK than the current one.
  # Cache the DEK immediately (using the old KEK) so no request
  # fails during the re-wrap.
  old_kek = config.security.key_encryption_key_previous  # local provider
  dek = provider.unwrap_with(row.wrapped_dek, old_kek)
  _cache_dek(dek)  # warm the cache before re-wrapping

  # Re-wrap with the current KEK and update the row.
  new_blob = provider.wrap(dek)
  update row: wrapped_dek=new_blob, kek_id_hash=provider.kek_id_hash()
```

For the AWS KMS provider, KEK rotation is handled transparently by KMS (see KEK Rotation below), so the rotation branch only applies to the local provider.

#### Updated `get_encryption_key()`

```python
_cached_dek: str | None = None
_cached_at: float = 0.0
_DEK_CACHE_TTL_SECONDS: float = 3600  # 1 hour

def get_encryption_key() -> str:
    global _cached_dek, _cached_at
    now = time.monotonic()
    if _cached_dek is not None and (now - _cached_at) < _DEK_CACHE_TTL_SECONDS:
        return _cached_dek

    config = get_config()

    if config.security.key_provider == "none":
        # Legacy mode — direct key, no envelope
        _cached_dek = config.security.app_encryption_key
    else:
        # Envelope mode — delegate to provider
        provider = _build_key_provider(config.security)
        _cached_dek = provider.get_dek()

    _cached_at = now
    return _cached_dek


def _build_key_provider(security: SecuritySettings) -> KeyProvider:
    if security.key_provider == "local":
        return LocalKeyProvider(
            kek=security.key_encryption_key,
            db_url=get_config().database.sync_database_uri,
        )
    elif security.key_provider == "aws_kms":
        return AwsKmsKeyProvider(
            kms_key_arn=security.aws_kms_key_arn,
            region=security.aws_kms_region,
        )
    else:
        raise ValueError(f"Unknown key_provider: {security.key_provider}")
```

The TTL-based cache ensures that after a DEK rotation (Phase 3), all pods converge to the new DEK within the TTL window without requiring restarts.

**Why this isn't breaking:** The branch is determined by `key_provider`. Existing deployments have `key_provider = "none"` (the default), so they always hit the legacy path. The envelope path only activates when an operator explicitly configures a provider.

**Testing:**

- Unit test: legacy mode returns `app_encryption_key` directly
- Unit test: local provider mode reads from DB, unwraps, caches
- Unit test: TTL expiry triggers re-fetch
- Unit test: bootstrap creates row when `encryption_keys` is empty
- Unit test: KEK rotation detects `kek_id_hash` mismatch, re-wraps, and updates row
- Integration test: write and read an encrypted column with envelope mode enabled
- Integration test: verify backward compat — existing config with only `app_encryption_key` works identically

**Depends on:** PR 2 (callable key), PR 3 (DB table), PR 4 (config fields), PR 5 or 6 (at least one provider).

---

## PR Dependency Graph

```
          PR 1 (migrate Organization)
               │
          PR 2 (factory refactor)
               │
               │     PR 3 (DB table)     PR 4 (config fields)
               │         │                    │
               │     PR 5 (LocalKeyProvider)  PR 6 (AwsKmsKeyProvider)
               │         │                    │
               └─────────┴────────────────────┘
                            │
                       PR 7 (wire it together)
```

- PR 1 must land before PR 2 (PR 2 converts the migrated columns to use the factory).
- PRs 3 and 4 are independent of each other and of PR 2. They can land in any order or in parallel.
- PRs 5 and 6 are independent of each other. Both depend on PR 3 (DB table). PR 6 is optional and can be deferred.
- PR 2 must land before PR 7.
- PRs 3, 4, and 5 (or 6) must all land before PR 7.

---

## What This Enables

### KEK Rotation (immediate benefit)

With envelope encryption in place, the KEK can be rotated without re-encrypting any application data — only the wrapped DEK blob in the `encryption_keys` table needs to be updated.

**Local provider:**

KEK rotation is config-driven and handled automatically by the startup task:

1. The operator sets `key_encryption_key` to the new KEK and `key_encryption_key_previous` to the old KEK.
2. On startup, the startup task compares `kek_id_hash` in the DB row against `HMAC(current KEK)`. If they don't match, it unwraps the DEK using `key_encryption_key_previous`, caches the plaintext DEK immediately, re-wraps with the new KEK, and updates the row.
3. On subsequent deploys, the operator removes `key_encryption_key_previous`. The startup task sees `kek_id_hash` matches and skips rotation.

Zero downtime. The DEK is cached before re-wrapping, so no request can fail during the transition. In a multi-pod deployment, each pod performs the same re-wrap idempotently — the result is deterministic since the same DEK is wrapped with the same new KEK.

**AWS KMS provider:**

KMS automatic key rotation generates new backing key material behind the same Key ARN. Existing wrapped DEK blobs remain decryptable because KMS embeds backing key version metadata in every ciphertext — `kms:Decrypt` automatically selects the correct version. No re-wrapping, restart, or Fides changes needed.

To migrate to a **different KMS key ARN** entirely (e.g., cross-account move), the operator would need to manually unwrap with the old key and re-wrap with the new one. This can be supported via an admin API endpoint in a follow-up.

### Per-domain DEKs (Phase 2)

The `get_encryption_key()` callable could accept a context parameter (table name, data domain) and return different DEKs for different data:

- Consent / user PII uses one DEK
- Secrets like API keys, passwords, etc. use a different DEK

Each DEK is independently wrapped and stored. Compromising one doesn't expose the others.

### DEK Rotation (Phase 3)

With key versioning in the `encryption_keys` table:

- New writes use the new DEK
- Reads try the active DEK first, fall back to previous versions
- A background task lazily re-encrypts old rows on read (read-old/write-new pattern)
- The TTL-based cache in `get_encryption_key()` ensures all pods converge to the new DEK without restarts
