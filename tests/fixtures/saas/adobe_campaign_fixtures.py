from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from sqlalchemy.orm import Session

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
from fides.lib.cryptography import cryptographic_util
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("adobe_campaign")


@pytest.fixture(scope="function")
def adobe_campaign_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "adobe_campaign.domain") or secrets["domain"],
        "organization": pydash.get(saas_config, "adobe_campaign.organization")
        or secrets["organization"],
        "organization_id": pydash.get(saas_config, "adobe_campaign.organization_id")
        or secrets["organization_id"],
        "client_id": pydash.get(saas_config, "adobe_campaign.client_id")
        or secrets["client_id"],
        "client_secret": pydash.get(saas_config, "adobe_campaign.client_secret")
        or secrets["client_secret"],
        "technical_account_id": pydash.get(
            saas_config, "adobe_campaign.technical_account_id"
        )
        or secrets["technical_account_id"],
        "private_key": pydash.get(saas_config, "adobe_campaign.private_key")
        or secrets["private_key"],
        "namespace": pydash.get(saas_config, "adobe_campaign.namespace")
        or secrets["namespace"],
        "regulation": pydash.get(saas_config, "adobe_campaign.regulation")
        or secrets["regulation"],
    }


@pytest.fixture(scope="function")
def adobe_campaign_identity_email(saas_config):
    return (
        pydash.get(saas_config, "adobe_campaign.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture(scope="function")
def adobe_campaign_erasure_identity_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture
def adobe_campaign_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/adobe_campaign_config.yml",
        "<instance_fides_key>",
        "adobe_campaign_instance",
    )


@pytest.fixture
def adobe_campaign_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/adobe_campaign_dataset.yml" "<instance_fides_key>",
        "adobe_campaign_instance",
    )[0]


@pytest.fixture(scope="function")
def adobe_campaign_connection_config(
    db: Session, adobe_campaign_config, adobe_campaign_secrets
) -> Generator:
    fides_key = adobe_campaign_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": adobe_campaign_secrets,
            "saas_config": adobe_campaign_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def adobe_campaign_dataset_config(
    db: Session,
    adobe_campaign_connection_config: ConnectionConfig,
    adobe_campaign_dataset: Dict[str, Any],
) -> Generator:
    fides_key = adobe_campaign_dataset["fides_key"]
    adobe_campaign_connection_config.name = fides_key
    adobe_campaign_connection_config.key = fides_key
    adobe_campaign_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, adobe_campaign_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": adobe_campaign_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def adobe_campaign_erasure_data(
    adobe_campaign_connection_config: ConnectionConfig,
    adobe_campaign_erasure_identity_email: str,
) -> None:

    secrets = adobe_campaign_connection_config.secrets
    base_url = f"https://{secrets['domain']}/{secrets['organization_id']}"
    headers = {
        "Authorization": f"Bearer {secrets['access_token']}",
        "X-Api-Key": secrets["client_id"],
    }

    # Create profile
    profile_data = {"email": adobe_campaign_erasure_identity_email}
    profile_response = requests.post(
        url=f"{base_url}/campaign/profileAndServices/profile",
        headers=headers,
        json=profile_data,
    )
    assert profile_response.ok
