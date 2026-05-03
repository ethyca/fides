"""Deliberate exemptions from the coverage tests in test_coverage_checks.py.

Each entry must include a documented reason. Exemptions are reviewed during
PR review and should be temporary — the framework's correctness contract is
strongest when these lists are empty.

See ``docs/fides/docs/event-framework/03-phase-1-plumbing.md`` §4.
"""

from typing import Dict, Type

# Event types deliberately published without a registered subscriber.
# Use case: a publisher lands in one PR ahead of the subscriber that will
# consume it. Removed once the subscriber lands.
PUBLISH_WITHOUT_SUBSCRIBER_OK: Dict[Type, str] = {
    # ExampleEvent: "subscriber lands in PR #1234",
}

# Subscribers without an in-tree publisher.
# Should remain empty in healthy repos — a subscriber with no publisher is a
# dead subscriber. The only legitimate use is during a transition (e.g. while
# a publisher is being moved between repos).
SUBSCRIBER_WITHOUT_PUBLISHER_OK: Dict[Type, str] = {
    # OrphanEvent: "transitioning from external publisher; tracked in ENG-9999",
}
