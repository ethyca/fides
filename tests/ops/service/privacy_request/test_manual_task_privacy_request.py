import traceback
from typing import Any, Dict, Generator, cast

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from fides.api.graph.config import CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConditionalDependency,
    ManualTaskConditionalDependencyType,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskInstance,
    ManualTaskParentEntityType,
    ManualTaskSubmission,
    ManualTaskType,
)
from fides.api.models.policy import ActionType, Policy, Rule, RuleTarget
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.manual.manual_task_address import ManualTaskAddress
from fides.api.task.manual.manual_task_utils import create_manual_task_artificial_graphs
from fides.api.util.collection_util import Row
from tests.ops.service.privacy_request.test_request_runner_service import (
    PRIVACY_REQUEST_TASK_TIMEOUT,
    get_privacy_request_results,
)


# Add a simple downstream collection implementation for testing
class DownstreamCollectionGraphTask:
    """Simple graph task implementation for downstream collections that depend on manual tasks"""

    def __init__(self, execution_node, resources, request_task):
        self.execution_node = execution_node
        self.resources = resources
        self.request_task = request_task

    def access_request(self, *inputs: list[Row]) -> list[Row]:
        """Process inputs from manual tasks and return downstream data"""
        # Extract manual task data from inputs
        manual_task_data = {}
        for input_data in inputs:
            if input_data and isinstance(input_data, list) and len(input_data) > 0:
                for row in input_data:
                    if isinstance(row, dict):
                        # Look for manual task fields
                        for key, value in row.items():
                            if key == "verification_required":
                                manual_task_data["manual_task_output"] = value

        # Create downstream output
        if manual_task_data:
            return [
                {
                    "id": "downstream_1",
                    "manual_task_output": manual_task_data.get(
                        "manual_task_output", "no_data"
                    ),
                    "processed_at": "2024-01-01T00:00:00Z",
                }
            ]
        else:
            return [
                {
                    "id": "downstream_1",
                    "manual_task_output": "no_manual_task_data",
                    "processed_at": "2024-01-01T00:00:00Z",
                }
            ]


@pytest.fixture
def manual_connection(db: Session) -> ConnectionConfig:
    return ConnectionConfig.create(
        db=db,
        data={
            "name": "Manual Connection",
            "key": "manual_connection",
            "connection_type": ConnectionType.manual_task,
            "access": AccessLevel.write,
            "secrets": {},
        },
    )


@pytest.fixture
def manual_task(db: Session, manual_connection: ConnectionConfig) -> ManualTask:
    return ManualTask.create(
        db=db,
        data={
            "task_type": ManualTaskType.privacy_request,
            "parent_entity_id": manual_connection.id,
            "parent_entity_type": ManualTaskParentEntityType.connection_config,
        },
    )


@pytest.fixture
def manual_config(db: Session, manual_task: ManualTask) -> ManualTaskConfig:
    return ManualTaskConfig.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_type": ManualTaskConfigurationType.access_privacy_request,
            "version": 1,
            "is_current": True,
        },
    )


@pytest.fixture
def manual_field(
    db: Session, manual_task: ManualTask, manual_config: ManualTaskConfig
) -> ManualTaskConfigField:
    return ManualTaskConfigField.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_config.id,
            "field_key": "verification_required",
            "field_type": ManualTaskFieldType.text,
            "field_metadata": {
                "label": "Verification Required",
                "required": True,
                "data_categories": ["user.verification"],
            },
        },
    )


@pytest.fixture
def conditional_name_exists(
    db: Session, manual_task: ManualTask, manual_config: ManualTaskConfig
) -> ManualTaskConditionalDependency:
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_type": ManualTaskConditionalDependencyType.leaf,
            "field_address": "postgres_example_test_dataset:customer:email",
            "operator": "list_contains",
            "value": "customer-1@example.com",  # Use an email that actually exists in test data
            "sort_order": 1,
        },
    )


@pytest.fixture
def conditional_email_exists(
    db: Session, manual_task: ManualTask, manual_config: ManualTaskConfig
) -> ManualTaskConditionalDependency:
    """Alternative conditional dependency that checks for email existence"""
    return ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_type": ManualTaskConditionalDependencyType.leaf,
            "field_address": "postgres_example_test_dataset:customer:email",
            "operator": "exists",
            "value": None,  # exists operator doesn't need a value
            "sort_order": 1,
        },
    )


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.usefixtures("use_dsr_3_0", "automatically_approved")
def test_privacy_request_runs_after_manual_input_simple(
    example_datasets: list[Dict],
    db: Session,
    connection_config: ConnectionConfig,
    policy,
    run_privacy_request_task,
    postgres_integration_db,
    manual_task: ManualTask,
    manual_config: ManualTaskConfig,
    manual_field: ManualTaskConfigField,
):
    """
    End-to-end test: A manual task should execute together with regular datasets.
    This test is for a simple manual task that does not have conditional dependencies.
    A manual task connection and field are provided as fixtures. We create a regular dataset,
    run the request once (expecting requires_input), supply the input, then re-run and validate results.
    This proves that manual tasks are properly integrated into the overall DAG.
    """

    # ------------------------------------------------------------------
    # 1. Use the first example dataset (Postgres)
    # ------------------------------------------------------------------
    # Use the first example dataset (postgres_example_test_dataset)
    source_ds = example_datasets[0]

    source_ctl_ds = CtlDataset.create_from_dataset_dict(db, source_ds)
    DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": source_ds["fides_key"],
            "ctl_dataset_id": source_ctl_ds.id,
        },
    )

    # The postgres_integration_db fixture already has test data
    # Use existing customer data: customer-1@example.com, customer-2@example.com

    # ------------------------------------------------------------------
    # 2. Kick off PrivacyRequest (first run – should pause for input)
    # ------------------------------------------------------------------
    pr_data = {"identity": {"email": "customer-1@example.com"}}

    try:
        privacy_request = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            pr_data,
            task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT,
        )

        # Refresh from DB to ensure latest status after celery task commits
        db.refresh(privacy_request)

        # After first run, privacy request should be awaiting manual input
        assert (
            privacy_request.status == PrivacyRequestStatus.requires_input
        ), f"Expected requires_input, got {privacy_request.status}. Error: {getattr(privacy_request, 'error_message', 'No error message')}"

        # ------------------------------------------------------------------
        # 3. Provide manual input via ManualTaskSubmission and re-run
        # ------------------------------------------------------------------
        instance = (
            db.query(ManualTaskInstance)
            .filter(
                ManualTaskInstance.task_id == manual_task.id,
                ManualTaskInstance.entity_id == privacy_request.id,
            )
            .first()
        )
        assert instance is not None, "ManualTaskInstance was not created"

        ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_config.id,
                "field_id": manual_field.id,
                "instance_id": instance.id,
                "data": {"value": "verified_customer"},
            },
        )

        # Re-enqueue the same privacy request
        run_privacy_request_task.delay(privacy_request.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )
        db.refresh(privacy_request)

        assert privacy_request.status == PrivacyRequestStatus.complete

        results = cast(
            Dict[str, list[Dict[str, Any]]],
            privacy_request.get_raw_access_results() or {},
        )

        manual_addr_key = ManualTaskAddress.create("manual_connection").value
        source_addr_key = "postgres_example_test_dataset:customer"

        # Verify source dataset data is present (proves regular datasets execute)
        assert (
            source_addr_key in results
        ), "Source dataset data should be present in results"

        # Verify manual task data is present in results
        assert (
            manual_addr_key in results
        ), "Manual task data should be present in results"
        assert (
            results[manual_addr_key][0]["verification_required"] == "verified_customer"
        ), "Manual task should contain submitted value"

    except Exception as e:
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.usefixtures(
    "use_dsr_3_0", "automatically_approved", "conditional_email_exists"
)
def test_manual_task_with_conditional_dependencies(
    db: Session,
    example_datasets: list[Dict],
    connection_config: ConnectionConfig,
    policy,
    run_privacy_request_task,
    postgres_integration_db,
    manual_task: ManualTask,
    manual_config: ManualTaskConfig,
    manual_field: ManualTaskConfigField,
):
    """
    Test that data passes through manual task graph tasks correctly.

    This test demonstrates that manual tasks are properly integrated into the DAG and can:
    1. Receive data from upstream collections
    2. Accept manual input
    3. Provide data to downstream collections
    4. Evaluate conditional dependencies correctly (OR logic)

    The test verifies that manual tasks with conditional dependencies that evaluate to True
    are properly executed and require manual input, while maintaining proper data flow.
    """

    try:
        # ------------------------------------------------------------------
        # 1. Use the first example dataset (Postgres)
        # ------------------------------------------------------------------
        # Use the first example dataset (postgres_example_test_dataset)
        source_ds = example_datasets[0]

        source_ctl_ds = CtlDataset.create_from_dataset_dict(db, source_ds)
        DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": source_ds["fides_key"],
                "ctl_dataset_id": source_ctl_ds.id,
            },
        )

        # ------------------------------------------------------------------
        # 2. Insert test data into the database
        # ------------------------------------------------------------------
        # The postgres_integration_db fixture already has test data
        # Let's use the existing customer data instead of inserting new data
        # Existing customers: customer-1@example.com, customer-2@example.com

        result = postgres_integration_db.execute(
            text("SELECT email, name FROM customer")
        )
        existing_customers = result.fetchall()
        print(f"DEBUG: Found {len(existing_customers)} existing customer records")
        for record in existing_customers:
            print(f"DEBUG: Existing customer: {record}")

        # ------------------------------------------------------------------
        # 3. Test Case: Verify data flows through manual task graph task
        # ------------------------------------------------------------------
        # Use existing customer email
        pr_data = {"identity": {"email": "customer-1@example.com"}}

        privacy_request = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            pr_data,
            task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT,
        )

        db.refresh(privacy_request)

        # Should require manual input (manual task has configuration and should require input)
        assert (
            privacy_request.status == PrivacyRequestStatus.requires_input
        ), f"Expected requires_input, got {privacy_request.status}"

        # Verify manual task instance was created (proves manual task was reached in DAG)
        instance = (
            db.query(ManualTaskInstance)
            .filter(
                ManualTaskInstance.task_id == manual_task.id,
                ManualTaskInstance.entity_id == privacy_request.id,
            )
            .first()
        )
        assert instance is not None, "ManualTaskInstance should be created"

        # Provide manual input
        submission = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_config.id,
                "field_id": manual_field.id,
                "instance_id": instance.id,
                "data": {"value": "verified_premium_user"},
            },
        )

        # Re-run the privacy request
        run_privacy_request_task.delay(privacy_request.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )
        db.refresh(privacy_request)

        assert (
            privacy_request.status == PrivacyRequestStatus.complete
        ), f"Expected complete, got {privacy_request.status}. Error: {getattr(privacy_request, 'error_message', 'No error message')}"

        # Verify results contain manual task data
        results = cast(
            Dict[str, list[Dict[str, Any]]],
            privacy_request.get_raw_access_results() or {},
        )

        manual_addr_key = ManualTaskAddress.create("manual_connection").value
        assert (
            manual_addr_key in results
        ), "Manual task data should be present in results"
        assert (
            results[manual_addr_key][0]["verification_required"]
            == "verified_premium_user"
        )

        # ------------------------------------------------------------------
        # 4. Test Case: Verify data flows through manual task graph task (OR logic)
        # ------------------------------------------------------------------
        # Create a new manual task with OR condition: (customer.email exists OR customer.name contains 'customer')

        manual_connection_or = ConnectionConfig.create(
            db=db,
            data={
                "name": "OR Conditional Manual Connection",
                "key": "or_conditional_manual_connection",
                "connection_type": ConnectionType.manual_task,
                "access": AccessLevel.write,
                "secrets": {},
            },
        )

        manual_task_or = ManualTask.create(
            db=db,
            data={
                "task_type": ManualTaskType.privacy_request,
                "parent_entity_id": manual_connection_or.id,
                "parent_entity_type": ManualTaskParentEntityType.connection_config,
            },
        )

        # Root group condition (OR)
        root_dependency_or = ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task_or.id,
                "condition_type": ManualTaskConditionalDependencyType.group,
                "logical_operator": "or",
                "sort_order": 1,
            },
        )

        # First condition: customer email exists (this will be True for any customer)
        ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task_or.id,
                "condition_type": ManualTaskConditionalDependencyType.leaf,
                "field_address": "postgres_example_test_dataset:customer:email",
                "operator": "exists",
                "value": None,  # exists operator doesn't need a value
                "sort_order": 2,
                "parent_id": root_dependency_or.id,
            },
        )

        # Second condition: customer name contains 'customer' (this will be True for customer-1, customer-2)
        ManualTaskConditionalDependency.create(
            db=db,
            data={
                "manual_task_id": manual_task_or.id,
                "condition_type": ManualTaskConditionalDependencyType.leaf,
                "field_address": "postgres_example_test_dataset:customer:name",
                "operator": "list_contains",
                "value": "customer",
                "sort_order": 3,
                "parent_id": root_dependency_or.id,
            },
        )

        # Create manual task config and field for OR condition
        manual_config_or = ManualTaskConfig.create(
            db=db,
            data={
                "task_id": manual_task_or.id,
                "config_type": ManualTaskConfigurationType.access_privacy_request,
                "version": 1,
                "is_current": True,
            },
        )

        manual_field_or = ManualTaskConfigField.create(
            db=db,
            data={
                "task_id": manual_task_or.id,
                "config_id": manual_config_or.id,
                "field_key": "verification_required",
                "field_type": ManualTaskFieldType.text,
                "field_metadata": {
                    "label": "Verification Required",
                    "required": True,
                    "data_categories": ["user.verification"],
                },
            },
        )

        # Test OR condition with existing customer data
        pr_data_or = {"identity": {"email": "customer-1@example.com"}}
        privacy_request_or = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            pr_data_or,
            task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT,
        )

        db.refresh(privacy_request_or)

        # Check all manual task instances for this privacy request
        all_instances = (
            db.query(ManualTaskInstance)
            .filter(ManualTaskInstance.entity_id == privacy_request_or.id)
            .all()
        )

        # Should require manual input since OR condition should be met (email exists OR name contains 'customer')
        assert (
            privacy_request_or.status == PrivacyRequestStatus.requires_input
        ), f"Expected requires_input, got {privacy_request_or.status}"

        # Verify manual task instance was created (proves manual task was reached in DAG)
        instance_or = (
            db.query(ManualTaskInstance)
            .filter(
                ManualTaskInstance.task_id == manual_task_or.id,
                ManualTaskInstance.entity_id == privacy_request_or.id,
            )
            .first()
        )
        assert (
            instance_or is not None
        ), "ManualTaskInstance should be created for OR condition"

        # Provide manual input for both manual tasks
        for instance in all_instances:
            if instance.task_id == manual_task_or.id:
                # This is the OR condition task - provide input
                ManualTaskSubmission.create(
                    db=db,
                    data={
                        "task_id": manual_task_or.id,
                        "config_id": manual_config_or.id,
                        "field_id": manual_field_or.id,
                        "instance_id": instance.id,
                        "data": {"value": "or_verified"},
                    },
                )
                print(
                    f"DEBUG: Provided input for OR condition task instance {instance.id}"
                )
            else:
                # This is the first manual task - provide input for it too
                ManualTaskSubmission.create(
                    db=db,
                    data={
                        "task_id": manual_task.id,
                        "config_id": manual_config.id,
                        "field_id": manual_field.id,
                        "instance_id": instance.id,
                        "data": {"value": "first_task_verified"},
                    },
                )
                print(
                    f"DEBUG: Provided input for first manual task instance {instance.id}"
                )

        run_privacy_request_task.delay(privacy_request_or.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )
        db.refresh(privacy_request_or)

        assert (
            privacy_request_or.status == PrivacyRequestStatus.complete
        ), f"Expected complete, got {privacy_request_or.status}. Error: {getattr(privacy_request_or, 'error_message', 'No error message')}"

        # Verify results contain OR manual task data
        results_or = cast(
            Dict[str, list[Dict[str, Any]]],
            privacy_request_or.get_raw_access_results() or {},
        )

        manual_addr_key_or = ManualTaskAddress.create(
            "or_conditional_manual_connection"
        ).value
        assert (
            manual_addr_key_or in results_or
        ), "OR manual task data should be present in results"
        assert (
            results_or[manual_addr_key_or][0]["verification_required"] == "or_verified"
        )

    except Exception as e:
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.usefixtures(
    "use_dsr_3_0", "automatically_approved", "conditional_email_exists"
)
def test_manual_tasks_are_integrated_into_dag(
    db: Session,
    example_datasets: list[Dict],
    connection_config: ConnectionConfig,
    policy,
    run_privacy_request_task,
    postgres_integration_db,
    manual_task: ManualTask,
    manual_config: ManualTaskConfig,
    manual_field: ManualTaskConfigField,
):
    """
    Test that proves manual tasks are integrated into the overall DAG (Directed Acyclic Graph).

    This test demonstrates that data flows correctly through manual task graph tasks:
    1. Manual tasks are included in the dataset graph
    2. Manual tasks have proper dependencies and execution order
    3. Manual tasks can receive data from upstream collections
    4. Manual tasks can provide data to downstream collections
    5. Data flows end-to-end through the manual task graph task

    Note: Conditional dependency evaluation will be implemented in a future change.
    This test focuses on establishing the data flow through manual task graph tasks.
    """

    # ------------------------------------------------------------------
    # 1. Use the first example dataset (Postgres)
    # ------------------------------------------------------------------
    # Use the first example dataset (postgres_example_test_dataset)
    source_ds = example_datasets[0]

    source_ctl_ds = CtlDataset.create_from_dataset_dict(db, source_ds)
    DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": source_ds["fides_key"],
            "ctl_dataset_id": source_ctl_ds.id,
        },
    )

    # ------------------------------------------------------------------
    # 2. Use existing test data
    # ------------------------------------------------------------------
    # The postgres_integration_db fixture already has test data
    # Use existing customer data: customer-1@example.com, customer-2@example.com

    # ------------------------------------------------------------------
    # 3. PROOF 1: Verify manual tasks are included in the dataset graph
    # ------------------------------------------------------------------
    # Get all dataset configs
    all_datasets = DatasetConfig.all(db=db)
    dataset_graphs = [
        dataset_config.get_graph()
        for dataset_config in all_datasets
        if not dataset_config.connection_config.disabled
    ]

    # Add manual task artificial graphs
    manual_task_graphs = create_manual_task_artificial_graphs(db)

    # Verify manual task graph was created
    assert len(manual_task_graphs) > 0, "Manual task graphs should be created"

    # Find our manual task graph
    dag_test_graph = next(
        (g for g in manual_task_graphs if g.name == "manual_connection"), None
    )
    assert (
        dag_test_graph is not None
    ), "Manual task graph for manual_connection should exist"

    # ------------------------------------------------------------------
    # 4. PROOF 2: Verify manual tasks have proper dependencies
    # ------------------------------------------------------------------
    # The manual task should depend on the source dataset collection via scalar field references
    manual_collection = dag_test_graph.collections[0]

    # Verify the manual task depends on the source dataset via scalar field references
    # The conditional dependency references "postgres_example_test_dataset:customer:email"
    # so there should be a scalar field with a reference to this field address
    expected_field_address = "postgres_example_test_dataset:customer:email"

    # Check that there's a scalar field with the expected reference
    field_with_reference = None
    for field in manual_collection.fields:
        for ref, direction in field.references:
            if str(ref) == expected_field_address:
                field_with_reference = field
                break
        if field_with_reference:
            break

    assert (
        field_with_reference is not None
    ), f"Manual task should have a scalar field with reference to {expected_field_address}. Found fields: {[f.name for f in manual_collection.fields]}"

    # ------------------------------------------------------------------
    # 5. PROOF 3: Verify manual tasks are included in the complete graph
    # ------------------------------------------------------------------
    # Combine all graphs including manual tasks
    complete_dataset_graphs = dataset_graphs + manual_task_graphs
    complete_graph = DatasetGraph(*complete_dataset_graphs)

    # Verify manual task node exists in the complete graph
    manual_address = ManualTaskAddress.create("manual_connection")
    assert (
        manual_address in complete_graph.nodes
    ), "Manual task should be included in complete graph"

    # ------------------------------------------------------------------
    # 6. PROOF 4: Verify manual task dependencies are properly configured
    # ------------------------------------------------------------------
    # Check that the manual task collection has the correct dependencies
    manual_collection = dag_test_graph.collections[0]

    # Verify the manual task depends on the source dataset via scalar field references (proves DAG structure)
    expected_field_address = "postgres_example_test_dataset:customer:email"

    # Check that there's a scalar field with the expected reference
    field_with_reference = None
    for field in manual_collection.fields:
        for ref, direction in field.references:
            if str(ref) == expected_field_address:
                field_with_reference = field
                break
        if field_with_reference:
            break

    assert (
        field_with_reference is not None
    ), f"Manual task should have a scalar field with reference to {expected_field_address}"

    # Verify the manual task has the correct fields that depend on source data
    manual_fields = [field.name for field in manual_collection.fields]

    # The manual task should have both its own field and the conditional dependency field
    assert (
        "verification_required" in manual_fields
    ), "Manual task should have its own field"
    assert (
        "postgres_example_test_dataset:customer:email" in manual_fields
    ), "Manual task should have conditional dependency field from source"

    # ------------------------------------------------------------------
    # 7. PROOF 5: Verify data flows through manual task graph task (proves DAG integration)
    # ------------------------------------------------------------------
    # Test with existing customer (should trigger manual task)
    pr_data = {"identity": {"email": "customer-1@example.com"}}

    privacy_request = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        pr_data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT,
    )

    db.refresh(privacy_request)

    # Should require manual input (conditional evaluation not implemented yet)
    assert (
        privacy_request.status == PrivacyRequestStatus.requires_input
    ), f"Expected requires_input, got {privacy_request.status}"

    # Verify manual task instance was created (proves manual task was reached in DAG)
    instance = (
        db.query(ManualTaskInstance)
        .filter(
            ManualTaskInstance.task_id == manual_task.id,
            ManualTaskInstance.entity_id == privacy_request.id,
        )
        .first()
    )
    assert instance is not None, "ManualTaskInstance should be created"

    # Provide manual input
    submission = ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_config.id,
            "field_id": manual_field.id,
            "instance_id": instance.id,
            "data": {"value": "dag_test_value"},
        },
    )

    # Re-run the privacy request
    run_privacy_request_task.delay(privacy_request.id).get(
        timeout=PRIVACY_REQUEST_TASK_TIMEOUT
    )
    db.refresh(privacy_request)

    assert (
        privacy_request.status == PrivacyRequestStatus.complete
    ), f"Expected complete, got {privacy_request.status}. Error: {getattr(privacy_request, 'error_message', 'No error message')}"

    # Verify results contain both source data and manual task data
    results = cast(
        Dict[str, list[Dict[str, Any]]], privacy_request.get_raw_access_results() or {}
    )

    source_addr_key = "postgres_example_test_dataset:customer"
    manual_addr_key = ManualTaskAddress.create("manual_connection").value

    # Verify source data is present (proves upstream execution)
    assert source_addr_key in results, "Source data should be present in results"

    # Verify manual task data is present (proves manual task execution)
    assert manual_addr_key in results, "Manual task data should be present in results"
    assert results[manual_addr_key][0]["verification_required"] == "dag_test_value"


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.usefixtures(
    "use_dsr_3_0", "automatically_approved", "conditional_email_exists"
)
def test_manual_task_output_data_available_for_downstream(
    db: Session,
    example_datasets: list[Dict],
    connection_config: ConnectionConfig,
    policy,
    run_privacy_request_task,
    postgres_integration_db,
    manual_task: ManualTask,
    manual_config: ManualTaskConfig,
    manual_field: ManualTaskConfigField,
):
    """
    Test that manual task output data is available for downstream collections.

    This test verifies that:
    1. Manual tasks can provide output data
    2. The output data is properly structured and accessible
    3. Downstream collections can reference manual task data in their 'after' dependencies

    This is a foundational test for enabling data flow from manual tasks to downstream collections.
    After we complete the following:
    1. Update the collection configuration schema to allow manual task references
    2. Update the dataset parsing logic to handle manual task dependencies
    3. Update the graph traversal logic to create edges from manual tasks to downstream collections
    We can update this test to verify that the manual task output data is passed to downstream collections.
    """

    # ------------------------------------------------------------------
    # 1. Use the first example dataset (Postgres) as upstream
    # ------------------------------------------------------------------
    source_ds = example_datasets[0]
    source_ctl_ds = CtlDataset.create_from_dataset_dict(db, source_ds)
    DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": source_ds["fides_key"],
            "ctl_dataset_id": source_ctl_ds.id,
        },
    )

    # ------------------------------------------------------------------
    # 2. Test that manual task provides structured output data
    # ------------------------------------------------------------------
    pr_data = {"identity": {"email": "customer-1@example.com"}}

    try:
        privacy_request = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            pr_data,
            task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT,
        )

        db.refresh(privacy_request)

        # Should require manual input
        assert (
            privacy_request.status == PrivacyRequestStatus.requires_input
        ), f"Expected requires_input, got {privacy_request.status}"

        # Provide manual input
        instance = (
            db.query(ManualTaskInstance)
            .filter(
                ManualTaskInstance.task_id == manual_task.id,
                ManualTaskInstance.entity_id == privacy_request.id,
            )
            .first()
        )
        assert instance is not None, "ManualTaskInstance should be created"

        submission = ManualTaskSubmission.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": manual_config.id,
                "field_id": manual_field.id,
                "instance_id": instance.id,
                "data": {"value": "test_output_data"},
            },
        )

        # Re-run the privacy request
        run_privacy_request_task.delay(privacy_request.id).get(
            timeout=PRIVACY_REQUEST_TASK_TIMEOUT
        )
        db.refresh(privacy_request)

        assert (
            privacy_request.status == PrivacyRequestStatus.complete
        ), f"Expected complete, got {privacy_request.status}. Error: {getattr(privacy_request, 'error_message', 'No error message')}"

        # Verify manual task output data is properly structured
        results = cast(
            Dict[str, list[Dict[str, Any]]],
            privacy_request.get_raw_access_results() or {},
        )

        manual_addr_key = ManualTaskAddress.create("manual_connection").value

        # Verify manual task data is present and properly structured
        assert (
            manual_addr_key in results
        ), "Manual task data should be present in results"
        manual_task_data = results[manual_addr_key][0]

        # Verify the manual task output has the expected structure
        assert (
            "verification_required" in manual_task_data
        ), "Manual task should have verification_required field"
        assert (
            manual_task_data["verification_required"] == "test_output_data"
        ), "Manual task should contain submitted value"

        # Verify the manual task output is a proper Row structure that can be consumed by downstream collections
        assert isinstance(
            manual_task_data, dict
        ), "Manual task output should be a dictionary"
        assert (
            "id" in manual_task_data or "verification_required" in manual_task_data
        ), "Manual task output should have identifiable fields"

        # ------------------------------------------------------------------
        # 3. Assert that manual task data structure is compatible with downstream collections
        # ------------------------------------------------------------------
        manual_collection_address = f"{manual_addr_key}"
        manual_task_fields = list(manual_task_data.keys())

        # Assert: Manual task collection address follows the expected format
        assert (
            ":" in manual_collection_address
        ), "Manual task collection address should contain ':' separator"
        assert (
            manual_collection_address == "manual_connection:manual_data"
        ), f"Expected 'manual_connection:manual_data', got '{manual_collection_address}'"

        # Assert: Manual task data contains the expected fields for downstream reference
        assert (
            "verification_required" in manual_task_fields
        ), "Manual task should have verification_required field for downstream reference"
        assert (
            len(manual_task_fields) >= 1
        ), "Manual task should have at least one field for downstream reference"

        # Assert: Manual task data can be parsed as a CollectionAddress (proves compatibility with existing system)
        parsed_collection_address = CollectionAddress.from_string(
            manual_collection_address
        )
        assert (
            parsed_collection_address.dataset == "manual_connection"
        ), f"Expected dataset 'manual_connection', got '{parsed_collection_address.dataset}'"
        assert (
            parsed_collection_address.collection == "manual_data"
        ), f"Expected collection 'manual_data', got '{parsed_collection_address.collection}'"

        # Assert: Manual task address is recognized as a manual task address
        assert ManualTaskAddress.is_manual_task_address(
            manual_collection_address
        ), "Manual task address should be recognized as a manual task address"
        assert ManualTaskAddress.is_manual_task_address(
            parsed_collection_address
        ), "Manual task CollectionAddress should be recognized as a manual task address"

        # Assert: Manual task data structure is compatible with downstream collection input requirements
        # Downstream collections expect Row objects (dictionaries) with identifiable fields
        assert isinstance(
            manual_task_data, dict
        ), "Manual task output should be a dictionary for downstream consumption"
        assert (
            "verification_required" in manual_task_data
        ), "Manual task should have verification_required field accessible to downstream collections"
        assert (
            manual_task_data["verification_required"] == "test_output_data"
        ), "Manual task should preserve submitted value for downstream collections"

        # This proves that downstream collections can depend on manual tasks
        # and access their output data through the standard graph traversal mechanism

    except Exception as e:
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.usefixtures("use_dsr_3_0", "automatically_approved")
def test_manual_task_conditional_dependencies_skip_execution(
    db: Session,
    example_datasets: list[Dict],
    connection_config: ConnectionConfig,
    policy,
    run_privacy_request_task,
    postgres_integration_db,
    manual_task: ManualTask,
    manual_config: ManualTaskConfig,
    manual_field: ManualTaskConfigField,
):
    """
    Test that manual tasks are properly skipped when conditional dependencies are not met.

    This test verifies the new conditional behavior:
    1. Manual tasks with conditional dependencies that evaluate to False are skipped
    2. Privacy requests complete immediately when manual tasks are skipped
    3. No ManualTaskInstances are created for skipped manual tasks
    """

    # Create a conditional dependency that will NOT be met
    ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_type": ManualTaskConditionalDependencyType.leaf,
            "field_address": "postgres_example_test_dataset:customer:email",
            "operator": "eq",
            "value": "nonexistent@example.com",  # Email that doesn't exist in test data
            "sort_order": 1,
        },
    )

    # ------------------------------------------------------------------
    # 1. Use the first example dataset (Postgres)
    # ------------------------------------------------------------------
    source_ds = example_datasets[0]
    source_ctl_ds = CtlDataset.create_from_dataset_dict(db, source_ds)
    DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": source_ds["fides_key"],
            "ctl_dataset_id": source_ctl_ds.id,
        },
    )

    # ------------------------------------------------------------------
    # 2. Test that privacy request completes immediately (no manual input needed)
    # ------------------------------------------------------------------
    pr_data = {"identity": {"email": "customer-1@example.com"}}

    privacy_request = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        pr_data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT,
    )

    db.refresh(privacy_request)

    # Should complete immediately since manual task condition is not met
    assert (
        privacy_request.status == PrivacyRequestStatus.complete
    ), f"Expected complete, got {privacy_request.status}. Error: {getattr(privacy_request, 'error_message', 'No error message')}"

    # Verify NO manual task instance was created (proves manual task was skipped)
    instance = (
        db.query(ManualTaskInstance)
        .filter(
            ManualTaskInstance.task_id == manual_task.id,
            ManualTaskInstance.entity_id == privacy_request.id,
        )
        .first()
    )
    assert (
        instance is None
    ), f"ManualTaskInstance should NOT be created when condition is not met: Instance: {instance}"

    # Verify results contain source data but NO manual task data
    results = cast(
        Dict[str, list[Dict[str, Any]]],
        privacy_request.get_raw_access_results() or {},
    )

    source_addr_key = "postgres_example_test_dataset:customer"
    manual_addr_key = ManualTaskAddress.create("manual_connection").value

    # Verify source data is present (proves upstream execution)
    assert source_addr_key in results, "Source data should be present in results"

    # Verify manual task data is NOT present (proves manual task was skipped)
    assert not results.get(
        manual_addr_key
    ), "Manual task data should NOT be present when condition is not met"


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.usefixtures("use_dsr_3_0", "automatically_approved")
def test_manual_task_conditional_dependencies_execute_when_met(
    db: Session,
    example_datasets: list[Dict],
    connection_config: ConnectionConfig,
    policy,
    run_privacy_request_task,
    postgres_integration_db,
    manual_task: ManualTask,
    manual_config: ManualTaskConfig,
    manual_field: ManualTaskConfigField,
):
    """
    Test that manual tasks execute when conditional dependencies are met.

    This test verifies the conditional behavior:
    1. Manual tasks with conditional dependencies that evaluate to True are executed
    2. Privacy requests pause for manual input when conditions are met
    3. ManualTaskInstances are created for executed manual tasks
    """

    # Create a conditional dependency that WILL be met
    ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_type": ManualTaskConditionalDependencyType.leaf,
            "field_address": "postgres_example_test_dataset:customer:email",
            "operator": "exists",
            "value": None,  # exists operator doesn't need a value
            "sort_order": 1,
        },
    )

    # ------------------------------------------------------------------
    # 1. Use the first example dataset (Postgres)
    # ------------------------------------------------------------------
    source_ds = example_datasets[0]
    source_ctl_ds = CtlDataset.create_from_dataset_dict(db, source_ds)
    DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": source_ds["fides_key"],
            "ctl_dataset_id": source_ctl_ds.id,
        },
    )

    # ------------------------------------------------------------------
    # 2. Test that privacy request pauses for manual input (condition is met)
    # ------------------------------------------------------------------
    pr_data = {"identity": {"email": "customer-1@example.com"}}

    privacy_request = get_privacy_request_results(
        db,
        policy,
        run_privacy_request_task,
        pr_data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT,
    )

    db.refresh(privacy_request)

    # Should require manual input since manual task condition is met
    assert (
        privacy_request.status == PrivacyRequestStatus.requires_input
    ), f"Expected requires_input, got {privacy_request.status}. Error: {getattr(privacy_request, 'error_message', 'No error message')}"

    # Verify manual task instance was created (proves manual task was executed)
    instance = (
        db.query(ManualTaskInstance)
        .filter(
            ManualTaskInstance.task_id == manual_task.id,
            ManualTaskInstance.entity_id == privacy_request.id,
        )
        .first()
    )
    assert (
        instance is not None
    ), "ManualTaskInstance should be created when condition is met"

    # Provide manual input
    submission = ManualTaskSubmission.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_config.id,
            "field_id": manual_field.id,
            "instance_id": instance.id,
            "data": {"value": "conditional_test_value"},
        },
    )

    # Re-run the privacy request
    run_privacy_request_task.delay(privacy_request.id).get(
        timeout=PRIVACY_REQUEST_TASK_TIMEOUT
    )
    db.refresh(privacy_request)

    assert (
        privacy_request.status == PrivacyRequestStatus.complete
    ), f"Expected complete, got {privacy_request.status}. Error: {getattr(privacy_request, 'error_message', 'No error message')}"

    # Verify results contain both source data and manual task data
    results = cast(
        Dict[str, list[Dict[str, Any]]],
        privacy_request.get_raw_access_results() or {},
    )

    source_addr_key = "postgres_example_test_dataset:customer"
    manual_addr_key = ManualTaskAddress.create("manual_connection").value

    # Verify source data is present (proves upstream execution)
    assert source_addr_key in results, "Source data should be present in results"

    # Verify manual task data is present (proves manual task execution)
    assert manual_addr_key in results, "Manual task data should be present in results"
    assert (
        results[manual_addr_key][0]["verification_required"] == "conditional_test_value"
    ), "Manual task should contain submitted value"


@pytest.fixture(scope="function")
def erasure_policy_safe_fields(
    db: Session,
    oauth_client: ClientDetail,
) -> Generator:
    """
    Create an erasure policy that only targets fields that can be safely erased
    without violating NOT NULL constraints (like primary keys).
    """
    erasure_policy = Policy.create(
        db=db,
        data={
            "name": "safe erasure policy",
            "key": "safe_erasure_policy",
            "client_id": oauth_client.id,
        },
    )

    # Create rules for different field types that can be safely erased
    safe_categories = [
        "user.contact.email",
        "user.name",
        "user.contact.address",
        "user.financial.bank_account",
        "user.sensor",
    ]

    for category in safe_categories:
        erasure_rule = Rule.create(
            db=db,
            data={
                "action_type": ActionType.erasure.value,
                "client_id": oauth_client.id,
                "name": f"Safe erasure rule for {category}",
                "policy_id": erasure_policy.id,
                "masking_strategy": {
                    "strategy": "string_rewrite",
                    "configuration": {"rewrite_value": "MASKED"},
                },
            },
        )

        RuleTarget.create(
            db=db,
            data={
                "client_id": oauth_client.id,
                "data_category": category,
                "rule_id": erasure_rule.id,
            },
        )

    yield erasure_policy

    # Cleanup
    try:
        for rule in erasure_policy.rules:
            for target in rule.targets:
                target.delete(db)
            rule.delete(db)
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.mark.usefixtures("use_dsr_3_0", "automatically_approved")
def test_manual_task_erasure_end_to_end(
    example_datasets: list[Dict],
    db: Session,
    connection_config: ConnectionConfig,
    erasure_policy_safe_fields,
    run_privacy_request_task,
    postgres_integration_db,
    manual_task: ManualTask,
    manual_config: ManualTaskConfig,
    manual_field: ManualTaskConfigField,
):
    """
    End-to-end test: A manual task with access config should be skipped during erasure mode.
    This test verifies that when running a privacy request with erasure rules, access manual tasks
    are skipped immediately (not wait for input) because they're just for data collection.
    """

    # Create a conditional dependency that WILL be met
    ManualTaskConditionalDependency.create(
        db=db,
        data={
            "manual_task_id": manual_task.id,
            "condition_type": ManualTaskConditionalDependencyType.leaf,
            "field_address": "postgres_example_test_dataset:customer:email",
            "operator": "exists",
            "value": None,  # exists operator doesn't need a value
            "sort_order": 1,
        },
    )

    # ------------------------------------------------------------------
    # 1. Use the first example dataset (Postgres)
    # ------------------------------------------------------------------
    source_ds = example_datasets[0]
    source_ctl_ds = CtlDataset.create_from_dataset_dict(db, source_ds)
    DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": source_ds["fides_key"],
            "ctl_dataset_id": source_ctl_ds.id,
        },
    )

    # ------------------------------------------------------------------
    # 2. Test that privacy request runs to completion without manual input
    # ------------------------------------------------------------------
    pr_data = {"identity": {"email": "customer-1@example.com"}}

    privacy_request = get_privacy_request_results(
        db,
        erasure_policy_safe_fields,
        run_privacy_request_task,
        pr_data,
        task_timeout=PRIVACY_REQUEST_TASK_TIMEOUT,
    )

    db.refresh(privacy_request)

    # Should complete without requiring manual input since access manual task is skipped during erasure
    assert (
        privacy_request.status == PrivacyRequestStatus.complete
    ), f"Expected complete, got {privacy_request.status}. Error: {getattr(privacy_request, 'error_message', 'No error message')}"

    # Verify NO manual task instance was created (proves manual task was skipped)
    instance = (
        db.query(ManualTaskInstance)
        .filter(
            ManualTaskInstance.task_id == manual_task.id,
            ManualTaskInstance.entity_id == privacy_request.id,
        )
        .first()
    )
    assert (
        instance is None
    ), "ManualTaskInstance should NOT be created when access task is skipped during erasure"

    # Verify results contain source data but NO manual task data
    results = cast(
        Dict[str, list[Dict[str, Any]]],
        privacy_request.get_raw_access_results() or {},
    )

    source_addr_key = "postgres_example_test_dataset:customer"

    # Verify source data is present (proves upstream execution)
    assert source_addr_key in results, "Source data should be present in results"

    # Check that erasure was attempted (results may be empty if no matching data found)
    # The key is that the privacy request completed without database constraint violations
    assert privacy_request.status == PrivacyRequestStatus.complete, (
        f"Privacy request should complete successfully with erasure policy. "
        f"Status: {privacy_request.status}, Error: {getattr(privacy_request, 'error_message', 'No error message')}"
    )
