import pytest
from fideslang import Dataset
from fideslang.models import MaskingStrategies

from fides.api.graph.graph import *
from fides.api.models.datasetconfig import convert_dataset_to_graph

from .graph_test_util import *

#  -------------------------------------------
#   graph object tests
#  -------------------------------------------


def test_graph_creation() -> None:
    t = generate_graph_resources(3)
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_2", "ds_2", "f1"), "to")
    )
    field(t, "dr_2", "ds_2", "f1").references.append(
        (FieldAddress("dr_3", "ds_3", "f1"), "to")
    )
    field(t, "dr_1", "ds_1", "f1").identity = "x"
    graph = DatasetGraph(*t)
    assert set(graph.nodes.keys()) == {
        CollectionAddress("dr_1", "ds_1"),
        CollectionAddress("dr_2", "ds_2"),
        CollectionAddress("dr_3", "ds_3"),
    }
    assert graph.edges == {
        Edge(FieldAddress("dr_2", "ds_2", "f1"), FieldAddress("dr_3", "ds_3", "f1")),
        Edge(FieldAddress("dr_1", "ds_1", "f1"), FieldAddress("dr_2", "ds_2", "f1")),
    }
    assert graph.identity_keys == {FieldAddress("dr_1", "ds_1", "f1"): "x"}


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
def test_graph_creation_with_collection_level_meta(
    example_datasets, bigquery_connection_config
):
    dataset = Dataset(**example_datasets[7])
    graph = convert_dataset_to_graph(dataset, bigquery_connection_config.key)
    dg = DatasetGraph(*[graph])

    # Assert erase_after
    customer_collection = dg.nodes[
        CollectionAddress("bigquery_example_test_dataset", "customer")
    ].collection
    assert customer_collection.erase_after == {
        CollectionAddress("bigquery_example_test_dataset", "address")
    }

    address_collection = dg.nodes[
        CollectionAddress("bigquery_example_test_dataset", "address")
    ].collection
    assert address_collection.erase_after == {
        CollectionAddress("bigquery_example_test_dataset", "employee")
    }
    assert address_collection.masking_strategy_override is None

    employee_collection = dg.nodes[
        CollectionAddress("bigquery_example_test_dataset", "employee")
    ].collection
    assert employee_collection.erase_after == set()
    assert employee_collection.masking_strategy_override == MaskingStrategyOverride(
        strategy=MaskingStrategies.DELETE
    )


def test_extract_seed_nodes() -> None:
    # TEST INIT:
    t = generate_graph_resources(3)
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_2", "ds_2", "f1"), None)
    )
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_3", "ds_3", "f1"), None)
    )
    field(t, "dr_1", "ds_1", "f1").identity = "x"
    graph: DatasetGraph = DatasetGraph(*t)

    assert set(graph.nodes.keys()) == {
        CollectionAddress("dr_1", "ds_1"),
        CollectionAddress("dr_2", "ds_2"),
        CollectionAddress("dr_3", "ds_3"),
    }

    assert graph.identity_keys == {FieldAddress("dr_1", "ds_1", "f1"): "x"}

    assert graph.edges == {
        BidirectionalEdge(
            FieldAddress("dr_1", "ds_1", "f1"), FieldAddress("dr_2", "ds_2", "f1")
        ),
        BidirectionalEdge(
            FieldAddress("dr_1", "ds_1", "f1"), FieldAddress("dr_3", "ds_3", "f1")
        ),
    }

    # extract see nodes
    traversal = Traversal(graph, {"x": 1})
    assert traversal.root_node.children.keys() == {CollectionAddress("dr_1", "ds_1")}


#  -------------------------------------------
#   graph traversal errors
#  -------------------------------------------


def test_catch_unreachable_node_collection_before() -> None:
    # test with before collection
    t = generate_graph_resources(3)
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_2", "ds_2", "f1"), None)
    )
    field(t, "dr_1", "ds_1", "f1").identity = "email"
    field(t, "dr_2", "ds_2", "f1").references.append(
        (FieldAddress("dr_3", "ds_3", "f1"), None)
    )
    collection(t, CollectionAddress("dr_1", "ds_1")).after.add(
        CollectionAddress("dr_2", "ds_2")
    )
    collection(t, CollectionAddress("dr_2", "ds_2")).after.add(
        CollectionAddress("dr_3", "ds_3")
    )
    collection(t, CollectionAddress("dr_3", "ds_3")).after.add(
        CollectionAddress("dr_1", "ds_1")
    )

    with pytest.raises(TraversalError):
        generate_traversal({"email": "a"}, *t)


def test_catch_unreachable_node_dataresource_before() -> None:
    # test with before data dataset
    t = generate_graph_resources(3)
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_2", "ds_2", "f1"), None)
    )
    field(t, "dr_1", "ds_1", "f1").identity = "email"
    field(t, "dr_2", "ds_2", "f1").references.append(
        (FieldAddress("dr_3", "ds_3", "f1"), None)
    )

    dataresource(t, "dr_1").after.add("dr_2")
    dataresource(t, "dr_2").after.add("dr_3")
    dataresource(t, "dr_3").after.add("dr_1")

    with pytest.raises(TraversalError):
        generate_traversal({"email": "a"}, *t)


def test_catch_unreachable_node_mixed_before() -> None:
    # test with before data dataset
    t = generate_graph_resources(3)
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_2", "ds_2", "f1"), None)
    )
    field(t, "dr_1", "ds_1", "f1").identity = "email"
    field(t, "dr_2", "ds_2", "f1").references.append(
        (FieldAddress("dr_3", "ds_3", "f1"), None)
    )

    dataresource(t, "dr_1").after.add("dr_2")
    collection(t, CollectionAddress("dr_2", "ds_2")).after.add(
        CollectionAddress("dr_3", "ds_3")
    )
    collection(t, CollectionAddress("dr_3", "ds_3")).after.add(
        CollectionAddress("dr_1", "ds_1")
    )

    with pytest.raises(TraversalError):
        generate_traversal({"email": "a"}, *t)


def test_catch_unreachable_node_no_link() -> None:
    t = generate_graph_resources(5)
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_2", "ds_2", "f1"), None)
    )
    field(t, "dr_2", "ds_2", "f1").references.append(
        (FieldAddress("dr_3", "ds_3", "f1"), None)
    )
    # no links to traversal_node 4, 5
    field(t, "dr_1", "ds_1", "f1").identity = "email"

    with pytest.raises(TraversalError):
        generate_traversal({"email": "a"}, *t)


def test_catch_invalid_reference_error() -> None:
    t = generate_graph_resources(3)
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("I_dont_exist", "x", "y"), None)
    )
    field(t, "dr_1", "ds_1", "f1").identity = "email"

    with pytest.raises(ValidationError):
        generate_traversal({"email": "a"}, *t)


def test_self_reference_error() -> None:
    t = generate_graph_resources(3)
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_1", "ds_1", "f1"), None)
    )
    field(t, "dr_1", "ds_1", "f1").identity = "email"

    with pytest.raises(ValidationError):
        generate_traversal({"email": "a"}, *t)


#  -------------------------------------------
#   graph traversal tests
#  -------------------------------------------


def test_fully_connected() -> None:
    """generate some fully connected graphs and assure that we generate a valid traversal"""
    t = generate_fully_connected_resources(25)
    field(t, "dr_1", "ds_1", "f1").identity = "email"
    generate_traversal({"email": "X"}, *t)  # should generate exception on unreachable


def test_tree_1() -> None:
    """t1:seed ->t3 -> t2"""
    t1 = Collection(
        name="t1",
        fields=[
            ScalarField(name="f1"),
            ScalarField(name="f2", identity="email"),
            ScalarField(name="f3", references=[(FieldAddress("s1", "t2", "f1"), "to")]),
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
            ScalarField(
                name="f3", references=[(FieldAddress("s1", "t2", "f1"), "from")]
            ),
        ],
    )
    t4 = Collection(
        name="t4",
        fields=[
            ObjectField(
                name="f4",
                fields={
                    "f5": ScalarField(name="f5", identity="email"),
                    "f6": ScalarField(name="f6"),
                },
            )
        ],
    )
    seed = {"email": "foo@bar.com"}
    traversal_map, terminators = generate_traversal(
        seed,
        GraphDataset(
            name="s1",
            collections=[t1, t2, t3, t4],
            connection_key="mock_connection_config_key",
        ),
    )

    assert traversal_map == {
        "__ROOT__:__ROOT__": {
            "from": {},
            "to": {"s1:t4": {"email -> f4.f5"}, "s1:t1": {"email -> f2"}},
        },
        "s1:t4": {"from": {"__ROOT__:__ROOT__": {"email -> f4.f5"}}, "to": {}},
        "s1:t1": {
            "from": {"__ROOT__:__ROOT__": {"email -> f2"}},
            "to": {"s1:t2": {"f3 -> f1"}},
        },
        "s1:t2": {"from": {"s1:t1": {"f3 -> f1"}}, "to": {"s1:t3": {"f1 -> f3"}}},
        "s1:t3": {"from": {"s1:t2": {"f1 -> f3"}}, "to": {}},
    }

    assert set(terminators) == {
        CollectionAddress("s1", "t3"),
        CollectionAddress("s1", "t4"),
    }


def test_traversal_ordering() -> None:
    # connect 1 -> 2, 2 <- 3,directional,  -> 3 is unreachable
    t = generate_graph_resources(3)
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_2", "ds_2", "f1"), "to")
    )

    field(t, "dr_3", "ds_3", "f3").references.append(
        (FieldAddress("dr_2", "ds_2", "f3"), "to")
    )
    field(t, "dr_1", "ds_1", "f1").identity = "email"
    with pytest.raises(TraversalError):
        _ = Traversal(DatasetGraph(*t), {"email": "X"})

    # this adapts https://ethyca.atlassian.net/wiki/spaces/EPRO/pages/466944001/Data+Attributes
    # we need to ensure that we retrieve addresses from orders and customers,
    # not orders from addresses
    customers = Collection(
        name="Customer",
        fields=[
            ScalarField(name="customer_id"),
            ScalarField(name="name"),
            ScalarField(name="email", identity="email"),
            ScalarField(
                name="contact_address_id",
                references=[(FieldAddress("mysql", "Address", "id"), "to")],
            ),
        ],
    )
    addresses = Collection(
        name="Address",
        fields=[
            ScalarField(name="id"),
            ScalarField(name="street"),
            ScalarField(name="city"),
            ScalarField(name="state"),
            ScalarField(name="zip"),
        ],
    )
    orders = Collection(
        name="Order",
        fields=[
            ScalarField(name="order_id"),
            ScalarField(
                name="customer_id",
                references=[(FieldAddress("mysql", "Customer", "customer_id"), None)],
            ),
            ScalarField(
                name="shipping_address_id",
                references=[(FieldAddress("mysql", "Address", "id"), "to")],
            ),
            ScalarField(
                name="billing_address_id",
                references=[(FieldAddress("mysql", "Address", "id"), "to")],
            ),
        ],
    )
    graph = DatasetGraph(
        GraphDataset(
            name="mysql",
            collections=[customers, addresses, orders],
            connection_key="mock_connection_config_key",
        )
    )
    traversal = Traversal(
        graph,
        {"email": "X"},
    )
    traversal_map, terminators = traversal.traversal_map()
    assert traversal_map == {
        "__ROOT__:__ROOT__": {"from": {}, "to": {"mysql:Customer": {"email -> email"}}},
        "mysql:Customer": {
            "from": {"__ROOT__:__ROOT__": {"email -> email"}},
            "to": {
                "mysql:Order": {"customer_id -> customer_id"},
                "mysql:Address": {"contact_address_id -> id"},
            },
        },
        "mysql:Order": {
            "from": {"mysql:Customer": {"customer_id -> customer_id"}},
            "to": {
                "mysql:Address": {
                    "billing_address_id -> id",
                    "shipping_address_id -> id",
                }
            },
        },
        "mysql:Address": {
            "from": {
                "mysql:Customer": {"contact_address_id -> id"},
                "mysql:Order": {
                    "billing_address_id -> id",
                    "shipping_address_id -> id",
                },
            },
            "to": {},
        },
    }
    assert terminators == [CollectionAddress("mysql", "Address")]


def test_circular_reference() -> None:
    """Create a graph A->B-C-A"""

    t = generate_graph_resources(3)
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_2", "ds_2", "f1"), "to")
    )
    field(t, "dr_2", "ds_2", "f2").references.append(
        (FieldAddress("dr_3", "ds_3", "f2"), "to")
    )
    field(t, "dr_3", "ds_3", "f3").references.append(
        (FieldAddress("dr_1", "ds_1", "f3"), "to")
    )
    field(t, "dr_1", "ds_1", "f2").identity = "email"
    traversal = Traversal(DatasetGraph(*t), {"email": "X"})
    traversal_map, terminators = traversal.traversal_map()
    assert traversal_map == {
        "__ROOT__:__ROOT__": {"from": {}, "to": {"dr_1:ds_1": {"email -> f2"}}},
        "dr_1:ds_1": {
            "from": {"__ROOT__:__ROOT__": {"email -> f2"}, "dr_3:ds_3": {"f3 -> f3"}},
            "to": {"dr_2:ds_2": {"f1 -> f1"}},
        },
        "dr_2:ds_2": {
            "from": {"dr_1:ds_1": {"f1 -> f1"}},
            "to": {"dr_3:ds_3": {"f2 -> f2"}},
        },
        "dr_3:ds_3": {
            "from": {"dr_2:ds_2": {"f2 -> f2"}},
            "to": {"dr_1:ds_1": {"f3 -> f3"}},
        },
    }

    assert terminators == [CollectionAddress("dr_1", "ds_1")]
    # this visits (root -> 1,1 -> 2,2 -> 3,3 -> 1,1) and then terminates.
    assert generate_traversal_order(traversal) == {
        CollectionAddress("__ROOT__", "__ROOT__"): [0],
        CollectionAddress("dr_1", "ds_1"): [1, 4],
        CollectionAddress("dr_2", "ds_2"): [2],
        CollectionAddress("dr_3", "ds_3"): [3],
    }


def test_multiple_field_links() -> None:
    t = generate_graph_resources(2)
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_2", "ds_2", "f1"), None)
    )
    field(t, "dr_1", "ds_1", "f2").references.append(
        (FieldAddress("dr_2", "ds_2", "f1"), None)
    )
    field(t, "dr_1", "ds_1", "f3").references.append(
        (FieldAddress("dr_2", "ds_2", "f3"), None)
    )
    field(t, "dr_1", "ds_1", "f1").identity = "email"
    traversal = Traversal(DatasetGraph(*t), {"email": "X"})

    assert incoming_edges(traversal, CollectionAddress("dr_1", "ds_1")) == {
        Edge(
            FieldAddress("__ROOT__", "__ROOT__", "email"),
            FieldAddress("dr_1", "ds_1", "f1"),
        )
    }

    assert set(incoming_edges(traversal, CollectionAddress("dr_2", "ds_2"))) == {
        Edge(FieldAddress("dr_1", "ds_1", "f1"), FieldAddress("dr_2", "ds_2", "f1")),
        Edge(FieldAddress("dr_1", "ds_1", "f2"), FieldAddress("dr_2", "ds_2", "f1")),
        Edge(FieldAddress("dr_1", "ds_1", "f3"), FieldAddress("dr_2", "ds_2", "f3")),
    }

    assert outgoing_edges(traversal, CollectionAddress("dr_1", "ds_1")) == {
        Edge(FieldAddress("dr_1", "ds_1", "f1"), FieldAddress("dr_2", "ds_2", "f1")),
        Edge(FieldAddress("dr_1", "ds_1", "f2"), FieldAddress("dr_2", "ds_2", "f1")),
        Edge(FieldAddress("dr_1", "ds_1", "f3"), FieldAddress("dr_2", "ds_2", "f3")),
    }


def test_tree_splay() -> None:
    """test of tree with one root traversal_node pointing to all end nodes"""
    t = generate_graph_resources(5)
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_2", "ds_2", "f1"), "to")
    )
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_3", "ds_3", "f1"), "to")
    )
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_4", "ds_4", "f1"), "to")
    )
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_5", "ds_5", "f1"), "to")
    )
    field(t, "dr_1", "ds_1", "f1").identity = "email"
    traversal = Traversal(DatasetGraph(*t), {"email": "X"})

    assert incoming_edges(traversal, CollectionAddress("dr_1", "ds_1")) == {
        Edge(
            FieldAddress("__ROOT__", "__ROOT__", "email"),
            FieldAddress("dr_1", "ds_1", "f1"),
        )
    }
    assert outgoing_edges(traversal, CollectionAddress("dr_1", "ds_1")) == {
        Edge(FieldAddress("dr_1", "ds_1", "f1"), FieldAddress("dr_3", "ds_3", "f1")),
        Edge(FieldAddress("dr_1", "ds_1", "f1"), FieldAddress("dr_4", "ds_4", "f1")),
        Edge(FieldAddress("dr_1", "ds_1", "f1"), FieldAddress("dr_5", "ds_5", "f1")),
        Edge(FieldAddress("dr_1", "ds_1", "f1"), FieldAddress("dr_2", "ds_2", "f1")),
    }

    assert outgoing_edges(traversal, CollectionAddress("dr_5", "ds_5")) == set()
    assert incoming_edges(traversal, CollectionAddress("dr_2", "ds_2")) == {
        Edge(FieldAddress("dr_1", "ds_1", "f1"), FieldAddress("dr_2", "ds_2", "f1"))
    }
    assert incoming_edges(traversal, CollectionAddress("dr_3", "ds_3")) == {
        Edge(FieldAddress("dr_1", "ds_1", "f1"), FieldAddress("dr_3", "ds_3", "f1"))
    }
    assert incoming_edges(traversal, CollectionAddress("dr_4", "ds_4")) == {
        Edge(FieldAddress("dr_1", "ds_1", "f1"), FieldAddress("dr_4", "ds_4", "f1"))
    }
    assert incoming_edges(traversal, CollectionAddress("dr_5", "ds_5")) == {
        Edge(FieldAddress("dr_1", "ds_1", "f1"), FieldAddress("dr_5", "ds_5", "f1"))
    }
    traversal_map, terminators = traversal.traversal_map()
    assert traversal_map == {
        "__ROOT__:__ROOT__": {"from": {}, "to": {"dr_1:ds_1": {"email -> f1"}}},
        "dr_1:ds_1": {
            "from": {"__ROOT__:__ROOT__": {"email -> f1"}},
            "to": {
                "dr_2:ds_2": {"f1 -> f1"},
                "dr_3:ds_3": {"f1 -> f1"},
                "dr_4:ds_4": {"f1 -> f1"},
                "dr_5:ds_5": {"f1 -> f1"},
            },
        },
        "dr_2:ds_2": {"from": {"dr_1:ds_1": {"f1 -> f1"}}, "to": {}},
        "dr_3:ds_3": {"from": {"dr_1:ds_1": {"f1 -> f1"}}, "to": {}},
        "dr_4:ds_4": {"from": {"dr_1:ds_1": {"f1 -> f1"}}, "to": {}},
        "dr_5:ds_5": {"from": {"dr_1:ds_1": {"f1 -> f1"}}, "to": {}},
    }

    assert set(terminators) == {
        CollectionAddress("dr_2", "ds_2"),
        CollectionAddress("dr_3", "ds_3"),
        CollectionAddress("dr_4", "ds_4"),
        CollectionAddress("dr_5", "ds_5"),
    }


def test_variant_traversals() -> None:
    """test traversal that varies based on input and requires identity traversal_node visit from multiple sources"""
    customers = Collection(
        name="customer",
        fields=[
            ScalarField(name="id"),
            ScalarField(name="email", identity="email"),
            ScalarField(
                name="user_id",
                references=[(FieldAddress("mysql", "user", "id"), "to")],
            ),
        ],
    )
    users = Collection(
        name="user",
        fields=[ScalarField(name="id"), ScalarField(name="ssn", identity="ssn")],
    )

    graph = DatasetGraph(
        GraphDataset(
            name="mysql",
            collections=[customers, users],
            connection_key="mock_connection_config_key",
        )
    )

    traversal_map1, terminators1 = Traversal(
        graph,
        {"email": "X"},
    ).traversal_map()

    assert traversal_map1 == {
        "__ROOT__:__ROOT__": {"from": {}, "to": {"mysql:customer": {"email -> email"}}},
        "mysql:customer": {
            "from": {"__ROOT__:__ROOT__": {"email -> email"}},
            "to": {"mysql:user": {"user_id -> id"}},
        },
        "mysql:user": {"from": {"mysql:customer": {"user_id -> id"}}, "to": {}},
    }
    assert terminators1 == [CollectionAddress("mysql", "user")]

    traversal_map2, terminators2 = Traversal(
        graph,
        {"email": "X", "ssn": "Y"},
    ).traversal_map()
    assert traversal_map2 == {
        "__ROOT__:__ROOT__": {
            "from": {},
            "to": {"mysql:user": {"ssn -> ssn"}, "mysql:customer": {"email -> email"}},
        },
        "mysql:user": {
            "from": {
                "__ROOT__:__ROOT__": {"ssn -> ssn"},
                "mysql:customer": {"user_id -> id"},
            },
            "to": {},
        },
        "mysql:customer": {
            "from": {"__ROOT__:__ROOT__": {"email -> email"}},
            "to": {"mysql:user": {"user_id -> id"}},
        },
    }
    assert terminators2 == [CollectionAddress("mysql", "user")]

    with pytest.raises(TraversalError):
        Traversal(
            graph,
            {"ssn": "Y"},
        ).traversal_map()


def test_tree_linear() -> None:
    """test of tree with all nodes in a chain"""
    t = generate_graph_resources(5)
    field(t, "dr_1", "ds_1", "f1").references.append(
        (FieldAddress("dr_2", "ds_2", "f1"), None)
    )
    field(t, "dr_2", "ds_2", "f1").references.append(
        (FieldAddress("dr_3", "ds_3", "f1"), None)
    )
    field(t, "dr_3", "ds_3", "f1").references.append(
        (FieldAddress("dr_4", "ds_4", "f1"), None)
    )
    field(t, "dr_4", "ds_4", "f1").references.append(
        (FieldAddress("dr_5", "ds_5", "f1"), None)
    )
    field(t, "dr_1", "ds_1", "f1").identity = "email"
    traversal = Traversal(DatasetGraph(*t), {"email": "X"})

    assert set(incoming_edges(traversal, CollectionAddress("dr_1", "ds_1"))) == {
        Edge(
            FieldAddress("__ROOT__", "__ROOT__", "email"),
            FieldAddress("dr_1", "ds_1", "f1"),
        )
    }
    assert outgoing_edges(traversal, CollectionAddress("dr_1", "ds_1")) == {
        Edge(FieldAddress("dr_1", "ds_1", "f1"), FieldAddress("dr_2", "ds_2", "f1"))
    }
    assert outgoing_edges(traversal, CollectionAddress("dr_5", "ds_5")) == set()
    assert set(incoming_edges(traversal, CollectionAddress("dr_2", "ds_2"))) == {
        Edge(FieldAddress("dr_1", "ds_1", "f1"), FieldAddress("dr_2", "ds_2", "f1"))
    }
    traversal_map, terminators = traversal.traversal_map()
    assert traversal_map == {
        "__ROOT__:__ROOT__": {"from": {}, "to": {"dr_1:ds_1": {"email -> f1"}}},
        "dr_1:ds_1": {
            "from": {"__ROOT__:__ROOT__": {"email -> f1"}},
            "to": {"dr_2:ds_2": {"f1 -> f1"}},
        },
        "dr_2:ds_2": {
            "from": {"dr_1:ds_1": {"f1 -> f1"}},
            "to": {"dr_3:ds_3": {"f1 -> f1"}},
        },
        "dr_3:ds_3": {
            "from": {"dr_2:ds_2": {"f1 -> f1"}},
            "to": {"dr_4:ds_4": {"f1 -> f1"}},
        },
        "dr_4:ds_4": {
            "from": {"dr_3:ds_3": {"f1 -> f1"}},
            "to": {"dr_5:ds_5": {"f1 -> f1"}},
        },
        "dr_5:ds_5": {"from": {"dr_4:ds_4": {"f1 -> f1"}}, "to": {}},
    }

    assert terminators == [CollectionAddress("dr_5", "ds_5")]


def test_tree_binary_tree() -> None:
    """test of tree with all nodes in a chain"""
    t = generate_binary_tree_resources(4, 3)
    field(t, "root", "ds", "f1").identity = "email"
    field(t, "root.0.1.0", "ds.0.1.0", "f1").identity = "ssn"
    field(t, "root.1.1", "ds.1.1", "f1").identity = "user_id"
    assert generate_traversal({"email": "X"}, *t)
    assert generate_traversal({"ssn": "X"}, *t)
    assert generate_traversal({"user_id": "X"}, *t)


def test_after_collection() -> None:
    t1 = generate_fully_connected_resources(5)
    field(t1, "dr_1", "ds_1", "f1").identity = "email"
    collection(t1, CollectionAddress("dr_2", "ds_2")).after.add(
        CollectionAddress("dr_5", "ds_5")
    )
    j1 = generate_traversal({"email": "1"}, *t1)

    t2 = generate_fully_connected_resources(5)
    field(t2, "dr_1", "ds_1", "f1").identity = "email"
    collection(t2, CollectionAddress("dr_5", "ds_5")).after.add(
        CollectionAddress("dr_2", "ds_2")
    )
    j2 = generate_traversal({"email": "1"}, *t2)

    assert j1 != j2


def test_after_dataresource() -> None:
    t1 = generate_fully_connected_resources(5)
    field(t1, "dr_1", "ds_1", "f1").identity = "email"
    dataresource(t1, "dr_2").after.add("dr_5")
    j1 = generate_traversal({"email": "1"}, *t1)

    t2 = generate_fully_connected_resources(5)
    field(t2, "dr_1", "ds_1", "f1").identity = "email"
    dataresource(t2, "dr_5").after.add("dr_2")
    j2 = generate_traversal({"email": "1"}, *t2)

    assert j1 != j2


def test_different_seed_alters_traversal() -> None:
    t1 = generate_fully_connected_resources(5)
    field(t1, "dr_1", "ds_1", "f1").identity = "email"
    field(t1, "dr_2", "ds_2", "f1").identity = "user_id"
    field(t1, "dr_3", "ds_3", "f1").identity = "ssn"
    field(t1, "dr_4", "ds_4", "f1").identity = "email"
    graph = DatasetGraph(*t1)
    # the number of the start nodes (that is, the children of the virtul
    # root traversal_node) in a traversal will = the # of nodes whose identities
    # match an available seed value.
    assert (
        len(Traversal(graph, {"email": "1"}).root_node.children) == 2
    )  # there are 2 email nodes
    assert len(Traversal(graph, {"user_id": "1"}).root_node.children) == 1
    assert len(Traversal(graph, {"ssn": "1"}).root_node.children) == 1
    assert len(Traversal(graph, {"ssn": "1", "email": "1"}).root_node.children) == 3
    assert (
        len(Traversal(graph, {"ssn": "1", "email": 1, "user_id": 1}).root_node.children)
        == 4
    )
