# Streamlined Stewarding -- Technical Design

## 1. Data Model Decision: Join Table vs. Extended FK

### Option A: New Join Table (Recommended)

A new `system_connection_config_link` table that explicitly models the relationship between systems and integrations with a qualified type:

```python
class SystemConnectionLinkType(str, enum.Enum):
    dsr = "dsr"
    monitoring = "monitoring"


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
    link_type = Column(
        Enum(SystemConnectionLinkType),
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
            "link_type",
            name="uq_system_connconfig_link_type",
        ),
    )
```

**Implemented in:** `src/fides/service/system_integration_link/models.py`

**Data migration:** For every `ConnectionConfig` row where `system_id IS NOT NULL`, insert a row into `system_connection_config_link` with `link_type='dsr'`. If the ConnectionConfig also has associated monitors, insert an additional row with `link_type='monitoring'`.

**Pros:**
- Forward-compatible with many:many if ever needed.
- Clean separation of link semantics (DSR vs. monitoring can point to different systems).
- Metadata columns (created_at, updated_at) on the relationship itself.
- No ambiguity about what the link means.

**Cons:**
- New table, new migration, new model code.
- Dual-write period while `ConnectionConfig.system_id` is still in use.
- Slightly more complex queries (join through the link table).

### Option B: Extend Existing FK with link_type Column

Add a `link_type` column to `ConnectionConfig` alongside the existing `system_id`.

**Pros:** Simpler -- no new table, fewer query changes.

**Cons:** Locks in 1:many, mixes relationship metadata into the entity (anti-pattern), cannot represent many:many.

### Recommendation

**Option A (join table)** is recommended.

### Transition Strategy

1. The join table is the source of truth for new link management APIs.
2. `ConnectionConfig.system_id` is maintained via a SQLAlchemy event listener on the link table (for `link_type='dsr'` only), keeping backward compat.
3. Once all consumers are migrated to read from the join table, `ConnectionConfig.system_id` can be deprecated.

## 2. API Contracts

### Architecture: Colocated Service Package

All link management code lives in a single self-contained package:

```
src/fides/service/system_integration_link/
    __init__.py
    models.py        # SQLAlchemy model + enum
    routes.py        # FastAPI route definitions (GET, PUT, DELETE)
    service.py       # Business logic
    repository.py    # Data access layer
    entities.py      # Domain entity dataclass
    exceptions.py    # Domain-specific exceptions
    schemas.py       # Pydantic request/response schemas
```

Routes are registered in `src/fides/api/api/v1/api.py` via:

```python
from fides.service.system_integration_link import routes as system_integration_link_routes
api_router.include_router(system_integration_link_routes.router)
```

The model is registered for Alembic discovery in `src/fides/api/db/base.py` via:

```python
from fides.service.system_integration_link.models import SystemConnectionConfigLink
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
      "system_fides_key": "my_system",
      "link_type": "monitoring"
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
    "link_type": "monitoring",
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
- If `link_type` is `dsr`, also updates `ConnectionConfig.system_id` for backward compat (not yet implemented in POC).

### 2.2 Remove a System Link

```
DELETE /api/v1/connection/{connection_key}/system-links/{system_fides_key}
```

**Scope:** `system_integration_link:delete`

**Query parameter:** `link_type` (optional; if omitted, removes all link types for that system)

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
    "link_type": "monitoring",
    "created_at": "2026-02-18T12:00:00Z"
  }
]
```

### 2.4 Extended GET /connection List Response

**Status:** Not yet implemented. Will add a `linked_systems` field alongside the existing `system_key`.

### Schemas

```python
class SystemLinkRequest(BaseModel):
    system_fides_key: str
    link_type: SystemConnectionLinkType


class SetSystemLinksRequest(BaseModel):
    links: list[SystemLinkRequest]


class SystemLinkResponse(BaseModel):
    system_fides_key: Optional[str] = None
    system_name: Optional[str] = None
    link_type: SystemConnectionLinkType
    created_at: datetime
```

**Implemented in:** `src/fides/service/system_integration_link/schemas.py`

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

| Existing API | Current behavior | After changes |
|---|---|---|
| `PATCH /system/{key}/connection` | Creates ConnectionConfig with `system_id` set | Unchanged; also creates a `dsr` link in join table |
| `DELETE /system/{key}/connection` | Deletes the single ConnectionConfig | Unchanged; also removes link table rows |
| `GET /connection/{key}` | Returns `system_key` field | Adds `linked_systems` field; `system_key` still works |

**Status:** Backward-compat sync (join table <-> `system_id` FK) is not yet implemented.

## 5. Steward Inference Design

### Option A: Compute on the Fly (Recommended for Short-Term)

When `GET /{monitor_config_key}/stewards` is called, compute effective stewards by traversing: MonitorConfig -> ConnectionConfig -> join table (`link_type=monitoring`) -> System -> `data_stewards`.

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

14 tests in `tests/service/system_integration_link/test_service.py` covering:

- `TestGetLinksForConnection` (3 tests): happy path, empty result, connection not found
- `TestSetLinks` (6 tests): single link, idempotent replace with pre-existing links, clear with empty list, reject >1 link, connection not found, system not found
- `TestDeleteLink` (5 tests): happy path, with specific link_type, connection/system/link not found

Tests mock the repository and inject it via the service constructor.

### Repository Layer (Integration Tests)

13 tests in `tests/service/system_integration_link/test_repository.py` covering:

- `TestUpsertLink` (2 tests): creates new link, returns existing on duplicate
- `TestGetLinksForConnection` (2 tests): returns links with system info, empty result
- `TestDeleteAllLinksForConnection` (3 tests): deletes all, delete-then-create in same session, zero when none exist
- `TestDeleteLinks` (2 tests): deletes specific system link, deletes by link_type
- `TestResolveHelpers` (4 tests): resolve connection config found/not found, resolve system found/not found

These run against the real test database and verify SQLAlchemy queries and session behavior.

## 8. Open Questions for Discussion

1. **Migration of existing links to "monitoring" type:** When we populate the join table from existing `system_id` values, should we create both `dsr` and `monitoring` link rows, or only `dsr`? Recommendation: create both.

2. **Should the Data Steward role also get `MONITOR_STEWARD_UPDATE`?** Product decision.

3. **Staged resource filtering by inferred stewards:** The compute-on-the-fly approach doesn't automatically extend the existing steward filter query. Defer to a follow-up task if needed.

4. **Link type enum extensibility:** Keep it closed for now; new values can be added via a migration.

5. **Raising the per-connection link limit:** The current limit of 1 is a product constraint, not technical. The API and data model already support multiple links.
