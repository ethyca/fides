from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .fides_settings import FidesSettings


class EventSettings(FidesSettings):
    """Configuration settings for the in-application event framework.

    See `docs/fides/docs/event-framework/01-design.md` for the design.
    """

    enabled: bool = Field(
        default=True,
        description=(
            "Master kill switch for event dispatch. When False, "
            "publish_after_commit becomes a no-op (events are still queued "
            "on the session for test introspection but never dispatched). "
            "Useful for incidents and for tests that don't want events firing."
        ),
    )

    model_config = SettingsConfigDict(env_prefix="FIDES__EVENTS__")
