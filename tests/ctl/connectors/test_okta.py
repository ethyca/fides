# pylint: disable=missing-docstring, redefined-outer-name
import os
from typing import Generator, List

import pytest
from fideslang.models import System, SystemMetadata

import fides.connectors.okta as okta_connector
from fides.api.service.connectors.okta_http_client import OktaApplication
from fides.connectors.models import OktaConfig


@pytest.fixture()
def okta_list_applications() -> Generator:
    """Sample Okta applications matching OktaApplication TypedDict."""
    okta_applications: List[OktaApplication] = [
        {
            "id": "okta_id_1",
            "name": "okta_id_1",
            "label": "okta_label_1",
            "status": "ACTIVE",
        },
        {
            "id": "okta_id_2",
            "name": "okta_id_2",
            "label": "okta_label_2",
            "status": "ACTIVE",
        },
    ]
    yield okta_applications


@pytest.fixture()
def okta_list_applications_with_inactive() -> Generator:
    """Sample Okta applications including inactive ones."""
    okta_applications: List[OktaApplication] = [
        {
            "id": "okta_id_1",
            "name": "okta_id_1",
            "label": "okta_label_1",
            "status": "ACTIVE",
        },
        {
            "id": "okta_id_2",
            "name": "okta_id_2",
            "label": "okta_label_2",
            "status": "INACTIVE",
        },
    ]
    yield okta_applications


# Unit
@pytest.mark.unit
def test_create_okta_systems(okta_list_applications: List[OktaApplication]) -> None:
    expected_result = [
        System(
            fides_key="okta_id_1",
            name="okta_id_1",
            fidesctl_meta=SystemMetadata(
                resource_id="okta_id_1",
            ),
            organization_fides_key="default_organization",
            description="Fides Generated Description for Okta Application: okta_label_1",
            system_type="okta_application",
            privacy_declarations=[],
        ),
        System(
            fides_key="okta_id_2",
            name="okta_id_2",
            fidesctl_meta=SystemMetadata(
                resource_id="okta_id_2",
            ),
            organization_fides_key="default_organization",
            description="Fides Generated Description for Okta Application: okta_label_2",
            system_type="okta_application",
            privacy_declarations=[],
        ),
    ]
    okta_systems = okta_connector.create_okta_systems(
        okta_applications=okta_list_applications,
        organization_key="default_organization",
    )
    assert okta_systems == expected_result


@pytest.mark.unit
def test_create_okta_systems_filters_inactive(
    okta_list_applications_with_inactive: List[OktaApplication],
) -> None:
    expected_result = [
        System(
            fides_key="okta_id_1",
            name="okta_id_1",
            fidesctl_meta=SystemMetadata(
                resource_id="okta_id_1",
            ),
            description="Fides Generated Description for Okta Application: okta_label_1",
            system_type="okta_application",
            organization_fides_key="default_organization",
            privacy_declarations=[],
        ),
    ]
    okta_systems = okta_connector.create_okta_systems(
        okta_applications=okta_list_applications_with_inactive,
        organization_key="default_organization",
    )
    assert okta_systems == expected_result


# Integration - requires OAuth2 credentials
@pytest.mark.external
def test_list_okta_applications() -> None:
    """
    Integration test for listing Okta applications.

    Requires environment variables:
    - OKTA_ORG_URL: Your Okta org URL (e.g. https://dev-12345.okta.com)
    - OKTA_CLIENT_ID: OAuth2 client ID
    - OKTA_PRIVATE_KEY: JWK private key (JSON string)
    """
    org_url = os.environ.get("OKTA_ORG_URL")
    client_id = os.environ.get("OKTA_CLIENT_ID")
    private_key = os.environ.get("OKTA_PRIVATE_KEY")

    if not all([org_url, client_id, private_key]):
        pytest.skip("Okta OAuth2 credentials not configured")

    client = okta_connector.get_okta_client(
        OktaConfig(
            orgUrl=org_url,
            clientId=client_id,
            privateKey=private_key,
        )
    )
    actual_result = okta_connector.list_okta_applications(okta_client=client)
    assert isinstance(actual_result, list)
