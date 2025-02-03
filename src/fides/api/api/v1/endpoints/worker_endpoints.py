from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Security
from loguru import logger
from starlette.status import HTTP_200_OK
from celery.app.control import Inspect
from fides.api.oauth.utils import verify_oauth_client
from fides.api.schemas.worker import QueueInfo, TaskDetails, WorkerInfo, WorkerStats
from fides.api.tasks import celery_app
from fides.api.util.api_router import APIRouter
from fides.api.util.cache import get_queue_counts
from fides.common.api.v1.urn_registry import V1_URL_PREFIX

router = APIRouter(tags=["Worker Stats"], prefix=V1_URL_PREFIX)


@router.get(
    "/worker-stats",
    dependencies=[Security(verify_oauth_client)],
    status_code=HTTP_200_OK,
    response_model=WorkerStats,
)
async def get_worker_stats() -> WorkerStats:
    """Get statistics about Celery queues and workers.

    Returns information about task queues and worker states in the Celery system:
    - Queue statistics: Number of pending tasks in each Redis-backed queue
    - Worker statistics: Current state of each Celery worker including:
        - Active task: Currently executing task, if any
        - Reserved tasks: Tasks reserved by a worker but not yet started
        - Registered tasks: Tasks this worker is configured to accept
    """

    try:
        return WorkerStats(queues=get_queue_info(), workers=get_worker_info())
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting worker stats: {str(e)}"
        )


def get_queue_info() -> Dict[str, QueueInfo]:
    """Return information about queue sizes"""
    return {
        queue_name: QueueInfo(messages=count)
        for queue_name, count in get_queue_counts().items()
    }


def get_worker_info() -> Dict[str, WorkerInfo]:
    inspector: Inspect = celery_app.control.inspect()
    active = inspector.active() or {}
    reserved = inspector.reserved() or {}

    workers = {}

    # Process active tasks
    for worker_name, tasks in active.items():
        current_task = None
        if tasks:
            current_task = TaskDetails.from_celery_task(tasks[0], state="started")
        workers[worker_name] = WorkerInfo(active_task=current_task, reserved_tasks=[])

    # Process reserved tasks
    for worker_name, tasks in reserved.items():
        if worker_name not in workers:  # new worker we haven't seen
            workers[worker_name] = WorkerInfo(active_task=None, reserved_tasks=[])

        if tasks:
            reserved_tasks = [
                TaskDetails.from_celery_task(task, state="received") for task in tasks
            ]
            workers[worker_name].reserved_tasks = reserved_tasks

    for worker_name, registered_tasks in inspector.registered().items():
        workers[worker_name].registered_tasks = registered_tasks

    return workers
