import pytest
from fideslang.models import Dataset

from fides.api.graph.graph import DatasetGraph
from fides.api.models.datasetconfig import convert_dataset_to_graph

from ...conftest import access_runner_tester, erasure_runner_tester


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@pytest.mark.asyncio
async def test_bigquery_nested_field_update(
    db,
    bigquery_resources,
    bigquery_example_test_dataset_config,
    privacy_request,
    erasure_policy,
    dsr_version,
    request,
):
    """Test that updates to nested fields in BigQuery are executed correctly."""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    # Configure policy to mask user data
    erasure_policy.rules[0].targets[0].data_category = "user"
    erasure_policy.rules[0].targets[0].save(db)
    privacy_request.policy_id = erasure_policy.id
    privacy_request.save(db)

    # Use the existing fixture data
    customer_email = bigquery_resources["email"]
    client = bigquery_resources["client"]

    # Verify that the fixture data includes the nested extra_address_data
    with client.connect() as connection:
        verify_stmt = (
            f"SELECT * FROM fidesopstest.customer WHERE email = '{customer_email}';"
        )
        result = connection.execute(verify_stmt).all()
        assert len(result) == 1
        assert result[0].email == customer_email
        assert result[0].extra_address_data is not None
        assert result[0].extra_address_data["city"] is not None
        assert result[0].extra_address_data["street"] is not None

    # Execute the erasure task using the runner tester
    dataset = Dataset.model_validate(bigquery_example_test_dataset_config.ctl_dataset)
    graph = convert_dataset_to_graph(
        dataset, bigquery_example_test_dataset_config.connection_config.key
    )
    dataset_graph = DatasetGraph(graph)

    # First run the access request to gather data
    access_results = access_runner_tester(
        privacy_request,
        erasure_policy,
        dataset_graph,
        [bigquery_example_test_dataset_config.connection_config],
        {"email": customer_email},
        db,
    )

    # Then run the erasure using the data from the access request
    erasure_runner_tester(
        privacy_request,
        erasure_policy,
        dataset_graph,
        [bigquery_example_test_dataset_config.connection_config],
        {"email": customer_email},
        access_results,
        db,
    )

    # Verify nested fields were properly masked
    with client.connect() as connection:
        verify_after_stmt = (
            f"SELECT * FROM fidesopstest.customer WHERE email = '{customer_email}';"
        )
        results_after = connection.execute(verify_after_stmt).all()

        assert len(results_after) == 1
        row = results_after[0]

        assert row.name is None
        assert row.extra_address_data["city"] is None
        assert row.extra_address_data["street"] is None
        assert row.extra_address_data["state"] is None


@pytest.mark.integration_external
@pytest.mark.integration_bigquery
@pytest.mark.parametrize(
    "dsr_version",
    ["use_dsr_3_0", "use_dsr_2_0"],
)
@pytest.mark.asyncio
async def test_bigquery_deeply_nested_field_update(
    db,
    bigquery_resources,
    bigquery_example_test_dataset_config,
    privacy_request,
    erasure_policy,
    dsr_version,
    request,
):
    """Test that updates to deeply nested fields in BigQuery are executed correctly."""
    request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

    # Configure policy to mask user data
    erasure_policy.rules[0].targets[0].data_category = "user"
    erasure_policy.rules[0].targets[0].save(db)
    privacy_request.policy_id = erasure_policy.id
    privacy_request.save(db)

    # Use the existing fixture data
    customer_email = bigquery_resources["email"]
    customer_id = bigquery_resources["id"]
    client = bigquery_resources["client"]

    # Verify that the fixture data includes customer_profile with nested contact_info
    with client.connect() as connection:
        verify_stmt = (
            f"SELECT * FROM fidesopstest.customer_profile WHERE id = {customer_id};"
        )
        result = connection.execute(verify_stmt).all()
        assert len(result) == 1
        assert result[0].id == customer_id
        assert result[0].contact_info is not None
        assert result[0].contact_info["primary_email"] == customer_email

    # Execute the erasure task using the runner tester
    dataset = Dataset.model_validate(bigquery_example_test_dataset_config.ctl_dataset)
    graph = convert_dataset_to_graph(
        dataset, bigquery_example_test_dataset_config.connection_config.key
    )
    dataset_graph = DatasetGraph(graph)

    # First run the access request to gather data
    access_results = access_runner_tester(
        privacy_request,
        erasure_policy,
        dataset_graph,
        [bigquery_example_test_dataset_config.connection_config],
        {"email": customer_email},
        db,
    )

    # Then run the erasure using the data from the access request
    erasure_runner_tester(
        privacy_request,
        erasure_policy,
        dataset_graph,
        [bigquery_example_test_dataset_config.connection_config],
        {"email": customer_email},
        access_results,
        db,
    )

    # Verify nested fields were properly masked
    with client.connect() as connection:
        verify_after_stmt = (
            f"SELECT * FROM fidesopstest.customer_profile WHERE id = {customer_id};"
        )
        results_after = connection.execute(verify_after_stmt).all()

        assert len(results_after) == 1
        result = results_after[0]

        # Check that nested fields were masked
        assert result.contact_info["primary_email"] is None
        assert result.contact_info["phone_number"] is None
        assert result.address is None
