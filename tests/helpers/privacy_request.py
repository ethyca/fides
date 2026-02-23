import time
from typing import Any, Dict, List

from sqlalchemy.orm import Query, Session

from fides.api.common_exceptions import PrivacyRequestExit
from fides.api.graph.graph import DatasetGraph
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import (
    EXITED_EXECUTION_LOG_STATUSES,
    PrivacyRequest,
    RequestTask,
)
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.graph_runners import access_runner, consent_runner, erasure_runner
from fides.api.util.collection_util import Row
from fides.config.utils import load_file


class DSRThreeTestRunnerTimedOut(Exception):
    """DSR 3.0 Test Runner Timed Out"""


class PrivacyRequestStatusTimedOut(Exception):
    """Privacy Request Status Polling Timed Out"""


def wait_for_tasks_to_complete(
    db: Session, pr: PrivacyRequest, action_type: ActionType
):
    """Testing Helper for DSR 3.0 - repeatedly checks to see if all Request Tasks
    have exited so bogged down test doesn't hang"""

    def all_tasks_have_run(tasks: Query) -> bool:
        return all(tsk.status in EXITED_EXECUTION_LOG_STATUSES for tsk in tasks)

    db.commit()
    counter = 0
    while not all_tasks_have_run(
        (
            db.query(RequestTask).filter(
                RequestTask.privacy_request_id == pr.id,
                RequestTask.action_type == action_type,
            )
        )
    ):
        time.sleep(1)
        counter += 1
        if counter == 5:
            raise DSRThreeTestRunnerTimedOut()


def wait_for_privacy_request_status(
    db: Session,
    privacy_request_id: str,
    target_status: PrivacyRequestStatus,
    timeout_seconds: int = 30,
    poll_interval_seconds: int = 1,
) -> PrivacyRequest:
    """Testing Helper - repeatedly checks to see if a PrivacyRequest has reached
    the target status, with configurable timeout and polling interval"""

    counter = 0
    max_attempts = timeout_seconds // poll_interval_seconds

    while counter < max_attempts:
        privacy_request = PrivacyRequest.get_by(
            db, field="id", value=privacy_request_id
        )

        if privacy_request.status == target_status:
            return privacy_request

        time.sleep(poll_interval_seconds)
        counter += 1

    raise PrivacyRequestStatusTimedOut(
        f"Privacy request {privacy_request.id} did not reach status '{target_status}' "
        f"within {timeout_seconds} seconds. Current status: '{privacy_request.status}'"
    )


def access_runner_tester(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
):
    """
    Function for testing the access request using DSR 3.0.
    """
    try:
        return access_runner(
            privacy_request,
            policy,
            graph,
            connection_configs,
            identity,
            session,
            privacy_request_proceed=False,
        )
    except PrivacyRequestExit:
        wait_for_tasks_to_complete(session, privacy_request, ActionType.access)
        return privacy_request.get_raw_access_results()


def erasure_runner_tester(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    access_request_data: Dict[str, List[Row]],
    session: Session,
):
    """
    Function for testing the erasure runner using DSR 3.0.
    """
    try:
        return erasure_runner(
            privacy_request,
            policy,
            graph,
            connection_configs,
            identity,
            access_request_data,
            session,
            privacy_request_proceed=False,
        )
    except PrivacyRequestExit:
        wait_for_tasks_to_complete(session, privacy_request, ActionType.erasure)
        return privacy_request.get_raw_masking_counts()


def consent_runner_tester(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
):
    """
    Function for testing the consent request using DSR 3.0.
    """
    try:
        return consent_runner(
            privacy_request,
            policy,
            graph,
            connection_configs,
            identity,
            session,
            privacy_request_proceed=False,
        )
    except PrivacyRequestExit:
        wait_for_tasks_to_complete(session, privacy_request, ActionType.consent)
        return privacy_request.get_consent_results()
