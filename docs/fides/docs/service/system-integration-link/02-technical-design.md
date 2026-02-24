# Streamlined Stewarding -- Technical Design

## 1. Data Model Decision: Join Table vs. Extended FK

### Option A: New Join Table (Recommended)

A new `system_connection_config_link` table that explicitly models the relationship between systems and integrations:

```python
class SystemConnectionConfigLink(Base):
    __tablename__ = "system_connection_config_link"

    system_id = Column(
        String,
        ForeignKey("ctl_systems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connection_config_id = Column(
        String,
        ForeignKey("connectionconfig.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    system = relationship("System")
    connection_config = relationship("ConnectionConfig")

    __table_args__ = (
        UniqueConstraint(
            "system_id",
            "connection_config_id",
            name="uq_system_connconfig_link",
        ),
    )
```

**Implemented in:** `src/fides/system_integration_link/models.py`

**Note:** A `link_type` concept (DSR vs. monitoring) was initially considered but removed to simplify the data migration and initial implementation. The join table can be extended with a type qualifier in the future if a concrete technical need arises.

**Data migration:** A migration (`xx_2026_02_20_migrate_system_id_fk_to_link_table.py`) copies every `ConnectionConfig` row where `system_id IS NOT NULL` into the join table, then drops the `system_id` column, its index, and its FK constraint from `connectionconfig`.

**Pros:**
- Forward-compatible with many:many if ever needed.
- Clean separation of link semantics (DSR vs. monitoring can point to different systems).
- Metadata columns (created_at, updated_at) on the relationship itself.
- No ambiguity about what the link means.

**Cons:**
- New table, new migration, new model code.
- Slightly more complex queries (join through the link table).

**Current state:** The migration is complete. `ConnectionConfig.system_id` has been removed. All reads and writes go through the join table.

### Option B: Extend Existing FK with link_type Column

Add a `link_type` column to `ConnectionConfig` alongside the existing `system_id`.

**Pros:** Simpler -- no new table, fewer query changes.

**Cons:** Locks in 1:many, mixes relationship metadata into the entity (anti-pattern), cannot represent many:many.

### Recommendation

**Option A (join table)** is recommended.

### Transition Strategy (Completed)

1. The join table was created alongside the existing FK.
2. A data migration copied all `ConnectionConfig.system_id` values to the join table.
3. SQLAlchemy relationships on `ConnectionConfig.system` and `System.connection_configs` were updated to use `secondary="system_connection_config_link"` with `uselist=False, viewonly=True`.
4. All write paths were migrated to use `SystemConnectionConfigLink.create_or_update_link()`.
5. All read paths (queries filtering on `ConnectionConfig.system_id`) were migrated to join through `SystemConnectionConfigLink`.
6. The `system_id` column, index, and FK constraint were dropped from `connectionconfig`.

## 2. API Contracts

### Architecture: Colocated Service Package

All link management code lives in a single self-contained package:

```
src/fides/system_integration_link/
    __init__.py
    models.py        # SQLAlchemy model + create_or_update_link helper
    routes.py        # FastAPI route definitions (GET, PUT, DELETE)
    service.py       # Business logic
    repository.py    # Data access layer
    entities.py      # Domain entity dataclass
    exceptions.py    # Domain-specific exceptions
    schemas.py       # Pydantic request/response schemas
```

Routes are registered in `src/fides/api/api/v1/api.py` via:

```python
from fides.system_integration_link import routes as system_integration_link_routes
api_router.include_router(system_integration_link_routes.router)
```

The model is registered for Alembic discovery in `src/fides/api/db/base.py` via:

```python
from fides.system_integration_link.models import SystemConnectionConfigLink
```

### Session Management

The service and repository use the shared `@with_optional_sync_session` decorator from `src/fides/core/repository/session_management.py`. This decorator provides composable session semantics:

- **When called without a session** (from routes): creates a new session, commits on success, closes on exit.
- **When called with a session** (from another service/repo method): participates in the caller's transaction (flush only, no commit).

This allows service methods to be called standalone from routes or composed in larger units of work. Routes do not inject a database session.

### Current Constraints

**Max 1 system link per integration.** The API accepts a list for forward compatibility, but the service enforces a maximum of 1 link per connection config. Requests exceeding this limit receive a `400 Bad Request`. This limit is defined as `MAX_LINKS_PER_CONNECTION` in the service and can be raised when the product is ready for multi-link support.

### 2.1 Set System Links for an Integration

```
PUT /api/v1/connection/{connection_key}/system-links
```

**Scope:** `system_integration_link:create_or_update`

**Request body:**

```json
{
  "links": [
    {
      "system_fides_key": "my_system"
    }
  ]
}
```

**Response (200):** flat list of link objects

```json
[
  {
    "system_fides_key": "my_system",
    "system_name": "My System",
    "created_at": "2026-02-18T12:00:00Z"
  }
]
```

**Error responses:**

| Status | Condition |
|--------|-----------|
| 400 | Request contains more links than `MAX_LINKS_PER_CONNECTION` |
| 404 | Connection config not found |
| 404 | Referenced system not found |

**Behavior:**
- **Idempotent replace.** The provided list becomes the complete set of links for this connection. Any existing links not in the new list are deleted. Submitting the same payload twice produces the same result.
- Validates that all referenced systems exist before making any mutations (fail-fast).
- An empty `links` list clears all links for the connection.

### 2.2 Remove a System Link

```
DELETE /api/v1/connection/{connection_key}/system-links/{system_fides_key}
```

**Scope:** `system_integration_link:delete`

**Response:** 204 No Content

**Error responses:**

| Status | Condition |
|--------|-----------|
| 404 | Connection config not found |
| 404 | Referenced system not found |
| 404 | No link exists between the given connection and system |

### 2.3 List System Links for an Integration

```
GET /api/v1/connection/{connection_key}/system-links
```

**Scope:** `system_integration_link:read`

**Response (200):** flat list of link objects

```json
[
  {
    "system_fides_key": "my_system",
    "system_name": "My System",
    "created_at": "2026-02-18T12:00:00Z"
  }
]
```

### 2.4 Extended GET /connection List Response

**Status:** Not yet implemented. Will add a `linked_systems` field alongside the existing `system_key`. The existing `system_key` continues to work via the `ConnectionConfig.system` relationship (which reads through the join table transparently).

### Schemas

```python
class SystemLinkRequest(BaseModel):
    system_fides_key: str


class SetSystemLinksRequest(BaseModel):
    links: list[SystemLinkRequest]


class SystemLinkResponse(BaseModel):
    system_fides_key: Optional[str] = None
    system_name: Optional[str] = None
    created_at: datetime
```

**Implemented in:** `src/fides/system_integration_link/schemas.py`

## 3. Scope Definitions

### New Scope Constants

Added in `src/fides/common/api/scope_registry.py`:

```python
SYSTEM_INTEGRATION_LINK = "system_integration_link"

SYSTEM_INTEGRATION_LINK_CREATE_OR_UPDATE = f"{SYSTEM_INTEGRATION_LINK}:{CREATE}"
SYSTEM_INTEGRATION_LINK_READ = f"{SYSTEM_INTEGRATION_LINK}:{READ}"
SYSTEM_INTEGRATION_LINK_DELETE = f"{SYSTEM_INTEGRATION_LINK}:{DELETE}"
```

### Role Mappings

| Role | `link:read` | `link:create_or_update` | `link:delete` |
|------|-------------|------------------------|---------------|
| Owner | yes | yes | yes |
| Contributor | yes | yes | yes |
| Data Steward | yes | yes | yes |
| Viewer | yes | no | no |
| Approver | no | no | no |

**Status:** `SYSTEM_INTEGRATION_LINK_READ` has been added to `viewer_scopes`. The Data Steward role is not yet implemented.

## 4. Backward Compatibility

| Existing API | Previous behavior | Current behavior |
|---|---|---|
| `PATCH /system/{key}/connection` | Created ConnectionConfig with `system_id` set | Creates ConnectionConfig, then creates link row via `SystemConnectionConfigLink.create_or_update_link()` |
| `DELETE /system/{key}/connection` | Deleted the ConnectionConfig (cascaded via FK) | Deletes the ConnectionConfig; link rows cascade-deleted via FK on the join table |
| `DELETE /system/{fides_key}` (system deletion) | Cascade-deleted the linked ConnectionConfig (and its DatasetConfig) via the direct `system_id` FK on `connectionconfig` | Cascade-deletes only the **link rows** in `system_connection_config_link`. The ConnectionConfig and DatasetConfig are **preserved** and become orphaned. |
| `GET /connection/{key}` | Returns `system_key` from `ConnectionConfig.system` | Unchanged -- `system_key` property reads through the `secondary=` relationship transparently |
| `GET /connection?orphaned_from_system=true` | Filtered on `ConnectionConfig.system_id IS NULL` | Uses `EXISTS` subquery on `SystemConnectionConfigLink` |
| `GET /system/{key}/connection` | Filtered on `ConnectionConfig.system_id` | Joins through `SystemConnectionConfigLink.system_id` |

**Status:** Migration complete. All read and write paths updated.

### Deprecated System-Connection Endpoints

The following endpoints on the `SYSTEM_CONNECTIONS_ROUTER` are now marked `deprecated=True` in OpenAPI. They continue to function but callers should migrate to the new APIs:

| Deprecated endpoint | Replacement |
|---|---|
| `GET /system/{fides_key}/connection` | `GET /connection` (with `linked_systems` in response), or `GET /connection/{key}/system-links` |
| `PATCH /system/{fides_key}/connection` | `PATCH /connection` + `PUT /connection/{key}/system-links` |
| `PATCH /system/{fides_key}/connection/secrets` | `PATCH /connection/{connection_key}/secret` |
| `DELETE /system/{fides_key}/connection` | `DELETE /connection/{key}` or `DELETE /connection/{key}/system-links/{system_fides_key}` |
| `POST /system/{fides_key}/connection/instantiate/{type}` | Connection config + system-links APIs independently |

## 5. Steward Inference Design

### Option A: Compute on the Fly (Recommended for Short-Term)

When `GET /{monitor_config_key}/stewards` is called, compute effective stewards by traversing: MonitorConfig -> ConnectionConfig -> `system_connection_config_link` -> System -> `data_stewards`.

**Pros:** No sync complexity, immediate consistency.
**Cons:** Additional queries on every steward read.

### Option B: Sync-Based

Background sync that propagates system stewards into `monitorsteward` as "inferred" rows.

**Recommendation:** Option A for short-term. Option B can be adopted later if performance requires it.

**Status:** Not yet implemented.

## 6. Frontend Component Design

### 6.1 Integration Overview Table -- Linked Systems Column

Add a column showing linked system names, each linking to the system detail page.

### 6.2 Integration Detail Page -- System Link Management Panel

Inline panel to link/unlink systems, replacing the current "go to system inventory" pattern.

### 6.3 Scope-Gated Rendering

Use `<Restrict scopes={[...]}>` to gate link/unlink actions behind `system_integration_link:*` scopes.

### 6.4 Steward Display Updates

Show combined explicit + inferred stewards on monitor detail pages.

**Status:** Not yet implemented.

## 7. Test Coverage

### Service Layer (Unit Tests)

13 tests in `tests/system_integration_link/test_service.py` covering:

- `TestGetLinksForConnection` (3 tests): happy path, empty result, connection not found
- `TestSetLinks` (6 tests): single link, idempotent replace with pre-existing links, clear with empty list, reject >1 link, connection not found, system not found
- `TestDeleteLink` (4 tests): happy path, connection/system/link not found

Tests mock the repository and inject it via the service constructor.

### Repository Layer (Integration Tests)

13 tests in `tests/system_integration_link/test_repository.py` covering:

- `TestUpsertLink` (2 tests): creates new link, returns existing on duplicate
- `TestGetLinksForConnection` (2 tests): returns links with system info, empty result
- `TestDeleteAllLinksForConnection` (3 tests): deletes all, delete-then-create in same session, zero when none exist
- `TestDeleteLinks` (1 test): deletes specific system link
- `TestResolveHelpers` (4 tests): resolve connection config found/not found, resolve system found/not found

These run against the real test database and verify SQLAlchemy queries and session behavior.

## 8. Open Questions for Discussion

1. **Should the Data Steward role also get `MONITOR_STEWARD_UPDATE`?** Product decision.

2. **Staged resource filtering by inferred stewards:** The compute-on-the-fly approach doesn't automatically extend the existing steward filter query. Defer to a follow-up task if needed.

3. **Raising the per-connection link limit:** The current limit of 1 is a product constraint, not technical. The API and data model already support multiple links.

4. **Adding link_type in the future:** If a concrete need arises to differentiate DSR vs. monitoring links, a new migration can add a `link_type` column to the join table. The unique constraint would need to be updated to include the new column.

## 9. Resolved Decisions

1. **link_type deferred:** The `link_type` concept (DSR vs. monitoring) was removed from the initial implementation to simplify the data migration. A single unqualified link between a system and a connection is sufficient for current needs.

2. **Data migration approach:** Existing `ConnectionConfig.system_id` values were copied to the join table via a SQL `INSERT ... SELECT` migration, then the old column was dropped. The migration is reversible.

3. **Relationship configuration:** Both `ConnectionConfig.system` and `System.connection_configs` use `secondary="system_connection_config_link"` with `uselist=False, viewonly=True`. This provides transparent reads while ensuring all writes go through the explicit `SystemConnectionConfigLink.create_or_update_link()` method.

4. **Write path centralization:** A `create_or_update_link` classmethod on `SystemConnectionConfigLink` ensures exactly one link per connection config. It replaces any existing link for the same connection config before creating the new one.

5. **System deletion no longer cascades to ConnectionConfig.** With the old direct FK (`ConnectionConfig.system_id`), deleting a system would cascade-delete all associated ConnectionConfig rows (and by extension their DatasetConfig rows). With the join table, the CASCADE on `system_connection_config_link.system_id` only deletes the **link rows**. The ConnectionConfig and DatasetConfig are preserved and become "orphaned from system." This is intentional: the join table decouples the lifecycle of systems and integrations, and orphaned connections can be re-linked or cleaned up independently.
