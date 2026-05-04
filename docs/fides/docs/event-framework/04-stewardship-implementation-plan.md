# Monitor Stewardship Inheritance — Implementation Plan

The first feature consumer of the event framework. Implements event-driven propagation of inherited stewardship: when a System's data stewards change (or a monitor's `inherit_system_stewards` flag toggles), affected `monitorsteward` rows are reconciled automatically.

This document is self-contained for another agent to pick up the work on a fresh branch. Read it in conjunction with:

- `01-design.md` — framework design + when-to-use boundary
- `02-implementation-plan.md` — phased rollout (this is Phase 2)
- `03-phase-1-plumbing.md` — framework plumbing details (the foundation this builds on)

## 1. Branch Dependencies

This work cannot start until **all three** of the following land on the respective `main` branches:

1. **fides — event framework plumbing.** Branch: `event-framework/plumbing` (or its merged successor). Provides `fides.common.events.{publish_after_commit, subscribes_to, publishes}` and the autodiscover hook.
2. **fides — model updates for stewardship inheritance** (PR #7888 or its successor). Adds:
    - `monitorsteward.source` column (enum: `explicit | inherited`)
    - `monitorsteward.source_system_id` column (nullable FK to `ctl_systems.id`)
    - `monitorconfig.inherit_system_stewards` column (bool, default `true` on new, `false` backfilled)
    - Updated unique constraint on `monitorsteward` to include `source` and `source_system_id`
3. **fidesplus — inheritance-aware API surface** (PR #3394 or its successor). Adds:
    - `inherit_system_stewards` field on `EditableMonitorConfig`
    - `StewardSource` enum + `InheritedFromSystem` schema + extended `MonitorStewardUserResponse`
    - `add_monitor_stewards_bulk` / `remove_monitor_stewards_bulk` (explicit-only)
    - `get_monitor_stewards_attributed` for read-side attribution

If any of these three are not yet on `main`, the work blocks. Coordinate with whoever owns each.

**Recommended branching once dependencies are met:**
- New branch off `main` in fidesplus: `event-framework/stewardship-inheritance` (or similar).
- Possibly a corresponding branch in fides for the publisher / repository changes (the fides changes are ~150 lines, can be a separate fides PR or land in a coordinated pair). My suggestion: separate fides PR shipped first, fidesplus PR follows once it's in.

## 2. Scope of This Implementation

**Triggers covered in this PR:**
1. `System.data_stewards` membership change (emitted from fides).
2. `monitorconfig.inherit_system_stewards` flag toggled / set on create (emitted from fidesplus).

**Triggers deferred to a follow-up PR** (same shape, intentionally out of initial scope to keep the PR tractable):
- `system_connection_config_link` rows added / removed.
- `MonitorConfig.connection_config_id` reassigned.
- New `MonitorConfig` created with `inherit_system_stewards = TRUE` (subset of the toggle case if create maps to "false → true" emission).

The subscriber + reconciler designed here handle all of those when the additional triggers land. No subscriber code changes needed for follow-ups, just additional publishers + event types.

**Out of scope entirely:**
- UI surfacing of "this is inherited" beyond what fidesplus PR #3394 already provides.
- Performance debouncing — see open question #1 in §11.
- Backfill — confirmed unnecessary; nobody has set `inherit_system_stewards=true` yet.

## 3. Event Types

Both event classes live in **fides** so fidesplus and any other repo can subscribe.

### `fides/api/events/system_events.py` (new file)

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class SystemDataStewardsChanged:
    """Emitted when the data stewards on a System change.

    Subscribers must read current state — by the time the subscriber
    runs, the membership may have changed again.
    """
    system_id: str
    user_id: str
    change: str  # "added" | "removed"
```

### `fides/api/events/monitor_events.py` (new file)

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class MonitorInheritanceFlagChanged:
    """Emitted when monitorconfig.inherit_system_stewards is set or
    toggled. Emitted on create when the value is True, and on update
    whenever the value changes between the previous and new value."""
    monitor_config_key: str
    enabled: bool
```

Both are frozen dataclasses with JSON-primitive fields per the framework's validation requirements (see `01-design.md` §6.1).

## 4. Trigger 1 — `System.data_stewards` (fides)

### 4.1 Today's mutation paths

`System.data_stewards` is a M2M via the `systemmanager` association table. The mutators today are model-level methods on `FidesUser`:

- `FidesUser.set_as_system_manager` — `src/fides/api/models/fides_user.py:206`
- `FidesUser.remove_as_system_manager` — `src/fides/api/models/fides_user.py:234`

Call sites (3, all in fides routes):
- `src/fides/api/v1/endpoints/system.py:469` — `add_user_as_system_manager`
- `src/fides/api/v1/endpoints/user_endpoints.py:381,386` — `update_managed_systems` (PUT replace; calls both)
- `src/fides/api/v1/endpoints/user_permission_endpoints.py` — delete path

### 4.2 Introduce `SystemStewardsRepository`

Per the recommended pattern in `01-design.md` §6.6, introduce a repository to host the publish chokepoint.

New file: `src/fides/api/repositories/system_stewards_repository.py`

```python
"""Repository for System.data_stewards mutations.

This is the publish chokepoint for SystemDataStewardsChanged events.
Routes call into this repository instead of the FidesUser model methods
directly so the publish call is colocated with the mutation in a layer
visible to PR review.
"""

from sqlalchemy.orm import Session

from fides.api.events import publish_after_commit, publishes
from fides.api.events.system_events import SystemDataStewardsChanged
from fides.api.models.fides_user import FidesUser
from fides.api.models.sql_models import System


class SystemStewardsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @publishes(SystemDataStewardsChanged)
    def add(self, user: FidesUser, system: System) -> None:
        """Add user as a data steward of system. No-op if already added."""
        if system in user.systems:
            return
        user.set_as_system_manager(self.session, system)
        publish_after_commit(
            self.session,
            SystemDataStewardsChanged(
                system_id=system.id,
                user_id=user.id,
                change="added",
            ),
        )

    @publishes(SystemDataStewardsChanged)
    def remove(self, user: FidesUser, system: System) -> None:
        """Remove user as a data steward of system. No-op if not present."""
        if system not in user.systems:
            return
        user.remove_as_system_manager(self.session, system)
        publish_after_commit(
            self.session,
            SystemDataStewardsChanged(
                system_id=system.id,
                user_id=user.id,
                change="removed",
            ),
        )

    def replace_for_user(self, user: FidesUser, systems: list[System]) -> None:
        """Replace the user's full set of managed systems.

        Computes diff and emits per-change events. Used by the
        update_managed_systems route which does a full-set replace.
        """
        current = set(user.systems)
        desired = set(systems)
        for system in current - desired:
            self.remove(user, system)
        for system in desired - current:
            self.add(user, system)
```

Note: leave `FidesUser.set_as_system_manager` / `remove_as_system_manager` callable. Document in those method docstrings that **production callers should go through `SystemStewardsRepository`** to ensure events are emitted. The model methods remain for legacy / non-routing callers (e.g. tests, scripts).

### 4.3 Migrate the 3 route handlers

Each call site moves from:
```python
user.set_as_system_manager(db, system)
```
to:
```python
SystemStewardsRepository(db).add(user, system)
```

For `update_managed_systems` which does a full-set replace:
```python
SystemStewardsRepository(db).replace_for_user(user, systems)
```

The route handlers' commit step is unchanged — events fire when the existing `db.commit()` runs.

### 4.4 Tests

In `tests/api/repositories/test_system_stewards_repository.py`:
- `add` emits `SystemDataStewardsChanged(change="added")` after commit.
- `remove` emits with `change="removed"`.
- `add` is idempotent — adding twice emits one event.
- `remove` is idempotent — removing absent user emits no event.
- `replace_for_user` emits the correct add/remove diff.
- Rollback path emits no event (use `assert_event_published` pre-commit + verify subscriber not invoked post-rollback).

Use `tests/common/events/_ping.py` as the canonical fixture pattern.

## 5. Trigger 2 — `inherit_system_stewards` toggle (fidesplus)

### 5.1 Today's write path

The flag is written via `upsert_discovery_monitor` route (`src/fidesplus/api/routes/discovery_monitor/discovery_monitors.py:2228`), which calls `DbMonitorConfig.create_or_update(db=db, data=data)` at line 2336.

After fidesplus PR #3394 lands, `inherit_system_stewards` flows in via the `EditableMonitorConfig` schema (`src/fidesplus/api/schemas/discovery_monitor.py`).

### 5.2 Introduce a wrapper helper for diff + publish

The route handler is already 100+ lines and the diff logic is small. Add a thin helper that wraps `create_or_update` with diff detection and event publication.

New file: `src/fidesplus/api/repositories/monitor_config_repository.py` (also used by §6 below)

```python
"""Repository for MonitorConfig writes that need cross-cutting behavior
(event publication, diff detection, etc.)."""

from typing import Optional

from sqlalchemy.orm import Session

from fides.api.events import publish_after_commit, publishes
from fides.api.events.monitor_events import MonitorInheritanceFlagChanged
from fidesplus.api.discovery_monitor.models.monitor_config import (
    DbMonitorConfig,
)


class MonitorConfigRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @publishes(MonitorInheritanceFlagChanged)
    def upsert_with_inheritance_flag_diff(
        self,
        data: dict,
    ) -> DbMonitorConfig:
        """Upsert a monitor config and emit MonitorInheritanceFlagChanged
        if the inherit_system_stewards flag changed (or was set to True
        on creation)."""
        existing = DbMonitorConfig.get_by(
            self.session, field="key", value=data.get("key")
        )
        prev_flag = bool(getattr(existing, "inherit_system_stewards", False))
        new_flag = bool(data.get("inherit_system_stewards", False))

        updated = DbMonitorConfig.create_or_update(db=self.session, data=data)

        if prev_flag != new_flag:
            publish_after_commit(
                self.session,
                MonitorInheritanceFlagChanged(
                    monitor_config_key=updated.key,
                    enabled=new_flag,
                ),
            )

        return updated
```

### 5.3 Migrate the route handler

In `upsert_discovery_monitor` (`src/fidesplus/api/routes/discovery_monitor/discovery_monitors.py`):

Replace:
```python
updated_db_config = DbMonitorConfig.create_or_update(db=db, data=data)
```
with:
```python
updated_db_config = MonitorConfigRepository(db).upsert_with_inheritance_flag_diff(data)
```

The existing `update_monitor_stewards(...)` call after this line stays unchanged — that handles **explicit** steward writes; inherited rows are managed by the subscriber.

### 5.4 Tests

In `tests/api/repositories/test_monitor_config_repository.py`:
- `upsert_with_inheritance_flag_diff` emits `MonitorInheritanceFlagChanged(enabled=True)` on create with `inherit_system_stewards=true`.
- Same on update from `false → true` and `true → false` (with the corresponding `enabled` value).
- Same value on both sides emits no event.
- Existing route-level tests for `upsert_discovery_monitor` should still pass; add one assertion-on-event for the inherit-system-stewards flow.

## 6. Subscriber (fidesplus)

### 6.1 Package layout

New package: `src/fidesplus/api/service/discovery/monitor_stewardship_inheritance/`

```
monitor_stewardship_inheritance/
    __init__.py
    subscribers.py    # @subscribes_to handlers
    reconciler.py     # APScheduler job + on-demand reconcile function
    service.py        # _reconcile_inherited_stewards_for_monitor + helpers
    repository.py     # read helpers (or extend MonitorConfigRepository)
```

### 6.2 Read path — extend `MonitorConfigRepository`

Add to `src/fidesplus/api/repositories/monitor_config_repository.py`:

```python
def list_inheriting_monitors_for_system(
    self, system_id: str
) -> list[DbMonitorConfig]:
    """Return MonitorConfigs whose linked Systems include system_id and
    whose inherit_system_stewards flag is True."""
    from fides.system_integration_link.models import SystemConnectionConfigLink

    return (
        self.session.query(DbMonitorConfig)
        .join(
            SystemConnectionConfigLink,
            SystemConnectionConfigLink.connection_config_id
            == DbMonitorConfig.connection_config_id,
        )
        .filter(SystemConnectionConfigLink.system_id == system_id)
        .filter(DbMonitorConfig.inherit_system_stewards.is_(True))
        .all()
    )

def list_all_inheriting_monitors(self) -> list[DbMonitorConfig]:
    """Return every MonitorConfig with inherit_system_stewards = True.
    Used by the periodic reconciler."""
    return (
        self.session.query(DbMonitorConfig)
        .filter(DbMonitorConfig.inherit_system_stewards.is_(True))
        .all()
    )

def get_by_key(self, monitor_config_key: str) -> Optional[DbMonitorConfig]:
    return DbMonitorConfig.get_by(
        self.session, field="key", value=monitor_config_key
    )
```

### 6.3 Reconciliation logic — `service.py`

```python
"""Core reconciliation logic for inherited stewardship.

Idempotent: computes the desired set of inherited steward rows for a
monitor and adjusts actual rows to match. Explicit rows are never touched.
"""

from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.sql_models import System
from fidesplus.api.discovery_monitor.models.monitor_config import (
    DbMonitorConfig,
)
from fidesplus.api.discovery_monitor.models.monitor_steward import (
    DbMonitorSteward,
    StewardSource,
)


def reconcile_inherited_stewards_for_monitor(
    session: Session, monitor: DbMonitorConfig
) -> None:
    """Compute desired inherited stewardship for ``monitor`` and write
    the diff to monitorsteward.

    Desired set: union of data_stewards across linked Systems, with
    source='inherited' and source_system_id pointing back to the system
    that contributed the user.

    Adds missing rows, removes now-stale inherited rows, leaves
    source='explicit' rows untouched.
    """
    desired: set[tuple[str, str]] = set()  # (user_id, source_system_id)

    # Walk the propagation graph: monitor -> connection_config ->
    # system_connection_config_link -> system -> data_stewards.
    for system in _linked_systems_for_monitor(session, monitor):
        for user in system.data_stewards:
            desired.add((user.id, system.id))

    actual_query = session.query(DbMonitorSteward).filter(
        DbMonitorSteward.monitor_config_id == monitor.id,
        DbMonitorSteward.source == StewardSource.inherited,
    )
    actual: dict[tuple[str, str], DbMonitorSteward] = {
        (row.user_id, row.source_system_id): row for row in actual_query
    }

    # Add missing rows.
    for key in desired - set(actual.keys()):
        user_id, source_system_id = key
        DbMonitorSteward.create(
            session,
            data={
                "user_id": user_id,
                "monitor_config_id": monitor.id,
                "source": StewardSource.inherited,
                "source_system_id": source_system_id,
            },
        )

    # Remove stale rows.
    for key in set(actual.keys()) - desired:
        actual[key].delete(session)


def delete_all_inherited_stewards_for_monitor(
    session: Session, monitor: DbMonitorConfig
) -> None:
    """Used when inherit_system_stewards toggles to False — drop every
    inherited row for the monitor; explicit rows untouched."""
    session.query(DbMonitorSteward).filter(
        DbMonitorSteward.monitor_config_id == monitor.id,
        DbMonitorSteward.source == StewardSource.inherited,
    ).delete()


def _linked_systems_for_monitor(
    session: Session, monitor: DbMonitorConfig
) -> list[System]:
    """Walk the connection_config -> system_connection_config_link path."""
    from fides.system_integration_link.models import SystemConnectionConfigLink

    return (
        session.query(System)
        .join(
            SystemConnectionConfigLink,
            SystemConnectionConfigLink.system_id == System.id,
        )
        .filter(
            SystemConnectionConfigLink.connection_config_id
            == monitor.connection_config_id
        )
        .all()
    )
```

### 6.4 Subscribers — `subscribers.py`

```python
"""Event subscribers for stewardship inheritance.

Inline handlers — work runs in the @subscribes_to Celery task itself.
The work is bounded (linear in the monitors affected by the source
system) and idempotent against current state.

If a subscriber's module fails to import, no propagation events fire
on its event types — the periodic reconciler is the safety net (see
01-design.md §6.4).
"""

from fides.api.events import subscribes_to
from fides.api.events.monitor_events import MonitorInheritanceFlagChanged
from fides.api.events.system_events import SystemDataStewardsChanged
from fidesplus.api.repositories.monitor_config_repository import (
    MonitorConfigRepository,
)
from fidesplus.api.service.discovery.monitor_stewardship_inheritance.service import (
    delete_all_inherited_stewards_for_monitor,
    reconcile_inherited_stewards_for_monitor,
)
from fides.api.tasks import DatabaseTask


@subscribes_to(SystemDataStewardsChanged)
def reconcile_after_system_stewards_change(
    event: SystemDataStewardsChanged,
) -> None:
    task = DatabaseTask()
    with task.get_new_session() as db:
        repo = MonitorConfigRepository(db)
        for monitor in repo.list_inheriting_monitors_for_system(event.system_id):
            reconcile_inherited_stewards_for_monitor(db, monitor)
        db.commit()


@subscribes_to(MonitorInheritanceFlagChanged)
def reconcile_after_flag_toggle(event: MonitorInheritanceFlagChanged) -> None:
    task = DatabaseTask()
    with task.get_new_session() as db:
        repo = MonitorConfigRepository(db)
        monitor = repo.get_by_key(event.monitor_config_key)
        if monitor is None:
            return
        if event.enabled:
            reconcile_inherited_stewards_for_monitor(db, monitor)
        else:
            delete_all_inherited_stewards_for_monitor(db, monitor)
        db.commit()
```

Subscribers run on the existing "Other" worker by default (see `01-design.md` §5.4). No new pod type or queue.

### 6.5 Subscriber autodiscovery

In fidesplus's worker / app startup, register the subscriber module:

```python
# fidesplus/api/worker/__init__.py (or wherever subscriber modules are wired)
from fides.common.events.autodiscover import register_subscriber_module

register_subscriber_module(
    "fidesplus.api.service.discovery.monitor_stewardship_inheritance.subscribers"
)
```

Make sure this import runs before `import_subscriber_modules()` is called.

## 7. Reconciler (fidesplus)

### 7.1 Reconciler function — `reconciler.py`

```python
"""Periodic full-sweep reconciler for stewardship inheritance.

Runs every ~15 minutes by default. Re-derives inherited steward rows
for every monitor with inherit_system_stewards=True regardless of
whether events fired.

The Redis last-run timestamp prevents over-firing across pods. See
04-stewardship-implementation-plan.md §7.2.
"""

import time

from loguru import logger

from fides.api.tasks import DatabaseTask
from fides.api.util.cache import get_cache
from fidesplus.api.repositories.monitor_config_repository import (
    MonitorConfigRepository,
)
from fidesplus.api.service.discovery.monitor_stewardship_inheritance.service import (
    reconcile_inherited_stewards_for_monitor,
)
from fidesplus.config import get_config

LAST_RUN_KEY = "steward_inheritance_reconciler_last_run"


def reconcile_all_inherited_stewards() -> None:
    """Full-sweep reconcile across every inheriting monitor.

    Skipped on pods that fired within the configured interval — the
    Redis timestamp acts as a coarse cluster-wide cooldown.
    """
    config = get_config()
    interval_seconds = (
        config.detection_discovery.steward_inheritance_reconciler_interval_minutes
        * 60
    )

    redis = get_cache()
    now = int(time.time())
    last_run = redis.get(LAST_RUN_KEY)
    if last_run is not None and now - int(last_run) < interval_seconds:
        logger.debug(
            "Stewardship reconciler last ran {}s ago; skipping (interval={}s)",
            now - int(last_run),
            interval_seconds,
        )
        return

    # Stamp before running so concurrent pods skip. A failure within the
    # body still consumes its interval; the on-demand endpoint is the
    # recovery path.
    redis.set(LAST_RUN_KEY, str(now))

    task = DatabaseTask()
    with task.get_new_session() as db:
        repo = MonitorConfigRepository(db)
        monitors = repo.list_all_inheriting_monitors()
        for monitor in monitors:
            try:
                reconcile_inherited_stewards_for_monitor(db, monitor)
            except Exception:
                logger.exception(
                    "Failed to reconcile inherited stewards for monitor: {}",
                    monitor.key,
                )
        db.commit()


def initiate_steward_inheritance_reconciler() -> None:
    """Register the periodic reconciler with APScheduler."""
    from fides.api.tasks.scheduled.scheduler import scheduler

    config = get_config()
    interval_minutes = (
        config.detection_discovery.steward_inheritance_reconciler_interval_minutes
    )

    scheduler.add_job(
        reconcile_all_inherited_stewards,
        trigger="interval",
        minutes=interval_minutes,
        id="steward_inheritance_reconciler",
        replace_existing=True,
    )
```

Wire `initiate_steward_inheritance_reconciler` into fidesplus app startup alongside other `initiate_*` functions.

### 7.2 The Redis last-run timestamp pattern

Each pod's APScheduler ticks on its own clock. Without coordination the reconciler would over-fire — N pods × evenly-staggered offsets gives N× the configured cadence.

The Redis key `steward_inheritance_reconciler_last_run` stores the unix timestamp of the most recent attempted run. Each pod's reconciler reads this before doing work and skips if not enough time has passed.

Trade-offs documented in conversation:
- Stamp **before** running, not after — closes the over-firing window the moment we decide to run. A failed run consumes its interval; the on-demand endpoint is the recovery path.
- Small TOCTOU race accepted: two pods could both observe a stale timestamp and both run. The reconcile body is idempotent; concurrent runs produce the same end state, just wasted DB cycles. Add an alert on this if it becomes common.
- No TTL on the key — small payload, persists across restarts (good for ops introspection).

### 7.3 Configuration

Add to `src/fidesplus/config/detection_discovery_settings.py`:

```python
steward_inheritance_reconciler_interval_minutes: int = Field(
    default=15,
    description=(
        "Interval (in minutes) between periodic reconciliations of "
        "inherited monitor stewardship. Tighter than typical reconcilers "
        "because functional staleness is at stake — until propagation "
        "runs, inherited stewardship is not in effect (a user expecting "
        "access via inheritance does not have it)."
    ),
    ge=1,
    le=1440,
)
```

Default `15` minutes per the design doc §10.2 starting suggestion.

### 7.4 On-demand reconcile endpoint

Add a route on the existing monitor-stewards router:

```
POST /discovery-monitor/stewardship/reconcile
```

- Auth: `Security(verify_oauth_client_plus, scopes=[MONITOR_STEWARD_UPDATE])`
- Body: empty (full-sweep) or `{"monitor_config_keys": [...]}` for scoped reconcile
- Behavior: synchronously calls `reconcile_all_inherited_stewards()` (or per-monitor variant)
- Bypasses the Redis last-run check — ops should be able to force a reconcile when investigating
- Returns 200 with a brief result summary on success

Useful for ops + product when something looks wrong.

## 8. Tests

Mirror the structure used in `tests/common/events/`. All tests should be deterministic and fast.

### fides side
- `tests/api/repositories/test_system_stewards_repository.py` — publish path tests (per §4.4).
- `tests/api/v1/endpoints/test_system_steward_routes.py` (or extend existing) — verify the migrated routes still work and now publish events.

### fidesplus side
- `tests/api/repositories/test_monitor_config_repository.py` — flag-toggle publish path + read helpers.
- `tests/api/service/discovery/test_monitor_stewardship_inheritance/` — new test directory.
  - `test_subscribers.py`: subscribers are registered, dispatch correctly on publish, idempotent.
  - `test_service.py`: reconcile logic produces correct end state across many seeded scenarios (multi-system, multi-user, explicit-coexisting-with-inherited, flag-flip).
  - `test_reconciler.py`: full-sweep + on-demand endpoint + Redis last-run skip semantics.
  - **"Events stopped flowing" test**: seed inconsistent state, run only the reconciler, assert correct end state. This is the framework's correctness contract for correctness-sensitive subscribers (`01-design.md` §6.4).
- Coverage tests: PR should not require new entries in `tests/common/events/coverage_excludes.py` — every subscriber's event type has a `@publishes` marker.

## 9. Acceptance Criteria

- Subscriber + reconciler converge on identical end state for a battery of seeded scenarios.
- Reconciler handles tenant-scale data without exceeding existing monitor-related job budget.
- "Events stopped flowing" test passes — reconciler alone produces correct end state.
- All routes that previously called the model methods directly are migrated to use the repository.
- `monitorsteward.source = explicit` rows are never modified by any code path introduced here.
- Redis last-run skip is exercised by tests (run twice within the interval; second run skips).
- On-demand endpoint bypasses the skip and runs synchronously.
- All new tests green.
- Coverage tests in `tests/common/events/test_coverage_checks.py` still green (no new entries needed in `coverage_excludes.py`).

## 10. Suggested PR Split

Three PRs in sequence (or two if comfortable):

1. **fides**: event types + `SystemStewardsRepository` + route migrations + tests. Independently shippable; events fire but no subscriber consumes them yet (logs a "no subscribers" warning at dispatch time, which is fine).
2. **fidesplus**: `MonitorConfigRepository` + flag-toggle publisher + subscriber + service + reconciler + on-demand endpoint + tests. Depends on PR 1 being merged into `main` first.
3. **(optional follow-up)**: additional triggers from §2 — link table changes, connection_config_id reassignment, new monitor with flag=true if not subsumed by toggle case.

Each PR should reference this doc + the design doc + the framework PR for context.

## 11. Open Questions To Confirm Before Coding

1. **Debouncing**: deliberately not addressed in this plan per direction. If observed pathologically (e.g. UI sees stale stewardship for >1 minute under bursty system mutations), revisit using the trailing-edge debounce pattern documented in conversation. Out of scope for this PR.
2. **Failure observability**: do we want a metric or alert on reconciler failure? Lean yes — emit a structured log with `reconciler=steward_inheritance result=failed` so an operator can grep / alert. Confirm log format.
3. **On-demand endpoint scope (single-monitor vs full-sweep)**: design above supports both via optional body. Confirm product wants both.
4. **Replace `update_managed_systems` route's full-set replace semantics**: `SystemStewardsRepository.replace_for_user` emits per-change events. If the route makes 10 changes, 10 events fire. Acceptable, but worth confirming we don't want a single batched `SystemStewardsBulkChanged(system_ids: list[str])` event instead. Lean per-change for symmetry with the other trigger paths and because the subscriber's reconcile is bounded per-system anyway.
5. **Reconciler interval**: starting at 15 minutes per design doc. Confirm with product before shipping — functional staleness ceiling matters more than display freshness, so this might want to be tighter (5 minutes) or fine (30 minutes) depending on tolerance.

## 12. Related References

- Design: `01-design.md`
- Phase plan: `02-implementation-plan.md` (this is Phase 2)
- Framework plumbing: `03-phase-1-plumbing.md`
- fides PR for model updates: #7888 (or successor)
- fidesplus PR for API surface: #3394 (or successor)
- Original system-integration-link technical design: `system-integration-link/02-technical-design.md` (specifically §5 Steward Inference Design)
