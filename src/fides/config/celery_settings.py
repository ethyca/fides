from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__CELERY__"


class CelerySettings(FidesSettings):
    """Configuration settings for Celery.  Only a small subset can be configured through Fides env vars"""

    event_queue_prefix: str = Field(
        default="fides_worker",
        description="The prefix to use for event receiver queue names",
    )
    task_default_queue: str = Field(
        default="fides",
        description="The name of the default queue if a message has no route or no custom queue has been specified",
    )
    task_always_eager: bool = Field(
        default=True,
        description="If true, tasks are executed locally instead of being sent to the queue.  "
        "If False, tasks are sent to the queue.",
    )
    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX)
