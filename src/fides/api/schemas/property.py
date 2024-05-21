from enum import Enum
from typing import Any, Iterable, List, Optional

from pydantic import validator

from fides.api.custom_types import CssStr
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.privacy_center_config import PrivacyCenterConfig


class MinimalPrivacyExperienceConfig(FidesSchema):
    """
    Minimal representation of a privacy experience config, contains enough information
    to select experience configs by name in the UI and an ID to link the selections in the database.
    """

    id: str
    name: str


class PropertyType(Enum):
    website = "Website"
    other = "Other"


class MinimalProperty(FidesSchema):
    id: str
    name: str


class Property(FidesSchema):
    name: str
    type: PropertyType
    id: Optional[str] = None
    experiences: List[MinimalPrivacyExperienceConfig]
    privacy_center_config: Optional[PrivacyCenterConfig]
    stylesheet: Optional[CssStr]
    paths: List[str]

    @validator("paths", pre=True)
    def convert_to_list(cls, value: Any) -> Any:
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
