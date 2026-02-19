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
from fides.api.util.collection_util import Row


def access_runner(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
    privacy_request_proceed: bool = True,
) -> None:
    """Run an access request via DSR 3.0, then signal the pipeline to halt."""
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


def erasure_runner(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    access_request_data: Dict[str, List[Row]],
    session: Session,
    privacy_request_proceed: bool = True,
) -> None:
    """Run an erasure request via DSR 3.0, then signal the pipeline to halt."""
    run_erasure_request(
        privacy_request=privacy_request,
        session=session,
        privacy_request_proceed=privacy_request_proceed,
    )
    raise PrivacyRequestExit()


def consent_runner(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
    privacy_request_proceed: bool = True,
) -> None:
    """Run a consent request via DSR 3.0, then signal the pipeline to halt."""
    run_consent_request(
        privacy_request=privacy_request,
        graph=graph,
        identity=identity,
        session=session,
        privacy_request_proceed=privacy_request_proceed,
    )
    raise PrivacyRequestExit()
