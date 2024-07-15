from typing import List, Optional

from pydantic import Field, root_validator

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


def format_private_key(raw_key):
    # Split the key into parts and remove spaces from the key body
    parts = raw_key.split('-----')
    body = parts[2].replace(' ', '\n')
    # Reassemble the key
    return f"-----{parts[1]}-----{body}-----{parts[3]}-----"


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
    password: Optional[str] = Field(
        title="Password",
        description="The password used to authenticate and access the database. You can use a password or a private key, but not both.",
        sensitive=True,
    )
    private_key: Optional[str] = Field(
        title="Private key",
        description="The private key used to authenticate and access the database. If a `private_key_passphrase` is also provided, it is assumed to be encrypted; otherwise, it is assumed to be unencrypted.",
        sensitive=True,
    )
    private_key_passphrase: Optional[str] = Field(
        title="Passphrase",
        description="The passphrase used for the encrypted private key.",
        sensitive=True,
    )
    warehouse_name: str = Field(
        title="Warehouse",
        description="The name of the Snowflake warehouse where your queries will be executed.",
    )
    database_name: str = Field(
        title="Database",
        description="The name of the Snowflake database you want to connect to.",
    )
    schema_name: str = Field(
        title="Schema",
        description="The name of the Snowflake schema within the selected database.",
    )
    role_name: Optional[str] = Field(
        None,
        title="Role",
        description="The Snowflake role to assume for the session, if different than Username.",
    )

    _required_components: List[str] = [
        "account_identifier",
        "user_login_name",
        "warehouse_name",
        "database_name",
        "schema_name",
    ]

    @root_validator()
    def validate(cls, values) -> dict:
        private_key: str = values.get('private_key', '')

        if values.get('password') and values.get('private_key'):
            raise ValueError('Cannot provide both password and private key at the same time.')

        if private_key:
            values['private_key'] = format_private_key(private_key)

        return values


class SnowflakeDocsSchema(SnowflakeSchema, NoValidationSchema):
    """Snowflake Secrets Schema for API Docs"""
