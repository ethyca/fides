from typing import ClassVar, List, Optional

from pydantic import Field

from fides.api.schemas.base_class import NoValidationSchema
from fides.api.schemas.connection_configuration.connection_secrets import (
    ConnectionConfigSecretsSchema,
)


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class TestSchema(ConnectionConfigSecretsSchema):
    """Schema to validate the secrets needed for testing multiselect functionality"""

    # Single select field with default value
    environment: Environment = Field(
        title="Environment",
        description="Select the environment to connect to",
        default="development",
    )

    # Multi-select field
    regions: List[str] = Field(
        title="Regions",
        description="Select one or more regions to sync data from",
        options=["us-east", "us-west", "eu-west", "ap-southeast"],
        json_schema_extra={"multiselect": True},
    )

    # Required single select field
    data_type: str = Field(
        title="Data Type",
        description="Type of data to sync",
        options=["users", "orders", "products"],
    )

    # Required multi-select field
    sync_frequency: List[str] = Field(
        title="Sync Frequency",
        description="How often to sync each data type",
        options=["hourly", "daily", "weekly", "monthly"],
        json_schema_extra={"multiselect": True},
    )

    # Sensitive field
    api_key: str = Field(
        title="API Key",
        description="API key for authentication",
        json_schema_extra={"sensitive": True},
    )

    # External reference fields
    user_dataset: Optional[str] = Field(
        title="User Dataset",
        description="Reference to the user dataset",
        json_schema_extra={"external_reference": True},
    )

    order_dataset: Optional[str] = Field(
        title="Order Dataset",
        description="Reference to the order dataset",
        json_schema_extra={"external_reference": True},
    )

    _required_components: ClassVar[List[str]] = [
        "data_type",
        "sync_frequency",
        "api_key",
    ]


class TestDocsSchema(TestSchema, NoValidationSchema):
    """Test Secrets Schema for API docs"""

    pass
