from typing import Any, Dict, Generator

import pydash
import pytest
import requests

from faker import Faker
from requests import Response
from sqlalchemy.orm import Session
from sqlalchemy_utils.functions import create_database, database_exists, drop_database

from fides.lib.cryptography import cryptographic_util
from fides.lib.db import session
from fides.api.ctl.sql_models import Dataset as CtlDataset
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets
from tests.ops.test_helpers.db_utils import seed_postgres_data

secrets = get_secrets("surveymonkey")


@pytest.fixture(scope="function")
def surveymonkey_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "surveymonkey.domain") or secrets["domain"],
        "access_token": pydash.get(saas_config, "surveymonkey.access_token")
        or secrets["access_token"],
        "identity_email": pydash.get(saas_config, "surveymonkey.domain")
        or secrets["domain"],
        "surveymonkey_survey_id": {
            "dataset": "surveymonkey_postgres",
            "field": "surveymonkey_surveys.surveymonkey_survey_id",
            "direction": "from",
        },
        "surveymonkey_erasure_survey_id": {
            "dataset": "surveymonkey_postgres",
            "field": "surveymonkey_surveys.surveymonkey_survey_id",
            "direction": "from",
        },
    }


@pytest.fixture(scope="function")
def surveymonkey_identity_email(saas_config):
    return (
        pydash.get(saas_config, "surveymonkey.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def surveymonkey_erasure_identity_email(saas_config):
    return (
        pydash.get(saas_config, "surveymonkey.erasure_identity_email")
        or secrets["erasure_identity_email"]
    )


@pytest.fixture(scope="session")
def surveymonkey_erasure_contact_identity_email(saas_config):
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def surveymonkey_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/surveymonkey_config.yml",
        "<instance_fides_key>",
        "surveymonkey_instance",
    )


@pytest.fixture
def surveymonkey_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/surveymonkey_dataset.yml",
        "<instance_fides_key>",
        "surveymonkey_instance",
    )[0]


@pytest.fixture(scope="function")
def surveymonkey_connection_config(
    db: session, surveymonkey_config, surveymonkey_secrets
) -> Generator:
    fides_key = surveymonkey_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": surveymonkey_secrets,
            "saas_config": surveymonkey_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def surveymonkey_dataset_config(
    db: Session,
    surveymonkey_connection_config: ConnectionConfig,
    surveymonkey_dataset: Dict[str, Any],
) -> Generator:
    fides_key = surveymonkey_dataset["fides_key"]
    surveymonkey_connection_config.name = fides_key
    surveymonkey_connection_config.key = fides_key
    surveymonkey_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, surveymonkey_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": surveymonkey_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture()
def surveymonkey_postgres_dataset() -> Dict[str, Any]:
    return {
        "fides_key": "surveymonkey_postgres",
        "name": "Surveymonkey Postgres",
        "description": "Lookup for Surveymonkey Survey IDs",
        "collections": [
            {
                "name": "surveymonkey_surveys",
                "fields": [
                    {
                        "name": "email",
                        "data_categories": ["user.contact.email"],
                        "fidesops_meta": {"data_type": "string", "identity": "email"},
                    },
                    {
                        "name": "surveymonkey_survey_id",
                        "fidesops_meta": {"data_type": "string"},
                    },
                ],
            }
        ],
    }


@pytest.fixture(scope="function")
def surveymonkey_postgres_db(postgres_integration_session):
    postgres_integration_session = seed_postgres_data(
        postgres_integration_session,
        "./tests/ops/fixtures/saas/external_datasets/surveymonkey.sql",
    )
    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)


@pytest.fixture
def surveymonkey_postgres_dataset_config(
    connection_config: ConnectionConfig,
    surveymonkey_postgres_dataset: Dict[str, Any],
    db: Session,
) -> Generator:
    fides_key = surveymonkey_postgres_dataset["fides_key"]
    connection_config.name = fides_key
    connection_config.key = fides_key
    connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, surveymonkey_postgres_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def surveymonkey_erasure_survey_id(saas_config):
    return (
        pydash.get(saas_config, "surveymonkey.erasure_survey_id")
        or secrets["surveymonkey_erasure_survey_id"]
    )


@pytest.fixture(scope="function")
def surveymonkey_postgres_erasure_db(
    postgres_integration_session,
    surveymonkey_erasure_identity_email,
    surveymonkey_erasure_survey_id,
):
    if database_exists(postgres_integration_session.bind.url):
        # Postgres cannot drop databases from within a transaction block, so
        # we should drop the DB this way instead
        drop_database(postgres_integration_session.bind.url)
    create_database(postgres_integration_session.bind.url)

    create_table_query = "CREATE TABLE public.surveymonkey_surveys (email CHARACTER VARYING(100) PRIMARY KEY,surveymonkey_survey_id CHARACTER VARYING(100));"
    postgres_integration_session.execute(create_table_query)
    insert_query = (
        "INSERT INTO public.surveymonkey_surveys VALUES('"
        + surveymonkey_erasure_identity_email
        + "', '"
        + surveymonkey_erasure_survey_id
        + "')"
    )
    postgres_integration_session.execute(insert_query)

    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)


class SurveymonkeyTestClient:
    """Helper to call various Surveymonkey data management requests"""

    def __init__(self, surveymonkey_connection_config: ConnectionConfig):
        self.surveymonkey_secrets = surveymonkey_connection_config.secrets
        auth_token = self.surveymonkey_secrets["access_token"]
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {auth_token}",
        }
        self.base_url = f"https://{self.surveymonkey_secrets['domain']}"

    def create_contact(self, email: str) -> Response:
        # create a new contact
        faker = Faker()
        body = {
            "first_name": faker.first_name(),
            "last_name": faker.last_name(),
            "email": email,
        }

        contact_response: Response = requests.post(
            url=f"{self.base_url}/v3/contacts", json=body, headers=self.headers
        )
        return contact_response

    def get_contact(self, contact_id: str) -> Response:
        # get contact created for erasure purposes
        url = f"{self.base_url}/v3/contacts/{contact_id}"
        contact_response: Response = requests.get(url=url, headers=self.headers)
        return contact_response

    def delete_contact(self, contact_id) -> Response:
        # delete contact created for erasure purposes
        url = f"{self.base_url}/v3/contacts/{contact_id}"
        contact_response: Response = requests.delete(url=url, headers=self.headers)
        return contact_response

    def get_survey_collectors(self, survey_id: str) -> Response:
        # get survey colelctors for erasure purposes
        url = f"{self.base_url}/v3/surveys/{survey_id}/collectors"
        survey_response: Response = requests.get(url=url, headers=self.headers)
        return survey_response

    def get_collectors_responses(self, collectors_id: str) -> Response:
        # get survey colelctors responses for erasure purposes
        url = f"{self.base_url}/v3/collectors/{collectors_id}/responses/bulk"
        survey_response: Response = requests.get(url=url, headers=self.headers)
        return survey_response

    def get_collectors_response_by_id(
        self, collectors_id: str, response_id: str
    ) -> Response:
        # get specific survey colelctors response for erasure purposes
        url = f"{self.base_url}/v3/collectors/{collectors_id}/responses/{response_id}"
        survey_response: Response = requests.get(url=url, headers=self.headers)
        return survey_response

    def update_survey_response(
        self,
        collectors_id: str,
        response_id: str,
        first_name: str,
        last_name: str,
        email: str,
    ) -> Response:
        # update survey response back that we updated for erasure purposes
        body = {
            "first_name": first_name,
            "last_name": last_name,
            "email_address": email,
        }
        url = f"{self.base_url}/v3/collectors/{collectors_id}/responses/{response_id}"
        survey_response: Response = requests.patch(
            url=url, json=body, headers=self.headers
        )
        return survey_response


@pytest.fixture(scope="function")
def surveymonkey_erasure_data(
    surveymonkey_test_client: SurveymonkeyTestClient,
    surveymonkey_erasure_identity_email: str,
    surveymonkey_erasure_survey_id: str,
    surveymonkey_erasure_contact_identity_email: str,
) -> Generator:

    contact_response = surveymonkey_test_client.create_contact(
        email=surveymonkey_erasure_contact_identity_email
    )
    contact = contact_response.json()

    contact_id = contact["id"]

    error_message = (
        f"Contact with contact id [{contact_id}] could not be added to Surveymonkey"
    )
    poll_for_existence(
        _contact_exists,
        (contact_id, surveymonkey_test_client),
        error_message=error_message,
    )

    survey_collector_response = surveymonkey_test_client.get_survey_collectors(
        survey_id=surveymonkey_erasure_survey_id
    )
    assert survey_collector_response.ok

    survey_collector = survey_collector_response.json()

    survey_collector_id = survey_collector["data"][0]["id"]

    survey_collectors_responses = surveymonkey_test_client.get_collectors_responses(
        collectors_id=survey_collector_id
    )
    assert survey_collectors_responses.ok
    survey_collectors_responses = survey_collectors_responses.json()

    response_id = survey_collectors_responses["data"][0]["id"]

    survey_collectors_response = surveymonkey_test_client.get_collectors_response_by_id(
        collectors_id=survey_collector_id, response_id=response_id
    )

    assert survey_collectors_response.ok
    survey_collectors_response = survey_collectors_response.json()

    response_id = survey_collectors_response["id"]
    first_name = survey_collectors_response["first_name"]
    last_name = survey_collectors_response["last_name"]
    email = survey_collectors_response["email_address"]

    yield contact_id, surveymonkey_erasure_survey_id

    contact_response = surveymonkey_test_client.delete_contact(contact_id)
    # Returns a 200 response code when successful or error based on whether the Contact ID being valid.
    assert contact_response.ok

    # Resetting values of response
    response_update = surveymonkey_test_client.update_survey_response(
        email=email,
        first_name=first_name,
        last_name=last_name,
        collectors_id=survey_collector_id,
        response_id=response_id,
    )
    assert response_update.ok


@pytest.fixture(scope="function")
def surveymonkey_test_client(
    surveymonkey_connection_config: SurveymonkeyTestClient,
) -> Generator:
    test_client = SurveymonkeyTestClient(
        surveymonkey_connection_config=surveymonkey_connection_config
    )
    yield test_client


def _contact_exists(
    contact_id: str, surveymonkey_test_client: SurveymonkeyTestClient
) -> Any:
    """check if the contact exists in the Surveymonkey"""
    contact_response = surveymonkey_test_client.get_contact(contact_id)
    contact = contact_response.json()
    # it return status 200 if contact exists with given id otherwise 400
    if contact_response.ok and contact:
        return contact
    return None
