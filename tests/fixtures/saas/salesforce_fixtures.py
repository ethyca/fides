import os
from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from fideslib.core.config import load_toml
from fideslib.db import session
from sqlalchemy.orm import Session

from fidesops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.models.datasetconfig import DatasetConfig
from fidesops.util import cryptographic_util
from tests.fixtures.application_fixtures import load_dataset
from tests.fixtures.saas_example_fixtures import load_config

saas_config = load_toml(["saas_config.toml"])


@pytest.fixture(scope="session")
def salesforce_secrets():
    return {
        "domain": pydash.get(saas_config, "salesforce.domain")
        or os.environ.get("SALESFORCE_DOMAIN"),
        "username": pydash.get(saas_config, "salesforce.username")
        or os.environ.get("SALESFORCE_USERNAME"),
        "password": pydash.get(saas_config, "salesforce.password")
        or os.environ.get("SALESFORCE_PASSWORD"),
        "client_id": pydash.get(saas_config, "salesforce.client_id")
        or os.environ.get("SALESFORCE_CLIENT_ID"),
        "client_secret": pydash.get(saas_config, "salesforce.client_secret")
        or os.environ.get("SALESFORCE_CLIENT_SECRET"),
        "access_token": pydash.get(saas_config, "salesforce.access_token")
        or os.environ.get("SALESFORCE_ACCESS_TOKEN"),
    }


@pytest.fixture(scope="session")
def salesforce_identity_email():
    return pydash.get(saas_config, "salesforce.identity_email") or os.environ.get(
        "SALESFORCE_IDENTITY_EMAIL"
    )


@pytest.fixture(scope="session")
def salesforce_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture(scope="session")
def salesforce_token(salesforce_secrets) -> str:
    body = {
        "client_id": salesforce_secrets["client_id"],
        "client_secret": salesforce_secrets["client_secret"],
        "grant_type": "password",
        "username": salesforce_secrets["username"],
        "password": salesforce_secrets["password"],
    }
    response = requests.post(
        "https://" + salesforce_secrets["domain"] + "/services/oauth2/token", body
    )
    return response.json()["access_token"]


@pytest.fixture
def salesforce_config() -> Dict[str, Any]:
    return load_config("data/saas/config/salesforce_config.yml")


@pytest.fixture
def salesforce_dataset() -> Dict[str, Any]:
    return load_dataset("data/saas/dataset/salesforce_dataset.yml")[0]


@pytest.fixture(scope="function")
def salesforce_connection_config(
    db: session,
    salesforce_config,
    salesforce_secrets,
    salesforce_token,
) -> Generator:
    fides_key = salesforce_config["fides_key"]
    salesforce_secrets["access_token"] = salesforce_token
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": salesforce_secrets,
            "saas_config": salesforce_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def salesforce_dataset_config(
    db: Session,
    salesforce_connection_config: ConnectionConfig,
    salesforce_dataset: Dict[str, Any],
) -> Generator:
    fides_key = salesforce_dataset["fides_key"]
    salesforce_connection_config.name = fides_key
    salesforce_connection_config.key = fides_key
    salesforce_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": salesforce_connection_config.id,
            "fides_key": fides_key,
            "dataset": salesforce_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def salesforce_create_erasure_data(
    salesforce_identity_email, salesforce_secrets
) -> Generator:
    """
    Creates a dynamic test data record for tests.
    Yields contact ID as this may be useful to have in test scenarios
    """

    base_url = f"https://{salesforce_secrets['domain']}"
    headers = {
        "Authorization": f"Bearer {salesforce_secrets['access_token']}",
    }

    # Create account
    account_data = {"name": "Ethyca Test"}
    accounts_response = requests.post(
        url=f"{base_url}/services/data/v54.0/sobjects/Account",
        headers=headers,
        json=account_data,
    )
    assert accounts_response.ok
    account_id = accounts_response.json()["id"]

    # Create contact
    contact_data = {
        "firstName": "Fidesops",
        "lastName": "Test Contact",
        "email": salesforce_identity_email,
        "AccountId": account_id,
    }
    contacts_response = requests.post(
        url=f"{base_url}/services/data/v54.0/sobjects/Contact",
        headers=headers,
        json=contact_data,
    )
    assert contacts_response.ok
    contact_id = contacts_response.json()["id"]

    # Create lead
    lead_data = {
        "firstName": "Fidesops",
        "lastName": "Test Lead",
        "email": salesforce_identity_email,
        "Company": "Test Company",
    }
    leads_response = requests.post(
        url=f"{base_url}/services/data/v54.0/sobjects/Lead",
        headers=headers,
        json=lead_data,
    )
    assert leads_response.ok
    lead_id = leads_response.json()["id"]

    # Create Case
    case_data = {
        "SuppliedEmail": salesforce_identity_email,
        "SuppliedCompany": "Test Company",
        "ContactId": contact_id,
    }
    cases_response = requests.post(
        url=f"{base_url}/services/data/v54.0/sobjects/Case",
        headers=headers,
        json=case_data,
    )
    assert cases_response.ok
    case_id = cases_response.json()["id"]

    # Create Campaign Member

    # We need to create a campaign for it first
    campaign_data = {
        "Description": "Test Description",
        "Name": "Test Campaign",
    }
    campaigns_response = requests.post(
        url=f"{base_url}/services/data/v54.0/sobjects/Campaign",
        headers=headers,
        json=campaign_data,
    )
    assert campaigns_response.ok
    campaign_id = campaigns_response.json()["id"]

    # Now creating campaign member for this campaign
    campaign_member_data = {
        "campaignId": campaign_id,
        "contactId": contact_id,
        "leadId": lead_id,
    }
    campaign_members_response = requests.post(
        url=f"{base_url}/services/data/v54.0/sobjects/CampaignMember",
        headers=headers,
        json=campaign_member_data,
    )
    assert campaign_members_response.ok
    campaign_member_id = campaign_members_response.json()["id"]

    yield contact_id, lead_id, case_id, account_id, campaign_member_id
