import copy
from datetime import datetime

import pytest
from bson import ObjectId
from fideslang.models import Dataset

from fides.api.graph.config import Collection, FieldAddress, GraphDataset, ScalarField
from fides.api.graph.data_type import (
    IntTypeConverter,
    ObjectIdTypeConverter,
    StringTypeConverter,
)
from fides.api.graph.graph import DatasetGraph, Edge, Node
from fides.api.graph.traversal import TraversalNode
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import RequestTask
from fides.api.service.connectors import get_connector
from fides.api.task.filter_results import filter_data_categories
from fides.api.task.graph_task import get_cached_data_for_erasures

from ...conftest import access_runner_tester, erasure_runner_tester
from ..graph.graph_test_util import assert_rows_match, erasure_policy, field
from ..task.traversal_data import (
    combined_mongo_postgresql_graph,
    integration_db_graph,
    integration_db_mongo_graph,
)

empty_policy = Policy()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_combined_erasure_task(
    db,
    postgres_inserts,
    integration_mongodb_config,
    integration_postgres_config,
    integration_mongodb_connector,
    privacy_request_with_erasure_policy,
    privacy_request,
    mongo_inserts,
    dsr_version,
    request,
):
    """Includes examples of mongo nested and array erasures"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    policy = erasure_policy(db, "user.name", "user.contact")
    seed_email = postgres_inserts["customer"][0]["email"]
    privacy_request_with_erasure_policy.policy_id = policy.id
    privacy_request_with_erasure_policy.save(db)

    mongo_dataset, postgres_dataset = combined_mongo_postgresql_graph(
        integration_postgres_config, integration_mongodb_config
    )

    field([postgres_dataset], "postgres_example", "address", "city").data_categories = [
        "user.name"
    ]
    field(
        [postgres_dataset], "postgres_example", "address", "state"
    ).data_categories = ["user.contact"]
    field([postgres_dataset], "postgres_example", "address", "zip").data_categories = [
        "user.email"
    ]
    field(
        [postgres_dataset], "postgres_example", "customer", "name"
    ).data_categories = ["user.name"]
    field([mongo_dataset], "mongo_test", "address", "city").data_categories = [
        "user.name"
    ]
    field([mongo_dataset], "mongo_test", "address", "state").data_categories = [
        "user.contact"
    ]
    field([mongo_dataset], "mongo_test", "address", "zip").data_categories = [
        "user.email"
    ]
    field(
        [mongo_dataset], "mongo_test", "customer_details", "workplace_info", "position"
    ).data_categories = ["user.name"]
    field(
        [mongo_dataset], "mongo_test", "customer_details", "emergency_contacts", "phone"
    ).data_categories = ["user.contact"]
    field(
        [mongo_dataset], "mongo_test", "customer_details", "children"
    ).data_categories = ["user.contact"]
    field(
        [mongo_dataset], "mongo_test", "internal_customer_profile", "derived_interests"
    ).data_categories = ["user.contact"]
    field([mongo_dataset], "mongo_test", "employee", "email").data_categories = [
        "user.contact"
    ]
    field(
        [mongo_dataset],
        "mongo_test",
        "customer_feedback",
        "customer_information",
        "phone",
    ).data_categories = ["user.name"]

    field(
        [mongo_dataset], "mongo_test", "conversations", "thread", "chat_name"
    ).data_categories = ["user.contact"]
    field(
        [mongo_dataset],
        "mongo_test",
        "flights",
        "passenger_information",
        "passenger_ids",
    ).data_categories = ["user.name"]
    field([mongo_dataset], "mongo_test", "aircraft", "planes").data_categories = [
        "user.name"
    ]

    graph = DatasetGraph(mongo_dataset, postgres_dataset)

    access_runner_tester(
        privacy_request_with_erasure_policy,
        policy,
        graph,
        [integration_mongodb_config, integration_postgres_config],
        {"email": seed_email},
        db,
    )

    x = erasure_runner_tester(
        privacy_request_with_erasure_policy,
        policy,
        graph,
        [integration_mongodb_config, integration_postgres_config],
        {"email": seed_email},
        get_cached_data_for_erasures(privacy_request_with_erasure_policy.id),
        db,
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

    rerun_access = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config, integration_postgres_config],
        {"email": seed_email},
        db,
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
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_mongo_erasure_task(
    db,
    mongo_inserts,
    integration_mongodb_config,
    dsr_version,
    request,
    privacy_request_with_erasure_policy,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    policy = erasure_policy(db, "user.name", "user.contact")
    seed_email = mongo_inserts["customer"][0]["email"]
    privacy_request_with_erasure_policy.policy_id = policy.id
    privacy_request_with_erasure_policy.save(db)

    dataset, graph = integration_db_mongo_graph(
        "mongo_test", integration_mongodb_config.key
    )
    field([dataset], "mongo_test", "address", "city").data_categories = ["user.name"]
    field([dataset], "mongo_test", "address", "state").data_categories = [
        "user.contact"
    ]
    field([dataset], "mongo_test", "address", "zip").data_categories = ["user.email"]
    field([dataset], "mongo_test", "customer", "name").data_categories = ["user.name"]

    access_runner_tester(
        privacy_request_with_erasure_policy,
        policy,
        graph,
        [integration_mongodb_config],
        {"email": seed_email},
        db,
    )
    v = erasure_runner_tester(
        privacy_request_with_erasure_policy,
        policy,
        graph,
        [integration_mongodb_config],
        {"email": seed_email},
        get_cached_data_for_erasures(privacy_request_with_erasure_policy.id),
        db,
    )
    assert v == {
        "mongo_test:customer": 1,
        "mongo_test:payment_card": 0,
        "mongo_test:orders": 0,
        "mongo_test:address": 2,
    }


@pytest.mark.integration_mongodb
@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_access_mongo_task(
    db,
    integration_mongodb_config: ConnectionConfig,
    dsr_version,
    privacy_request,
    request,
) -> None:
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    v = access_runner_tester(
        privacy_request,
        empty_policy,
        integration_db_graph("mongo_test", integration_mongodb_config.key),
        [integration_mongodb_config],
        {"email": "customer-1@example.com"},
        db,
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
@pytest.mark.asyncio
async def test_composite_key_erasure(
    db,
    integration_mongodb_config: ConnectionConfig,
    mongo_inserts,
    privacy_request,
    privacy_request_with_erasure_policy,
    use_dsr_3_0,
) -> None:
    policy = erasure_policy(db, "user.name")
    privacy_request_with_erasure_policy.policy_id = policy.id
    privacy_request_with_erasure_policy.save(db)

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
                data_categories=["user.name"],
            ),
            ScalarField(
                name="customer_id",
                data_type_converter=IntTypeConverter(),
                references=[(FieldAddress("mongo_test", "customer", "id"), "from")],
            ),
        ],
    )

    dataset = GraphDataset(
        name="mongo_test",
        collections=[customer, composite_pk_test],
        connection_key=integration_mongodb_config.key,
    )

    access_request_data = access_runner_tester(
        privacy_request_with_erasure_policy,
        policy,
        DatasetGraph(dataset),
        [integration_mongodb_config],
        {"email": "customer-1@example.com"},
        db,
    )

    customer = access_request_data["mongo_test:customer"][0]
    composite_pk_test = access_request_data["mongo_test:composite_pk_test"][0]

    assert customer["id"] == 1
    assert composite_pk_test["customer_id"] == 1

    # erasure
    erasure = erasure_runner_tester(
        privacy_request_with_erasure_policy,
        policy,
        DatasetGraph(dataset),
        [integration_mongodb_config],
        {"email": "employee-1@example.com"},
        get_cached_data_for_erasures(privacy_request_with_erasure_policy.id),
        db,
    )

    assert erasure == {"mongo_test:customer": 0, "mongo_test:composite_pk_test": 1}

    # re-run access request. Description has been
    # nullified here.

    access_request_data = access_runner_tester(
        privacy_request,
        policy,
        DatasetGraph(dataset),
        [integration_mongodb_config],
        {"email": "customer-1@example.com"},
        db,
    )

    assert access_request_data["mongo_test:composite_pk_test"][0]["description"] is None


@pytest.mark.integration_mongodb
@pytest.mark.integration
@pytest.mark.asyncio
async def test_access_erasure_type_conversion(
    db,
    integration_mongodb_config: ConnectionConfig,
    privacy_request_with_erasure_policy,
    use_dsr_3_0,
) -> None:
    """Retrieve data from the type_link table. This requires retrieving data from
    the employee foreign_id field, which is an object_id stored as a string, and
    converting it into an object_id to query against the type_link_test._id field."""

    policy = erasure_policy(db, "user.name")

    privacy_request_with_erasure_policy.policy_id = policy.id
    privacy_request_with_erasure_policy.save(db)

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
                data_categories=["user.name"],
            ),
            ScalarField(name="key", data_type_converter=IntTypeConverter()),
        ],
    )

    dataset = GraphDataset(
        name="mongo_test",
        collections=[employee, type_link],
        connection_key=integration_mongodb_config.key,
    )

    access_request_data = access_runner_tester(
        privacy_request_with_erasure_policy,
        policy,
        DatasetGraph(dataset),
        [integration_mongodb_config],
        {"email": "employee-1@example.com"},
        db,
    )

    employee = access_request_data["mongo_test:employee"][0]
    link = access_request_data["mongo_test:type_link_test"][0]

    assert employee["foreign_id"] == "000000000000000000000001"
    assert link["_id"] == ObjectId("000000000000000000000001")

    # erasure
    erasure = erasure_runner_tester(
        privacy_request_with_erasure_policy,
        policy,
        DatasetGraph(dataset),
        [integration_mongodb_config],
        {"email": "employee-1@example.com"},
        get_cached_data_for_erasures(privacy_request_with_erasure_policy.id),
        db,
    )

    assert erasure == {"mongo_test:employee": 0, "mongo_test:type_link_test": 1}


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_object_querying_mongo(
    db,
    privacy_request,
    example_datasets,
    policy,
    integration_mongodb_config,
    integration_postgres_config,
    dsr_version,
    request,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0
    postgres_config = copy.copy(integration_postgres_config)

    dataset_postgres = Dataset(**example_datasets[0])
    graph = convert_dataset_to_graph(dataset_postgres, integration_postgres_config.key)
    dataset_mongo = Dataset(**example_datasets[1])
    mongo_graph = convert_dataset_to_graph(
        dataset_mongo, integration_mongodb_config.key
    )
    dataset_graph = DatasetGraph(*[graph, mongo_graph])

    access_request_results = access_runner_tester(
        privacy_request,
        policy,
        dataset_graph,
        [postgres_config, integration_mongodb_config],
        {"email": "customer-1@example.com"},
        db,
    )

    target_categories = {
        "user.demographic.gender",
        "user.demographic.date_of_birth",
        "user.unique_id",
    }

    filtered_results = filter_data_categories(
        access_request_results, target_categories, dataset_graph
    )

    # Mongo results obtained via customer_id relationship from postgres_example_test_dataset.customer.id
    assert filtered_results == {
        "mongo_test:customer_details": [
            {
                "gender": "male",
                "birthday": datetime(1988, 1, 10, 0, 0),
                "customer_id": 1.0,
                "customer_uuid": "3b241101-e2bb-4255-8caf-4136c566a962",
            }
        ],
        "mongo_test:employee": [{"id": "1"}, {"id": "2"}],
        "mongo_test:payment_card": [{"customer_id": 1}],
        "postgres_example_test_dataset:customer": [{"id": 1}],
        "postgres_example_test_dataset:login": [
            {"customer_id": 1},
            {"customer_id": 1},
            {"customer_id": 1},
            {"customer_id": 1},
            {"customer_id": 1},
            {"customer_id": 1},
        ],
        "postgres_example_test_dataset:orders": [
            {"customer_id": 1},
            {"customer_id": 1},
            {"customer_id": 1},
        ],
        "postgres_example_test_dataset:payment_card": [{"customer_id": 1}],
        "postgres_example_test_dataset:service_request": [{"employee_id": 1}],
    }

    # mongo_test:customer_feedback collection reached via nested identity
    target_categories = {"user.contact.phone_number"}
    filtered_results = filter_data_categories(
        access_request_results,
        target_categories,
        dataset_graph,
    )
    assert filtered_results["mongo_test:customer_feedback"][0] == {
        "customer_information": {"phone": "333-333-3333"}
    }

    # Includes nested workplace_info.position field
    target_categories = {"user"}
    filtered_results = filter_data_categories(
        access_request_results,
        target_categories,
        dataset_graph,
    )
    assert len(filtered_results["mongo_test:customer_details"]) == 1

    # Array of embedded emergency contacts returned, array of children, nested array of workplace_info.direct_reports
    assert filtered_results["mongo_test:customer_details"][0]["birthday"] == datetime(
        1988, 1, 10, 0, 0
    )
    assert filtered_results["mongo_test:customer_details"][0]["gender"] == "male"
    assert filtered_results["mongo_test:customer_details"][0]["customer_id"] == 1.0
    assert filtered_results["mongo_test:customer_details"][0]["children"] == [
        "Christopher Customer",
        "Courtney Customer",
    ]
    assert filtered_results["mongo_test:customer_details"][0]["emergency_contacts"] == [
        {"name": "June Customer", "phone": "444-444-4444"},
        {"name": "Josh Customer", "phone": "111-111-111"},
    ]
    assert filtered_results["mongo_test:customer_details"][0]["workplace_info"] == {
        "position": "Chief Strategist",
        "direct_reports": ["Robbie Margo", "Sully Hunter"],
    }

    # Includes data retrieved from a nested field that was joined with a nested field from another table
    target_categories = {"user"}
    filtered_results = filter_data_categories(
        access_request_results,
        target_categories,
        dataset_graph,
    )

    # Test for accessing array
    assert filtered_results["mongo_test:internal_customer_profile"][0] == {
        "derived_interests": ["marketing", "food"]
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_cached_data_for_erasures(
    integration_postgres_config,
    integration_mongodb_config,
    policy,
    db,
    use_dsr_2_0,
    privacy_request,
) -> None:
    mongo_dataset, postgres_dataset = combined_mongo_postgresql_graph(
        integration_postgres_config, integration_mongodb_config
    )
    graph = DatasetGraph(mongo_dataset, postgres_dataset)

    access_request_results = access_runner_tester(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config, integration_postgres_config],
        {"email": "customer-1@example.com"},
        db,
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
@pytest.mark.asyncio
async def test_get_saved_data_for_erasures_3_0(
    integration_postgres_config,
    integration_mongodb_config,
    policy,
    db,
    use_dsr_3_0,
    privacy_request,
) -> None:
    mongo_dataset, postgres_dataset = combined_mongo_postgresql_graph(
        integration_postgres_config, integration_mongodb_config
    )
    graph = DatasetGraph(mongo_dataset, postgres_dataset)

    access_runner_tester(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config, integration_postgres_config],
        {"email": "customer-1@example.com"},
        db,
    )

    conversations_task = privacy_request.access_tasks.filter(
        RequestTask.collection_address == "mongo_test:conversations"
    ).first()

    # Assert access task saved data in erasure format, that will be copied over to the erasure
    # nodes of the same name
    assert conversations_task.get_data_for_erasures()[0]["thread"] == [
        {
            "comment": "com_0001",
            "message": "hello, testing in-flight chat feature",
            "chat_name": "John C",
            "ccn": "123456789",
        },
        "FIDESOPS_DO_NOT_MASK",
    ]

    # The access request results are filtered on array data, because it was an entrypoint into the node.
    assert conversations_task.get_access_data()[0]["thread"] == [
        {
            "comment": "com_0001",
            "message": "hello, testing in-flight chat feature",
            "chat_name": "John C",
            "ccn": "123456789",
        }
    ]


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_return_all_elements_config_access_request(
    db,
    privacy_request,
    example_datasets,
    policy,
    integration_mongodb_config,
    integration_postgres_config,
    integration_mongodb_connector,
    dsr_version,
    request,
):
    """Annotating array entrypoint field with return_all_elements=true means both the entire array is returned from the
    queried data and used to locate data in other collections

    mongo_test:internal_customer_profile.customer_identifiers.derived_phone field and mongo_test:rewards.owner field
    have return_all_elements set to True
    """
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    postgres_config = copy.copy(integration_postgres_config)

    dataset_postgres = Dataset(**example_datasets[0])
    graph = convert_dataset_to_graph(dataset_postgres, integration_postgres_config.key)
    dataset_mongo = Dataset(**example_datasets[1])
    mongo_graph = convert_dataset_to_graph(
        dataset_mongo, integration_mongodb_config.key
    )
    dataset_graph = DatasetGraph(*[graph, mongo_graph])

    access_request_results = access_runner_tester(
        privacy_request,
        policy,
        dataset_graph,
        [postgres_config, integration_mongodb_config],
        {"phone_number": "254-344-9868", "email": "jane@gmail.com"},
        db,
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
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_return_all_elements_config_erasure(
    db,
    mongo_inserts,
    postgres_inserts,
    integration_mongodb_config,
    integration_postgres_config,
    integration_mongodb_connector,
    dsr_version,
    request,
    privacy_request,
):
    """Includes examples of mongo nested and array erasures"""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    policy = erasure_policy(db, "user.name", "user.contact")
    privacy_request.policy_id = policy.id
    privacy_request.save(db)

    mongo_dataset, postgres_dataset = combined_mongo_postgresql_graph(
        integration_postgres_config, integration_mongodb_config
    )

    field(
        [mongo_dataset], "mongo_test", "rewards", "owner", "phone"
    ).data_categories = ["user.name"]
    field(
        [mongo_dataset],
        "mongo_test",
        "internal_customer_profile",
        "customer_identifiers",
        "derived_phone",
    ).data_categories = ["user.contact"]

    graph = DatasetGraph(mongo_dataset, postgres_dataset)

    seed_email = postgres_inserts["customer"][0]["email"]
    seed_phone = mongo_inserts["rewards"][0]["owner"][0]["phone"]

    access_runner_tester(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config, integration_postgres_config],
        {"email": seed_email, "phone_number": seed_phone},
        db,
    )

    x = erasure_runner_tester(
        privacy_request,
        policy,
        graph,
        [integration_mongodb_config, integration_postgres_config],
        {"email": seed_email},
        get_cached_data_for_erasures(privacy_request.id),
        db,
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
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
async def test_array_querying_mongo(
    db,
    privacy_request,
    privacy_request_status_pending,
    example_datasets,
    policy,
    integration_mongodb_config,
    integration_postgres_config,
    dsr_version,
    request,
):
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    postgres_config = copy.copy(integration_postgres_config)

    dataset_postgres = Dataset(**example_datasets[0])
    graph = convert_dataset_to_graph(dataset_postgres, integration_postgres_config.key)
    dataset_mongo = Dataset(**example_datasets[1])
    mongo_graph = convert_dataset_to_graph(
        dataset_mongo, integration_mongodb_config.key
    )
    dataset_graph = DatasetGraph(*[graph, mongo_graph])

    access_request_results = access_runner_tester(
        privacy_request,
        policy,
        dataset_graph,
        [postgres_config, integration_mongodb_config],
        {"email": "jane@example.com"},
        db,
    )

    # This is a different category than was specified on the policy, this is just for testing.
    target_categories = {"user"}
    filtered_results = filter_data_categories(
        access_request_results,
        target_categories,
        dataset_graph,
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
        {"user"},
        dataset_graph,
    )

    # Includes array field
    assert filtered_identifiable["mongo_test:customer_details"][0][
        "birthday"
    ] == datetime(1990, 2, 28, 0, 0)
    assert filtered_identifiable["mongo_test:customer_details"][0]["customer_id"] == 3.0
    assert filtered_identifiable["mongo_test:customer_details"][0]["gender"] == "female"
    assert filtered_identifiable["mongo_test:customer_details"][0]["children"] == [
        "Erica Example"
    ]
    customer_detail_logs = privacy_request.execution_logs.filter_by(
        dataset_name="mongo_test", collection_name="customer_details", status="complete"
    )
    # Returns fields_affected for all possible targeted fields, even though this identity only had some
    # of them actually populated
    assert sorted(
        customer_detail_logs[0].fields_affected, key=lambda e: e["field_name"]
    ) == [
        {
            "path": "mongo_test:customer_details:birthday",
            "field_name": "birthday",
            "data_categories": ["user.demographic.date_of_birth"],
        },
        {
            "path": "mongo_test:customer_details:children",
            "field_name": "children",
            "data_categories": ["user.childrens"],
        },
        {
            "path": "mongo_test:customer_details:customer_id",
            "field_name": "customer_id",
            "data_categories": ["user.unique_id"],
        },
        {
            "data_categories": ["user.unique_id"],
            "field_name": "customer_uuid",
            "path": "mongo_test:customer_details:customer_uuid",
        },
        {
            "path": "mongo_test:customer_details:emergency_contacts.name",
            "field_name": "emergency_contacts.name",
            "data_categories": ["user.name"],
        },
        {
            "path": "mongo_test:customer_details:emergency_contacts.phone",
            "field_name": "emergency_contacts.phone",
            "data_categories": ["user.contact.phone_number"],
        },
        {
            "path": "mongo_test:customer_details:gender",
            "field_name": "gender",
            "data_categories": ["user.demographic.gender"],
        },
        {
            "path": "mongo_test:customer_details:workplace_info.direct_reports",
            "field_name": "workplace_info.direct_reports",
            "data_categories": ["user.name"],
        },
        {
            "path": "mongo_test:customer_details:workplace_info.position",
            "field_name": "workplace_info.position",
            "data_categories": ["user.job_title"],
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
            "data_categories": ["user.name"],
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
    assert {
        "path": "mongo_test:conversations:thread.chat_name",
        "field_name": "thread.chat_name",
        "data_categories": ["user.name"],
    } in conversation_logs[0].fields_affected

    assert {
        "path": "mongo_test:conversations:thread.ccn",
        "field_name": "thread.ccn",
        "data_categories": ["user.financial.bank_account"],
    } in conversation_logs[0].fields_affected

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
        {"email": "employee-2@example.com", "name": "Jane Employee", "id": "2"}
    ]
    employee_logs = privacy_request.execution_logs.filter_by(
        dataset_name="mongo_test", collection_name="employee", status="complete"
    )
    assert employee_logs.count() == 1
    assert employee_logs[0].fields_affected == [
        {
            "path": "mongo_test:employee:email",
            "field_name": "email",
            "data_categories": ["user.contact.email"],
        },
        {
            "path": "mongo_test:employee:id",
            "field_name": "id",
            "data_categories": ["user.unique_id"],
        },
        {
            "path": "mongo_test:employee:name",
            "field_name": "name",
            "data_categories": ["user.name"],
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
            "data_categories": ["user.contact.phone_number"],
        },
        {
            "path": "mongo_test:customer_feedback:message",
            "field_name": "message",
            "data_categories": ["user"],
        },
        {
            "path": "mongo_test:customer_feedback:rating",
            "field_name": "rating",
            "data_categories": ["user"],
        },
    ]

    # Only matched embedded document in mongo_test:conversations.thread.ccn used to locate mongo_test:payment_card
    assert filtered_identifiable["mongo_test:payment_card"] == [
        {
            "code": "123",
            "name": "Example Card 2",
            "ccn": "987654321",
            "preferred": False,
            "customer_id": 2,
        }
    ]
    payment_logs = privacy_request.execution_logs.filter_by(
        dataset_name="mongo_test", collection_name="payment_card", status="complete"
    )
    assert payment_logs.count() == 1
    assert payment_logs[0].fields_affected == [
        {
            "path": "mongo_test:payment_card:ccn",
            "field_name": "ccn",
            "data_categories": ["user.financial.bank_account"],
        },
        {
            "path": "mongo_test:payment_card:code",
            "field_name": "code",
            "data_categories": ["user.financial"],
        },
        {
            "path": "mongo_test:payment_card:name",
            "field_name": "name",
            "data_categories": ["user.financial"],
        },
        {
            "path": "mongo_test:payment_card:customer_id",
            "field_name": "customer_id",
            "data_categories": ["user.unique_id"],
        },
        {
            "path": "mongo_test:payment_card:preferred",
            "field_name": "preferred",
            "data_categories": ["user"],
        },
    ]

    # Run again with different email
    access_request_results = access_runner_tester(
        privacy_request_status_pending,
        policy,
        dataset_graph,
        [postgres_config, integration_mongodb_config],
        {"email": "customer-1@example.com"},
        db,
    )
    filtered_identifiable = filter_data_categories(
        access_request_results,
        {"user"},
        dataset_graph,
    )

    # Two values in mongo_test:flights:pilots array field mapped to mongo_test:employee ids
    assert filtered_identifiable["mongo_test:employee"] == [
        {"email": "employee-1@example.com", "name": "Jack Employee", "id": "1"},
        {"email": "employee-2@example.com", "name": "Jane Employee", "id": "2"},
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
    def execution_node(self, example_datasets, integration_mongodb_config):
        dataset = Dataset(**example_datasets[1])
        graph = convert_dataset_to_graph(dataset, integration_mongodb_config.key)
        customer_details_collection = None
        for collection in graph.collections:
            if collection.name == "customer_details":
                customer_details_collection = collection
                break
        node = Node(graph, customer_details_collection)
        traversal_node = TraversalNode(node)
        return traversal_node.to_mock_execution_node()

    def test_retrieving_data(
        self,
        privacy_request,
        connector,
        execution_node,
    ):
        execution_node.incoming_edges = {
            Edge(
                FieldAddress("fake_dataset", "fake_collection", "id"),
                FieldAddress("mongo_test", "customer_details", "customer_id"),
            )
        }

        results = connector.retrieve_data(
            execution_node,
            Policy(),
            privacy_request,
            RequestTask(),
            {"customer_id": [1]},
        )

        assert results[0]["customer_id"] == 1

    def test_retrieving_data_no_input(
        self,
        privacy_request,
        connector,
        execution_node,
    ):
        execution_node.incoming_edges = {
            Edge(
                FieldAddress("fake_dataset", "fake_collection", "email"),
                FieldAddress("mongo_test", "customer_details", "customer_id"),
            )
        }
        results = connector.retrieve_data(
            execution_node,
            Policy(),
            privacy_request,
            RequestTask(),
            {"customer_id": []},
        )
        assert results == []

        results = connector.retrieve_data(
            execution_node, Policy(), privacy_request, RequestTask(), {}
        )
        assert results == []

        results = connector.retrieve_data(
            execution_node,
            Policy(),
            privacy_request,
            RequestTask(),
            {"bad_key": ["test"]},
        )
        assert results == []

        results = connector.retrieve_data(
            execution_node, Policy(), privacy_request, RequestTask(), {"email": [None]}
        )
        assert results == []

        results = connector.retrieve_data(
            execution_node, Policy(), privacy_request, RequestTask(), {"email": None}
        )
        assert results == []

    def test_retrieving_data_input_not_in_table(
        self,
        privacy_request,
        connector,
        execution_node,
    ):
        execution_node.incoming_edges = {
            Edge(
                FieldAddress("fake_dataset", "fake_collection", "email"),
                FieldAddress("mongo_test", "customer_details", "customer_id"),
            )
        }

        results = connector.retrieve_data(
            execution_node,
            Policy(),
            privacy_request,
            RequestTask(),
            {"customer_id": [5]},
        )

        assert results == []
