# pylint: disable=missing-docstring, redefined-outer-name
import os
from typing import Generator

import pytest
from fideslang.models import System, SystemMetadata
from okta.models import Application as OktaApplication
from py._path.local import LocalPath

import fides.ctl.connectors.okta as okta_connector
from fides.ctl.connectors.models import OktaConfig
from fides.ctl.core.config import FidesctlConfig


@pytest.fixture()
def okta_list_applications() -> Generator:
    okta_applications = [
        OktaApplication(
            config={
                "id": "okta_id_1",
                "name": "okta_id_1",
                "label": "okta_label_1",
                "status": "ACTIVE",
            }
        ),
        OktaApplication(
            config={
                "id": "okta_id_2",
                "name": "okta_id_2",
                "label": "okta_label_2",
                "status": "ACTIVE",
            }
        ),
    ]
    yield okta_applications


@pytest.fixture()
def okta_list_applications_with_inactive() -> Generator:
    okta_applications = [
        OktaApplication(
            config={
                "id": "okta_id_1",
                "name": "okta_id_1",
                "label": "okta_label_1",
                "status": "ACTIVE",
            }
        ),
        OktaApplication(
            config={
                "id": "okta_id_2",
                "name": "okta_id_2",
                "label": "okta_label_2",
                "status": "INACTIVE",
            }
        ),
    ]
    yield okta_applications


# Unit
@pytest.mark.unit
def test_create_okta_systems(okta_list_applications: Generator) -> None:
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
def test_create_okta_datasets_filters_inactive(
    okta_list_applications_with_inactive: Generator,
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


# Integration
@pytest.mark.external
def test_list_okta_applications(tmpdir: LocalPath, test_config: FidesctlConfig) -> None:
    client = okta_connector.get_okta_client(
        OktaConfig(
            orgUrl="https://dev-78908748.okta.com",
            token=os.environ["OKTA_CLIENT_TOKEN"],
        )
    )
    actual_result = okta_connector.list_okta_applications(okta_client=client)
    assert actual_result
