from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import root_validator

from fides.api.schemas.base_class import FidesSchema


class PropertyType(Enum):
    website = "Website"
    other = "Other"


class Property(FidesSchema):
    name: str
    type: PropertyType
    key: Optional[str] = None

    @root_validator
    def generate_key(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the property key from the name if not supplied
        """
        values["key"] = re.sub(r"\s+", "_", values["name"].lower().strip())
        return values
