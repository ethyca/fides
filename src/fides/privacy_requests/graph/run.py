"""
Module for building and executing Privacy Request graphs.
"""
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.util.collection_util import Row
from fides.privacy_requests.graph.build_access_graph import build_access_graph
from fides.privacy_requests.graph.build_consent_graph import build_consent_graph
from fides.privacy_requests.graph.build_erasure_graph import build_erasure_graph
from fides.privacy_requests.graph.execution import execute_consent_graph, execute_graph
from fides.privacy_requests.graph.graph import DatasetGraph


async def run_access_request(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
) -> Dict[str, List[Row]]:
    """Build and run an Access request."""
    request_graph = await build_access_graph(
        privacy_request=privacy_request,
        policy=policy,
        graph=graph,
        connection_configs=connection_configs,
        identity=identity,
        session=session,
    )
    access_result = await execute_graph(request_graph=request_graph)
    return access_result


async def run_erasure_request(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    access_request_data: Dict[str, List[Row]],
    identity: Dict[str, Any],
    session: Session,
) -> Dict[str, List[Row]]:
    """Build and run an Erasure request."""
    request_graph = await build_erasure_graph(
        privacy_request=privacy_request,
        policy=policy,
        graph=graph,
        connection_configs=connection_configs,
        access_request_data=access_request_data,
        identity=identity,
        session=session,
    )
    erasure_result = await execute_graph(request_graph=request_graph)
    return erasure_result


async def run_consent_request(
    privacy_request: PrivacyRequest,
    policy: Policy,
    graph: DatasetGraph,
    connection_configs: List[ConnectionConfig],
    identity: Dict[str, Any],
    session: Session,
) -> Dict[str, bool]:
    """Build and run a Consent request."""
    request_graph, graph_keys = await build_consent_graph(
        privacy_request=privacy_request,
        policy=policy,
        graph=graph,
        connection_configs=connection_configs,
        identity=identity,
        session=session,
    )
    consent_result = await execute_consent_graph(request_graph, graph_keys)
    return consent_result
