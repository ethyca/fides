from typing import List

from pydantic import Field

from fides.api.schemas.base_class import FidesSchema


class QueueStats(FidesSchema):
    """Statistics for a single queue."""

    queue_name: str = Field(..., description="Logical Celery queue name")
    available: int = Field(..., description="Messages ready to be consumed")
    delayed: int = Field(..., description="Messages scheduled for future delivery")
    in_flight: int = Field(..., description="Messages being processed by workers")


class QueueMonitorResponse(FidesSchema):
    """Response from the queue monitor endpoint."""

    sqs_enabled: bool = Field(..., description="Whether SQS queue mode is enabled")
    queues: List[QueueStats] = Field(
        default_factory=list, description="Per-queue statistics"
    )
