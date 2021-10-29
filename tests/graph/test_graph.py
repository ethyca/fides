from fidesops.core.config import config
from fidesops.graph.config import *
from fidesops.graph.traversal import *
from fidesops.models.policy import ActionType
from fidesops.task.graph_task import retry
from tests.task.traversal_data import integration_db_graph

t1 = Collection(
    name="t1",
    fields=[
        Field(name="f1", primary_key="True"),
        Field(name="f2", identity="email"),
        Field(name="f3", references=[(FieldAddress("s1", "t2", "f1"), "to")]),
    ],
)
t2 = Collection(
    name="t2",
    fields=[
        Field(name="f1"),
        Field(name="f2"),
        Field(name="f3"),
    ],
)
t3 = Collection(
    name="t3",
    fields=[
        Field(name="f1"),
        Field(name="f2"),
        Field(name="f3", references=[(FieldAddress("s1", "t2", "f1"), "from")]),
    ],
)
graph = DatasetGraph(
    Dataset(
        name="s1", collections=[t1, t2, t3], connection_key="mock_connection_config_key"
    )
)


def test_node_eq() -> None:
    """two nodes are equal if they have the same collection address"""
    assert graph.nodes[CollectionAddress("s1", "t1")] == Node(
        Dataset(name="s1", collections=[], connection_key="mock_connection_config_key"),
        Collection(name="t1", fields=[]),
    )
    assert graph.nodes[CollectionAddress("s1", "t1")] != 1


def test_node_contains() -> None:
    node = graph.nodes[CollectionAddress("s1", "t1")]
    assert node.contains_field(lambda f: f.name == "f3")
    assert node.contains_field(lambda f: f.name == "f4") == False
    assert node.contains_field(lambda f: f.primary_key)


def test_retry_decorator():
    input_data = {"test": "data"}
    graph: DatasetGraph = integration_db_graph("postgres_example")
    traversal = Traversal(graph, {"email": "X"})
    traversal_nodes: Dict[
        CollectionAddress, TraversalNode
    ] = traversal.traversal_node_dict
    payment_card_node = traversal_nodes[
        CollectionAddress("postgres_example", "payment_card")
    ]

    config.execution.TASK_RETRY_COUNT = 5
    config.execution.TASK_RETRY_DELAY = 0.1
    config.execution.TASK_RETRY_BACKOFF = 0.01

    class TestRetrySar:
        def __init__(self):
            self.traversal_node = payment_card_node
            self.call_count = 0
            self.start_logged = 0
            self.retry_logged = 0
            self.end_called_with = ()

        def log_end(self, action_type: ActionType, exc: Optional[str] = None):
            self.end_called_with = (action_type, exc)

        def log_start(self, _: ActionType):
            self.start_logged += 1

        def log_retry(self, _: ActionType):
            self.retry_logged += 1

        @retry(action_type=ActionType.access, default_return=[])
        def test_function(self):
            self.call_count += 1
            input_data["nonexistant_value"]

    test_obj = TestRetrySar()
    test_obj.test_function()
    assert test_obj.call_count == 6  # called once, with 5 retries
    assert test_obj.end_called_with[0] == ActionType.access
    assert isinstance(test_obj.end_called_with[1], KeyError)
    assert test_obj.start_logged == 1
    assert test_obj.retry_logged == 5
