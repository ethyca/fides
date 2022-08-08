import json
from typing import Any, Dict, Generator

import pydash
import pytest
from fideslib.cryptography import cryptographic_util
from sqlalchemy.orm import Session

from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.models.datasetconfig import DatasetConfig
from fidesops.schemas.saas.shared_schemas import HTTPMethod, SaaSRequestParams
from fidesops.service.connectors import SaaSConnector
from fidesops.util.saas_util import format_body, load_config
from tests.ops.fixtures.application_fixtures import load_dataset
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("hubspot")

HUBSPOT_FIRSTNAME = "SomeoneFirstname"


@pytest.fixture(scope="session")
def hubspot_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "hubspot.domain") or secrets["domain"],
        "hapikey": pydash.get(saas_config, "hubspot.hapikey") or secrets["hapikey"],
    }


@pytest.fixture(scope="function")
def hubspot_identity_email(saas_config):
    return (
        pydash.get(saas_config, "hubspot.identity_email") or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def hubspot_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def hubspot_config() -> Dict[str, Any]:
    return load_config("data/saas/config/hubspot_config.yml")


@pytest.fixture
def hubspot_dataset() -> Dict[str, Any]:
    return load_dataset("data/saas/dataset/hubspot_dataset.yml")[0]


@pytest.fixture(scope="function")
def connection_config_hubspot(
    db: Session,
    hubspot_config,
    hubspot_secrets,
) -> Generator:
    fides_key = hubspot_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": hubspot_secrets,
            "saas_config": hubspot_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def dataset_config_hubspot(
    db: Session,
    connection_config_hubspot: ConnectionConfig,
    hubspot_dataset,
    hubspot_config,
) -> Generator:
    fides_key = hubspot_config["fides_key"]
    connection_config_hubspot.name = fides_key
    connection_config_hubspot.key = fides_key
    connection_config_hubspot.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config_hubspot.id,
            "fides_key": fides_key,
            "dataset": hubspot_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def hubspot_erasure_data(
    connection_config_hubspot, hubspot_erasure_identity_email
) -> Generator:
    """
    Gets the current value of the resource and restores it after the test is complete.
    Used for erasure tests.
    """

    connector = SaaSConnector(connection_config_hubspot)

    body = json.dumps(
        {
            "properties": {
                "company": "test company",
                "email": hubspot_erasure_identity_email,
                "firstname": HUBSPOT_FIRSTNAME,
                "lastname": "SomeoneLastname",
                "phone": "(123) 123-1234",
                "website": "someone.net",
            }
        }
    )

    updated_headers, formatted_body = format_body({}, body)

    # create contact
    contacts_request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.POST,
        path=f"/crm/v3/objects/contacts",
        headers=updated_headers,
        body=formatted_body,
    )
    contacts_response = connector.create_client().send(contacts_request)
    contacts_body = contacts_response.json()
    contact_id = contacts_body["id"]

    # no need to subscribe contact, since creating a contact auto-subscribes them

    # Allows contact to be propagated in Hubspot before calling access / erasure requests
    error_message = (
        f"Contact with contact id {contact_id} could not be added to Hubspot"
    )
    poll_for_existence(
        _contact_exists,
        (hubspot_erasure_identity_email, connector),
        error_message=error_message,
    )

    yield contact_id

    # delete contact
    delete_request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.DELETE,
        path=f"/crm/v3/objects/contacts/{contact_id}",
    )
    connector.create_client().send(delete_request)

    # verify contact is deleted
    error_message = (
        f"Contact with contact id {contact_id} could not be deleted from Hubspot"
    )
    poll_for_existence(
        _contact_exists,
        (hubspot_erasure_identity_email, connector),
        error_message=error_message,
        existence_desired=False,
    )


def _contact_exists(
    hubspot_erasure_identity_email: str, connector: SaaSConnector
) -> Any:
    """
    Confirm whether contact exists by calling search api and comparing firstname str.
    """

    body = json.dumps(
        {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "value": hubspot_erasure_identity_email,
                            "propertyName": "email",
                            "operator": "EQ",
                        }
                    ]
                }
            ]
        }
    )

    updated_headers, formatted_body = format_body({}, body)
    contact_request: SaaSRequestParams = SaaSRequestParams(
        method=HTTPMethod.POST,
        path="/crm/v3/objects/contacts/search",
        headers=updated_headers,
        body=formatted_body,
    )
    contact_response = connector.create_client().send(contact_request)
    contact_body = contact_response.json()
    if (
        contact_body["results"]
        and contact_body["results"][0]["properties"]["firstname"] == HUBSPOT_FIRSTNAME
    ):
        return contact_body
