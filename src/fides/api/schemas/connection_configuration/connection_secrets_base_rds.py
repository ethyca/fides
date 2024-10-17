from pydantic import Field

from fides.api.schemas.connection_configuration.connection_secrets_base_aws import (
    BaseAWSSchema,
)


class BaseRDSSchema(BaseAWSSchema):
    """
    Schema to validate the secrets needed to connect to a RDS Database
    """

    db_username: str = Field(
        default="fides_service_user",
        title="DB Username",
        description="The user account used to authenticate and access the databases.",
    )
    region: str = Field(
        title="Region",
        description="The AWS region where the RDS instances are located.",
    )
