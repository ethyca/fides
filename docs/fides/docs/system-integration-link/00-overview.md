# Streamlined Discovery Monitor Stewarding -- Overview

## Problem Statement

Data stewards -- the users responsible for governing the data assets within their organization's systems -- face two significant friction points in their workflow:

**1. Monitor stewards must be explicitly assigned per-monitor.** When a system has designated data stewards, and that system's integration has one or more discovery monitors, each monitor's stewards must be separately, manually configured. There is no mechanism to inherit stewardship from the system level. The only "inference" today is a frontend default that pre-populates system data stewards when *creating* a new monitor -- but this is a one-time copy, not a live link. If a system's steward roster changes, existing monitors are not updated.

**2. The UX for associating systems with integrations is fragmented and inaccessible to steward-role users.** The current "Link system" step on an integration detail page simply tells the user to navigate to the System inventory and link from there (`useLinkSystemStep.tsx`). There is no inline capability to search for and link a system from the integration page itself. Furthermore, the actions required to create or update this link require `connection:create_or_update` scope, which the Viewer role does not have -- meaning data stewards operating as Viewers cannot perform this association themselves.

## Broader Product and Technical Gaps

These two issues are symptoms of deeper structural problems:

### System:Integration Cardinality Confusion

The data model declares the System-to-ConnectionConfig relationship as **1:1** (`uselist=False` on both sides of the relationship in `sql_models.py` and `connectionconfig.py`), even though the codebase contains comments acknowledging the intent to support 1:many. Code in `system.py` accesses `system.connection_configs.key` as a scalar value. The mismatch between the intended cardinality and the implemented cardinality creates fragility and blocks features that need a system to have multiple integrations (e.g., a system with separate connections for DSR processing and data discovery).

### Ambiguity of the System-Integration Link's Purpose

A ConnectionConfig's `system_id` foreign key currently serves double duty: it associates the integration with a system for DSR graph traversal, *and* it implicitly associates the integration's monitors with that system for discovery/monitoring purposes. These are semantically different relationships. A system might be linked to one integration for DSR but to a different integration for monitoring. The current model cannot represent this.

### Dataset:System Relationship Fragmentation

There are two independent paths linking datasets to systems:
- A soft reference via `System.dataset_references` (an array of fides_key strings)
- An implicit link through ConnectionConfig -> DatasetConfig -> Dataset

These can diverge, leading to inconsistencies in what the system "owns."

### RBAC Inflexibility

The role system is a fixed set of roles (Owner, Contributor, Viewer, Approver, etc.) with hardcoded scope mappings. There is no way for customers to define custom roles or grant granular permissions. This means introducing a "data steward" persona requires either shoehorning it into an existing role or adding a new hardcoded role -- neither of which is ideal long-term.

## Short-Term Vision

The short-term goal is to unblock the steward workflow with the minimum set of changes that leave the codebase in a better structural position:

1. **Inferred monitor stewardship.** Monitor stewards can be derived from the stewards of the monitor's associated system, so that changes to a system's steward roster are automatically reflected in monitor stewardship. The specific mechanism (sync-based vs. compute-on-the-fly) is covered in the [technical design doc](./02-technical-design.md).

2. **First-class system-integration link management.** New, dedicated APIs for creating, reading, and deleting associations between systems and integrations. These APIs are guarded by a new scope (`system_integration_link:create_or_update`, `system_integration_link:delete`) that can be granted independently of full connection management permissions.

3. **Data model evolution.** Move the System:ConnectionConfig relationship from 1:1 toward 1:many via a new join table (`system_connection_config_link`). The old `ConnectionConfig.system_id` FK has been fully migrated to the join table and removed. See [technical design](./02-technical-design.md) for the full analysis.

4. **Data Steward role.** A new role (or extension of Viewer) that grants the system-integration link management scopes plus monitor steward read access, allowing data stewards to perform their duties without requiring full Contributor/Owner privileges.

5. **Improved Integrations page UX.** On the integration overview table, show the associated system(s) for each integration. On the integration detail page, provide inline system search, link, and unlink capabilities. Gate destructive/edit actions behind scopes so that the Data Steward role sees only what they can act on.

## Long-Term Vision

- **Many:many system-integration relationships** if use cases emerge (e.g., a single integration shared across multiple systems). The join-table approach in the short-term design is forward-compatible with this.
- **Flexible RBAC.** Allow customers to define custom roles with arbitrary scope combinations, eliminating the need for bespoke roles like "Data Steward."
- **Holistic Dataset:System cleanup.** Converge the two Dataset-System relationship paths into a single, consistent mechanism. Likely deprecate `System.dataset_references` in favor of the ConnectionConfig -> DatasetConfig path (or a dedicated join table).
- **Qualified integration links.** A `link_type` concept (monitoring vs. DSR) was considered but deferred to simplify the initial migration. The join table can be extended with a type qualifier when a concrete technical need arises.

## Current State Reference

For context, here is a summary of the current data model relationships:

```
System (ctl_systems)
+-- connection_configs (via system_connection_config_link, uselist=False, viewonly=True) -> ConnectionConfig
|   +-- datasets (1:N) -> DatasetConfig -> Dataset (ctl_datasets)
|   +-- monitors (1:N) -> MonitorConfig
|       +-- stewards (M:N via monitorsteward) -> FidesUser
|       +-- executions (1:N) -> MonitorExecution
+-- data_stewards (M:N via systemmanager) -> FidesUser
+-- system_groups (M:N via system_group_member) -> SystemGroup
+-- dataset_references (soft reference array) -> Dataset fides_keys
```

Note: The System:ConnectionConfig relationship was migrated from a direct FK (`ConnectionConfig.system_id`) to the `system_connection_config_link` join table. The old FK has been removed. Both sides of the relationship use `uselist=False` and `viewonly=True` for backward compatibility; writes go through `SystemIntegrationLinkRepository.create_or_update_link()`.

**Cascade behavior change:** Deleting a system previously cascade-deleted its linked ConnectionConfig (and DatasetConfig) via the direct FK. With the join table, system deletion only cascade-deletes the link rows -- the ConnectionConfig and DatasetConfig are preserved as orphans. This decouples system and integration lifecycles.

Key files:
- System model: `src/fides/api/models/sql_models.py`
- ConnectionConfig model: `src/fides/api/models/connectionconfig.py`
- MonitorConfig model: `src/fides/api/models/detection_discovery/core.py`
- MonitorSteward join table: `src/fides/api/models/detection_discovery/monitor_steward.py`
- SystemManager join table: `src/fides/api/models/system_manager.py`
- Scope registry: `src/fides/common/api/scope_registry.py`
- Roles: `src/fides/api/oauth/roles.py`
- FE integration page nav: `clients/admin-ui/src/features/common/nav/nav-config.tsx`
- FE permission check: `clients/admin-ui/src/features/common/Restrict.tsx`
- FE link system hook: `clients/admin-ui/src/features/integrations/setup-steps/hooks/useLinkSystemStep.tsx`

New files (added as part of this effort):

```
src/fides/system_integration_link/   # Self-contained feature package
    __init__.py
    models.py        # SQLAlchemy model (SystemConnectionConfigLink)
    routes.py        # FastAPI route definitions (GET, PUT, DELETE)
    service.py       # Business logic + session management
    repository.py    # Data access layer (SQLAlchemy queries)
    deps.py          # FastAPI dependency factories
    entities.py      # Domain entity dataclass
    exceptions.py    # Domain-specific exceptions
    schemas.py       # Pydantic request/response schemas

src/fides/core/repository/
    session_management.py   # Shared session decorators (with_optional_sync_session, with_optional_async_session)

src/fides/api/alembic/migrations/versions/
    xx_2026_02_18_1700_create_system_connection_config_link.py   # Creates the join table
    xx_2026_02_20_migrate_system_id_fk_to_link_table.py         # Migrates data, drops ConnectionConfig.system_id

tests/system_integration_link/
    test_routes.py       # Route-level integration tests
    test_service.py      # Unit tests (mock-based)
    test_repository.py   # Integration tests (real DB)
```
