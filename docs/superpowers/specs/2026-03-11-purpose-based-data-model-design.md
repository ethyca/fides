# Purpose-Based Data Model Design Spec

**Date:** 2026-03-11
**PRD:** [PRD: Purpose-Based Data Model](https://ethyca.atlassian.net/wiki/spaces/PM/pages/4457660423/PRD+Purpose-Based+Data+Model)
**Scope:** Full roadmap architecture, Phase 1 implementation

---

## Summary

Introduce a purpose-based data model built on four new first-class entities (Data Purpose, Data Consumer, Data Producer, extended Dataset) that decouple data governance from the system-centric model. Phase 1 delivers schema, models, and CRUD APIs. Later phases add migration from existing PrivacyDeclarations, dual-write, downstream feature migration, and deprecation of the old model.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| OSS/Paid split | Models + migrations in fides, routes + services in fidesplus | Consistent with existing architecture |
| Data migration | Deferred to Phase 2 | Reduce Phase 1 risk; schema designed to support it |
| DataConsumer for systems | Facade over `ctl_systems`, no new table row | Avoid sync overhead; systems stay in `ctl_systems` |
| DataConsumer for groups/projects | New `data_consumer` table | Non-system types need their own persistence |
| DataPurpose identity | `FidesBase` (fides_key), flat | Taxonomy citizen without hierarchy complexity |
| Dataset purposes | Extend JSON schema with soft references at all levels | Consistent with existing collection/field JSON pattern |
| Dataset purpose routes | No new routes; purposes are part of existing dataset payload | Avoids over-granular API surface |
| DataProducer | Full CRUD in Phase 1 | Low coupling, straightforward to build |
| Consumer-Purpose join | Audited (created_at, updated_at, assigned_by) | Avoids future migration on a potentially large table |
| Approach | Split tables, unified API schema (Approach C) | No sync burden for systems; clean relational model per type; repository layer abstraction available later |

---

## Data Model

### New Tables (fides OSS)

#### `data_purpose`

Replaces PrivacyDeclaration as a standalone, reusable entity. Inherits from both `Base` and `FidesBase` (like `System` and `Dataset`), giving it `id` (UUID PK from `Base`) plus `fides_key`, `name`, `description`, `organization_fides_key`, and `tags` (from `FidesBase`). No parent key / hierarchy. `fides_key` is used as the unique PK in `FidesBase`, but `id` is the actual PK used by join table FKs. This matches the existing dual-key pattern used by `System`, `Dataset`, etc.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | String (UUID) | PK (from `Base`) |
| `fides_key` | String | Unique, Not Null, Indexed (from `FidesBase`) |
| `name` | String | Not Null (from `FidesBase`) |
| `description` | String | Nullable (from `FidesBase`) |
| `organization_fides_key` | String | Nullable (from `FidesBase`, default "default_organization") |
| `tags` | ARRAY(String) | Nullable (from `FidesBase`) |
| `data_use` | String | Not Null, Indexed |
| `data_subject` | String | Nullable |
| `data_categories` | ARRAY(String) | server_default `{}` |
| `legal_basis_for_processing` | String | Nullable |
| `flexible_legal_basis_for_processing` | Boolean | server_default `true` |
| `special_category_legal_basis` | String | Nullable |
| `impact_assessment_location` | String | Nullable |
| `retention_period` | String | Nullable |
| `features` | ARRAY(String) | server_default `{}` |
| `created_at` | DateTime(tz) | Auto |
| `updated_at` | DateTime(tz) | Auto |

Design notes:
- One data use per purpose (deliberate constraint per PRD)
- At most one data subject (0..1 for MVP). Note: existing `PrivacyDeclaration.data_subjects` is `ARRAY(String)`. Declarations with multiple subjects will need to be split into multiple purposes during Phase 2 migration.
- Data categories are optional (act as allowlist when specified)
- `processes_special_category_data` from PrivacyDeclaration is intentionally omitted (derived: present when `special_category_legal_basis` is set)
- All join tables reference `data_purpose.id` (UUID), not `fides_key`. API routes use `fides_key` as the URL identifier; services perform the `fides_key` to `id` lookup internally.
- `flexible_legal_basis_for_processing` and `features` should be `NOT NULL` (matching PrivacyDeclaration pattern), with their `server_default` values.
- All models require explicit `__tablename__` overrides (e.g., `__tablename__ = "data_purpose"`) since the auto-generated names from class names would produce `datapurpose`, `dataconsumer`, etc.

**Facade field coercion (system-type consumers):** When mapping `ctl_systems` rows into `DataConsumerResponse`, the service must:
- Set `type` to `"system"` (hardcoded)
- Coalesce `tags` from `None` to `[]` (System's `tags` column has no server default)
- Map `egress`/`ingress` from System's JSON columns to `Optional[dict]`
- Populate `data_shared_with_third_parties`, `third_parties`, `shared_categories` from the system's privacy declarations where available

#### `data_consumer`

Stores non-system consumers (groups, projects, custom types). System-type consumers are surfaced via a facade over `ctl_systems`.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | String (UUID) | PK |
| `name` | String | Not Null |
| `description` | String | Nullable |
| `type` | String | Not Null, Indexed, CHECK `type != 'system'` |
| `external_id` | String | Nullable |
| `egress` | JSON | Nullable |
| `ingress` | JSON | Nullable |
| `data_shared_with_third_parties` | Boolean | server_default `false` |
| `third_parties` | String | Nullable |
| `shared_categories` | ARRAY(String) | server_default `{}` |
| `contact_email` | String | Nullable |
| `contact_slack_channel` | String | Nullable |
| `contact_details` | JSON | Nullable |
| `tags` | ARRAY(String) | server_default `{}` |
| `created_at` | DateTime(tz) | Auto |
| `updated_at` | DateTime(tz) | Auto |

Type extensibility: `type` is a free-form string, not a DB enum. There is no type registry table. Seed values (`group`, `project`) are documented conventions, not enforced. Customers can use any string value except `system`. The CHECK constraint prevents `system` type rows (those go through the facade).

Note: `data_consumer` has no `fides_key`. Non-system consumers are identified by opaque UUID `id` only. System-type consumers exposed via the facade have a `system_fides_key` available in the response schema (from `ctl_systems.fides_key`). This is a deliberate difference: purposes are taxonomy-like (hence `fides_key`), consumers are not.

#### `data_consumer_purpose`

Join table: non-system consumer to purpose. Audited.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | String (UUID) | PK |
| `data_consumer_id` | String (FK) | Not Null, references `data_consumer.id` |
| `data_purpose_id` | String (FK) | Not Null, references `data_purpose.id` |
| `assigned_by` | String (FK) | Nullable, references `fidesuser.id` |
| `created_at` | DateTime(tz) | Auto |
| `updated_at` | DateTime(tz) | Auto |

Unique constraint on `(data_consumer_id, data_purpose_id)`.

#### `system_purpose`

Join table: system to purpose (via facade). Identical schema to `data_consumer_purpose` for future abstraction.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | String (UUID) | PK |
| `system_id` | String (FK) | Not Null, references `ctl_systems.id` |
| `data_purpose_id` | String (FK) | Not Null, references `data_purpose.id` |
| `assigned_by` | String (FK) | Nullable, references `fidesuser.id` |
| `created_at` | DateTime(tz) | Auto |
| `updated_at` | DateTime(tz) | Auto |

Unique constraint on `(system_id, data_purpose_id)`.

#### `data_producer`

Lightweight entity representing people/teams responsible for data registration and purpose assignment.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | String (UUID) | PK |
| `name` | String | Not Null |
| `description` | String | Nullable |
| `external_id` | String | Nullable |
| `monitor_id` | String (FK) | Nullable, references `monitorconfig.id` (UUID, not the `key` field) |
| `contact_email` | String | Nullable |
| `contact_slack_channel` | String | Nullable |
| `contact_details` | JSON | Nullable |
| `created_at` | DateTime(tz) | Auto |
| `updated_at` | DateTime(tz) | Auto |

#### `data_producer_member`

Join table: producer to user.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | String (UUID) | PK |
| `data_producer_id` | String (FK) | Not Null, references `data_producer.id` |
| `user_id` | String (FK) | Not Null, references `fidesuser.id` |
| `created_at` | DateTime(tz) | Auto |
| `updated_at` | DateTime(tz) | Auto |

Unique constraint on `(data_producer_id, user_id)`.

#### `dataset_purpose`

Join table: dataset to purpose. Audited.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | String (UUID) | PK |
| `dataset_id` | String (FK) | Not Null, references `ctl_datasets.id` |
| `data_purpose_id` | String (FK) | Not Null, references `data_purpose.id` |
| `assigned_by` | String (FK) | Nullable, references `fidesuser.id` |
| `created_at` | DateTime(tz) | Auto |
| `updated_at` | DateTime(tz) | Auto |

Unique constraint on `(dataset_id, data_purpose_id)`.

### Extended Existing Tables

#### `ctl_datasets`

New column:

| Column | Type | Constraints |
|--------|------|-------------|
| `data_producer_id` | String (FK) | Nullable, references `data_producer.id` |

#### Collection/Field JSON Schema Extension

The existing JSON blob for collections, fields, and sub-fields gains an optional `data_purposes` array at every level:

```yaml
dataset:
  fides_key: customer_analytics_db
  data_purposes: ["customer_marketing"]       # dataset level (join table)
  collections:
    - name: user_profiles
      data_purposes: ["personalization"]       # collection level (JSON)
      fields:
        - name: preferences
          data_purposes: ["recommendation"]    # field level (JSON)
          fields:
            - name: topics
              data_purposes: ["content_curation"]  # sub-field level (JSON)
```

Purposes are soft references (`fides_key` strings). Validated on write against the `data_purpose` table.

**Additive inheritance:** Effective purposes at any level = own purposes + all ancestor purposes. No override or exclusion mechanism.

### Entity Relationship Diagram

```
                                      +-----------------+
                                      |   data_purpose  |
                                      |  (FidesBase)    |
                                      |  - fides_key    |
                                      |  - data_use     |
                                      |  - data_subject |
                                      +--------+--------+
                                               |
                    +-----------+------+--------+--------+----------+
                    |           |      |                 |          |
              system_purpose    | data_consumer_purpose  |    dataset_purpose
              (audited join)    |    (audited join)      |    (audited join)
                    |           |         |              |          |
             +------+------+   |  +------+-------+      |   +------+------+
             | ctl_systems |   |  | data_consumer |      |   | ctl_datasets|
             | (existing)  |   |  | (group/proj)  |      |   | (extended)  |
             +-------------+   |  +--------------+       |   +------+------+
                               |                         |          |
                               |                         |     data_producer_id FK
                               |                         |          |
                               |                         |   +------+-------+
                               |                         |   | data_producer |
                               |                         |   +------+-------+
                               |                         |          |
                               |                         |   data_producer_member
                               |                         |     (join table)
                               |                         |          |
                               |                         |   +------+------+
                               |                         |   |  fidesuser  |
                               |                         |   +-------------+
                               |                         |
                          Collection/Field JSON           |
                          (soft data_purposes refs) ------+
```

---

## Service Layer Architecture

All services live in **fidesplus**. Models and migrations in **fides OSS**.

### DataPurposeService

- Standard CRUD on the `data_purpose` table
- Validates `data_use` references exist in the `DataUse` taxonomy
- Validates `data_subject` references exist in the `DataSubject` taxonomy
- Validates `fides_key` uniqueness
- On delete: blocked by DB-level ON DELETE RESTRICT if the purpose is referenced by any `system_purpose`, `data_consumer_purpose`, or `dataset_purpose` rows. The `?force=true` query param bypasses this by first removing all join table references, then deleting the purpose. Collection-level JSON soft references are not FK-enforced; the service scans and warns about orphaned references but does not block on them.

### DataConsumerService

The core facade. Two internal code paths, one external interface.

**Read path:**
- `get(id, type)`: if `type=system`, queries `ctl_systems` + `system_purpose`; otherwise queries `data_consumer` + `data_consumer_purpose`
- `list(filters)`: queries both sources, merges into unified `DataConsumerResponse` list. Supports filtering by type, purpose, tags.
- For system-type consumers, hydrates purpose associations from `system_purpose` and maps System fields into the `DataConsumerResponse` schema

**Write path (system):**
- Purpose assignment/removal only. Writes to `system_purpose` join table. Does not modify `ctl_systems` directly.
- System creation/update continues through existing System endpoints.

**Write path (group/project):**
- Full CRUD on `data_consumer` table
- Purpose assignment writes to `data_consumer_purpose`

**Listing across types:**
- For paginated list endpoints, query both sources with matching filters, merge in-memory, sort, paginate. Acceptable for Phase 1 volumes.

### DataProducerService

- CRUD on `data_producer` table
- Member management: add/remove users via `data_producer_member` join table
- Dataset assignment: set/clear `data_producer_id` FK on `ctl_datasets`
- Optional monitor link: validate `monitor_id` references a valid `MonitorConfig`

### Dataset Purpose Handling

Not a separate service. Integrated into the existing dataset write path:
- On dataset create/update, if `data_purposes` is present at dataset level, validate and persist via `dataset_purpose` join table
- If `data_purposes` is present at collection/field/sub-field levels in the JSON, validate all `fides_key` references and persist in the JSON blob
- On dataset read, include `data_purposes` at each level as stored

### Repository Layer

For Phase 1, services interact with models directly (SQLAlchemy session). The two-path logic in `DataConsumerService` is contained within the service methods.

Future refactor path (when complexity warrants it):
- `SystemConsumerRepository`: reads/writes `ctl_systems` + `system_purpose`
- `NonSystemConsumerRepository`: reads/writes `data_consumer` + `data_consumer_purpose`
- Both implement a shared `ConsumerRepositoryProtocol`

### Cross-Cutting Concerns

**Audit logging:** All mutations fire audit events. For system-type consumers, purpose changes log against the system. For non-system consumers, use the generic audit log.

**Permissions:** New scope prefixes:
- `data_purpose:read`, `data_purpose:create`, `data_purpose:update`, `data_purpose:delete`
- `data_consumer:read`, `data_consumer:create`, `data_consumer:update`, `data_consumer:delete`
- `data_producer:read`, `data_producer:create`, `data_producer:update`, `data_producer:delete`

System-type consumer purpose assignment requires `system:update` scope.

---

## API Routes

All routes in **fidesplus**, under `/api/v1/`.

### Data Purpose

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/data-purpose` | Create a new Data Purpose |
| `GET` | `/data-purpose` | List purposes (paginated, filterable by `data_use`, `data_subject`) |
| `GET` | `/data-purpose/{fides_key}` | Get a single purpose |
| `PUT` | `/data-purpose/{fides_key}` | Update a purpose |
| `DELETE` | `/data-purpose/{fides_key}` | Delete (blocked if in use, unless `?force=true`) |

### Data Consumer

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/data-consumer` | List all consumers (unified). Filters: `type`, `purpose_fides_key`, `tags` |
| `GET` | `/data-consumer/{id}` | Get a single consumer. Requires `?type=system` query param for system lookups (uses system `id`). Without `type` param, looks up in `data_consumer` table only. |
| `POST` | `/data-consumer` | Create a non-system consumer. Returns 400 if `type=system`. |
| `PUT` | `/data-consumer/{id}` | Update a non-system consumer. Returns 400 for system-type. |
| `DELETE` | `/data-consumer/{id}` | Delete a non-system consumer. System-type cannot be deleted here. |

**Purpose assignment (works for all types):**

| Method | Path | Description |
|--------|------|-------------|
| `PUT` | `/data-consumer/{id}/purpose` | Set the full list of purposes (replace semantics) |
| `POST` | `/data-consumer/{id}/purpose/{fides_key}` | Add a single purpose |
| `DELETE` | `/data-consumer/{id}/purpose/{fides_key}` | Remove a single purpose |

Purpose assignment routes also require `?type=system` query param when operating on a system consumer. Without the param, the `{id}` is looked up in the `data_consumer` table only. This matches the GET-by-ID resolution strategy.

### Data Producer

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/data-producer` | Create a producer |
| `GET` | `/data-producer` | List producers (paginated) |
| `GET` | `/data-producer/{id}` | Get a single producer |
| `PUT` | `/data-producer/{id}` | Update a producer |
| `DELETE` | `/data-producer/{id}` | Delete (nullifies `data_producer_id` on datasets) |

**Member management:**

| Method | Path | Description |
|--------|------|-------------|
| `PUT` | `/data-producer/{id}/member` | Set the full member list (replace semantics) |
| `POST` | `/data-producer/{id}/member/{user_id}` | Add a member |
| `DELETE` | `/data-producer/{id}/member/{user_id}` | Remove a member |

### Dataset (existing endpoints, extended payload)

No new routes. Existing `POST /dataset` and `PUT /dataset/{fides_key}` accept:
- `data_purposes: string[]` at dataset level
- `data_purposes: string[]` within each collection, field, and sub-field in the JSON blob
- `data_producer_id: string | None`

Existing `GET /dataset/{fides_key}` response extended with these fields.

### Unified Response Schema

```python
class DataConsumerResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    type: str                                   # "system", "group", "project", custom
    external_id: Optional[str]
    purposes: List[DataPurposeResponse]
    # System-type only (from ctl_systems):
    system_fides_key: Optional[str]
    vendor_id: Optional[str]
    # All types (from data_consumer table or ctl_systems+privacydeclaration):
    egress: Optional[dict]
    ingress: Optional[dict]
    data_shared_with_third_parties: Optional[bool]
    third_parties: Optional[str]
    shared_categories: Optional[List[str]]
    tags: List[str]
    contact_email: Optional[str]
    contact_slack_channel: Optional[str]
    contact_details: Optional[dict]
    created_at: datetime
    updated_at: datetime
```

Notes:
- Uses `Optional[X]` / `List[X]` (not `X | None` / `list[X]`) to match existing codebase Pydantic conventions.
- `data_shared_with_third_parties`, `third_parties`, `shared_categories` are included for all types. For system-type consumers, these are populated from `ctl_systems`/`privacydeclaration` data where available.
- System-specific fields (`cookie_max_age_seconds`, etc.) are not duplicated. Clients needing full system detail use existing system endpoints via `system_fides_key`.

---

## Migration & Backward Compatibility

### Alembic Migration (Phase 1)

Single migration file. Table creation order (respects FK dependencies):

1. `data_purpose` (no FKs to new tables)
2. `data_producer` (FK to `monitorconfig`)
3. `data_consumer` (no FKs to new tables)
4. `data_consumer_purpose` (FKs to `data_consumer` + `data_purpose`)
5. `system_purpose` (FKs to `ctl_systems` + `data_purpose`)
6. `data_producer_member` (FKs to `data_producer` + `fidesuser`)
7. `dataset_purpose` (FKs to `ctl_datasets` + `data_purpose`)
8. ALTER `ctl_datasets`: add `data_producer_id` FK column

Migration conventions:
- All new nullable columns use `nullable=True`
- Array columns use `server_default="{}"`
- Boolean columns use `server_default` with explicit values

Indexes:
- `data_purpose(fides_key)` — unique index (lookups by fides_key)
- `data_purpose(data_use)` — for filtering by data use
- `data_consumer(type)` — for filtering by type
- `system_purpose(system_id)` — for hydrating system consumers
- `system_purpose(data_purpose_id)` — for "find all consumers for a purpose" queries
- `data_consumer_purpose(data_consumer_id)` — for hydrating non-system consumers
- `data_consumer_purpose(data_purpose_id)` — for "find all consumers for a purpose" queries
- `dataset_purpose(dataset_id)` — for hydrating dataset purposes
- `dataset_purpose(data_purpose_id)` — for "find all datasets for a purpose" queries
- `data_producer_member(data_producer_id)` — for listing producer members
- `data_producer_member(user_id)` — for finding a user's producer memberships

FK cascade/delete behavior:
- `system_purpose.system_id` ON DELETE CASCADE (matches existing `privacydeclaration` cascade-on-system-delete behavior)
- `system_purpose.data_purpose_id` ON DELETE RESTRICT (prevent deleting a purpose that's in use)
- `data_consumer_purpose.data_consumer_id` ON DELETE CASCADE (deleting a consumer removes its purpose links)
- `data_consumer_purpose.data_purpose_id` ON DELETE RESTRICT (prevent deleting a purpose that's in use)
- `dataset_purpose.dataset_id` ON DELETE CASCADE (deleting a dataset removes its purpose links)
- `dataset_purpose.data_purpose_id` ON DELETE RESTRICT (prevent deleting a purpose that's in use)
- `data_producer_member.data_producer_id` ON DELETE CASCADE (deleting a producer removes its member links)
- `data_producer_member.user_id` ON DELETE CASCADE (deleting a user removes their producer memberships)
- `ctl_datasets.data_producer_id` ON DELETE SET NULL (deleting a producer nullifies the FK on datasets)

Downgrade: drop tables in reverse order, remove `data_producer_id` from `ctl_datasets`.

### Backward Compatibility Guarantees

- `ctl_systems` table untouched (no column adds/removes/renames)
- `privacydeclaration` table untouched
- All existing System and PrivacyDeclaration API endpoints continue to work identically
- `systemmanager` join table continues to function
- DSR traversal path (System > ConnectionConfig > DatasetConfig) unchanged
- Existing dataset payloads without `data_purposes` or `data_producer_id` continue to work
- Collection/field JSON blobs without `data_purposes` are valid (absence = empty list)
- No existing API response shapes change; new fields are additive only

### Feature Flag

fidesplus setting: `purpose_based_model_enabled: bool = False`

- When `False`: new endpoints return 404, dataset purpose fields are ignored on write, stripped on read
- When `True`: full functionality available
- Allows deployment of the migration without exposing the feature until ready

---

## Phased Roadmap

### Phase 1: Schema + CRUD (implementation scope)

**fides OSS:**
- Alembic migration: all new tables, `data_producer_id` FK on `ctl_datasets`
- SQLAlchemy models for all new tables
- Extend dataset/collection/field Pydantic schemas with optional `data_purposes`

**fidesplus:**
- `DataPurposeService` + CRUD routes
- `DataConsumerService` (facade) + CRUD routes + purpose assignment routes
- `DataProducerService` + CRUD routes + member management routes
- Dataset service extension: validate and persist purpose references on dataset write

**Not included:** Data migration from PrivacyDeclarations, dual-write, downstream feature updates.

### Phase 2: Dual-Write Bridge

- System endpoint writes (create/update privacy declarations) intercepted to mirror into `system_purpose`
- Feature flag controls whether reads come from old model or new model
- Data migration script: backfill `data_purpose` rows from existing PrivacyDeclarations, create `system_purpose` associations
- Deduplication strategy decided at migration time

### Phase 3: Downstream Feature Migration

| Feature | Migration |
|---------|-----------|
| **Policy Evaluation** | Read purposes from `system_purpose` / `data_consumer_purpose` instead of `privacydeclaration` |
| **Datamap / Data Inventory** | Render DataConsumers (all types) with their purposes. System-type includes system metadata via facade. |
| **Consent / TCF** | `TCFPurposeOverride` references `data_purpose.fides_key`. Flexibility evaluated at purpose level. |
| **Privacy Requests (DSR)** | No change. Connection configs remain on System. DataConsumer(system) > System > ConnectionConfig unchanged. |
| **Discovery / Classification** | Classification proposes DataPurpose assignments. DataProducer members review. |
| **PBAC** | Built natively: compare DataConsumer purposes against Dataset effective purposes. |

### Phase 4: Deprecation

- PrivacyDeclaration endpoints marked deprecated
- Dual-write removed, old model becomes read-only
- Eventually: drop `privacydeclaration` table, remove bridge code

---

## Testing Strategy

### Unit Tests (fides OSS)

- **Model tests:** CRUD on each new model, constraint validation (unique fides_key, CHECK constraint on `data_consumer.type`, unique join table entries)
- **Schema tests:** Pydantic validation for DataPurpose, DataConsumer, DataProducer schemas. Dataset schema extension with `data_purposes` at all levels.
- **Additive inheritance:** Compute effective purposes across dataset > collection > field > sub-field hierarchy

### Integration Tests (fidesplus)

- **DataPurposeService:** Create/read/update/delete. Validate `data_use` and `data_subject` references. Delete blocked when purpose is in use.
- **DataConsumerService facade:**
  - List returns both system-type and non-system consumers in unified schema
  - Purpose assignment to system-type writes to `system_purpose`
  - Purpose assignment to group/project writes to `data_consumer_purpose`
  - Create with `type=system` is rejected
  - Get by ID resolves system-type from `ctl_systems`
- **DataProducerService:** CRUD, member add/remove, dataset assignment
- **Dataset purposes:** Full dataset payload with purposes at multiple levels, round-trip read/write, purpose validation failures

### API Tests (fidesplus)

- Route-level tests for each endpoint: auth/permissions, request validation, response shape
- Feature flag off: endpoints return 404
- Cross-type consumer listing with pagination and filters

---

## Open Questions (from PRD)

| # | Question | Status |
|---|----------|--------|
| 1 | Should `data_subject` on Data Purpose be required or optional? | **Decided: Optional (0..1) for MVP** |
| 2 | Deduplication during migration? | **Deferred to Phase 2** |
| 3 | Should Consumer-Purpose join carry metadata? | **Decided: Yes (created_at, updated_at, assigned_by)** |
| 4 | How does `flexible_legal_basis_for_processing` map to new model? | **Deferred to Phase 3 (TCF migration)** |
| 5 | Data Producers assigned to collections or dataset only? | **Decided: Dataset level only (FK on ctl_datasets)** |
| 6 | Naming convention for auto-generated `fides_key` during migration? | **Deferred to Phase 2** |
