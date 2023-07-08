from typing import List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class SnowflakeSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to Snowflake"""


    account_identifier: str = Field(None, title="Account ID")
    user_login_name: str = Field(None, title="Username")
    password: str = Field(None, title="Password", sensitive=True)
    warehouse_name: Optional[str] = Field(None, title="Warehouse")
    database_name: Optional[str] = Field(None, title="Database")
    schema_name: Optional[str] = Field(None, title="Schema")
    role_name: Optional[str] = Field(None, title="Role")

    _required_components: List[str] = [
        "user_login_name",
        "password",
        "account_identifier",
    ]


class SnowflakeDocsSchema(SnowflakeSchema, NoValidationSchema):
    """Snowflake Secrets Schema for API Docs"""
