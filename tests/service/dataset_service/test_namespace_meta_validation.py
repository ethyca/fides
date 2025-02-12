import pytest
from fideslang.models import Dataset as FideslangDataset

from fides.api.common_exceptions import ValidationError
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.schemas.namespace_meta.bigquery_namespace_meta import (
    BigQueryNamespaceMeta,
)
from fides.api.schemas.namespace_meta.snowflake_namespace_meta import (
    SnowflakeNamespaceMeta,
)
from fides.service.dataset.dataset_validator import DatasetValidationContext
from fides.service.dataset.validation_steps.namespace_meta import (
    NamespaceMetaValidationStep,
)


def test_validate_no_connection_config():
    """Test validation when no connection config is provided"""
    dataset = FideslangDataset(fides_key="test_dataset", collections=[])
    context = DatasetValidationContext(db=None, dataset=dataset, connection_config=None)

    validator = NamespaceMetaValidationStep()
    validator.validate(context)  # Should not raise any exceptions


def test_validate_unsupported_connection_type():
    """Test validation with a connection type that doesn't require namespace metadata"""
    dataset = FideslangDataset(fides_key="test_dataset", collections=[])
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.postgres,
        name="Test Connection",
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    validator.validate(context)


def test_validate_snowflake_missing_namespace_and_secrets():
    """Test validation fails when Snowflake dataset has no namespace metadata and missing required secrets"""
    dataset = FideslangDataset(fides_key="test_dataset", collections=[])
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.snowflake,
        name="Test Connection",
        secrets={},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    with pytest.raises(ValidationError) as exc:
        validator.validate(context)

    assert (
        "Dataset for snowflake connection must either have namespace metadata or the connection must have the following configuration: account_identifier, user_login_name, warehouse_name"
        in str(exc.value)
    )


def test_validate_snowflake_with_valid_namespace():
    """Test validation succeeds with valid Snowflake namespace metadata"""
    dataset = FideslangDataset(
        fides_key="test_dataset",
        collections=[],
        fides_meta={
            "namespace": {
                "database_name": "TEST_DB",
                "schema": "TEST_SCHEMA",
            }
        },
    )
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.snowflake,
        name="Test Connection",
        secrets={},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    validator.validate(context)


def test_validate_snowflake_with_invalid_namespace():
    """Test validation fails with invalid Snowflake namespace metadata"""
    dataset = FideslangDataset(
        fides_key="test_dataset",
        collections=[],
        fides_meta={
            "namespace": {
                "schema": "TEST_SCHEMA",  # Missing required database_name
            }
        },
    )
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.snowflake,
        name="Test Connection",
        secrets={},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    with pytest.raises(ValidationError) as exc:
        validator.validate(context)

    assert "Invalid namespace metadata for snowflake" in str(exc.value)


def test_validate_bigquery_with_valid_namespace():
    """Test validation succeeds with valid BigQuery namespace metadata"""
    dataset = FideslangDataset(
        fides_key="test_dataset",
        collections=[],
        fides_meta={
            "namespace": {
                "project_id": "test-project",
                "dataset_id": "test_dataset",
            }
        },
    )
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.bigquery,
        name="Test Connection",
        secrets={},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    validator.validate(context)


def test_validate_bigquery_with_invalid_namespace():
    """Test validation fails with invalid BigQuery namespace metadata"""
    dataset = FideslangDataset(
        fides_key="test_dataset",
        collections=[],
        fides_meta={
            "namespace": {
                "dataset_id": "test_dataset",  # Missing required project_id
            }
        },
    )
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.bigquery,
        name="Test Connection",
        secrets={},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    with pytest.raises(ValidationError) as exc:
        validator.validate(context)

    assert "Invalid namespace metadata for bigquery" in str(exc.value)


def test_validate_with_connection_defaults():
    """Test validation succeeds when connection has required secret fields"""
    dataset = FideslangDataset(fides_key="test_dataset", collections=[])
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.snowflake,
        name="Test Connection",
        secrets={
            "account_identifier": "test_account",
            "user_login_name": "test_user",
            "warehouse_name": "test_warehouse",
            "password": "test_password",
        },
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    validator.validate(context)
