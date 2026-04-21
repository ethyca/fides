from typing import List, Union

from fastapi import APIRouter, Response, Security
from starlette.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.queue_monitor import QueueMonitorResponse, QueueStats
from fides.api.tasks.broker import get_all_celery_queue_names
from fides.api.util.queue_stats import SQSQueueStatsProvider
from fides.common.urn_registry import V1_URL_PREFIX
from fides.config import CONFIG

router = APIRouter(tags=["Queue Monitor"], prefix=V1_URL_PREFIX)


@router.get(
    "/queue-monitor",
    dependencies=[Security(verify_oauth_client, scopes=[])],
    status_code=HTTP_200_OK,
    response_model=QueueMonitorResponse,
)
def get_queue_monitor() -> Union[QueueMonitorResponse, Response]:
    """Get per-queue message statistics.

    Returns SQS queue statistics (available, delayed, in-flight) for each
    known Celery queue when the backend is configured to use SQS.
    """
    if not CONFIG.queue.use_sqs_queue:
        return QueueMonitorResponse(sqs_enabled=False, queues=[])

    provider = SQSQueueStatsProvider(CONFIG)

    queues: List[QueueStats] = []

    try:
        for queue_name in get_all_celery_queue_names():
            attrs = provider.get_queue_attributes(queue_name)
            queues.append(
                QueueStats(
                    queue_name=queue_name,
                    available=attrs["available"],
                    delayed=attrs["delayed"],
                    in_flight=attrs["in_flight"],
                )
            )
    except Exception:
        # Auth / credential errors from any queue become a 503 with empty body
        return Response(status_code=HTTP_503_SERVICE_UNAVAILABLE)

    return QueueMonitorResponse(sqs_enabled=True, queues=queues)
