from typing import Generator, Iterator
import pytest
from starlette.testclient import TestClient
from fides.api.models.detection_discovery import StagedResource
from fides.config import CONFIG, FidesConfig
from sqlalchemy.orm import Session
from fides.api.util.endpoint_utils import API_PREFIX
from fides.config import FidesConfig


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
