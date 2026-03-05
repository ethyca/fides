import pytest
from fideslang.models import Dataset as FideslangDataset

from fides.api.common_exceptions import ValidationError
from fides.api.models.connectionconfig import ConnectionConfig, ConnectionType
from fides.api.schemas.namespace_meta.bigquery_namespace_meta import (  # noqa: F401
    BigQueryNamespaceMeta,
)
from fides.api.schemas.namespace_meta.google_cloud_sql_postgres_namespace_meta import (  # noqa: F401
    GoogleCloudSQLPostgresNamespaceMeta,
)
from fides.api.schemas.namespace_meta.postgres_namespace_meta import (  # noqa: F401
    PostgresNamespaceMeta,
)
from fides.api.schemas.namespace_meta.rds_postgres_namespace_meta import (  # noqa: F401
    RDSPostgresNamespaceMeta,
)
from fides.api.schemas.namespace_meta.snowflake_namespace_meta import (  # noqa: F401
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
        connection_type=ConnectionType.mariadb,
        name="Test Connection",
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    validator.validate(context)


def test_validate_postgres_without_namespace_or_schema():
    """Test validation passes for Postgres without namespace_meta or db_schema.

    Postgres defaults to the public schema, so neither namespace_meta nor
    db_schema is required — this must remain backward compatible.
    """
    dataset = FideslangDataset(fides_key="test_dataset", collections=[])
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.postgres,
        name="Test Connection",
        secrets={},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    validator.validate(context)  # Should not raise — defaults to public schema


def test_validate_postgres_with_valid_namespace():
    """Test validation succeeds with valid Postgres namespace metadata"""
    dataset = FideslangDataset(
        fides_key="test_dataset",
        collections=[],
        fides_meta={
            "namespace": {
                "connection_type": "postgres",
                "schema": "billing",
            }
        },
    )
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.postgres,
        name="Test Connection",
        secrets={},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    validator.validate(context)


def test_validate_postgres_with_connection_defaults():
    """Test validation succeeds when Postgres connection has db_schema in secrets"""
    dataset = FideslangDataset(fides_key="test_dataset", collections=[])
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.postgres,
        name="Test Connection",
        secrets={"db_schema": "billing"},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    validator.validate(context)


def test_validate_postgres_with_invalid_namespace():
    """Test validation fails with invalid Postgres namespace metadata (missing schema)"""
    dataset = FideslangDataset(
        fides_key="test_dataset",
        collections=[],
        fides_meta={
            "namespace": {
                "connection_type": "postgres",
                "database_name": "example_db",  # Missing required schema
            }
        },
    )
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.postgres,
        name="Test Connection",
        secrets={},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    with pytest.raises(ValidationError) as exc:
        validator.validate(context)

    assert "Invalid namespace metadata for postgres" in str(exc.value)


def test_validate_gcs_postgres_without_namespace_or_schema():
    """Test validation passes for GCS Postgres without namespace_meta or db_schema.

    GCS Postgres defaults to the public schema, so neither namespace_meta nor
    db_schema is required — this must remain backward compatible.
    """
    dataset = FideslangDataset(fides_key="test_dataset", collections=[])
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.google_cloud_sql_postgres,
        name="Test Connection",
        secrets={},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    validator.validate(context)  # Should not raise


def test_validate_gcs_postgres_with_valid_namespace():
    """Test validation succeeds with valid GCS Postgres namespace metadata"""
    dataset = FideslangDataset(
        fides_key="test_dataset",
        collections=[],
        fides_meta={
            "namespace": {
                "schema": "billing",
            }
        },
    )
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.google_cloud_sql_postgres,
        name="Test Connection",
        secrets={},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    validator.validate(context)


def test_validate_gcs_postgres_with_connection_defaults():
    """Test validation succeeds when GCS Postgres has db_schema in secrets"""
    dataset = FideslangDataset(fides_key="test_dataset", collections=[])
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.google_cloud_sql_postgres,
        name="Test Connection",
        secrets={"db_schema": "billing"},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    validator.validate(context)


def test_validate_gcs_postgres_with_invalid_namespace():
    """Test validation fails with invalid GCS Postgres namespace metadata"""
    dataset = FideslangDataset(
        fides_key="test_dataset",
        collections=[],
        fides_meta={
            "namespace": {
                "database_name": "prod_db",  # Missing required schema
            }
        },
    )
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.google_cloud_sql_postgres,
        name="Test Connection",
        secrets={},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    with pytest.raises(ValidationError) as exc:
        validator.validate(context)

    assert "Invalid namespace metadata for google_cloud_sql_postgres" in str(exc.value)


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
        "Dataset for snowflake connection must either have namespace metadata "
        "or the connection must have values for the following fields:"
    ) in str(exc.value)
    assert "Schema" in str(exc.value)
    assert "Database" in str(exc.value)


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
            "database_name": "test_db",
            "schema_name": "test_schema",
        },
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    validator.validate(context)


def test_validate_mismatched_namespace_skipped():
    """Test that namespace_meta for a different connection type is silently skipped.

    When datasets of mixed types are linked to a single connection (e.g. a BigQuery
    dataset linked to a Postgres connection), the namespace_meta's connection_type
    discriminator routes validation to the correct schema.
    """
    dataset = FideslangDataset(
        fides_key="test_dataset",
        collections=[],
        fides_meta={
            "namespace": {
                "connection_type": "bigquery",
                "project_id": "my-project",
                "dataset_id": "my_dataset",
            }
        },
    )
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.google_cloud_sql_postgres,
        name="Test Connection",
        secrets={},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    # Should not raise — namespace is for BigQuery, not GCS Postgres
    validator.validate(context)


@pytest.mark.parametrize(
    "falsy_value",
    [None, ""],
)
def test_validate_bigquery_with_missing_dataset(falsy_value):
    """Test validation fails when BigQuery dataset has falsy value in required secret field"""
    dataset = FideslangDataset(fides_key="test_dataset", collections=[])
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.bigquery,
        name="Test Connection",
        secrets={"dataset": falsy_value},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    with pytest.raises(ValidationError) as exc:
        validator.validate(context)

    assert (
        "Dataset for bigquery connection must either have namespace metadata "
        "or the connection must have values for the following fields:"
    ) in str(exc.value)
    assert "Dataset" in str(exc.value)


@pytest.mark.parametrize(
    "field,falsy_value",
    [
        ("database_name", None),
        ("database_name", ""),
        ("schema_name", None),
        ("schema_name", ""),
    ],
)
def test_validate_snowflake_with_missing_required_fields(field, falsy_value):
    """Test validation fails when Snowflake has falsy values in required secret fields"""
    dataset = FideslangDataset(fides_key="test_dataset", collections=[])
    secrets = {
        "database_name": "test_db",
        "schema_name": "test_schema",
    }
    secrets[field] = falsy_value  # Override one field with falsy value

    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.snowflake,
        name="Test Connection",
        secrets=secrets,
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    with pytest.raises(ValidationError) as exc:
        validator.validate(context)

    assert (
        "Dataset for snowflake connection must either have namespace metadata "
        "or the connection must have values for the following fields:"
    ) in str(exc.value)
    assert "Database" in str(exc.value)
    assert "Schema" in str(exc.value)


def test_validate_rds_postgres_with_valid_namespace():
    """Test validation succeeds with valid RDS Postgres namespace metadata"""
    dataset = FideslangDataset(
        fides_key="test_dataset",
        collections=[],
        fides_meta={
            "namespace": {
                "connection_type": "rds_postgres",
                "database_instance_id": "my-rds-instance",
                "database_id": "mydb",
                "schema": "billing",
            }
        },
    )
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.rds_postgres,
        name="Test Connection",
        secrets={},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    validator.validate(context)


def test_validate_rds_postgres_with_invalid_namespace():
    """Test validation fails with invalid RDS Postgres namespace metadata (missing required fields)"""
    dataset = FideslangDataset(
        fides_key="test_dataset",
        collections=[],
        fides_meta={
            "namespace": {
                "connection_type": "rds_postgres",
                "schema": "billing",  # Missing required database_instance_id and database_id
            }
        },
    )
    connection_config = ConnectionConfig(
        key="test_connection",
        connection_type=ConnectionType.rds_postgres,
        name="Test Connection",
        secrets={},
    )
    context = DatasetValidationContext(
        db=None, dataset=dataset, connection_config=connection_config
    )

    validator = NamespaceMetaValidationStep()
    with pytest.raises(ValidationError) as exc:
        validator.validate(context)

    assert "Invalid namespace metadata for rds_postgres" in str(exc.value)
