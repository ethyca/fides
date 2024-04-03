from typing import Any, Dict, List

from sqlalchemy.orm import Session

from fides.api.common_exceptions import PrivacyRequestExit
from fides.api.graph.graph import DatasetGraph
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
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
from fides.api.util.collection_util import Row
from fides.config import CONFIG


def access_runner(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
    queue_privacy_request: bool,
) -> Dict[str, List[Row]]:
    """Access runner that temporarily supports running Access Request with DSR 3.0  2.0.
    DSR 2.0 will be going away"""
    use_dsr_3_0 = CONFIG.execution.use_dsr_3_0

    prev_results = privacy_request.get_raw_access_results()

    if privacy_request.access_tasks.count() and not use_dsr_3_0:
        # If we've previously processed this Privacy Request using DSR 3.0, continue doing so
        use_dsr_3_0 = True

    elif prev_results and use_dsr_3_0:
        # If we've previously tried to process this Privacy Request using DSR 2.0, continue doing so
        use_dsr_3_0 = False

    if use_dsr_3_0:
        run_access_request(
            privacy_request=privacy_request,
            policy=policy,
            graph=graph,
            connection_configs=connection_configs,
            identity=identity,
            session=session,
            queue_privacy_request=queue_privacy_request,
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
    queue_privacy_request: bool,
) -> Dict[str, int]:
    """Erasure runner that temporarily supports running Erasure DAGs with DSR 3.0 or 2.0.
    DSR 2.0 will be going away"""
    if CONFIG.execution.use_dsr_3_0:
        run_erasure_request(
            privacy_request=privacy_request,
            session=session,
            queue_privacy_request=queue_privacy_request,
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
    queue_privacy_request: bool,
) -> Dict[str, bool]:
    """Consent runner that temporarily supports running Consent DAGs with DSR 3.0 or 2.0.
    DSR 2.0 will be going away"""
    if CONFIG.execution.use_dsr_3_0:
        run_consent_request(
            privacy_request=privacy_request,
            graph=graph,
            identity=identity,
            session=session,
            queue_privacy_request=queue_privacy_request,
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
