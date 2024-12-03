from typing import Iterator

import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.detection_discovery import StagedResource
from fides.api.models.sql_models import System
from fides.api.util.endpoint_utils import API_PREFIX
from fides.config import CONFIG, FidesConfig
import uuid


@pytest.fixture(scope="function")
def sample_projects(
    db: Session,
) -> Iterator:
    """Fixture to add sample projects to the database"""
    resources = [
        StagedResource(
            urn="test_monitor_config_id.test_project",
            name="test_project",
            resource_type="Database",
            monitor_config_id="test_monitor_config_id",
            description="test project",
            diff_status="addition",
            child_diff_statuses={},
        ),
        StagedResource(
            urn="test_monitor_config_id.test_project2",
            name="test_project2",
            resource_type="Database",
            monitor_config_id="test_monitor_config_id",
            description="test project2",
            diff_status="addition",
            child_diff_statuses={},
            hidden=True,
        ),
    ]
    for resource in resources:
        db.add(resource)
    db.commit()
    yield resources
    for resource in resources:
        db.delete(resource)
    db.commit()


@pytest.fixture(scope="function")
def sample_datasets(
    db: Session,
) -> Iterator:
    """Fixture to add sample datasets to the database"""
    resources = [
        StagedResource(
            urn="test_monitor_config_id.test_dataset",
            name="test_dataset",
            resource_type="schema",
            monitor_config_id="test_monitor_config_id",
            description="test dataset",
            diff_status="addition",
            child_diff_statuses={},
        ),
        StagedResource(
            urn="test_monitor_config_id.test_dataset2",
            name="test_dataset2",
            resource_type="schema",
            monitor_config_id="test_monitor_config_id",
            description="test dataset2",
            diff_status="addition",
            child_diff_statuses={},
            hidden=True,
        ),
    ]
    for resource in resources:
        db.add(resource)
    db.commit()
    yield resources
    for resource in resources:
        db.delete(resource)
    db.commit()


@pytest.fixture(scope="function")
def sample_systems(
    db: Session,
) -> Iterator:
    """Fixture to add sample systems to the database"""
    system_id = "aaaad"
    connection = ConnectionConfig(
        id="aaaaa",
        name="test integration",
        key="test_system_with_connections",
        description="test integration for system with connections",
        connection_type=ConnectionType.fides,
        system_id=system_id,
        secrets={},
        access=AccessLevel.read,
    )
    systems = [
        System(
            id="aaaab",
            fides_key="test_system_no_integrations",
            name="test_system_no_integrations",
            description="test system with no connections to datasets or integrations",
            organization_fides_key="default_organization",
            system_type="",
        ),
        System(
            id="aaaac",
            fides_key="test_system_with_datasets",
            name="test_system_with_datasets",
            description="test system with connections to datasets",
            dataset_references=["test_dataset"],
            organization_fides_key="default_organization",
            system_type="",
        ),
        System(
            id=system_id,
            fides_key="test_system_with_connections",
            name="test_system_with_connections",
            description="test system with connections to integrations",
            organization_fides_key="default_organization",
            system_type="",
        ),
        System(
            id="aaaaf",
            fides_key="test_system_hidden",
            name="test_system_hidden",
            description="test system hidden",
            dataset_references=["test_dataset"],
            hidden=True,
            organization_fides_key="default_organization",
            system_type="",
        ),
    ]

    db.add(connection)
    for system in systems:
        db.add(system)
    db.commit()
    yield systems
    db.delete(connection)
    for system in systems:
        db.delete(system)
    db.commit()


def test_lifecycle_get_projects(
    test_config: FidesConfig,
    test_client: TestClient,
    sample_projects: None,
):

    result = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/lifecycle/project",
        headers=test_config.user.auth_header,
    )
    assert result.status_code == 200

    expected_non_hidden = [
        resource for resource in sample_projects if not resource.hidden
    ]
    assert len(result.json()["items"]) == len(expected_non_hidden)

    result = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/lifecycle/project",
        headers=test_config.user.auth_header,
        params={"show_hidden": "true"},
    )
    assert result.status_code == 200
    assert len(result.json()["items"]) == len([project for project in sample_projects])


def test_lifecycle_get_datasets(
    test_config: FidesConfig,
    test_client: TestClient,
    sample_datasets: None,
):

    result = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/lifecycle/dataset",
        headers=test_config.user.auth_header,
    )
    assert result.status_code == 200

    expected_non_hidden = [
        resource for resource in sample_datasets if not resource.hidden
    ]
    assert len(result.json()["items"]) == len(expected_non_hidden)

    result = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/lifecycle/dataset",
        headers=test_config.user.auth_header,
        params={"show_hidden": "true"},
    )
    assert result.status_code == 200
    assert len(result.json()["items"]) == len([dataset for dataset in sample_datasets])


def test_lifecycle_get_systems(
    test_config: FidesConfig,
    test_client: TestClient,
    sample_systems: None,
):

    result = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/lifecycle/system",
        headers=test_config.user.auth_header,
    )
    assert result.status_code == 200
    assert len(result.json()["items"]) == 2
    actual_systems = result.json()["items"]
    assert set([system["fides_key"] for system in actual_systems]) == set(
        [
            "test_system_with_connections",
            "test_system_with_datasets",
        ]
    )

    result = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/lifecycle/system",
        headers=test_config.user.auth_header,
        params={"show_hidden": "true"},
    )
    assert result.status_code == 200
    assert len(result.json()["items"]) == 3

    # assert that on each system in response we have whether it is hidden or not and the monitor_config_ids
    for system in result.json()["items"]:
        print(f"system: {system}")
