import pytest

from fides.api.common_exceptions import TraversalError
from fides.api.graph.graph import DatasetGraph
from fides.api.models.privacy_request import (
    ExecutionLog,
    ExecutionLogStatus,
    PrivacyRequestStatus,
)
from fides.api.task.deprecated_graph_task import run_access_request_deprecated


class TestDeprecatedGraphTasks:
    def test_run_access_request_deprecated_with_unreachable_nodes(
        self,
        db,
        privacy_request,
        policy,
        dataset_graph_with_unreachable_collections: DatasetGraph,
    ):
        with pytest.raises(TraversalError) as err:
            run_access_request_deprecated(
                privacy_request,
                policy,
                dataset_graph_with_unreachable_collections,
                [],
                {"email": "customer-4@example.com"},
                db,
            )

        assert "Some nodes were not reachable:" in str(err.value)
        assert "dataset_with_unreachable_collections:login" in str(err.value)
        assert "dataset_with_unreachable_collections:report" in str(err.value)

        db.refresh(privacy_request)
        assert privacy_request.status == PrivacyRequestStatus.error

        # We expect two error logs, one per unreachable collection
        error_logs = privacy_request.execution_logs.filter(
            ExecutionLog.status == ExecutionLogStatus.error
        )
        assert error_logs.count() == 2
        error_logs = sorted(
            error_logs, key=lambda execution_log: execution_log.collection_name
        )
        assert error_logs[0].dataset_name == "Dataset traversal"
        assert (
            error_logs[0].collection_name
            == "dataset_with_unreachable_collections.login"
        )
        assert (
            error_logs[0].message
            == "Node dataset_with_unreachable_collections:login is not reachable"
        )
        assert error_logs[1].dataset_name == "Dataset traversal"
        assert (
            error_logs[1].collection_name
            == "dataset_with_unreachable_collections.report"
        )
        assert (
            error_logs[1].message
            == "Node dataset_with_unreachable_collections:report is not reachable"
        )
