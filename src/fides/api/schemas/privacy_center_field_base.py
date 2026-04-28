"""Abstract base for ``custom_privacy_request_fields`` entries.

Lives in its own module so helpers (validator, evaluator) can depend on
the field shape without importing ``privacy_center_config`` and
introducing a circular import.
"""

from abc import ABC
from typing import Any, Optional

from pydantic import model_validator

from fides.api.schemas.base_class import FidesSchema
from fides.api.task.conditional_dependencies.schemas import Condition


class BaseCustomPrivacyRequestField(FidesSchema, ABC):
    """Abstract base class for all custom privacy request fields"""

    label: str
    required: Optional[bool] = True
    default_value: Optional[str] = None
    hidden: Optional[bool] = False
    query_param_key: Optional[str] = None
    display_condition: Optional[Condition] = None

    @model_validator(mode="before")
    @classmethod
    def validate_default_value(cls, values: dict[str, Any]) -> dict[str, Any]:
        if (
            values.get("hidden")
            and values.get("default_value") is None
            and values.get("query_param_key") is None
        ):
            raise ValueError(
                "default_value or query_param_key are required when hidden is True"
            )
        return values
