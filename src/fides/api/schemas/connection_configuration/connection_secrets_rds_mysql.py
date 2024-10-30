from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets_base_rds import (
    BaseRDSSchema,
)


class RDSMySQLSchema(BaseRDSSchema):
    """
    Schema to validate the secrets needed to connect to a RDS MySQL Database
    """


class RDSMySQLDocsSchema(RDSMySQLSchema, NoValidationSchema):
    """RDS MySQL Secrets Schema for API Docs"""
