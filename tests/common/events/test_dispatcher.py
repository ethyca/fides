"""Unit tests for the dispatcher: kill switch, error handling, multi-subscriber fan-out."""

from dataclasses import dataclass
from unittest.mock import patch

import pytest

from fides.common.events import publish_after_commit, subscribes_to
from fides.common.events.dispatcher import dispatch
from fides.config import CONFIG


@dataclass(frozen=True)
class _DispatchEvent:
    label: str


_FIRST: list = []
_SECOND: list = []


@subscribes_to(_DispatchEvent)
def _first_handler(event: _DispatchEvent) -> None:
    _FIRST.append(event)


@subscribes_to(_DispatchEvent)
def _second_handler(event: _DispatchEvent) -> None:
    _SECOND.append(event)


@pytest.fixture(autouse=True)
def _reset_received():
    _FIRST.clear()
    _SECOND.clear()
    yield
    _FIRST.clear()
    _SECOND.clear()


def test_dispatch_fans_out_to_all_subscribers(session) -> None:
    publish_after_commit(session, _DispatchEvent(label="hi"))
    session.commit()

    assert len(_FIRST) == 1
    assert len(_SECOND) == 1
    assert _FIRST[0].label == _SECOND[0].label == "hi"


def test_kill_switch_skips_dispatch_entirely(session, monkeypatch) -> None:
    monkeypatch.setattr(CONFIG.events, "enabled", False)

    publish_after_commit(session, _DispatchEvent(label="muted"))
    session.commit()

    assert _FIRST == []
    assert _SECOND == []


def test_dispatch_failure_in_one_subscriber_does_not_block_others() -> None:
    """If apply_async raises for one subscriber, the dispatcher
    logs and proceeds to the next subscriber."""
    from fides.api.tasks import celery_app

    call_log: list = []
    # Capture both task objects up-front so we can wire a flaky wrapper.
    subs = sorted(
        [
            celery_app.tasks[name]
            for name in celery_app.tasks
            if "_DispatchEvent" in name
        ],
        key=lambda t: t.name,
    )
    assert len(subs) == 2, f"Expected 2 _DispatchEvent subscribers, got {len(subs)}"

    real_first_apply = subs[0].apply_async

    def flaky_first_apply(*args, **kwargs):
        call_log.append(subs[0].name)
        raise RuntimeError("simulated broker failure")

    real_second_apply = subs[1].apply_async

    def tracking_second_apply(*args, **kwargs):
        call_log.append(subs[1].name)
        return real_second_apply(*args, **kwargs)

    with (
        patch.object(subs[0], "apply_async", side_effect=flaky_first_apply),
        patch.object(subs[1], "apply_async", side_effect=tracking_second_apply),
    ):
        dispatch("event-id-1", _DispatchEvent(label="resilience"))

    # Both subscribers were attempted; one failed (raised), one succeeded.
    assert len(call_log) == 2
    # The successful one ran its handler.
    successful_capture = _FIRST if _SECOND == [] else _SECOND
    assert len(successful_capture) == 1
