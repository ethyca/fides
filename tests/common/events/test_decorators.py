"""Unit tests for @subscribes_to and @publishes."""

from dataclasses import dataclass

import pytest

from fides.common.events import publishes, subscribes_to
from fides.common.events.base import InvalidEventTypeError
from fides.common.events.celery_integration import is_subscriber_task_registered
from fides.common.events.registry import (
    Subscriber,
    get_publishes_markers,
    get_subscribers,
)


@dataclass(frozen=True)
class _DecoratorTestEvent:
    value: str


def test_subscribes_to_registers_subscriber_and_creates_celery_task() -> None:
    @subscribes_to(_DecoratorTestEvent)
    def handler(event: _DecoratorTestEvent) -> None:
        pass

    subs = get_subscribers(_DecoratorTestEvent)
    assert any(s.func is handler for s in subs)

    # The Celery task wrapper is registered.
    [sub] = [s for s in subs if s.func is handler]
    assert is_subscriber_task_registered(sub.task_name)


def test_subscribes_to_returns_original_function() -> None:
    @subscribes_to(_DecoratorTestEvent)
    def handler(event: _DecoratorTestEvent) -> None:
        return None

    # Direct callability preserved.
    handler(_DecoratorTestEvent(value="x"))


def test_subscribes_to_rejects_invalid_event_class() -> None:
    @dataclass  # not frozen
    class Bad:
        x: int

    with pytest.raises(InvalidEventTypeError):

        @subscribes_to(Bad)
        def _h(event):  # pragma: no cover - never reached
            pass


def test_subscribes_to_supports_multiple_subscribers_per_event() -> None:
    @dataclass(frozen=True)
    class MultiSubEvent:
        v: int

    @subscribes_to(MultiSubEvent)
    def first(event: MultiSubEvent) -> None:
        pass

    @subscribes_to(MultiSubEvent)
    def second(event: MultiSubEvent) -> None:
        pass

    subs = get_subscribers(MultiSubEvent)
    funcs = {s.func for s in subs}
    assert {first, second}.issubset(funcs)


def test_subscribes_to_default_queue_is_fides() -> None:
    @dataclass(frozen=True)
    class DefaultQueueEvent:
        v: int

    @subscribes_to(DefaultQueueEvent)
    def handler(event: DefaultQueueEvent) -> None:
        pass

    [sub] = [s for s in get_subscribers(DefaultQueueEvent) if s.func is handler]
    assert sub.queue == "fides"


def test_subscribes_to_queue_override() -> None:
    @dataclass(frozen=True)
    class CustomQueueEvent:
        v: int

    @subscribes_to(CustomQueueEvent, queue="my.custom.queue")
    def handler(event: CustomQueueEvent) -> None:
        pass

    [sub] = [s for s in get_subscribers(CustomQueueEvent) if s.func is handler]
    assert sub.queue == "my.custom.queue"


def test_publishes_marker_records_event_types() -> None:
    @dataclass(frozen=True)
    class MarkerTestEvent:
        v: int

    @publishes(MarkerTestEvent)
    def some_method(self):  # pragma: no cover - never invoked
        pass

    markers = get_publishes_markers()
    assert some_method in markers
    assert MarkerTestEvent in markers[some_method]


def test_publishes_marker_returns_original_function() -> None:
    @dataclass(frozen=True)
    class MarkerEvent:
        v: int

    def original():
        return 42

    decorated = publishes(MarkerEvent)(original)
    assert decorated is original
    assert decorated() == 42


def test_publishes_marker_rejects_invalid_event_class() -> None:
    @dataclass  # not frozen
    class Bad:
        x: int

    with pytest.raises(InvalidEventTypeError):
        publishes(Bad)
