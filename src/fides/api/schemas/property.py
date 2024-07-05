from enum import Enum
from typing import Any, Iterable, List, Optional

from pydantic import field_validator

from fides.api.custom_types import CssStr
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_center_config import PrivacyCenterConfig


class MinimalPrivacyExperienceConfig(FidesSchema):
    """
    Minimal representation of a privacy experience config, contains enough information
    to select experience configs by name in the UI and an ID to link the selections in the database.

    NOTE: Add to this schema with care. Any fields added to
    this response schema will be exposed in public-facing
    (i.e. unauthenticated) API responses. If a field has
    sensitive information, it should NOT be added to this schema!
    """

    id: str
    name: str


class MinimalMessagingTemplate(FidesSchema):
    """
    Minimal representation of a messaging template.

    NOTE: Add to this schema with care. Any fields added to
    this response schema will be exposed in public-facing
    (i.e. unauthenticated) API responses. If a field has
    sensitive information, it should NOT be added to this schema!
    """

    id: str
    type: str


class PropertyType(Enum):
    website = "Website"
    other = "Other"


class MinimalProperty(FidesSchema):
    id: str
    name: str


class PublicPropertyResponse(FidesSchema):
    """
    Schema that represents a `Property` as returned in the
    public-facing Property APIs.

    NOTE: Add to this schema with care. Any fields added to
    this response schema will be exposed in public-facing
    (i.e. unauthenticated) API responses. If a field has
    sensitive information, it should NOT be added to this schema!

    Any `Property` fields that are sensitive should be added to the
    appropriate non-public schemas that extend this schema.
    """

    name: str
    type: PropertyType
    id: Optional[str] = None
    experiences: List[MinimalPrivacyExperienceConfig]
    messaging_templates: Optional[List[MinimalMessagingTemplate]] = None
    privacy_center_config: Optional[PrivacyCenterConfig] = None
    stylesheet: Optional[CssStr] = None
    paths: List[str]

    @field_validator("paths", mode="before")
    @classmethod
    def convert_to_list(cls, value: Any) -> Any:  # type: ignore[misc]
        """
        Convert the 'paths' value to a list if it is an iterable of strings.
        This validator is necessary because SQLAlchemy returns the 'paths' value
        as an iterable (association proxy) instead of a list. The validator checks
        if the 'paths' value is an iterable (excluding strings) and if all its
        elements are strings. If these conditions are met, it converts the iterable
        to a list. Otherwise, it returns the original value unchanged.
        """
        if (
            isinstance(value, Iterable)
            and not isinstance(value, str)
            and all(isinstance(item, str) for item in value)
        ):
            return list(value)
        return value


class Property(PublicPropertyResponse):
    """
    A schema representing the complete `Property` model.

    This schema extends the base `PublicPropertyResponse` schema,
    which only includes fields that are appropriate to be exposed
    in public endpoints.

    Any `Property` fields that are sensitive but need to be included in private
    API responses should be added to this schema.
    """
