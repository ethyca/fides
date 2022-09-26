from typing import List, Optional

from fides.api.ops.schemas.base_class import NoValidationSchema
from fides.api.ops.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class SnowflakeSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to Snowflake"""

    user_login_name: Optional[str] = None
    password: Optional[str] = None
    account_identifier: Optional[
        str
    ] = None  # Do not include the snowflakecomputing.com domain name as part of your account identifier.
    database_name: Optional[str] = None
    schema_name: Optional[str] = None
    warehouse_name: Optional[str] = None
    role_name: Optional[str] = None

    _required_components: List[str] = [
        "user_login_name",
        "password",
        "account_identifier",
    ]


class SnowflakeDocsSchema(SnowflakeSchema, NoValidationSchema):
    """Snowflake Secrets Schema for API Docs"""
