import json
import os
from json import JSONDecodeError
from typing import Any, Dict

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


def merge_celery_environment(celery_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Given a dict of config settings, merges configs which are found
    in environment variables. Environment variable configs are treated
    as overrides. Environment variables must use the prefix FIDES__CELERY__.

    Example:
        FIDES__CELERY__WORKER_PREFETCH_MULTIPLIER=4

    Merges to:
        {"worker_prefetch_multiplier": 4}

    This allows arbitrary Celery configuration to be set via environment variables,
    not just the explicitly defined fields in CelerySettings.
    """
    for key, value in os.environ.items():
        if key.startswith(ENV_PREFIX):
            # Strip the prefix and convert to lowercase
            stripped_key = key[len(ENV_PREFIX) :].lower()
            if stripped_key:
                # Normalize boolean strings only to preserve case-sensitive values
                # like URLs (e.g., Redis://myhost) or passwords
                normalized_value = value
                if value.lower() in ("true", "false"):
                    normalized_value = value.lower()

                # Use JSON parsing to handle type conversion properly
                # This handles booleans (true/false), integers, floats, etc.
                try:
                    celery_dict[stripped_key] = json.loads(normalized_value)
                except (JSONDecodeError, ValueError):
                    # If JSON parsing fails, keep it as a string
                    celery_dict[stripped_key] = value

    return celery_dict
