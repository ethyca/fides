from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from sqlalchemy.orm import Session
from starlette.status import HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from fides.api.cryptography import cryptographic_util
from fides.api.db import session
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from tests.ops.test_helpers.vault_client import get_secrets
from tests.ops.integration_tests.saas.connector_runner import ConnectorRunner

secrets = get_secrets("salesforce")


@pytest.fixture(scope="session")
def salesforce_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "salesforce.domain") or secrets["domain"],
        "client_id": pydash.get(saas_config, "salesforce.client_id")
        or secrets["client_id"],
        "client_secret": pydash.get(saas_config, "salesforce.client_secret")
        or secrets["client_secret"],
        "redirect_uri": pydash.get(saas_config, "salesforce.redirect_uri")
        or secrets["redirect_uri"],
        "access_token": pydash.get(saas_config, "salesforce.access_token")
        or secrets["access_token"],
        "refresh_token": pydash.get(saas_config, "salesforce.refresh_token")
        or secrets["refresh_token"],
    }


@pytest.fixture(scope="session")
def salesforce_identity_email(saas_config):
    return (
        pydash.get(saas_config, "salesforce.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def salesforce_identity_phone_number(saas_config):
    return (
        pydash.get(saas_config, "salesforce.identity_phone_number")
        or secrets["identity_phone_number"]
    )


@pytest.fixture(scope="session")
def salesforce_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture(scope="function")
def salesforce_create_erasure_data(
    salesforce_erasure_identity_email, salesforce_secrets
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
        "email": salesforce_erasure_identity_email,
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
        "email": salesforce_erasure_identity_email,
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
        "SuppliedEmail": salesforce_erasure_identity_email,
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

    yield account_id, contact_id, case_id, lead_id, campaign_member_id

    # cleanup data by doing a full deletion instead of just masking
    case_response = requests.delete(
        url=f"{base_url}/services/data/v54.0/sobjects/Case/{case_id}", headers=headers
    )
    assert case_response.status_code == HTTP_204_NO_CONTENT

    case_response = requests.get(
        url=f"{base_url}/services/data/v54.0/sobjects/Case/{case_id}", headers=headers
    )
    assert case_response.status_code == HTTP_404_NOT_FOUND

    account_response = requests.delete(
        url=f"{base_url}/services/data/v54.0/sobjects/Account/{account_id}",
        headers=headers,
    )
    assert account_response.status_code == HTTP_204_NO_CONTENT

    account_response = requests.get(
        url=f"{base_url}/services/data/v54.0/sobjects/Account/{account_id}",
        headers=headers,
    )
    assert account_response.status_code == HTTP_404_NOT_FOUND


@pytest.fixture
def salesforce_runner(
    db,
    cache,
    salesforce_secrets,
) -> ConnectorRunner:
    return ConnectorRunner(db, cache, "salesforce", salesforce_secrets)
