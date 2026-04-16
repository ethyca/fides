from typing import Optional

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from .fides_settings import FidesSettings


class QueueSettings(FidesSettings):
    """Configuration settings for the task queue."""

    use_sqs_queue: bool = Field(
        default=False,
        description="Whether to use SQS instead of Redis for the celery queue.",
    )
    sqs_url: Optional[str] = Field(
        default=None,
        description="The URL for the SQS queue or ElasticMQ instance.",
    )
    aws_region: str = Field(
        default="us-east-1",
        description="The AWS region for SQS.",
    )
    aws_access_key_id: Optional[str] = Field(
        default=None,
        description="The AWS access key ID for SQS. Overrides default boto3 chain.",
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None,
        description="The AWS secret access key for SQS. Overrides default boto3 chain.",
    )
    sqs_queue_name_prefix: str = Field(
        default="ethyca-",
        description="The prefix to apply to SQS queue names.",
    )

    model_config = SettingsConfigDict(env_prefix="FIDES__QUEUE__")
