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
│  Unwrapped at runtime, cached in memory.                     │
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
                     │   cached)         │
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
                   │ Storage: DB  │  │ Storage: AWS  │  │  Azure, ...) │
                   │ Crypto: local│  │ Crypto: KMS   │  │              │
                   │ AES-GCM      │  │ API calls     │  │              │
                   └──────────────┘  └───────────────┘  └──────────────┘
```

### Key Provider Abstraction

Each provider owns both the **crypto** (wrap/unwrap) and the **storage** (where the wrapped DEK persists):

| Provider            | Wrapped DEK storage                      | Wrap/unwrap mechanism                       | KEK location                                    |
| ------------------- | ---------------------------------------- | ------------------------------------------- | ----------------------------------------------- |
| `LocalKeyProvider`  | `encryption_keys` DB table               | In-process AES-256-GCM                      | Env var (`FIDES__SECURITY__KEY_ENCRYPTION_KEY`) |
| `AwsKmsKeyProvider` | AWS Secrets Manager (or Parameter Store) | AWS KMS API (`kms:Encrypt` / `kms:Decrypt`) | Inside AWS KMS (never leaves)                   |

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

`get_encryption_key()` is lazy and cached:

```python
_cached_dek: str | None = None

def get_encryption_key() -> str:
    global _cached_dek
    if _cached_dek is not None:
        return _cached_dek

    config = get_config()
    if not config.security.key_provider or config.security.key_provider == "none":
        _cached_dek = config.security.app_encryption_key
    else:
        provider = _build_key_provider(config.security)
        _cached_dek = provider.get_dek()

    return _cached_dek
```

This eliminates the import-time binding problem. The DEK is resolved on the first encrypt/decrypt operation — long after the app is fully started and the database is reachable.

---

## PR Breakdown

### PR 0a: Migrate `Organization` to standard encryption

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

---

### PR 0b: Migrate `UserRegistration` to standard encryption

**Goal:** Replace the `AesEngine` (AES-CBC) mechanism with `AesGcmEngine` (AES-GCM) on the `UserRegistration` model, eliminating the last non-standard encryption engine.

**Context:**

`UserRegistration` has 1 column (`user_email`) using `StringEncryptedType(AesEngine)` — AES-CBC instead of the AES-GCM used everywhere else.

**Migration strategy (expand-contract):**

Both `AesEngine` and `AesGcmEngine` use `app_encryption_key`, so no key change — only the cipher mode changes (CBC to GCM).

1. **Expand:** Add a new column `user_email_new` alongside the existing `user_email`
2. **Migrate:** For each row, decrypt `user_email` using `AesEngine`, re-encrypt using `AesGcmEngine`, write to `user_email_new`. Skip `NULL` values.
3. **Contract:** Drop `user_email`, rename `user_email_new` to `user_email`

**Risk considerations:**

- The `userregistration` table typically contains a single row, so the migration is trivial.
- `AesEngine` import can be removed from `registration.py` after this PR.

**Independent of PR 0a.** Can land before or after.

---

### PR 1: `encrypted_type()` factory + callable key (pure refactor)

**Goal:** Centralize all `StringEncryptedType` construction and switch from import-time key binding to a callable key. Zero behavior change.

Create a new `get_encryption_key()` function (initially just returns `CONFIG.security.app_encryption_key`) and an `encrypted_type()` factory that passes it as a callable to `StringEncryptedType`. Replace all 39 inline `StringEncryptedType(...)` calls across 18 model files with `encrypted_type(...)`. Update `optionally_encrypted_type()`, `_get_sqlalchemy_compatible_key()`, and `_make_encryptor()` to use `get_encryption_key()`.

Alembic migration files are frozen historical snapshots and are not modified.

**Testing:** All existing tests pass with zero config changes. Add unit test verifying `get_encryption_key()` returns `CONFIG.security.app_encryption_key` in legacy mode.

---

### PR 2: `KeyProvider` ABC + `LocalKeyProvider`

**Goal:** Introduce the provider abstraction and the local (in-process) implementation. New code only — nothing wired up yet.

Create a `KeyProvider` ABC with a `get_dek()` method, and a `LocalKeyProvider` implementation that reads the wrapped DEK from the `encryption_keys` DB table via raw SQL (not ORM) and decrypts it with AES-256-GCM using a KEK from config.

**No behavioral change.** Nothing calls these classes yet.

---

### PR 3: `AwsKmsKeyProvider` (optional, can be deferred)

**Goal:** Add the AWS KMS provider implementation.

Create an `AwsKmsKeyProvider` that fetches the wrapped DEK from Secrets Manager and calls `kms:Decrypt` to unwrap it. The KEK never leaves AWS. No new dependencies — `boto3` is already in Fides's dependency tree.

**Independent of PR 2.** Can land before or after. Can also be deferred to a later phase.

---

### PR 4: `encryption_keys` database table

**Goal:** Create the database table used by `LocalKeyProvider` for wrapped DEK storage.

**Table schema:**

```sql
CREATE TABLE encryption_keys (
    id          VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    key_id      VARCHAR NOT NULL UNIQUE,      -- version identifier (e.g. "v1")
    wrapped_dek TEXT NOT NULL,                 -- base64-encoded ciphertext
    provider    VARCHAR NOT NULL DEFAULT 'local',
    is_active   BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    rotated_at  TIMESTAMP WITH TIME ZONE
);

CREATE UNIQUE INDEX ix_encryption_keys_active
    ON encryption_keys (is_active) WHERE is_active = true;
```

The partial unique index on `is_active WHERE is_active = true` ensures at most one active key at any time.

**No behavioral change.** The table exists but nothing reads from or writes to it yet.

**Independent of PRs 2 and 3.**

---

### PR 5: New config fields

**Goal:** Add envelope encryption configuration to `SecuritySettings`. All fields are optional with backward-compatible defaults.

**New fields in `SecuritySettings`:**

| Field                            | Type  | Default  | Description                                              |
| -------------------------------- | ----- | -------- | -------------------------------------------------------- |
| `key_provider`                   | `str` | `"none"` | Provider type: `"none"` (legacy), `"local"`, `"aws_kms"` |
| `key_encryption_key`             | `str` | `""`     | KEK for local provider (32 chars)                        |
| `aws_kms_key_arn`                | `str` | `""`     | KMS key ARN for AWS KMS provider                         |
| `aws_kms_region`                 | `str` | `""`     | AWS region                                               |
| `aws_secrets_manager_secret_arn` | `str` | `""`     | Secrets Manager ARN for wrapped DEK storage              |

**Validation logic:**

- `key_provider = "none"`: require `app_encryption_key` (existing behavior)
- `key_provider = "local"`: require `key_encryption_key` (32 chars)
- `key_provider = "aws_kms"`: require `aws_kms_key_arn` and `aws_kms_region`

**Update to `check_required_webserver_config_values`:** `app_encryption_key` is no longer unconditionally required — it is only required when `key_provider = "none"`.

**No behavioral change.** The new settings exist but nothing reads them yet. Existing deployments have `key_provider = "none"` by default.

---

### PR 6: Wire `get_encryption_key()` to envelope mode

**Goal:** Connect the callable key resolver to the provider system. This is the PR that activates envelope encryption.

Add the envelope resolution path to `get_encryption_key()` and a `_build_key_provider()` factory:

**Updated `get_encryption_key()`:**

```python
_cached_dek: str | None = None

def get_encryption_key() -> str:
    global _cached_dek
    if _cached_dek is not None:
        return _cached_dek

    config = get_config()

    if config.security.key_provider == "none":
        # Legacy mode — direct key, no envelope
        _cached_dek = config.security.app_encryption_key
    else:
        # Envelope mode — delegate to provider
        provider = _build_key_provider(config.security)
        _cached_dek = provider.get_dek()

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
            secret_arn=security.aws_secrets_manager_secret_arn,
        )
    else:
        raise ValueError(f"Unknown key_provider: {security.key_provider}")
```

**Why this isn't breaking:** The branch is determined by `key_provider`. Existing deployments have `key_provider = "none"` (the default), so they always hit the legacy path. The envelope path only activates when an operator explicitly configures a provider _and_ has bootstrapped a wrapped DEK.

**Testing:**

- Unit test: legacy mode returns `app_encryption_key` directly
- Unit test: local provider mode reads from DB, unwraps, caches
- Integration test: write and read an encrypted column with envelope mode enabled
- Integration test: verify backward compat — existing config with only `app_encryption_key` works identically

**Depends on:** PR 1 (callable key), PR 2 or 3 (at least one provider), PR 4 (DB table, if testing local provider), PR 5 (config fields).

---

## PR Dependency Graph

```
PR 0a (migrate Organization)    PR 0b (migrate UserRegistration)
  │                                │
  └────────────┬───────────────────┘
               │
          PR 1 (factory refactor)
               │
               │       PR 2 (LocalKeyProvider)      PR 3 (AwsKmsKeyProvider)
               │           │                             │
               │       PR 4 (DB table)             (no DB needed)
               │           │                             │
               │       PR 5 (config fields)              │
               │           │                             │
               └───────────┴─────────────────────────────┘
                            │
                       PR 6 (wire it together)
```

- PRs 0a and 0b are independent of each other and can land in any order or in parallel.
- Both PRs 0a and 0b must land before PR 1 (PR 1 converts the migrated columns to use the factory).
- PRs 2, 3, 4, and 5 are independent of each other and can land in any order or in parallel.
- PR 1 must land before PR 6.
- All of PRs 2 (or 3), 4 (if using local), and 5 must land before PR 6.

---

## What This Enables

### KEK Rotation (immediate benefit)

With envelope encryption in place, the KEK can be rotated without touching any data:

- **Local provider:** Generate new KEK, re-wrap the DEK with the new KEK, update the `encryption_keys` row. Zero data re-encryption.
- **AWS KMS:** Use KMS automatic key rotation (built-in). No Fides changes needed.

### Per-domain DEKs (Phase 2)

The `get_encryption_key()` callable could accept a context parameter (table name, data domain) and return different DEKs for different data:

- Consent / user PII uses one DEK
- Secrets like API keys, passwords, etc. use a different DEK

Each DEK is independently wrapped and stored. Compromising one doesn't expose the others.

### DEK Rotation (Phase 3)

With key versioning in the `encryption_keys` table (or Secrets Manager versions):

- New writes use the new DEK
- Reads try the active DEK first, fall back to previous versions
- A background task lazily re-encrypts old rows on read (read-old/write-new pattern)
