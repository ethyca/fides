from typing import List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class SnowflakeSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed to connect to Snowflake"""

    account_identifier: str = Field(
        title="Account Name",
        description="The unique identifier for your Snowflake account.",
    )
    user_login_name: str = Field(
        title="Username",
        description="The user account used to authenticate and access the database.",
    )
    password: str = Field(
        title="Password",
        description="The password used to authenticate and access the database.",
        sensitive=True,
    )
    warehouse_name: Optional[str] = Field(
        None,
        title="Warehouse",
        description="The name of the Snowflake warehouse where your queries will be executed.",
    )
    database_name: Optional[str] = Field(
        None,
        title="Database",
        description="The name of the Snowflake database you want to connect to.",
    )
    schema_name: Optional[str] = Field(
        None,
        title="Schema",
        description="The name of the Snowflake schema within the selected database.",
    )
    role_name: Optional[str] = Field(
        None,
        title="Role",
        description="The Snowflake role to assume for the session, if different than Username.",
    )

    _required_components: List[str] = [
        "user_login_name",
        "password",
        "account_identifier",
    ]


class SnowflakeDocsSchema(SnowflakeSchema, NoValidationSchema):
    """Snowflake Secrets Schema for API Docs"""
