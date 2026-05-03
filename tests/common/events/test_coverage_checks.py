"""Coverage checks for the event framework registry.

In v1 only the "subscriber has a publisher" check is implemented (hard fail).
Static-analysis-based checks for ``publish_after_commit`` call sites
(publish-target coverage and @publishes marker coverage from the design doc)
are deferred until production subscribers exist that would benefit from them.

See ``docs/fides/docs/event-framework/03-phase-1-plumbing.md`` §4.
"""

from fides.common.events.registry import (
    all_subscribers,
    get_publishes_markers,
)

from .coverage_excludes import SUBSCRIBER_WITHOUT_PUBLISHER_OK


def _is_test_event(event_type: type) -> bool:
    """True if ``event_type`` is defined in test code rather than production.

    Test-defined events are created inside test fixtures, helpers, or test
    bodies and have no production publishers by design — checking them
    against the production publisher registry would always fail.

    Detection:
    - Module path starts with ``tests.`` (test fixture event).
    - Qualified name contains ``<locals>`` (event defined inside a function
      body, e.g. local @dataclass inside a test).
    """
    return (
        event_type.__module__.startswith("tests.")
        or "<locals>" in event_type.__qualname__
    )


def test_every_production_subscriber_has_an_in_tree_publisher() -> None:
    """Hard fail: every registered subscriber's event type must have at
    least one ``@publishes`` marker somewhere in the codebase, unless the
    event type is explicitly exempted via ``SUBSCRIBER_WITHOUT_PUBLISHER_OK``.

    A subscriber without a publisher is a dead subscriber — either it was
    forgotten when the publisher was removed, or its event type is a typo.
    """
    markers = get_publishes_markers()
    published_types = {
        event_type for events in markers.values() for event_type in events
    }

    orphans = []
    for subscriber in all_subscribers():
        if _is_test_event(subscriber.event_type):
            continue
        if subscriber.event_type in SUBSCRIBER_WITHOUT_PUBLISHER_OK:
            continue
        if subscriber.event_type not in published_types:
            orphans.append((subscriber.task_name, subscriber.event_type.__qualname__))

    assert not orphans, (
        "Subscribers without an in-tree @publishes marker: "
        f"{orphans}. Either add a @publishes marker on a publisher method, "
        "or add the event type to SUBSCRIBER_WITHOUT_PUBLISHER_OK with a "
        "documented reason."
    )
