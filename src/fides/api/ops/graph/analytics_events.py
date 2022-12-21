from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, List, Optional

from fideslog.sdk.python.event import AnalyticsEvent

from fides.api.ops.analytics import in_docker_container, send_analytics_event
from fides.api.ops.graph.config import CollectionAddress
from fides.api.ops.graph.graph_differences import (
    GraphDiffSummary,
    GraphRepr,
    find_graph_differences_summary,
    format_graph_for_caching,
)
from fides.api.ops.models.policy import ActionType
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.task.task_resources import TaskResources
from fides.api.ops.util.collection_util import Row
from fides.core.config import get_config

if TYPE_CHECKING:
    from fides.api.ops.task.graph_task import GraphTask

CONFIG = get_config()


async def fideslog_graph_failure(event: Optional[AnalyticsEvent]) -> None:
    """Send an Analytics Event if privacy request execution has failed"""
    if CONFIG.user.analytics_opt_out or not event:
        return

    await send_analytics_event(event)


async def fideslog_graph_rerun(event: Optional[AnalyticsEvent]) -> None:
    """Send an Analytics Event if a privacy request has been reprocessed, comparing its graph to the previous graph"""
    if CONFIG.user.analytics_opt_out or not event:
        return

    await send_analytics_event(event)


def prepare_rerun_graph_analytics_event(
    privacy_request: PrivacyRequest,
    env: Dict[CollectionAddress, "GraphTask"],
    end_nodes: List[CollectionAddress],
    resources: TaskResources,
    step: ActionType,
) -> Optional[AnalyticsEvent]:
    """Prepares an AnalyticsEvent to send to Fideslog with stats on how an access graph
    has changed from the previous run if applicable.

    Even for erasure requests, we still compare the "access graphs", because that reflects
    what data has changed and the relationships between them.
    The erasure graph is really just a list that runs each node with data from the access graphs.
    """
    previous_graph: Optional[GraphRepr] = privacy_request.get_cached_access_graph()
    current_graph: GraphRepr = format_graph_for_caching(env, end_nodes)

    previous_access_results: Dict[
        str, Optional[List[Row]]
    ] = resources.get_all_cached_objects()

    previous_erasure_results: Dict[str, int] = {}
    if step == ActionType.erasure:
        # Don't bother looking this up if we are running this just for the access portion
        previous_erasure_results = resources.get_all_cached_erasures()

    graph_diff_summary: Optional[GraphDiffSummary] = find_graph_differences_summary(
        previous_graph, current_graph, previous_access_results, previous_erasure_results
    )

    if not graph_diff_summary:
        return None

    data = graph_diff_summary.dict()
    data["privacy_request"] = privacy_request.id

    return AnalyticsEvent(
        docker=in_docker_container(),
        event="rerun_access_graph"
        if step == ActionType.access
        else "rerun_erasure_graph",
        event_created_at=datetime.now(tz=timezone.utc),
        local_host=None,
        endpoint=None,
        status_code=None,
        error=None,
        extra_data=data,
    )


def failed_graph_analytics_event(
    privacy_request: PrivacyRequest, exc: Optional[BaseException]
) -> Optional[AnalyticsEvent]:
    """Prepares an AnalyticsEvent to send to Fideslog if privacy request execution has failed."""

    data = {"privacy_request": privacy_request.id}

    return AnalyticsEvent(
        docker=in_docker_container(),
        event="privacy_request_execution_failure",
        event_created_at=datetime.now(tz=timezone.utc),
        local_host=None,
        endpoint=None,
        status_code=500,
        error=exc.__class__.__name__ if exc else None,
        extra_data=data,
    )
