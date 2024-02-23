from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict

from pydantic import root_validator

from fides.api.common_exceptions import ValidationError
from fides.api.schemas.base_class import FidesSchema


class PropertyType(Enum):
    website = "Website"
    other = "Other"


class Property(FidesSchema):
    name: str
    key: str
    type: PropertyType


class PropertyCreate(Property):
    name: str
    type: PropertyType

    @root_validator(pre=True)
    def generate_key(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the notice_key from the name if not supplied
        """
        name = values.get("name")
        if not name:
            raise ValidationError("Property keys must be generated from a string.")
        values["key"] = re.sub(r"\s+", "_", name.lower().strip())
        return values
