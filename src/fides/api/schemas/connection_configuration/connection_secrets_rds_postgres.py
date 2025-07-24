from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets_base_rds import (
    BaseRDSSchema,
)


class RDSPostgresSchema(BaseRDSSchema):
    """
    Schema to validate the secrets needed to connect to a RDS Postgres Database
    """


class RDSPostgresDocsSchema(RDSPostgresSchema, NoValidationSchema):
    """RDS Postgres Secrets Schema for API Docs"""
