from typing import Dict, Generator, List
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.ctl.sql_models import Dataset as CtlDataset
from fides.api.ctl.sql_models import Organization
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.service.connectors import SovrnConnector


@pytest.fixture(scope="function")
def email_connection_config(db: Session) -> Generator:
    name = str(uuid4())
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my_email_connection_config",
            "connection_type": ConnectionType.email,
            "access": AccessLevel.write,
            "secrets": {
                "test_email_address": "processor_address@example.com",
                "recipient_email_address": "test@example.com",
                "third_party_vendor_name": "Email",
            },
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def email_dataset_config(
    email_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    email_dataset = example_datasets[9]
    fides_key = email_dataset["fides_key"]
    email_connection_config.name = fides_key
    email_connection_config.key = fides_key
    email_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, email_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": email_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture(scope="function")
def sovrn_email_connection_config(db: Session) -> Generator:
    name = str(uuid4())
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my_email_connection_config",
            "connection_type": ConnectionType.sovrn,
            "access": AccessLevel.write,
            "secrets": {
                "test_email_address": "processor_address@example.com",
                "recipient_email_address": "sovrn@example.com",
                "advanced_settings": {
                    "identity_types": {
                        "email": False,
                        "phone_number": False,
                        "cookie_ids": ["ljt_readerID"],
                    }
                },
                "third_party_vendor_name": "Sovrn",
            },
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def test_sovrn_consent_email_connector(
    sovrn_email_connection_config: Dict[str, str],
) -> SovrnConnector:
    return SovrnConnector(configuration=sovrn_email_connection_config)


@pytest.fixture(scope="function")
def test_fides_org(db: Session) -> Generator:
    test_org = Organization(name="Test Org", fides_key="test_organization")
    db.add(test_org)
    db.commit()
    db.flush()
    yield test_org
    db.delete(test_org)
