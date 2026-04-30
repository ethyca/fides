# Consent Identity Enrichment

## Overview

Consent identity enrichment resolves missing user identities before consent propagation by querying database integrations. This enables consent to propagate to all configured connectors even when the incoming request only contains a subset of the required identities.

**Example:** A Bloomreach webhook sends a consent update with only `external_id`. Iterable requires `email` to update subscription preferences. Without enrichment, Iterable gets skipped. With enrichment, Fides queries a consent-enabled Postgres integration to look up the user's email from their external_id, then propagates consent to both Bloomreach and Iterable.

## How It Works

```
Consent request arrives
  identity_data = {external_id: "abc123"}
         │
         ▼
┌─────────────────────────────────┐
│  Consent Identity Enrichment    │
│                                 │
│  1. Build enrichment graph from │
│     consent-enabled DB          │
│     integrations                │
│                                 │
│  2. Find collections reachable  │
│     from seed identity that     │
│     contain missing identities  │
│                                 │
│  3. Query the DB (e.g. SELECT   │
│     email, external_id FROM     │
│     users WHERE external_id =   │
│     'abc123')                   │
│                                 │
│  4. Merge discovered identities │
│     into identity_data          │
└────────────────┬────────────────┘
                 │
  identity_data = {external_id: "abc123", email: "user@example.com"}
                 │
                 ▼
┌─────────────────────────────────┐
│  Consent Propagation (existing) │
│                                 │
│  Bloomreach ← external_id ✓     │
│  Iterable   ← email ✓           │
└─────────────────────────────────┘
```

### Execution Context

Enrichment runs inline within the existing `run_privacy_request` Celery task, immediately before the consent propagation step. No additional Celery tasks or queue overhead are introduced. Typically this adds a single DB query.

### Graceful Fallback

If enrichment fails for any reason (DB error, user not found, no consent-enabled DB integrations), the system logs a warning and proceeds with the original identity data. Consent propagation behaves exactly as it does without enrichment -- connectors that lack a required identity get skipped with `missing_data`.

### Query Generation

Enrichment uses each connector's own query building infrastructure (`QueryConfig` subclasses). This ensures correct SQL dialect, column quoting, schema prefixing, and parameter binding for each database type (Postgres, MySQL, BigQuery, etc.).

## Configuration

### Step 1: Ensure Your Database Integration Has Identity Fields

Your database dataset configuration must declare identity fields on the collection that contains the user mapping. For example, a `users` collection with both `email` and `external_id` as identity fields:

```yaml
dataset:
  - fides_key: my_database
    collections:
      - name: users
        fields:
          - name: id
            fides_meta:
              primary_key: true
              data_type: integer
          - name: email
            data_categories: [user.contact.email]
            fides_meta:
              identity: email
              data_type: string
          - name: external_id
            data_categories: [user.unique_id]
            fides_meta:
              identity: external_id
              data_type: string
          - name: phone
            data_categories: [user.contact.phone_number]
            fides_meta:
              identity: phone_number
              data_type: string
```

The `identity` annotation on each field tells the enrichment system which identity type that column maps to. Multiple identity fields on the same collection enable bidirectional resolution (external_id to email, or email to external_id).

### Step 2: Enable the Consent Action on the Connection

Set `enabled_actions` on the database `ConnectionConfig` to include `consent`:

**Via API (system connection endpoint):**

```bash
PATCH /api/v1/system/{system_fides_key}/connection
[
  {
    "key": "my_postgres_connection",
    "name": "My Postgres",
    "connection_type": "postgres",
    "access": "read",
    "enabled_actions": ["consent"]
  }
]
```

If the integration is also used for access and erasure DSRs, include all action types:

```json
{
  "enabled_actions": ["access", "erasure", "consent"]
}
```

Note: `enabled_actions` is available on the system connection endpoint (`/system/{fides_key}/connection`), not the base `/connection` endpoint.

**Important:** A `null` value for `enabled_actions` (the default) does **not** enable consent enrichment. The `consent` action must be explicitly listed. This is an opt-in mechanism to prevent unintended DB queries during consent propagation.

### Step 3: Verify

Once configured, consent requests that arrive with a partial set of identities will automatically resolve the missing identities from your database before propagating consent. Check the application logs for:

```
Consent identity enrichment: resolving missing identities {'email'}
Consent identity enrichment discovered: {'email'}
```

### What Qualifies for Enrichment


| Criterion         | Required                                                                                                      |
| ----------------- | ------------------------------------------------------------------------------------------------------------- |
| Connection type   | Non-SaaS (Postgres, MySQL, MSSQL, BigQuery, etc.)                                                             |
| `enabled_actions` | Must explicitly include `consent`                                                                             |
| `disabled`        | Must be `false`                                                                                               |
| Dataset           | Must have collections with `identity`-annotated fields                                                        |
| Collection        | Must have at least one identity field matching the seed identity AND at least one matching a missing identity |


SaaS connectors are excluded from enrichment because they typically do not expose read endpoints suitable for identity resolution.