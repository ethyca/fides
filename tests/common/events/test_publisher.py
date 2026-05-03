"""Unit tests for publish_after_commit + session lifecycle behavior."""

from dataclasses import dataclass

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fides.common.events import (
    assert_event_published,
    clear_pending_events,
    publish_after_commit,
    published_events,
    subscribes_to,
)


@dataclass(frozen=True)
class _PubEvent:
    n: int


_RECEIVED: list = []


@subscribes_to(_PubEvent)
def _handler(event: _PubEvent) -> None:
    _RECEIVED.append(event)


@pytest.fixture(autouse=True)
def _reset_received():
    _RECEIVED.clear()
    yield
    _RECEIVED.clear()


def _new_session():
    engine = create_engine("sqlite:///:memory:")
    return sessionmaker(bind=engine)()


def test_publish_after_commit_returns_event_id(session) -> None:
    event_id = publish_after_commit(session, _PubEvent(n=1))
    assert isinstance(event_id, str) and len(event_id) > 0


def test_publish_after_commit_does_not_dispatch_until_commit(session) -> None:
    publish_after_commit(session, _PubEvent(n=1))
    assert _RECEIVED == []
    session.commit()
    assert len(_RECEIVED) == 1


def test_two_sessions_are_isolated() -> None:
    """An event published on session A does not fire when session B commits."""
    a = _new_session()
    b = _new_session()
    try:
        publish_after_commit(a, _PubEvent(n=1))
        b.commit()
        assert _RECEIVED == []
        a.commit()
        assert len(_RECEIVED) == 1
    finally:
        a.close()
        b.close()


def test_published_events_helper_returns_queued(session) -> None:
    publish_after_commit(session, _PubEvent(n=1))
    publish_after_commit(session, _PubEvent(n=2))

    queued = published_events(session)
    assert [e.n for e in queued if isinstance(e, _PubEvent)] == [1, 2]


def test_assert_event_published_count_constraint(session) -> None:
    publish_after_commit(session, _PubEvent(n=1))
    publish_after_commit(session, _PubEvent(n=2))

    matches = assert_event_published(session, _PubEvent, count=2)
    assert [e.n for e in matches] == [1, 2]


def test_assert_event_published_count_mismatch_fails(session) -> None:
    publish_after_commit(session, _PubEvent(n=1))

    with pytest.raises(AssertionError):
        assert_event_published(session, _PubEvent, count=2)


def test_clear_pending_events_drops_queued_without_dispatching(session) -> None:
    publish_after_commit(session, _PubEvent(n=1))
    clear_pending_events(session)
    session.commit()

    assert _RECEIVED == []


def test_callbacks_installed_only_once_per_session(session) -> None:
    """Multiple publishes on the same session don't double-fire on commit."""
    publish_after_commit(session, _PubEvent(n=1))
    publish_after_commit(session, _PubEvent(n=2))
    publish_after_commit(session, _PubEvent(n=3))

    session.commit()

    assert [e.n for e in _RECEIVED] == [1, 2, 3]


def test_post_commit_pending_events_are_drained(session) -> None:
    """After commit, the pending list is empty so a subsequent publish
    on the same session works correctly."""
    publish_after_commit(session, _PubEvent(n=1))
    session.commit()
    assert len(_RECEIVED) == 1

    publish_after_commit(session, _PubEvent(n=2))
    session.commit()
    assert [e.n for e in _RECEIVED] == [1, 2]
