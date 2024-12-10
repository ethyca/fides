from typing import Dict, Generator
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset, Organization
from fides.api.service.connectors.consent_email_connector import (
    GenericConsentEmailConnector,
)
from fides.api.service.connectors.dynamic_erasure_email_connector import (
    DynamicErasureEmailConnector,
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
            "name": "Attentive Email",
            "key": "my_email_connection_config",
            "connection_type": ConnectionType.generic_erasure_email,
            "access": AccessLevel.write,
            "secrets": {
                "test_email_address": "processor_address@example.com",
                "recipient_email_address": "attentive@example.com",
                "advanced_settings": {
                    "identity_types": {"email": True, "phone_number": False}
                },
                "third_party_vendor_name": "Attentive Email",
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
            "name": "Attentive Email",
            "key": "my_email_connection_config",
            "connection_type": ConnectionType.attentive_email,
            "access": AccessLevel.write,
            "secrets": {
                "test_email_address": "processor_address@example.com",
                "recipient_email_address": "attentive@example.com",
                "advanced_settings": {
                    "identity_types": {"email": True, "phone_number": False}
                },
                "third_party_vendor_name": "Attentive Email",
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


# Dynamic erasure email integration


@pytest.fixture(scope="function")
def dynamic_email_address_config_dataset(
    db: Session, test_fides_org: Organization
) -> Generator[Dataset, None, None]:
    dataset = Dataset.create(
        db=db,
        data={
            "name": "postgres_example_custom_request_field_dataset",
            "fides_key": "postgres_example_custom_request_field_dataset",
            "organization_fides_key": test_fides_org.fides_key,
            "collections": [
                {
                    "name": "dynamic_email_address_config",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                            "fides_meta": {"data_type": "string"},
                        },
                        {
                            "name": "email_address",
                            "data_categories": ["system.operations"],
                            "fides_meta": {"data_type": "string"},
                        },
                        {
                            "name": "vendor_name",
                            "data_categories": ["system.operations"],
                            "fides_meta": {"data_type": "string"},
                        },
                        {
                            "name": "site_id",
                            "data_categories": ["system.operations"],
                            "fides_meta": {
                                "data_type": "string",
                                "custom_request_field": "tenant_id",
                            },
                        },
                    ],
                }
            ],
        },
    )
    yield dataset
    dataset.delete(db)


@pytest.fixture(scope="function")
def dynamic_email_address_config_second_dataset(
    db: Session, test_fides_org: Organization
) -> Generator[Dataset, None, None]:
    dataset = Dataset.create(
        db=db,
        data={
            "name": "second_dataset",
            "fides_key": "second_dataset",
            "organization_fides_key": test_fides_org.fides_key,
            "collections": [
                {
                    "name": "dynamic_email_address_config",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["system.operations"],
                            "fides_meta": {"data_type": "string"},
                        },
                        {
                            "name": "email_address",
                            "data_categories": ["system.operations"],
                            "fides_meta": {"data_type": "string"},
                        },
                        {
                            "name": "vendor_name",
                            "data_categories": ["system.operations"],
                            "fides_meta": {"data_type": "string"},
                        },
                        {
                            "name": "custom_field",
                            "data_categories": ["system.operations"],
                            "fides_meta": {
                                "data_type": "string",
                                "custom_request_field": "custom_field",
                            },
                        },
                    ],
                },
                {
                    "name": "dynamic_email_address_config_2",
                    "fields": [
                        {
                            "name": "id2",
                            "data_categories": ["system.operations"],
                            "fides_meta": {"data_type": "string"},
                        },
                        {
                            "name": "email_address2",
                            "data_categories": ["system.operations"],
                            "fides_meta": {"data_type": "string"},
                        },
                        {
                            "name": "vendor_name2",
                            "data_categories": ["system.operations"],
                            "fides_meta": {"data_type": "string"},
                        },
                        {
                            "name": "site_id2",
                            "data_categories": ["system.operations"],
                            "fides_meta": {
                                "data_type": "string",
                                "custom_request_field": "tenant_id",
                            },
                        },
                    ],
                },
            ],
        },
    )
    yield dataset
    dataset.delete(db)


@pytest.fixture(scope="function")
def dynamic_email_address_config_dataset_config(
    db: Session,
    dynamic_email_address_config_dataset: Dataset,
    connection_config: ConnectionConfig,  # postgres_example connection config
):
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "ctl_dataset_id": dynamic_email_address_config_dataset.id,
            "connection_config_id": connection_config.id,
            "fides_key": "postgres_example_custom_request_field_dataset",
        },
    )

    yield dataset_config
    dataset_config.delete(db)


@pytest.fixture(scope="function")
def dynamic_email_address_config_dataset_config_second_dataset(
    db: Session,
    dynamic_email_address_config_second_dataset: Dataset,
    connection_config: ConnectionConfig,  # postgres_example connection config
):
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "ctl_dataset_id": dynamic_email_address_config_second_dataset.id,
            "connection_config_id": connection_config.id,
            "fides_key": "second_dataset",
        },
    )

    yield dataset_config
    dataset_config.delete(db)


@pytest.fixture(scope="function")
def dynamic_erasure_email_connection_config(
    db: Session,
    dynamic_email_address_config_dataset_config: DatasetConfig,
) -> Generator[ConnectionConfig, None, None]:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": "Dynamic Erasure Email Config",
            "key": "my_dynamic_erasure_email_config",
            "connection_type": ConnectionType.dynamic_erasure_email,
            "access": AccessLevel.write,
            "secrets": {
                "test_email_address": "test@example.com",
                "recipient_email_address": {
                    "dataset": dynamic_email_address_config_dataset_config.fides_key,
                    "field": "dynamic_email_address_config.email_address",
                },
                "advanced_settings": {
                    "identity_types": {"email": True, "phone_number": False}
                },
                "third_party_vendor_name": {
                    "dataset": dynamic_email_address_config_dataset_config.fides_key,
                    "field": "dynamic_email_address_config.vendor_name",
                },
            },
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def test_dynamic_erasure_email_connector(
    dynamic_erasure_email_connection_config: ConnectionConfig,
) -> DynamicErasureEmailConnector:
    return DynamicErasureEmailConnector(
        configuration=dynamic_erasure_email_connection_config
    )


@pytest.fixture(scope="function")
def dynamic_erasure_email_connection_config_no_secrets(
    db: Session,
) -> Generator[ConnectionConfig, None, None]:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": "Dynamic Erasure Email Config",
            "key": "my_dynamic_erasure_email_config",
            "connection_type": ConnectionType.dynamic_erasure_email,
            "access": AccessLevel.write,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def dynamic_erasure_email_connector_config_invalid_dataset(
    db: Session,
) -> Generator[ConnectionConfig, None, None]:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": "Dynamic Erasure Email Invalid Config",
            "key": "my_dynamic_erasure_email_invalid_config",
            "connection_type": ConnectionType.dynamic_erasure_email,
            "access": AccessLevel.write,
            "secrets": {
                "test_email_address": "test@example.com",
                "recipient_email_address": {
                    "dataset": "nonexistent_dataset",
                    "field": "collection.field",
                },
                "advanced_settings": {
                    "identity_types": {"email": True, "phone_number": False}
                },
                "third_party_vendor_name": {
                    "dataset": "nonexistent_dataset",
                    "field": "collection.field2",
                },
            },
        },
    )
    connector = DynamicErasureEmailConnector(configuration=connection_config)
    yield connector
    connection_config.delete(db)


@pytest.fixture(scope="function")
def dynamic_erasure_email_connector_config_invalid_field(
    db: Session,
    dynamic_email_address_config_dataset_config: DatasetConfig,
) -> Generator[ConnectionConfig, None, None]:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": "Dynamic Erasure Email Invalid Config",
            "key": "my_dynamic_erasure_email_invalid_config",
            "connection_type": ConnectionType.dynamic_erasure_email,
            "access": AccessLevel.write,
            "secrets": {
                "test_email_address": "test@example.com",
                "recipient_email_address": {
                    "dataset": dynamic_email_address_config_dataset_config.fides_key,
                    "field": "weird-field-no-dots",
                },
                "advanced_settings": {
                    "identity_types": {"email": True, "phone_number": False}
                },
                "third_party_vendor_name": {
                    "dataset": dynamic_email_address_config_dataset_config.fides_key,
                    "field": "dynamic_email_address_config.vendor_name",
                },
            },
        },
    )
    connector = DynamicErasureEmailConnector(configuration=connection_config)
    yield connector
    connection_config.delete(db)


@pytest.fixture(scope="function")
def dynamic_erasure_email_connection_config_different_datasets(
    db: Session,
    dynamic_email_address_config_dataset_config: DatasetConfig,
    dynamic_email_address_config_dataset_config_second_dataset: DatasetConfig,
) -> Generator[ConnectionConfig, None, None]:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": "Dynamic Erasure Email Config",
            "key": "my_dynamic_erasure_email_config_mismatched_datasets",
            "connection_type": ConnectionType.dynamic_erasure_email,
            "access": AccessLevel.write,
            "secrets": {
                "test_email_address": "test@example.com",
                "recipient_email_address": {
                    "dataset": dynamic_email_address_config_dataset_config.fides_key,
                    "field": "dynamic_email_address_config.email_address",
                },
                "advanced_settings": {
                    "identity_types": {"email": True, "phone_number": False}
                },
                "third_party_vendor_name": {
                    "dataset": dynamic_email_address_config_dataset_config_second_dataset.fides_key,
                    "field": "dynamic_email_address_config.vendor_name",
                },
            },
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def dynamic_erasure_email_connection_config_different_collections(
    db: Session,
    dynamic_email_address_config_dataset_config_second_dataset: DatasetConfig,
) -> Generator[ConnectionConfig, None, None]:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": "Dynamic Erasure Email Config",
            "key": "my_dynamic_erasure_email_config_mismatched_datasets",
            "connection_type": ConnectionType.dynamic_erasure_email,
            "access": AccessLevel.write,
            "secrets": {
                "test_email_address": "test@example.com",
                "recipient_email_address": {
                    "dataset": dynamic_email_address_config_dataset_config_second_dataset.fides_key,
                    "field": "dynamic_email_address_config.email_address",
                },
                "advanced_settings": {
                    "identity_types": {"email": True, "phone_number": False}
                },
                "third_party_vendor_name": {
                    "dataset": dynamic_email_address_config_dataset_config_second_dataset.fides_key,
                    "field": "dynamic_email_address_config2.vendor_name",
                },
            },
        },
    )
    yield connection_config
    connection_config.delete(db)
