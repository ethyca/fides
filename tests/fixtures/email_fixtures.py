from typing import Dict, Generator
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.sql_models import Organization
from fides.api.service.connectors.consent_email_connector import (
    GenericConsentEmailConnector,
)
from fides.api.service.connectors.email.attentive_connector import AttentiveConnector
from fides.api.service.connectors.email.sovrn_connector import SovrnConnector
from fides.api.service.connectors.erasure_email_connector import (
    GenericErasureEmailConnector,
)


# generic consent email
@pytest.fixture(scope="function")
def generic_consent_email_connection_config(db: Session) -> Generator:
    name = str(uuid4())
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my_email_connection_config",
            "connection_type": ConnectionType.generic_consent_email,
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
def test_generic_consent_email_connector(
    generic_consent_email_connection_config: Dict[str, str],
) -> GenericConsentEmailConnector:
    return GenericConsentEmailConnector(
        configuration=generic_consent_email_connection_config
    )


# generic erasure email
@pytest.fixture(scope="function")
def generic_erasure_email_connection_config(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": "Attentive",
            "key": "my_email_connection_config",
            "connection_type": ConnectionType.generic_erasure_email,
            "access": AccessLevel.write,
            "secrets": {
                "test_email_address": "processor_address@example.com",
                "recipient_email_address": "attentive@example.com",
                "advanced_settings": {
                    "identity_types": {"email": True, "phone_number": False}
                },
                "third_party_vendor_name": "Attentive",
            },
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def test_generic_erasure_email_connector(
    generic_erasure_email_connection_config: Dict[str, str],
) -> GenericErasureEmailConnector:
    return GenericErasureEmailConnector(
        configuration=generic_erasure_email_connection_config
    )


# Sovrn (consent email)
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


# Attentive (erasure email)
@pytest.fixture(scope="function")
def attentive_email_connection_config(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": "Attentive",
            "key": "my_email_connection_config",
            "connection_type": ConnectionType.attentive,
            "access": AccessLevel.write,
            "secrets": {
                "test_email_address": "processor_address@example.com",
                "recipient_email_address": "attentive@example.com",
                "advanced_settings": {
                    "identity_types": {"email": True, "phone_number": False}
                },
                "third_party_vendor_name": "Attentive",
            },
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def test_attentive_erasure_email_connector(
    attentive_email_connection_config: Dict[str, str]
) -> AttentiveConnector:
    return AttentiveConnector(configuration=attentive_email_connection_config)


@pytest.fixture(scope="function")
def test_fides_org(db: Session) -> Generator:
    test_org = Organization(name="Test Org", fides_key="test_organization")
    db.add(test_org)
    db.commit()
    db.flush()
    yield test_org
    db.delete(test_org)
