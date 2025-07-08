from typing import Any, Dict, cast

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.manual_task import (
    ManualTask,
    ManualTaskConfig,
    ManualTaskConfigField,
    ManualTaskConfigurationType,
    ManualTaskFieldType,
    ManualTaskInstance,
    ManualTaskParentEntityType,
    ManualTaskSubmission,
    ManualTaskType,
)
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.task.manual.manual_task_utils import ManualTaskAddress
from tests.ops.service.privacy_request.test_request_runner_service import (
    PRIVACY_REQUEST_TASK_TIMEOUT,
    get_privacy_request_results,
)


@pytest.mark.integration_postgres
@pytest.mark.integration
@pytest.mark.usefixtures("use_dsr_3_0", "automatically_approved")
def test_privacy_request_runs_after_manual_input(
    db: Session,
    example_datasets: list[Dict],
    connection_config: ConnectionConfig,
    policy,
    run_privacy_request_task,
    postgres_integration_db,
):
    """
    End-to-end test: A downstream Postgres collection should execute after required manual input
    is provided. We create a manual task connection and field, reference it from the Postgres dataset,
    run the request once (expecting requires_input), supply the input, then re-run and validate results.
    """

    # ------------------------------------------------------------------
    # 1. Manual-task connection + field setup
    # ------------------------------------------------------------------
    manual_connection = ConnectionConfig.create(
        db=db,
        data={
            "name": "Manual Connection",
            "key": "manual_connection",
            "connection_type": ConnectionType.manual_task,
            "access": AccessLevel.write,
            "secrets": {},
        },
    )

    manual_task = ManualTask.create(
        db=db,
        data={
            "task_type": ManualTaskType.privacy_request,
            "parent_entity_id": manual_connection.id,
            "parent_entity_type": ManualTaskParentEntityType.connection_config,
        },
    )

    manual_config = ManualTaskConfig.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_type": ManualTaskConfigurationType.access_privacy_request,
            "version": 1,
            "is_current": True,
        },
    )

    manual_field = ManualTaskConfigField.create(
        db=db,
        data={
            "task_id": manual_task.id,
            "config_id": manual_config.id,
            "field_key": "test_customer_id",
            "field_type": ManualTaskFieldType.text,
            "field_metadata": {
                "label": "Customer ID",
                "required": True,
                "data_categories": ["user.unique_id"],
            },
        },
    )

    # ------------------------------------------------------------------
    # 2. Create minimal Postgres dataset with single collection referencing manual data
    # ------------------------------------------------------------------

    downstream_ds = {
        "fides_key": "postgres_manual_downstream_dataset",
        "name": "Postgres Manual Downstream Dataset",
        "description": "Dataset to test manual reference to manual_task data",
        "collections": [
            {
                "name": "orders",
                "fields": [
                    {
                        "name": "id",
                        "data_categories": ["system.operations"],
                    },
                    {
                        "name": "customer_id",
                        "data_categories": ["user.unique_id"],
                        "fides_meta": {
                            "references": [
                                {
                                    "dataset": "manual_connection",
                                    "field": "manual_data.test_customer_id",
                                    "direction": "from",
                                }
                            ]
                        },
                    },
                ],
            }
        ],
    }

    ctl_ds = CtlDataset.create_from_dataset_dict(db, downstream_ds)

    # Attach cloned dataset to existing Postgres connection (connection_config fixture)
    DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": downstream_ds["fides_key"],
            "ctl_dataset_id": ctl_ds.id,
        },
    )

    # ------------------------------------------------------------------
    # 3. Kick off PrivacyRequest (first run – should pause for input)
    # ------------------------------------------------------------------
    pr_data = {"identity": {"email": "customer-1@example.com"}}
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
    assert privacy_request.status == PrivacyRequestStatus.requires_input

    # ------------------------------------------------------------------
    # 4. Provide manual input via ManualTaskSubmission and re-run
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
            "data": {"value": 1},
        },
    )

    # Re-enqueue the same privacy request
    run_privacy_request_task.delay(privacy_request.id).get(
        timeout=PRIVACY_REQUEST_TASK_TIMEOUT
    )
    db.refresh(privacy_request)

    assert privacy_request.status == PrivacyRequestStatus.complete

    results = cast(
        Dict[str, list[Dict[str, Any]]], privacy_request.get_raw_access_results() or {}
    )

    manual_addr_key = ManualTaskAddress.create("manual_connection").value
    orders_addr_key = "postgres_manual_downstream_dataset:orders"

    assert manual_addr_key in results
    assert orders_addr_key in results

    # Manual data contains our submitted value
    assert results[manual_addr_key][0]["test_customer_id"] == 1

    # Ensure downstream Postgres collection returned data and rows reference customer_id 1
    assert len(results[orders_addr_key]) > 0, "Orders collection returned no rows"
    assert all(row["customer_id"] == 1 for row in results[orders_addr_key])
