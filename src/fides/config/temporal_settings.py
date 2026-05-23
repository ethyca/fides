from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__TEMPORAL__"


class TemporalSettings(FidesSettings):
    """Configuration settings for the Temporal workflow engine."""

    server_url: str = Field(
        default="localhost:7233",
        description="Temporal server gRPC address.",
    )
    namespace: str = Field(
        default="default",
        description="Temporal namespace for DSR workflows.",
    )
    task_queue: str = Field(
        default="fides-dsr",
        description="Task queue name for DSR workflow workers.",
    )
    worker_count: int = Field(
        default=2,
        description="Number of concurrent workflow/activity workers.",
    )

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)
