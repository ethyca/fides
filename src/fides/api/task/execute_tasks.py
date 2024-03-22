from typing import Callable, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Query, Session

from fides.api.common_exceptions import PrivacyRequestNotFound, RequestTaskNotFound
from fides.api.graph.config import (
    ROOT_COLLECTION_ADDRESS,
    TERMINATOR_ADDRESS,
    CollectionAddress,
)
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.policy import CurrentStep
from fides.api.models.privacy_request import (
    PrivacyRequest,
    PrivacyRequestStatus,
    RequestTask,
    TaskStatus,
)
from fides.api.models.sql_models import System  # type: ignore[attr-defined]
from fides.api.task.graph_task import GraphTask
from fides.api.task.task_resources import TaskResources
from fides.api.tasks import DatabaseTask, celery_app
from fides.api.util.collection_util import Row


def order_tasks_by_input_key(
    input_keys: List[CollectionAddress], upstream_tasks: Query
) -> List[Optional[RequestTask]]:
    """Order tasks by input key. If task doesn't exist, add None in its place"""
    tasks: List[Optional[RequestTask]] = []
    for key in input_keys:
        task = next(
            (
                upstream
                for upstream in upstream_tasks
                if upstream.collection_address == key.value
            ),
            None,
        )
        tasks.append(task)
    return tasks


def get_task_resources(session: Session, privacy_request: PrivacyRequest):
    return TaskResources(
        privacy_request,
        privacy_request.policy,
        session.query(ConnectionConfig).all(),
        session,
    )


def upfront_checks(session, privacy_request_id, privacy_request_task_id):
    privacy_request: PrivacyRequest = PrivacyRequest.get(
        db=session, object_id=privacy_request_id
    )
    request_task: RequestTask = RequestTask.get(
        db=session, object_id=privacy_request_task_id
    )

    if not privacy_request:
        raise PrivacyRequestNotFound(
            f"Privacy request with id {privacy_request_id} not found"
        )

    if not request_task:
        raise RequestTaskNotFound(f"Request Task with id {request_task} not found")

    upstream_results = session.query(RequestTask).filter(False)
    if request_task.status == TaskStatus.pending:
        upstream_results: Query = session.query(RequestTask).filter(
            RequestTask.privacy_request_id == privacy_request_id,
            RequestTask.status == PrivacyRequestStatus.complete,
            RequestTask.action_type == request_task.action_type,
            RequestTask.collection_address.in_(request_task.upstream_tasks),
        )

        if not upstream_results.count() == len(request_task.upstream_tasks):
            raise RequestTaskNotFound(
                f"Cannot start Privacy Request Task {request_task.id} - status is {request_task.status}"
            )
    return privacy_request, request_task, upstream_results


@celery_app.task(base=DatabaseTask, bind=True)
def run_access_node(
    self: DatabaseTask, privacy_request_id: str, privacy_request_task_id: str
) -> None:
    with self.get_new_session() as session:
        privacy_request, request_task, upstream_results = upfront_checks(
            session, privacy_request_id, privacy_request_task_id
        )

        graph_task_key = CollectionAddress.from_string(request_task.collection_address)

        if request_task.status != TaskStatus.pending:
            logger.info(
                f"Cannot start access Privacy Request Task {request_task.id} {request_task.collection_address} - status is {request_task.status}"
            )
            return

        task_resources = get_task_resources(session, privacy_request)

        logger.info(
            f"Running access request task {request_task.id}:{request_task.collection_address} for privacy request {privacy_request.id}"
        )

        if graph_task_key == TERMINATOR_ADDRESS:
            # For the terminator node, collect all of the results
            final_results: Dict = {}
            for task in privacy_request.access_tasks.filter(
                RequestTask.status == PrivacyRequestStatus.complete,
                RequestTask.collection_address.notin_(
                    [ROOT_COLLECTION_ADDRESS.value, TERMINATOR_ADDRESS.value]
                ),
            ):
                final_results[task.collection_address] = task.access_data

            request_task.terminator_data = final_results
        else:
            # For regular nodes, store the data on the node
            graph_task: GraphTask = GraphTask(request_task, task_resources)
            func = graph_task.access_request
            ordered_upstream_tasks = order_tasks_by_input_key(
                graph_task.execution_node.input_keys, upstream_results
            )
            # Put access data in the same order as the input keys
            func(
                *[
                    upstream.access_data if upstream else []
                    for upstream in ordered_upstream_tasks
                ]
            )

        request_task.status = TaskStatus.complete
        request_task.save(session)

        # If there are other downstream tasks that are ready to go, queue those now
        pending_downstream_tasks: Query = request_task.pending_downstream_tasks(session)
        for downstream_task in pending_downstream_tasks:
            if downstream_task.upstream_tasks_complete(session):
                logger.info(f"Upstream tasks complete so queuing {downstream_task.id}")
                run_access_node.delay(
                    privacy_request_id=privacy_request_id,
                    privacy_request_task_id=downstream_task.id,
                )
            else:
                logger.info(f"Upstream tasks not completed for {downstream_task.id}")

        # If we've made it to the terminator node, requeue the entire Privacy request to continue where we left off,
        # by uploading the current access results.
        if graph_task_key == TERMINATOR_ADDRESS:
            from fides.api.service.privacy_request.request_runner_service import (
                queue_privacy_request,
            )

            queue_privacy_request(
                privacy_request_id=privacy_request.id,
                from_step=CurrentStep.upload_access.value,
            )


@celery_app.task(base=DatabaseTask, bind=True)
def run_erasure_node(
    self: DatabaseTask, privacy_request_id: str, privacy_request_task_id: str
) -> None:
    with self.get_new_session() as session:
        privacy_request, request_task, upstream_results = upfront_checks(
            session, privacy_request_id, privacy_request_task_id
        )
        graph_task_key = CollectionAddress.from_string(request_task.collection_address)

        if request_task.status == TaskStatus.complete:
            logger.info(
                f"Cannot start erasure Privacy Request Task {request_task.id} {request_task.collection_address} - status is {request_task.status}"
            )
            return

        task_resources = get_task_resources(session, privacy_request)

        logger.info(
            f"Running erasure task {request_task.collection_address}:{request_task.id} for privacy request {privacy_request.id}"
        )

        if graph_task_key != TERMINATOR_ADDRESS:
            graph_task: GraphTask = GraphTask(request_task, task_resources)
            func: Callable = graph_task.erasure_request
            retrieved_data: List[Row] = request_task.data_for_erasures or []
            inputs: List[List[Row]] = request_task.erasure_input_data or []
            func(retrieved_data, inputs)
            request_task.status = TaskStatus.complete
            request_task.save(session)
            logger.info(f"Marking node {graph_task_key} as complete")

        else:
            request_task.status = TaskStatus.complete
            request_task.save(session)
            logger.info(f"Marking node {graph_task_key} as complete")

            from fides.api.service.privacy_request.request_runner_service import (
                queue_privacy_request,
            )

            logger.info(
                f"Terminator node reached for erasure graph of {privacy_request.id}. Queueing."
            )

            queue_privacy_request(
                privacy_request_id=privacy_request.id,
                from_step=CurrentStep.finalize_erasure.value,
            )
            return

        # If there are other downstream tasks that are ready to go, queue those now
        pending_downstream_tasks: Query = request_task.pending_downstream_tasks(session)
        for downstream_task in pending_downstream_tasks:
            if downstream_task.upstream_tasks_complete(session):
                logger.info(f"Upstream tasks complete so queuing {downstream_task.id}")
                run_erasure_node.delay(
                    privacy_request_id=privacy_request_id,
                    privacy_request_task_id=downstream_task.id,
                )
            else:
                logger.info(
                    f"Upstream tasks not completed for {downstream_task.collection_address} {downstream_task.id}"
                )


@celery_app.task(base=DatabaseTask, bind=True)
def run_consent_node(
    self: DatabaseTask, privacy_request_id: str, privacy_request_task_id: str
) -> None:
    with self.get_new_session() as session:
        privacy_request, request_task, upstream_results = upfront_checks(
            session, privacy_request_id, privacy_request_task_id
        )

        graph_task_key = CollectionAddress.from_string(request_task.collection_address)

        if request_task.status != TaskStatus.pending:
            logger.info(
                f"Cannot start consent Privacy Request Task {request_task.id} {request_task.collection_address} - status is {request_task.status}"
            )
            return

        logger.info(
            f"Running consent request task {request_task.id}:{request_task.collection_address} for privacy request {privacy_request.id}"
        )

        if graph_task_key != TERMINATOR_ADDRESS:
            task_resources = TaskResources(
                privacy_request,
                privacy_request.policy,
                session.query(ConnectionConfig).all(),
                session,
            )
            task = GraphTask(request_task, task_resources)

            # For regular nodes, store the data on the node
            func = task.consent_request
            task.request_task = request_task

            # TODO catch errors if no upstream result
            func(upstream_results[0].consent_data)

        request_task.status = TaskStatus.complete
        request_task.save(session)

        # If there are other downstream tasks that are ready to go, queue those now
        pending_downstream_tasks: Query = request_task.pending_downstream_tasks(session)
        for downstream_task in pending_downstream_tasks:
            if downstream_task.upstream_tasks_complete(session):
                logger.info(f"Upstream tasks complete so queuing {downstream_task.id}")
                run_consent_node.delay(
                    privacy_request_id=privacy_request_id,
                    privacy_request_task_id=downstream_task.id,
                )
            else:
                logger.info(f"Upstream tasks not completed for {downstream_task.id}")

        # If we've made it to the terminator node, requeue the entire Privacy request to continue where we left off,
        if graph_task_key == TERMINATOR_ADDRESS:
            from fides.api.service.privacy_request.request_runner_service import (
                queue_privacy_request,
            )

            queue_privacy_request(
                privacy_request_id=privacy_request.id,
                from_step=CurrentStep.finalize_consent.value,
            )
