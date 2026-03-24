# Purpose-Based Access Control (PBAC)

Open-source evaluation service for purpose-based data access control. Determines whether a data consumer has the declared purposes required to access datasets, collections, and fields.

## Quick Start

### 1. Register consumers (who accesses data)

```
POST /api/v1/data-consumer
{
  "name": "Analytics Team",
  "type": "group",
  "external_id": "analytics-team",
  "contact_email": "analytics-lead@company.com",
  "members": ["analyst@company.com", "lead@company.com"]
}
```

### 2. Define purposes (why data is accessed)

```
POST /api/v1/data-purpose
{
  "fides_key": "marketing_analytics",
  "name": "Marketing Analytics",
  "data_use": "marketing.advertising"
}
```

### 3. Assign purposes to consumers

```
PUT /api/v1/data-consumer/{id}/purposes
{ "purpose_fides_keys": ["marketing_analytics"] }
```

### 4. Annotate datasets with purposes

Datasets declare their allowed purposes via fideslang `data_purposes` on datasets, collections, and fields.

### 5. Evaluate a SQL query

```
POST /api/v1/pbac/evaluate
{
  "query_text": "SELECT email, purchase_history FROM customers.orders",
  "user_identity": "analyst@company.com"
}
```

Response:

```json
{
  "query_id": "abc-123",
  "is_compliant": false,
  "consumer": {
    "name": "Analytics Team",
    "external_id": "analytics-team",
    "purpose_fides_keys": ["marketing_analytics"]
  },
  "violations": [
    {
      "dataset_key": "customers",
      "consumer_purposes": ["marketing_analytics"],
      "dataset_purposes": ["billing_operations"],
      "reason": "Consumer purposes do not overlap with dataset purposes",
      "control": "purpose_restriction"
    }
  ]
}
```

## How It Works

```
raw SQL
  |
  v
SQL Parser (sqlglot) -- extracts table references
  |
  v
RawQueryLogEntry
  |
  v
PBACEvaluationService
  |
  +-- 1. Identity Resolution
  |     user email --> consumer (via contact_email, external_id, or members list)
  |
  +-- 2. Dataset Resolution
  |     table references --> fides dataset keys
  |
  +-- 3. Purpose Map
  |     consumer --> declared purposes
  |     dataset  --> declared purposes
  |
  +-- 4. PBAC Engine
  |     Do consumer purposes overlap with dataset purposes?
  |       yes --> COMPLIANT
  |       no  --> VIOLATION
  |
  +-- 5. Policy v2 Engine (optional)
  |     Does any access policy override the violation?
  |       ALLOW       --> suppress violation
  |       DENY        --> confirm violation
  |       NO_DECISION --> confirm violation
  |
  v
EvaluationResult
  is_compliant: bool
  violations: [...]
```

## Identity Resolution

The system resolves who is running a query by matching the user identity against registered consumers.

**Resolution chain (in order):**

1. **contact_email** -- exact match on the consumer's contact email
2. **external_id** -- match on the consumer's external identifier (group name, role ID, etc.)
3. **members** -- match if the user email appears in the consumer's members list

If no consumer matches, the user is marked as "unresolved" with no declared purposes, which means all dataset accesses are violations.

### Group membership

Consumers can represent groups or teams. Add user emails to the `members` list:

```json
{
  "name": "Analytics Team",
  "type": "group",
  "external_id": "analytics-team",
  "members": [
    "analyst@company.com",
    "data-scientist@company.com",
    "intern@company.com"
  ]
}
```

When `analyst@company.com` runs a query, they inherit the Analytics Team's purposes.

## Policy v2 (Override Engine)

When PBAC finds a violation (purposes don't overlap), the Policy v2 engine gets a chance to override it. Policies use priority-based, first-decisive-match-wins evaluation.

A policy can ALLOW access even when purposes don't match:

```
POST /api/v1/policy
{
  "fides_key": "allow_analytics_on_orders",
  "decision": "ALLOW",
  "priority": 100,
  "match": {
    "data_use": { "any": ["marketing.advertising"] }
  }
}
```

PBAC is always checked first. Policies only evaluated when purposes don't match.

## Package Structure

```
fides/service/pbac/
  types.py              -- RawQueryLogEntry, TableRef
  sql_parser.py         -- Generic SQL --> RawQueryLogEntry (sqlglot)
  engine/               -- PBAC evaluation engine (zero dependencies)
    types.py            -- ConsumerPurposes, DatasetPurposes, QueryAccess, etc.
    evaluate.py         -- evaluate_access()
    reason.py           -- Human-readable violation reasons
  evaluation/           -- Service boundary
    types.py            -- EvaluationResult, ResolvedConsumer, EvaluationViolation
    interface.py        -- PBACEvaluationService Protocol
  identity/             -- Consumer identity resolution
    interface.py        -- IdentityResolver Protocol
    basic.py            -- BasicIdentityResolver (email + external_id + members)
  policies/             -- Policy v2 evaluation interface
    interface.py        -- AccessPolicyEvaluator Protocol + types
    noop.py             -- NoOpPolicyEvaluator (default)
```

## Extending (Fidesplus)

Fidesplus adds platform-specific capabilities on top of the OSS evaluation:

- **Platform connectors** -- BigQuery, Snowflake, Databricks audit log ingestion
- **Platform identity resolution** -- queries BigQuery IAM / Snowflake RBAC to resolve user roles, then matches roles against consumer `external_id`
- **Access control dashboard** -- violation logs, timeseries, per-consumer breakdowns
