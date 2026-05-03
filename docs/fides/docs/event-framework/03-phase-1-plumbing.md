# Phase 1 — Core Plumbing Checklist

Concrete checklist for the framework plumbing PR described in `02-implementation-plan.md` Phase 1. References design decisions in `01-design.md`.

Single PR, scoped to `fides/common/events/` plus minimal touches to existing Celery integration. No production publishers or subscribers — the framework's correctness is demonstrated entirely via a test-only "ping" event.

## 0. Branch & PR

- Branch: `event-framework/plumbing` (or similar).
- PR title: `feat(events): add core event framework plumbing`.
- PR description: link to `01-design.md`, `02-implementation-plan.md` Phase 1, and this checklist. State explicitly that no production code path is wired in.

## 1. Package layout

New package at `fides/common/events/`:

```
fides/common/events/
    __init__.py            # public API surface
    base.py                # event conventions + validation
    registry.py            # in-process registry singleton
    decorators.py          # @subscribes_to, @publishes
    publisher.py           # publish_after_commit + after-commit hook
    dispatcher.py          # the after-commit callback
    celery_integration.py  # task wrapper factory + event_id signal handlers
    autodiscover.py        # hook into existing autodiscover_task_locations
    testing.py             # assert_event_published + fixtures
```

Config:
- `fides/config/event_settings.py` — new `EventSettings` Pydantic config class with at least `enabled: bool = True`.
- Wired into `fides.config.FidesConfig` as `events: EventSettings`.

## 2. Components

Each item below has a concrete acceptance bar. Order is logical, not strictly sequential — they all land in one PR.

### 2.1 Event base + validation (`base.py`)

- [ ] Define a `validate_event_class(cls)` helper that asserts `cls` is a frozen dataclass and that all fields are JSON-primitive types (str, int, float, bool, None, list, dict) or other validated event classes. Called by `@subscribes_to` and `@publishes` at decoration time.
- [ ] Helpers `event_to_dict(event) -> dict` (uses `dataclasses.asdict`) and `dict_to_event(cls, payload: dict) -> cls` (calls `cls(**payload)`).
- [ ] Document the field-type constraint in the module docstring; reject UUID/datetime/Enum fields with a clear error message.

**Acceptance**: unit tests covering each accepted/rejected field type; round-trip serialization tests.

### 2.2 Registry (`registry.py`)

- [ ] Module-level `_REGISTRY: dict[type, list[Subscriber]]`.
- [ ] `Subscriber` is a small dataclass: `func`, `task_name`, `queue`, `event_type`.
- [ ] Helpers: `register(subscriber)`, `get_subscribers(event_type) -> list[Subscriber]`, `all_event_types() -> set[type]`, `all_subscribers() -> list[Subscriber]`.
- [ ] `_PUBLISHES_MARKERS: dict[Callable, list[type]]` — separate registry for `@publishes`-marked methods (test-time introspection).

**Acceptance**: unit tests for register / lookup; concurrent registrations from different modules.

### 2.3 Decorators (`decorators.py`)

- [ ] `@subscribes_to(event_type, queue="fides", max_retries=None, retry_backoff=None)`:
  - Validates `event_type` via `validate_event_class`.
  - Creates a Celery task wrapper (see §2.5) and registers it.
  - Adds a `Subscriber` entry to the registry.
  - Returns the original function unchanged.
- [ ] `@publishes(*event_types)`:
  - Validates each event type.
  - Records the marker in `_PUBLISHES_MARKERS`.
  - Returns the original function unchanged.
  - Does **not** affect runtime behavior — see design doc §6.5.

**Acceptance**: unit tests covering successful registration, invalid event class rejection, multiple subscribers per event, multiple event types per `@publishes`.

### 2.4 Publisher (`publisher.py`)

- [ ] `publish_after_commit(session, event)`:
  - Validates `type(event)` is registered (or accept any event class — TBD per §4 below).
  - Generates `event_id = uuid4().hex`.
  - Appends `(event_id, event)` to `session.info.setdefault("pending_events", [])`.
  - On first call per session, registers `_after_commit_dispatch` and `_after_rollback_clear` callbacks via `sqlalchemy.event.listens_for(session, "after_commit", once=True)` (and `"after_rollback"`).
- [ ] `_after_commit_dispatch(session)`: drains `session.info["pending_events"]` and hands each entry to the dispatcher.
- [ ] `_after_rollback_clear(session)`: clears `session.info["pending_events"]` without dispatching.

**Acceptance**: unit tests covering the commit, rollback, multiple-events-per-txn, and "no events on a session that didn't publish" paths.

### 2.5 Dispatcher (`dispatcher.py`)

- [ ] `dispatch(event_id, event)`:
  - Looks up subscribers via `registry.get_subscribers(type(event))`.
  - For each subscriber: calls `celery.send_task(subscriber.task_name, args=[event_to_dict(event)], headers={"event_id": event_id}, queue=subscriber.queue)`.
  - Wraps each `send_task` in try/except — failures log and continue.
  - Skips dispatch entirely if `CONFIG.events.enabled is False`.
- [ ] Structured logging at dispatch time per design doc §8.

**Acceptance**: unit tests with mocked Celery — assert correct task name, args, headers, queue per subscriber. Test the kill-switch path. Test that one failing send_task doesn't block subsequent ones.

### 2.6 Celery task wrapper (`celery_integration.py`)

- [ ] `make_subscriber_task(subscriber)`:
  - Returns a Celery task that:
    - Reads `event_id` from task headers; sets it in the worker context (mirrors existing `request_id` pattern).
    - Calls `dict_to_event(subscriber.event_type, payload)`.
    - Invokes `subscriber.func(event)`.
    - Logs start/end/latency/outcome.
  - Registered with the existing `celery_app` via the standard `@celery_app.task(name=..., queue=...)` mechanism.
- [ ] Task name format: `events.{event_class_qualname}.{subscriber_func_qualname}`.
- [ ] Boot-time validation: every registered subscriber's `task_name` must resolve to a registered Celery task. Run after autodiscovery completes; fail loudly if any subscriber is unbound.

**Acceptance**: unit tests for the wrapper (deserialization, error handling, header propagation); boot-time validation test (negative case).

### 2.7 Autodiscovery (`autodiscover.py`)

- [ ] Extend `autodiscover_task_locations` (or a parallel `autodiscover_event_subscriber_locations`) so that subscriber modules under `fides/common/events/` and any registered subscriber paths get imported at app boot. fidesplus extends this list the same way it extends Celery autodiscovery in `fidesplus/api/worker/__init__.py`.
- [ ] Both webserver and worker import subscriber modules — confirmed by a test that imports the app and asserts the registry is populated.

**Acceptance**: unit test that simulates app boot and asserts the registry contains expected subscribers.

### 2.8 Logging + `event_id` propagation

- [ ] Extend the existing `before_task_publish` / `task_prerun` / `task_postrun` signal handlers in `fides/api/tasks/__init__.py` to read/write `event_id` in task headers and propagate it into the worker's contextvar.
- [ ] Standard `logging.LoggerAdapter` (or equivalent) makes `event_id` available to subscriber logs.

**Acceptance**: integration test publishes an event, runs the subscriber inline (eager mode), and asserts the subscriber's logs include the publishing `event_id`.

### 2.9 Test helpers (`testing.py`)

- [ ] `assert_event_published(session, event_type, count=1) -> list[event_type]`:
  - Inspects `session.info.get("pending_events", [])`, filters by type, asserts the count, returns the matching event instances.
- [ ] `published_events(session) -> list`: returns all pending events for ad-hoc assertions.
- [ ] `clear_pending_events(session)`: drops pending events without dispatching (test cleanup).
- [ ] **Marker-coverage test** (added in `tests/common/events/`): walks `_PUBLISHES_MARKERS`, asserts each marked method's source contains a `publish_after_commit` call referencing the declared event type. Soft warning, not hard fail, in v1.
- [ ] **Registry-coverage test**: every registered subscriber's `event_type` has at least one `@publishes` marker in tree. Hard fail.

**Acceptance**: each helper has its own unit test; coverage tests run as part of the standard test suite.

### 2.10 Public API (`__init__.py`)

Re-export:

```python
from fides.common.events.publisher import publish_after_commit
from fides.common.events.decorators import subscribes_to, publishes
from fides.common.events.testing import (
    assert_event_published,
    published_events,
    clear_pending_events,
)
```

Internal modules (`registry`, `dispatcher`, `celery_integration`, `autodiscover`) are not re-exported. Consumers go through the public API.

## 3. End-to-end "ping" validation

The PR's primary correctness demonstration. Lives entirely under `tests/common/events/`.

### 3.1 Ping fixtures (`tests/common/events/_ping.py`)

```python
"""Test-only event + subscriber + publisher.

This module is the canonical example of how the framework is used.
It is also the end-to-end validation for the framework itself.
"""
from dataclasses import dataclass

from fides.common.events import (
    publish_after_commit,
    publishes,
    subscribes_to,
)


@dataclass(frozen=True)
class PingEvent:
    """Test-only event used to validate the framework end-to-end."""
    payload: str


# Module-level capture list — read and cleared per-test via the
# `ping_received` fixture in conftest.py.
_PING_RECEIVED: list[PingEvent] = []


@subscribes_to(PingEvent)
def ping_handler(event: PingEvent) -> None:
    """The single registered subscriber for PingEvent."""
    _PING_RECEIVED.append(event)


class PingRepository:
    """Demonstrates the recommended publish-from-repository pattern (§6.6).

    Has no DB write of its own — the ping flow only needs to demonstrate
    that publish_after_commit fires on commit and not on rollback.
    """

    def __init__(self, session):
        self.session = session

    @publishes(PingEvent)
    def emit(self, payload: str) -> None:
        publish_after_commit(self.session, PingEvent(payload=payload))
```

### 3.2 Ping conftest

```python
# tests/common/events/conftest.py
import pytest

from . import _ping  # registers ping_handler at import time


@pytest.fixture
def ping_received():
    """Yields the capture list and clears it after the test."""
    _ping._PING_RECEIVED.clear()
    yield _ping._PING_RECEIVED
    _ping._PING_RECEIVED.clear()
```

### 3.3 Ping tests (`tests/common/events/test_ping.py`)

Each test below corresponds to a specific framework guarantee. Together they validate the full lifecycle.

```python
def test_publish_then_commit_dispatches_subscriber(db, ping_received):
    """Happy path: publish + commit → subscriber runs synchronously
    (under task_always_eager) and receives the event instance."""
    _ping.PingRepository(db).emit("hello")
    db.commit()
    assert ping_received == [_ping.PingEvent(payload="hello")]


def test_publish_then_rollback_does_not_dispatch(db, ping_received):
    """Rollback safety: events queued on a rolled-back session never fire."""
    _ping.PingRepository(db).emit("hello")
    db.rollback()
    assert ping_received == []


def test_multiple_publishes_in_one_transaction_dispatch_in_order(db, ping_received):
    """Ordering: events dispatch in publish order on the same session."""
    repo = _ping.PingRepository(db)
    repo.emit("first")
    repo.emit("second")
    repo.emit("third")
    db.commit()
    assert [e.payload for e in ping_received] == ["first", "second", "third"]


def test_assert_event_published_helper(db, ping_received):
    """The assert_event_published helper inspects pending events
    pre-commit so subscriber assertions don't need to wait for dispatch."""
    _ping.PingRepository(db).emit("hello")
    [event] = assert_event_published(db, _ping.PingEvent)
    assert event.payload == "hello"


def test_kill_switch_disables_dispatch(db, ping_received, monkeypatch):
    """CONFIG.events.enabled = False stops dispatch on commit."""
    monkeypatch.setattr(CONFIG.events, "enabled", False)
    _ping.PingRepository(db).emit("hello")
    db.commit()
    assert ping_received == []


def test_publishes_marker_recorded():
    """The @publishes marker on PingRepository.emit is captured for
    test-time introspection."""
    from fides.common.events.registry import _PUBLISHES_MARKERS
    assert _ping.PingEvent in _PUBLISHES_MARKERS[_ping.PingRepository.emit]


def test_event_id_propagates_to_subscriber_logs(db, ping_received, caplog):
    """The event_id stamped at publish time appears in subscriber log records."""
    _ping.PingRepository(db).emit("hello")
    db.commit()
    publish_records = [r for r in caplog.records if "event_id" in getattr(r, "extra", {})]
    assert publish_records  # at least one log record carried event_id
    # Subscriber log records should carry the same event_id
    handle_records = [r for r in caplog.records if "ping_handler" in r.message]
    assert all(r.extra["event_id"] == publish_records[0].extra["event_id"] for r in handle_records)
```

### 3.4 What the ping suite does NOT cover (intentionally)

- Multi-subscriber fan-out — covered separately by `test_dispatch_to_multiple_subscribers` in `test_dispatcher.py`. Ping has one subscriber to keep the canonical example minimal.
- Reconciler behavior — Phase 1 has no reconciler; reconcilers land with subscribers in Phase 2/3.
- Cross-process Celery dispatch — relies on `task_always_eager`. Worker-side correctness is covered by component tests in `test_celery_integration.py`.

## 4. Coverage checks — pattern

All three coverage checks below run as test-time assertions, not runtime errors. Each supports a deliberate opt-out via a module-level exclude list with a required string reason. The pattern (sketch):

```python
# tests/common/events/coverage_excludes.py

# Event types deliberately published without a registered subscriber.
# Each entry must be justified.
PUBLISH_WITHOUT_SUBSCRIBER_OK: dict[type, str] = {
    # ExampleEvent: "first-publisher landing ahead of subscriber in PR #1234",
}

# Methods that call publish_after_commit deliberately without a @publishes marker.
PUBLISH_WITHOUT_MARKER_OK: dict[Callable, str] = {
    # SomeRepo.legacy_method: "marker added in follow-up; tracked in ENG-9999",
}
```

A test exempting an entry without a reason fails. The exclude lists live in test code (not framework code), keeping the framework strict by default.

### 4.1 Publish-target coverage (typo check)

- Walks every `publish_after_commit` call site detected by static analysis (or by an instrumentation hook in tests).
- Asserts `type(event)` is in the registry for that test session.
- **Opt-out** via `PUBLISH_WITHOUT_SUBSCRIBER_OK` for the deliberate first-publisher-without-subscriber case.
- **Runtime behavior**: `publish_after_commit` itself is permissive — logs a warning if the event type has no subscribers but does not raise. Catching the typo is the test suite's job, not the request path's.

### 4.2 `@publishes` marker coverage (soft)

- Walks every method that calls `publish_after_commit` (detected via the same instrumentation as 4.1).
- Asserts the method has a `@publishes(EventType)` marker for each event type it publishes.
- **Opt-out** via `PUBLISH_WITHOUT_MARKER_OK`.
- Failure mode: test failure with a message pointing at the missing marker and instructions to either add it or add an exemption with reason.

### 4.3 Subscriber → publisher coverage (hard)

- Walks every registered subscriber.
- Asserts the subscriber's event type has at least one in-tree publisher (either a `@publishes` marker or a detected `publish_after_commit` call).
- **No opt-out** — a subscriber without a publisher is a dead subscriber.
- Failure mode: test failure listing the orphaned subscriber and its event type.

## 5. Out of scope (deferred)

- Production publishers / subscribers (Phase 2 + 3).
- Metrics emission — logging only in v1.
- A second transport (Redis Pub/Sub, Postgres, etc.) — see design doc §5.5.
- Schema versioning / event payload migration.
- Operator-facing tooling (event replay, dead-letter inspection) — substituted by the per-subscriber reconciler model.
- Helm or compose changes — none required.

## 6. Acceptance criteria

- Single PR merged to fides main.
- All tests under `tests/common/events/` green, including the ping suite.
- Marker- and registry-coverage tests in place.
- No production code paths reference `fides.common.events` outside the test ping module.
- This doc + design doc + implementation plan all merged.
- `CONFIG.events.enabled` toggle exercised by tests.
- A short developer-facing how-to (linked from `dev-docs/`) showing the ping pattern as the canonical reference, with a note that production publishers + subscribers will come in subsequent phases.
