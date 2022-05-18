import pytest
from okta.models import Application as OktaApplication

import fidesctl.connectors.okta as okta_connector
from fideslang.models import Dataset, DatasetMetadata


@pytest.fixture()
def okta_list_applications():
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
def okta_list_applications_with_inactive():
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
def test_create_okta_datasets(okta_list_applications):
    expected_result = [
        Dataset(
            fides_key="okta_id_1",
            name="okta_id_1",
            fidesctl_meta=DatasetMetadata(
                resource_id="okta_id_1",
            ),
            description=f"Fides Generated Description for Okta Application: okta_label_1",
            data_categories=[],
            collections=[],
        ),
        Dataset(
            fides_key="okta_id_2",
            name="okta_id_2",
            fidesctl_meta=DatasetMetadata(
                resource_id="okta_id_2",
            ),
            description=f"Fides Generated Description for Okta Application: okta_label_2",
            data_categories=[],
            collections=[],
        ),
    ]
    okta_datasets = okta_connector.create_okta_datasets(
        okta_applications=okta_list_applications
    )
    assert okta_datasets == expected_result


@pytest.mark.unit
def test_create_okta_datasets_filters_inactive(okta_list_applications_with_inactive):
    expected_result = [
        Dataset(
            fides_key="okta_id_1",
            name="okta_id_1",
            fidesctl_meta=DatasetMetadata(
                resource_id="okta_id_1",
            ),
            description=f"Fides Generated Description for Okta Application: okta_label_1",
            data_categories=[],
            collections=[],
        ),
    ]
    okta_datasets = okta_connector.create_okta_datasets(
        okta_applications=okta_list_applications_with_inactive
    )
    assert okta_datasets == expected_result


# Integration
@pytest.mark.external
def test_list_okta_applications(tmpdir, test_config):
    client = okta_connector.get_okta_client(org_url="https://dev-78908748.okta.com")
    actual_result = okta_connector.list_okta_applications(okta_client=client)
    assert actual_result
