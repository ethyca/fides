"""Test-only event + subscriber + publisher.

This module is the canonical example of how the event framework is used
end-to-end. It is also the primary correctness validation for the framework
itself — see ``test_ping.py``.

Importing this module has the side effect of registering ``ping_handler``
as a subscriber for ``PingEvent``. Tests that need a clean registry
(e.g. ``test_registry.py``) reset state via ``registry._reset_for_tests``.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from fides.common.events import (
    get_current_event_id,
    publish_after_commit,
    publishes,
    subscribes_to,
)


@dataclass(frozen=True)
class PingEvent:
    """Test-only event used to validate the framework end-to-end."""

    payload: str


# Module-level capture list — read and cleared per test via the
# ``ping_received`` fixture in conftest.py. Each entry is a tuple of
# (event, current event_id observed by the subscriber).
_PING_RECEIVED: List[Tuple[PingEvent, Optional[str]]] = []


@subscribes_to(PingEvent)
def ping_handler(event: PingEvent) -> None:
    """The single registered subscriber for PingEvent."""
    _PING_RECEIVED.append((event, get_current_event_id()))


class PingRepository:
    """Demonstrates the recommended publish-from-repository pattern (§6.6).

    Has no DB write of its own — the ping flow only needs to demonstrate
    that publish_after_commit fires on commit and not on rollback.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    @publishes(PingEvent)
    def emit(self, payload: str) -> str:
        """Queue a PingEvent on the session. Returns the generated event_id."""
        return publish_after_commit(self.session, PingEvent(payload=payload))
