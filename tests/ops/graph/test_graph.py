import pytest

import fides.api.graph.graph as graph_mod
from fides.api.graph.config import *
from fides.api.service.privacy_request.request_runner_service import (
    _partition_configs_by_property,
    _refs_cross_boundary,
)
from fides.api.graph.graph import (
    Node,
    _dataset_graph_filters,
    apply_dataset_graph_filters,
    is_property_filtering_active,
    register_dataset_graph_filter,
    register_property_filtering_check,
)
from fides.api.graph.traversal import *
from fides.api.models.policy import ActionType
from fides.api.task.graph_task import retry
from fides.api.task.task_resources import TaskResources
from fides.config import CONFIG
from tests.ops.task.traversal_data import integration_db_graph

t1 = Collection(
    name="t1",
    fields=[
        ScalarField(name="f1", primary_key="True"),
        ScalarField(name="f2", identity="email"),
        ScalarField(name="f3", references=[(FieldAddress("s1", "t2", "f1"), "to")]),
        ObjectField(name="f4", fields={"f5": ScalarField(name="f5", identity="ssn")}),
    ],
)
t2 = Collection(
    name="t2",
    fields=[
        ScalarField(name="f1"),
        ScalarField(name="f2"),
        ScalarField(name="f3"),
    ],
)
t3 = Collection(
    name="t3",
    fields=[
        ScalarField(name="f1"),
        ScalarField(name="f2"),
        ScalarField(name="f3", references=[(FieldAddress("s1", "t2", "f1"), "from")]),
    ],
)
graph = DatasetGraph(
    GraphDataset(
        name="s1", collections=[t1, t2, t3], connection_key="mock_connection_config_key"
    )
)


class TestNode:
    def test_node_eq(self) -> None:
        """two nodes are equal if they have the same collection address"""
        assert graph.nodes[CollectionAddress("s1", "t1")] == Node(
            GraphDataset(
                name="s1", collections=[], connection_key="mock_connection_config_key"
            ),
            Collection(name="t1", fields=[]),
        )
        assert graph.nodes[CollectionAddress("s1", "t1")] != 1

    def test_node_contains_field(self) -> None:
        node = graph.nodes[CollectionAddress("s1", "t1")]
        assert node.collection.contains_field(lambda f: f.name == "f3")
        assert node.collection.contains_field(lambda f: f.name == "f6") is False
        assert node.collection.contains_field(lambda f: f.primary_key)
        assert node.collection.contains_field(lambda f: f.identity == "ssn")

    @pytest.mark.parametrize(
        "property_scope,expected_in_scope",
        [
            (PropertyScope.IN_SCOPE, True),
            (PropertyScope.TRAVERSAL_ONLY, False),
        ],
    )
    def test_node_in_scope(self, property_scope, expected_in_scope):
        coll = Collection(
            name="scoped",
            fields=[ScalarField(name="f1")],
            property_scope=property_scope,
        )
        ds = GraphDataset(name="ds", collections=[coll], connection_key="mock_key")
        node = Node(ds, coll)
        assert node.in_scope is expected_in_scope


class TestDatasetGraphFilterRegistry:
    @pytest.fixture(autouse=True)
    def _clear_filters(self):
        """Ensure filter registry is clean before and after each test."""
        _dataset_graph_filters.clear()
        yield
        _dataset_graph_filters.clear()

    def test_no_filters_is_noop(self):
        datasets = [
            GraphDataset(name="ds1", collections=[], connection_key="k1"),
            GraphDataset(name="ds2", collections=[], connection_key="k2"),
        ]
        result = apply_dataset_graph_filters(datasets, "prop_1")
        assert result == datasets

    def test_single_filter_applied(self):
        def drop_ds2(graphs, property_id):
            return [g for g in graphs if g.name != "ds2"]

        register_dataset_graph_filter(drop_ds2)

        datasets = [
            GraphDataset(name="ds1", collections=[], connection_key="k1"),
            GraphDataset(name="ds2", collections=[], connection_key="k2"),
        ]
        result = apply_dataset_graph_filters(datasets, "prop_1")
        assert [d.name for d in result] == ["ds1"]

    def test_filters_compose_in_order(self):
        """Multiple filters are applied as a pipeline."""
        register_dataset_graph_filter(
            lambda graphs, pid: [g for g in graphs if g.name != "ds1"]
        )
        register_dataset_graph_filter(
            lambda graphs, pid: [g for g in graphs if g.name != "ds3"]
        )

        datasets = [
            GraphDataset(name="ds1", collections=[], connection_key="k1"),
            GraphDataset(name="ds2", collections=[], connection_key="k2"),
            GraphDataset(name="ds3", collections=[], connection_key="k3"),
        ]
        result = apply_dataset_graph_filters(datasets, None)
        assert [d.name for d in result] == ["ds2"]

    def test_filter_receives_property_id(self):
        """Filter function receives the property_id argument."""
        captured = {}

        def capture_pid(graphs, property_id):
            captured["property_id"] = property_id
            return graphs

        register_dataset_graph_filter(capture_pid)
        datasets = [GraphDataset(name="ds1", collections=[], connection_key="k1")]

        apply_dataset_graph_filters(datasets, "my_prop")
        assert captured["property_id"] == "my_prop"

        apply_dataset_graph_filters(datasets, None)
        assert captured["property_id"] is None


class TestPropertyFilteringCheck:
    @pytest.fixture(autouse=True)
    def _clear_check(self):
        """Reset the property filtering check before and after each test."""

        graph_mod._property_filtering_active_fn = None
        yield
        graph_mod._property_filtering_active_fn = None

    def test_inactive_when_no_callback_registered(self):
        assert is_property_filtering_active() is False

    def test_active_when_callback_returns_true(self):
        register_property_filtering_check(lambda: True)
        assert is_property_filtering_active() is True

    def test_inactive_when_callback_returns_false(self):
        register_property_filtering_check(lambda: False)
        assert is_property_filtering_active() is False

    def test_reflects_runtime_changes(self):
        """Callback is evaluated at call time, not registration time."""
        enabled = [True]
        register_property_filtering_check(lambda: enabled[0])

        assert is_property_filtering_active() is True
        enabled[0] = False
        assert is_property_filtering_active() is False


class _StubDatasetConfig:
    """Minimal stand-in for DatasetConfig for partition tests."""

    def __init__(self, fides_key: str, property_ids: list[str] | None = None):
        self.fides_key = fides_key
        self.property_ids = property_ids or []


class TestPartitionConfigsByProperty:
    def test_empty_configs(self):
        matching, excluded = _partition_configs_by_property([], "prop_1")
        assert matching == []
        assert excluded == []

    def test_universal_dataset_matches(self):
        dc = _StubDatasetConfig("ds_universal", [])
        matching, excluded = _partition_configs_by_property([dc], "prop_1")
        assert matching == [dc]
        assert excluded == []

    def test_none_property_ids_treated_as_universal(self):
        dc = _StubDatasetConfig("ds_none")
        dc.property_ids = None
        matching, excluded = _partition_configs_by_property([dc], "prop_1")
        assert matching == [dc]
        assert excluded == []

    def test_matching_property_id(self):
        dc = _StubDatasetConfig("ds_a", ["prop_1", "prop_2"])
        matching, excluded = _partition_configs_by_property([dc], "prop_1")
        assert matching == [dc]
        assert excluded == []

    def test_non_matching_property_id(self):
        dc = _StubDatasetConfig("ds_a", ["prop_2", "prop_3"])
        matching, excluded = _partition_configs_by_property([dc], "prop_1")
        assert matching == []
        assert excluded == [dc]


class TestRefsCrossBoundary:
    @staticmethod
    def _make_graph(
        name: str, refs: list[tuple[str, str, str]] | None = None
    ) -> GraphDataset:
        fields = [ScalarField(name="id", primary_key=True)]
        if refs:
            fields.append(
                ScalarField(
                    name="fk",
                    references=[
                        (FieldAddress(ds, col, field), "to") for ds, col, field in refs
                    ],
                )
            )
        col = Collection(name="main", fields=fields)
        return GraphDataset(name=name, collections=[col], connection_key=name)

    def test_no_refs_no_crossing(self):
        graphs = [self._make_graph("ds_a")]
        assert _refs_cross_boundary(graphs, {"ds_b"}) is False

    def test_ref_to_non_excluded_no_crossing(self):
        graphs = [self._make_graph("ds_a", refs=[("ds_b", "main", "id")])]
        assert _refs_cross_boundary(graphs, {"ds_c"}) is False

    def test_ref_to_excluded_crosses_boundary(self):
        graphs = [self._make_graph("ds_a", refs=[("ds_b", "main", "id")])]
        assert _refs_cross_boundary(graphs, {"ds_b"}) is True

    def test_empty_excluded_keys_no_crossing(self):
        graphs = [self._make_graph("ds_a", refs=[("ds_b", "main", "id")])]
        assert _refs_cross_boundary(graphs, set()) is False

    def test_multiple_graphs_one_crossing(self):
        graphs = [
            self._make_graph("ds_a"),
            self._make_graph("ds_b", refs=[("ds_excluded", "main", "id")]),
        ]
        assert _refs_cross_boundary(graphs, {"ds_excluded"}) is True


def test_retry_decorator(privacy_request, policy, db):
    input_data = {"test": "data"}
    graph: DatasetGraph = integration_db_graph("postgres_example")
    traversal = Traversal(graph, {"email": "X"})
    traversal_nodes: Dict[CollectionAddress, TraversalNode] = (
        traversal.traversal_node_dict
    )
    payment_card_node = traversal_nodes[
        CollectionAddress("postgres_example", "payment_card")
    ]
    execution_node = payment_card_node.to_mock_execution_node()

    CONFIG.execution.task_retry_count = 5
    CONFIG.execution.task_retry_delay = 0.1
    CONFIG.execution.task_retry_backoff = 0.01

    class TestRetryDecorator:
        def __init__(self):
            self.execution_node = execution_node
            self.call_count = 0
            self.start_logged = 0
            self.retry_logged = 0
            self.end_called_with = ()
            self.resources = TaskResources(
                privacy_request,
                policy,
                [],
                payment_card_node.to_mock_request_task(),
                db,
            )

        def log_end(self, action_type: ActionType, exc: Optional[str] = None):
            self.end_called_with = (action_type, exc)

        def log_start(self, _: ActionType):
            self.start_logged += 1

        def log_retry(self, _: ActionType):
            self.retry_logged += 1

        def skip_if_disabled(self) -> bool:
            return False

        def skip_if_action_disabled(self, action_type: ActionType):
            return False

        @retry(action_type=ActionType.access, default_return=[])
        def test_function(self):
            self.call_count += 1
            input_data["nonexistent_value"]

    test_obj = TestRetryDecorator()
    with pytest.raises(Exception):
        test_obj.test_function()
    assert test_obj.call_count == 6  # called once, with 5 retries
    assert test_obj.end_called_with[0] == ActionType.access
    assert isinstance(test_obj.end_called_with[1], KeyError)
    assert test_obj.start_logged == 1
    assert test_obj.retry_logged == 5
