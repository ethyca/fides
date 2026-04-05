# Purpose-Based Access Control (PBAC)

Evaluates whether a data consumer has the declared purposes required to access datasets. Produces three outcomes per query: **compliant**, **violation** (purpose mismatch), or **gap** (incomplete configuration).

## How a query is evaluated

```
RawQueryLogEntry { identity: "analyst@co.com", referenced_tables: [...], query_text: "..." }
  │
  ▼
InProcessPBACEvaluationService.evaluate(entry)
  │
  ├─ 1. Identity Resolution
  │    IdentityResolver.resolve("analyst@co.com") → DataConsumerEntity | None
  │
  ├─ 2. Dataset Resolution
  │    DatasetResolver.resolve(TableRef) → fides_key | None
  │
  ├─ 3. Engine: evaluate_access(consumer_purposes, dataset_purposes, query)
  │    │
  │    ├─ Consumer has no purposes → GAP (unresolved_identity)
  │    ├─ Dataset has no purposes  → GAP (unconfigured_dataset)
  │    ├─ Purposes overlap         → COMPLIANT
  │    └─ Purposes don't overlap   → VIOLATION
  │
  ├─ 4. Policy Override (optional)
  │    AccessPolicyEvaluator.evaluate(request) → ALLOW / DENY / NO_DECISION
  │    Only runs when step 3 found a violation. ALLOW suppresses it.
  │
  ▼
EvaluationResult
  identity: str
  consumer: DataConsumerEntity | None
  is_compliant: bool
  violations: [EvaluationViolation, ...]
  gaps: [EvaluationGap, ...]
```

### Three outcomes

| Outcome | Meaning |
|---------|---------|
| **Compliant** | Purposes overlap, access authorized |
| **Violation** | Purposes don't overlap, policy breach |
| **Gap** | Can't evaluate — config incomplete |

Gaps are not violations. They indicate incomplete configuration — either the user isn't mapped to a consumer (`unresolved_identity`) or the dataset doesn't have purposes configured (`unconfigured_dataset`). Gaps are immutable records. When the underlying configuration is addressed, future queries are evaluated correctly — but historical gaps remain for auditability.

## Extension points

All collaborators are injected via constructor. Defaults are provided for each.

| Interface | Kind | What it does | Default |
|-----------|------|-------------|---------|
| `IdentityResolver` | Protocol | `resolve(str) → DataConsumerEntity \| None` | `RedisIdentityResolver` |
| `DatasetResolver` | Class | `resolve(TableRef) → fides_key \| None` | `DatasetResolver()` |
| `AccessPolicyEvaluator` | Protocol | `evaluate(request) → PolicyEvaluationResult` | `NoOpPolicyEvaluator` |
| `PBACEvaluationService` | Protocol | `evaluate(entry) → EvaluationResult` | `InProcessPBACEvaluationService` |

## Types

All shared types live in `types.py` — plain dataclasses with no external dependencies.

**Input types:**
- `TableRef(catalog, schema, table)` — standard SQL catalog terminology
- `RawQueryLogEntry(identity, query_text, referenced_tables, timestamp, ...)` — `identity` is a plain string

**Engine types** (internal to `evaluate_access`):
- `ConsumerPurposes(consumer_id, purpose_keys: frozenset)`
- `DatasetPurposes(dataset_key, purpose_keys: frozenset, collection_purposes)`
- `QueryAccess(query_id, consumer_id, dataset_keys)`
- `Violation(consumer_id, dataset_key, consumer_purposes, dataset_purposes, reason)`
- `ValidationResult(violations, is_compliant, total_accesses)`

**Result types** (returned by evaluation service):
- `EvaluationResult(identity, consumer, is_compliant, violations, gaps)`
- `EvaluationViolation(dataset_key, consumer_purposes, dataset_purposes, data_use, reason, control)`
- `EvaluationGap(gap_type: GapType, identifier, dataset_key, reason)`

**Enums:**
- `GapType` — `UNRESOLVED_IDENTITY`, `UNCONFIGURED_DATASET`
- `ConsumerType` — `GROUP`, `SYSTEM`, `UNRESOLVED`, and platform-specific types (`GOOGLE_GROUP`, `IAM_ROLE`, etc.)

## Identity resolution

The `IdentityResolver` Protocol maps a user identity string to a `DataConsumerEntity`.

**OSS implementations:**

| Class | Backing | Resolution chain |
|-------|---------|-----------------|
| `BasicIdentityResolver` | In-memory list | contact_email → scope email → members list |
| `RedisIdentityResolver` | Redis | contact_email → scope email |

If no consumer matches, the resolver returns `None` and the engine records an `unresolved_identity` gap.

## Package structure

```
fides/service/pbac/
  types.py              All shared types + enums
  sql_parser.py         SQL text → RawQueryLogEntry (sqlglot)
  evaluate.py           Pure engine: evaluate_access() → EvaluationOutput
  reason.py             Human-readable violation reasons
  service.py            PBACEvaluationService Protocol + InProcessPBACEvaluationService
  redis_repository.py   RedisRepository[T] generic ABC

  identity/
    interface.py        IdentityResolver Protocol
    basic.py            BasicIdentityResolver (in-memory)
    resolver.py         RedisIdentityResolver (Redis-backed)

  dataset/
    resolver.py         DatasetResolver (TableRef → fides_key)

  policies/
    interface.py        AccessPolicyEvaluator Protocol + types
    noop.py             NoOpPolicyEvaluator (default)
    evaluator.py        Priority-based policy evaluator

  consumers/
    entities.py         DataConsumerEntity
    repository.py       DataConsumerRedisRepository

  purposes/
    entities.py         DataPurposeEntity
    repository.py       DataPurposeRedisRepository
```
