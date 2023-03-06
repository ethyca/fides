# pylint: disable=missing-docstring, redefined-outer-name
import pytest
from starlette.testclient import TestClient

from fides.api.ctl.routes.util import API_PREFIX
from fides.api.ctl.sql_models import (  # type: ignore[attr-defined]
    CustomField,
    CustomFieldDefinition,
)
from fides.core.config import FidesConfig


@pytest.fixture
def custom_fields(db, resources_dict):
    definition = CustomFieldDefinition.create_or_update(
        db=db,
        data={
            "name": "my_custom_field_definition",
            "description": "test",
            "field_type": "string",
            "resource_type": "system",
            "field_definition": "string",
        },
    )
    field = CustomField.create(
        db=db,
        data={
            "resource_type": definition.resource_type,
            "resource_id": resources_dict["system"].fides_key,
            "custom_field_definition_id": definition.id,
            "value": "Test value 1",
        },
    )
    yield
    field.delete(db)
    definition.delete(db)


@pytest.mark.integration
@pytest.mark.parametrize(
    "organization_fides_key, expected_status_code",
    [
        ("fake_organization", 404),
        ("default_organization", 200),
    ],
)
def test_datamap(
    test_config: FidesConfig,
    organization_fides_key: str,
    expected_status_code: int,
    test_client: TestClient,
) -> None:
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + organization_fides_key,
        headers=test_config.user.auth_header,
    )
    assert response.status_code == expected_status_code


@pytest.mark.integration
@pytest.mark.parametrize(
    "organization_fides_key, expected_status_code",
    [
        ("fake_organization", 404),
        ("default_organization", 200),
    ],
)
@pytest.mark.usefixtures("custom_fields")
def test_datamap_with_custom_fields(
    test_config,
    organization_fides_key,
    expected_status_code,
    test_client,
):
    response = test_client.get(
        test_config.cli.server_url + API_PREFIX + "/datamap/" + organization_fides_key,
        headers=test_config.user.auth_header,
    )
    assert response.status_code == expected_status_code
