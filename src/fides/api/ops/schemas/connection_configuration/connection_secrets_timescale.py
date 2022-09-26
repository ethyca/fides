from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets_postgres import (
    PostgreSQLSchema,
)


class TimescaleSchema(PostgreSQLSchema):
    """Schema to validate the secrets needed to connect to TimescaleDB
    This is currently completely using the existing PostgreSQL schema.
    """


class TimescaleDocsSchema(TimescaleSchema, NoValidationSchema):
    """TimescaleDB Secrets Schema for API Docs"""
