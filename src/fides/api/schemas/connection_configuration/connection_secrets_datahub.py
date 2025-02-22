from enum import Enum
from typing import ClassVar, List

from pydantic import Field

from fides.api.custom_types import AnyHttpUrlStringRemovesSlash
from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class PeriodicIntegrationFrequency(Enum):
    """Enum for periodic integration frequency"""

    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class DatahubSchema(ConnectionConfigSecretsSchema):
    datahub_server_url: AnyHttpUrlStringRemovesSlash = Field(
        title="DataHub Server URL",
        description="The URL of your DataHub server.",
    )
    datahub_token: str = Field(
        title="DataHub Token",
        description="The token used to authenticate with your DataHub server.",
        json_schema_extra={"sensitive": True},
    )
    frequency: PeriodicIntegrationFrequency = Field(
        title="Frequency",
        description="The frequency at which the integration should run. Defaults to daily.",
        default=PeriodicIntegrationFrequency.daily,
    )
    glossary_node: str = Field(
        title="Glossary Node",
        description="The glossary node name to use on Datahub for Fides Data Categories. Defaults to FidesDataCategories",
        default="FidesDataCategories",
    )

    _required_components: ClassVar[List[str]] = ["datahub_server_url", "datahub_token"]


class DatahubDocsSchema(DatahubSchema, NoValidationSchema):
    """
    Datahub Schema for API docs.
    """
