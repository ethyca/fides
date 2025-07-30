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
    not_scheduled = "not scheduled"


PERIODIC_INTEGRATION_FREQUENCY_TO_DAYS = {
    PeriodicIntegrationFrequency.daily.value: 1,
    PeriodicIntegrationFrequency.weekly.value: 7,
    PeriodicIntegrationFrequency.monthly.value: 30,
    PeriodicIntegrationFrequency.not_scheduled.value: -1,  # negative value to indicate that the integration is not scheduled
}


class DatahubSchema(ConnectionConfigSecretsSchema):
    datahub_server_url: AnyHttpUrlStringRemovesSlash = Field(
        title="DataHub server URL",
        description="The URL of your DataHub server.",
    )
    datahub_token: str = Field(
        title="DataHub token",
        description="The token used to authenticate with your DataHub server.",
        json_schema_extra={"sensitive": True},
    )
    frequency: PeriodicIntegrationFrequency = Field(
        title="Frequency",
        description="The frequency at which the integration should run. Available options are daily, weekly, monthly, and not scheduled.",
    )
    glossary_node: str = Field(
        title="Glossary node",
        description="The glossary node name to use on Datahub for Fides Data Categories. (e.g. FidesDataCategories)",
    )

    _required_components: ClassVar[List[str]] = ["datahub_server_url", "datahub_token"]


class DatahubDocsSchema(DatahubSchema, NoValidationSchema):
    """
    Datahub Schema for API docs.
    """
