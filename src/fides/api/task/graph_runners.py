from typing import Any, Dict, List

from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestExit
from fides.api.graph.graph import DatasetGraph
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.task.create_request_tasks import (
    run_access_request,
    run_consent_request,
    run_erasure_request,
)
from fides.api.task.deprecated_graph_task import (
    run_access_request_deprecated,
    run_consent_request_deprecated,
    run_erasure_request_deprecated,
)
from fides.api.task.scheduler_utils import use_dsr_3_0_scheduler
from fides.api.util.collection_util import Row


def access_runner(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
    privacy_request_proceed: bool = True,  # Can be set to False in testing to run this in isolation
) -> Dict[str, List[Row]]:
    """
    Access runner that temporarily supports running Access Requests with either DSR 3.0 or DSR 2.0

    DSR 2.0 will be going away
    """
    use_dsr_3_0 = use_dsr_3_0_scheduler(privacy_request, ActionType.access)

    if use_dsr_3_0:
        run_access_request(
            privacy_request=privacy_request,
            policy=policy,
            graph=graph,
            connection_configs=connection_configs,
            identity=identity,
            session=session,
            privacy_request_proceed=privacy_request_proceed,
        )
        raise PrivacyRequestExit()

    return run_access_request_deprecated(
        privacy_request=privacy_request,
        policy=policy,
        graph=graph,
        connection_configs=connection_configs,
        identity=identity,
        session=session,
    )


def erasure_runner(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    access_request_data: Dict[str, List[Row]],
    session: Session,
    privacy_request_proceed: bool = True,  # Can be set to False in testing to run this in isolation
) -> Dict[str, int]:
    """Erasure runner that temporarily supports running Erasure DAGs with DSR 3.0 or 2.0.

    DSR 2.0 will be going away
    """
    use_dsr_3_0 = use_dsr_3_0_scheduler(privacy_request, ActionType.erasure)

    if use_dsr_3_0:
        run_erasure_request(
            privacy_request=privacy_request,
            session=session,
            privacy_request_proceed=privacy_request_proceed,
        )
        raise PrivacyRequestExit()

    return run_erasure_request_deprecated(
        privacy_request=privacy_request,
        policy=policy,
        graph=graph,
        connection_configs=connection_configs,
        identity=identity,
        access_request_data=access_request_data,
        session=session,
    )


def consent_runner(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
    privacy_request_proceed: bool = True,  # Can be set to False in testing to run this in isolation
) -> Dict[str, bool]:
    """Consent runner that temporarily supports running Consent DAGs with DSR 3.0 or 2.0.

    DSR 2.0 will be going away"""
    use_dsr_3_0 = use_dsr_3_0_scheduler(privacy_request, ActionType.consent)

    if use_dsr_3_0:
        run_consent_request(
            privacy_request=privacy_request,
            graph=graph,
            identity=identity,
            session=session,
            privacy_request_proceed=privacy_request_proceed,
        )
        raise PrivacyRequestExit()

    return run_consent_request_deprecated(
        privacy_request=privacy_request,
        policy=policy,
        graph=graph,
        connection_configs=connection_configs,
        identity=identity,
        session=session,
    )
