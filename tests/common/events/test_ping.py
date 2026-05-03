"""End-to-end validation of the event framework via the ping fixtures.

Each test corresponds to a specific framework guarantee. Together they
demonstrate the full lifecycle: publish → commit → dispatch → handle,
and the rollback / kill-switch / event_id-propagation paths.
"""

import pytest

from fides.common.events import assert_event_published
from fides.config import CONFIG

from . import _ping


def test_publish_then_commit_dispatches_subscriber(session, ping_received):
    """Happy path: publish + commit → subscriber runs synchronously
    (under task_always_eager) and receives the event instance."""
    _ping.PingRepository(session).emit("hello")
    session.commit()

    assert len(ping_received) == 1
    event, _event_id = ping_received[0]
    assert event == _ping.PingEvent(payload="hello")


def test_publish_then_rollback_does_not_dispatch(session, ping_received):
    """Rollback safety: events queued on a rolled-back session never fire."""
    _ping.PingRepository(session).emit("hello")
    session.rollback()

    assert ping_received == []


def test_multiple_publishes_in_one_transaction_dispatch_in_order(
    session, ping_received
):
    """Ordering: events dispatch in publish order on the same session."""
    repo = _ping.PingRepository(session)
    repo.emit("first")
    repo.emit("second")
    repo.emit("third")
    session.commit()

    assert [event.payload for event, _ in ping_received] == [
        "first",
        "second",
        "third",
    ]


def test_assert_event_published_helper_inspects_pre_commit(session, ping_received):
    """The assert_event_published helper inspects pending events
    pre-commit so subscriber assertions don't need to wait for dispatch."""
    _ping.PingRepository(session).emit("hello")

    [event] = assert_event_published(session, _ping.PingEvent)
    assert event.payload == "hello"
    # Subscriber has not yet run — we haven't committed.
    assert ping_received == []


def test_kill_switch_disables_dispatch(session, ping_received, monkeypatch):
    """CONFIG.events.enabled = False stops dispatch on commit."""
    monkeypatch.setattr(CONFIG.events, "enabled", False)

    _ping.PingRepository(session).emit("hello")
    session.commit()

    assert ping_received == []


def test_publishes_marker_recorded_for_emit_method():
    """The @publishes marker on PingRepository.emit is captured for
    test-time introspection."""
    from fides.common.events.registry import get_publishes_markers

    markers = get_publishes_markers()
    assert _ping.PingRepository.emit in markers
    assert _ping.PingEvent in markers[_ping.PingRepository.emit]


def test_event_id_returned_from_publish_is_observed_by_subscriber(
    session, ping_received
):
    """The event_id generated at publish time is the same one the
    subscriber sees via get_current_event_id() during handling."""
    published_event_id = _ping.PingRepository(session).emit("hello")
    session.commit()

    assert len(ping_received) == 1
    _event, observed_event_id = ping_received[0]
    # In eager mode with task_prerun firing, the subscriber should see the
    # same event_id that publish_after_commit returned.
    assert observed_event_id == published_event_id


def test_publishing_with_no_subscriber_logs_warning_but_does_not_raise(
    session, ping_received
):
    """An event class with no registered subscribers logs a warning at
    dispatch time but does not raise. Establishes the framework's
    permissive runtime stance — typo-checking lives in coverage tests."""
    from dataclasses import dataclass

    from fides.common.events import publish_after_commit

    @dataclass(frozen=True)
    class OrphanEvent:
        value: str

    publish_after_commit(session, OrphanEvent(value="lonely"))
    session.commit()

    # Subscriber for PingEvent did not fire — different event type.
    assert ping_received == []
