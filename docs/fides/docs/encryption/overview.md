# Encryption in Fides: Current State Overview

This document describes the encryption mechanisms currently used across the Fides codebase, including the algorithms, key management, encrypted data inventory, and known limitations.

---

## Encryption Algorithms

Fides uses several encryption approaches depending on the context:

| Mechanism | Algorithm | Library | Usage |
|---|---|---|---|
| **StringEncryptedType** | AES-256-GCM | `sqlalchemy-utils` | Column-level database encryption (primary) |
| **AES-GCM scheme** | AES-256-GCM | `cryptography` | Privacy request result encryption, large data encryption |
| **JWE** | AES-256-GCM | `python-jose` | OAuth tokens, authentication tokens |
| **PGEncryptedString** | PGP symmetric | PostgreSQL `pgcrypto` | Organization model fields |
| **AesEngine** | AES-CBC | `sqlalchemy-utils` | Legacy (UserRegistration only) |
| **HMAC** | SHA-256 / SHA-512 | `cryptography` | Data masking (one-way, not encryption) |
| **Bcrypt** | Bcrypt | `bcrypt` | Password hashing (one-way) |

---

## Key Management

### `app_encryption_key` (Primary)

- **Config path:** `CONFIG.security.app_encryption_key`
- **Environment variable:** `FIDES__SECURITY__APP_ENCRYPTION_KEY`
- **Constraints:** Must be exactly 32 characters (validated at startup)
- **Used by:** Nearly all encryption — `StringEncryptedType` columns, AES-GCM scheme, JWE tokens

When used with `sqlalchemy-utils`, the raw key string is passed directly to the `AesGcmEngine`, which internally derives a 32-byte key via `SHA256(key)`. The `aes_gcm_encryption_util.py` module replicates this derivation in `_get_sqlalchemy_compatible_key()` to maintain compatibility when encrypting/decrypting outside of SQLAlchemy.

When used with the `aes_gcm_encryption_scheme.py` module (privacy request results), the key is encoded directly to bytes — **no SHA256 derivation** — meaning the same `app_encryption_key` value produces different ciphertext depending on the code path.

### `user.encryption_key` (PostgreSQL pgcrypto)

- **Config path:** `CONFIG.user.encryption_key`
- **Used by:** `PGEncryptedString` TypeDecorator (Organization model only)
- **Mechanism:** Passed as the passphrase to PostgreSQL's `pgp_sym_encrypt` / `pgp_sym_decrypt` functions

### Per-request encryption keys (Privacy request results)

- **Storage:** Redis cache, keyed by `privacy_request_id`
- **Lifecycle:** Cached when a privacy request begins; used to encrypt access request results returned to the data subject
- **Key length:** 16 bytes (validated by `aes_encryption_key_length` config)
- **Nonce:** Random 12 bytes generated per encryption, prepended to the ciphertext

---

## Encrypted Data Inventory

### Column-Level Encryption via `StringEncryptedType(AesGcmEngine)`

This is the most widely used mechanism. SQLAlchemy-Utils transparently encrypts/decrypts column values at the ORM layer. The ciphertext is stored as the column value in PostgreSQL (typically `Text` or `BYTEA`).

| Model | Columns | Underlying Type |
|---|---|---|
| `ConnectionConfig` | `secrets` | `JSONTypeOverride` |
| `StorageConfig` | `secrets` | `JSONTypeOverride` |
| `MessagingConfig` | `secrets` | `JSONTypeOverride` |
| `ApplicationConfig` | `api_set`, `config_set` | `JSONTypeOverride` |
| `PrivacyRequest` | `_filtered_final_upload`, `access_result_urls` | `JSONTypeOverride` |
| `CustomPrivacyRequestField` | `encrypted_value` | `JSONTypeOverride` |
| `ProvidedIdentity` | `encrypted_value` | `JSONTypeOverride` |
| `RequestTask` | `_access_data`, `_data_for_erasures` | `JSONTypeOverride` |
| `SubRequest` | `param_values`, `_access_data` | `JSONTypeOverride` |
| `PrivacyPreferenceHistory` | `secondary_user_ids` | `JSONTypeOverride` |
| `ConsentIdentitiesMixin` | `email`, `fides_user_device`, `phone_number`, `external_id` | `String` |
| `LastServedNotice` | `email`, `fides_user_device`, `phone_number` | `String` |
| `ConsentReportingMixinV2` | `anonymized_ip_address`, `user_agent` | `String` |
| `FidesUser` | `totp_secret` | `String` |
| `OpenIDProvider` | `client_id`, `client_secret` | `String` |
| `OAuthConfig` | `client_secret` | `String` |
| `ChatConfig` | `client_secret`, `access_token`, `signing_secret` | `String` |
| `MaskingSecret` | `secret` | `JSONTypeOverride` |
| `IdentitySalt` | `encrypted_value` | `JSONTypeOverride` |
| `Rule` | `masking_strategy` | `JSONTypeOverride` |

### Column-Level Encryption via `StringEncryptedType(AesEngine)`

| Model | Columns | Notes |
|---|---|---|
| `UserRegistration` | `user_email` | Legacy — uses AES-CBC instead of AES-GCM |

### Conditional Encryption via `optionally_encrypted_type()`

| Model | Columns | Config Flag |
|---|---|---|
| `PrivacyPreferences` (v3) | `record_data` | `CONFIG.consent.consent_v3_encryption_enabled` |

When the flag is `False`, the column stores plaintext. An `is_encrypted` boolean column on the model tracks whether the value was encrypted. Defined in `src/fides/api/db/util.py`.

### PostgreSQL pgcrypto Encryption via `PGEncryptedString`

| Model | Columns |
|---|---|
| `Organization` | `controller`, `data_protection_officer`, `representative` |

Encryption/decryption happens at the database layer using `pgp_sym_encrypt` / `pgp_sym_decrypt` SQL functions, not at the application layer.

### Application-Layer Encryption (Non-Column)

| Context | Module | Details |
|---|---|---|
| Privacy request results | `api/tasks/encryption_utils.py` | Per-request key from Redis; AES-GCM via `aes_gcm_encryption_scheme`; nonce prepended to ciphertext |
| Large data external storage | `api/util/encryption/aes_gcm_encryption_util.py` | Chunked AES-GCM encryption for data stored in S3; uses SHA256-derived key for SQLAlchemy-Utils compatibility |
| OAuth / auth tokens | `api/oauth/jwt.py` | JWE with AES-256-GCM via `python-jose`; uses `app_encryption_key` |

### Descriptor-Based External Storage with Encryption

The `EncryptedLargeDataDescriptor` (`api/models/field_types/encrypted_large_data.py`) provides a transparent fallback for columns whose data exceeds a size threshold. When data is too large for the database column, it is encrypted and stored externally (e.g., S3), and the column stores a JSON metadata pointer instead. Used by:

- `PrivacyRequest.filtered_final_upload`
- `RequestTask.access_data`
- `RequestTask.data_for_erasures`

---

## How `StringEncryptedType` Works Under the Hood

1. **Encrypt (on write):** `AesGcmEngine.encrypt(plaintext)` is called by SQLAlchemy-Utils before the value is persisted. Internally:
   - The engine derives a 32-byte key via `SHA256(app_encryption_key)`
   - Generates a random 12-byte nonce (IV)
   - Encrypts with AES-256-GCM, producing ciphertext + 16-byte authentication tag
   - Packs as: `base64(nonce + tag + ciphertext)`
   - The base64 string is stored in the database column

2. **Decrypt (on read):** `AesGcmEngine.decrypt(stored_value)` is called transparently when accessing the ORM attribute. It reverses the process.

3. **Key binding:** The key is captured at **model class definition time** (module import), not at query time. If `app_encryption_key` changes, existing encrypted data becomes unreadable.

---

## Configuration Reference

All encryption-relevant settings live in `SecuritySettings` (`src/fides/config/security_settings.py`):

| Setting | Default | Description |
|---|---|---|
| `app_encryption_key` | `""` (empty) | Primary 32-character encryption key |
| `aes_encryption_key_length` | `16` | Expected byte-length for per-request encryption keys |
| `aes_gcm_nonce_length` | `12` | Nonce length in bytes for AES-GCM |
| `encoding` | `UTF-8` | Text encoding used throughout encryption |

Additionally, `CONFIG.user.encryption_key` (from `UserSettings`) is used exclusively for `PGEncryptedString`.

---

## Key Observations and Limitations

### Single key for all data

All `StringEncryptedType` columns and most application-layer encryption share the same `app_encryption_key`. Rotating this key requires re-encrypting every encrypted column across all tables simultaneously — there is no built-in key rotation mechanism.

### Key is bound at import time

`StringEncryptedType` columns capture the encryption key when the Python module defining the model is first imported. The key is effectively a module-level constant. This means:

- No runtime key switching
- No per-tenant or per-record key differentiation
- Key changes require application restart **and** full data re-encryption

### No key versioning

There is no metadata stored alongside ciphertext to indicate which key (or key version) was used to encrypt a value. If the key changes, there is no way to distinguish old-key ciphertext from new-key ciphertext without attempting decryption.

### Two distinct key derivation paths

The same `app_encryption_key` is used in two incompatible ways:

1. **SQLAlchemy-Utils path:** `SHA256(app_encryption_key)` → 32-byte derived key
2. **Direct `cryptography` path** (in `aes_gcm_encryption_scheme.py`): `app_encryption_key.encode("UTF-8")` → raw bytes (must be exactly 16 bytes for the scheme's validation, used for per-request encryption)

This means encryption keys for the two paths are not interchangeable despite originating from the same configuration value.

### Mixed encryption engines

The `UserRegistration` model uses `AesEngine` (AES-CBC) while everything else uses `AesGcmEngine` (AES-GCM). The `Organization` model uses an entirely different mechanism (`PGEncryptedString` via PostgreSQL `pgcrypto`). This adds operational complexity.

### No envelope encryption

The data encryption key (DEK) **is** the master key. There is no separation between key-encrypting keys (KEKs) and data-encrypting keys. This means:

- Key rotation requires touching every encrypted value in the database
- The master key must be available in plaintext in the application's memory at all times
- There is no ability to scope encryption keys to specific data domains or tenants

### Large data threshold

The `EncryptedLargeDataDescriptor` introduces a dual storage path (database vs. external) based on data size. This adds complexity to data lifecycle management, backup strategies, and encryption key dependencies.
