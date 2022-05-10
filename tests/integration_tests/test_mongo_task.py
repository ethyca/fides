import copy
import random
from datetime import datetime
from unittest import mock
from unittest.mock import Mock

import dask
import pytest
from bson import ObjectId

from fidesops.graph.config import (
    FieldAddress,
    ScalarField,
    Collection,
    Dataset,
)
from fidesops.graph.data_type import (
    IntTypeConverter,
    StringTypeConverter,
    ObjectIdTypeConverter,
)
from fidesops.graph.graph import DatasetGraph, Node, Edge
from fidesops.graph.traversal import TraversalNode
from fidesops.models.connectionconfig import (
    ConnectionConfig,
)
from fidesops.models.datasetconfig import convert_dataset_to_graph
from fidesops.models.policy import Policy
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.schemas.dataset import FidesopsDataset
from fidesops.service.connectors import get_connector
from fidesops.task import graph_task
from fidesops.task.filter_results import filter_data_categories
from fidesops.task.graph_task import (
    get_cached_data_for_erasures,
)

from ..graph.graph_test_util import assert_rows_match, erasure_policy, field
from ..task.traversal_data import (
    integration_db_graph,
    integration_db_mongo_graph,
    combined_mongo_postgresql_graph,
)

dask.config.set(scheduler="processes")
empty_policy = Policy()


@pytest.mark.integration
def test_combined_erasure_task(
    db,
    mongo_inserts,
    postgres_inserts,
    integration_mongodb_config,
    integration_postgres_config,
    integration_mongodb_connector,
):
    """Includes examples of mongo nested and array erasures"""
    policy = erasure_policy("A", "B")
    seed_email = postgres_inserts["customer"][0]["email"]
    privacy_request = PrivacyRequest(
        id=f"test_sql_erasure_task_{random.randint(0, 1000)}"
    )
    mongo_dataset, postgres_dataset = combined_mongo_postgresql_graph(
        integration_postgres_config, integration_mongodb_config
    )

    field([postgres_dataset], "postgres_example", "address", "city").data_categories = [
        "A"
    ]
    field(
        [postgres_dataset], "postgres_example", "address", "state"
    ).data_categories = ["B"]
    field([postgres_dataset], "postgres_example", "address", "zip").data_categories = [
        "C"
    ]
    field(
        [postgres_dataset], "postgres_example", "customer", "name"
    ).data_categories = ["A"]
    field([mongo_dataset], "mongo_test", "address", "city").data_categories = ["A"]
    field([mongo_dataset], "mongo_test", "address", "state").data_categories = ["B"]
    field([mongo_dataset], "mongo_test", "address", "zip").data_categories = ["C"]
    field(
        [mongo_dataset], "mongo_test", "customer_details", "workplace_info", "position"
    ).data_categories = ["A"]
    field(
        [mongo_dataset], "mongo_test", "customer_details", "emergency_contacts", "phone"
    ).data_categories = ["B"]
    field(
        [mongo_dataset], "mongo_test", "customer_details", "children"
    ).data_categories = ["B"]
    field(
        [mongo_dataset], "mongo_test", "internal_customer_profile", "derived_interests"
    ).data_categories = ["B"]
    field([mongo_dataset], "mongo_test", "employee", "email").data_categories = ["B"]
    field(
        [mongo_dataset],
        "mongo_test",
        "customer_feedback",
        "customer_information",
        "phone",
    ).data_categories = ["A"]

    field(
        [mongo_dataset], "mongo_test", "conversations", "thread", "chat_name"
    ).data_categories = ["B"]
    field(
        [mongo_dataset],
        "mongo_test",
        "flights",
        "passenger_information",
        "passenger_ids",
    ).data_categories = ["A"]
    field([mongo_dataset], "mongo_test", "aircraft", "planes").data_categories = ["A"]

    graph = DatasetGraph(mongo_dataset, postgres_dataset)

    graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config, integration_postgres_config],
        {"email": seed_email},
    )

    x = graph_task.run_erasure(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config, integration_postgres_config],
        {"email": seed_email},
        get_cached_data_for_erasures(privacy_request.id),
    )

    assert x == {
        "postgres_example:customer": 1,
        "mongo_test:employee": 2,
        "mongo_test:customer_feedback": 1,
        "mongo_test:internal_customer_profile": 1,
        "postgres_example:payment_card": 0,
        "postgres_example:orders": 0,
        "mongo_test:customer_details": 1,
        "mongo_test:address": 1,
        "postgres_example:address": 2,
        "mongo_test:orders": 0,
        "mongo_test:flights": 1,
        "mongo_test:conversations": 2,
        "mongo_test:aircraft": 1,
        "mongo_test:rewards": 0,
    }

    rerun_access = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config, integration_postgres_config],
        {"email": seed_email},
    )

    # Nested resource deleted
    assert (
        rerun_access["mongo_test:customer_details"][0]["workplace_info"]["position"]
        is None
    )
    # Untargeted nested resource is not deleted
    assert (
        rerun_access["mongo_test:customer_details"][0]["workplace_info"]["employer"]
        is not None
    )
    # Every element in array field deleted
    assert rerun_access["mongo_test:customer_details"][0]["children"] == [None, None]

    # Nested resource deleted
    assert (
        rerun_access["mongo_test:customer_feedback"][0]["customer_information"]["phone"]
        is None
    )
    # Untarged nested resource is not deleted
    assert (
        rerun_access["mongo_test:customer_feedback"][0]["customer_information"]["email"]
        is not None
    )

    # Every element in array field deleted
    assert rerun_access["mongo_test:internal_customer_profile"][0][
        "derived_interests"
    ] == [None, None]

    # Untargeted nested resource not deleted
    assert rerun_access["mongo_test:internal_customer_profile"][0][
        "customer_identifiers"
    ] == {"internal_id": "cust_014"}

    # Only the chat name in the matched array elements are masked (reference field)
    mongo_db = integration_mongodb_connector["mongo_test"]
    thread_one = mongo_db.conversations.find_one({"id": "thread_1"})
    thread_two = mongo_db.conversations.find_one({"id": "thread_2"})
    assert thread_one["thread"] == [
        {
            "comment": "com_0011",
            "message": "hey do you know when we're landing?",
            "chat_name": None,
            "ccn": "123456789",
        },
        {
            "comment": "com_0012",
            "message": "the detour we're taking for the storm we'll probably add an hour",
            "chat_name": "Jenny C",
            "ccn": "987654321",
        },
    ]
    assert thread_two["thread"] == [
        {
            "comment": "com_0013",
            "message": "should we text Grace when we land or should we just surprise her?",
            "chat_name": None,
            "ccn": "123456789",
        },
        {
            "comment": "com_0014",
            "message": "I think we should give her a heads-up",
            "chat_name": "Jenny C",
            "ccn": "987654321",
        },
        {
            "comment": "com_0015",
            "message": "Aw but she loves surprises.",
            "chat_name": None,
            "ccn": "123456789",
        },
        {
            "comment": "com_0016",
            "message": "I'm pretty sure she needs the peace of mind",
            "chat_name": "Jenny C",
        },
    ]

    # Assert only matched elements in array are masked (reference field)
    flights = mongo_db.flights.find_one({"id": "cust_flight_1"})
    assert flights["passenger_information"]["passenger_ids"] == [
        "old_travel_number",
        None,
    ]

    # Assert only matched element in array is matched (reference field)
    aircraft = mongo_db.aircraft.find_one({"id": "plane_type_1"})
    # Integer field was used to locate string in arrays
    assert aircraft["planes"] == ["20001", None, "20003", "20004", "20005"]

    # Assert two rows targeted by array field
    employee_3 = mongo_db.employee.find_one({"id": "3"})
    assert employee_3["email"] is None
    employee_4 = mongo_db.employee.find_one({"id": "4"})
    assert employee_4["email"] is None


@pytest.mark.integration_mongodb
@pytest.mark.integration
def test_mongo_erasure_task(db, mongo_inserts, integration_mongodb_config):
    policy = erasure_policy("A", "B")
    seed_email = mongo_inserts["customer"][0]["email"]
    privacy_request = PrivacyRequest(
        id=f"test_sql_erasure_task_{random.randint(0, 1000)}"
    )

    dataset, graph = integration_db_mongo_graph(
        "mongo_test", integration_mongodb_config.key
    )
    field([dataset], "mongo_test", "address", "city").data_categories = ["A"]
    field([dataset], "mongo_test", "address", "state").data_categories = ["B"]
    field([dataset], "mongo_test", "address", "zip").data_categories = ["C"]
    field([dataset], "mongo_test", "customer", "name").data_categories = ["A"]

    graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config],
        {"email": seed_email},
    )
    v = graph_task.run_erasure(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config],
        {"email": seed_email},
        get_cached_data_for_erasures(privacy_request.id),
    )

    assert v == {
        "mongo_test:customer": 1,
        "mongo_test:payment_card": 0,
        "mongo_test:orders": 0,
        "mongo_test:address": 2,
    }


@pytest.mark.integration_mongodb
@pytest.mark.integration
def test_dask_mongo_task(integration_mongodb_config: ConnectionConfig) -> None:
    privacy_request = PrivacyRequest(id=f"test_mongo_task_{random.randint(0,1000)}")

    v = graph_task.run_access_request(
        privacy_request,
        empty_policy,
        integration_db_graph("mongo_test", integration_mongodb_config.key),
        [integration_mongodb_config],
        {"email": "customer-1@example.com"},
    )

    assert_rows_match(
        v["mongo_test:orders"],
        min_size=3,
        keys=["id", "customer_id", "payment_card_id"],
    )
    assert_rows_match(
        v["mongo_test:payment_card"],
        min_size=2,
        keys=["id", "name", "ccn", "customer_id"],
    )
    assert_rows_match(
        v["mongo_test:customer"],
        min_size=1,
        keys=["id", "name", "email"],
    )

    # links
    assert v["mongo_test:customer"][0]["email"] == "customer-1@example.com"


@pytest.mark.integration_mongodb
@pytest.mark.integration
def test_composite_key_erasure(
    db,
    integration_mongodb_config: ConnectionConfig,
) -> None:

    privacy_request = PrivacyRequest(id=f"test_mongo_task_{random.randint(0,1000)}")
    policy = erasure_policy("A")
    customer = Collection(
        name="customer",
        fields=[
            ScalarField(name="id", primary_key=True),
            ScalarField(
                name="email",
                identity="email",
                data_type_converter=StringTypeConverter(),
            ),
        ],
    )

    composite_pk_test = Collection(
        name="composite_pk_test",
        fields=[
            ScalarField(
                name="id_a",
                primary_key=True,
                data_type_converter=IntTypeConverter(),
            ),
            ScalarField(
                name="id_b",
                primary_key=True,
                data_type_converter=IntTypeConverter(),
            ),
            ScalarField(
                name="description",
                data_type_converter=StringTypeConverter(),
                data_categories=["A"],
            ),
            ScalarField(
                name="customer_id",
                data_type_converter=IntTypeConverter(),
                references=[(FieldAddress("mongo_test", "customer", "id"), "from")],
            ),
        ],
    )

    dataset = Dataset(
        name="mongo_test",
        collections=[customer, composite_pk_test],
        connection_key=integration_mongodb_config.key,
    )

    access_request_data = graph_task.run_access_request(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_mongodb_config],
        {"email": "customer-1@example.com"},
    )

    customer = access_request_data["mongo_test:customer"][0]
    composite_pk_test = access_request_data["mongo_test:composite_pk_test"][0]

    assert customer["id"] == 1
    assert composite_pk_test["customer_id"] == 1

    # erasure
    erasure = graph_task.run_erasure(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_mongodb_config],
        {"email": "employee-1@example.com"},
        get_cached_data_for_erasures(privacy_request.id),
    )

    assert erasure == {"mongo_test:customer": 0, "mongo_test:composite_pk_test": 1}

    # re-run access request. Description has been
    # nullified here.
    access_request_data = graph_task.run_access_request(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_mongodb_config],
        {"email": "customer-1@example.com"},
    )

    assert access_request_data["mongo_test:composite_pk_test"][0]["description"] is None


@pytest.mark.integration_mongodb
@pytest.mark.integration
def test_access_erasure_type_conversion(
    db,
    integration_mongodb_config: ConnectionConfig,
) -> None:
    """Retrieve data from the type_link table. This requires retrieving data from
    the employee foreign_id field, which is an object_id stored as a string, and
    converting it into an object_id to query against the type_link_test._id field."""
    privacy_request = PrivacyRequest(id=f"test_mongo_task_{random.randint(0,1000)}")
    policy = erasure_policy("A")
    employee = Collection(
        name="employee",
        fields=[
            ScalarField(name="id", primary_key=True),
            ScalarField(name="name", data_type_converter=StringTypeConverter()),
            ScalarField(
                name="email",
                identity="email",
                data_type_converter=StringTypeConverter(),
            ),
            ScalarField(name="foreign_id", data_type_converter=StringTypeConverter()),
        ],
    )

    type_link = Collection(
        name="type_link_test",
        fields=[
            ScalarField(
                name="_id",
                primary_key=True,
                data_type_converter=ObjectIdTypeConverter(),
                references=[
                    (FieldAddress("mongo_test", "employee", "foreign_id"), "from")
                ],
            ),
            ScalarField(
                name="name",
                data_type_converter=StringTypeConverter(),
                data_categories=["A"],
            ),
            ScalarField(name="key", data_type_converter=IntTypeConverter()),
        ],
    )

    dataset = Dataset(
        name="mongo_test",
        collections=[employee, type_link],
        connection_key=integration_mongodb_config.key,
    )

    access_request_data = graph_task.run_access_request(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_mongodb_config],
        {"email": "employee-1@example.com"},
    )

    employee = access_request_data["mongo_test:employee"][0]
    link = access_request_data["mongo_test:type_link_test"][0]

    assert employee["foreign_id"] == "000000000000000000000001"
    assert link["_id"] == ObjectId("000000000000000000000001")

    # erasure
    erasure = graph_task.run_erasure(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_mongodb_config],
        {"email": "employee-1@example.com"},
        get_cached_data_for_erasures(privacy_request.id),
    )

    assert erasure == {"mongo_test:employee": 0, "mongo_test:type_link_test": 1}


@pytest.mark.integration
def test_object_querying_mongo(
    db,
    privacy_request,
    example_datasets,
    policy,
    integration_mongodb_config,
    integration_postgres_config,
):

    postgres_config = copy.copy(integration_postgres_config)

    dataset_postgres = FidesopsDataset(**example_datasets[0])
    graph = convert_dataset_to_graph(dataset_postgres, integration_postgres_config.key)
    dataset_mongo = FidesopsDataset(**example_datasets[1])
    mongo_graph = convert_dataset_to_graph(
        dataset_mongo, integration_mongodb_config.key
    )
    dataset_graph = DatasetGraph(*[graph, mongo_graph])

    access_request_results = graph_task.run_access_request(
        privacy_request,
        policy,
        dataset_graph,
        [postgres_config, integration_mongodb_config],
        {"email": "customer-1@example.com"},
    )

    target_categories = {
        "user.provided.identifiable.gender",
        "user.provided.identifiable.date_of_birth",
    }
    filtered_results = filter_data_categories(
        access_request_results,
        target_categories,
        dataset_graph.data_category_field_mapping,
    )

    # Mongo results obtained via customer_id relationship from postgres_example_test_dataset.customer.id
    assert filtered_results == {
        "mongo_test:customer_details": [
            {"gender": "male", "birthday": datetime(1988, 1, 10, 0, 0)}
        ]
    }

    # mongo_test:customer_feedback collection reached via nested identity
    target_categories = {"user.provided.identifiable.contact.phone_number"}
    filtered_results = filter_data_categories(
        access_request_results,
        target_categories,
        dataset_graph.data_category_field_mapping,
    )
    assert filtered_results["mongo_test:customer_feedback"][0] == {
        "customer_information": {"phone": "333-333-3333"}
    }

    # Includes nested workplace_info.position field
    target_categories = {"user.provided.identifiable"}
    filtered_results = filter_data_categories(
        access_request_results,
        target_categories,
        dataset_graph.data_category_field_mapping,
    )
    assert len(filtered_results["mongo_test:customer_details"]) == 1

    # Array of embedded emergency contacts returned, array of children, nested array of workplace_info.direct_reports
    assert filtered_results["mongo_test:customer_details"][0] == {
        "birthday": datetime(1988, 1, 10, 0, 0),
        "gender": "male",
        "children": ["Christopher Customer", "Courtney Customer"],
        "emergency_contacts": [
            {"name": "June Customer", "phone": "444-444-4444"},
            {"name": "Josh Customer", "phone": "111-111-111"},
        ],
        "workplace_info": {
            "position": "Chief Strategist",
            "direct_reports": ["Robbie Margo", "Sully Hunter"],
        },
    }

    # Includes data retrieved from a nested field that was joined with a nested field from another table
    target_categories = {"user.derived"}
    filtered_results = filter_data_categories(
        access_request_results,
        target_categories,
        dataset_graph.data_category_field_mapping,
    )

    # Test for accessing array
    assert filtered_results["mongo_test:internal_customer_profile"][0] == {
        "derived_interests": ["marketing", "food"]
    }


@pytest.mark.integration
def test_get_cached_data_for_erasures(
    integration_postgres_config, integration_mongodb_config, policy
) -> None:
    privacy_request = PrivacyRequest(id=f"test_mongo_task_{random.randint(0,1000)}")

    mongo_dataset, postgres_dataset = combined_mongo_postgresql_graph(
        integration_postgres_config, integration_mongodb_config
    )
    graph = DatasetGraph(mongo_dataset, postgres_dataset)

    access_request_results = graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config, integration_postgres_config],
        {"email": "customer-1@example.com"},
    )
    cached_data_for_erasures = get_cached_data_for_erasures(privacy_request.id)

    # Cached raw results preserve the indices
    assert cached_data_for_erasures["mongo_test:conversations"][0]["thread"] == [
        {
            "comment": "com_0001",
            "message": "hello, testing in-flight chat feature",
            "chat_name": "John C",
            "ccn": "123456789",
        },
        "FIDESOPS_DO_NOT_MASK",
    ]

    # The access request results are filtered on array data, because it was an entrypoint into the node.
    assert access_request_results["mongo_test:conversations"][0]["thread"] == [
        {
            "comment": "com_0001",
            "message": "hello, testing in-flight chat feature",
            "chat_name": "John C",
            "ccn": "123456789",
        }
    ]


@pytest.mark.integration
def test_return_all_elements_config_access_request(
    db,
    privacy_request,
    example_datasets,
    policy,
    integration_mongodb_config,
    integration_postgres_config,
    integration_mongodb_connector,
):
    """Annotating array entrypoint field with return_all_elements=true means both the entire array is returned from the
    queried data and used to locate data in other collections

    mongo_test:internal_customer_profile.customer_identifiers.derived_phone field and mongo_test:rewards.owner field
    have return_all_elements set to True
    """
    postgres_config = copy.copy(integration_postgres_config)

    dataset_postgres = FidesopsDataset(**example_datasets[0])
    graph = convert_dataset_to_graph(dataset_postgres, integration_postgres_config.key)
    dataset_mongo = FidesopsDataset(**example_datasets[1])
    mongo_graph = convert_dataset_to_graph(
        dataset_mongo, integration_mongodb_config.key
    )
    dataset_graph = DatasetGraph(*[graph, mongo_graph])

    access_request_results = graph_task.run_access_request(
        privacy_request,
        policy,
        dataset_graph,
        [postgres_config, integration_mongodb_config],
        {"phone_number": "254-344-9868", "email": "jane@gmail.com"},
    )

    # Both indices in mongo_test:internal_customer_profile.customer_identifiers.derived_phone are returned from the node
    assert access_request_results["mongo_test:internal_customer_profile"][0][
        "customer_identifiers"
    ]["derived_phone"] == ["530-486-6983", "254-344-9868"]

    # Assert both phone numbers are then used to locate records in rewards collection.
    # All nested documents are returned because return_all_elements=true also specified
    assert len(access_request_results["mongo_test:rewards"]) == 2
    assert access_request_results["mongo_test:rewards"][0]["owner"] == [
        {"phone": "530-486-6983", "shopper_name": "janec"},
        {"phone": "818-695-1881", "shopper_name": "janec"},
    ]
    assert access_request_results["mongo_test:rewards"][1]["owner"] == [
        {"phone": "254-344-9868", "shopper_name": "janec"}
    ]


@pytest.mark.integration
def test_return_all_elements_config_erasure(
    mongo_inserts,
    postgres_inserts,
    integration_mongodb_config,
    integration_postgres_config,
    integration_mongodb_connector,
):
    """Includes examples of mongo nested and array erasures"""
    policy = erasure_policy("A", "B")

    privacy_request = PrivacyRequest(
        id=f"test_sql_erasure_task_{random.randint(0, 1000)}"
    )
    mongo_dataset, postgres_dataset = combined_mongo_postgresql_graph(
        integration_postgres_config, integration_mongodb_config
    )

    field(
        [mongo_dataset], "mongo_test", "rewards", "owner", "phone"
    ).data_categories = ["A"]
    field(
        [mongo_dataset],
        "mongo_test",
        "internal_customer_profile",
        "customer_identifiers",
        "derived_phone",
    ).data_categories = ["B"]

    graph = DatasetGraph(mongo_dataset, postgres_dataset)

    seed_email = postgres_inserts["customer"][0]["email"]
    seed_phone = mongo_inserts["rewards"][0]["owner"][0]["phone"]

    graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config, integration_postgres_config],
        {"email": seed_email, "phone_number": seed_phone},
    )

    x = graph_task.run_erasure(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config, integration_postgres_config],
        {"email": seed_email},
        get_cached_data_for_erasures(privacy_request.id),
    )

    assert x["mongo_test:internal_customer_profile"] == 1
    assert x["mongo_test:rewards"] == 2

    mongo_db = integration_mongodb_connector["mongo_test"]

    reward_one = mongo_db.rewards.find_one({"id": "rew_1"})
    # All phone numbers masked because return_all_elements is True
    assert reward_one["owner"][0]["phone"] is None
    assert reward_one["owner"][1]["phone"] is None

    reward_two = mongo_db.rewards.find_one({"id": "rew_2"})
    # Masked because targeted by another element in original array
    assert reward_two["owner"][0]["phone"] is None

    reward_three = mongo_db.rewards.find_one({"id": "rew_3"})
    # Not masked because not targeted by query
    assert reward_three["owner"][0]["phone"] is not None

    # Both elements in array entrypoint masked by return_all_elements is True
    assert mongo_db.internal_customer_profile.find_one({"id": "prof_3"})[
        "customer_identifiers"
    ]["derived_phone"] == [None, None]


@pytest.mark.integration
def test_array_querying_mongo(
    db,
    privacy_request,
    example_datasets,
    policy,
    integration_mongodb_config,
    integration_postgres_config,
):
    postgres_config = copy.copy(integration_postgres_config)

    dataset_postgres = FidesopsDataset(**example_datasets[0])
    graph = convert_dataset_to_graph(dataset_postgres, integration_postgres_config.key)
    dataset_mongo = FidesopsDataset(**example_datasets[1])
    mongo_graph = convert_dataset_to_graph(
        dataset_mongo, integration_mongodb_config.key
    )
    dataset_graph = DatasetGraph(*[graph, mongo_graph])

    access_request_results = graph_task.run_access_request(
        privacy_request,
        policy,
        dataset_graph,
        [postgres_config, integration_mongodb_config],
        {"email": "jane@example.com"},
    )

    # This is a different category than was specified on the policy, this is just for testing.
    target_categories = {"user.derived"}
    filtered_results = filter_data_categories(
        access_request_results,
        target_categories,
        dataset_graph.data_category_field_mapping,
    )
    # Array field mongo_test:internal_customer_profile.customer_identifiers contains identity
    # Only matching identity returned
    assert filtered_results["mongo_test:internal_customer_profile"][0][
        "customer_identifiers"
    ]["derived_emails"] == ["jane@example.com"]

    # # Entire derived_interests array returned - this is not an identity or "to" reference field
    assert filtered_results["mongo_test:internal_customer_profile"][0][
        "derived_interests"
    ] == ["interior design", "travel", "photography"]

    # This matches the category on the policy
    filtered_identifiable = filter_data_categories(
        access_request_results,
        {"user.provided.identifiable"},
        dataset_graph.data_category_field_mapping,
    )

    # Includes array field
    assert filtered_identifiable["mongo_test:customer_details"] == [
        {
            "birthday": datetime(1990, 2, 28, 0, 0),
            "gender": "female",
            "children": ["Erica Example"],
        }
    ]
    customer_detail_logs = privacy_request.execution_logs.filter_by(
        dataset_name="mongo_test", collection_name="customer_details", status="complete"
    )
    # Returns fields_affected for all possible targeted fields, even though this identity only had some
    # of them actually populated
    assert customer_detail_logs[0].fields_affected == [
        {
            "path": "mongo_test:customer_details:birthday",
            "field_name": "birthday",
            "data_categories": ["user.provided.identifiable.date_of_birth"],
        },
        {
            "path": "mongo_test:customer_details:children",
            "field_name": "children",
            "data_categories": ["user.provided.identifiable.childrens"],
        },
        {
            "path": "mongo_test:customer_details:emergency_contacts.name",
            "field_name": "emergency_contacts.name",
            "data_categories": ["user.provided.identifiable.name"],
        },
        {
            "path": "mongo_test:customer_details:workplace_info.direct_reports",
            "field_name": "workplace_info.direct_reports",
            "data_categories": ["user.provided.identifiable.name"],
        },
        {
            "path": "mongo_test:customer_details:emergency_contacts.phone",
            "field_name": "emergency_contacts.phone",
            "data_categories": ["user.provided.identifiable.contact.phone_number"],
        },
        {
            "path": "mongo_test:customer_details:gender",
            "field_name": "gender",
            "data_categories": ["user.provided.identifiable.gender"],
        },
        {
            "path": "mongo_test:customer_details:workplace_info.position",
            "field_name": "workplace_info.position",
            "data_categories": ["user.provided.identifiable.job_title"],
        },
    ]

    # items in array mongo_test:customer_details.travel_identifiers used to lookup matching array elements
    # in mongo_test:flights:passenger_information.passenger_ids.  passenger_information.full_name has relevant
    # data category.
    assert len(filtered_identifiable["mongo_test:flights"]) == 1
    assert filtered_identifiable["mongo_test:flights"][0] == {
        "passenger_information": {"full_name": "Jane Customer"}
    }
    completed_flight_logs = privacy_request.execution_logs.filter_by(
        dataset_name="mongo_test", collection_name="flights", status="complete"
    )
    assert completed_flight_logs.count() == 1
    assert completed_flight_logs[0].fields_affected == [
        {
            "path": "mongo_test:flights:passenger_information.full_name",
            "field_name": "passenger_information.full_name",
            "data_categories": ["user.provided.identifiable.name"],
        }
    ]

    # Nested customer_details:comments.comment_id field used to find embedded objects conversations.thread.comment
    # fields. Only matching embedded documents queried for relevant data categories
    assert filtered_identifiable["mongo_test:conversations"] == [
        {"thread": [{"chat_name": "Jane C", "ccn": "987654321"}]},
        {
            "thread": [
                {"chat_name": "Jane C", "ccn": "987654321"},
                {"chat_name": "Jane C"},
            ]
        },
    ]
    conversation_logs = privacy_request.execution_logs.filter_by(
        dataset_name="mongo_test", collection_name="conversations", status="complete"
    )
    assert conversation_logs.count() == 1
    assert conversation_logs[0].fields_affected == [
        {
            "path": "mongo_test:conversations:thread.chat_name",
            "field_name": "thread.chat_name",
            "data_categories": ["user.provided.identifiable.name"],
        },
        {
            "path": "mongo_test:conversations:thread.ccn",
            "field_name": "thread.ccn",
            "data_categories": ["user.provided.identifiable.financial.account_number"],
        },
    ]

    # Integer field mongo_test:flights.plane used to locate only matching elem in mongo_test:aircraft:planes array field
    assert access_request_results["mongo_test:aircraft"][0]["planes"] == ["30005"]
    # Filtered out, however, because there's no relevant matched data category
    assert filtered_identifiable["mongo_test:aircraft"] == []
    aircraft_logs = privacy_request.execution_logs.filter_by(
        dataset_name="mongo_test", collection_name="aircraft", status="complete"
    )
    assert aircraft_logs.count() == 1
    assert aircraft_logs[0].fields_affected == []

    # Values in mongo_test:flights:pilots array field used to locate scalar field in mongo_test:employee.id
    assert filtered_identifiable["mongo_test:employee"] == [
        {"email": "employee-2@example.com", "name": "Jane Employee"}
    ]
    employee_logs = privacy_request.execution_logs.filter_by(
        dataset_name="mongo_test", collection_name="employee", status="complete"
    )
    assert employee_logs.count() == 1
    assert employee_logs[0].fields_affected == [
        {
            "path": "mongo_test:employee:email",
            "field_name": "email",
            "data_categories": ["user.provided.identifiable.contact.email"],
        },
        {
            "path": "mongo_test:employee:name",
            "field_name": "name",
            "data_categories": ["user.provided.identifiable.name"],
        },
    ]

    # No data for identity in this collection
    assert access_request_results["mongo_test:customer_feedback"] == []
    customer_feedback_logs = privacy_request.execution_logs.filter_by(
        dataset_name="mongo_test",
        collection_name="customer_feedback",
        status="complete",
    )
    assert customer_feedback_logs.count() == 1
    # Returns all possible fields affected, even though there is no associated data for this collection
    assert customer_feedback_logs[0].fields_affected == [
        {
            "path": "mongo_test:customer_feedback:customer_information.phone",
            "field_name": "customer_information.phone",
            "data_categories": ["user.provided.identifiable.contact.phone_number"],
        }
    ]

    # Only matched embedded document in mongo_test:conversations.thread.ccn used to locate mongo_test:payment_card
    assert filtered_identifiable["mongo_test:payment_card"] == [
        {"code": "123", "name": "Example Card 2", "ccn": "987654321"}
    ]
    payment_logs = privacy_request.execution_logs.filter_by(
        dataset_name="mongo_test", collection_name="payment_card", status="complete"
    )
    assert payment_logs.count() == 1
    assert payment_logs[0].fields_affected == [
        {
            "path": "mongo_test:payment_card:ccn",
            "field_name": "ccn",
            "data_categories": ["user.provided.identifiable.financial.account_number"],
        },
        {
            "path": "mongo_test:payment_card:code",
            "field_name": "code",
            "data_categories": ["user.provided.identifiable.financial"],
        },
        {
            "path": "mongo_test:payment_card:name",
            "field_name": "name",
            "data_categories": ["user.provided.identifiable.financial"],
        },
    ]

    # Run again with different email
    access_request_results = graph_task.run_access_request(
        privacy_request,
        policy,
        dataset_graph,
        [postgres_config, integration_mongodb_config],
        {"email": "customer-1@example.com"},
    )
    filtered_identifiable = filter_data_categories(
        access_request_results,
        {"user.provided.identifiable"},
        dataset_graph.data_category_field_mapping,
    )

    # Two values in mongo_test:flights:pilots array field mapped to mongo_test:employee ids
    assert filtered_identifiable["mongo_test:employee"] == [
        {"name": "Jack Employee", "email": "employee-1@example.com"},
        {"name": "Jane Employee", "email": "employee-2@example.com"},
    ]

    # Only embedded documents matching mongo_test:conversations.thread.comment returned
    assert filtered_identifiable["mongo_test:conversations"] == [
        {"thread": [{"ccn": "123456789", "chat_name": "John C"}]},
        {
            "thread": [
                {"ccn": "123456789", "chat_name": "John C"},
                {"ccn": "123456789", "chat_name": "John C"},
            ]
        },
    ]


@pytest.mark.integration_mongodb
@pytest.mark.integration
class TestRetrievingDataMongo:
    @pytest.fixture
    def connector(self, integration_mongodb_config):
        return get_connector(integration_mongodb_config)

    @pytest.fixture
    def traversal_node(self, example_datasets, integration_mongodb_config):
        dataset = FidesopsDataset(**example_datasets[1])
        graph = convert_dataset_to_graph(dataset, integration_mongodb_config.key)
        customer_details_collection = None
        for collection in graph.collections:
            if collection.name == "customer_details":
                customer_details_collection = collection
                break
        node = Node(graph, customer_details_collection)
        traversal_node = TraversalNode(node)
        return traversal_node

    @mock.patch("fidesops.graph.traversal.TraversalNode.incoming_edges")
    def test_retrieving_data(
        self,
        mock_incoming_edges: Mock,
        privacy_request,
        db,
        connector,
        traversal_node,
    ):
        mock_incoming_edges.return_value = {
            Edge(
                FieldAddress("fake_dataset", "fake_collection", "id"),
                FieldAddress("mongo_test", "customer_details", "customer_id"),
            )
        }

        results = connector.retrieve_data(
            traversal_node, Policy(), privacy_request, {"customer_id": [1]}
        )

        assert results[0]["customer_id"] == 1

    @mock.patch("fidesops.graph.traversal.TraversalNode.incoming_edges")
    def test_retrieving_data_no_input(
        self,
        mock_incoming_edges: Mock,
        privacy_request,
        db,
        connector,
        traversal_node,
    ):
        mock_incoming_edges.return_value = {
            Edge(
                FieldAddress("fake_dataset", "fake_collection", "email"),
                FieldAddress("mongo_test", "customer_details", "customer_id"),
            )
        }
        results = connector.retrieve_data(
            traversal_node, Policy(), privacy_request, {"customer_id": []}
        )
        assert results == []

        results = connector.retrieve_data(traversal_node, Policy(), privacy_request, {})
        assert results == []

        results = connector.retrieve_data(
            traversal_node, Policy(), privacy_request, {"bad_key": ["test"]}
        )
        assert results == []

        results = connector.retrieve_data(
            traversal_node, Policy(), privacy_request, {"email": [None]}
        )
        assert results == []

        results = connector.retrieve_data(
            traversal_node, Policy(), privacy_request, {"email": None}
        )
        assert results == []

    @mock.patch("fidesops.graph.traversal.TraversalNode.incoming_edges")
    def test_retrieving_data_input_not_in_table(
        self,
        mock_incoming_edges: Mock,
        db,
        privacy_request,
        connection_config,
        example_datasets,
        connector,
        traversal_node,
    ):
        mock_incoming_edges.return_value = {
            Edge(
                FieldAddress("fake_dataset", "fake_collection", "email"),
                FieldAddress("mongo_test", "customer_details", "customer_id"),
            )
        }

        results = connector.retrieve_data(
            traversal_node, Policy(), privacy_request, {"customer_id": [5]}
        )

        assert results == []
